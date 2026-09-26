"""AIM reference arithmetic, ISA interpreter, and transparent system estimates."""
from __future__ import annotations
import json, math, struct
from dataclasses import dataclass, field
from pathlib import Path

CONFIGS = json.loads((Path(__file__).resolve().parents[1]/'configs/aim.json').read_text())


def config(name):
    return dict(CONFIGS[name])


def quantize_float(value, exponent_bits, mantissa_bits, bias=None):
    """Nearest-even finite minifloat; IEEE-like subnormals, infinities and NaNs."""
    if exponent_bits < 2 or mantissa_bits < 1: raise ValueError('invalid format')
    bias = bias if bias is not None else (1 << (exponent_bits-1))-1
    sign = math.copysign(1., value)
    v = abs(float(value))
    if math.isnan(v): return float('nan')
    if math.isinf(v): return sign*float('inf')
    if v == 0: return sign*0.
    emin, emax = 1-bias, (1 << exponent_bits)-2-bias
    step = 2.**(emin-mantissa_bits)
    if v < 2.**emin:
        return sign * (round(v/step)*step)
    exponent = math.floor(math.log2(v))
    if exponent > emax: return sign*float('inf')
    quantum = 2.**(exponent-mantissa_bits)
    rounded = round(v/quantum)*quantum
    return sign*(rounded if rounded < 2.**(emax+1) else float('inf'))


def cast(value, fmt):
    if fmt == 'BF16':
        bits = struct.unpack('>I', struct.pack('>f', float(value)))[0]
        upper = bits >> 16
        # round-to-nearest-even; preserve NaN payload
        if (bits & 0x7f800000) != 0x7f800000:
            upper = (bits + 0x7fff + (upper & 1)) >> 16
        return struct.unpack('>f', struct.pack('>I', upper << 16))[0]
    if fmt == 'FP16': return struct.unpack('>e', struct.pack('>e', value))[0]
    if fmt == 'FP8E4M3': return quantize_float(value, 4, 3)
    if fmt == 'FP8E5M2': return quantize_float(value, 5, 2)
    if fmt == 'FP10E2M7': return quantize_float(value, 2, 7)
    if fmt in ('INT8','INT4'):
        bits = 8 if fmt == 'INT8' else 4
        return max(-(1 << (bits-1)), min((1 << (bits-1))-1, round(value)))
    if fmt == 'FP32': return struct.unpack('>f', struct.pack('>f', value))[0]
    raise ValueError(fmt)


def gemm(a, b, fmt='INT8'):
    m = len(a); k = len(a[0]) if m else 0
    if any(len(row)!=k for row in a) or len(b)!=k: raise ValueError('shape')
    n = len(b[0]) if b else 0
    if any(len(row)!=n for row in b): raise ValueError('shape')
    return [[sum(cast(a[i][t],fmt)*cast(b[t][j],fmt) for t in range(k)) for j in range(n)] for i in range(m)]


@dataclass
class Counters:
    cycles: int = 0
    macs: int = 0
    bytes_hbm: int = 0
    bytes_noc: int = 0
    bytes_fpga: int = 0
    stalls: int = 0


@dataclass
class Machine:
    """Functional instruction interpreter plus non-overlapped lower-bound event timing."""
    cfg: dict
    memory: dict = field(default_factory=dict)
    registers: dict = field(default_factory=dict)
    c: Counters = field(default_factory=Counters)
    pending: dict = field(default_factory=dict)

    def run(self, program):
        for ins in program:
            op = ins['op']; dst = ins.get('dst'); src = ins.get('src')
            if op in ('DMA_LOAD','DMA_STORE'):
                data = self.memory[src] if op == 'DMA_LOAD' else self.registers[src]
                target = self.registers if op == 'DMA_LOAD' else self.memory
                target[dst] = [r[:] if isinstance(r,list) else r for r in data]
                self.c.bytes_hbm += ins.get('bytes',len(str(data)))
                self.c.cycles += ins.get('latency',100)
            elif op == 'GEMM':
                a, b = self.registers[ins['a']], self.registers[ins['b']]
                self.registers[dst] = gemm(a,b,ins.get('format','INT8'))
                macs = len(a)*(len(a[0]) if a else 0)*(len(b[0]) if b else 0)
                self.c.macs += macs
                self.c.cycles += math.ceil(len(a)/self.cfg['array_m'])*math.ceil(len(b[0])/self.cfg['array_n'])*(len(b)+self.cfg['array_m']+self.cfg['array_n']-2)
            elif op == 'VECTOR':
                x = self.registers[src]
                func = ins.get('func','RELU')
                self.registers[dst] = [max(0,v) if func=='RELU' else v+ins.get('scalar',0) for v in x]
                self.c.cycles += math.ceil(len(x)/ins.get('width',8))
            elif op == 'REDUCE':
                self.registers[dst] = sum(self.registers[src]); self.c.cycles += len(self.registers[src])
            elif op == 'SEND':
                size = ins['bytes']; self.c.bytes_noc += size
                if ins.get('inter_fpga'): self.c.bytes_fpga += size
                self.c.cycles += ins.get('latency',3) + math.ceil(size/ins.get('bytes_per_cycle',16))
            elif op == 'BARRIER': self.c.cycles += max(self.pending.values(),default=0); self.pending.clear()
            elif op == 'ASYNC': self.pending[ins['tag']] = ins['cycles']
            elif op == 'WAIT': self.c.cycles += self.pending.pop(ins['tag'])
            else: raise ValueError(op)
        return self


def model(cfg, fmt='FP8E4M3', hbm_tbps_per_stack=2.8, usable_gb=None, utilization=0.5):
    dies = cfg['packages']*cfg['dies_per_package']
    engines = dies*cfg['superclusters_per_die']*cfg['clusters_per_supercluster']*cfg['engines_per_cluster']
    lanes = engines*cfg['array_m']*cfg['array_n']
    multiplier = {'BF16':0.5,'FP16':0.5,'FP8E4M3':1,'FP8E5M2':1,'INT8':1,'INT4':2,'FP10E2M7':0.5}[fmt]
    peak = lanes*2*cfg['clock_ghz']*1e9*multiplier
    stacks = cfg['packages']*cfg['hbm_stacks_per_package']
    hbm = stacks*hbm_tbps_per_stack*1e12
    raw = stacks*cfg['hbm_gb_per_stack']
    usable = raw if usable_gb is None else usable_gb
    if usable > raw: raise ValueError('usable exceeds physical capacity')
    sram_mib = dies*cfg['l2_mib_per_die'] + dies*cfg['superclusters_per_die']*cfg['clusters_per_supercluster']*cfg['scratchpad_kib_per_cluster']/1024
    return dict(dies=dies,engines=engines,lanes=lanes,peak_ops_s=peak,sustained_assumption_ops_s=peak*utilization,raw_hbm_gb=raw,usable_hbm_gb=usable,peak_hbm_bytes_s=hbm,sram_mib=sram_mib,ridge_ops_per_byte=peak/hbm if hbm else None)


def roofline(flops, bytes_transferred, cfg=None, fmt='FP8E4M3', efficiency=0.7):
    cfg = cfg or config('AIM_FULL'); m=model(cfg,fmt,usable_gb=512)
    compute_seconds=flops/m['peak_ops_s']; memory_seconds=bytes_transferred/(m['peak_hbm_bytes_s']*efficiency)
    return dict(compute_s=compute_seconds,memory_s=memory_seconds,lower_bound_s=max(compute_seconds,memory_seconds),limiter='compute' if compute_seconds>=memory_seconds else 'memory')


def decode_estimate(parameters_b, weight_bits=8, batch=1, active_fraction=1., kv_bytes_per_token=0, cfg=None):
    """Optimistic lower bound: weights fetched once per batch, no orchestration cost."""
    cfg=cfg or config('AIM_FULL'); params=parameters_b*1e9*active_fraction
    weight_bytes=params*weight_bits/8
    flops=2*params*batch
    return roofline(flops,weight_bytes+batch*kv_bytes_per_token,cfg)


def mesh_traffic(width, height, packets, link_bytes_per_cycle=32):
    """Deterministic XY routing, link serialization; returns congestion lower bound.

    packets: (source_x, source_y, dest_x, dest_y, bytes). Injection and
    router pipeline contention beyond link serialization are excluded.
    """
    if width < 1 or height < 1 or link_bytes_per_cycle < 1: raise ValueError('mesh')
    links = {}
    for sx,sy,dx,dy,size in packets:
        if not (0<=sx<width and 0<=dx<width and 0<=sy<height and 0<=dy<height) or size<0:
            raise ValueError('packet')
        x,y=sx,sy
        while x!=dx:
            nx=x+(1 if dx>x else -1)
            edge=(x,y,nx,y); links[edge]=links.get(edge,0)+size; x=nx
        while y!=dy:
            ny=y+(1 if dy>y else -1)
            edge=(x,y,x,ny); links[edge]=links.get(edge,0)+size; y=ny
    return {'link_bytes':links,'peak_link_bytes':max(links.values(),default=0),
            'link_congestion_cycles':max((math.ceil(v/link_bytes_per_cycle) for v in links.values()),default=0)}


def partition_penalty(messages, bandwidth_gbps=100, latency_us=2, serialization=1):
    """Conservative FPGA cross-partition link estimate, messages are byte counts."""
    if bandwidth_gbps<=0 or latency_us<0 or serialization<1: raise ValueError('link')
    return sum(latency_us*1e-6 + size*8/(bandwidth_gbps*1e9) for size in messages)*serialization


def collective_lower_bound(devices, payload_bytes, link_bytes_s, kind='ALLREDUCE'):
    if devices<1 or link_bytes_s<=0: raise ValueError('collective')
    if kind in ('ALLREDUCE','ALLGATHER','REDUCESCATTER'):
        factor=(2 if kind=='ALLREDUCE' else 1)*(devices-1)/devices
    elif kind=='ALLTOALL': factor=(devices-1)/devices
    else: raise ValueError(kind)
    return factor*payload_bytes/link_bytes_s

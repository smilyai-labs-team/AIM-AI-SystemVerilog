import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sim.aim import *
full=config('AIM_FULL')
print('ARCHITECTURAL MODEL — never measured silicon performance')
for fmt in ('FP16','BF16','FP8E4M3','INT8','INT4','FP10E2M7'):
    m=model(full,fmt,usable_gb=512)
    print(f'{fmt:10s} theoretical peak {m["peak_ops_s"]/1e15:6.3f} P' + ('FLOP/s' if fmt not in ('INT8','INT4') else 'OP/s'))
print('raw HBM 576 GB, addressable budget 512 GB, peak HBM target 44.8 TB/s')
print('Decode optimistic bandwidth/compute lower bound; 8-bit resident weights, batch=1, KV excluded')
for p in (1,7,30,70,100,200):
    x=decode_estimate(p)
    print(f'{p:3d}B: {1/x["lower_bound_s"]:8.1f} tokens/s upper bound, {x["limiter"]}-limited')
print('Prefill/training: provide actual GEMM shapes, optimizer traffic, precision and utilization before predictions.')

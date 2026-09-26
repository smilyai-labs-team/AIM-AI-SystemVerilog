import math, random, shutil, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sim.aim import *
from sim.aim import decode_estimate, mesh_traffic, partition_penalty, collective_lower_bound
from sim.transformer import attention, rmsnorm, rope, topk_route, swiglu
class TestAIM(unittest.TestCase):
 def test_transformer_kernels(self):
  self.assertEqual(topk_route([.1,.5,.5],2),[1,2])
  self.assertAlmostEqual(rmsnorm([3.,4.],[1.,1.])[0],3/math.sqrt(12.5+1e-6))
  self.assertAlmostEqual(rope([1.,0.],0)[0],1.)
  out=attention([[1.,0.],[0.,1.]],[[1.,0.],[0.,1.]],[[2.],[4.]])
  self.assertEqual(out[0],[2.])
  self.assertTrue(2<out[1][0]<4)
  self.assertEqual(len(swiglu([0.,1.],[2.,3.])),2)
 def test_full(self):
  c=config('AIM_FULL'); m=model(c,usable_gb=512)
  self.assertEqual(m['lanes'],2097152)
  self.assertAlmostEqual(m['peak_ops_s']/1e15,10.0663296)
  self.assertEqual((m['raw_hbm_gb'],m['usable_hbm_gb']),(576,512))
  self.assertAlmostEqual(model(c,'BF16')['peak_ops_s']/1e15,5.0331648)
  self.assertAlmostEqual(m['peak_hbm_bytes_s']/1e12,44.8)
 def test_ugly_shapes(self):
  r=random.Random(76)
  for m,k,n in [(1,1,1),(3,5,7),(9,17,2),(13,4,11)]:
   a=[[r.randrange(-128,128) for _ in range(k)] for _ in range(m)]
   b=[[r.randrange(-128,128) for _ in range(n)] for _ in range(k)]
   out=gemm(a,b)
   for i in range(m):
    for j in range(n): self.assertEqual(out[i][j],sum(a[i][t]*b[t][j] for t in range(k)))
 def test_edge_formats(self):
  self.assertTrue(math.isnan(cast(float('nan'),'BF16')))
  self.assertTrue(math.isinf(cast(float('inf'),'FP8E4M3')))
  self.assertEqual(cast(8,'FP10E2M7'),float('inf'))
  self.assertEqual(cast(-100,'INT4'),-8)
 def test_program(self):
  x=Machine(config('AIM_TINY'),memory={'a':[[1,2,3]],'b':[[4],[5],[6]]})
  x.run([{'op':'DMA_LOAD','src':'a','dst':'a'},{'op':'DMA_LOAD','src':'b','dst':'b'}, {'op':'GEMM','a':'a','b':'b','dst':'c'}, {'op':'SEND','bytes':37,'inter_fpga':True}])
  self.assertEqual(x.registers['c'],[[32]]);self.assertEqual(x.c.macs,3)
  self.assertEqual(x.c.bytes_fpga,37)
 def test_roofline(self):
  self.assertEqual(decode_estimate(70)['limiter'],'memory')
  with self.assertRaises(ValueError): model(config('AIM_FULL'),usable_gb=600)
 def test_noc(self):
  x=mesh_traffic(3,3,[(0,0,2,2,64),(0,0,2,1,31)],32)
  self.assertEqual(x['peak_link_bytes'],95)
  self.assertEqual(x['link_congestion_cycles'],3)
  self.assertGreater(partition_penalty([2048],100,2),2e-6)
  self.assertAlmostEqual(collective_lower_bound(4,1000,1000),1.5)
 def test_rtl_if_available(self):
  if not shutil.which('iverilog') or not shutil.which('vvp'): self.skipTest('Icarus Verilog unavailable')
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   exe=str(Path(d)/'tb')
   subprocess.run(['iverilog','-g2012','-s','tb_aim','-o',exe,str(ROOT/'rtl/aim_tensor.sv'),str(ROOT/'tests/tb_aim.sv')],check=True)
   out=subprocess.run(['vvp',exe],capture_output=True,text=True,check=True)
   self.assertIn('PASS',out.stdout)
if __name__=='__main__':unittest.main()

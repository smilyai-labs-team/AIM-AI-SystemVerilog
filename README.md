# AIM — Artificial Intelligence Machine (v0.1 research implementation)

A silicon-first accelerator architecture and a small, working Soft Chip slice. `AIM_FULL` is an **architectural target**; it is not an implemented 10 PFLOPS chip. The synthesizable RTL covers a parameterized INT8 matrix engine, vector engine, SRAM/DMA, command control and a packet switch. HBM PHY, FP tensor datapaths, package links, ECC, and distributed FPGA transport remain future work, explicitly tracked in `docs/roadmap.md`.

## Reproduce

```sh
python3 -m unittest discover -s tests -v
python3 benchmarks/run.py
python3 scripts/feasibility.py
# if installed: iverilog -g2012 -s tb_aim -o /tmp/aim_tb rtl/*.sv tests/tb_aim.sv && vvp /tmp/aim_tb
# if installed: yosys -s scripts/synth.ys
```

No Python dependencies beyond the standard library. The HDL tests require Icarus Verilog; they skip cleanly if unavailable. Each RTL array computes a tiled INT8 dot product with signed accumulation; Python's format library extends beyond the current RTL. See `docs/architecture.md` and `docs/evidence.md` before interpreting performance figures.

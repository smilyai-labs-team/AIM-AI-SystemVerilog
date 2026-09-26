# AIM v2 milestone roadmap and honest completeness ledger

## Delivered in v0.1

- ASIC target model with explicit format-dependent peaks, HBM budget, roofline and package-level hierarchy.
- Synthesizable stand-alone INT8 matrix outer-product engine, saturated vector ALU, single-port SRAM, handshaked DMA, command issue decoder, small ready/valid packet switch.
- Python instruction interpreter, precision quantization reference, odd-dimension GEMM tests, traffic and communication lower-bound models, reproducible script.

## Required to call it a working full Soft Chip

1. Integrate RTL primitives into a top-level cluster with arbitration and an executable program memory; implement an end-to-end tile-level RTL/Python scoreboard and reset/hazard regressions.
2. Add BF16/FP16/FP8 tensor datapaths, reproducible rounding modes, exception handling, accumulation precision, random differential tests and public-model numerical quality studies. Experimental E2M7 has only a Python toy quantizer; evaluate underflow, overflow and quality before silicon.
3. Implement banked ECC SRAM, HBM channel scheduling model, DMA outstanding IDs, asynchronous queues, page translation, faults, KV gather and scratchpad tiling.
4. Build credit-based 2D mesh, hardware multicast/reduction, cycle traffic simulation, congestion tests and QoS for MoE all-to-all.
5. Implement partition packet framing, clock virtualization, link transport, distributed barriers and fault recovery, then synthesize real FPGA builds and report LUT/BRAM/DSP/Fmax **measured**.
6. Build compiler/runtime kernels for attention, RMSNorm, RoPE, SwiGLU, sparse GEMM, grouped MoE and training backward; benchmark validated weights against CPU reference on real workloads.
7. Acquire PDK/library and PHY collateral; perform logical synthesis, physical floorplan, clock/power/thermal/packaging feasibility; iterate lanes, clock, chiplet count and bandwidth until gates close.

No tensor engine RTL today supports floating point. No RTL test ran in this environment because Icarus/Verilator/Yosys are absent. No real silicon, FPGA resource, PFLOPS, tokens/s or bandwidth measurement exists.

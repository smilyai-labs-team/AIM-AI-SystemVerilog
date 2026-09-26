# Physical feasibility gates

| Item | Status | Initial bound and gate |
|---|---|---|
| Compute node | architectural assumption | Approx. 3 nm compute logic; timing requires place and route with qualified libraries. |
| Clock | target | 2.4 GHz; 1.6 GHz fallback delivers 6.71 PFLOP/s FP8. |
| Logic dies | target | 16 dies, four per module; assume 500–800 mm²/die as **unvalidated budget**, requiring die-level floorplans. |
| Compute density | target | 131,072 FP8 MAC lanes/die; area per lane and reduction/broadcast wires are a major risk. |
| SRAM | calculated capacity | 4 MiB/die, 64 MiB total; macro area/port count and ECC not estimated from a library. |
| HBM | public product evidence + assumption | 16 × 36 GB HBM4 stacks; 2.8 TB/s/stack target near reported HBM4 class, vendor-specific qualification required. |
| Package | conceptual | Four liquid-cooled four-die/four-HBM modules on a coherent baseboard; routing and power delivery open. |
| Power | speculative envelope | 1000–1800 W/module; 4–7.2 kW/device including HBM/fabric. Neither RTL nor Python estimates power. |
| Thermal | unresolved | Direct liquid cooling and module cold plates assumed; thermal CFD/IR and fault behavior needed. |
| Die-to-die I/O | target | 2 TB/s device bisection; PHY width/energy and protocol not designed. |
| Production feasibility | unproven | Cost, yield, supply, SerDes, HBM availability and physical closure are all major gates. |

A 16-die multi-module board makes the memory count conceivable, yet 2.4 GHz across such a wide operand broadcast and 131k MAC lanes per die may exceed the tentative 500–800 mm² / 250–450 W per-die budget. Avoid treating this area or power envelope as achieved. A sensible v2 alternative is more modules and lanes at lower clock, with greater collective overhead, subject to a real physical design study.

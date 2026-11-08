# Working with the KiCad seed

Open `pcb/mx/worxboard-ergo-mx.kicad_pro` or `pcb/choc/worxboard-ergo-choc.kicad_pro` with KiCad 10.0.7. The projects include the schematic, XML netlist, placed board, project library tables and generated placement coordinates. Library files under `pcb/lib/` are committed; stock KiCad libraries are required for regeneration.

`make pcb` regenerates source files, checks every schematic pin net against the numbered PCB pads, and writes fresh ERC and DRC reports under `pcb/reports/`. It does not autoroute. The boards include 48 switches and their 48 diodes, and zero routed tracks. The four-layer count is chosen as a starting point, but a real stackup and plane strategy must be reviewed before routing.

The schematic and board references are linked by UUID. MCU/support parts start in the center service area and USB components near each receptacle. Their placement must be reviewed against actual component height, switch/socket and keycap envelopes. Specific clearance, solder-mask, courtyard and silk findings are retained in the DRC reports. Report generation is allowed to complete so engineers can inspect a seed; `make check-fabrication` is the separate gate and remains blocked.

For A2, fix actual causes of DRC findings, add the local power/ground layout, route the USB data pairs and matrix, run schematic parity, and review all fabrication layers manually. Export Gerbers and drills only after this work. `tools/pcb.sh` currently overwrites manual PCB edits when rerun; commit manual routing as its own stage and change the workflow to preserve/import it before starting A2 routing.

The source matrix order is independent of physical row stagger. For switch `SK101 + i`, the corresponding diode is `D101 + i`, and the logical matrix position is `(i // 15, i % 15)`. This order also drives ZMK's matrix transform and all keymap layers.

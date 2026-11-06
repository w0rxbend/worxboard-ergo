# Engineering workflow and acceptance gates

The workflow is started at **A0 / reviewable source and geometry**. Tasks are recorded here so the repository remains useful without relying on this chat.

| Gate | Deliverable | Acceptance |
|---|---|---|
| A0 | Canonical 87-key layout, MX/Choc models, KiCad seeds, ZMK board/module, CI | Editable files exist; topology, mesh and compile evidence recorded |
| A1 | Electrical and mechanical review | Correct local component placement; switch/stabilizer/keycap samples selected; ROM flashing override reviewed; connector/LCD envelopes measured |
| A2 | Routed PCBs | Both switch variants have zero ERC/DRC errors and zero unconnected nets, schematic parity, verified planes/USB pairs, reviewed stackup and BOM |
| A3 | Fit and electronics prototype | Switch/LCD/USB coupons pass, power rails and backfeed tested, every key works, all three ports enumerate/reconnect, LCD shows correct layer, Studio remaps persist |
| A4 | RGB and ergonomics completion | Per-key RGB circuit/driver/current limit tested; palm-rest attachment, print joinery, tilt/tenting choice and case geometry validated |
| A5 | Manufacturing package | Reviewed Gerbers/drills/BOM/CPL, STEP/STL/3MF/FCStd manifest and build logs; small pilot run; release notes state tested hardware revision |

Immediate engineering tasks:

- [ ] Review three-port VBUS diode OR, mux analog path 3, ESD return, USB attach current and sense thresholds.
- [ ] Review and test the J6/J7 hardware override: RUN shunts 1–2, center-port ROM shunts 2–3, disconnected firmware control pins.
- [ ] Move support components next to the MCU/regulator/crystal/connectors, check courtyards and mechanical stack; then route both boards.
- [ ] Verify Choc footprint pin mapping, socket side, plate opening, PCB thickness and source stable wide keycaps/stabilizers. Add matching PCB stabilizer clearance holes, and adjust the familiar layout if necessary.
- [ ] Measure actual LCD breakout/header height and mounting, then make the bezel retention functional.
- [ ] Add fit coupons and registration/fastening for split print sections; choose palm-rest attachment and screw hardware.
- [ ] Choose RGB LEDs/driver/level shifting and enforce USB current limits, suspend behavior and LED-off default.
- [ ] Evaluate a domed/tented design against the initial flat board; document new rigid-board or interconnect geometry.
- [ ] Prototype and record measurements/photos before calling any hardware orderable.

CI builds sources and firmware. Manufacturing gating remains red until A2; do not make it green by filtering unrouted errors or by adding blanket DRC exclusions.

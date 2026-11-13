# Engineering workflow and acceptance gates

The workflow is started at **A0 / reviewable source and geometry**. Tasks are recorded here so the repository remains useful without relying on this chat.

| Gate | Deliverable | Acceptance |
|---|---|---|
| A0 | Canonical 48-key split Planck, MX/Choc models, KiCad seeds, ZMK board/module, CI | Editable files exist; topology, mesh and compile evidence recorded |
| A1 | Electrical and mechanical review | Correct local component placement; switch/stabilizer/keycap samples selected; ROM flashing override reviewed; connector/LCD envelopes measured |
| A2 | Routed PCBs | Both switch variants have zero ERC/DRC errors and zero unconnected nets, schematic parity, verified planes/USB pairs, reviewed stackup and BOM |
| A3 | Fit and electronics prototype | Switch/LCD/USB coupons pass, power rails and backfeed tested, every key works, all three ports enumerate/reconnect, LCD shows correct layer, Studio remaps persist |
| A4 | RGB and ergonomics completion | Per-key RGB circuit/driver/current limit tested; palm-rest attachment, print joinery, tilt/tenting choice and case geometry validated |
| A5 | Manufacturing package | Reviewed Gerbers/drills/BOM/CPL, STEP/STL/3MF/FCStd manifest and build logs; small pilot run; release notes state tested hardware revision |

Immediate engineering tasks:

- [ ] Review three-port VBUS diode OR, mux analog path 3, ESD return, USB attach current and sense thresholds.
- [ ] Review and test the J6/J7 hardware override: RUN shunts 1–2, center-port ROM shunts 2–3, disconnected firmware control pins.
- [x] Move support components next to the MCU/regulator/crystal/connectors and route both boards. Every SMD part is on B.Cu. See [verification.md](verification.md) for the checks and the open review items.
- [ ] Human review of the routed boards before ordering: USB pairs and their ground return, plane splits, every Gerber layer and drill file, and the PCBWay order sheet in `pcb/fab/<variant>/ORDER.md`.
- [ ] Verify Choc footprint pin mapping, socket side, plate opening, PCB thickness and source stable wide keycaps/stabilizers. Add matching PCB stabilizer clearance holes, and adjust the familiar layout if necessary.
- [ ] Measure actual LCD breakout/header height and mounting, then make the module retention under the top-cover window functional.
- [ ] Print the center-tab coupon and the palm-rest screws. The tab and the six shelf screws are modeled; fit is not measured.
- [ ] Slice the Sculpt-style chassis, top cover and palm rest, then print coupons: one USB tunnel with a real plug, a cover boss with its screw from below, a magnet pocket, a pad recess, the plate and cover recess corner, and the palm lip. The shell is envelope CAD; none of this is measured.
- [x] Turn J1, J2 and J3 so each mouth is flush with the PCB rear edge and faces rearward, on the bay's straight rear edge. `PORTS`, the board and the case agree.
- [ ] Clear the space under the plate. Done: every SMD part is on B.Cu, inside the 4.0 mm under the board. Open: J4 to J7 are still top-side through-hole footprints taller than the room under the plate (fit wire links instead, see [assembly.md](assembly.md)); BOOT, RESET and the J6/J7 links have no access path through the closed case; component keep-outs are not in the fit gate.
- [ ] Mounting holes: all eight sit closer than 1 mm to the board edge, so `layout.board_outline()` opens each into an edge slot. Moving them inward needs the rim and boss layout to change; the slots are a stopgap to review.
- [ ] Move the shell plan and the palm-screw, magnet and pad positions into `layout/model.py`, and replace `palm_outline()` and `palm_screws()`. Until then `cad/model.py` holds them as a recorded exception to the layout authority rule.
- [ ] Choose the pad part. The riser stance assumes pads 2.0 mm proud of a 1.0 mm recess.
- [x] Reconcile the CAD frame with the PCB top view. The export is right-handed and tests hold the eight holes to the PCB positions. See [verification.md](verification.md).
- [ ] Draw the shell and the top cover in `assets/layout.svg`. It still shows the earlier short palm rest. The product page uses renders of the CAD model instead.
- [ ] Choose RGB LEDs/driver/level shifting and enforce USB current limits, suspend behavior and LED-off default.
- [ ] Decide whether roll-tenting is required. The chassis sits flat and the magnetic riser tips the whole flat deck 6.7 degrees. Separate keywell angles still need two PCBs or a flex.
- [ ] Prototype and record measurements/photos before calling any hardware orderable.

CI builds sources and firmware. Manufacturing gating remains red until A2; do not make it green by filtering unrouted errors or by adding blanket DRC exclusions.

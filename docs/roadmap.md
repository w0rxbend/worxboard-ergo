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

- [ ] Finish the RP2040 fan-out on MX. The bay is boxed in: about 25 GPIOs plus SWD and RUN must leave the QFN through one ring of escape vias, and the SPI display pins face away from J4. Options that cost nothing at PCBWay: move the display to SPI0 on GP5–7 and COL0/COL1 to GP26/27 (needs a firmware rebuild), rotate U1, add rip-up and retry to `pcb/scripts/maze.py`, or hand-route the fan-out once and commit it as a fixed input.
- [ ] Route Choc with the same pipeline, regenerate ERC/DRC/parity reports, then build the PCBWay package with `tools/pcb_fab.sh`.
- [ ] Pick a real LCD socket for J4 and headers for J5–J7 that fit under the plate (1.0 mm on Choc, 3.5 mm on MX), or move them. Check the SK119 and SK143 socket courtyards against the chassis bosses.
- [ ] Choose the crystal: the fitted YXC part is CL 18 pF, not the ABM8-272-T3 the RP2040 design guide names.

- [ ] Review three-port VBUS diode OR, mux analog path 3, ESD return, USB attach current and sense thresholds.
- [ ] Review and test the J6/J7 hardware override: slide switches, RUN on 1–2, center-port ROM on 2–3, disconnected firmware control pins.
- [ ] Move support components next to the MCU/regulator/crystal/connectors, check courtyards and mechanical stack; then route both boards.
- [ ] Verify Choc footprint pin mapping, socket side, plate opening, PCB thickness and source stable wide keycaps/stabilizers. Add matching PCB stabilizer clearance holes, and adjust the familiar layout if necessary.
- [ ] Measure actual LCD breakout/header height and mounting, then make the module retention under the top-cover window functional.
- [ ] Print the center-tab coupon and the palm-rest screws. The tab and the six shelf screws are modeled; fit is not measured.
- [ ] Slice the Sculpt-style chassis, top cover and palm rest, then print coupons: one USB tunnel with a real plug, a cover boss with its screw from below, a magnet pocket, a pad recess, the plate and cover recess corner, and the palm lip. The shell is envelope CAD; none of this is measured.
- [ ] Turn J1, J2 and J3 so each mouth is at the PCB rear edge and faces rearward, and move the side jacks off the rounded plank corner. Give `place.py` a per-part angle. Move `PORTS` to match, then regenerate the PCB and the case. The case keep-outs already assume this placement.
- [ ] Clear the space under the plate: move diodes and ICs to the bottom copper on Choc, replace or relocate the J4 to J7 headers, and give BOOT, RESET and the J6/J7 jumpers an access path through the closed case. Then add component keep-outs to the fit gate.
- [ ] Move the two mounting holes that break the board edge, or widen the board there. Keep at least a hole radius plus 1 mm of board outside each hole.
- [ ] Move the shell plan and the palm-screw, magnet and pad positions into `layout/model.py`, and replace `palm_outline()` and `palm_screws()`. Until then `cad/model.py` holds them as a recorded exception to the layout authority rule.
- [ ] Choose the pad part. The riser stance assumes pads 2.0 mm proud of a 1.0 mm recess.
- [x] Reconcile the CAD frame with the PCB top view. The export is right-handed and tests hold the eight holes to the PCB positions. See [verification.md](verification.md).
- [ ] Draw the shell and the top cover in `assets/layout.svg`. It still shows the earlier short palm rest. The product page uses renders of the CAD model instead.
- [ ] Choose RGB LEDs/driver/level shifting and enforce USB current limits, suspend behavior and LED-off default.
- [ ] Decide whether roll-tenting is required. The chassis sits flat and the magnetic riser tips the whole flat deck 6.7 degrees. Separate keywell angles still need two PCBs or a flex.
- [ ] Prototype and record measurements/photos before calling any hardware orderable.

CI builds sources and firmware. Manufacturing gating remains red until A2; do not make it green by filtering unrouted errors or by adding blanket DRC exclusions.

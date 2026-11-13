# A0 verification and known limitations

This repository is an **engineering starter**, dated 2026-11-08. No physical keyboard, PCB, enclosure, USB isolation circuit or display has been built or tested. The Sculpt-style shell, revised 2026-11-12, is a geometry revision of that starter. It is envelope CAD, not a fabrication release, and its physical fit is unmeasured. The PCB is unrouted and is not ready for production.

| Area | Evidence | Meaning |
|---|---|---|
| Layout | `tests/test_contracts.py`, `assets/layout.json` | 48 orthogonal keys in two Planck blocks, no numpad, no intersecting keycap envelopes, screw and display clearance |
| Electrical source | Circuit contract tests, two KiCad schematic XML netlists | Diode matrix, per-port CC/VBUS nets, mux mapping and boot jumpers defined |
| PCB | `pcb/reports/*-connectivity.json`, ERC and DRC reports | Pad-net parity matches; **zero tracks**. Each board has 329 unconnected items. MX DRC is 115 errors and 205 warnings (199 of them silk over copper). Choc DRC is 121 errors and 113 warnings (108 of them silk over copper). ERC is 2 isolated-pin-label warnings per board. Not fabrication approved |
| CAD solids | `cad/validation.json` | 26 exported part models total, 13 per variant; valid single solids and positive volume, STEP volume round-trip |
| Case fit | `cad/validation.json`, key `interference_mm3` | Zero overlap volume for 21 pairs, both variants. Chassis against the PCB, LCD, keycap, USB receptacle, USB plug and pad envelopes and against the plate, top cover, palm rest and riser. Plate against the USB envelopes and the top cover. Top cover against the PCB, LCD, keycap, switch-housing and USB envelopes. Palm rest against the keycaps. Riser against the pads. Keycap envelopes are swept through the full key travel |
| Case geometry | `tests/test_case_geometry.py` builds `cad/model.py` | Thirteen single solids per variant; skin at least 5.0 mm; valley wall, front fence and slot-to-palm web at least 2.5 mm in plan; the outline is tangent arcs only; exactly the 2.4 mm floor under every key; at least 1.0 mm left over magnet, pad and palm-pilot pockets; the top cover closes every screw position with 0.8 mm of skin and opens over every key; a seated USB plug clears and an offset one collides; screw holes open; the palm top is 2.5 mm under the keycap tops, bears on the shelf and is at least 60 mm deep; the chassis and the riser clear the riser-stance desk |
| Case frame | `tests/test_case_geometry.py`, `tests/test_contracts.py` | The export is right-handed. Each of the eight `holes()` positions is open at (x, −y) in the built chassis and plate, and each hole in `pcb/*/placement.json` is open at (x, −y) in the exported `chassis.step` and `plate.step`. The mirror-image positions hold material. `chassis_left` carries the left keys |
| Meshes | Test suite loads every STL | 26 watertight positive-volume meshes; 3MF and STEP files also present |
| Native CAD | `cad/freecad-validation.json` | FreeCAD 1.1.4 save/reopen of this export passed, and the four whole-part volumes match `cad/validation.json`. The four parts are the chassis, plate, top cover and palm rest. The riser and the split halves are not in the native file. A later report that does not match is stale. |
| USB selection logic | Compiled host C assertions | Center-first priority, powered-input selection and retained active selection across all input combinations |
| Firmware | `firmware/artifacts/build-report.json` and UF2 | RP2040 ZMK compile/link, LCD driver and Studio USB transport checked against real build outputs |
| Reproducibility | `uv.lock`, `pcb/requirements.lock`, `toolchain.lock.json`, pinned west manifest | Versioned source, dependencies and container digests; upstream Launch preserved as a gitlink |
| Artifact inventory | `assets/artifact-manifest.json`, `assets/SHA256SUMS` | File size and SHA-256 for committed deliverables |

The CAD checks are topology and envelope checks. They do not establish switch retention, stabilizer compatibility, connector fit, display glass/PCB height, print shrinkage, fastener strength, rigidity, ergonomics or assembly clearance against detailed vendor models. The PCB shape shown in STEP is an envelope, not a fully populated board model. Keycaps shown in the assembly are solid envelopes without stems.

Known unfinished work is explicit in [roadmap.md](roadmap.md): both PCB routings and local support-component placement, USB/power measurements, display retention, a printed check of the center tab, per-key RGB power, and all physical bring-up. This grid has no key wider than 1u, so the generated plates have no stabilizer slots. The plate has a south window at each key. The RGB header is not a stuffed LED chain, and a chain would exceed USB suspend without a power switch this MCU cannot currently enable. The chassis sits flat. The riser sets 6.7 degrees of negative tilt; it is modeled, not built. The rim is flat. The keywells are not roll-tented. The selected host-input arrangement does not include Launch's USB hub.

Case shell, not verified:

- No slicer run and no printed or machined part. Fit of the plate in its recess, the top cover in the rim, the palm rest on its shelf, and the riser under the front is unmeasured.
- The top cover is held by eight M2.5 screws from below into blind 2.1 mm pilots, 6.7 mm deep on MX and 3.9 mm on Choc v1. Thread engagement in printed plastic is untested. The cover has a 1.0 mm web between the display pocket and each key window.
- USB plug reach, magnet fit and pull, pad seating, palm screw engagement, and the riser stance. Pads are taken as 2.0 mm proud; the pad part is not chosen.
- On Choc v1 the three USB mouths are open notches through the rim and the top cover. The rim is too low to bridge a plug. The side mouths cross the shoulder at an angle, so their two walls differ in length.
- The palm rest rear and wing-side edges are square in CAD. Edges cut after the dress pass are sharp. Split joinery is unchanged and unvalidated; the riser is one 224 mm piece.
- The interference check uses envelopes. Keycaps are boxes without stems or wobble. Switch housings use nominal sizes.
- The outline is tangent arcs, not curvature-continuous. Curvature steps 7.9 times at the lip-to-corner joint.
- The 4.5 mm sweep under the wall is a plain 45° chamfer, not a convex section.
- `assets/layout.svg` and `assets/layout.png` still show the earlier short palm rest, not the shell. The product page and `assets/product.png` use path-traced renders from `tools/render.py`. The case parts in them come from the CAD model. The keycaps, legends, switch housings, plain PCB, display content and colours are drawn for the picture in `tools/render_parts.py` and are not design data. The renders are not photographs and are not evidence of fit. The `palm` and `palm_screws` keys in `assets/layout.json` describe that earlier rest. See the authority exception in [design.md](design.md).

Known blockers the case model does not resolve. They belong to the PCB and the layout, which this case revision did not change:

- **USB jacks face the wrong way.** `pcb/scripts/support_places.py` seats J1, J2 and J3 at the port datum plus 6 mm, and `pcb/scripts/place.py` gives every fixed part angle 0. The HRO TYPE-C-31-M-12 footprint then has its mouth toward the typist and its signal pads at the board edge. The side jacks also sit on the rounded plank corner. The case keep-outs assume the corrected placement: mouth flush with the PCB rear edge, facing rearward, plug axis along y. Until the PCB matches, the USB fit result describes an intended board, not this one. If the side jacks are turned square to the plank edge, the side tunnels must follow.
- **Component heights are not in the fit gate.** Every non-switch part is on the top copper, under the plate and the top cover. The Choc plate is 1.0 mm above the PCB, lower than the SOD-123 diodes, the TS-1088 switches, the SOIC-8 and the SOT-23 parts. On both variants the J4 socket and the J5, J6 and J7 pin headers are taller than the space under the plate. The closed case gives no access to BOOT, RESET or the J6/J7 ROM jumpers. The fix is on the PCB: move parts to the bottom copper or use low or bottom-entry parts, then add their keep-outs to the gate.
- **Two mounting holes break the board edge.** `holes()` keeps hole centers 4.6 mm inside the deck outline, and Edge.Cuts is 3.4 mm inside it. A 2.7 mm hole then has 0.00 mm of board left at (−139.99, 47.0) and overlaps the edge by 0.11 mm at (105.01, −30.5). The other six have 0.08 to 0.53 mm. The chassis wall is scalloped around each of these holes so the cover boss can pass.

Resolved in this revision: the exported solids were the mirror image of the PCB top view. They are now right-handed, and tests hold the eight holes to the PCB positions.

No Gerber or drill package is published. `docs/bom.csv` is an illustrative list marked `UNVERIFIED_A0_NOT_FOR_ORDER`. The shared UF2 is 418304 bytes and was compiled for this 48-key grid. `firmware/artifacts/build-report.json` records `hardware_tested: false`.

`make check-fabrication` must fail at A0. A passing source-generation CI job means the design files are internally generated and checked; it does not mean a PCB can be ordered. No Gerbers, drill production package, pick-and-place assembly package, regulatory claim or hardware release is published in this milestone.

After the initial GitHub push, inspect the workflow run for each new revision; local checks and remote CI are separate evidence. Do not infer remote CI success from this static file.

Latest local PCB regeneration: both variants have pad-net parity, 169 footprints, and **zero tracks**. Each board has 2 ERC warnings, the DRC counts above, and **329 unconnected items**. These are development blockers, not waived findings. The UF2 compiled for this layout passed the host verifier in `tools/firmware.sh`. That check reads build outputs. It is not a device test.

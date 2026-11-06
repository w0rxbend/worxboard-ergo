# A0 verification and known limitations

This repository is an **engineering starter**, dated 2026-11-06. No physical keyboard, PCB, enclosure, USB isolation circuit or display has been built or tested.

| Area | Evidence | Meaning |
|---|---|---|
| Layout | `tests/test_contracts.py`, `assets/layout.json` | 87 keys, no intersecting keycap envelopes, screw and center-display clearance in the model |
| Electrical source | Circuit contract tests, two KiCad schematic XML netlists | Diode matrix, per-port CC/VBUS nets, mux mapping and boot jumpers defined |
| PCB | `pcb/reports/*-connectivity.json`, ERC and DRC reports | Pad-net parity is checked; boards are **unrouted** and not fabrication approved |
| CAD solids | `cad/validation.json` | 20 exported part models total; valid single solids and positive volume, STEP round-trip |
| Meshes | Test suite loads every STL | 20 watertight positive-volume meshes; 3MF and STEP files also present |
| Native CAD | `cad/freecad-validation.json` | Both FreeCAD 1.1.4 files saved and reopened; four named physical parts per file, valid shapes and matching volume |
| USB selection logic | Compiled host C assertions | Center-first priority, powered-input selection and retained active selection across all input combinations |
| Firmware | `firmware/artifacts/build-report.json` and UF2 | RP2040 ZMK compile/link, LCD driver and Studio USB transport checked against real build outputs |
| Reproducibility | `uv.lock`, `pcb/requirements.lock`, `toolchain.lock.json`, pinned west manifest | Versioned source, dependencies and container digests; upstream Launch preserved as a gitlink |
| Artifact inventory | `assets/artifact-manifest.json`, `assets/SHA256SUMS` | File size and SHA-256 for committed deliverables |

The CAD checks are topology and envelope checks. They do not establish switch retention, stabilizer compatibility, connector fit, display glass/PCB height, print shrinkage, fastener strength, rigidity, ergonomics or assembly clearance against detailed vendor models. The PCB shape shown in STEP is an envelope, not a fully populated board model. Keycaps shown in the assembly are solid envelopes without stems.

Known unfinished work is explicit in [roadmap.md](roadmap.md): both PCB routings and local support-component placement, USB/power measurements, stabilizer and wide Choc keycap selection, display retention, palm-rest attachment, split-print joinery, per-key RGB, tilt/tenting and all physical bring-up. The RGB expansion header is not per-key lighting. The selected host-input arrangement does not include Launch's USB hub.

`make check-fabrication` must fail at A0. A passing source-generation CI job means the design files are internally generated and checked; it does not mean a PCB can be ordered. No Gerbers, drill production package, pick-and-place assembly package, regulatory claim or hardware release is published in this milestone.

After the initial GitHub push, inspect the workflow run for each new revision; local checks and remote CI are separate evidence. Do not infer remote CI success from this static file.

Final local A0 results: seven contract/artifact tests passed. Both variants have **zero ERC findings**, 614 schematic pin assignments matching PCB pads, and 249 footprints. Each board still has **447 unconnected items and 15 DRC errors**. These are development blockers, not waived findings. The shared USB/LCD/Studio UF2 is 423,424 bytes.

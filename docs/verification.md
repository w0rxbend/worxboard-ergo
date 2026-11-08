# A0 verification and known limitations

This repository is an **engineering starter**, dated 2026-11-08. No physical keyboard, PCB, enclosure, USB isolation circuit or display has been built or tested. The split Planck case is a geometry revision of that starter, not a fabrication release.

| Area | Evidence | Meaning |
|---|---|---|
| Layout | `tests/test_contracts.py`, `assets/layout.json` | 48 orthogonal keys in two Planck blocks, no numpad, no intersecting keycap envelopes, screw and display clearance |
| Electrical source | Circuit contract tests, two KiCad schematic XML netlists | Diode matrix, per-port CC/VBUS nets, mux mapping and boot jumpers defined |
| PCB | `pcb/reports/*-connectivity.json`, ERC and DRC reports | Pad-net parity matches; **zero tracks**. Each board has 329 unconnected items. MX DRC is 115 errors and 205 warnings (199 of them silk over copper). Choc DRC is 121 errors and 113 warnings (108 of them silk over copper). ERC is 2 isolated-pin-label warnings per board. Not fabrication approved |
| CAD solids | `cad/validation.json` | 20 exported part models total; valid single solids and positive volume, STEP round-trip |
| Meshes | Test suite loads every STL | 20 watertight positive-volume meshes; 3MF and STEP files also present |
| Native CAD | `cad/freecad-validation.json` | FreeCAD 1.1.4 save/reopen of this export passed, and the four whole-part volumes match `cad/validation.json`. A later report that does not match is stale. |
| USB selection logic | Compiled host C assertions | Center-first priority, powered-input selection and retained active selection across all input combinations |
| Firmware | `firmware/artifacts/build-report.json` and UF2 | RP2040 ZMK compile/link, LCD driver and Studio USB transport checked against real build outputs |
| Reproducibility | `uv.lock`, `pcb/requirements.lock`, `toolchain.lock.json`, pinned west manifest | Versioned source, dependencies and container digests; upstream Launch preserved as a gitlink |
| Artifact inventory | `assets/artifact-manifest.json`, `assets/SHA256SUMS` | File size and SHA-256 for committed deliverables |

The CAD checks are topology and envelope checks. They do not establish switch retention, stabilizer compatibility, connector fit, display glass/PCB height, print shrinkage, fastener strength, rigidity, ergonomics or assembly clearance against detailed vendor models. The PCB shape shown in STEP is an envelope, not a fully populated board model. Keycaps shown in the assembly are solid envelopes without stems.

Known unfinished work is explicit in [roadmap.md](roadmap.md): both PCB routings and local support-component placement, USB/power measurements, display retention, a printed check of the center tab, per-key RGB power, and all physical bring-up. This grid has no key wider than 1u, so the generated plates have no stabilizer slots. The plate has a south window at each key. The RGB header is not a stuffed LED chain, and a chain would exceed USB suspend without a power switch this MCU cannot currently enable. Feet set about 7 degrees of negative tilt. The keywells are not roll-tented. The selected host-input arrangement does not include Launch's USB hub.

No Gerber or drill package is published. `docs/bom.csv` is an illustrative list marked `UNVERIFIED_A0_NOT_FOR_ORDER`. The shared UF2 is 418304 bytes and was compiled for this 48-key grid. `firmware/artifacts/build-report.json` records `hardware_tested: false`.

`make check-fabrication` must fail at A0. A passing source-generation CI job means the design files are internally generated and checked; it does not mean a PCB can be ordered. No Gerbers, drill production package, pick-and-place assembly package, regulatory claim or hardware release is published in this milestone.

After the initial GitHub push, inspect the workflow run for each new revision; local checks and remote CI are separate evidence. Do not infer remote CI success from this static file.

Latest local PCB regeneration: both variants have pad-net parity, 169 footprints, and **zero tracks**. Each board has 2 ERC warnings, the DRC counts above, and **329 unconnected items**. These are development blockers, not waived findings. The UF2 compiled for this layout passed the host verifier in `tools/firmware.sh`. That check reads build outputs. It is not a device test.

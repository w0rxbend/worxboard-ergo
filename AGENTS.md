# Project instructions

This repository is a hardware development starter, revision A0. Never describe unrouted boards or envelope CAD as fabrication-ready.

- `layout/model.py` is authoritative for geometry, key order, and shared holes. `pcb/scripts/design.py` is authoritative for electrical connectivity. Regenerate downstream files after changing either.
- Keep MX and Choc v1 separate; they share logical firmware, not switch footprints or plate height.
- Preserve three independent USB input data pairs and diode-isolated VBUS. Never directly parallel host data/power. RP2040 ROM flashing uses the J6/J7 center-port override, which needs hardware validation.
- CAD checks: valid single solids, watertight meshes, STEP volume round-trip, and native FreeCAD save/reopen reports. Whole and split print models have different readiness; split joinery is unfinished.
- PCB release requires ERC, DRC, zero unconnected nets, schematic parity, manual USB/ground review and hardware prototype evidence. Do not suppress errors to pass a gate.
- Firmware changes require a real pinned ZMK build and meaningful host tests for standalone logic; do not claim device testing from compilation.
- Original sources are GPL-3.0-or-later. Preserve all upstream notices and provenance. Do not copy private sibling repository content or credentials.
- Update `docs/verification.md`, `docs/roadmap.md`, and artifact checksums when generated outputs change.

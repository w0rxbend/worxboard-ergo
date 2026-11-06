# A0 design specification

This is a familiar keyboard in a single enclosure, with separate angled left/right typing fields. It is not an ErgoDox column-stagger design. The supplied gray reference contributes the continuous enclosure and palm rest; Sculpt 1559 contributes the separated hands, angled rows and split spaces. No reference photo is redistributed.

The design uses 19.05 mm pitch for both variants. Left and right key fields rotate +10° and −10° in the model coordinate plane. There are 87 keys: 74 in the typing fields and 13 navigation/system keys. Fn replaces a menu key. Physical row geometry and electrical matrix coordinates are distinct: electrical positions are assigned sequentially into 6×15. Both switch variants use the exact same logical order and firmware.

The center gap is 48 mm at the rotation pivots and grows toward the typist. A landscape nice!view-class 160×68 memory LCD occupies a 36×18 mm nominal module envelope in the center at (0,43). The viewing window is 32×12 mm. These are A0 envelopes, not a supplier fit guarantee; connector, panel glass and breakout stack measurements must be reconciled before A1. The display has its own removable bezel.

The enclosure is approximately 457×185 mm, before the detachable palm rest. It is intentionally a first fit-study enclosure with a service strip behind the keys. Compacting the service strip and curving the palm rest are A1 refinements. This model is flat, without a sculpted dome, negative tilt, or medical/ergonomic certification. Future tenting must use separate angled PCBs or a flexible interconnect, rather than bending an assembled rigid PCB.

| Vertical stack (mm) | MX | Choc v1 |
|---|---:|---:|
| Floor thickness | 2.4 | 2.4 |
| PCB thickness | 1.6 | 1.6 |
| PCB top above enclosure bottom | 8.0 | 8.0 |
| Plate top above PCB top | 5.0 | 2.2 |
| Plate thickness | 1.5 | 1.2 |
| Switch opening | 14.0 square | 13.8 square |

The dimensions above are starting parameters requiring retention and travel coupons. The Choc board is not pin-compatible with MX. The vendored Choc footprint supports PG1350/PG1353 families, but only **PG1350 Choc v1** is the project's selected option; Choc v2 is not validated. Hot-swap pads sit on B.Cu. Switch diodes sit on F.Cu. The plate has provisional stabilizer apertures; PCB stabilizer clearance holes are not yet generated and must be added for the chosen stabilizer family before routing.

All coordinates are millimeters, x to the right, y toward the typist, and z up. KiCad applies a fixed (200,60) offset. Ten M2.5 screw locations are shared between PCB and case. The bosses use 2.1 mm pilot bores for prototype tapping; threaded insert pockets are not included. The plate carries clearance bores and fastens down to those bosses.

Whole parts and left/right split fit models are exported. The split models have no registration joints or fasteners across the cut, and must not be advertised as finished small-printer assemblies. The single-piece board and enclosure exceed many desktop printer beds. The palm rest is a removable blank requiring a chosen attachment method and surface material. Keycap and display solids are design envelopes, not mechanically detailed vendor models.

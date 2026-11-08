# Split Planck design

Each half is a Planck block: four rows, six columns, every key 1u. The left block is Tab through the two spaces. The right block is Y through Enter, with the arrow keys on the bottom row. Lower and Raise are layer keys. There is no number pad and no function row on the base layer.

The halves are splayed 10 degrees about the inner edge, so the valley is wider at the front than at the back. A low rear bay joins them into one PCB and carries the memory LCD and the center USB-C mouth. The side USB-C mouths sit on the rear of each plank. One short palm rest runs across the front and dips at the center so the valley still reads. Rear feet are taller than front feet, which tips the whole deck back about 7 degrees when the soles are on a desk. That is not tenting of the two keywells. Roll-tenting still needs two board planes or a flex, which this revision does not have.

| Vertical stack (mm) | MX | Choc v1 |
|---|---:|---:|
| Floor thickness | 2.4 | 2.4 |
| PCB thickness | 1.6 | 1.6 |
| PCB top above the floor | 8.0 | 8.0 |
| Plate top above PCB top | 5.0 | 2.2 |
| Plate thickness | 1.5 | 1.2 |
| Switch opening | 14.0 square | 13.8 square |
| South LED window | 2.6 × 1.1 | 2.6 × 1.1 |

The deck is about 290 × 138 mm. With the palm rest the outline is about 292 × 142 mm. Eight M2.5 pilots are shared by the chassis, the plate, and the PCB. Two further screws hold the palm rest and do not go through the PCB. Split print files add a rear registration tab. The tab and the palm-rest screws are the joinery; they still need a printed coupon.

Plate openings have sharp corners in the model. See [cnc.md](cnc.md) before posting a toolpath. The PCB files are placement seeds until routing, DRC, and a hardware article exist. Per-key LED windows are in the plate. The electrical source still exposes GP29 on a header rather than a stuffed LED chain. See [electrical.md](electrical.md).

All coordinates are millimeters, x to the right, y toward the typist, and z up. KiCad applies a fixed (200, 60) offset.

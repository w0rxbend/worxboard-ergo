# Prototype machining and printing

This is a shop traveler for the split Planck prototypes. It is not a released manufacturing package. No first article has been cut, printed, or measured. Switch openings in the STEP files have sharp internal corners; a round end mill cannot cut those corners as drawn.

The authoritative solids are generated from `cad/model.py`. Regenerate them with `make cad` after any geometry change. Units are millimeters. The PCB face is the datum: z = 0 is the outside of the chassis floor, and z increases toward the keycaps. Rear soles are 14 mm below the floor and front soles are 3 mm below it. The sole faces are not coplanar. With both on a desk the deck tips back about 7 degrees. Do not bend the PCB to create that tilt.

## What each file is for

| File | Process | Material for a metal article | Printed stand-in |
|---|---|---|---|
| `chassis.step` | CNC, one piece | 6061-T6 | PETG or ASA, or the left/right pair |
| `plate.step` | Laser, waterjet, or CNC with corner relief added later | 6061-T6, 1.5 mm MX or 1.2 mm Choc v1 | PETG coupon first; a printed plate is not the metal article |
| `palm_rest.step` | Print | — | PETG or ASA, bottom face on the bed |
| `display_bezel.step` | Print or small CNC | 6061-T6 optional | PETG |
| `*_left.step` / `*_right.step` | Print, bed under about 250 mm | — | Same plastics |

MX and Choc plates are different thicknesses and different opening sizes. Cut the plate that matches the PCB.

## Chassis, CNC

Deck envelope is about 290 × 138 mm, and with the palm shelf the outline is about 292 × 142 mm. Leave 6 mm of stock outside the finished plan and enough thickness for a 11.5 mm wall plus the 14 mm rear feet. A 40 mm plate is enough if both ops share one datum.

1. Face the top. The finished top of the wall is the plate seat: 11.5 mm above the floor for MX, 9.0 mm for Choc v1.
2. Pocket the interior to a 2.4 mm floor. Wall thickness is 3.2 mm. Boss tops land at the PCB bottom (6.4 mm above the floor).
3. Drill the eight 2.1 mm pilots through the bosses. These are tap drills for M2.5 in aluminum, not heat-set insert holes.
4. Open the three USB-C mouths, 12.5 mm wide and 6.2 mm tall, on the rear wall. Deburr the plug path.
5. Flip the part. Cut the two front soles to 3 mm below the floor and the two rear soles to 14 mm below the floor. They are separate Z levels in one setup.
6. Break the outside edges about 0.3 mm. Confirm the pocket's smallest concave radius against the finishing tool before the program is posted. The model does not yet contain tool-radius relief.
7. Tap M2.5 only after a coupon holds a screw without stripping. Pilot depth stops before the sole of a nearby foot.

## Plate

Openings are 14.0 mm square for MX and 13.8 mm square for Choc v1. This grid has no key wider than 1u, so the generated plates have no stabilizer slots. Each key also has a 2.6 × 1.1 mm south window for a later LED. Screw clearance is 2.7 mm.

Laser or waterjet can hold the square switch corners. A milled plate needs dogbone or other corner relief added from a switch coupon; do not hand-edit the generated STEP and still call it the source model. Minimum web between a switch opening and its LED window is about 1.8 mm, so the LED window wants a 1 mm cutter if it is milled.

## Printing

`chassis_left` and `chassis_right` meet on a tab in the rear apron, 18 mm wide and 18 mm deep, crossing the center. The tab registers the halves. It has not been printed. Print that tab as a small coupon before committing a full half. The palm rest crosses the center with a notch left open and screws to both halves. Those two holes are in the shelf and the rest only. They are not PCB holes. Their coordinates come from `palm_screws()` and are not a measured fit.

Printed pilots are still 2.1 mm. That is the metal tap drill. Heat-set inserts need a larger hole, which is not in this model. Use machine screws only in metal, or redesign the printed boss after a coupon.

The palm rest bottom is flat. The chassis soles are not, so a chassis print needs support under the taller rear feet or a temporary sprue that is cut off. Reorient in the slicer. STL and 3MF are millimeters and carry no print profile. 3MF unit metadata is checked by the test suite.

Suggested first plastic: PETG, 0.2 mm layers, four perimeters. Print a plate coupon of one switch opening and its LED window before a full plate.

## Still required before a shop release

- Tool-radius check and, for a milled plate, corner relief.
- Tap and insert coupons.
- USB plug, switch, and LED-window coupons.
- A printed center-tab coupon.
- First-article measurement of foot height, wall thickness, and plate thickness.

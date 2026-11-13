# Prototype machining and printing

This is a shop traveler for the split Planck prototypes. It is not a released manufacturing package. No first article has been cut, printed, or measured. Switch openings in the STEP files have sharp internal corners; a round end mill cannot cut those corners as drawn.

The authoritative solids are generated from `cad/model.py`. Regenerate them with `make cad` after any geometry change. Units are millimeters. The PCB face is the datum: z = 0 is the outside of the chassis floor, and z increases toward the keycaps. The underside is flat and has no feet. The riser is a separate printed wedge. Do not bend the PCB to create tilt.

## What each file is for

| File | Process | Material for a metal article | Printed stand-in |
|---|---|---|---|
| `chassis.step` | CNC, one piece | 6061-T6 | PETG or ASA, or the left/right pair |
| `plate.step` | Laser, waterjet, or CNC with corner relief added later | 6061-T6, 1.5 mm MX or 1.2 mm Choc v1 | PETG coupon first; a printed plate is not the metal article |
| `palm_rest.step` | Print | — | PETG or ASA, bottom face on the bed |
| `top_cover.step` | Print | — | PETG or ASA, top face on the bed |
| `riser.step` | Print, one piece | — | PETG or ASA, flat top face on the bed |
| `*_left.step` / `*_right.step` | Print, when the bed is under the one-piece size | — | Same plastics |

MX and Choc plates are different thicknesses and different opening sizes. Cut the plate that matches the PCB.

## Chassis, CNC

The shell plan is 303.03 × 223.00 mm. Leave 6 mm of stock outside it. The chassis is 15.5 mm tall for MX and 12.7 mm for Choc v1; the blank must cover that plus facing stock.

1. Face the top. The rim is flat and carries a 2.0 mm fillet, which needs a form tool or 3D surfacing. The plate seat is a recess: 11.5 mm above the outside of the floor for MX, 9.0 mm for Choc v1.
2. Pocket the interior to a 2.4 mm floor. The pocket wall is 3.2 mm inside the deck outline. Cut the valley slot through, and the front shelf down to 6.0 mm. Boss tops land at the PCB bottom (6.4 mm above the floor).
3. Drill the eight 2.8 mm clearance holes through the bosses. The screws thread into the top cover, not the chassis. Cut the 5.4 mm scallop in the wall beside each boss, from the PCB top up.
4. Open the three USB-C tunnels, 14 mm wide, from 5.5 to 13.3 mm above the underside. On Choc v1 they are open at the top. Deburr the plug path.
5. Flip the part. Cut the 4.5 mm bottom sweep, the rear undercut, four pad recesses, four magnet pockets, and fourteen screw counterbores.
6. Break the outside edges about 0.3 mm. Confirm the pocket's smallest concave radius against the finishing tool before the program is posted. The model does not yet contain tool-radius relief.
7. No hole in the chassis is tapped.

## Plate

Openings are 14.0 mm square for MX and 13.8 mm square for Choc v1. This grid has no key wider than 1u, so the generated plates have no stabilizer slots. Each key also has a 2.6 × 1.1 mm south window for a later LED. The eight screw positions are 5.4 mm holes that pass the top-cover bosses. Each plate has three 14 mm notches on the rear edge over the USB jacks.

Laser or waterjet can hold the square switch corners. A milled plate needs dogbone or other corner relief added from a switch coupon; do not hand-edit the generated STEP and still call it the source model. Minimum web between a switch opening and its LED window is about 1.8 mm, so the LED window wants a 1 mm cutter if it is milled.

## Printing

`chassis_left` and `chassis_right` meet on a tab in the rear apron, 18 mm wide and 18 mm deep, crossing the center. The tab registers the halves. It has not been printed. Print that tab as a small coupon before committing a full half. The palm rest crosses the center and screws to both halves, three screws each. Print it whole if the bed allows, so it bridges the split. Those six holes are in the shelf and the rest only. They are not PCB holes. Their coordinates are `PALM_SCREWS` in `cad/model.py` and are not a measured fit.

The printed pilots in the top cover and the palm rest are 2.1 mm, for a thread-forming screw after a coupon. Heat-set inserts need a larger hole, which is not in this model.

The chassis and palm rest bottoms are flat. The rim and the top cover are flat. The palm top will show layer steps. No slicer run backs this. Reorient in the slicer. STL and 3MF are millimeters and carry no print profile. 3MF unit metadata is checked by the test suite.

Suggested first plastic: PETG, 0.2 mm layers, four perimeters. Print a plate coupon of one switch opening and its LED window before a full plate.

## Still required before a shop release

- Tool-radius check and, for a milled plate, corner relief.
- Tap and insert coupons.
- USB plug, switch, and LED-window coupons.
- A printed center-tab coupon.
- A USB relief, magnet pocket, and pad recess coupon.
- First-article measurement of rim height, wall thickness, and plate thickness.

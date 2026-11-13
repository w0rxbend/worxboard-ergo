# Split Planck design

Each half is a Planck block: four rows, six columns, every key 1u. The left block is Tab through the two spaces. The right block is Y through Enter, with the arrow keys on the bottom row. Lower and Raise are layer keys. There is no number pad and no function row on the base layer.

The halves are splayed 10 degrees about the inner edge, so the valley is wider at the front than at the back. A low rear bay joins them into one PCB and carries the memory LCD and the center USB-C mouth. The side USB-C mouths sit on the rear of each plank. One smooth shell wraps both planks and the bay, in the manner of the Microsoft Sculpt. A slot through the valley keeps the wells apart. A flat top cover fills the rim, so the keys rise through one top skin. A full-width palm rest sits on the front shelf. The chassis has no feet and sits flat. A separate magnetic riser under the front edge lifts the front 6.7 degrees. That is not tenting of the two keywells. Roll-tenting still needs two board planes or a flex, which this revision does not have.

| Vertical stack (mm) | MX | Choc v1 |
|---|---:|---:|
| Floor thickness | 2.4 | 2.4 |
| PCB thickness | 1.6 | 1.6 |
| PCB top above the floor | 8.0 | 8.0 |
| Plate top above PCB top | 5.0 | 2.2 |
| Plate thickness | 1.5 | 1.2 |
| Switch opening | 14.0 square | 13.8 square |
| South LED window | 2.6 × 1.1 | 2.6 × 1.1 |

The deck is about 290 × 138 mm. The shell plan is 303.03 × 223.00 mm. Eight M2.5 screws come up from the underside. Each passes a chassis boss and a PCB hole and threads into a boss on the top cover. That clamps the PCB and traps the plate. Six further screws hold the palm rest from below and do not go through the PCB. Split print files add a rear registration tab. The tab and the screws are the joinery; they still need a printed coupon.

## Case shell

The shell is envelope CAD at revision A0. It is not fabrication-ready. No part has been sliced, printed, cut, or measured. `cad/model.py` holds every number below. `layout/model.py` still owns the deck outline, the keys, the eight shared holes, and the ports, and none of those changed.

| Shell (mm) | MX | Choc v1 |
|---|---:|---:|
| Chassis plan | 303.03 × 223.00 | 303.03 × 223.00 |
| Chassis height | 15.50 | 12.70 |
| Rim above the plate top, flat | 2.5 | 2.5 |
| Skin outside the deck outline, minimum | 5.89 | 5.89 |
| Valley wall / front fence, to the plate recess | 2.75 / 2.64 | 2.75 / 2.64 |
| Web between the valley slot and the palm zone | 3.24 | 3.24 |
| Valley slot | about 8 to 25 wide, 53.6 long | same |
| Top cover, sheet 2.5 thick; height with its bosses | 288.87 × 136.40 × 7.50 | 288.87 × 136.40 × 4.70 |
| Palm rest | 302.74 × 88.33 × 19.00 | 302.74 × 88.33 × 10.20 |
| Palm depth at x = 0 / 70 / 120 / 135 | 67.0 / 68.5 / 65.0 / 58.0 | same |
| Palm top: fall from rear edge to lip, mean slope | 6.0, 5.1° to 5.7° | same |
| Palm rear edge below the keycap tops | 2.5 | 2.5 |
| Riser | 224.00 × 33.21 × 21.25 | same |

- **Frame.** The model is built in layout coordinates, y toward the typist, the way KiCad draws the board from the top. With z up that frame is left-handed. `make()` mirrors every solid once at the end. Exported STEP, STL, 3MF and FCStd are right-handed: x right, y away from the typist, z up. A PCB hole at layout (x, y) is at (x, −y) in the export. `chassis_left` is the typist's left.
- **Plan.** Thirty-four tangent arcs. The front lip is one arc of radius 395 mm and the rear is one arc of radius 343.5 mm. Each side is sixteen arcs fitted to a spline through two waypoints. No edge is straight and no joint has a corner. The smallest radius is 40.5 mm. The curvature still steps: 7.9 times where the lip meets the front corner, 3.4 times or less elsewhere. Guards in `make()` stop the build if the shell, the slot, the palm zone, the riser, or a pad drifts.
- **Top.** The rim is flat, 2.5 mm above the plate top. The earlier crown is gone; on an FDM print it would show as contour steps. The top cover is a 2.5 mm inlay that drops into the rim with a 0.2 mm gap and sits flush. It has one rounded window per key block, 1.0 mm outside the 1u cells, and the 32 × 12 mm display window with a pocket for the module behind it. The display bezel is no longer a separate part. A 5.0 mm boss under each screw position passes a 5.4 mm plate hole and lands on the PCB top. Its blind 2.1 mm pilot leaves 0.8 mm of unbroken top. Pilot depth is 6.7 mm on MX and 3.9 mm on Choc v1.
- **Edges.** 2.0 mm top fillet, a 4.5 mm 45° sweep under the side wall, 1.5 mm fillet and chamfer on the slot. The palm top is 32 chords, 0.33° apart, and its 3.0 mm lip roll is 16 chords, 5° apart. The palm rear edge and wing-side edges are square: fillets there fail the STEP round-trip gate. Edges cut after the dress pass, such as the plate recess and the fence, are sharp.
- **Palm rest.** It bears on the 6.0 mm shelf, with a 0.8 mm chamfer at its foot as the shadow line and a deliberate 0.8 mm reveal to the front fence. The top is level at the rear edge and falls 6.0 mm to the lip on one arc, on both variants. Six blind 2.1 mm pilots take screws from below, three each side; the outer pair is at x = ±135.
- **USB.** The keep-outs assume a receptacle on the PCB top, mouth flush with the PCB rear edge, facing rearward. Each port has a 14 mm wide tunnel from the mouth out through the wall and the skin, floor 5.5 mm and ceiling 13.3 mm above the underside, with rounded floor corners. On MX 2.2 mm of rim bridges it. On Choc v1 the rim top is 12.7 mm, so the tunnel is an open notch and the top cover is notched too. The plate has a 14 mm notch that runs 8 mm in front of each mouth. A receptacle body of 8.94 × 7.3 × 3.26 mm and a plug with a 12.35 × 6.5 mm overmold are in the fit gate. No plug has been tried. The PCB does not place the jacks this way yet; see [verification.md](verification.md).
- **Underside.** Four 10.2 × 1.0 mm pad recesses, at (±100, 116.6) and (±118, −42) in layout coordinates. Pads are taken to stand 2.0 mm proud. Four 6.1 × 3.1 mm magnet pockets. Fourteen 2.8 mm screw holes with 5.2 × 2.2 mm counterbores: eight for the cover, six for the palm rest. The rear edge lies behind the rear pads, so a shallow undercut holds it 0.5 mm off the desk when the board stands on the riser.
- **Signature.** The owner's signature is a laser engraving on the underside, under the middle of the right well: "Oleksandr", a one-stroke flourish for the B, and "Signature Edition". It is about 95 × 72 mm, turned with the well, and reads from below. It is a surface mark. It is not in the solid model and it does not thin the 2.4 mm floor. The artwork is filled vector outlines in `cad/exports/laser/`: `signature.svg` alone and `chassis-underside.svg` placed on the underside outline, each with a PDF and a 4000 px PNG. The nearest screw counterbore is 6 mm away. Source: `tools/signature.py`; regenerate with `make laser`.
- **Riser.** A band that follows the lip arc, 224 mm wide and 18 mm deep, 6 mm inside the lip. Two pockets in its top drop over the front pads and locate it. Four magnet pairs hold it. Its sole has two pad recesses and stands 2.0 mm off the desk, the height of its pads.
- **Not modeled.** A real dome, tenting, stepped key heights, a roofed USB mouth on Choc v1, palm hollowing, textures, the pads themselves, snap features. PCB components are not in the fit gate. The riser, the pads and the split halves are not in the native FreeCAD file.

Authority exception. `AGENTS.md` makes `layout/model.py` the owner of geometry and shared holes. The shell plan and the palm-screw, magnet and pad positions live in `cad/model.py` for now. `layout.palm_outline()` and `layout.palm_screws()` still describe the earlier short palm rest, so the `palm` and `palm_screws` keys in `assets/layout.json` and `assets/layout.svg` are stale. They do not draw the shell yet.

Plate openings have sharp corners in the model. See [cnc.md](cnc.md) before posting a toolpath. The PCB files are placement seeds until routing, DRC, and a hardware article exist. Per-key LED windows are in the plate. The electrical source still exposes GP29 on a header rather than a stuffed LED chain. See [electrical.md](electrical.md).

Layout and PCB coordinates are millimeters, x to the right and y toward the typist. KiCad applies a fixed (200, 60) offset. The CAD export flips y, as described above, and has z up.

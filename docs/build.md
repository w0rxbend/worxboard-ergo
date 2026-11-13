# How to build this keyboard

This is the shop and bench sequence for the 48-key split Planck. It uses the files in this repository. It is not a released manufacturing package. No board, case, or cable arrangement has been built or measured. The visual introduction is the [microsite](../site/index.html).

Read this page once, then follow the sections in order. Do the coupons before a full case. Do not send the PCB to a fabricator from the files that are here today.

## What you can make now, and what you cannot

| Work | Files that exist | Status |
|---|---|---|
| Review the shape | `assets/layout.svg`, `cad/exports/*/assembly.step` | Geometry checked. Not a fit test against real switches. |
| CNC the chassis and, with the right process, the plate | `cad/exports/<variant>/*.step` | Traveler in [cnc.md](cnc.md). No posted toolpath. No first article. |
| 3D-print the case, plate, top cover, and palm rest | Matching `.stl` and `.3mf` files | Watertight meshes. No validated slicer profile. The center tab is not a measured joint. |
| Read the circuit and the placed parts | `pcb/<variant>/*.kicad_sch`, `*.kicad_pcb`, `docs/bom.csv` | Schematic and placement seed. **Zero copper tracks.** |
| Order an assembled PCB | Gerbers, drills, stackup, paste, centroid | **Not in this repository. Do not invent them from the unrouted board.** |
| Flash firmware | `firmware/artifacts/worxboard-ergo.uf2` after `make firmware` | Compile check only. No keyboard has been plugged in. |

`make check-fabrication` is required to fail until routing, USB review, and a physical bring-up exist. Do not weaken that gate to get a green build.

## 1. Choose one switch family

MX and Choc v1 share the key map and the firmware. They do not share the plate, the plate thickness, or the PCB.

| | MX | Choc v1 |
|---|---|---|
| Switches | Cherry MX compatible, 48 pieces | Kailh Choc v1 / PG1350, 48 pieces |
| Hot-swap sockets | Kailh MX | Kailh Choc v1 |
| Plate | `cad/exports/mx/plate.step` | `cad/exports/choc/plate.step` |
| Plate thickness | 1.5 mm | 1.2 mm |
| Switch opening | 14.0 mm square | 13.8 mm square |
| PCB | `pcb/mx/` | `pcb/choc/` |
| Wall top above the chassis floor | 11.5 mm | 9.0 mm |

Every key is 1u, including Tab, Backspace, both Shifts, Enter, and the two Space keys. Buy 48 keycaps of 1u. This model has no stabilizer.

Keycaps in the assembly STEP are solid blocks without stems. Print them only as a visual check.

## 2. Run the checks before you cut material

From a clean checkout, with uv, Docker, and FreeCAD 1.1:

```sh
uv sync --locked
make generate
make cad
make native
make test
make pcb
make firmware
make manifest
make check-fabrication   # this exit is failure, on purpose
```

`make cad` checks each solid, writes STEP, STL, and 3MF, and round-trips the STEP volume. `make native` reopens the whole parts in FreeCAD. `make test` loads every mesh. `make pcb` regenerates the unrouted boards and writes ERC/DRC reports. It does not autoroute. `make firmware` builds the pinned ZMK image. The last command must print `Fabrication blocked` and exit non-zero.

Current evidence is in [verification.md](verification.md). If you change `layout/model.py` or `pcb/scripts/design.py`, regenerate before you trust the exports.

## 3. 3D printing

Units are millimeters. The 3MF files record `unit="millimeter"`. They contain no temperatures, infill, or supports.

Print the variant you chose. The one-piece chassis is 303 × 223 mm and needs a 350 mm class bed. The split chassis halves are 169.5 and 151.5 × 223 mm and need a bed of about 235 mm or more in one direction. The one-piece top cover is 289 × 136 mm.

| Part | One piece | Split | Face on the bed |
|---|---|---|---|
| Chassis | `chassis.stl` | `chassis_left.stl`, `chassis_right.stl` | The flat underside. It has no feet. |
| Plate | `plate.stl` | `plate_left.stl`, `plate_right.stl` | Flat face down, after a coupon |
| Palm rest | `palm_rest.stl` | `palm_rest_left.stl`, `palm_rest_right.stl` | The flat bottom |
| Top cover | `top_cover.stl` | `top_cover_left.stl`, `top_cover_right.stl` | The top face, bosses up |
| Riser, optional | `riser.stl` | same file; one 224 mm piece | The flat top face |

Suggested first plastic, not a qualified profile: PETG or ASA, 0.2 mm layers, four perimeters, 20% infill on the chassis. Reorient in the slicer. The chassis and the palm rest have flat bottoms. The rim and the top cover are flat. The palm top will show layer steps. No slicer run backs any of this.

`chassis_left` keeps an 18 mm by 18 mm tab in the rear apron. `chassis_right` has the matching recess. That tab has not been printed. Before a full pair, print only that corner and check that the halves meet without force and without a gap you can see. If the tab is tight or loose, change the model and regenerate. Do not sand the source of truth away and still call the file current.

All screws enter from the underside. The chassis holes are 2.8 mm clearance with a 5.2 × 2.2 mm counterbore. Eight of them pass the PCB and meet blind 2.1 mm pilots in the top-cover bosses, 6.7 mm deep on MX and 3.9 mm on Choc v1. Six pass the shelf and meet 2.1 mm blind pilots, 6 mm deep, in the palm rest. The 2.1 mm pilots are for a thread-forming screw after a coupon. They are too small for heat-set inserts. Their coordinates are `PALM_SCREWS` in `cad/model.py` and are not a measured fit.

### Print coupons, in this order

1. One switch opening and its 2.6 × 1.1 mm south window, cut from the plate mesh or printed as a small excerpt. The switch must clip, travel, and release. The window is for a later LED. No LED is stuffed on this PCB.
2. The center-tab corner, left and right.
3. One USB tunnel: 14 mm wide, 7.8 mm tall, roofed on MX and open on Choc v1. A real USB-C plug must pass it without lifting the board. The PCB does not place the jacks at these mouths yet; see [verification.md](verification.md).
4. One top-cover boss with its screw from below.
5. Only then, the full chassis, plate, top cover, and palm rest.

Square switch corners will be rounded by a printer nozzle. That is acceptable for a fit check. It is not the metal plate.

## 4. CNC

Follow [cnc.md](cnc.md) for the operation order. Short form:

1. Stock is 6061-T6. Leave about 6 mm outside the 303.03 × 223.00 mm shell plan. The chassis is 15.5 mm tall for MX and 12.7 mm for Choc v1, and has no feet.
2. The plate seat is 11.5 mm above the outside of the floor for MX and 9.0 mm for Choc v1. The flat rim rises 4.0 mm above it on MX and 3.7 mm on Choc v1. Pocket to a 2.4 mm floor. Walls are 3.2 mm. Boss tops meet the bottom of the 1.6 mm PCB.
3. Drill eight 2.8 mm clearance holes through the bosses and counterbore them from below. The thread is in the top cover.
4. Open three USB-C tunnels on the rear wall, 14 mm wide. Deburr the plug path.
5. Flip. Cut the bottom sweep, the rear undercut, the pad recesses, the magnet pockets, and the fourteen screw counterbores. The chassis sits flat. Do not bend the PCB to create an angle.
6. Break outside edges about 0.3 mm.

The plate openings are sharp squares. Laser or waterjet can cut them. A round end mill cannot. Add dogbones only after a switch coupon, and do not hand-edit the generated STEP and still treat it as the source model. The LED window wants about a 1 mm cutter if it is milled. The web beside it is about 1.8 mm.

There is no posted G-code in this repository. The STEP is the geometry input to your CAM, after you choose a tool and confirm the smallest inside radius.

## 5. PCB and PCBA

Do not order boards from this revision.

What you have:

- KiCad 10.0.7 projects: `pcb/mx/worxboard-ergo-mx.kicad_pro` and `pcb/choc/worxboard-ergo-choc.kicad_pro`.
- Schematics, XML netlists, and placed footprints. Each board has 169 footprints: 48 switches, 48 diodes, the RP2040 support circuit, three USB-C receptacles, and eight mounting holes.
- An illustrative BOM, `docs/bom.csv`. Every line is `UNVERIFIED_A0_NOT_FOR_ORDER`. LCSC numbers are references, not a cart.
- `placement.json` in each PCB directory. That is a development coordinate list in layout millimeters. It is not a centroid file, and it has no rotation-checked assembly drawing.

What is missing, and why a fabricator cannot build it yet:

- The boards have **no routed tracks**. Latest reports: 329 unconnected items on each board. MX DRC has 115 errors and 205 warnings. Choc DRC has 121 errors and 113 warnings. ERC has 2 isolated-pin-label warnings per board.
- No reviewed four-layer stackup, no ground plane, no USB differential geometry.
- No Gerbers, drills, paste layer, or pick-and-place package. Do not export those from the unrouted board.
- No current measurement of the diode-OR VBUS path, and no hardware check of the J6/J7 ROM override.
- Per-key LEDs are windows in the plate only. Do not add a SK6812 chain. GP29 is a header, and a stuffed chain would exceed USB suspend.

When a later revision actually routes both boards, the acceptance bar is in [roadmap.md](roadmap.md) gate A2: zero ERC errors, zero DRC errors, zero unconnected nets, schematic parity, a reviewed stackup, and a reviewed BOM. Physical bring-up is gate A3. Only then does gate A5 allow Gerbers.

Until that work, the useful electrical review is to open the schematic and read [electrical.md](electrical.md). Three USB-C jacks are alternate cable positions. Their data pairs stay separate through a TS3USB3031 mux. Their VBUS pins meet only through Schottky diodes. Never tie the host data pins or the host VBUS pins together.

## 6. Assemble, after a real PCB exists

Skip this section for a plastic fit check that has no board. The stack below is the model. Measure it against the parts you actually received before you tap the bosses.

1. Chassis, floor down. The floor is 2.4 mm. The PCB sits on the bosses, its top 8.0 mm above the outside of the floor.
2. PCB, component side up, on the bosses. Do not fit its screws yet.
3. Plate. MX plate is 1.5 mm with its top 5.0 mm above the PCB. Choc plate is 1.2 mm with its top 2.2 mm above the PCB.
4. Switches, clipped in from above, pins seated in the hot-swap sockets. Diodes are on the PCB, cathode toward the row.
5. Display module in the rear bay, then `top_cover` into the rim. Its window is 32 × 12 mm. Confirm the real module before you trust that window. Eight M2.5 screws from the underside pass the chassis bosses and the 2.7 mm PCB holes into the cover bosses. Length is not specified here. Measure the stack.
6. Palm rest on the front shelf, six screws from below, three each side. Those screws do not go through the PCB.
7. 1u keycaps.
8. Four pads in the 10.2 mm underside recesses. The pads are not modeled. The optional riser drops over the two front pads and holds with four magnet pairs.

Split printed halves: join on the rear tab, then the palm rest bridges the front. Treat a first pair as a test article.

## 7. Power and firmware

Do this on a bench supply with a current limit before you trust a USB host. Confirm 3.3 V and 1.1 V. Confirm that a powered port does not back-feed another port's VBUS. Details and the mux table are in [electrical.md](electrical.md).

Normal run: both J6 and J7 shunts on pins 1–2.

ROM flashing, only after the jumper wiring has been checked on the real board:

1. Disconnect USB. Do not move a shunt while the board is powered.
2. Move both J6 and J7 to pins 2–3.
3. Connect only the center USB-C port.
4. Hold BOOT, press RESET, and copy the UF2 to the `RPI-RP2` drive.
5. Disconnect USB. Move both shunts back to pins 1–2.

SWD is the recovery path if that sequence does not enumerate. The first programming method for a new board is SWD, not the ROM port.

The image shows BASE, LOWER, and RAISE on the memory LCD.

- BASE is the printed legends.
- Hold Lower for the number row and F1–F11.
- Hold Raise, then Esc, for the bootloader. Hold Raise, then Tab, for reset.

The UF2 in `firmware/artifacts/worxboard-ergo.uf2` is 418304 bytes and was compiled for this 48-key grid. Rebuild it with `make firmware` if you change the keymap. A successful flash is not evidence that the keys, the display, or the three ports work. No keyboard has been plugged in.

## 8. Bring-up checklist

Record the result of each line. A missing line means the keyboard is not done.

- [ ] Switch coupon clips and releases in the plate material you will use.
- [ ] USB plug passes each mouth.
- [ ] Center tab coupon fits.
- [ ] The chassis sits on its four pads without rocking, flat and on the riser.
- [ ] PCB has zero unconnected nets and a reviewed USB layout. Gerbers come from that board only.
- [ ] 3.3 V and 1.1 V are in range. No VBUS back-feed.
- [ ] J6/J7 ROM override and the restore to pins 1–2 both work.
- [ ] Each of the 48 keys scans. Diodes are oriented cathode to the row.
- [ ] Each USB port enumerates alone, survives a reconnect, and does not fight another connected port.
- [ ] LCD reads BASE, LOWER, and RAISE.
- [ ] Studio can remap a key and the remap survives a replug.

## Illustrative shopping list

Do not paste this into a distributor cart. Confirm each line against a current datasheet.

- 48 switches and 48 hot-swap sockets, one family only.
- 48 keycaps, 1u. Two of them are Space.
- 1 memory LCD module of the nice!view class, 160×68, SPI. Measure it against the 36 × 18 mm pocket before you commit the top cover.
- M2.5 screws: eight for the top cover and six for the palm rest. Length from measurement.
- Four 10 mm pads for the chassis. For the riser: eight 6 × 3 mm disc magnets and two more pads. Fit is unverified.
- One USB-C cable. The three jacks are three places to plug in, not three computers at once.
- PCB, stencil, and assembly: blocked until gate A2 and a reviewed BOM.

The full reference list with footprints is [bom.csv](bom.csv). The case process is [cnc.md](cnc.md). The circuit is [electrical.md](electrical.md). The acceptance gates are [roadmap.md](roadmap.md).

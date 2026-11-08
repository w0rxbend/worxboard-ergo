# How to build this keyboard

This is the shop and bench sequence for the 48-key split Planck. It uses the files in this repository. It is not a released manufacturing package. No board, case, or cable arrangement has been built or measured. The visual introduction is the [microsite](../site/index.html).

Read this page once, then follow the sections in order. Do the coupons before a full case. Do not send the PCB to a fabricator from the files that are here today.

## What you can make now, and what you cannot

| Work | Files that exist | Status |
|---|---|---|
| Review the shape | `assets/layout.svg`, `cad/exports/*/assembly.step` | Geometry checked. Not a fit test against real switches. |
| CNC the chassis and, with the right process, the plate | `cad/exports/<variant>/*.step` | Traveler in [cnc.md](cnc.md). No posted toolpath. No first article. |
| 3D-print the case, plate, palm rest, and bezel | Matching `.stl` and `.3mf` files | Watertight meshes. No validated slicer profile. The center tab is not a measured joint. |
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

Print the variant you chose. A bed under about 250 mm can use the split files. A larger bed can use the one-piece files.

| Part | One piece | Split, bed under 250 mm | Face on the bed |
|---|---|---|---|
| Chassis | `chassis.stl` | `chassis_left.stl`, `chassis_right.stl` | Not the sole face. The rear feet hang 14 mm below the floor. |
| Plate | `plate.stl` | `plate_left.stl`, `plate_right.stl` | Flat face down, after a coupon |
| Palm rest | `palm_rest.stl` | `palm_rest_left.stl`, `palm_rest_right.stl` | The flat bottom |
| Display bezel | `display_bezel.stl` | same file; it is small | Flat face down |

Suggested first plastic, not a qualified profile: PETG or ASA, 0.2 mm layers, four perimeters, 20% infill on the chassis. Reorient in the slicer. Add support under the rear feet, or print a sprue you will cut off. The palm rest does not need that support.

`chassis_left` keeps an 18 mm by 18 mm tab in the rear apron. `chassis_right` has the matching recess. That tab has not been printed. Before a full pair, print only that corner and check that the halves meet without force and without a gap you can see. If the tab is tight or loose, change the model and regenerate. Do not sand the source of truth away and still call the file current.

The 2.1 mm holes are tap drills for M2.5 in aluminum. They are too small for heat-set inserts. A printed chassis uses the holes only as pilots for a later metal article, or you redesign the boss after a coupon. The palm-rest holes are 2.2 mm in the shelf and 2.8 mm in the rest. Their coordinates come from `palm_screws()` and are not a measured fit.

### Print coupons, in this order

1. One switch opening and its 2.6 × 1.1 mm south window, cut from the plate mesh or printed as a small excerpt. The switch must clip, travel, and release. The window is for a later LED. No LED is stuffed on this PCB.
2. The center-tab corner, left and right.
3. One USB mouth: 12.5 mm wide and 6.2 mm tall. A real USB-C plug must pass the deburred opening without lifting the board.
4. Only then, the full chassis, plate, palm rest, and bezel.

Square switch corners will be rounded by a printer nozzle. That is acceptable for a fit check. It is not the metal plate.

## 4. CNC

Follow [cnc.md](cnc.md) for the operation order. Short form:

1. Stock is 6061-T6. Leave about 6 mm outside the 290 × 138 mm deck. The rear feet need 14 mm below the 2.4 mm floor, so plan the blank thickness before the flip.
2. MX wall top is 11.5 mm above the floor. Choc v1 wall top is 9.0 mm. Pocket to a 2.4 mm floor. Walls are 3.2 mm. Boss tops meet the bottom of the 1.6 mm PCB.
3. Drill eight 2.1 mm pilots. Tap M2.5 only after a coupon holds a screw. These are not insert holes.
4. Open three USB-C mouths on the rear wall, 12.5 × 6.2 mm. Deburr the plug path.
5. Flip. Cut front soles to 3 mm below the floor and rear soles to 14 mm below the floor. On a desk the deck tips back about 7°. Do not bend the PCB to create that angle.
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
2. PCB, component side up. Eight M2.5 screws pass through the plate and the 2.7 mm PCB holes into the tapped bosses. Length is not specified here. Measure the stack.
3. Plate. MX plate is 1.5 mm with its top 5.0 mm above the PCB. Choc plate is 1.2 mm with its top 2.2 mm above the PCB.
4. Switches, clipped in from above, pins seated in the hot-swap sockets. Diodes are on the PCB, cathode toward the row.
5. Display module in the rear bay, then `display_bezel`. The bezel opening is 32 × 12 mm. Confirm the real module before you trust that window.
6. Palm rest on the front shelf, two screws, one each side. Those screws do not go through the PCB.
7. 1u keycaps.
8. Rubber feet are not modeled. The aluminum soles are the feet.

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
- [ ] Foot heights measure 3 mm front and 14 mm rear, and the deck sits without rocking.
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
- 1 memory LCD module of the nice!view class, 160×68, SPI. Measure it against the 36 × 18 mm pocket before you commit the bezel.
- M2.5 screws for eight plate bosses and two palm screws. Length from measurement.
- One USB-C cable. The three jacks are three places to plug in, not three computers at once.
- PCB, stencil, and assembly: blocked until gate A2 and a reviewed BOM.

The full reference list with footprints is [bom.csv](bom.csv). The case process is [cnc.md](cnc.md). The circuit is [electrical.md](electrical.md). The acceptance gates are [roadmap.md](roadmap.md).

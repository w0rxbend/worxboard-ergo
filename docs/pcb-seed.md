# Working with the KiCad boards

Open `pcb/mx/worxboard-ergo-mx.kicad_pro` or `pcb/choc/worxboard-ergo-choc.kicad_pro` with KiCad 10.0.7. Each project holds the schematic, the XML netlist, the routed four-layer board, the project library tables and the placement coordinates. Library files under `pcb/lib/` are committed; stock KiCad libraries are required for regeneration.

The boards are generated, not drawn. A hand edit in KiCad is overwritten by the next `make pcb`. Change the scripts instead:

| Script | Owns |
|---|---|
| `layout/model.py` | Key positions, board outline, mounting holes, USB mouths |
| `pcb/scripts/design.py` | Parts, pins and nets: the electrical source |
| `pcb/scripts/support_places.py` | Seats of every part that is not a key or a hole |
| `pcb/scripts/rules.py` | Stackup, design rules, net classes, USB pair geometry |
| `pcb/scripts/place.py` | Footprints, sides, Edge.Cuts; writes `pcb/.work/<v>/seed.kicad_pcb` |
| `pcb/scripts/route.py` | Scripted copper, planes, the autorouter hand-off, completion, stitching |
| `pcb/scripts/maze.py` | The grid router `route.py` uses |
| `pcb/scripts/fab.py` | PCBWay BOM, centroid and order sheet |

## Pipeline

1. `gen_sch.py` writes the schematic from `design.py`; `kicad-cli` exports its netlist.
2. `place.py` loads every footprint, copies the schematic fields and pad nets, and seats the parts. Every SMD part is on B.Cu. The USB-C receptacles and the through-hole headers are on F.Cu.
3. `route.py <v> critical` routes, in this order: the crystal, QSPI and RP2040-side USB nets; the exposed-pad and plane vias; each receptacle pair on F.Cu over the In1 ground plane, joined to its second pad, ESD clamp and mux pins inside small windows; VBUS and VSYS. It adds the planes and a rule area over each receptacle shell, then writes `pcb/.work/<v>/board.dsn`.
4. `make pcb-autoroute` (Java, network for the first jar download) runs Freerouting 2.5.0 on that DSN and commits `pcb/<v>/autoroute.ses` and `pcb/<v>/autoroute.json`. The JSON holds the DSN hash, so a stale session is refused.
5. `route.py <v> finish` imports the session, joins anything the autorouter left open with the grid router, adds ground stitching vias and the B.Cu ground pour, fills the zones and saves the project board.
6. `check.py` compares every schematic pin net with the board pad; `kicad-cli` writes ERC and DRC (with `--schematic-parity`) under `pcb/reports/`.

`make pcb` runs 1–3, 5 and 6 and needs neither Java nor the network. Run `make pcb-autoroute` first whenever placement or scripted copper changes; `finish` stops with a message if you forget. `python3 tools/check_pcb_reports.py` gates the reports. `make pcb-fab` writes the PCBWay package under `pcb/fab/`.

## Rules and stackup

`pcb/scripts/rules.py` cites the sources. In short: PCBWay's standard 4-layer 1.6 mm build, 1 oz finished copper on all layers, 7628 prepreg 0.1855 mm (Dk 4.74) under each outer layer. 0.15 mm clearance, 0.20 mm signal track, 0.40 mm power track, 0.6/0.3 mm vias, 0.30 mm copper to edge. USB pairs 0.22 mm wide, 0.15 mm gap, about 90 Ω by the IPC-2141A closed form. Layer use: F.Cu signals and USB pairs, In1.Cu solid ground, In2.Cu ground with a 3V3 area under the controller bay, B.Cu signals and a ground pour.

## Matrix order

The source matrix order is independent of physical row stagger. For switch `SK101 + i`, the corresponding diode is `D101 + i`, and the logical matrix position is `(i // 15, i % 15)`. This order also drives ZMK's matrix transform and all keymap layers.

Clean reports mean the design files agree with each other and with the rules. They do not mean a board works. See [verification.md](verification.md) for what has and has not been checked.

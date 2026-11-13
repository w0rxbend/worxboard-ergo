# SPDX-License-Identifier: GPL-3.0-or-later
"""PCBWay assembly files for one routed board: BOM, centroid and the order sheet.

    fab.py <variant>   ->  pcb/fab/<variant>/{bom-pcbway.csv, centroid-pcbway.csv, ORDER.md}

Column headers follow PCBWay's sample BOM and sample centroid file (read 2026-11-13).
tools/pcb_fab.sh plots the Gerbers, drills, drawings and renders beside them.
"""
import csv,sys
from collections import defaultdict
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from pcb.scripts import rules
from pcb.scripts.design import design,sourcing

BOM_COLUMNS=('Item #','Designator','Qty','Manufacturer','Mfg Part #','Description / Value','Package/Footprint','Type',
             'Your Instructions / Notes')
CENTROID_COLUMNS=('Designator','Footprint','Mid X','Mid Y','Ref X','Ref Y','Pad X','Pad Y','TB','Rotation','Comment')
CUSTOMER='DNS - fitted by the customer after delivery'
UNVERIFIED='PART NUMBER NOT VERIFIED - confirm before ordering'
SOCKET='Hot-swap socket on the bottom side. The key switch is not supplied and not fitted.'

def is_smd(fp):return bool(fp.GetAttributes()&p.FP_SMD) or all(pad.GetDrillSizeX()==0 for pad in fp.Pads() if pad.GetNumber())

def bom_lines(parts):
    """One line per distinct part: [(part, [refs])], assembler-fitted lines first."""
    groups=defaultdict(list)
    for part in parts:
        if part.in_bom:groups[part.dnp,sourcing(part),part.footprint,'' if part.ref.startswith('SK') else part.value].append(part)
    return [(members[0],[m.ref for m in members]) for _,members in sorted(groups.items(),key=lambda g:(g[0][0],g[1][0].ref))]

def write_bom(folder,lines,fps):
    with (folder/'bom-pcbway.csv').open('w',newline='') as handle:
        writer=csv.writer(handle,lineterminator='\n');writer.writerow(BOM_COLUMNS)
        for item,(part,refs) in enumerate(lines,1):
            maker,mpn,verified=sourcing(part)
            notes=[CUSTOMER] if part.dnp else []
            if part.ref.startswith('SK'):notes.append(SOCKET)
            if not verified:notes.append(UNVERIFIED)
            value='hot-swap socket' if part.ref.startswith('SK') else part.value
            writer.writerow([item,' '.join(refs),len(refs),maker,mpn,value,part.footprint.split(':',1)[1],
                             'SMD' if is_smd(fps[part.ref]) else 'thru-hole',' '.join(notes)])

def write_centroid(folder,fitted,fps,origin):
    """Millimetres from the board's lower-left corner, seen from the top, Y up. Rotation as KiCad stores it."""
    x0,y1=origin
    with (folder/'centroid-pcbway.csv').open('w',newline='') as handle:
        writer=csv.writer(handle,lineterminator='\n');writer.writerow(CENTROID_COLUMNS)
        for part in fitted:
            fp=fps[part.ref]
            if not is_smd(fp):continue
            x=f'{p.ToMM(fp.GetPosition().x)-x0:.3f}mm';y=f'{y1-p.ToMM(fp.GetPosition().y):.3f}mm'
            writer.writerow([part.ref,part.footprint.split(':',1)[1],x,y,x,y,x,y,'B' if fp.IsFlipped() else 'T',
                             f'{fp.GetOrientationDegrees()%360:.2f}',sourcing(part)[1]])

def order_sheet(v,board,lines,fitted,fps):
    box=board.GetBoardEdgesBoundingBox();tracks=list(board.GetTracks())
    widths=[p.ToMM(t.GetWidth()) for t in tracks if t.Type()==p.PCB_TRACE_T]
    drills=[p.ToMM(pad.GetDrillSizeX()) for fp in board.GetFootprints() for pad in fp.Pads() if pad.GetDrillSizeX()>0]
    smd=[part for part in fitted if is_smd(fps[part.ref])];tht=[part for part in fitted if not is_smd(fps[part.ref])]
    sides={('Bottom' if fps[part.ref].IsFlipped() else 'Top') for part in smd}
    customer=[refs for part,refs in lines if part.dnp]
    rows=[
     ('Board type','Single pieces'),('Different design in panel','1'),
     ('Size',f'{p.ToMM(box.GetWidth()):.2f} x {p.ToMM(box.GetHeight()):.2f} mm (Edge_Cuts; eight open M2.5 screw slots in the edge)'),
     ('Quantity','5 (prototype run; the owner decides)'),('Layers','4'),('Material','FR-4'),('FR4-TG','TG 150-160'),
     ('Thickness','1.6 mm'),
     ('Min track/spacing',f'6/6 mil (narrowest track {min(widths):.2f} mm, design clearance {rules.CLEARANCE:.2f} mm)'),
     ('Min hole size',f'0.3 mm (vias {rules.VIA_DRILL:.2f} mm drill, {rules.VIA_D:.2f} mm pad; smallest drill {min(drills+[rules.VIA_DRILL]):.2f} mm)'),
     ('Solder mask','Green (0.2 mm gaps between QFN pads: other colours lose the mask bridge)'),('Silkscreen','White'),
     ('Edge connector','No'),('Surface finish','Immersion gold (ENIG), 1U" (flat pads for the 0.4 mm pitch QFN)'),
     ('Via process','Tenting vias'),('Finished copper','1 oz'),('Inner copper','1 oz'),
     ('Layer order','L1 F_Cu signal, L2 In1_Cu ground plane, L3 In2_Cu ground plane with a 3V3 island, L4 B_Cu signal'),
     ('Impedance control','Not ordered. USB is full speed (12 Mbit/s). See the note on the pair geometry below.'),
     ('Custom stackup','No. Standard 4-layer 1.6 mm build: 7628 prepreg, 1.03 mm core.'),
     ('Castellated holes / edge plating / via in pad','No / No / No (four tented 0.3 mm vias sit in the RP2040 ground pad)'),
     ('Remove product No.','Owner decides'),
     ('Assembly type','Turnkey'),('Assembly board type','Single pieces'),('Assembly side(s)',' and '.join(sorted(sides))+' (both)' if len(sides)>1 else sides.pop()),
     ('Number of unique parts',str(sum(not part.dnp for part,_ in lines))),
     ('Number of SMD parts',str(len(smd))),('Number of BGA/QFP parts','1 (RP2040, QFN-56, 0.4 mm pitch)'),
     ('Number of through-hole parts',str(len(tht))),
     ('Function test / firmware loading','No / No'),
     ('Customer-fitted, not on the order',f'48 key switches; {", ".join(" ".join(refs) for refs in customer)}'),
    ]
    z=rules.microstrip_z_diff(rules.USB_TRACK,rules.USB_GAP)
    text=[f'# PCBWay order sheet: worxboard ergo {v}, revision A0 prototype','',
     'This is a prototype order package. No board of this design has been built or tested.',
     'A human must review the USB and ground layout and the items in docs/verification.md before paying.','',
     '| Order form field | Value |','|---|---|']+[f'| {name} | {value} |' for name,value in rows]+['',
     '## Notes for the PCBWay engineer','',
     f'- USB pairs run on L1 over the L2 ground plane, {rules.USB_TRACK} mm wide with a {rules.USB_GAP} mm gap. '
     f'IPC-2141 gives about {z:.0f} ohm differential on {rules.PREPREG_H} mm of 7628 (Dk {rules.PREPREG_DK}). No coupon is needed.',
     '- The mounting holes break the board edge on purpose. Rout them as open slots.',
     '- The three USB-C receptacles sit with the shell mouth flush with the board edge.',
     '- The key switch footprints stay empty. Fit only the hot-swap sockets on the bottom side.',
     '- Stock and price of every BOM line are unknown. Ask before substituting any part.','']
    return '\n'.join(text)

def main(v):
    folder=ROOT/'pcb/fab'/v;folder.mkdir(parents=True,exist_ok=True)
    board=p.LoadBoard(str(ROOT/'pcb'/v/f'worxboard-ergo-{v}.kicad_pcb'))
    fps={fp.GetReference():fp for fp in board.GetFootprints()}
    parts=design(v);lines=bom_lines(parts)
    fitted=[part for part in parts if part.in_bom and not part.dnp]
    box=board.GetBoardEdgesBoundingBox()
    write_bom(folder,lines,fps)
    write_centroid(folder,fitted,fps,(p.ToMM(box.GetLeft()),p.ToMM(box.GetBottom())))
    (folder/'ORDER.md').write_text(order_sheet(v,board,lines,fitted,fps))
    print(v,len(lines),'BOM lines,',len(fitted),'assembler-fitted parts')

if __name__=='__main__':main(sys.argv[1])

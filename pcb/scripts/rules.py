# SPDX-License-Identifier: GPL-3.0-or-later
"""Design rules and stackup for PCBWay's standard 4-layer 1.6 mm service.

Sources, read 2026-11-13: pcbway.com/capabilities.html,
pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html and
pcbway.com/multi-layer-laminated-structure.html. PCBWay publishes 0.10 mm
track and space, 0.15 mm drill, 0.15 mm annular ring and 0.25 mm copper to a
routed edge as limits. Every value here is looser than the limit and inside
the "6/6 mil, 0.3 mm hole" price class. Millimetres throughout.
"""
from math import exp,log,sqrt

CLEARANCE=0.15
TRACK=0.20
TRACK_MIN=0.15
POWER_TRACK=0.40
VIA_D,VIA_DRILL=0.60,0.30
EDGE_CLEARANCE=0.30
HOLE_CLEARANCE=0.25
HOLE_TO_HOLE=0.45
# PCBWay laminated structure, 4 layers 1.6 mm, row 1: 0.5 oz base outer copper plated to 1 oz, 1 oz inner,
# 7628 RC46 % prepreg (Dk 4.74) pressed to 0.1855 mm, 1.03 mm core (Dk 4.6). Row 1 is the one for more than
# 60 % residual copper on the inner layers, and both inner layers here are planes.
COPPER_T=0.035
PREPREG_H,PREPREG_DK=0.1855,4.74
CORE_H,CORE_DK=1.03,4.6
USB_Z_DIFF=90.0
USB_Z_TOLERANCE=5.0
USB_TRACK,USB_GAP=0.22,0.15
PLANE_NETS=('GND','3V3')
POWER_NETS=('VSYS','VBUS_*')    # GND, 3V3 and 1V1 leave 0.2 mm QFN pads, so they stay in Default
USB_NETS=('USB_*',)

def microstrip_z_diff(width,gap,height=PREPREG_H,dk=PREPREG_DK,copper=COPPER_T):
    """Edge-coupled surface microstrip, IPC-2141A closed form. No solder mask term: read it as +/-10 %."""
    single=87.0/sqrt(dk+1.41)*log(5.98*height/(0.8*width+copper))
    return 2.0*single*(1.0-0.48*exp(-0.96*gap/height))

assert abs(microstrip_z_diff(USB_TRACK,USB_GAP)-USB_Z_DIFF)<USB_Z_TOLERANCE

def _netclass(name,track,**extra):
    return {'name':name,'clearance':CLEARANCE,'track_width':track,'via_diameter':VIA_D,'via_drill':VIA_DRILL,
            'diff_pair_width':USB_TRACK,'diff_pair_gap':USB_GAP,'diff_pair_via_gap':0.25,
            'microvia_diameter':0.3,'microvia_drill':0.1,'wire_width':6,'bus_width':12,'line_style':0,
            'pcb_color':'rgba(0, 0, 0, 0.000)','schematic_color':'rgba(0, 0, 0, 0.000)',**extra}

def project_settings():
    """The board and net-class sections of a .kicad_pro. Severities are left at KiCad's defaults."""
    patterns=[{'netclass':'Power','pattern':net} for net in POWER_NETS]
    patterns+=[{'netclass':'USB','pattern':net} for net in USB_NETS]
    return {
        'board':{'design_settings':{'rules':{
            'min_clearance':CLEARANCE,'min_track_width':TRACK_MIN,'min_via_diameter':VIA_D,
            'min_via_annular_width':(VIA_D-VIA_DRILL)/2,'min_through_hole_diameter':VIA_DRILL,
            'min_copper_edge_clearance':EDGE_CLEARANCE,'min_hole_clearance':HOLE_CLEARANCE,
            'min_hole_to_hole':HOLE_TO_HOLE,'min_connection':0.0,'min_microvia_diameter':0.2,
            'min_microvia_drill':0.1,'min_resolved_spokes':2,'min_silk_clearance':0.0,
            'min_text_height':0.8,'min_text_thickness':0.08,'solder_mask_to_copper_clearance':0.0,
            'use_height_for_length_calcs':True}}},
        'net_settings':{'classes':[_netclass('Default',TRACK),_netclass('Power',POWER_TRACK),
                                    _netclass('USB',USB_TRACK)],
                        'meta':{'version':4},'net_colors':None,'netclass_assignments':None,
                        'netclass_patterns':patterns}}

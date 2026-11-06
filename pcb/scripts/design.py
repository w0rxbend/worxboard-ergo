# SPDX-License-Identifier: GPL-3.0-or-later
"""Electrical source of truth. Based on worxboard's RP2040 support circuit.
A0 is an UNROUTED engineering seed, not a fabrication release.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from layout import keys,holes
GROUPS=("MCU","USB-POWER","SELECTOR","DISPLAY","MATRIX")
R0402="Resistor_SMD:R_0402_1005Metric"
C0402="Capacitor_SMD:C_0402_1005Metric"
SOD123="Diode_SMD:D_SOD-123"
TESTPAD="TestPoint:TestPoint_Pad_D1.0mm"
LCSC_R={"5.1k":"C25905","27":"C2909343","1k":"C11702","10k":"C25744"}
LCSC_C={"100n":"C1525","1u":"C52923","10u":"C15525","27p":"C1557"}
LCSC_FLASH="C97521"
LCSC_XTAL="C49304726"
GPIO_NETS=([f"ROW{i}" for i in range(6)]+[f"COL{i}" for i in range(15)]
 +["USB_SEL0","USB_SEL1","VBUS_LEFT_SENSE","VBUS_CENTER_SENSE","VBUS_RIGHT_SENSE",
 "DISP_SCK","DISP_MOSI","DISP_CS","RGB_DATA"])
@dataclass(frozen=True)
class Part:
    ref: str
    lib_id: str
    value: str
    footprint: str
    lcsc: str                      # "" only for parts kept out of the JLC BOM
    pins: dict[str, str | None]    # pin number or name -> net (None = no connect)
    group: str
    in_bom: bool = True            # False: JP1, test pads, holes (spec §7)
    dnp: bool = False              # True: on the board but not fitted by JLC (no such part on rev A)
    key: str = ""                  # layout key id of a matrix SK/D part (also its "Key" field)
    extra: dict[str, str] = field(default_factory=dict)   # further symbol fields

def R(ref: str, value: str, a: str, b: str, group: str) -> Part:
    return Part(ref, "Device:R", value, R0402, LCSC_R[value], {"1": a, "2": b}, group)

def C(ref: str, value: str, net: str, group: str) -> Part:
    return Part(ref, "Device:C", value, C0402, LCSC_C[value], {"1": net, "2": "GND"}, group)

def TP(ref: str, net: str, group: str) -> Part:
    return Part(ref, "Connector:TestPoint", net, TESTPAD, "", {"1": net}, group, in_bom=False)

def _mcu() -> list[Part]:
    g = "MCU"
    u1 = {(f"GPIO{i}" if i<26 else f"GPIO{i}/ADC{i-26}"):net for i,net in enumerate(GPIO_NETS)}
    u1.update({"~{QSPI_SS}":"QSPI_SS","RUN":"RUN","SWCLK":"SWCLK","SWDIO":"SWDIO",
       "TESTEN":"GND","XIN":"XIN","XOUT":"XOUT","USB_DP":"USB_DP","USB_DM":"USB_DM"})
    u1.update({"IOVDD": "3V3", "USB_VDD": "3V3", "ADC_AVDD": "3V3", "VREG_VIN": "3V3",
               "VREG_VOUT": "1V1", "DVDD": "1V1", "GND": "GND",
               "QSPI_SCLK": "QSPI_SCLK", "QSPI_SD0": "QSPI_SD0", "QSPI_SD1": "QSPI_SD1",
               "QSPI_SD2": "QSPI_SD2", "QSPI_SD3": "QSPI_SD3"})
    parts = [
        Part("U1", "MCU_RaspberryPi:RP2040", "RP2040", "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
             "C2040", u1, g),
        Part("U2", "Memory_Flash:W25Q128JVS", "W25Q128JVSIQ", "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm", LCSC_FLASH,
             {"~{CS}": "QSPI_SS", "CLK": "QSPI_SCLK", "DI/IO_{0}": "QSPI_SD0", "DO/IO_{1}": "QSPI_SD1",
              "~{WP}/IO_{2}": "QSPI_SD2", "~{HOLD}/~{RESET}/IO_{3}": "QSPI_SD3", "VCC": "3V3", "GND": "GND"}, g),
        C("C5", "100n", "3V3", g),
        Part("Y1", "Device:Crystal_GND24", "12MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", LCSC_XTAL,
             {"1": "XIN", "3": "XTAL_OUT", "G": "GND"}, g),
        R("R7", "1k", "XTAL_OUT", "XOUT", g),
        C("C6", "27p", "XIN", g),
        C("C7", "27p", "XTAL_OUT", g),
        R("R8", "10k", "QSPI_SS", "3V3", g),
        R("R9", "1k", "QSPI_SS", "BOOT", g),
        Part("SW1", "Switch:SW_Push", "BOOT", "Button_Switch_SMD:SW_SPST_TS-1088-xR020", "C455280",
             {"1": "BOOT", "2": "GND"}, g),
        R("R10", "10k", "RUN", "3V3", g),
        Part("SW2", "Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_SPST_TS-1088-xR020", "C455280",
             {"1": "RUN", "2": "GND"}, g),
    ]
    # 100 nF on each IOVDD (6), USB_VDD, ADC_AVDD and both DVDD; 1 uF on VREG_VIN and VREG_VOUT
    parts += [C(f"C{8 + i}", "100n", "3V3", g) for i in range(8)]
    parts += [C("C16", "100n", "1V1", g), C("C17", "100n", "1V1", g),
              C("C18", "1u", "3V3", g), C("C19", "1u", "1V1", g)]
    parts += [TP("TP8", "SWCLK", g), TP("TP9", "SWDIO", g), TP("TP10", "GND", g)]
    return parts

def design(variant):
 if variant not in ('mx','choc'): raise ValueError(variant)
 parts=_mcu()
 g='USB-POWER'
 # Each receptacle has its own Rd resistors, ESD clamp, and diode-isolated VBUS.
 for i,port in enumerate(['LEFT','CENTER','RIGHT'],1):
  v=f'VBUS_{port}';dp=f'USB_{port}_DP';dm=f'USB_{port}_DM'
  parts += [Part(f'J{i}','Connector:USB_C_Receptacle_USB2.0_16P','TYPE-C-31-M-12',
   'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12','C165948',
   {'VBUS':v,'GND':'GND','SHIELD':'GND','CC1':f'CC{i}A','CC2':f'CC{i}B','D+':dp,'D-':dm,'SBU1':None,'SBU2':None},g),
   R(f'R{20+i*5}','5.1k',f'CC{i}A','GND',g),R(f'R{21+i*5}','5.1k',f'CC{i}B','GND',g),
   R(f'R{22+i*5}','10k',v,f'{v}_SENSE',g),R(f'R{23+i*5}','10k',f'{v}_SENSE','GND',g),
   Part(f'D{i}','Device:D_Schottky','B5819W',SOD123,'C8598',{'A':v,'K':'VSYS'},g),
   Part(f'U{3+i}','Power_Protection:USBLC6-2SC6','USBLC6-2SC6','Package_TO_SOT_SMD:SOT-23-6','C7519',
        {'I/O1':dp,'I/O2':dm,'VBUS':v,'GND':'GND'},g)]
 parts += [Part('U3','Regulator_Linear:AP2112K-3.3','AP2112K-3.3','Package_TO_SOT_SMD:SOT-23-5','C51118',
     {'VIN':'VSYS','EN':'VSYS','GND':'GND','VOUT':'3V3','NC':None},g),
     C('C1','1u','VSYS',g),C('C2','1u','VSYS',g),C('C3','10u','3V3',g),C('C4','1u','3V3',g),
     R('R3','27','USB_MUX_DP','USB_DP',g),R('R4','27','USB_MUX_DM','USB_DM',g)]
 # Explicit pin numbers from TI TS3USB3031 SCDS348D table 4-1.
 parts += [Part('U7','worxboard:TS3USB3031','TS3USB3031RMGR',
  'Package_DFN_QFN:Texas_RMG0012A_WQFN-12_1.8x1.8mm_P0.4mm','',
  {'1':'MUX_S0','2':'MUX_S1','3':'USB_LEFT_DP','4':'USB_LEFT_DM','5':'USB_CENTER_DP','6':'USB_CENTER_DM',
   '7':'USB_RIGHT_DP','8':'USB_RIGHT_DM','9':'GND','10':'USB_MUX_DM','11':'USB_MUX_DP','12':'3V3'},'SELECTOR'),
  R('R40','10k','MUX_S0','3V3','SELECTOR'),R('R41','10k','MUX_S1','3V3','SELECTOR'),
  C('C20','100n','3V3','SELECTOR'),
  R('R42','1k','USB_SEL0','MUX_S0_FW','SELECTOR'),R('R43','1k','USB_SEL1','MUX_S1_FW','SELECTOR'),
  Part('J6','Connector_Generic:Conn_01x03','SEL0: RUN 1-2 / ROM 2-3',
   'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical','',
   {'1':'MUX_S0_FW','2':'MUX_S0','3':'3V3'},'SELECTOR'),
  Part('J7','Connector_Generic:Conn_01x03','SEL1: RUN 1-2 / ROM 2-3',
   'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical','',
   {'1':'MUX_S1_FW','2':'MUX_S1','3':'GND'},'SELECTOR')]
 parts += [Part('J4','Connector_Generic:Conn_01x05','nice!view SPI LCD',
 'worxboard:PinSocket_1x05_P2.54mm_Vertical_H5.0mm','',
 dict(zip(map(str,range(1,6)),['DISP_MOSI','DISP_SCK','3V3','GND','DISP_CS'])),'DISPLAY'),
 Part('J5','Connector_Generic:Conn_01x03','RGB expansion (3V3 logic)',
 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical','',
 {'1':'VSYS','2':'RGB_DATA','3':'GND'},'DISPLAY')]
 fp='worxboard:SW_MX_Hotswap_Kailh' if variant=='mx' else 'worxboard:SW_Choc_V1_Hotswap'
 for n,k in enumerate(keys(),101):
  idx=n-101;row,col=divmod(idx,15)
  parts += [Part(f'SK{n}','worxboard:SW_Push_MX',variant.upper(),fp,'',
    {'1':f'COL{col}','2':f'KEY_{k.id}'},'MATRIX',key=k.id,extra={'Key':k.id}),
   Part(f'D{n}','Device:D','1N4148W',SOD123,'C81598',
    {'A':f'KEY_{k.id}','K':f'ROW{row}'},'MATRIX',key=k.id,extra={'Key':k.id})]
 parts += [Part(f'H{i}','Mechanical:MountingHole','M2.5','MountingHole:MountingHole_2.7mm_M2.5','',{},'MATRIX',in_bom=False) for i in range(1,len(holes())+1)]
 assert len({p.ref for p in parts})==len(parts)
 return parts

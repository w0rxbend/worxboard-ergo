# SPDX-License-Identifier: GPL-3.0-or-later
import json,re,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];build=root/'build/firmware/zephyr'
config=(build/'.config').read_text();dts=(build/'zephyr.dts').read_text()
for flag in ['CONFIG_ZMK_USB=y','CONFIG_ZMK_DISPLAY=y','CONFIG_ZMK_STUDIO=y','CONFIG_ZMK_STUDIO_TRANSPORT_UART=y','CONFIG_USB_CDC_ACM=y']:
 assert flag in config,flag
assert 'CONFIG_BT=y' not in config
assert 'CONFIG_ZMK_SPLIT=y' not in config
assert 'zmk,studio-rpc-uart' in dts
assert 'sharp,ls0xx' in dts
assert 'usb_selector.c.obj' in (root/'build/firmware/build.ninja').read_text()
uf2=root/'firmware/artifacts/worxboard-ergo.uf2'
assert uf2.read_bytes()==(build/'zmk.uf2').read_bytes(), 'UF2 is stale relative to the compiled image'
report={'zmk_sha':'4dd95d7840eb3d5a3f59bb29fbf1ab054715ef85','board':'worxboard_ergo/rp2040',
 'snippet':'studio-rpc-usb-uart','compiled':True,'usb_only':True,'lcd_driver':'sharp,ls0xx',
 'studio_transport':'USB CDC ACM','hardware_tested':False,'uf2_bytes':uf2.stat().st_size,
 'uf2_sha256':hashlib.sha256(uf2.read_bytes()).hexdigest()}
(root/'firmware/artifacts/build-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('RP2040 USB/LCD/Studio firmware verified from build outputs')

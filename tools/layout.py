# SPDX-License-Identifier: GPL-3.0-or-later
import json, html
from pathlib import Path
from layout.model import serializable, keys, outline, DISPLAY
ROOT=Path(__file__).resolve().parents[1]
def main():
 d=ROOT/'assets';d.mkdir(exist_ok=True)
 (d/'layout.json').write_text(json.dumps(serializable(),indent=2)+'\n')
 x0,y0,x1,y1=outline().bounds
 s=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-8} {y0-18} {x1-x0+16} {y1-y0+93}">',
 '<rect x="-210" y="-70" width="510" height="310" rx="10" fill="#101923"/>',
 '<style>text{font-family:DejaVu Sans,sans-serif;fill:#e9eff5;text-anchor:middle} .key{fill:#283b4c;stroke:#7d98ac;stroke-width:.5}</style>',
 '<text fill="#e9eff5" x="35" y="-46" font-size="8">worxboard ergo • 87-key wired TKL • design study A0</text>',
 '<path d="M '+' L '.join(f'{x:.3f} {y:.3f}' for x,y in outline().exterior.coords)+' Z" fill="#182b38" stroke="#77b7aa"/>',
 f'<rect x="{x0+4}" y="{y1+5}" width="{x1-x0-8}" height="51" rx="18" fill="#253b40" stroke="#77b7aa"/>']
 for k in keys():
  s.append(f'<g transform="translate({k.x},{k.y}) rotate({k.angle})"><rect fill="#283b4c" stroke="#7d98ac" stroke-width=".5" class="key" x="{-k.w*19.05/2+.7}" y="-8.825" width="{k.w*19.05-1.4}" height="17.65" rx="1.8"/><text fill="#e9eff5" y="1.5" font-size="3.7">{html.escape(k.label)}</text></g>')
 x,y=DISPLAY['x'],DISPLAY['y']
 s += [f'<rect x="{x-18}" y="{y-9}" width="36" height="18" rx="2" fill="#90baaa"/>',
 f'<text x="{x}" y="{y-1}" style="fill:#102820" font-size="3.3">BASE</text><text x="{x}" y="{y+4}" style="fill:#102820" font-size="2.5">USB • layer 0</text>',
 '<text fill="#e9eff5" x="35" y="189" font-size="5">Cherry MX or Kailh Choc v1 • RP2040 • center memory LCD</text></svg>']
 (d/'layout.svg').write_text(''.join(s))
 print(len(keys()),'keys; enclosure',tuple(round(v,2) for v in outline().bounds))
if __name__=='__main__': main()

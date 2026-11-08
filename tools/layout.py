# SPDX-License-Identifier: GPL-3.0-or-later
import json, html
from pathlib import Path
from layout.model import serializable, keys, outline, palm_outline, holes, DISPLAY, PORTS
ROOT=Path(__file__).resolve().parents[1]

def path(poly, **style):
    d='M '+' L '.join(f'{x:.2f} {y:.2f}' for x,y in poly.exterior.coords)+' Z'
    attrs=' '.join(f'{k}="{v}"' for k,v in style.items())
    return f'<path d="{d}" {attrs}/>'

def main():
    data=serializable()
    deck, palm=outline(), palm_outline()
    x0,y0,x1,y1=deck.bounds
    px0,py0,px1,py1=palm.bounds
    vx0, vy0=min(x0,px0)-14, min(y0,py0)-28
    vx1, vy1=max(x1,px1)+14, max(y1,py1)+16
    accent={'Ctrl','Alt','Fn','Shift','Caps','Tab','Enter','Bksp','Space','Esc','Lower','Raise'}
    s=[
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx0:.1f} {vy0:.1f} {vx1-vx0:.1f} {vy1-vy0:.1f}">',
        '<defs><linearGradient id="deck" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e6e8ea"/><stop offset="1" stop-color="#c5c8cc"/></linearGradient>',
        '<linearGradient id="rest" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9aa0a6"/><stop offset="1" stop-color="#6d737a"/></linearGradient></defs>',
        f'<rect x="{vx0:.1f}" y="{vy0:.1f}" width="{vx1-vx0:.1f}" height="{vy1-vy0:.1f}" fill="#121418"/>',
        '<style>text{font-family:DejaVu Sans,sans-serif;text-anchor:middle;fill:#2a2e33}</style>',
        f'<text x="{(x0+x1)/2:.1f}" y="{vy0+16:.1f}" fill="#d7dbdf" font-size="7">worxboard ergo · split Planck · detached wells</text>',
        path(deck, fill='url(#deck)', stroke='#8d9399', **{'stroke-width':'0.6'}),
        path(palm, fill='url(#rest)', stroke='#5c636a', **{'stroke-width':'0.5'}),
    ]
    for k in keys():
        fill='#4f8f9a' if k.label in accent else '#f4f1ea'
        ink='#f7fbfb' if k.label in accent else '#2a2e33'
        s.append(
            f'<g transform="translate({k.x},{k.y}) rotate({k.angle})">'
            f'<rect x="{-k.w*19.05/2+0.55}" y="-8.9" width="{k.w*19.05-1.1}" height="17.8" rx="2.2" fill="{fill}" stroke="#b7b1a8" stroke-width="0.35"/>'
            f'<circle cx="0" cy="7.6" r="0.7" fill="#f2c14e"/>'
            f'<text y="1.4" font-size="3.5" fill="{ink}">{html.escape(k.label)}</text></g>')
    dx,dy=DISPLAY['x'],DISPLAY['y']
    s.append(f'<rect x="{dx-16}" y="{dy-6}" width="32" height="12" rx="1.4" fill="#1c3a36" stroke="#8fb9ae"/>')
    s.append(f'<text x="{dx}" y="{dy+1.2}" fill="#d7efe8" font-size="3">BASE</text>')
    for x,y in holes():
        s.append(f'<circle cx="{x}" cy="{y}" r="1.5" fill="none" stroke="#6e757c" stroke-width="0.4"/>')
    for name,(x,y) in PORTS.items():
        s.append(f'<rect x="{x-5}" y="{y-1}" width="10" height="4" rx="0.6" fill="#2c3136"/>')
    s.append(f'<text x="{(x0+x1)/2:.1f}" y="{vy1-6:.1f}" fill="#aeb4ba" font-size="3.4">MX or Choc v1 hot-swap · south LED windows · RP2040 · not a fabrication release</text>')
    s.append('</svg>')
    out=ROOT/'assets'
    (out/'layout.json').write_text(json.dumps(data, indent=2)+'\n')
    (out/'layout.svg').write_text(''.join(s))
    print(len(keys()), 'keys; deck', tuple(round(v,1) for v in deck.bounds))

if __name__=='__main__':
    main()

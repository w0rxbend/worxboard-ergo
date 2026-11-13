# SPDX-License-Identifier: GPL-3.0-or-later
"""Product renders for the microsite and the README.

pyvista is not a locked project dependency. Run:
    uv run --with pyvista==0.46.3 python -m tools.render
The pictures show envelope CAD: keycaps and the display are blocks.
"""
from pathlib import Path

import pyvista as pv
from PIL import Image

from cad.model import make

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'site/img'
SIZE = (2400, 1350)
TESSELLATION_MM = 0.05
BODY = '#3a3d42'
COLOURS = {
    'chassis': BODY,
    'top_cover': '#2c2f33',
    'palm_rest': '#1d1f22',
    'riser': BODY,
    'plate': '#8d9399',
    'keycap_envelopes': '#e9e6df',
    'lcd_envelope': '#9fc4b8',
}
# name -> (variant, camera position, focal point, view up, labels shown)
SHELL = ('chassis', 'top_cover', 'palm_rest', 'keycap_envelopes', 'lcd_envelope')
VIEWS = {
    'hero': ('mx', (-260, -520, 330), (0, -20, 0), (0, 0, 1), SHELL),
    'top': ('mx', (0, -40, 900), (0, -40, 0), (0, 1, 0), SHELL),
    'side': ('mx', (900, -40, 60), (0, -40, 8), (0, 0, 1), SHELL),
    'choc': ('choc', (-260, -520, 330), (0, -20, 0), (0, 0, 1), SHELL),
    'parts': ('mx', (-400, -760, 560), (0, -30, 20), (0, 0, 1), SHELL + ('plate', 'riser')),
}
# Lift per label in the exploded view, in millimeters.
EXPLODE = {'riser': -45.0, 'plate': 30.0, 'top_cover': 60.0, 'keycap_envelopes': 95.0, 'lcd_envelope': 60.0, 'palm_rest': 30.0}


def mesh_of(shape):
    vertices, triangles = shape.tessellate(TESSELLATION_MM, 0.1)
    faces = [(3, *triangle) for triangle in triangles]
    return pv.PolyData([tuple(v) for v in vertices], [index for face in faces for index in face])


def solids(variant):
    _, assembly = make(variant)
    return {child.label: child for child in assembly.children}


def render(name, by_label):
    _, position, focus, up, labels = VIEWS[name]
    plotter = pv.Plotter(off_screen=True, window_size=SIZE, lighting='three lights')
    for label in labels:
        mesh = mesh_of(by_label[label])
        if name == 'parts':
            mesh.translate((0, 0, EXPLODE.get(label, 0.0)), inplace=True)
        plotter.add_mesh(mesh, color=COLOURS[label], smooth_shading=True, split_sharp_edges=True,
                         feature_angle=30, specular=0.25, specular_power=18, ambient=0.22, diffuse=0.85)
    plotter.camera_position = (position, focus, up)
    plotter.camera.view_angle = 24
    plotter.enable_anti_aliasing('ssaa')
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / (name + '.png')
    plotter.screenshot(target, transparent_background=True)
    plotter.close()
    picture = Image.open(target)
    picture.crop(picture.getbbox()).save(target, optimize=True)


def main():
    built = {}
    for name, view in VIEWS.items():
        variant = view[0]
        if variant not in built:
            built[variant] = solids(variant)
        render(name, built[variant])
        print('rendered', name)


if __name__ == '__main__':
    main()

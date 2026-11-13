# SPDX-License-Identifier: GPL-3.0-or-later
"""Path-traced product renders for the microsite and the README.

Blender (bpy, Cycles on the CPU) is not a locked project dependency, and its wheel needs
Python 3.13. Run from the repository root, in an ephemeral environment:

    uv run --no-project --python 3.13 --with bpy==5.3.0 --with build123d==0.13.0 \
        --with shapely==2.2.0 --with pillow==13.0.0 --with imagequant==1.1.6 python -m tools.render

Add shot names to render only those: ... python -m tools.render hero rear

The pictures show a design that has never been built. The shell, plate, cover, palm rest and
riser are the exported CAD. Keycaps, switches, legends, USB shells, PCB pads, the display
content, colours and finishes come from tools/render_parts.py and from this file.
"""
import sys
import tempfile
from dataclasses import dataclass
from math import cos, radians, sin
from pathlib import Path

import bpy
import bmesh   # importable only after bpy
import imagequant
from mathutils import Matrix, Vector
from PIL import Image

from cad.model import CAP_LIFT, LCD_SINK, LCD_T, PAD_PROUD, PCB_TOP, REAR_PAD_Y, RISER_TILT, cad_xy, make
from layout import DISPLAY, keys, variants
from tools.render_parts import CAPS, SWITCHES, keycap, pcb_pads, riser_pads, usb_shells

ROOT = Path(__file__).resolve().parents[1]
SITE_IMAGES = ROOT / 'site/img'
PRODUCT = ROOT / 'assets/product.png'
PRODUCT_SIZE, PRODUCT_BACKGROUND, PRODUCT_FILL = (1500, 1000), '#f5f5f7', 0.9
MM = 0.001                    # the scene is in metres, so light, depth of field and bump are physical
TESSELLATION_MM, TESSELLATION_RAD = 0.03, 0.08
WELD_MM, SHARP_DEG = 0.001, 32.0
SAMPLES = 96
SENSOR_MM = 36.0
FRAME_FILL = 0.84             # share of the frame the subject may span; the rest is room for its shadow
ALPHA_FLOOR = 6               # shadow fainter than this does not count when cropping
ALPHA_SOLID = 250             # at or above this a pixel is the product, not its shadow
PNG_COLOURS, PNG_MAX_WIDTH, WEBP_QUALITY = 256, 2400, 88
SURFACE_GAP_MM = 0.01         # how far a legend sits off the surface under it


@dataclass(frozen=True)
class Finish:
    """A principled surface. Grain is a bump of fine noise, for moulded or blasted texture."""
    colour: str
    roughness: float
    metallic: float = 0.0
    grain: float = 0.0
    grain_mm: float = 0.25
    coat: float = 0.0


FINISHES = {
    'shell': Finish('#303236', 0.62, grain=0.5),
    'cover': Finish('#1f2124', 0.55, grain=0.35),
    'palm': Finish('#101112', 0.32, grain=0.12, grain_mm=0.6),
    'plate': Finish('#6e7277', 0.42, metallic=1.0, grain=0.25, grain_mm=0.12),
    'pcb': Finish('#0b0c0d', 0.6, coat=0.25),
    'gold': Finish('#d8a94a', 0.3, metallic=1.0),
    'hole': Finish('#020202', 0.9),
    'steel': Finish('#c9cbce', 0.28, metallic=1.0),
    'rubber': Finish('#1a1a1b', 0.85),
    'lcd': Finish('#aeb5aa', 0.16, metallic=0.75, coat=1.0),
    'ink': Finish('#101112', 0.5),
    'cap_light': Finish('#e7e4dc', 0.5, grain=0.3, grain_mm=0.18),
    'cap_dark': Finish('#55585e', 0.5, grain=0.3, grain_mm=0.18),
    'legend_dark': Finish('#17181a', 0.6),
    'legend_light': Finish('#e7e4dc', 0.6),
    'switch_base': Finish('#111213', 0.4),
    'switch_top': Finish('#2a2c30', 0.25, coat=0.5),
    'switch_stem': Finish('#b5503c', 0.4),
}
# Assembly label -> (layer, finish). A layer moves as one in the exploded view.
ASSEMBLY = {
    'chassis': ('chassis', 'shell'), 'pad_envelopes': ('chassis', 'rubber'), 'riser': ('riser', 'shell'),
    'palm_rest': ('palm', 'palm'), 'top_cover': ('cover', 'cover'), 'plate': ('plate', 'plate'),
    'pcb_envelope': ('pcb', 'pcb'), 'lcd_envelope': ('lcd', 'lcd'),
}
# Exploded view: how far each layer moves from its seat, CAD frame. The palm rest slides toward the typist.
EXPLODE_MM = {'riser': (0, 0, -45), 'palm': (0, -70, 12), 'pcb': (0, 0, 40), 'plate': (0, 0, 85), 'lcd': (0, 0, 105),
              'cover': (0, 0, 130), 'switches': (0, 0, 170), 'caps': (0, 0, 215)}
SEATED = (0, 0, 0)
LEGEND_MM = {'glyph': 6.0, 'word': 2.8}   # font size for a one-character legend and for a word
LEGEND_BOLD_MM = 0.1                      # the built-in font is light; fatten every outline by this much
LCD_TEXT, LCD_TEXT_MM = 'BASE', 6.0


@dataclass(frozen=True)
class Light:
    """An area light in the camera rig frame: the camera stands toward -y, x is camera right."""
    position: tuple   # metres from the subject
    size: float       # metres
    watts: float


LIGHTS = (
    Light((-0.70, 0.30, 0.80), 1.0, 14.0),    # key: a soft box above, camera left
    Light((0.70, -0.50, 0.75), 1.2, 4.0),     # fill
    Light((0.35, 0.80, 0.55), 0.5, 7.0),      # rim, from behind
)
WORLD_STRENGTH = 0.5


@dataclass(frozen=True)
class Shot:
    """One picture. Azimuth turns the camera from the typist's seat toward the typist's left."""
    variant: str
    azimuth: float
    elevation: float
    stance: str = 'flat'                  # flat, riser or exploded
    size: tuple = (2400, 1350)
    lens: float = 90.0
    detail: tuple | None = None           # frame only this: centre x, y, z and radius, CAD frame, mm
    fstop: float | None = None            # depth of field, focused on the frame centre


SHOTS = {
    'top': Shot('mx', 0, 90, size=(2400, 1700), lens=200),
    'hero': Shot('mx', 24, 34),
    'side': Shot('mx', -90, 3, size=(2400, 800)),
    'rear': Shot('mx', 156, 17),
    'choc': Shot('choc', 24, 34),
    'parts': Shot('mx', 24, 22, stance='exploded', size=(2400, 2700)),
    'riser': Shot('mx', -90, 3, stance='riser', size=(2400, 800)),
    'detail-display': Shot('mx', 12, 42, detail=(0, 16, 16, 34), fstop=11.0),
    'detail-palm': Shot('mx', 38, 13, detail=(-35, -132, 12, 55), fstop=8.0),
    'detail-legends': Shot('mx', 18, 40, detail=(-66, -32, 22, 26), fstop=8.0),
}


@dataclass(frozen=True)
class Stage:
    camera: bpy.types.Object
    rig: bpy.types.Object      # the lights hang on it; it turns with the camera
    ground: bpy.types.Object   # catches the shadow and nothing else


@dataclass
class Board:
    """One variant in the scene: a root, and under it one empty per layer with that layer's objects."""
    root: bpy.types.Object
    layers: dict


def linear(colour):
    """An sRGB hex colour as the linear RGBA Blender shades with."""
    channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels] + [1.0]


def material_of(name):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    finish = FINISHES[name]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    surface = nodes['Principled BSDF']
    surface.inputs['Base Color'].default_value = linear(finish.colour)
    surface.inputs['Roughness'].default_value = finish.roughness
    surface.inputs['Metallic'].default_value = finish.metallic
    surface.inputs['Coat Weight'].default_value = finish.coat
    if finish.grain:
        noise, bump = nodes.new('ShaderNodeTexNoise'), nodes.new('ShaderNodeBump')
        noise.inputs['Scale'].default_value = 1 / (finish.grain_mm * MM)
        bump.inputs['Strength'].default_value = finish.grain
        bump.inputs['Distance'].default_value = finish.grain_mm * MM / 10
        links.new(nodes.new('ShaderNodeTexCoord').outputs['Object'], noise.inputs['Vector'])
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], surface.inputs['Normal'])
    return material


def mesh_of(name, shape, finish):
    """A build123d shape as a smooth-shaded Blender mesh in metres, in one finish."""
    vertices, triangles = shape.tessellate(TESSELLATION_MM, TESSELLATION_RAD)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(v.X * MM, v.Y * MM, v.Z * MM) for v in vertices], [], triangles)
    welded = bmesh.new()
    welded.from_mesh(mesh)
    bmesh.ops.remove_doubles(welded, verts=welded.verts, dist=WELD_MM * MM)
    welded.to_mesh(mesh)
    welded.free()
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=radians(SHARP_DEG))
    mesh.materials.append(material_of(finish))
    return mesh


def text_of(body, size_mm, finish):
    text = bpy.data.curves.new(body, 'FONT')
    text.body, text.size, text.offset = body, size_mm * MM, LEGEND_BOLD_MM * MM
    text.align_x = text.align_y = 'CENTER'
    text.materials.append(material_of(finish))
    return text


def place(board, layer, geometry, at=Matrix.Identity(4)):
    """Link mesh or text geometry into a layer of the board, at a pose in metres."""
    if layer not in board.layers:
        anchor = bpy.data.objects.new(layer, None)
        anchor.parent = board.root
        bpy.context.scene.collection.objects.link(anchor)
        board.layers[layer] = [anchor]
    placed = bpy.data.objects.new(geometry.name, geometry)
    placed.parent, placed.matrix_local = board.layers[layer][0], at
    bpy.context.scene.collection.objects.link(placed)
    board.layers[layer].append(placed)
    return placed


def key_pose(key, z_mm):
    x, y = cad_xy(key.x, key.y)
    return Matrix.Translation((x * MM, y * MM, z_mm * MM)) @ Matrix.Rotation(radians(-key.angle), 4, 'Z')


def is_modifier(key):
    return len(key.label) > 1


def place_legend(board, key, cap, top_mm):
    """The key's base-layer label as flat geometry, wrapped onto the dished cap top."""
    finish = 'legend_light' if is_modifier(key) else 'legend_dark'
    size = LEGEND_MM['word' if is_modifier(key) else 'glyph']
    legend = place(board, 'caps', text_of(key.label, size, finish), key_pose(key, top_mm))
    wrap = legend.modifiers.new('wrap', 'SHRINKWRAP')
    wrap.target, wrap.wrap_mode, wrap.offset = cap, 'ABOVE_SURFACE', SURFACE_GAP_MM * MM


def place_keys(board, variant, plate_top):
    profile = CAPS[variant]
    cap_bottom = plate_top + CAP_LIFT + variants[variant]['cap_height'] - profile.height
    switch = {name: mesh_of(name, shape, name) for name, shape in SWITCHES[variant](variants[variant]['plate_to_pcb']).items()}
    caps = {finish: mesh_of(finish, keycap(profile), finish) for finish in ('cap_light', 'cap_dark')}
    for key in keys():
        for mesh in switch.values():
            place(board, 'switches', mesh, key_pose(key, plate_top))
        cap = place(board, 'caps', caps['cap_dark' if is_modifier(key) else 'cap_light'], key_pose(key, cap_bottom))
        place_legend(board, key, cap, cap_bottom + profile.height)


def place_display_text(board, plate_top):
    x, y = cad_xy(DISPLAY['x'], DISPLAY['y'])
    glass = plate_top - LCD_SINK + LCD_T + SURFACE_GAP_MM
    place(board, 'lcd', text_of(LCD_TEXT, LCD_TEXT_MM, 'ink'), Matrix.Translation((x * MM, y * MM, glass * MM)))


def build_board(variant):
    _, assembly = make(variant)
    solids = {child.label: child for child in assembly.children}
    board = Board(bpy.data.objects.new(variant, None), {})
    bpy.context.scene.collection.objects.link(board.root)
    for label, (layer, finish) in ASSEMBLY.items():
        place(board, layer, mesh_of(label, solids[label], finish))
    place(board, 'pcb', mesh_of('usb_shells', usb_shells(solids['usb_receptacle_envelopes']), 'steel'))
    for finish, shape in pcb_pads(variant).items():
        place(board, 'pcb', mesh_of('pcb_' + finish, shape, finish))
    place(board, 'riser', mesh_of('riser_pads', riser_pads(), 'rubber'))
    plate_top = PCB_TOP + variants[variant]['plate_to_pcb']
    place_keys(board, variant, plate_top)
    place_display_text(board, plate_top)
    return board


def pose(boards, shot):
    """Show one board in the shot's stance and hide the others. Returns the visible mesh objects."""
    # On the riser the desk is the plane z = 0: the inverse of cad.model._desk() in the CAD frame.
    on_riser = Matrix.Rotation(radians(-RISER_TILT), 4, 'X') @ Matrix.Translation((0, REAR_PAD_Y * MM, PAD_PROUD * MM))
    visible = []
    for variant, board in boards.items():
        board.root.matrix_world = on_riser if shot.stance == 'riser' else Matrix.Identity(4)
        for layer, (anchor, *members) in board.layers.items():
            anchor.location = Vector(EXPLODE_MM.get(layer, SEATED) if shot.stance == 'exploded' else SEATED) * MM
            # The riser is an accessory: the flat stance is the board without it.
            shown = variant == shot.variant and not (layer == 'riser' and shot.stance == 'flat')
            for member in members:
                member.hide_render = not shown
            if shown:
                visible += [member for member in members if member.type == 'MESH']
    bpy.context.view_layer.update()
    return visible


def corners(objects):
    return [member.matrix_world @ Vector(corner) for member in objects for corner in member.bound_box]


def detail_corners(detail):
    *centre, radius = detail
    return [Vector(centre) * MM + Vector((sx, sy, sz)) * radius * MM
            for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]


def frame(stage, shot, points):
    """Stand the camera at the shot's angles, just far enough back that every point is in frame,
    and turn the lights with it."""
    azimuth, elevation = radians(shot.azimuth), radians(shot.elevation)
    toward_camera = Vector((-sin(azimuth) * cos(elevation), -cos(azimuth) * cos(elevation), sin(elevation)))
    # Straight down, the typist's side is the bottom of the picture.
    upright = Vector((0, 1, 0)) if shot.elevation == 90 else Vector((0, 0, 1))
    right = upright.cross(toward_camera).normalized()
    up = toward_camera.cross(right)
    turn = Matrix((right, up, toward_camera)).transposed()
    seen = [turn.transposed() @ point for point in points]
    middle = [(min(p[axis] for p in seen) + max(p[axis] for p in seen)) / 2 for axis in range(3)]
    width, height = shot.size
    half = [SENSOR_MM / 2 / shot.lens * side / max(shot.size) * FRAME_FILL for side in (width, height)]
    distance = max(max(abs(p.x - middle[0]) / half[0], abs(p.y - middle[1]) / half[1]) + p.z - middle[2] for p in seen)
    stand = turn @ Vector((middle[0], middle[1], middle[2] + distance))
    stage.camera.matrix_world = Matrix.Translation(stand) @ turn.to_4x4()
    optics = stage.camera.data
    optics.lens, optics.dof.use_dof, optics.dof.focus_distance = shot.lens, shot.fstop is not None, distance
    if shot.fstop:
        optics.dof.aperture_fstop = shot.fstop
    stage.rig.location, stage.rig.rotation_euler.z = turn @ Vector(middle), radians(-shot.azimuth)


def set_up_renderer(scene):
    scene.render.engine, scene.render.film_transparent = 'CYCLES', True
    scene.cycles.samples, scene.cycles.use_denoising = SAMPLES, True
    scene.view_settings.view_transform, scene.view_settings.look = 'AgX', 'AgX - Medium High Contrast'
    scene.render.image_settings.file_format, scene.render.image_settings.color_mode = 'PNG', 'RGBA'
    scene.world = bpy.data.worlds.new('studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = WORLD_STRENGTH


def build_stage():
    """An empty scene with a camera, a light rig and a shadow-catching ground."""
    scene = bpy.context.scene
    for leftover in list(scene.objects):
        bpy.data.objects.remove(leftover)
    set_up_renderer(scene)
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    camera.data.sensor_width, camera.data.clip_start, camera.data.clip_end = SENSOR_MM, 0.01, 100.0
    rig = bpy.data.objects.new('rig', None)
    ground = bpy.data.objects.new('ground', bpy.data.meshes.new('ground'))
    ground.data.from_pydata([(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)], [], [(0, 1, 2, 3)])
    ground.is_shadow_catcher = True
    for staged in (camera, rig, ground):
        scene.collection.objects.link(staged)
    scene.camera = camera
    for light in LIGHTS:
        lamp = bpy.data.objects.new('light', bpy.data.lights.new('light', 'AREA'))
        lamp.data.size, lamp.data.energy = light.size, light.watts
        lamp.parent, lamp.location = rig, light.position
        lamp.rotation_euler = Vector(light.position).to_track_quat('Z', 'Y').to_euler()
        scene.collection.objects.link(lamp)
    return Stage(camera, rig, ground)


def trace(shot, target):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = shot.size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(target)
    bpy.ops.render.render(write_still=True)


def extent(picture, alpha_floor):
    """Bounding box of the pixels more opaque than the floor."""
    return picture.getchannel('A').point(lambda alpha: 255 if alpha > alpha_floor else 0).getbbox()


def cropped(path, whole_subject):
    """The render, trimmed to the product and its shadow. A whole subject must not reach the frame edge."""
    picture = Image.open(path).convert('RGBA')
    left, top, right, bottom = extent(picture, ALPHA_SOLID)
    if whole_subject and (left == 0 or top == 0 or right == picture.width or bottom == picture.height):
        raise RuntimeError(f'{path.stem} is clipped by the frame')
    return picture.crop(extent(picture, ALPHA_FLOOR))


def save_web(picture, target):
    """A palette PNG, small enough for the page, and a WebP beside it."""
    if picture.width > PNG_MAX_WIDTH:
        picture = picture.resize((PNG_MAX_WIDTH, round(picture.height * PNG_MAX_WIDTH / picture.width)), Image.LANCZOS)
    imagequant.quantize_pil_image(picture, max_colors=PNG_COLOURS).save(target, optimize=True)
    picture.save(target.with_suffix('.webp'), quality=WEBP_QUALITY, method=6)


def save_product(top):
    """The top view on the page background, for the README."""
    card = Image.new('RGBA', PRODUCT_SIZE, PRODUCT_BACKGROUND)
    scale = PRODUCT_FILL * min(PRODUCT_SIZE[0] / top.width, PRODUCT_SIZE[1] / top.height)
    fitted = top.resize((round(top.width * scale), round(top.height * scale)), Image.LANCZOS)
    card.alpha_composite(fitted, ((PRODUCT_SIZE[0] - fitted.width) // 2, (PRODUCT_SIZE[1] - fitted.height) // 2))
    imagequant.quantize_pil_image(card, max_colors=PNG_COLOURS).save(PRODUCT, optimize=True)


def main(names):
    unknown = set(names) - set(SHOTS)
    if unknown:
        raise SystemExit(f'unknown shots {sorted(unknown)}; known: {", ".join(SHOTS)}')
    shots = {name: SHOTS[name] for name in names or SHOTS}
    stage = build_stage()
    boards = {variant: build_board(variant) for variant in {shot.variant for shot in shots.values()}}
    SITE_IMAGES.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        for name, shot in shots.items():
            subject = corners(pose(boards, shot))
            stage.ground.location.z = min(point.z for point in subject)
            stage.ground.hide_render = shot.stance == 'exploded'   # parts in mid-air cast one shapeless blot
            frame(stage, shot, detail_corners(shot.detail) if shot.detail else subject)
            raw = Path(scratch) / (name + '.png')
            trace(shot, raw)
            picture = cropped(raw, whole_subject=shot.detail is None)
            save_web(picture, SITE_IMAGES / (name + '.png'))
            if name == 'top':
                save_product(picture)
            print('rendered', name, picture.size)


if __name__ == '__main__':
    main(sys.argv[1:])

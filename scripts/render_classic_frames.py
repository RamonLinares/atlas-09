"""Render review frames of every clip from a prepared classic-mecha Blender file.

Usage: blender -b --python scripts/render_classic_frames.py -- <blender-name> <character-id> [frames-per-clip] [clip,clip]
Writes output/<character-id>/motion/<clip>-<view>-<frame>.png using EEVEE.
"""
import bpy, sys, math, json
from pathlib import Path
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
BLEND, CHAR = argv[0], argv[1]; PER = int(argv[2]) if len(argv) > 2 else 6
ONLY = argv[3].split(',') if len(argv) > 3 else None
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / 'output' / CHAR / 'motion'; OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender' / f'{BLEND}.blend'))
scene = bpy.context.scene; rig = bpy.data.objects[f'{BLEND}_RIG']; armor = bpy.data.objects[f'{BLEND}_Armor']
scene.render.engine = 'BLENDER_EEVEE'; scene.render.resolution_x = 520; scene.render.resolution_y = 520; scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 12
cam = scene.camera; cam.data.type = 'PERSP'; cam.data.lens = 40
H = max(v.co.z for v in armor.data.vertices)
def look(position, target):
    cam.location = position; cam.rotation_euler = (Vector(target) - Vector(position)).to_track_quat('-Z', 'Y').to_euler()
views = {'front': ((3, -52, H * .55), (0, 0, H * .48)), 'side': ((52, -6, H * .55), (0, 0, H * .48)), 'quarter': ((34, -40, H * .6), (0, 0, H * .48))}
rendered = []
for action in bpy.data.actions:
    if ONLY and action.name not in ONLY: continue
    rig.animation_data.action = action; start, end = map(int, action.frame_range)
    frames = [round(start + (end - start) * i / (PER - 1)) for i in range(PER)]
    for frame in frames:
        scene.frame_set(frame)
        for view, (pos, tgt) in views.items():
            if view == 'side' and action.name not in ('Run', 'KneelFire', 'Backflip', 'RocketPunch', 'BoostJump', 'ChestBeam', 'RifleBurst'): continue
            look(pos, tgt); scene.render.filepath = str(OUT / f'{action.name}-{view}-{frame:03d}.png'); bpy.ops.render.render(write_still=True)
            rendered.append(scene.render.filepath)
(OUT / 'index.json').write_text(json.dumps(rendered, indent=2)); print('RENDERED', len(rendered))

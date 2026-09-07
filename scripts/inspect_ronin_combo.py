"""Render magnetic docking, unarmed strikes, and retrieval for visual review."""
import bpy
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/RONIN-04.blend'))
r=bpy.data.objects['RONIN_04_RIG'];r.animation_data.action=bpy.data.actions['PunchCombo']
s=bpy.context.scene;c=s.camera;s.render.resolution_x=800;s.render.resolution_y=900;s.cycles.samples=8;c.data.ortho_scale=21
for name,time,position in [
 ('dock',2.4,(-17,30,16)),('jab',4.3,(14,-30,15)),('cross-back',5.2,(-17,30,16)),
 ('hook',6.1,(-17,-30,15)),('retrieve',9.4,(-17,30,16)),('ready',12,(14,-30,15))]:
 s.frame_set(round(time*30)+1);c.location=position;c.rotation_euler=(Vector((0,0,9))-c.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=str(ROOT/f'output/ronin-04/combo-{name}.png');bpy.ops.render.render(write_still=True)

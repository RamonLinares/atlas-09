"""Save SERAPH with deployed wings and render its reusable Blender studio."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/SERAPH-03.blend'))
rig=bpy.data.objects['SERAPH_03_RIG'];rig.animation_data.action=bpy.data.actions['WingDeploy'];bpy.context.scene.frame_set(91)
scene=bpy.context.scene;scene.camera.data.ortho_scale=25;scene.camera.data.clip_end=2000;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.cycles.samples=16
floor=bpy.data.objects['Studio floor'];floor.dimensions.x=2000;floor.dimensions.y=2000
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/SERAPH-03.blend'))
bpy.context.scene.render.filepath=str(ROOT/'output/seraph-03/seraph-03-beauty.png');bpy.ops.render.render(write_still=True)

"""Confirm Ronin uses Aether's established punch timing and limb directions."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from retarget_library import MotionSource
source=MotionSource(ROOT/'public/models/aether-02.glb')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/RONIN-04.blend'))
r=bpy.data.objects['RONIN_04_RIG'];r.animation_data.action=bpy.data.actions['PunchCombo'];s=bpy.context.scene
names=['upper_arm.L','forearm.L','upper_arm.R','forearm.R']
minimum={n:1.0 for n in names}
for i in range(118):
 t=i/30;s.frame_set(121+i);bpy.context.view_layer.update();pose=source.sample('PunchCombo',t)
 for n in names:
  a=(r.pose.bones[n].tail-r.pose.bones[n].head).normalized()
  c=(pose[n].to_3x3()@Vector((0,1,0))).normalized()
  minimum[n]=min(minimum[n],float(a.dot(c)))
report={'reference':'AETHER-02 PunchCombo','combat_start_s':4.0,'combat_duration_s':3.9,'samples':118,'minimum_arm_direction_cosine':minimum}
(ROOT/'output/ronin-04/punch-source-comparison.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
assert min(minimum.values())>.99,report

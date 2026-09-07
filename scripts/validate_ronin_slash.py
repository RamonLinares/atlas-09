"""Verify that SwordSlash is a fast, coordinated full-body attack."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/RONIN-04.blend'))
r=bpy.data.objects['RONIN_04_RIG'];r.animation_data.action=bpy.data.actions['SwordSlash'];s=bpy.context.scene;b=r.pose.bones
start,end=r.animation_data.action.frame_range;points=[];chest=[];hips=[];feet={side:[] for side in ['L','R']}
probe=Vector((-4.8587651,-2.4900517,4.9727192));rest=b['sword.R'].bone.matrix_local.inverted()
for tick in range(round((end-start)*4)+1):
 f=start+tick/4;s.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
 points.append(b['sword.R'].matrix@rest@probe);chest.append(b['chest'].matrix.to_quaternion());hips.append(b['pelvis'].head.copy())
 for side in feet:feet[side].append(b['foot.'+side].head.copy())
def span(values):return max((x-y).length for x in values for y in values)
peak=max((x-y).length*120 for x,y in zip(points,points[1:]));turn=max(2*math.acos(min(1,abs(x.dot(y)))) for x in chest for y in chest)
report={'clip':'SwordSlash','duration_s':(end-start)/30,'strike_source_duration_s':.533333333333,'peak_blade_probe_speed_m_s':peak,'blade_probe_travel_m':span(points),'chest_rotation_range_rad':turn,'hip_travel_m':span(hips),'foot_travel_m':{side:span(v) for side,v in feet.items()}}
(ROOT/'output/motion/ronin-slash-dynamics.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
assert report['duration_s']<2.5 and peak>20 and turn>.45 and span(hips)>.5 and max(report['foot_travel_m'].values())>.5, 'Slash lacks speed or whole-body commitment'

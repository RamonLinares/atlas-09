import bpy,json
from mathutils.bvhtree import BVHTree
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/RONIN-04.blend'))
o=bpy.data.objects['RONIN_04_Armor'];rig=bpy.data.objects['RONIN_04_RIG'];s=bpy.context.scene
parts={}
for name in ['shoulder.R','upper_arm.R','forearm.R','hand.R']:
 g=o.vertex_groups[name].index;parts[name]=[list(f.vertices) for f in o.data.polygons if o.data.vertices[f.vertices[0]].groups[0].group==g]
result={}
for name in ['BladeSalute','SwordSlash']:
 rig.animation_data.action=bpy.data.actions[name];rows=[]
 for f in range(1,int(rig.animation_data.action.frame_range[1])+1,3):
  s.frame_set(f);bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();p=[v.co.copy() for v in m.vertices];trees={n:BVHTree.FromPolygons(p,fs,all_triangles=True) for n,fs in parts.items()};rows.append({'frame':f,**{n:len(trees['shoulder.R'].overlap(trees[n])) for n in parts if n!='shoulder.R'}});e.to_mesh_clear()
 result[name]=rows
path=R/'output/ronin-04/shoulder-collision.json';path.write_text(json.dumps(result,indent=2));print({n:{part:max(x[part] for x in rows) for part in ['upper_arm.R','forearm.R','hand.R']} for n,rows in result.items()})

# The forearm and grip must never pass through the protector. Shared upper-arm
# seams at the closed hinge are reported separately, not treated as penetration.
for rows in result.values():
 assert all(row['forearm.R']==0 and row['hand.R']==0 for row in rows)
from mathutils import Vector
rig.animation_data.action=bpy.data.actions['SwordSlash'];edge=Vector((-.28816719,-.70580132,.6471508));axis=Vector((-.2719205,-.5876843,-.76202783));checks=[]
for frame in range(36,53):
 s.frame_set(frame-1);bpy.context.view_layer.update();hand=rig.pose.bones['hand.R'];before=(hand.matrix@hand.bone.matrix_local.inverted()).to_3x3()@axis
 s.frame_set(frame+1);bpy.context.view_layer.update();after=(hand.matrix@hand.bone.matrix_local.inverted()).to_3x3()@axis
 s.frame_set(frame);bpy.context.view_layer.update();rotation=(hand.matrix@hand.bone.matrix_local.inverted()).to_3x3();d=rotation@axis;e=rotation@edge;velocity=after-before;velocity-=d*velocity.dot(d);alignment=e.normalized().dot(velocity.normalized());checks.append(alignment)
assert min(checks)>.98,checks
(R/'output/ronin-04/blade-edge-validation.json').write_text(json.dumps({'sharp_edge_alignment_min':min(checks),'strike_frames_checked':len(checks)},indent=2))
print('SHARP_EDGE_ALIGNMENT',min(checks))

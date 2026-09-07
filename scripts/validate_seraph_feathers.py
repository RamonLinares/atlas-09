"""Validate compact deployment, rigid plates, independent feather motion and clearance."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/seraph-03'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/SERAPH-03.blend'));o=bpy.data.objects['SERAPH_03_Armor'];r=bpy.data.objects['SERAPH_03_RIG'];s=bpy.context.scene;r.animation_data.action=bpy.data.actions['WingDeploy'];specs=json.loads(r['Feather articulation']);groups={g.index:g.name for g in o.vertex_groups}
faces={};wing_ids=[]
for item in specs:
 name=item['name'];hub=Vector(item['hub']);ids={v.index for v in o.data.vertices if groups[v.groups[0].group]==name};wing_ids.extend(ids)
 faces[name]=[tuple(p.vertices) for p in o.data.polygons if all(i in ids and (o.data.vertices[i].co-hub).length>3.2 and o.data.attributes['original_vertex'].data[i].value>=0 for i in p.vertices)]
previous=None;step=0;low=1e9;contacts=[];first=None;last=None;spans={};angles={};joint_error=0
for tick in range(361):
 f=1+tick/2;s.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=[p.co.copy() for p in m.vertices];ev.to_mesh_clear();low=min(low,min(p.z for p in v));first=first or v;last=v
 quats=[r.pose.bones[x['name']].rotation_euler.to_quaternion() for x in specs]
 if previous:step=max(step,max(2*math.acos(min(1,abs(a.dot(b)))) for a,b in zip(previous,quats)))
 previous=quats
 for item in specs:
  b=r.pose.bones[item['name']];expected=b.parent.matrix@b.parent.bone.matrix_local.inverted()@Vector(item['head']);joint_error=max(joint_error,(b.head-expected).length)
 if tick in [0,180]:
  key='folded' if tick==0 else 'open';spans[key]=max(v[i].x for i in wing_ids)-min(v[i].x for i in wing_ids)
  dirs=[(r.pose.bones[x['name']].tail-r.pose.bones[x['name']].head).normalized() for x in specs if x['side']=='L'];angles[key]=max(a.angle(b) for a in dirs for b in dirs)
 trees={n:BVHTree.FromPolygons(v,p) for n,p in faces.items()}
 for i,a in enumerate(specs):
  for b in specs[i+1:]:
   pairs=trees[a['name']].overlap(trees[b['name']])
   if pairs:contacts.append({'time':tick/60,'a':a['name'],'b':b['name'],'triangles':len(pairs)})
report={'feathers':len(specs),'samples':361,'wing_width_m':spans,'feather_direction_spread_rad':angles,'minimum_floor_m':low,'max_half_frame_angle_rad':step,'hinge_position_error_m':joint_error,'loop_vertex_error_m':max((a-b).length for a,b in zip(first,last)),'distal_feather_contacts':contacts}
(OUT/'feather-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({**report,'distal_feather_contacts':contacts[:12],'contact_sample_count':len(contacts)}),flush=True)
assert len(specs)==10 and spans['folded']<spans['open']*.5 and angles['folded']<.12 and angles['open']>1.1
assert low>-.004 and step<.12 and joint_error<1e-4 and report['loop_vertex_error_m']<1e-4
assert not contacts,'Feather tips intersect during deployment'

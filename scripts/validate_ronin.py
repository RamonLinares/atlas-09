"""Validate rigid binding, anatomy isolation, UVs, and swept motion geometry."""
import bpy,json,math,numpy as np
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/ronin-04'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/RONIN-04.blend'))
o=bpy.data.objects['RONIN_04_Armor'];rig=bpy.data.objects['RONIN_04_RIG'];scene=bpy.context.scene
report={'rigid_vertices':all(len(v.groups)==1 and abs(v.groups[0].weight-1)<1e-6 for v in o.data.vertices),'rigid_faces':all(len({o.data.vertices[i].groups[0].group for i in f.vertices})==1 for f in o.data.polygons)}
assert report['rigid_vertices'] and report['rigid_faces']
report['uv_maps']=[]
for uv in o.data.uv_layers:
 bad=zero=0
 for face in o.data.polygons:
  p=[uv.data[i].uv[:] for i in face.loop_indices];bad+=any(c<-.0001 or c>1.0001 or not np.isfinite(c) for v in p for c in v)
  zero+=abs(sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p))))<2e-12
 report['uv_maps'].append({'name':uv.name,'out_of_bounds':int(bad),'zero_area':int(zero)})
 assert not bad and not zero,report['uv_maps']

def clear():
 for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
def sample(frame=1):
 scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',p);ev.to_mesh_clear();return p.reshape((-1,3))
rig.animation_data.action=None;clear();p=sample()
report['shoulder_protectors']=[]
for side,sign in [('L',1),('R',-1)]:
 ids=np.where((p[:,0]*sign>3.0)&(p[:,2]>11.0))[0]
 driver='upper_arm.'+side
 assert len(ids)>50
 assert all(o.vertex_groups[o.data.vertices[int(i)].groups[0].group].name==driver for i in ids)
 clear();rig.pose.bones[driver].rotation_euler.x=.8;q=sample()
 transform=rig.pose.bones[driver].matrix@rig.data.bones[driver].matrix_local.inverted()
 expected=np.array([tuple(transform@o.data.vertices[int(i)].co) for i in ids])
 error=float(np.linalg.norm(q[ids]-expected,axis=1).max())
 assert error<1e-5 and np.linalg.norm(q[ids]-p[ids],axis=1).max()>.2
 report['shoulder_protectors'].append({'side':side,'driver':driver,'sampled_vertices':len(ids),'transform_error_m':error})
clear()
# Independent anatomical cores exclude seam hardware and use source geometry.
domains={
 'legs':np.where((abs(p[:,0])<3.1)&(abs(p[:,0])>.5)&(p[:,2]>1.6)&(p[:,2]<6.3))[0],
 'torso':np.where((abs(p[:,0])<1)&(p[:,2]>10.5)&(p[:,2]<12.5))[0],
 'sword':np.where((p[:,0]<-4.4)&(p[:,2]>1)&(p[:,2]<4.5))[0],
 'left_arm':np.where((p[:,0]>3.3)&(p[:,2]>6.5)&(p[:,2]<9.8))[0],
 'right_arm':np.where((p[:,0]<-3.3)&(p[:,2]>7.1)&(p[:,2]<9.8))[0],
 'head':np.where((abs(p[:,0])<1)&(p[:,2]>13.7))[0]}
assert all(len(v)>15 for v in domains.values())
report['isolation']=[]
for name,moved in [('upper_arm.R',['right_arm','sword']),('upper_arm.L',['left_arm']),('thigh.R',['legs']),('thigh.L',['legs']),('head',['head']),('sword.R',['sword'])]:
 clear();rig.pose.bones[name].rotation_euler.x=.8;q=sample();movement={key:float(np.linalg.norm(q[ids]-p[ids],axis=1).max()) for key,ids in domains.items()}
 for key,value in movement.items():
  if key not in moved:assert value<1e-5,(name,key,value)
 assert any(movement[k]>.2 for k in moved)
 report['isolation'].append({'bone':name,'displacement_m':movement})
clear();edges=np.array([e.vertices[:] for e in o.data.edges]);report['animations']=[]
slash_report={'wrist_rotation_rad':0,'joint_gap_m':0,'half_frame_step_rad':0,'tip_positions':[]}
for name in ['Sentinel','BladeSalute','SwordSlash','Run','KneelFire','Backflip']:
 rig.animation_data.action=bpy.data.actions[name];start,end=map(int,rig.animation_data.action.frame_range);first=sample(start);last=sample(end);base=np.linalg.norm(first[edges[:,0]]-first[edges[:,1]],axis=1);low=1e9;stretch=0;motion=0;maxclear=0
 previous=None
 for frame in np.arange(start,end+.1,.5):
  q=sample(float(frame))
  if name=='SwordSlash':
   bones=rig.pose.bones
   slash_report['wrist_rotation_rad']=max(slash_report['wrist_rotation_rad'],bones['hand.R'].rotation_euler.to_quaternion().angle)
   for part in ['forearm.R','hand.R','sword.R']:
    b=bones[part];slash_report['joint_gap_m']=max(slash_report['joint_gap_m'],(b.head-b.parent.tail).length)
   current={n:bones[n].matrix.to_quaternion() for n in ['chest','upper_arm.R','forearm.R','hand.R','sword.R']}
   if previous:
    slash_report['half_frame_step_rad']=max(slash_report['half_frame_step_rad'],max(2*math.acos(min(1,abs(previous[n].dot(v)))) for n,v in current.items()))
   previous=current
   slash_report['tip_positions'].append(list(bones['sword.R'].tail))
  assert np.isfinite(q).all();low=min(low,float(q[:,2].min()));maxclear=max(maxclear,float(q[:,2].min()));stretch=max(stretch,float(abs(np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)-base).max()));motion=max(motion,float(np.linalg.norm(q-first,axis=1).max()))
 closure=float(np.linalg.norm(first-last,axis=1).max())
 assert low>-.004 and stretch<.0001 and closure<.0001 and motion>.01,(name,low,stretch,closure,motion)
 report['animations'].append({'name':name,'lowest_vertex_m':low,'rigid_edge_error_m':stretch,'loop_error_m':closure,'max_displacement_m':motion,'max_ground_clearance_m':maxclear})
positions=np.array(slash_report.pop('tip_positions'))
slash_report['sword_tip_sweep_m']=(positions.max(axis=0)-positions.min(axis=0)).tolist()
assert slash_report['wrist_rotation_rad']<1e-4 and slash_report['joint_gap_m']<1e-4, slash_report
assert slash_report['half_frame_step_rad']<.30 and slash_report['sword_tip_sweep_m'][0]>2, slash_report
report['sword_slash']=slash_report
blade=json.loads((OUT/'blade-orientation.json').read_text())
rig.animation_data.action=bpy.data.actions['SwordSlash']
sword=rig.pose.bones['sword.R'];rest=sword.bone.matrix_local.inverted()
probe=Vector(blade['blade_probe']);edge=Vector(blade['cutting_edge_direction'])
def blade_point(frame):
 scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
 return sword.matrix@rest@probe
alignment=[]
for frame in [40,42,44,46]:
 velocity=(blade_point(frame+.1)-blade_point(frame-.1)).normalized()
 blade_point(frame);cutting_edge=(sword.matrix@rest).to_3x3()@edge
 alignment.append(float(cutting_edge.dot(velocity)))
assert min(alignment)>.8,alignment
report['katana_cutting_edge']={'leading_edge_alignment':alignment,'minimum_required':.8}
report['packed_textures']=all(im.packed_file for im in bpy.data.images if im.type=='IMAGE' and im.name!='Render Result');assert report['packed_textures']
(OUT/'blender-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

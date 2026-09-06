"""Validate rigid binding, anatomy isolation, UVs, and swept motion geometry."""
import bpy,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/seraph-03'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/SERAPH-03.blend'))
o=bpy.data.objects['SERAPH_03_Armor'];rig=bpy.data.objects['SERAPH_03_RIG'];scene=bpy.context.scene
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
# Independent anatomical cores exclude seam hardware and use source geometry.
domains={'legs':np.where((abs(p[:,0])<2.5)&(p[:,2]>2.5)&(p[:,2]<8))[0],
 'torso':np.where((abs(p[:,0])<1)&(p[:,2]>10.5)&(p[:,2]<12.5)&(p[:,1]<1))[0],
 'wings':np.where((abs(p[:,0])>5)&(p[:,2]>12)&(p[:,1]>1.7))[0],
 'cannon':np.where((p[:,0]<-2.8)&(p[:,1]<-.7)&(p[:,2]>2)&(p[:,2]<8))[0],
 'left_arm':np.where((p[:,0]>3.2)&(p[:,2]>7)&(p[:,2]<10)&(p[:,1]<1.4))[0]}
assert all(len(v)>15 for v in domains.values())
# Match mirrored leg surfaces independently of the assigned bone groups. The
# source's legs are bilateral; the asymmetric cannon has no matching left leg.
from mathutils.kdtree import KDTree
left=[v for v in o.data.vertices if v.co.x>0 and v.co.z<9.0]
tree=KDTree(len(left))
for i,v in enumerate(left):tree.insert(v.co,i)
tree.balance();paired=0
for v in o.data.vertices:
 if v.co.x>=0 or v.co.z>=9.0:continue
 mirrored=v.co.copy();mirrored.x=-mirrored.x;co,index,distance=tree.find(mirrored)
 if distance>.002:continue
 a=o.vertex_groups[v.groups[0].group].name;b=o.vertex_groups[left[index].groups[0].group].name
 if b.startswith(('thigh.','shin.','foot.')):
  # Shared seam vertices can occur on either adjacent rigid leg section.
  assert a in ['thigh.R','shin.R','foot.R','pelvis'],(list(v.co),a,b);paired+=1
assert paired>500
report['mirrored_leg_vertices_checked']=paired
report['isolation']=[]
for name,moved in [('upper_arm.R','cannon'),('upper_arm.L','left_arm'),('thigh.R','legs'),('thigh.L','legs'),('wing_root.R','wings'),('wing_root.L','wings')]:
 clear();rig.pose.bones[name].rotation_euler.x=.8;q=sample();movement={key:float(np.linalg.norm(q[ids]-p[ids],axis=1).max()) for key,ids in domains.items()}
 for key,value in movement.items():
  if key!=moved:assert value<1e-5,(name,key,value)
 assert movement[moved]>.2
 report['isolation'].append({'bone':name,'displacement_m':movement})
clear();edges=np.array([e.vertices[:] for e in o.data.edges]);report['animations']=[]
for name in ['Sentinel','WingDeploy','Run','KneelFire','Backflip','Flight']:
 rig.animation_data.action=bpy.data.actions[name];start,end=map(int,rig.animation_data.action.frame_range);first=sample(start);last=sample(end);base=np.linalg.norm(first[edges[:,0]]-first[edges[:,1]],axis=1);low=1e9;stretch=0;motion=0;maxclear=0
 for frame in np.arange(start,end+.1,.5):
  q=sample(float(frame));assert np.isfinite(q).all();low=min(low,float(q[:,2].min()));maxclear=max(maxclear,float(q[:,2].min()));stretch=max(stretch,float(abs(np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)-base).max()));motion=max(motion,float(np.linalg.norm(q-first,axis=1).max()))
 closure=float(np.linalg.norm(first-last,axis=1).max())
 assert low>-.004 and stretch<.0001 and closure<.0001 and motion>.01,(name,low,stretch,closure,motion)
 report['animations'].append({'name':name,'lowest_vertex_m':low,'rigid_edge_error_m':stretch,'loop_error_m':closure,'max_displacement_m':motion,'max_ground_clearance_m':maxclear})
report['packed_textures']=all(im.packed_file for im in bpy.data.images if im.type=='IMAGE' and im.name!='Render Result');assert report['packed_textures']
(OUT/'blender-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

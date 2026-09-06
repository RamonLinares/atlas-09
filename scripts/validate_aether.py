"""Validate actual AETHER armor motion and independent anatomical bindings."""
import bpy,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/AETHER-02.blend'))
obj=bpy.data.objects['AETHER_02_Armor'];rig=bpy.data.objects['AETHER_02_RIG'];scene=bpy.context.scene
report={}
report['all_vertices_have_one_rigid_weight']=all(len(v.groups)==1 and abs(v.groups[0].weight-1)<1e-6 for v in obj.data.vertices)
report['faces_span_only_one_bone']=all(len({obj.data.vertices[vi].groups[0].group for vi in p.vertices})==1 for p in obj.data.polygons)
assert report['all_vertices_have_one_rigid_weight'] and report['faces_span_only_one_bone']
report['paired_chains']=all(n+'.L' in rig.data.bones and n+'.R' in rig.data.bones for n in ['shoulder','upper_arm','forearm','hand','thigh','shin','foot'])
assert report['paired_chains']
report['uv_maps']=[]
for layer in obj.data.uv_layers:
 outside=degenerate=0
 for f in obj.data.polygons:
  points=[layer.data[i].uv[:] for i in f.loop_indices]
  outside+=int(any(not np.isfinite(c) or c<-.0001 or c>1.0001 for p in points for c in p))
  area=abs(sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points))))*.5
  degenerate+=int(area<1e-12)
 report['uv_maps'].append({'name':layer.name,'out_of_bounds_faces':outside,'zero_area_faces':degenerate})
 assert outside==0 and degenerate==0
def sample(frame=1):
 scene.frame_set(frame);bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',a);ev.to_mesh_clear();return a.reshape((-1,3))
def clear():
 for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
rig.animation_data.action=None;clear();neutral=sample()
# Select known anatomical domains in rest coordinates, independently of weights.
leg_ids=[v.index for v in obj.data.vertices if abs(v.co.x)<2.25 and 2<v.co.z<8.4]
arm_ids=[v.index for v in obj.data.vertices if abs(v.co.x)>2.6 and 6.4<v.co.z<8.8]
assert len(leg_ids)>100 and len(arm_ids)>100
for side in ['L','R']:
 rig.pose.bones['upper_arm.'+side].rotation_euler.x=.9;rig.pose.bones['forearm.'+side].rotation_euler.x=-1.1
arms=sample();arm_leak=float(np.linalg.norm(arms[leg_ids]-neutral[leg_ids],axis=1).max())
assert arm_leak<1e-5;assert np.linalg.norm(arms[arm_ids]-neutral[arm_ids],axis=1).max()>.5
clear()
for side in ['L','R']:rig.pose.bones['thigh.'+side].rotation_euler.x=.7
legs=sample();leg_leak=float(np.linalg.norm(legs[arm_ids]-neutral[arm_ids],axis=1).max())
assert leg_leak<1e-5;assert np.linalg.norm(legs[leg_ids]-neutral[leg_ids],axis=1).max()>.5
report['anatomical_isolation']={'leg_vertices':len(leg_ids),'arm_vertices':len(arm_ids),'leg_motion_from_arms_m':arm_leak,'arm_motion_from_legs_m':leg_leak}
clear();edges=np.array([e.vertices[:] for e in obj.data.edges],dtype=np.int32)
report['animations']=[]
for name in ['Sentinel','Awaken','Run','KneelFire','Backflip']:
 rig.animation_data.action=bpy.data.actions[name];start,end=map(int,rig.animation_data.action.frame_range);first=sample(start);last=sample(end);base=np.linalg.norm(first[edges[:,0]]-first[edges[:,1]],axis=1);stretch=0;ground=1e9;clearance=-1e9;motion=0
 for frame in range(start,end+1,3):
  p=sample(frame);assert np.isfinite(p).all();stretch=max(stretch,float(abs(np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1)-base).max()));ground=min(ground,float(p[:,2].min()));clearance=max(clearance,float(p[:,2].min()));motion=max(motion,float(np.linalg.norm(p-first,axis=1).max()))
 closure=float(np.linalg.norm(first-last,axis=1).max());assert stretch<.0001 and closure<.0001 and ground>-.001 and motion>.01
 report['animations'].append({'name':name,'max_edge_stretch_m':stretch,'loop_error_m':closure,'lowest_vertex_m':ground,'max_clearance_m':clearance,'max_displacement_m':motion})
report['packed_textures']=all(im.packed_file for im in bpy.data.images if im.type=='IMAGE' and im.name!='Render Result')
assert report['packed_textures']
glass=next(m for m in obj.data.materials if 'opaque' in m.name);p=next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
report['opaque_glass']={'alpha':p.inputs['Alpha'].default_value,'transmission':p.inputs['Transmission Weight'].default_value,'roughness':p.inputs['Roughness'].default_value}
assert report['opaque_glass']['alpha']==1 and report['opaque_glass']['transmission']==0
(ROOT/'output/aether-02/blender-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

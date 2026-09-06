"""Audit the saved Blender deliverable, including deformation of actual vertices."""
import bpy,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/ATLAS-09.blend'))
obj=bpy.data.objects['ATLAS_09_Armor'];rig=bpy.data.objects['ATLAS_09_RIG'];scene=bpy.context.scene
report={}
report['packed_textures']=[{'name':im.name,'packed':bool(im.packed_file)} for im in bpy.data.images if im.type=='IMAGE' and im.name!='Render Result']
report['all_vertices_have_one_rigid_weight']=all(len(v.groups)==1 and abs(v.groups[0].weight-1)<1e-6 for v in obj.data.vertices)
report['faces_span_only_one_bone']=all(len({obj.data.vertices[vi].groups[0].group for vi in p.vertices})==1 for p in obj.data.polygons)
report['default_action']=rig.animation_data.action.name
report['paired_chains']=all(n+'.L' in rig.data.bones and n+'.R' in rig.data.bones for n in ['shoulder','upper_arm','forearm','hand','thigh','shin','foot'])
edges=np.array([e.vertices[:] for e in obj.data.edges],dtype=np.int32)
def evaluated(frame):
 scene.frame_set(frame);bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',a);ev.to_mesh_clear();return a.reshape((-1,3))
# Anatomical regression: source thigh panels next to the resting hands must
# remain still when only the arms move, then move with their own thigh.
# Use rest-space geometry, independent of the assigned groups under test.
panel_faces=[p for p in obj.data.polygons if p.material_index==0 and 3.35<abs(p.center.x)<4.15 and 8.0<p.center.z<10.0]
panel_ids=sorted({vi for p in panel_faces for vi in p.vertices})
assert panel_ids
assert all(obj.vertex_groups[obj.data.vertices[vi].groups[0].group].name=='thigh.'+('L' if obj.data.vertices[vi].co.x>0 else 'R') for vi in panel_ids)
rig.animation_data.action=None
def reset_pose():
 for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
reset_pose();neutral=evaluated(1)
for side in ['L','R']:
 rig.pose.bones['upper_arm.'+side].rotation_euler.x=1.0
 rig.pose.bones['forearm.'+side].rotation_euler.x=-1.2
 rig.pose.bones['hand.'+side].rotation_euler.z=.5
arms_raised=evaluated(1)
panel_error=float(np.linalg.norm(arms_raised[panel_ids]-neutral[panel_ids],axis=1).max())
assert panel_error<.00001
assert float(np.linalg.norm(arms_raised-neutral,axis=1).max())>1.0
reset_pose()
for side in ['L','R']:rig.pose.bones['thigh.'+side].rotation_euler.x=.6
legs_moved=evaluated(1)
panel_motion=float(np.linalg.norm(legs_moved[panel_ids]-neutral[panel_ids],axis=1).min())
assert panel_motion>.001  # Even vertices close to the hinge must follow it.
report['thigh_arm_isolation']={'panel_faces':len(panel_faces),'panel_vertices':len(panel_ids),'max_panel_motion_with_arms_m':panel_error,'min_panel_motion_with_thighs_m':panel_motion}
reset_pose()
report['animations']=[]
for name in ['Sentinel','Awaken','Run','KneelFire','Backflip']:
 rig.animation_data.action=bpy.data.actions[name];start,end=map(int,rig.animation_data.action.frame_range);rest=evaluated(start);last=evaluated(end);base_lengths=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);disp=0;stretch=0
 ground_min=1e9;ground_max=-1e9
 for frame in range(start,end+1,3):
  p=evaluated(frame);assert np.isfinite(p).all();disp=max(disp,float(np.linalg.norm(p-rest,axis=1).max()));lengths=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);stretch=max(stretch,float(np.abs(lengths-base_lengths).max()));ground_min=min(ground_min,float(p[:,2].min()));ground_max=max(ground_max,float(p[:,2].min()))
 report['animations'].append({'name':name,'max_vertex_displacement_m':disp,'max_rigid_edge_length_change_m':stretch,'loop_closure_max_error_m':float(np.linalg.norm(last-rest,axis=1).max()),'ground_min_m':ground_min,'max_clearance_m':ground_max})
assert report['all_vertices_have_one_rigid_weight'] and report['faces_span_only_one_bone'] and report['paired_chains']
assert all(a['max_rigid_edge_length_change_m']<.0001 and a['loop_closure_max_error_m']<.0001 for a in report['animations'])
(ROOT/'output/blender-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

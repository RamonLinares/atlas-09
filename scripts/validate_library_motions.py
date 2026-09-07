"""Validate transferred motion behavior on the evaluated armored meshes."""
import bpy,json,math,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];reports=[]
for asset in ['AETHER-02','ATLAS-09']:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/{asset}.blend'))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');obj=next(o for o in bpy.context.scene.objects if o.type=='MESH' and 'Armor' in o.name);scene=bpy.context.scene
 assert {a.name for a in bpy.data.actions}>={'Sentinel','Run','KneelFire','Backflip','Walk','PunchCombo','Collapse'}
 feet={s:[v.index for v in obj.data.vertices if any(g.group==obj.vertex_groups['foot.'+s].index for g in v.groups)] for s in ['L','R']}
 def sample(frame):
  scene.frame_set(int(frame),subframe=float(frame%1));bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();v=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',v);ev.to_mesh_clear();return v.reshape((-1,3))
 results=[]
 for clip in ['Walk','PunchCombo','Collapse']:
  rig.animation_data.action=bpy.data.actions[clip];start,end=rig.animation_data.action.frame_range
  first=sample(start);last=sample(end);low=1e9;highest_support=-1e9;head=[];hands={s:[] for s in ['L','R']}
  for f in np.arange(start,end+.01,.5):
   v=sample(f);assert np.isfinite(v).all();low=min(low,float(v[:,2].min()));highest_support=max(highest_support,min(float(v[feet[s],2].min()) for s in feet));head.append(rig.pose.bones['head'].head.z)
   for s in hands:hands[s].append(list(rig.pose.bones['hand.'+s].head))
  closure=float(np.linalg.norm(first-last,axis=1).max());travel={s:float(np.linalg.norm(np.asarray(hands[s])-hands[s][0],axis=1).max()) for s in hands}
  hold=float(np.linalg.norm(sample(end)-sample(end-10),axis=1).max())
  assert low>-.001,(asset,clip,'penetration',low)
  if clip!='Collapse':assert closure<.0001,(asset,clip,'closure',closure)
  if clip=='Walk':assert highest_support<.2,(asset,'walk support',highest_support)
  if clip=='PunchCombo':assert min(travel.values())>1.5,(asset,'punch travel',travel)
  if clip=='Collapse':assert head[-1]<head[0]*.35 and hold<.0001,(asset,'collapse hold',head[0],head[-1],hold)
  results.append({'clip':clip,'half_frame_samples':len(head),'lowest_vertex_m':low,'highest_support_foot_m':highest_support,'loop_error_m':closure if clip!='Collapse' else None,'hand_travel_m':travel,'head_height_start_end_m':[head[0],head[-1]],'final_hold_error_m':hold if clip=='Collapse' else None})
 reports.append({'asset':asset,'clips':results})
(ROOT/'output/motion/library-validation.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports,indent=2))

"""Check gait contacts and coordination from evaluated, baked armor motion."""
import bpy, json, math
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reports=[]
for asset,mesh_name,rig_name,stance in [('ATLAS-09','ATLAS_09_Armor','ATLAS_09_RIG',.44),('AETHER-02','AETHER_02_Armor','AETHER_02_RIG',.40)]:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender'/f'{asset}.blend'))
 scene=bpy.context.scene;obj=bpy.data.objects[mesh_name];rig=bpy.data.objects[rig_name]
 rig.animation_data.action=bpy.data.actions['Run'];start,end=rig.animation_data.action.frame_range
 groups={s:obj.vertex_groups['foot.'+s].index for s in ['L','R']}
 ids={s:[v.index for v in obj.data.vertices if any(g.group==groups[s] for g in v.groups)] for s in groups}
 samples=[]
 for frame in np.arange(start,end+.01,.5):
  scene.frame_set(int(frame),subframe=float(frame%1));bpy.context.view_layer.update()
  ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',v);ev.to_mesh_clear();v=v.reshape((-1,3))
  feet={}
  for side in ['L','R']:
   b=rig.pose.bones['foot.'+side];delta=b.matrix.to_3x3()@b.bone.matrix_local.to_3x3().inverted()
   feet[side]={'ankle':list(b.head),'lowest':float(v[ids[side],2].min()),'pitch':delta.to_euler().x}
  yaw={name:(rig.pose.bones[name].matrix.to_3x3()@rig.data.bones[name].matrix_local.to_3x3().inverted()).to_euler().z for name in ['pelvis','chest']}
  samples.append({'phase':float((frame-start)/(end-start)),'feet':feet,'lowest':float(v[:,2].min()),'yaw':yaw})
 hips=abs(rig.data.bones['thigh.L'].head_local.x-rig.data.bones['thigh.R'].head_local.x)
 widths=[abs(s['feet']['L']['ankle'][0]-s['feet']['R']['ankle'][0])/hips for s in samples]
 contact_errors=[];travel_errors=[]
 for side,offset in [('L',0),('R',.5)]:
  planted=[s for s in samples if .03<((s['phase']+offset)%1)<stance-.025]
  contact_errors.extend(abs(s['feet'][side]['lowest']) for s in planted)
  # Midfoot support should move backward at a constant speed in an in-place run.
  mid=[s for s in samples if stance*.30<((s['phase']+offset)%1)<stance*.50]
  phase=np.array([((s['phase']+offset)%1) for s in mid]);y=np.array([s['feet'][side]['ankle'][1] for s in mid])
  if len(mid)>=3:
   fit=np.polyfit(phase,y,1);travel_errors.extend(abs(y-np.polyval(fit,phase)))
 pitches=[s['feet']['L']['pitch'] for s in samples]
 report={'character':asset,'cycle_seconds':float((end-start)/scene.render.fps),'sampled_frames':len(samples),
  'foot_width_over_hip_width':[min(widths),max(widths)],'foot_pitch_degrees':[math.degrees(min(pitches)),math.degrees(max(pitches))],
  'max_planted_foot_ground_error_m':max(contact_errors),'lowest_armor_m':min(s['lowest'] for s in samples),
  'max_midfoot_travel_fit_error_m':max(travel_errors,default=0),
  'hip_yaw_degrees':[math.degrees(min(s['yaw']['pelvis'] for s in samples)),math.degrees(max(s['yaw']['pelvis'] for s in samples))],
  'chest_yaw_degrees':[math.degrees(min(s['yaw']['chest'] for s in samples)),math.degrees(max(s['yaw']['chest'] for s in samples))],
  'flight_fraction':sum(s['feet']['L']['lowest']>.025 and s['feet']['R']['lowest']>.025 for s in samples)/len(samples)}
 reports.append(report)
 print(json.dumps(report,indent=2))
 assert max(widths)<1.15, 'Foot placement remains too wide'
 assert min(pitches)<-.04 and max(pitches)>.40, 'Missing heel/toe roll'
 assert max(contact_errors)<.035 and report['lowest_armor_m']>-.035, 'Ground contact drift'
 assert report['max_midfoot_travel_fit_error_m']<.015, 'Planted foot slides irregularly'
 assert report['hip_yaw_degrees'][0]<-2 and report['chest_yaw_degrees'][1]>2, 'Torso is still locked'
 assert .02<report['flight_fraction']<.3, 'Excessive flight or no flight'
(ROOT/'output/motion/run-validation.json').write_text(json.dumps(reports,indent=2))

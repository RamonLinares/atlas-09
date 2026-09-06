"""Cannon-aware mechanical animation and independent rigid wing articulation."""
import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from motion_library import build_motions

def build_seraph_motions(rig,obj):
 scene=bpy.context.scene;bones=rig.pose.bones;rig.animation_data_create()
 def update():bpy.context.view_layer.update()
 def neutral():
  for b in bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
  update()
 def wings(fold,fan=0):
  for sign,side in [(1,'L'),(-1,'R')]:
   for part,angle,axis in [('wing_root',sign*fold,Vector((0,0,1))),('wing_outer',sign*fan,Vector((0,1,0)))]:
    b=bones[part+'.'+side];local=b.bone.matrix_local.to_3x3().inverted()@axis
    b.rotation_euler=Matrix.Rotation(angle,3,local).to_euler()
  update()
 def aim(name,direction):
  b=bones[name];rest=b.bone;q=(rest.tail_local-rest.head_local).rotation_difference(direction)@rest.matrix_local.to_quaternion()
  b.matrix=Matrix.Translation(b.head)@q.to_matrix().to_4x4();update()
 def cannon(u,kind):
  # Run carries the long cannon forward; swinging it like a human forearm
  # would sweep the barrel through the floor and the knees.
  root=bones['root'].matrix.to_3x3()
  if kind=='Run':
   aim('upper_arm.R',Vector((-.28,-.18,-1)))
   aim('forearm.R',Vector((-.14,-1,-.05+.04*math.sin(u*math.tau))))
  elif kind=='Backflip':
   aim('upper_arm.R',root@Vector((-.45,-.4,-.65)))
   aim('forearm.R',root@Vector((-.35,-1,.35)))
  wings(math.radians(72 if kind in ['Run','Backflip'] else 55),.06)
 report=build_motions(rig,obj,dict(run_frames=35,run_stance=.44,run_width=1.12,run_front=.75,run_back=2.1,
  run_compression=.38,run_bounce=.13,run_lean=.10,run_hip_twist=.04,run_chest_twist=.03,
  run_hip_roll=.008,run_shift=.03,run_toeoff=.48,run_recovery=2.6,run_arm_swing=.42,run_elbow=1.35,run_arm_out=.22,
  ankle_z=1.85,ankle_y=1.35,ankle_x=2.5,kneel_drop=4.3,kneel_front=(1.9,-2.5,1.85),kneel_back=(-1.3,5.0,2.9),
  crouch=1.15,landing=.9,tuck_width=.65,tuck_back=1.9,tuck_lift=3.8,jump=14,pivot=(0,.8,8.95),fire_interval=.64,
  pose_adjust=lambda name,u:cannon(u,name)))
 def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
 def idle(u):
  neutral();wings(math.radians(55)+.018*math.sin(u*math.tau),.06)
  bones['forearm.L'].rotation_euler.x=.035*(1-math.cos(u*math.tau))
 def deploy(u):
  neutral();open_=smooth(u/.3)*(1-smooth((u-.68)/.32))
  wings(math.radians(55)*(1-open_),-.10*open_)
  bones['chest'].rotation_euler.x=-.025*open_
 def flight(u):
  neutral();lift=smooth(u/.2)*(1-smooth((u-.78)/.22))
  bones['root'].matrix=Matrix.Translation((0,0,6*lift+.25*lift*math.sin(u*math.tau*2)))@bones['root'].bone.matrix_local;update()
  wings(math.radians(55)*(1-lift)+.08*math.sin(u*math.tau*2)*lift,-.12*lift)
  aim('upper_arm.R',Vector((-.3,-.25*lift,-1)))
  aim('forearm.R',Vector((-.2,-lift,-1+lift*.9)))
  bones['forearm.L'].rotation_euler.x=-.5*lift
  for side in ['L','R']:bones['shin.'+side].rotation_euler.x=.18*lift
 for name,frames,fn in [('Sentinel',181,idle),('WingDeploy',181,deploy),('Flight',241,flight)]:
  rig.animation_data.action=None;previous={}
  for frame in range(1,frames+1):
   fn((frame-1)/(frames-1));update()
   for b in bones:
    if b.name in previous:b.rotation_euler.make_compatible(previous[b.name])
    previous[b.name]=b.rotation_euler.copy();b.keyframe_insert('rotation_euler',frame=frame,group=b.name);b.keyframe_insert('location',frame=frame,group=b.name)
  a=rig.animation_data.action;a.name=name;a.use_fake_user=True;rig.animation_data.action=None
  track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,1,a);track.mute=True
  report.append({'name':name,'frames':frames,'duration':(frames-1)/30})
 # Bound interpolation as well as keyed poses and save per-clip swept bounds
 # for a stable camera that includes the wide wings and long cannon.
 root_up=bones['root'].bone.matrix_local.to_3x3().inverted()@Vector((0,0,1));bounds={}
 for item in report:
  print('SERAPH_MOTION_CHECK',item['name'],flush=True)
  a=bpy.data.actions[item['name']];rig.animation_data.action=a
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for c in bag.fcurves:
      for k in c.keyframe_points:k.interpolation='LINEAR'
  lifts=[0.]*item['frames']
  for i in range(item['frames']-1):
   for f in [0,.25,.5,.75,1]:
    scene.frame_set(i+1,subframe=f);update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();low=min(v.co.z for v in m.vertices);ev.to_mesh_clear()
    if low<0:lifts[i]=max(lifts[i],-low+.003);lifts[i+1]=max(lifts[i+1],-low+.003)
  lifts[0]=lifts[-1]=max(lifts[0],lifts[-1])
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for c in bag.fcurves:
      if c.data_path=='pose.bones["root"].location':
       for k in c.keyframe_points:k.co.y+=lifts[round(k.co.x)-1]*root_up[c.array_index]
  low=Vector((1e9,1e9,1e9));high=-low
  for frame in range(1,item['frames']+1):
   scene.frame_set(frame);update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
   coords=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',coords);coords=coords.reshape((-1,3))
   lo=coords.min(axis=0);hi=coords.max(axis=0)
   for axis in range(3):low[axis]=min(low[axis],float(lo[axis]));high[axis]=max(high[axis],float(hi[axis]))
   ev.to_mesh_clear()
  bounds[item['name']]={'min':list(low),'max':list(high)};item['interpolation_lift_m']=max(lifts)
 (Path(__file__).resolve().parents[1]/'src/seraph-motion-bounds.json').write_text(json.dumps(bounds,indent=2))
 rig.animation_data.action=None;neutral()
 return report

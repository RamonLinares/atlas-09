"""Sword-aware samurai motion with independent rigid skirt articulation."""
import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from motion_library import build_motions

def build_ronin_motions(rig,obj):
 scene=bpy.context.scene;bones=rig.pose.bones;rig.animation_data_create()
 def update():bpy.context.view_layer.update()
 def neutral():
  for b in bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
  update()
 def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
 def aim(name,direction):
  b=bones[name];rest=b.bone;q=(rest.tail_local-rest.head_local).rotation_difference(direction)@rest.matrix_local.to_quaternion()
  b.matrix=Matrix.Translation(b.head)@q.to_matrix().to_4x4();update()
 def arm(side,target):
  upper=bones['upper_arm.'+side];lower=bones['forearm.'+side];h=upper.head.copy();v=Vector(target)-h
  l1=upper.bone.length;l2=lower.bone.length;dist=min(l1+l2-.003,max(abs(l1-l2)+.003,v.length));axis=v.normalized()
  pole=Vector((1 if side=='L' else -1,0,-.3));pole-=axis*pole.dot(axis);pole.normalize()
  along=(l1*l1-l2*l2+dist*dist)/(2*dist);k=h+axis*along+pole*math.sqrt(max(0,l1*l1-along*along))
  aim('upper_arm.'+side,k-h);aim('forearm.'+side,Vector(target)-bones['forearm.'+side].head)
 def blade(direction):
  hand=bones['hand.R'];rest=hand.bone;sword=bones['sword.R'].bone
  delta=(sword.tail_local-sword.head_local).rotation_difference(Vector(direction))
  hand.matrix=Matrix.Translation(hand.head)@(delta@rest.matrix_local.to_quaternion()).to_matrix().to_4x4();update()
 def skirt():
  for side in ['L','R']:
   thigh=bones['thigh.'+side];b=bones['skirt.'+side]
   # Following the thigh from the shared hip pivot keeps armor off the leg.
   delta=thigh.matrix.to_3x3()@thigh.bone.matrix_local.to_3x3().inverted()
   b.matrix=Matrix.Translation(b.head)@delta.to_4x4()@b.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
  update()
 def adapt(name,u):
  root=bones['root'].matrix.to_3x3()
  if name=='Run':
   aim('upper_arm.R',Vector((-.35,.12,-1)));aim('forearm.R',Vector((-.22,-1,.05)))
   blade(Vector((-.55,.15,1)))
  elif name=='Backflip':
   aim('upper_arm.R',root@Vector((-.5,-.15,-1)));aim('forearm.R',root@Vector((-.3,-1,.2)))
   blade(root@Vector((-.7,-.15,1)))
  elif name=='KneelFire':
   seconds=u*8;b=smooth(seconds/2.15)*(1-smooth((seconds-6)/2))
   aim('upper_arm.R',Vector((-.35,-.3*b,-1)));aim('forearm.R',Vector((-.2,-b,-1+b)))
   rest=bones['sword.R'].bone;direction=(rest.tail_local-rest.head_local).normalized().lerp(Vector((-.7,-.1,1)).normalized(),b)
   blade(direction)
   recoil=.06*max(0,1-((seconds-2.4)%.48)/.1) if 2.4<=seconds<5.8 else 0
   aim('upper_arm.L',Vector((.3,-.8*b,-1+.5*b)))
   aim('forearm.L',Vector((.22,-.09,-1)).lerp(Vector((.02,-1,recoil)),b))
   aim('hand.L',Vector((.22,-.09,-1)).lerp(Vector((.02,-1,recoil)),b))
  skirt()
 report=build_motions(rig,obj,dict(run_frames=41,run_stance=.44,run_width=1.3,run_front=.7,run_back=1.8,
  run_compression=.4,run_bounce=.12,run_lean=.10,run_hip_twist=.035,run_chest_twist=.025,
  run_hip_roll=.008,run_shift=.03,run_toeoff=.45,run_recovery=2.2,run_arm_swing=.4,run_elbow=1.3,run_arm_out=.25,
  ankle_z=1.25,ankle_y=.15,ankle_x=2.45,kneel_drop=3.9,kneel_front=(2,-2,1.25),kneel_back=(-1.4,4.2,2.65),
  crouch=1.05,landing=.85,tuck_width=.65,tuck_back=1.6,tuck_lift=3.3,jump=14,pivot=(0,0,8.85),fire_interval=.48,
  pose_adjust=adapt))
 restblade=(bones['sword.R'].bone.tail_local-bones['sword.R'].bone.head_local).normalized()
 def idle(u):
  neutral();bones['chest'].rotation_euler.x=.006*math.sin(u*math.tau);bones['head'].rotation_euler.y=.025*math.sin(u*math.tau);update()
 def salute(u):
  neutral();b=smooth(u/.3)*(1-smooth((u-.68)/.32))
  arm('R',Vector((-3.55,-.25,8)).lerp(Vector((-3.4,-1.9,11.8)),b))
  blade(restblade.lerp(Vector((-.12,-.15,1)).normalized(),b))
  bones['head'].rotation_euler.x=.08*b;update()
 def curve(u,keys):
  if u<=keys[0][0]:return keys[0][1]
  for (ta,a),(tb,b) in zip(keys,keys[1:]):
   if u<=tb:return a+(b-a)*smooth((u-ta)/(tb-ta))
  return keys[-1][1]
 def slash(u):
  neutral()
  ready=curve(u,[(0,0),(.23,1),(.31,1),(.91,0),(1,0)])
  cut=curve(u,[(0,0),(.31,0),(.39,1),(.49,1),(.91,0),(1,0)])
  follow=curve(u,[(0,0),(.39,0),(.49,1),(.91,0),(1,0)])
  yaw=-.20*ready+.50*cut+.10*follow
  pitch=-.035*ready+.09*cut
  chest=bones['chest'];frame=Matrix.Rotation(yaw,3,'Z')@Matrix.Rotation(pitch,3,'X')
  chest.matrix=Matrix.Translation(chest.head)@frame.to_4x4()@chest.bone.matrix_local.to_quaternion().to_matrix().to_4x4();update()
  # The arm carries a firm grip through a diagonal cut. The sword and wrist
  # keep their rest relationship instead of independently aiming the blade.
  poses={
   'upper_arm.R':(-.50*ready-.14*cut, -.18*ready+.48*cut, .12*ready),
   'forearm.R':(-2.05*ready+.98*cut+.33*follow, -.25*ready+.68*cut, 0),
   'upper_arm.L':(-.25*ready, .10*ready, -.06*ready),
   'forearm.L':(-.75*ready, .05*ready,0),
  }
  for name,(x,z,y) in poses.items():
   b=bones[name];rotation=frame@Matrix.Rotation(z,3,'Z')@Matrix.Rotation(y,3,'Y')@Matrix.Rotation(x,3,'X')
   b.matrix=Matrix.Translation(b.head)@rotation.to_4x4()@b.bone.matrix_local.to_quaternion().to_matrix().to_4x4();update()
  bones['hand.R'].rotation_euler=(0,0,0);bones['sword.R'].rotation_euler=(0,0,0)
  bones['head'].rotation_euler.y=-.3*yaw;update()
 from ronin_punch_combo import make_punch_combo,refine_docked_keys
 combo=make_punch_combo(rig)
 for name,frames,fn in [('Sentinel',181,idle),('BladeSalute',181,salute),('SwordSlash',121,slash),('PunchCombo',361,combo)]:
  rig.animation_data.action=None;previous={}
  for frame in range(1,frames+1):
   fn((frame-1)/(frames-1));update()
   for b in bones:
    if b.name in previous:b.rotation_euler=b.rotation_euler.to_quaternion().to_euler('XYZ',previous[b.name])
    previous[b.name]=b.rotation_euler.copy();b.keyframe_insert('rotation_euler',frame=frame,group=b.name);b.keyframe_insert('location',frame=frame,group=b.name)
  a=rig.animation_data.action;a.name=name;a.use_fake_user=True;rig.animation_data.action=None
  track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,1,a);track.mute=True
  report.append({'name':name,'frames':frames,'duration':(frames-1)/30})
 # Set sampled body tracks to linear before resolving the magnetic constraint
 # between frames; the refinement must use the same interpolation as the GLB.
 for layer in bpy.data.actions['PunchCombo'].layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for c in bag.fcurves:
     for k in c.keyframe_points:k.interpolation='LINEAR'
 refine_docked_keys(rig)
 # Bound interpolation as well as keyed poses and save per-clip swept bounds
 # for a stable camera that includes the katana throughout each motion.
 root_up=bones['root'].bone.matrix_local.to_3x3().inverted()@Vector((0,0,1));bounds={}
 for item in report:
  print('RONIN_MOTION_CHECK',item['name'],flush=True)
  a=bpy.data.actions[item['name']];rig.animation_data.action=a
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for c in bag.fcurves:
      for k in c.keyframe_points:k.interpolation='LINEAR'
  lifts=[0.]*item['frames']
  for i in range(item['frames']-1):
   for f in [0,.25,.5,.75,1]:
    scene.frame_set(i+1,subframe=f);update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();pts=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',pts);low=float(pts.reshape((-1,3))[:,2].min());ev.to_mesh_clear()
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
 (Path(__file__).resolve().parents[1]/'src/ronin-motion-bounds.json').write_text(json.dumps(bounds,indent=2))
 rig.animation_data.action=None;neutral()
 return report

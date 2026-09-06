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
  pole=Vector((.35 if side=='L' else -.35,-.2,-1));pole-=axis*pole.dot(axis);pole.normalize()
  along=(l1*l1-l2*l2+dist*dist)/(2*dist);k=h+axis*along+pole*math.sqrt(max(0,l1*l1-along*along))
  aim('upper_arm.'+side,k-h);aim('forearm.'+side,Vector(target)-bones['forearm.'+side].head)
 # The bright beveled edge was identified in a normal-facing blade close-up.
 # These orthogonal axes come from the actual long blade, not the grip bone.
 blade_axis=Vector((-.2719205,-.5876843,-.76202783)).normalized()
 blade_edge=Vector((-.28816719,-.70580132,.6471508)).normalized()
 source_frame=Matrix((blade_edge,blade_axis.cross(blade_edge),blade_axis)).transposed()
 def blade(direction,edge=None,roll_blend=1):
  hand=bones['hand.R'];rest=hand.bone;sword=bones['sword.R'].bone
  d=Vector(direction).normalized()
  delta=(sword.tail_local-sword.head_local).rotation_difference(d)
  if edge is not None:
   e=Vector(edge);e=(e-d*e.dot(d)).normalized()
   target_frame=Matrix((e,d.cross(e),d)).transposed()
   oriented=(target_frame@source_frame.transposed()).to_quaternion()
   delta=delta.slerp(oriented,roll_blend)
  hand.matrix=Matrix.Translation(hand.head)@(delta@rest.matrix_local.to_quaternion()).to_matrix().to_4x4();update()
 def protector(amount):
  # Independent hinge: the upper arm is parented to the chest so lifting
  # its protector does not displace the shoulder joint or the solved grip.
  b=bones['shoulder.R'];r=b.bone.matrix_local
  b.matrix=Matrix.Translation(r.translation)@Matrix.Rotation(-.15*amount,4,'Z')@Matrix.Rotation(.9*amount,4,'Y')@r.to_quaternion().to_matrix().to_4x4();update()
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
  protector(smooth(b/.4))
  arm('R',Vector((-3.55,-.25,8)).lerp(Vector((-4,-2.8,10.6)),b))
  blade(restblade.lerp(Vector((-.12,-.15,1)).normalized(),b),Vector((0,-1,0)),b)
  bones['head'].rotation_euler.x=.08*b;update()
 def slash(u):
  neutral();ready=smooth(u/.23);strike=smooth((u-.28)/.16);return_=smooth((u-.64)/.36)
  protector(smooth(ready*(1-return_)/.4))
  target=Vector((-3.55,-.25,8)).lerp(Vector((-4,-2.8,10.8)),ready).lerp(Vector((-3.4,-2.0,9.2)),strike).lerp(Vector((-3.55,-.25,8)),return_)
  arm('R',target)
  direction=restblade.lerp(Vector((-.3,.05,1)).normalized(),ready).lerp(Vector((-.55,-1,-.18)).normalized(),strike).lerp(restblade,return_)
  blade(direction,Vector((-.55,-1,-.18)).normalized()-Vector((-.3,.05,1)).normalized(),ready*(1-return_));update()
 for name,frames,fn in [('Sentinel',181,idle),('BladeSalute',181,salute),('SwordSlash',121,slash)]:
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

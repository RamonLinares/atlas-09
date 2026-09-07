"""Retarget selected Quaternius CC0 clips to the two rigid mecha skeletons."""
import bpy, json, struct, math, bisect
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
ROOT=Path(__file__).resolve().parents[1]

class MotionSource:
 def __init__(self,path):
  raw=Path(path).read_bytes();n=struct.unpack_from('<I',raw,12)[0];self.doc=json.loads(raw[20:20+n]);self.blob=raw[28+n:]
  self.nodes=self.doc['nodes'];self.names={n.get('name',str(i)):i for i,n in enumerate(self.nodes)}
  self.parents={child:i for i,n in enumerate(self.nodes) for child in n.get('children',[])}
  self.accessors={};self.clips={a['name']:a for a in self.doc['animations']}
  self.rest=self.sample(None,0)
 def values(self,index):
  if index not in self.accessors:
   a=self.doc['accessors'][index];v=self.doc['bufferViews'][a['bufferView']];size={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
   start=v.get('byteOffset',0)+a.get('byteOffset',0);flat=struct.unpack_from('<'+'f'*(a['count']*size),self.blob,start)
   self.accessors[index]=[flat[i:i+size] for i in range(0,len(flat),size)]
  return self.accessors[index]
 def duration(self,name):return max(self.values(s['input'])[-1][0] for s in self.clips[name]['samplers'])
 def sample(self,name,t):
  transforms=[{'translation':n.get('translation',[0,0,0]),'rotation':n.get('rotation',[0,0,0,1]),'scale':n.get('scale',[1,1,1])} for n in self.nodes]
  if name:
   a=self.clips[name]
   for c in a['channels']:
    s=a['samplers'][c['sampler']];times=[x[0] for x in self.values(s['input'])];values=self.values(s['output']);path=c['target']['path']
    i=max(0,min(len(times)-2,bisect.bisect_right(times,t)-1));f=max(0,min(1,(t-times[i])/(times[i+1]-times[i]))) if len(times)>1 else 0
    x,y=values[i],values[min(i+1,len(values)-1)]
    if s.get('interpolation')=='STEP':value=x
    elif path=='rotation':
     q=Quaternion((x[3],*x[:3])).slerp(Quaternion((y[3],*y[:3])),f);value=[q.x,q.y,q.z,q.w]
    else:value=[a+(b-a)*f for a,b in zip(x,y)]
    transforms[c['target']['node']][path]=value
  world={};conversion=Matrix.Rotation(math.pi/2,4,'X')
  def get(i):
   if i not in world:
    v=transforms[i];q=v['rotation'];m=Matrix.LocRotScale(Vector(v['translation']),Quaternion((q[3],*q[:3])),Vector(v['scale']))
    world[i]=(get(self.parents[i]) if i in self.parents else conversion)@m
   return world[i]
  return {name:get(i) for name,i in self.names.items()}

def retarget_motions(rig,obj,clip_names=None,timescale_override=None,pose_adjust=None):
 scene=bpy.context.scene;bones=rig.pose.bones;scene.render.fps=30
 sources=[MotionSource(ROOT/f'assets/animations/quaternius/UAL{i}_selected.glb') for i in [1,2]]
 src=sources[0];rest=src.rest
 height=14 if 'AETHER' in rig.name else 18;heavy=height==18
 legscale=(bones['thigh.L'].bone.length+bones['shin.L'].bone.length)/(rest['thigh_l'].translation-rest['foot_l'].translation).length
 timescale=1.20 if heavy else 1.0
 if timescale_override is not None:timescale=timescale_override
 mapping={'pelvis':'pelvis','chest':'spine_03','head':'Head'}
 for s,side in [('l','L'),('r','R')]:
  mapping.update({f'upper_arm.{side}':f'upperarm_{s}',f'forearm.{side}':f'lowerarm_{s}',f'hand.{side}':f'hand_{s}',f'thigh.{side}':f'thigh_{s}',f'shin.{side}':f'calf_{s}',f'foot.{side}':f'foot_{s}'})
 child={'upperarm':'lowerarm','lowerarm':'hand','thigh':'calf','calf':'foot'}
 calibration={}
 for target,source in mapping.items():
  t=bones[target].bone;canonical=t.matrix_local.to_quaternion()
  prefix=source.rsplit('_',1)[0]
  if prefix in child:
   end=child[prefix]+'_'+source[-1];direction=rest[end].translation-rest[source].translation
   canonical=(t.tail_local-t.head_local).rotation_difference(direction)@canonical
  elif target.startswith('hand.'):
   fore=bones['forearm.'+target[-1]].bone
   direction=rest['hand_'+source[-1]].translation-rest['lowerarm_'+source[-1]].translation
   canonical=(t.tail_local-t.head_local).rotation_difference(direction)@canonical
  calibration[target]=rest[source].to_quaternion().inverted()@canonical
 footverts={s:[v.co-bones['foot.'+s].bone.head_local for v in obj.data.vertices if any(g.group==obj.vertex_groups['foot.'+s].index for g in v.groups)] for s in ['L','R']}
 def update():bpy.context.view_layer.update()
 def clear():
  for b in bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
  update()
 def rotate(name,q):
  b=bones[name];b.matrix=Matrix.Translation(b.head)@q.to_matrix().to_4x4();update()
 def aim(name,direction):
  b=bones[name];q=(b.tail-b.head).rotation_difference(direction)@b.matrix.to_quaternion();rotate(name,q)
 def pose(sample,kind,settle=0):
  clear();pelvis0=rest['pelvis'].translation;pelvis=sample['pelvis'].translation
  delta=(pelvis-pelvis0)*legscale
  bones['root'].matrix=Matrix.Translation(delta)@bones['root'].bone.matrix_local;update()
  for name in ['pelvis','chest','head']:
   q=sample[mapping[name]].to_quaternion()@calibration[name];rotate(name,q)
   if name=='chest' and kind=='Collapse':
    # The source bends through three spine bones; our solid chest has one.
    # Transfer the anatomical torso direction as well as its axial twist.
    current=bones['head'].head-bones['chest'].head
    direction=sample['Head'].translation-sample['spine_01'].translation
    q=current.rotation_difference(direction)@bones['chest'].matrix.to_quaternion();rotate('chest',q)
  # Shoulder housings stay attached to the chest; limb rotations come from
  # the source's global orientation, calibrated from T-pose to our A-pose.
  for side,s in [('L','l'),('R','r')]:
   sign=1 if side=='L' else -1
   for part in ['upper_arm','forearm','hand','thigh','shin','foot']:
    name=part+'.'+side;q=sample[mapping[name]].to_quaternion()@calibration[name];rotate(name,q)
   if kind!='Collapse':
    # Give the armored elbows room outside the ribcage without changing the
    # source's timing or strike direction.
    b=bones['upper_arm.'+side];direction=(b.tail-b.head).normalized()
    if direction.z<-.15 and sign*direction.x<.22:
     direction.x=sign*.22;aim('upper_arm.'+side,direction)
     for part in ['forearm','hand']:
      name=part+'.'+side;rotate(name,sample[mapping[name]].to_quaternion()@calibration[name])
    # Human boots are much thinner. Re-solve the legs to the source foot
    # trajectory with clearance computed from the actual mecha sole.
    source_foot=sample['foot_'+s].translation;source_rest=rest['foot_'+s].translation
    ankle=bones['foot.'+side].bone.head_local.copy()
    ankle.x=bones['thigh.'+side].bone.head_local.x+(source_foot.x-source_rest.x)*legscale
    ankle.y+=(source_foot.y-source_rest.y)*legscale
    qfoot=bones['foot.'+side].matrix.to_quaternion();deltafoot=qfoot@bones['foot.'+side].bone.matrix_local.to_quaternion().inverted()
    support=-min((deltafoot@v).z for v in footverts[side])
    # Both source heel and toe touching define support, including toe-off.
    toe=sample['ball_'+s].translation
    source_low=min(source_foot.z-.104,toe.z-.015)
    ankle.z=support+max(0,source_low)*legscale
    thigh=bones['thigh.'+side];shin=bones['shin.'+side];h=thigh.head.copy();v=ankle-h
    l1=thigh.bone.length;l2=shin.bone.length;dist=max(abs(l1-l2)+.001,min(l1+l2-.001,v.length));axis=v.normalized()
    pole=sample['calf_'+s].translation-sample['thigh_'+s].translation;pole-=axis*pole.dot(axis)
    if pole.length<.001:pole=Vector((0,-1,0))-axis*axis.dot(Vector((0,-1,0)))
    pole.normalize();along=(l1*l1-l2*l2+dist*dist)/(2*dist);k=h+axis*along+pole*math.sqrt(max(0,l1*l1-along*along))
    aim('thigh.'+side,k-h);aim('shin.'+side,ankle-bones['shin.'+side].head);rotate('foot.'+side,qfoot)
  update()
  if pose_adjust:pose_adjust()
  ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear()
  if low<0:
   bones['root'].matrix=Matrix.Translation((0,0,-low))@bones['root'].matrix;update()
  if kind=='Collapse' and settle>0:
   # Let the back/arms settle onto the floor, then bend the knees to keep the
   # thick boots above it. A human foot-only correction left the entire heavy
   # torso suspended above the floor at the end of the source death motion.
   ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
   body_low=min(v.co.z for v in mesh.vertices if not obj.vertex_groups[obj.data.vertices[v.index].groups[0].group].name.startswith(('foot.','shin.','thigh.')));ev.to_mesh_clear()
   bones['root'].matrix=Matrix.Translation((0,0,-max(0,body_low)*settle))@bones['root'].matrix;update()
   for side in ['L','R']:
    foot=bones['foot.'+side];qfoot=foot.matrix.to_quaternion();deltafoot=qfoot@foot.bone.matrix_local.to_quaternion().inverted()
    support=-min((deltafoot@v).z for v in footverts[side]);ankle=foot.head.copy();ankle.z=max(ankle.z,support)
    thigh=bones['thigh.'+side];shin=bones['shin.'+side];h=thigh.head.copy();v=ankle-h
    l1=thigh.bone.length;l2=shin.bone.length;dist=max(abs(l1-l2)+.001,min(l1+l2-.001,v.length));axis=v.normalized()
    pole=Vector((0,0,1));pole-=axis*pole.dot(axis);pole.normalize()
    along=(l1*l1-l2*l2+dist*dist)/(2*dist);k=h+axis*along+pole*math.sqrt(max(0,l1*l1-along*along))
    aim('thigh.'+side,k-h);aim('shin.'+side,ankle-bones['shin.'+side].head);rotate('foot.'+side,qfoot)
   ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low2=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear()
   if low2<0:bones['root'].matrix=Matrix.Translation((0,0,-low2))@bones['root'].matrix;update()
  return max(0,-low)
 def blend(a,b,f):
  return {name:Matrix.LocRotScale(a[name].translation.lerp(b[name].translation,f),a[name].to_quaternion().slerp(b[name].to_quaternion(),f),Vector((1,1,1))) for name in a}
 # Preserve original jab/cross timing and add the hook plus its recovery.
 # Crossfades join clips with different guard poses, then return to the jab
 # guard so the full combination loops without a pose jump.
 segments=[(sources[0],'Punch_Jab'),(sources[0],'Punch_Cross'),(sources[1],'Melee_Hook'),(sources[1],'Melee_Hook_Rec')]
 durations=[s.duration(n) for s,n in segments];transition=.18;combo_duration=sum(durations)+transition*len(segments)+.25
 def combo(t):
  cursor=0;first=segments[0][0].sample(segments[0][1],0)
  for i,((source,name),duration) in enumerate(zip(segments,durations)):
   if t<=cursor+duration:return source.sample(name,t-cursor)
   cursor+=duration;last=source.sample(name,duration)
   dest=segments[i+1][0].sample(segments[i+1][1],0) if i+1<len(segments) else first
   if t<=cursor+transition:
    f=(t-cursor)/transition;return blend(last,dest,f*f*(3-2*f))
   cursor+=transition
  return first
 specs=[('Walk',src.duration('Walk_Loop'),lambda t:src.sample('Walk_Loop',t)),('PunchCombo',combo_duration,combo),('Collapse',src.duration('Death01')+.6,lambda t:src.sample('Death01',min(t,src.duration('Death01'))))]
 if clip_names is not None:specs=[spec for spec in specs if spec[0] in clip_names]
 report=[]
 rig.animation_data.action=None
 for name,duration,sampler in specs:
  frames=round(duration*timescale*30)+1;previous={};maxlift=0
  for frame in range(1,frames+1):
   t=(frame-1)/(frames-1)*duration;sample=sampler(t);settle=max(0,min(1,(t-.75)/.5));settle=settle*settle*(3-2*settle)
   maxlift=max(maxlift,pose(sample,name,settle if name=='Collapse' else 0))
   for b in bones:
    q=b.rotation_quaternion
    if b.name in previous and q.dot(previous[b.name])<0:q.negate()
    previous[b.name]=q.copy();b.keyframe_insert('rotation_quaternion',frame=frame,group=b.name);b.keyframe_insert('location',frame=frame,group=b.name)
  action=rig.animation_data.action;action.name=name;action.use_fake_user=True
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for curve in bag.fcurves:
      for key in curve.keyframe_points:key.interpolation='LINEAR'
  rig.animation_data.action=None;track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,1,action);track.mute=True
  report.append({'name':name,'duration':(frames-1)/30,'frames':frames,'source_clips':([n for s,n in segments] if name=='PunchCombo' else ['Walk_Loop' if name=='Walk' else 'Death01']),'max_ground_correction_m':maxlift,'playback':'once, hold final pose' if name=='Collapse' else 'loop'})
 clear()
 # Existing clips use Euler curves; restore their rotation mode and identity.
 for b in bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0)
 # The new action quaternion curves require matching per-action modes. Bake
 # them to Euler now so all exported clips and Blender playback share one mode.
 for item in report:
  action=bpy.data.actions[item['name']];rig.animation_data.action=action
  for b in bones:b.rotation_mode='QUATERNION'
  samples=[]
  for frame in range(1,item['frames']+1):
   scene.frame_set(frame);samples.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in bones})
  rig.animation_data.action=None;previous={}
  for b in bones:b.rotation_mode='XYZ'
  for frame,poses in enumerate(samples,1):
   for b in bones:
    q,loc=poses[b.name];e=q.to_euler('XYZ',previous.get(b.name)) if b.name in previous else q.to_euler('XYZ');previous[b.name]=e.copy();b.rotation_euler=e;b.location=loc
    b.keyframe_insert('rotation_euler',frame=frame,group=b.name);b.keyframe_insert('location',frame=frame,group=b.name)
  baked=rig.animation_data.action;baked.name=item['name']+'_baked';baked.use_fake_user=True
  for layer in baked.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for curve in bag.fcurves:
      for key in curve.keyframe_points:key.interpolation='LINEAR'
  rig.animation_data.action=None
  for track in list(rig.animation_data.nla_tracks):
   if track.name==item['name']:rig.animation_data.nla_tracks.remove(track)
  bpy.data.actions.remove(action);baked.name=item['name'];track=rig.animation_data.nla_tracks.new();track.name=item['name'];track.strips.new(item['name'],1,baked);track.mute=True
 # Rigid boots can sweep slightly below their endpoint contact planes while
 # the player interpolates rotations. Bound that swept motion at eighth-frames
 # and lift the adjacent root keys by the required (local) contact envelope.
 # This preserves the action's timing and prevents between-key floor clipping.
 root_up=bones['root'].bone.matrix_local.to_3x3().inverted()@Vector((0,0,1))
 for item in report:
  action=bpy.data.actions[item['name']];rig.animation_data.action=action
  lifts=[0.0]*item['frames']
  for i in range(item['frames']-1):
   deficit=0
   for fraction in [.125,.25,.375,.5,.625,.75,.875]:
    scene.frame_set(i+1,subframe=fraction);update()
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear()
    deficit=max(deficit,-low)
   if deficit>.0001:lifts[i]=max(lifts[i],deficit+.002);lifts[i+1]=max(lifts[i+1],deficit+.002)
  if item['name']!='Collapse':lifts[0]=lifts[-1]=max(lifts[0],lifts[-1])
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for curve in bag.fcurves:
      if curve.data_path=='pose.bones["root"].location':
       for key in curve.keyframe_points:
        amount=lifts[round(key.co.x)-1]*root_up[curve.array_index]
        key.co.y+=amount;key.handle_left.y+=amount;key.handle_right.y+=amount
  item['max_interpolation_contact_lift_m']=max(lifts)
 rig.animation_data.action=None
 for b in bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
 update()
 return report

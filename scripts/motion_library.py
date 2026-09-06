"""Authored mechanical motion, baked into portable Blender/glTF keyframes."""
import bpy, bmesh, math
from mathutils import Vector, Matrix

def add_hardware(obj, rig):
    metal=bpy.data.materials.new('Joint housings — blackened steel');metal.use_nodes=True
    p=metal.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.025,.035,.04,1);p.inputs['Metallic'].default_value=.85;p.inputs['Roughness'].default_value=.42
    trim=bpy.data.materials.new('Actuator collars — worn bronze');trim.use_nodes=True
    p=trim.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.18,.14,.065,1);p.inputs['Metallic'].default_value=.8;p.inputs['Roughness'].default_value=.5
    glow=bpy.data.materials.new('Cannon reactor emission');glow.use_nodes=True
    p=glow.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.025,.3,.36,1);p.inputs['Emission Color'].default_value=(.12,.8,1,1);p.inputs['Emission Strength'].default_value=4
    pieces=[]
    def bind(o,name,material):
        o.data.materials.append(material);o.vertex_groups.new(name=name).add(list(range(len(o.data.vertices))),1,'REPLACE')
        for layer in o.data.uv_layers:layer.name='Atlas_Surface'
        if not o.data.uv_layers:o.data.uv_layers.new(name='Atlas_Surface')
        light=o.data.uv_layers.new(name='Atlas_Lightmap')
        for a,b in zip(light.data,o.data.uv_layers['Atlas_Surface'].data):a.uv=b.uv
        for f in o.data.polygons:f.use_smooth=True
        pieces.append(o)
    def sphere(center,radius,bone):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=radius,location=center)
        bind(bpy.context.object,bone,metal)
    def cylinder(center,radius,length,direction,bone,material):
        bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=radius,depth=length,location=center)
        o=bpy.context.object;o.rotation_euler=Vector(direction).to_track_quat('Z','Y').to_euler();bind(o,bone,material)
    for side in ['L','R']:
        for name,r in [('thigh',1.0),('shin',.88),('foot',.69),('upper_arm',.9),('forearm',.72),('hand',.61)]:
            b=rig.data.bones[name+'.'+side];sphere(b.head_local,r,name+'.'+side)
            if name in ['shin','forearm']:
                cylinder(b.head_local,r*.78,r*2.15,(1,0,0),name+'.'+side,trim)
    sphere((0,0,10.4),1.5,'chest');sphere((0,-.15,15.7),.72,'head')
    # An integrated pulse cannon beside the right forearm; its socket exports too.
    direction=Vector((-.17,-.065,-.983)).normalized();center=Vector((-6.9,-.1,9.0))
    cylinder(center,.46,2.65,direction,'forearm.R',metal)
    for offset in [-1.08,.35,1.15]:cylinder(center+direction*offset,.53,.2,direction,'forearm.R',trim)
    cylinder(center+direction*1.34,.34,.1,direction,'forearm.R',glow)
    bpy.ops.object.empty_add(type='ARROWS',location=center+direction*1.43)
    muzzle=bpy.context.object;muzzle.name='Muzzle_R';muzzle.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    world=muzzle.matrix_world.copy();muzzle.parent=rig;muzzle.parent_type='BONE';muzzle.parent_bone='forearm.R';muzzle.matrix_world=world
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
    for o in pieces:o.select_set(True)
    bpy.context.view_layer.objects.active=obj;bpy.ops.object.join()
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bm.to_mesh(obj.data);bm.free();obj.data.update()
    return muzzle

def build_motions(rig,obj,profile=None):
    scene=bpy.context.scene
    bones=rig.pose.bones
    p=dict(ankle_z=1.7,ankle_y=0,ankle_x=3.65,
           kneel_drop=5.72,kneel_front=(3.3,-3.7,1.7),kneel_back=(-2.25,5.27,3.12),
           crouch=1.65,landing=1.5,tuck_width=.8,tuck_back=2.1,tuck_lift=4.8,jump=10.0,pivot=(0,0,9.1),
           run_frames=35,run_stance=.44,run_width=2.15,run_front=.85,run_back=2.5,
           run_compression=.42,run_bounce=.16,run_lean=.12,run_hip_twist=.065,run_chest_twist=.045,
           run_hip_roll=.012,run_shift=.055,run_toeoff=.48,run_recovery=2.5,
           run_arm_swing=.44,run_elbow=1.35,run_arm_out=.20)
    if profile:p.update(profile)
    rear_group=obj.vertex_groups['shin.R'].index
    rear_indices=[v.index for v in obj.data.vertices if any(g.group==rear_group for g in v.groups)]
    def update():bpy.context.view_layer.update()
    def clear():
        for b in bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
        update()
    def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
    def lerp(a,b,t):return Vector(a).lerp(Vector(b),t)
    def aim(name,direction):
        b=bones[name];rest=b.bone;delta=(rest.tail_local-rest.head_local).rotation_difference(Vector(direction))
        b.matrix=Matrix.Translation(b.head) @ (delta @ rest.matrix_local.to_quaternion()).to_matrix().to_4x4();update()
    def world_rotation(name,angle):
        b=bones[name];b.matrix=Matrix.Translation(b.head) @ Matrix.Rotation(angle,4,'X') @ b.bone.matrix_local.to_quaternion().to_matrix().to_4x4();update()
    def leg(side,ankle,foot_angle=0):
        thigh=bones['thigh.'+side];shin=bones['shin.'+side];h=thigh.head.copy();a=Vector(ankle)
        l1=thigh.bone.length;l2=shin.bone.length;v=a-h;dist=min(l1+l2-.002,max(abs(l1-l2)+.002,v.length));axis=v.normalized()
        pole=Vector((0,-1,0));pole-=axis*pole.dot(axis)
        if pole.length<.001:pole=Vector((0,0,-1))
        pole.normalize();along=(l1*l1-l2*l2+dist*dist)/(2*dist);height=math.sqrt(max(0,l1*l1-along*along));k=h+axis*along+pole*height
        aim('thigh.'+side,k-h);aim('shin.'+side,a-bones['shin.'+side].head);world_rotation('foot.'+side,foot_angle)
    def arms(left,right,bend=.65):
        for side,angle in [('L',left),('R',right)]:
            world_rotation('upper_arm.'+side,angle);world_rotation('forearm.'+side,angle-bend);world_rotation('hand.'+side,angle-bend)
    def base(lower=0,lean=0):
        clear();bones['root'].matrix=Matrix.Translation((0,0,lower))@bones['root'].bone.matrix_local;update();world_rotation('pelvis',lean);world_rotation('chest',lean*1.3)
    # Solve foot contact from the actual rigid boot geometry. In the old cycle
    # every boot stayed flat and a root translation lifted planted feet.
    foot_points={}
    for side in ['L','R']:
        name='foot.'+side;group=obj.vertex_groups[name].index;origin=rig.data.bones[name].head_local
        foot_points[side]=[v.co-origin for v in obj.data.vertices if any(g.group==group for g in v.groups)]
    def foot_support(side,pitch):
        rotation=Matrix.Rotation(pitch,3,'X')
        points=foot_points[side]
        # Keep the forefoot's ground travel continuous through toe-off.
        toe=min(points,key=lambda v:v.y)
        return -min((rotation@v).z for v in points),toe.y-(rotation@toe).y
    def hermite(t,a,b,va,vb,span):
        return (2*t**3-3*t*t+1)*a+(t**3-2*t*t+t)*va*span+(-2*t**3+3*t*t)*b+(t**3-t*t)*vb*span
    def curve(phase,keys):
        for (ta,a,va),(tb,b,vb) in zip(keys,keys[1:]):
            if phase<=tb+1e-9:return hermite((phase-ta)/(tb-ta),a,b,va,vb,tb-ta)
        return keys[-1][1]
    def world_euler(name,lean,roll=0,yaw=0):
        b=bones[name]
        rotation=Matrix.Rotation(yaw,4,'Z')@Matrix.Rotation(roll,4,'Y')@Matrix.Rotation(lean,4,'X')
        b.matrix=Matrix.Translation(b.head)@rotation@b.bone.matrix_local.to_quaternion().to_matrix().to_4x4();update()
    def run(u):
        theta=u*math.tau;duty=p['run_stance'];speed=(p['run_front']+p['run_back'])/duty
        clear()
        # Compression during support; a small rise toward flight, without
        # translating the feet after their contact solve.
        root_z=-p['run_compression']+p['run_bounce']*math.cos(4*math.pi*(u-.47))
        bones['root'].matrix=Matrix.Translation((p['run_shift']*math.sin(theta),0,root_z))@bones['root'].bone.matrix_local;update()
        world_euler('pelvis',p['run_lean'],p['run_hip_roll']*math.sin(theta),-p['run_hip_twist']*math.cos(theta))
        chest_yaw=p['run_chest_twist']*math.cos(theta)
        world_euler('chest',p['run_lean']*1.1,-p['run_hip_roll']*.4*math.sin(theta),chest_yaw)
        for sign,side,offset in [(1,'L',0),(-1,'R',.5)]:
            phase=(u+offset)%1
            if phase<=duty:
                # Heel settling, midfoot support, then a forefoot pivot.
                settle=smooth(phase/(duty*.28))
                roll=smooth((phase-duty*.52)/(duty*.48))
                pitch=-.08*(1-settle)+p['run_toeoff']*roll
                height,roll_y=foot_support(side,pitch)
                y=p['ankle_y']-p['run_front']+speed*phase+roll_y
            else:
                pitch=curve(phase,[(duty,p['run_toeoff'],0),(.60,.60,0),(.84,-.08,0),(1,-.08,0)])
                height,_=foot_support(side,pitch)
                clearance=curve(phase,[(duty,0,0),(.61,p['run_recovery'],0),(.84,.45,-5),(1,0,0)])
                height+=max(0,clearance)
                _,toeoff_y=foot_support(side,p['run_toeoff'])
                _,landing_y=foot_support(side,-.08)
                y=p['ankle_y']+curve(phase,[
                    (duty,p['run_back']+toeoff_y,speed),
                    (.61,p['run_back']*1.05,-speed*.5),
                    (.87,-p['run_front']*1.65,0),
                    (1,-p['run_front']+landing_y,speed)])
            leg(side,(sign*p['run_width'],y,height),pitch)
        # Elbows stay flexed and swing opposite the legs, with enough lateral
        # clearance for armor but without carrying over the wide A-pose.
        shoulder_frame=Matrix.Rotation(chest_yaw,3,'Z')@Matrix.Rotation(p['run_lean']*1.1,3,'X')
        for sign,side in [(1,'L'),(-1,'R')]:
            swing=sign*p['run_arm_swing']*math.cos(theta)
            elbow=p['run_elbow']+.10*math.sin(theta+(.0 if side=='L' else math.pi))
            upper=Vector((sign*p['run_arm_out'],math.sin(swing),-math.cos(swing)))
            lower=Vector((sign*p['run_arm_out']*.45,math.sin(swing-elbow),-math.cos(swing-elbow)))
            aim('upper_arm.'+side,shoulder_frame@upper)
            aim('forearm.'+side,shoulder_frame@lower)
            aim('hand.'+side,shoulder_frame@lower)
        update()
    def kneel(u):
        seconds=u*8;blend=smooth(seconds/2.15)*(1-smooth((seconds-6)/2))
        base(-p['kneel_drop']*blend,.015*blend)
        front_rest=(p['ankle_x'],p['ankle_y'],p['ankle_z'])
        leg('L',lerp(front_rest,p['kneel_front'],blend))
        leg('R',lerp((-p['ankle_x'],p['ankle_y'],p['ankle_z']),p['kneel_back'],blend),math.pi*.5*blend)
        recoil=0
        if 2.4<=seconds<5.8:
            phase=(seconds-2.4)%.32;recoil=.07*max(0,1-phase/.1)
        world_rotation('upper_arm.R',-1.07*blend+recoil*.4)
        world_rotation('forearm.R',-math.pi*.5*blend+recoil)
        world_rotation('hand.R',-math.pi*.5*blend+recoil)
        world_rotation('upper_arm.L',-.7*blend);world_rotation('forearm.L',-1.4*blend)
        world_rotation('hand.L',-1.4*blend);world_rotation('head',-.04*blend)
        # The armored knee pad is thicker than its pivot sphere. Seat that pad,
        # then solve the front leg again so the planted boot stays on the floor.
        if blend>0:
            ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();low=min(m.vertices[i].co.z for i in rear_indices);ev.to_mesh_clear()
            if low<0:
                bones['root'].matrix=Matrix.Translation((0,0,-low))@bones['root'].matrix;update()
                leg('L',lerp(front_rest,p['kneel_front'],blend))
    def backflip(u):
        # Compress, launch, tuck for a full backward rotation, then absorb landing.
        air=max(0,min(1,(u-.22)/.56))
        prep=smooth(u/.18)*(1-smooth((u-.18)/.12))
        landing=smooth((u-.78)/.06)*(1-smooth((u-.84)/.16))
        tuck=math.sin(math.pi*air)**1.2
        lower=-p['crouch']*prep-p['landing']*landing
        base(lower, .12*(prep+landing))
        for s,side in [(1,'L'),(-1,'R')]:leg(side,(s*(p['ankle_x']-p['tuck_width']*tuck),p['ankle_y']+p['tuck_back']*tuck,p['ankle_z']+p['tuck_lift']*tuck))
        arms(.6*prep-2.15*tuck,.6*prep-2.15*tuck,.4+.7*tuck)
        jump=p['jump']*math.sin(math.pi*air)**.85
        angle=-math.tau*smooth(air)
        pivot=Vector(p['pivot']);root=bones['root']
        root.matrix=Matrix.Translation(pivot+Vector((0,.7*math.sin(math.pi*air),jump))) @ Matrix.Rotation(angle,4,'X') @ Matrix.Translation(-pivot) @ root.matrix
        update()
    report=[]
    for name,frames,fn in [('Run',p['run_frames'],run),('KneelFire',241,kneel),('Backflip',109,backflip)]:
        rig.animation_data.action=None;previous={};max_correction=0
        for frame in range(1,frames+1):
            fn((frame-1)/(frames-1))
            # Final contact pass uses actual armor vertices, not an estimated box.
            ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();lowest=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear()
            if lowest<0:
                correction=-lowest;max_correction=max(correction,max_correction)
                bones['root'].matrix=Matrix.Translation((0,0,correction))@bones['root'].matrix;update()
            for b in bones:
                if b.name in previous:b.rotation_euler.make_compatible(previous[b.name])
                previous[b.name]=b.rotation_euler.copy()
                b.keyframe_insert('rotation_euler',frame=frame,group=b.name);b.keyframe_insert('location',frame=frame,group=b.name)
        action=rig.animation_data.action;action.name=name;action.use_fake_user=True
        if name=='Run':
            # These are sampled IK poses; Bezier handle easing overshoots the
            # planted-foot path. Match glTF's linear interpolation for the bake.
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for fcurve in bag.fcurves:
                            for key in fcurve.keyframe_points:key.interpolation='LINEAR'
        rig.animation_data.action=None;track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,1,action);track.mute=True
        report.append({'name':name,'frames':frames,'duration':(frames-1)/30,'max_ground_correction_m':max_correction})
    clear()
    rig['Motion notes']='Run is in-place. KneelFire drops onto the right knee, holds a firing pose, then stands. Backflip uses authored root motion around the pelvis. All controls are baked into ordinary bone keyframes.'
    return report

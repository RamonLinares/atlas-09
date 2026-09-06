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
    p=dict(run_drop=.75,run_bob=.22,stride=2.7,ankle_z=1.7,ankle_y=0,ankle_x=3.65,run_x=3.35,step_lift=2.7,
           kneel_drop=5.72,kneel_front=(3.3,-3.7,1.7),kneel_back=(-2.25,5.27,3.12),
           crouch=1.65,landing=1.5,tuck_width=.8,tuck_back=2.1,tuck_lift=4.8,jump=10.0,pivot=(0,0,9.1),flight=.42)
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
    def run(u):
        theta=u*math.tau;base(-p['run_drop']+p['run_bob']*math.cos(theta*2),.14)
        for s,side,offset in [(1,'L',0),(-1,'R',.5)]:
            phase=(u+offset)%1
            if phase<.5:y=p['ankle_y']-p['stride']+2*p['stride']*(phase/.5);z=p['ankle_z']
            else:
                f=(phase-.5)/.5;y=p['ankle_y']+p['stride']-2*p['stride']*smooth(f);z=p['ankle_z']+p['step_lift']*math.sin(math.pi*f)
            leg(side,(s*p['run_x'],y,z))
        arms(.72*math.cos(theta),-.72*math.cos(theta),.72)
        bones['head'].rotation_euler.y=.035*math.sin(theta);update()
        flight=p['flight']*max(0,math.cos(theta*2))**4
        bones['root'].matrix=Matrix.Translation((0,0,flight))@bones['root'].matrix;update()
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
    for name,frames,fn in [('Run',43,run),('KneelFire',241,kneel),('Backflip',109,backflip)]:
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
        rig.animation_data.action=None;track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,1,action);track.mute=True
        report.append({'name':name,'frames':frames,'duration':(frames-1)/30,'max_ground_correction_m':max_correction})
    clear()
    rig['Motion notes']='Run is in-place. KneelFire drops onto the right knee, holds a firing pose, then stands. Backflip uses authored root motion around the pelvis. All controls are baked into ordinary bone keyframes.'
    return report

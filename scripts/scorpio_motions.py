"""Continuous mechanical motion with attached claws and a measured tail chain."""
import bpy, math, json, numpy as np
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
from motion_library import build_motions
from scorpio_anatomy import TAIL_NAMES, BARREL_AXIS


def build_scorpio_motions(rig,obj):
    scene=bpy.context.scene;bones=rig.pose.bones;rig.animation_data_create()
    def update():bpy.context.view_layer.update()
    def neutral():
        for b in bones:
            b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
        update()
    def smooth(x):
        x=max(0.,min(1.,float(x)));return x*x*(3-2*x)
    def curve(u,keys):
        if u<=keys[0][0]:return keys[0][1]
        for (ta,a),(tb,b) in zip(keys,keys[1:]):
            if u<=tb:
                t=smooth((u-ta)/(tb-ta));return a*(1-t)+b*t
        return keys[-1][1]
    def axis(name):
        b=bones[name].bone;return (b.tail_local-b.head_local).normalized()
    def aim(name,direction):
        b=bones[name];q=axis(name).rotation_difference(Vector(direction).normalized())@b.bone.matrix_local.to_quaternion()
        b.matrix=Matrix.Translation(b.head)@q.to_matrix().to_4x4();update()
    def front_leg(target):
        h=bones['thigh.L'].head.copy();a=Vector(target)
        l1=bones['thigh.L'].bone.length;l2=bones['shin.L'].bone.length
        v=a-h;d=v.normalized();dist=min(l1+l2-.002,max(abs(l1-l2)+.002,v.length))
        pole=Vector((0,-1,0));pole-=d*pole.dot(d);pole.normalize()
        along=(l1*l1-l2*l2+dist*dist)/(2*dist)
        k=h+d*along+pole*math.sqrt(max(0,l1*l1-along*along))
        aim('thigh.L',k-h);aim('shin.L',a-bones['shin.L'].head)
        aim('foot.L',axis('foot.L'))
    def body_frame():
        return bones['chest'].matrix.to_3x3()@bones['chest'].bone.matrix_local.to_3x3().inverted()
    def carry(blend,phase=0):
        frame=body_frame()
        for sign,side in [(1,'L'),(-1,'R')]:
            sway=.08*sign*math.sin(phase*math.tau)
            targets=[('upper_arm',Vector((sign*.30,-.23+sway,-1))),
                     ('forearm',Vector((sign*.28,-1,.10-sway))),
                     ('hand',Vector((sign*.30,-1,-.04)))]
            for part,target in targets:
                name=part+'.'+side
                local=axis(name).lerp(target.normalized(),blend).normalized()
                orientation=frame @ (axis(name).rotation_difference(local) @ bones[name].bone.matrix_local.to_quaternion()).to_matrix()
                bones[name].matrix=Matrix.Translation(bones[name].head)@orientation.to_4x4();update()
    # Counter-bending advances the upper arc without collapsing the tail into
    # the body. Each hinge follows its own real coupling; no joint translates.
    tail_pitch=[.05,.04,.035,.03,.02,0,-.01,-.02,-.03,-.04,-.05]
    def tail_pose(amount=0,sway=0,phase=0):
        for i,name in enumerate(TAIL_NAMES):
            b=bones[name];r=b.bone.matrix_local.to_3x3()
            pitch=tail_pitch[i]*amount
            yaw=sway*math.sin(phase+i*.35)/(1+i*.15)
            b.rotation_euler=(r.inverted()@Matrix.Rotation(pitch,3,'X')@Matrix.Rotation(yaw,3,'Z')@r).to_euler()
            b.location=(0,0,0)
        update()
    def adapt(name,u):
        if name=='Run':
            carry(1,u);tail_pose(-.12+.025*math.sin(u*math.tau),.004,u*math.tau)
        elif name=='KneelFire':
            seconds=u*8;b=smooth(seconds/2.15)*(1-smooth((seconds-6)/2))
            carry(.90*b);tail_pose(.10*b)
            recoil=.018*max(0,1-((seconds-2.4)%.48)/.12) if 2.4<=seconds<5.8 else 0
            # Aim the actual barrel forward, with angular recoil at its hinge.
            desired=BARREL_AXIS.lerp(Vector((0,-1,recoil)).normalized(),b)
            aim('stinger',desired)
            # Seat the full knee shield as well as the shin. Re-solve the
            # front leg after seating so its boot is not lifted with the root.
            ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
            low=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear()
            if low<0:
                bones['root'].matrix=Matrix.Translation((0,0,-low))@bones['root'].matrix;update()
                front_leg(Vector((3.1,-1.2,1.2)).lerp(Vector((2.1,-3.6,1.2)),b))
        elif name=='Backflip':
            air=max(0,min(1,(u-.22)/.56));tuck=math.sin(math.pi*air)**1.2
            prep=smooth(u/.18)*(1-smooth((u-.18)/.12))
            landing=smooth((u-.78)/.06)*(1-smooth((u-.84)/.16))
            carry(.88*max(tuck,prep,landing));tail_pose(-.06*tuck)
        update()
    report=build_motions(rig,obj,dict(
        run_frames=43,run_stance=.46,run_width=1.85,run_front=.65,run_back=1.50,
        run_compression=.28,run_bounce=.10,run_lean=.08,run_hip_twist=.025,run_chest_twist=.02,
        run_hip_roll=.008,run_shift=.025,run_toeoff=.32,run_recovery=1.50,
        run_arm_swing=.30,run_elbow=1.2,run_arm_out=.25,
        ankle_z=1.20,ankle_y=-1.20,ankle_x=3.10,
        kneel_drop=3.60,kneel_front=(2.1,-3.6,1.20),kneel_back=(-2.1,1.9,2.25),
        crouch=.75,landing=.80,tuck_width=.4,tuck_back=1.2,tuck_lift=2.7,
        jump=10,pivot=(0,-1.45,6.80),fire_interval=.48,pose_adjust=adapt))

    def idle(u):
        neutral();t=u*math.tau
        bones['chest'].rotation_euler.x=.004*math.sin(t)
        bones['head'].rotation_euler.z=.018*math.sin(t)
        tail_pose(.025*math.sin(t),.0025,t)
    def torso(pitch,yaw=0):
        b=bones['chest']
        b.matrix=Matrix.Translation(b.head)@Matrix.Rotation(yaw,4,'Z')@Matrix.Rotation(pitch,4,'X')@b.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
        update()
    def stinger_strike(u):
        neutral()
        # Rearward cock, a 0.24-second whip, then a measured return.
        wind=curve(u,[(0,0),(.22,1),(.30,1),(.34,0),(1,0)])
        hit=curve(u,[(0,0),(.30,0),(.34,1),(.38,1),(.72,0),(1,0)])
        ready=curve(u,[(0,0),(.20,.75),(.44,.75),(.80,0),(1,0)])
        torso(.12*hit-.065*wind)
        carry(ready)
        wind_angles=[-.16,-.06,-.03,0,.02,.02,.02,.02,.02,.02,.02]
        hit_angles=[.35,.12,.10,.04,-.02,-.02,-.02,-.02,-.02,-.02,-.02]
        for i,name in enumerate(TAIL_NAMES):
            bone=bones[name];r=bone.bone.matrix_local.to_3x3()
            bone.rotation_euler=(r.inverted()@Matrix.Rotation(wind_angles[i]*wind+hit_angles[i]*hit,3,'X')@r).to_euler()
        update()
        # Keep the stinger aligned with the whipping tail instead of cancelling
        # its forward travel by independently aiming back at the rest direction.
        bones['head'].rotation_euler.x=-.025*hit
    def claw_slash(u):
        neutral()
        pitch=yaw=0
        for sign,delay in [(-1,0),(1,.38)]:
            t=u-delay
            ready=curve(t,[(0,0),(.16,1),(.31,1),(.58,0)])
            hit=curve(t,[(0,0),(.19,0),(.25,1),(.29,1),(.58,0)])
            yaw+=sign*(.12*ready-.34*hit)
            pitch+=.105*hit-.035*ready
        torso(pitch,yaw)
        frame=body_frame()
        for sign,side,delay in [(-1,'R',0),(1,'L',.38)]:
            t=u-delay
            ready=curve(t,[(0,0),(.16,1),(.31,1),(.58,0)])
            hit=curve(t,[(0,0),(.19,0),(.25,1),(.29,1),(.58,0)])
            # Authored joint orientations avoid an IK elbow branch flip during
            # the fast reversal from the wide pullback to the forward hit.
            for part,cock,contact in [
                ('upper_arm',(sign*.95,.20,-.15),(sign*.18,-1,-.15)),
                ('forearm',(sign*.85,.05,.50),(sign*.12,-1,.10)),
                ('hand',(sign*.65,-.30,.45),(-sign*.15,-1,-.05))]:
                name=part+'.'+side;bone=bones[name];rest=bone.bone.matrix_local.to_quaternion()
                wind_q=axis(name).rotation_difference(Vector(cock).normalized())@rest
                hit_q=axis(name).rotation_difference(Vector(contact).normalized())@rest
                orientation=rest.slerp(wind_q,ready).slerp(hit_q,hit)
                bone.matrix=Matrix.Translation(bone.head)@(frame@orientation.to_matrix()).to_4x4();update()
        tail_pose(-.06*math.sin(u*math.pi)**2,.002,u*math.tau)
    for name,frames,fn in [('Sentinel',181,idle),('StingerStrike',181,stinger_strike),('ClawSlash',121,claw_slash)]:
        rig.animation_data.action=None;previous={}
        for frame in range(1,frames+1):
            fn((frame-1)/(frames-1));update()
            for b in bones:
                if b.name in previous:b.rotation_euler=b.rotation_euler.to_quaternion().to_euler('XYZ',previous[b.name])
                previous[b.name]=b.rotation_euler.copy()
                b.keyframe_insert('rotation_euler',frame=frame,group=b.name)
                b.keyframe_insert('location',frame=frame,group=b.name)
        a=rig.animation_data.action;a.name=name;a.use_fake_user=True;rig.animation_data.action=None
        track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,1,a);track.mute=True
        report.append({'name':name,'frames':frames,'duration':(frames-1)/30})
    root_up = bones['root'].bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, 1))
    bounds = {}
    for item in report:
        a = bpy.data.actions[item['name']]
        rig.animation_data.action = a
        for layer in a.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for c in bag.fcurves:
                        for k in c.keyframe_points:
                            k.interpolation = 'LINEAR'
        lifts = [0.0] * item['frames']
        for i in range(item['frames'] - 1):
            for f in [0, .25, .5, .75, 1]:
                scene.frame_set(i + 1, subframe=f)
                update()
                ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
                m = ev.to_mesh()
                pts = np.empty(len(m.vertices) * 3, dtype=np.float32)
                m.vertices.foreach_get('co', pts)
                low = float(pts.reshape((-1, 3))[:, 2].min())
                ev.to_mesh_clear()
                if low < 0:
                    lifts[i] = max(lifts[i], -low + .003)
                    lifts[i + 1] = max(lifts[i + 1], -low + .003)
        lifts[0] = lifts[-1] = max(lifts[0], lifts[-1])
        for layer in a.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for c in bag.fcurves:
                        if c.data_path == 'pose.bones["root"].location':
                            for k in c.keyframe_points:
                                k.co.y += lifts[round(k.co.x) - 1] * root_up[c.array_index]
        low = Vector((1e9, 1e9, 1e9))
        high = -low
        for frame in range(1, item['frames'] + 1):
            scene.frame_set(frame)
            update()
            ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            m = ev.to_mesh()
            coords = np.empty(len(m.vertices) * 3, dtype=np.float32)
            m.vertices.foreach_get('co', coords)
            coords = coords.reshape((-1, 3))
            lo = coords.min(axis=0)
            hi = coords.max(axis=0)
            for axis in range(3):
                low[axis] = min(low[axis], float(lo[axis]))
                high[axis] = max(high[axis], float(hi[axis]))
            ev.to_mesh_clear()
        bounds[item['name']] = {
            'min': [round(float(v), 3) for v in low],
            'max': [round(float(v), 3) for v in high],
            'center': [round(float(v), 3) for v in (low + high) / 2],
            'size': [round(float(v), 3) for v in (high - low)],
            'interpolation_lift_m': round(float(max(lifts)), 4)
        }
    (Path(__file__).resolve().parents[1] / 'src/scorpio-motion-bounds.json').write_text(json.dumps(bounds, indent=2))
    rig.animation_data.action = None
    neutral()
    return report

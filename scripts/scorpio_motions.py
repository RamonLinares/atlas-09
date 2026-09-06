"""Tail-aware predatory motion with articulated segmented stinger and pincer claws."""
import bpy, math, json, numpy as np
from pathlib import Path
from mathutils import Matrix, Vector
from motion_library import build_motions

def build_scorpio_motions(rig, obj):
    scene = bpy.context.scene
    bones = rig.pose.bones
    rig.animation_data_create()
    
    def update():
        bpy.context.view_layer.update()
        
    def neutral():
        for b in bones:
            b.rotation_mode = 'XYZ'
            b.rotation_euler = (0, 0, 0)
            b.location = (0, 0, 0)
            b.scale = (1, 1, 1)
        update()
        
    def smooth(x):
        x = max(0.0, min(1.0, float(x)))
        return x * x * (3 - 2 * x)
        
    def aim(name, direction):
        b = bones[name]
        rest = b.bone
        q = (rest.tail_local - rest.head_local).rotation_difference(direction) @ rest.matrix_local.to_quaternion()
        b.matrix = Matrix.Translation(b.head) @ q.to_matrix().to_4x4()
        update()
        
    def arm(side, target):
        upper = bones['upper_arm.' + side]
        lower = bones['forearm.' + side]
        h = upper.head.copy()
        v = Vector(target) - h
        l1 = upper.bone.length
        l2 = lower.bone.length
        dist = min(l1 + l2 - .003, max(abs(l1 - l2) + .003, v.length))
        axis = v.normalized()
        pole = Vector((1 if side == 'L' else -1, 0, -.3))
        pole -= axis * pole.dot(axis)
        pole.normalize()
        along = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
        k = h + axis * along + pole * math.sqrt(max(0, l1 * l1 - along * along))
        aim('upper_arm.' + side, k - h)
        aim('forearm.' + side, Vector(target) - bones['forearm.' + side].head)
        
    def adapt(name, u):
        root = bones['root'].matrix.to_3x3()
        if name == 'Run':
            # Claws held forward and slightly inward to avoid leg collision
            aim('upper_arm.R', Vector((-.35, -.22, -1)))
            aim('forearm.R', Vector((-.22, -.9, -.2 + .06 * math.sin(u * math.tau))))
            aim('upper_arm.L', Vector((.35, -.22, -1)))
            aim('forearm.L', Vector((.22, -.9, -.2 - .06 * math.sin(u * math.tau))))
            # Tail lowers slightly as aerodynamic counterweight
            bones['tail_01'].rotation_euler.x = .12 + .03 * math.sin(u * math.tau)
            bones['tail_02'].rotation_euler.x = -.08
            bones['tail_03'].rotation_euler.x = -.10
            bones['tail_04'].rotation_euler.x = .06
            bones['stinger'].rotation_euler.x = .10
            bones['stinger'].rotation_euler.z = .04 * math.sin(u * math.tau)
        elif name == 'Backflip':
            aim('upper_arm.R', root @ Vector((-.45, -.3, -.7)))
            aim('forearm.R', root @ Vector((-.3, -.9, .2)))
            aim('upper_arm.L', root @ Vector((.45, -.3, -.7)))
            aim('forearm.L', root @ Vector((.3, -.9, .2)))
            bones['tail_01'].rotation_euler.x = -.2
            bones['tail_02'].rotation_euler.x = -.25
            bones['tail_03'].rotation_euler.x = .15
            bones['tail_04'].rotation_euler.x = .2
            bones['stinger'].rotation_euler.x = .25
        elif name == 'KneelFire':
            seconds = u * 8
            b = smooth(seconds / 2.15) * (1 - smooth((seconds - 6) / 2))
            aim('upper_arm.R', Vector((-.35, -.4 * b, -1)))
            aim('forearm.R', Vector((-.25, -.8 * b, -.8)))
            aim('upper_arm.L', Vector((.35, -.4 * b, -1)))
            aim('forearm.L', Vector((.25, -.8 * b, -.8)))
            
            recoil = .12 * max(0, 1 - ((seconds - 2.4) % .48) / .1) if 2.4 <= seconds < 5.8 else 0
            # Tail arches forward to lock stinger cannon horizontally down-range
            bones['tail_01'].rotation_euler.x = .25 * b
            bones['tail_02'].rotation_euler.x = .35 * b
            bones['tail_03'].rotation_euler.x = .40 * b
            bones['tail_04'].rotation_euler.x = .30 * b
            bones['stinger'].rotation_euler.x = .25 * b + recoil
            bones['stinger'].location.y = recoil * .8
        update()

    # Base profile for Scorpio's heavy predator frame
    report = build_motions(rig, obj, dict(
        run_frames=38, run_stance=.45, run_width=1.4, run_front=.75, run_back=2.0,
        run_compression=.40, run_bounce=.14, run_lean=.12, run_hip_twist=.04, run_chest_twist=.03,
        run_hip_roll=.01, run_shift=.035, run_toeoff=.48, run_recovery=2.4,
        run_arm_swing=.35, run_elbow=1.2, run_arm_out=.28,
        ankle_z=1.3, ankle_y=-1.4, ankle_x=3.0, kneel_drop=4.2, kneel_front=(2.2, -2.8, 1.3), kneel_back=(-1.5, 4.0, 2.5),
        crouch=1.1, landing=.9, tuck_width=.7, tuck_back=1.8, tuck_lift=3.5, jump=14, pivot=(0, -1.5, 7.8), fire_interval=.48,
        pose_adjust=adapt
    ))
    
    # 1. Sentinel idle
    def idle(u):
        neutral()
        bones['chest'].rotation_euler.x = .008 * math.sin(u * math.tau)
        bones['head'].rotation_euler.z = .035 * math.sin(u * math.tau)
        bones['head'].rotation_euler.x = .015 * math.cos(u * math.tau)
        # Serpentine tail sway
        bones['tail_01'].rotation_euler.z = .04 * math.sin(u * math.tau)
        bones['tail_02'].rotation_euler.z = .07 * math.sin(u * math.tau + .6)
        bones['tail_03'].rotation_euler.z = .09 * math.sin(u * math.tau + 1.2)
        bones['tail_04'].rotation_euler.z = .07 * math.sin(u * math.tau + 1.8)
        bones['stinger'].rotation_euler.z = .04 * math.sin(u * math.tau + 2.4)
        bones['stinger'].rotation_euler.x = .03 * math.cos(u * math.tau)
        # Gentle claw flex
        for sign, side in [(1, 'L'), (-1, 'R')]:
            bones['hand.' + side].rotation_euler.z = sign * .04 * (1 - math.cos(u * math.tau))
            
    # 2. Stinger Strike (Activation)
    def stinger_strike(u):
        neutral()
        if u < 0.35:
            # Coil back and charge
            t = smooth(u / 0.35)
            bones['chest'].rotation_euler.x = -.06 * t
            bones['head'].rotation_euler.x = .08 * t
            bones['tail_01'].rotation_euler.x = -.25 * t
            bones['tail_02'].rotation_euler.x = -.35 * t
            bones['tail_03'].rotation_euler.x = -.30 * t
            bones['tail_04'].rotation_euler.x = -.20 * t
            bones['stinger'].rotation_euler.x = -.25 * t
            # Claws spread wide in threat posture
            aim('upper_arm.L', Vector((.5, -.3, -1)))
            aim('upper_arm.R', Vector((-.5, -.3, -1)))
            aim('forearm.L', Vector((.7, -.6, -.4)))
            aim('forearm.R', Vector((-.7, -.6, -.4)))
            bones['hand.L'].rotation_euler.z = .25 * t
            bones['hand.R'].rotation_euler.z = -.25 * t
        elif u < 0.50:
            # Explosive forward thrust of the tail stinger
            t = smooth((u - 0.35) / 0.15)
            bones['chest'].rotation_euler.x = -.06 + .14 * t
            bones['head'].rotation_euler.x = .08 - .12 * t
            # Tail snaps forward like a scorpion strike
            bones['tail_01'].rotation_euler.x = -.25 + .65 * t
            bones['tail_02'].rotation_euler.x = -.35 + .85 * t
            bones['tail_03'].rotation_euler.x = -.30 + .90 * t
            bones['tail_04'].rotation_euler.x = -.20 + .75 * t
            bones['stinger'].rotation_euler.x = -.25 + .60 * t
            bones['stinger'].location.y = -1.2 * t
            # Claws snap shut together
            aim('upper_arm.L', Vector((.25, -.5, -1)))
            aim('upper_arm.R', Vector((-.25, -.5, -1)))
            aim('forearm.L', Vector((.3, -.8, -.5)))
            aim('forearm.R', Vector((-.3, -.8, -.5)))
            bones['hand.L'].rotation_euler.z = .25 - .40 * t
            bones['hand.R'].rotation_euler.z = -.25 + .40 * t
        elif u < 0.65:
            # Hold strike with vibration
            t = (u - 0.50) / 0.15
            vib = math.sin(t * math.tau * 6) * .02 * (1 - t)
            bones['chest'].rotation_euler.x = .08 + vib
            bones['tail_01'].rotation_euler.x = .40
            bones['tail_02'].rotation_euler.x = .50
            bones['tail_03'].rotation_euler.x = .60
            bones['tail_04'].rotation_euler.x = .55
            bones['stinger'].rotation_euler.x = .35 + vib
            bones['stinger'].location.y = -1.2 + vib
            bones['hand.L'].rotation_euler.z = -.15
            bones['hand.R'].rotation_euler.z = .15
        else:
            # Recover to neutral
            t = smooth((u - 0.65) / 0.35)
            bones['chest'].rotation_euler.x = .08 * (1 - t)
            bones['tail_01'].rotation_euler.x = .40 * (1 - t)
            bones['tail_02'].rotation_euler.x = .50 * (1 - t)
            bones['tail_03'].rotation_euler.x = .60 * (1 - t)
            bones['tail_04'].rotation_euler.x = .55 * (1 - t)
            bones['stinger'].rotation_euler.x = .35 * (1 - t)
            bones['stinger'].location.y = -1.2 * (1 - t)
            bones['hand.L'].rotation_euler.z = -.15 * (1 - t)
            bones['hand.R'].rotation_euler.z = .15 * (1 - t)

    # 3. Claw Strike (Attack)
    def claw_slash(u):
        neutral()
        if u < 0.30:
            # Right claw draws back, torso twists
            t = smooth(u / 0.30)
            bones['chest'].rotation_euler.z = .18 * t
            aim('upper_arm.R', Vector((-.6, .2 * t, -1)))
            aim('forearm.R', Vector((-.5, -.4, .3 * t)))
            bones['hand.R'].rotation_euler.z = -.35 * t
            bones['tail_02'].rotation_euler.z = -.15 * t
        elif u < 0.55:
            # Right claw heavy scissor swipe across front
            t = smooth((u - 0.30) / 0.25)
            bones['chest'].rotation_euler.z = .18 - .38 * t
            aim('upper_arm.R', Vector((-.2, -.6 * t, -1)))
            aim('forearm.R', Vector((.3 * t, -1.0, -.2)))
            bones['hand.R'].rotation_euler.z = -.35 + .65 * t
            bones['tail_02'].rotation_euler.z = -.15 + .30 * t
        elif u < 0.80:
            # Left claw cross follow-through
            t = smooth((u - 0.55) / 0.25)
            bones['chest'].rotation_euler.z = -.20 + .25 * t
            aim('upper_arm.L', Vector((.2, -.6 * t, -1)))
            aim('forearm.L', Vector((-.3 * t, -1.0, -.2)))
            bones['hand.L'].rotation_euler.z = .30 * t
            bones['hand.R'].rotation_euler.z = .30 * (1 - t)
        else:
            # Recover to rest
            t = smooth((u - 0.80) / 0.20)
            bones['chest'].rotation_euler.z = .05 * (1 - t)
            bones['hand.L'].rotation_euler.z = .30 * (1 - t)
            bones['tail_02'].rotation_euler.z = .15 * (1 - t)

    for name, frames, fn in [('Sentinel', 181, idle), ('StingerStrike', 181, stinger_strike), ('ClawSlash', 121, claw_slash)]:
        rig.animation_data.action = None
        previous = {}
        for frame in range(1, frames + 1):
            fn((frame - 1) / (frames - 1))
            update()
            for b in bones:
                if b.name in previous:
                    b.rotation_euler.make_compatible(previous[b.name])
                previous[b.name] = b.rotation_euler.copy()
                b.keyframe_insert('rotation_euler', frame=frame, group=b.name)
                b.keyframe_insert('location', frame=frame, group=b.name)
        a = rig.animation_data.action
        a.name = name
        a.use_fake_user = True
        rig.animation_data.action = None
        track = rig.animation_data.nla_tracks.new()
        track.name = name
        track.strips.new(name, 1, a)
        track.mute = True
        report.append({'name': name, 'frames': frames, 'duration': (frames - 1) / 30})

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

"""Super-robot motion for TITAN: rocket punch, chest beam, idle, run, kneel-fire, backflip."""
import bpy, math
from pathlib import Path
from mathutils import Vector, Matrix
from motion_library import build_motions
from classic_mecha import PoseKit, bake_clips
from titan_anatomy import ANKLE

ROOT = Path(__file__).resolve().parents[1]


def build_titan_motions(rig, obj):
    kit = PoseKit(rig, obj); bones = kit.bones; smooth = kit.smooth; curve = kit.curve; aim = kit.aim

    def arm_pose(side, upper, lower, hand, b, frame=None):
        """Blend each arm bone from its rest axis toward a world direction."""
        for name, target in [('upper_arm.' + side, upper), ('forearm.' + side, lower), ('hand.' + side, hand)]:
            t = Vector(target).normalized()
            if frame is not None: t = frame @ t
            kit.aim_stable(name, kit.blend_direction(kit.rest_axis(name), t, b))

    def brace(drop, spread=0, pelvis_pitch=0, pelvis_yaw=0):
        """Lower the root, tilt the pelvis and re-solve both legs on planted boots."""
        kit.lift_root(-drop); kit.world_rotation('pelvis', pelvis_pitch, 0, pelvis_yaw)
        for side, sign in [('L', 1), ('R', -1)]:
            kit.two_bone('thigh.' + side, 'shin.' + side, (sign * (ANKLE[0] + spread), ANKLE[1], ANKLE[2]), (0, -1, 0), 'foot.' + side)

    def torso(pitch=0, yaw=0, roll=0):
        kit.world_rotation('chest', pitch, roll, yaw)
        return Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(roll, 3, 'Y') @ Matrix.Rotation(pitch, 3, 'X')

    rear_leg = None
    kneel_front = (3.2, -2.9, ANKLE[2])

    def adapt(name, u):
        nonlocal rear_leg
        if name == 'KneelFire':
            seconds = u * 8; b = smooth(seconds / 2.15) * (1 - smooth((seconds - 6) / 2))
            recoil = .08 * max(0, 1 - ((seconds - 2.4) % .48) / .12) if 2.4 <= seconds < 5.8 else 0
            forward = Vector((-.04, -1, .02 + recoil * .9))
            # Knuckle blaster: the whole right arm lines up on the target.
            arm_pose('R', forward + Vector((-.22, 0, -.06)), forward, forward, b)
            # Left arm stays bent with the fist held forward at hip height;
            # TITAN's eleven-metre arm would reach the floor if it hung down.
            arm_pose('L', (.30, -.70, -.65), (.10, -.60, .80), (.10, -.70, .70), b)
            # TITAN rests on the rear thigh rather than the shin: seat the whole
            # rear leg, then re-plant the front boot so it does not lift with the root.
            if rear_leg is None:
                import numpy as np
                rear_leg = np.concatenate([kit.group_indices(n) for n in ('thigh.R', 'shin.R', 'foot.R')])
            if b > 0:
                low = kit.lowest_vertex(rear_leg)
                if low < 0:
                    kit.lift_root(-low)
                    target = Vector((ANKLE[0], ANKLE[1], ANKLE[2])).lerp(Vector(kneel_front), b)
                    kit.two_bone('thigh.L', 'shin.L', target, (0, -1, 0), 'foot.L')

    report = build_motions(rig, obj, dict(
        run_frames=37, run_stance=.47, run_width=2.7, run_front=.9, run_back=2.4,
        run_compression=.42, run_bounce=.15, run_lean=.12, run_hip_twist=.05, run_chest_twist=.04,
        run_hip_roll=.012, run_shift=.05, run_toeoff=.45, run_recovery=2.4,
        run_arm_swing=.42, run_elbow=1.15, run_arm_out=.55,
        ankle_z=ANKLE[2], ankle_y=ANKLE[1], ankle_x=ANKLE[0],
        kneel_drop=5.6, kneel_front=kneel_front, kneel_back=(-2.0, 2.8, 3.0),
        crouch=1.5, landing=1.3, tuck_width=.6, tuck_back=1.8, tuck_lift=3.8,
        jump=12, pivot=(0, 0, 9.0), fire_interval=.48, pose_adjust=adapt))

    def idle(u):
        kit.neutral(); t = u * math.tau
        bones['chest'].rotation_euler.x = .006 * math.sin(t); bones['head'].rotation_euler.z = .02 * math.sin(t)
        for side, sign in [('L', 1), ('R', -1)]:
            bones['upper_arm.' + side].rotation_euler.x = .012 * math.sin(t + sign * .4)
        kit.update()

    def rocket_punch(u):
        kit.neutral()
        # Fighting stance, right arm cocked back, driven forward, gauntlet
        # launched along its own axis, recovered, then relax.
        stance = curve(u, [(0, 0), (.12, 1), (.86, 1), (1, 0)])
        ready = curve(u, [(0, 0), (.10, 0), (.24, 1), (.30, 0), (1, 0)])
        thrust = curve(u, [(0, 0), (.22, 0), (.30, 1), (.70, 1), (.88, 0), (1, 0)])
        launch = curve(u, [(0, 0), (.31, 0), (.42, 1), (.56, 1), (.70, 0), (1, 0)])
        yaw = .30 * ready - .40 * thrust; pitch = .06 * thrust - .04 * ready
        brace(.45 * stance, .25 * stance, .02 * stance, .35 * yaw)
        frame = torso(pitch, yaw)
        # Left arm holds a guard throughout.
        arm_pose('L', (.55, -.55, -.62), (-.35, -.75, .55), (-.30, -.60, .74), stance, frame)
        # The fist is cocked back at chest height, then driven forward around
        # the outside of the elbow so no bone ever sweeps through vertical.
        def along(points, t):
            """Piecewise spherical path through waypoints, t in [0, 1]."""
            n = len(points) - 1; i = min(n - 1, int(t * n)); return kit.blend_direction(points[i], points[i + 1], t * n - i)
        guard = [Vector(v) for v in ((-.55, -.55, -.62), (.35, -.75, .55), (.30, -.60, .74))]
        wind = [Vector(v) for v in ((-.80, .05, -.55), (-.85, .20, .25), (-.85, .20, .25))]
        cocked = [Vector(v) for v in ((-.72, .50, -.48), (-.40, .90, -.15), (-.35, .92, -.15))]
        outside = [Vector(v) for v in ((-.97, -.05, -.25), (-.97, -.22, -.08), (-.97, -.22, -.08))]
        punch = [Vector(v) for v in ((-.40, -.92, .00), (-.12, -1, .04), (-.12, -1, .04))]
        targets = []
        for g, w, c, o, pn in zip(guard, wind, cocked, outside, punch):
            d = along([g, w, c], ready) if thrust <= 0 else along([along([g, w, c], ready), o, pn], thrust)
            targets.append(d)
        arm_pose('R', targets[0], targets[1], targets[2], stance, frame)
        bones['forearm.R'].location = (0, 9.5 * launch, 0)
        bones['head'].rotation_euler.z = -.5 * yaw; bones['head'].rotation_euler.x = -.06 * launch
        kit.update()

    def chest_beam(u):
        kit.neutral()
        spread = curve(u, [(0, 0), (.18, 1), (.72, 1), (.90, 0), (1, 0)])
        charge = curve(u, [(0, 0), (.18, 0), (.30, 1), (.72, 1), (.82, 0), (1, 0)])
        fire = 1 if .32 <= u <= .72 else 0
        shake = fire * .015 * math.sin(u * 240)
        brace(.55 * spread, .4 * spread, -.06 * spread, 0)
        frame = torso(-.16 * spread - .05 * charge + shake, 0, 0)
        for side, sign in [('L', 1), ('R', -1)]:
            arm_pose(side, (sign * .95, .25, -.05), (sign * .85, .35, .45), (sign * .6, .1, .8), spread, frame)
        bones['head'].rotation_euler.x = .12 * spread + .05 * charge
        kit.update()

    clips = [('Sentinel', 181, idle), ('RocketPunch', 106, rocket_punch), ('ChestBeam', 121, chest_beam)]
    bake_clips(kit, clips, report, ROOT / 'src/titan-motion-bounds.json')
    return report

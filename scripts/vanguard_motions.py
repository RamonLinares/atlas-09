"""Real-robot motion for VANGUARD: rifle burst, shield guard, boost jump, idle, run, kneel-fire, backflip."""
import bpy, math
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from motion_library import build_motions
from classic_mecha import PoseKit, bake_clips
from vanguard_anatomy import ANKLE

ROOT = Path(__file__).resolve().parents[1]


def build_vanguard_motions(rig, obj):
    kit = PoseKit(rig, obj); bones = kit.bones; smooth = kit.smooth; curve = kit.curve; aim = kit.aim
    rest_rifle = kit.rest_axis('rifle.R')

    def arm_pose(side, upper, lower, hand, b, frame=None):
        for name, target in [('upper_arm.' + side, upper), ('forearm.' + side, lower), ('hand.' + side, hand)]:
            if target is None: continue
            t = Vector(target).normalized()
            if frame is not None: t = frame @ t
            aim(name, kit.blend_direction(kit.rest_axis(name), t, b))

    def rifle_aim(direction, b):
        """Rotate the right hand so the rifle barrel follows `direction`."""
        hand = bones['hand.R']; rifle = bones['rifle.R'].bone
        target = rest_rifle.lerp(Vector(direction).normalized(), b)
        q = (rifle.tail_local - rifle.head_local).rotation_difference(target) @ hand.bone.matrix_local.to_quaternion()
        hand.matrix = Matrix.Translation(hand.head) @ q.to_matrix().to_4x4(); kit.update()

    def support_hand(b, along=1.9, offset=(0, 0, -.25)):
        """Bring the left wrist onto the rifle fore-grip with two-bone IK."""
        if b <= 0: return
        r = bones['rifle.R']; direction = (r.tail - r.head).normalized()
        target = r.head + direction * along + Vector(offset)
        rest_wrist = bones['forearm.L'].tail.copy()
        kit.two_bone('upper_arm.L', 'forearm.L', rest_wrist.lerp(target, b), (1, 0, -.3))
        aim('hand.L', kit.rest_axis('hand.L').lerp(direction, b))

    def skirt():
        # Plates swing with a thigh that lifts forward or outward, but hang
        # instead of following a thigh that folds backward under the hip.
        pelvis_frame = bones['pelvis'].matrix.to_3x3() @ bones['pelvis'].bone.matrix_local.to_3x3().inverted()
        for side in 'LR':
            thigh = bones['thigh.' + side]; b = bones['skirt.' + side]
            delta = (thigh.matrix.to_3x3() @ thigh.bone.matrix_local.to_3x3().inverted()).to_quaternion()
            # Measure the fold relative to the pelvis so whole-body rotation
            # (backflip, lean) does not read as a backward thigh swing.
            local_dir = pelvis_frame.inverted() @ (thigh.tail - thigh.head).normalized()
            backward = max(0.0, (kit.rest_axis('thigh.' + side).y - local_dir.y) / .5)
            follow = Quaternion((1, 0, 0, 0)).slerp(delta, max(0.0, 1.0 - min(1.0, backward)))
            b.matrix = Matrix.Translation(b.head) @ follow.to_matrix().to_4x4() @ b.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
        kit.update()

    def brace(drop, spread=0, pelvis_pitch=0, pelvis_yaw=0):
        kit.lift_root(-drop); kit.world_rotation('pelvis', pelvis_pitch, 0, pelvis_yaw)
        for side, sign in [('L', 1), ('R', -1)]:
            kit.two_bone('thigh.' + side, 'shin.' + side, (sign * (ANKLE[0] + spread), ANKLE[1], ANKLE[2]), (0, -1, 0), 'foot.' + side)

    def torso(pitch=0, yaw=0, roll=0):
        kit.world_rotation('chest', pitch, roll, yaw)
        return Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(roll, 3, 'Y') @ Matrix.Rotation(pitch, 3, 'X')

    def adapt(name, u):
        if name == 'KneelFire':
            seconds = u * 8; b = smooth(seconds / 2.15) * (1 - smooth((seconds - 6) / 2))
            recoil = .07 * max(0, 1 - ((seconds - 2.4) % .48) / .12) if 2.4 <= seconds < 5.8 else 0
            arm_pose('R', (-.18, -.85, -.45), (-.02, -1, .08), None, b)
            rifle_aim((0, -1, recoil), b)
            # Left arm bent with the hand forward at knee height; the shield hangs outboard.
            arm_pose('L', (.30, -.70, -.65), (.10, -.75, .65), (.10, -.80, .60), b)
        elif name == 'Run':
            # Rifle carried across the front; the shield arm swings less.
            arm_pose('R', (-.32, -.12, -.94), (-.08, -1, -.12), None, 1)
            rifle_aim((-.1, -.85, -.55), 1)
        elif name == 'Backflip':
            rifle_aim((bones['root'].matrix.to_3x3() @ Vector((-.3, -.5, -.8))), 1)
        skirt()

    report = build_motions(rig, obj, dict(
        run_frames=33, run_stance=.44, run_width=2.1, run_front=.85, run_back=2.4,
        run_compression=.4, run_bounce=.15, run_lean=.12, run_hip_twist=.06, run_chest_twist=.045,
        run_hip_roll=.012, run_shift=.05, run_toeoff=.48, run_recovery=2.4,
        run_arm_swing=.38, run_elbow=1.35, run_arm_out=.28,
        ankle_z=ANKLE[2], ankle_y=ANKLE[1], ankle_x=ANKLE[0],
        kneel_drop=6.1, kneel_front=(3.0, -3.4, ANKLE[2]), kneel_back=(-1.9, 3.9, 2.45),
        crouch=1.3, landing=1.1, tuck_width=.5, tuck_back=1.7, tuck_lift=3.6,
        jump=13, pivot=(0, 0, 8.9), fire_interval=.48, pose_adjust=adapt))

    def idle(u):
        kit.neutral(); t = u * math.tau
        bones['chest'].rotation_euler.x = .006 * math.sin(t); bones['head'].rotation_euler.y = .02 * math.sin(t)
        bones['upper_arm.R'].rotation_euler.x = .012 * math.sin(t + .5); bones['upper_arm.L'].rotation_euler.x = .010 * math.sin(t - .3)
        kit.update(); skirt()

    def rifle_burst(u):
        kit.neutral(); t = u * 3.2
        raise_ = curve(u, [(0, 0), (.20, 1), (.78, 1), (.95, 0), (1, 0)])
        recoil = .06 * max(0, 1 - ((t - 1.0) % .2) / .08) if 1.0 <= t < 2.2 else 0
        yaw = .28 * raise_
        brace(.28 * raise_, .2 * raise_, .01 * raise_, .3 * yaw)
        torso(.02 * raise_ + .03 * recoil, yaw)
        arm_pose('R', (-.22, -.92, -.22), (-.03, -1, .04), None, raise_)
        rifle_aim((0, -1, .02 + recoil * .8), raise_)
        # Shield arm comes up beside the rifle as a forward guard.
        arm_pose('L', (.55, -.70, -.45), (.12, -.92, -.35), (.1, -.95, -.3), raise_)
        bones['head'].rotation_euler.z = -yaw * .9; bones['head'].rotation_euler.x = -.03 * raise_
        kit.update(); skirt()

    def shield_guard(u):
        kit.neutral()
        guard = curve(u, [(0, 0), (.22, 1), (.75, 1), (.95, 0), (1, 0)])
        shake = curve(u, [(0, 0), (.46, 0), (.49, 1), (.64, 0), (1, 0)])
        yaw = -.38 * guard
        brace(.55 * guard + .15 * shake, .3 * guard, .03 * guard, .35 * yaw)
        r = bones['root']; r.matrix = Matrix.Translation((0, .35 * shake, 0)) @ r.matrix; kit.update()
        frame = torso(.06 * guard + .06 * shake, yaw)
        # Shield forearm crosses the chest; the rifle drops back out of the way.
        arm_pose('L', (.30, -.80, -.45), (-.85, -.35, .30), (-.9, -.25, .25), guard, frame)
        arm_pose('R', (-.55, .30, -.78), (-.30, -.55, -.78), None, guard, frame)
        rifle_aim(frame @ Vector((-.35, -.75, -.55)), guard)
        bones['head'].rotation_euler.z = -yaw * .6; bones['head'].rotation_euler.x = -.08 * guard
        kit.update(); skirt()

    def boost_jump(u):
        kit.neutral()
        # Feet stay planted while grounded; the legs trail only in the air.
        # Landing compression begins after touchdown so no phase overlaps.
        height = curve(u, [(0, 0), (.16, 0), (.38, 6.5), (.62, 6.5), (.84, 0), (1, 0)])
        dip = curve(u, [(0, 0), (.10, 1), (.16, 1), (.24, 0), (.84, 0), (.90, 1), (1, 0)])
        air = curve(u, [(0, 0), (.16, 0), (.32, 1), (.66, 1), (.84, 0), (1, 0)])
        bob = .18 * math.sin(u * math.tau * 2.5) * (1 if .38 <= u <= .62 else 0)
        kit.lift_root(height + bob - 1.0 * dip); kit.world_rotation('pelvis', .05 * air - .02 * dip, 0, 0)
        for side, sign in [('L', 1), ('R', -1)]:
            # Boots stay on their floor marks through the crouch (the root dip
            # only bends the knees), rise with the root and trail in the air.
            target = Vector((sign * (ANKLE[0] + .2 * dip), ANKLE[1] + 2.2 * air, ANKLE[2] + height + 1.3 * air))
            kit.two_bone('thigh.' + side, 'shin.' + side, target, (0, -1, 0))
            kit.aim('foot.' + side, kit.rest_axis('foot.' + side).lerp(Vector((0, -.4, -1)), air))
        frame = torso(.10 * air + .05 * dip, 0)
        arm_pose('L', (.92, -.25, -.30), (.75, -.45, -.45), (.7, -.5, -.5), air, frame)
        arm_pose('R', (-.80, -.25, -.50), (-.35, -.80, -.45), None, air, frame)
        rifle_aim(frame @ Vector((-.3, -.7, -.65)), air)
        bones['head'].rotation_euler.x = -.08 * air
        kit.update(); skirt()

    clips = [('Sentinel', 181, idle), ('RifleBurst', 97, rifle_burst), ('ShieldGuard', 91, shield_guard), ('BoostJump', 109, boost_jump)]
    bake_clips(kit, clips, report, ROOT / 'src/vanguard-motion-bounds.json')
    return report

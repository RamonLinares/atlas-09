"""Rest-space anatomy measured from the preserved VANGUARD mesh (metres, Z up, -Y forward).

The source arrives 0.52 m right of centre and 0.3 m behind it; the build
shifts it so the rig is symmetric. Left side is +X. The right hand holds the
beam rifle, the left forearm carries the shield.
"""
from mathutils import Vector

SHIFT = (-.52, -.3, 0)
SHOULDER = (3.3, .35, 14.9)
ELBOW = (5.0, .3, 13.05)
WRIST = (6.6, -.7, 11.35)
HAND_TIP = (7.35, -1.3, 10.1)
HIP = (1.9, 0, 8.7)
KNEE = (2.45, .3, 6.45)
ANKLE = (3.0, .5, 2.0)
TOE = (3.1, -1.9, .3)
RIFLE_REAR = (-6.7, -2.4, 12.0)
RIFLE_MUZZLE = (-10.45, -4.55, 6.7)
RIFLE_GRIP = (-7.6, -2.9, 10.8)
THRUSTER = (.9, 3.05, 12.9)
THRUSTER_DIR = (0, .55, -.83)

FOREARM_DIR = tuple((Vector(WRIST) - Vector(ELBOW)).normalized())
HAND_DIR = tuple((Vector(HAND_TIP) - Vector(WRIST)).normalized())
RIFLE_DIR = tuple((Vector(RIFLE_MUZZLE) - Vector(RIFLE_REAR)).normalized())


def mirror(p, sign):
    return (p[0] * sign, p[1], p[2])


def shield_inner_edge(z):
    # Inner long edge of the shield slab in the x-z plane.
    return 5.65 + (15.3 - z) * .2155


def segment_distance(p, a, b):
    p = Vector(p); a = Vector(a); b = Vector(b); ab = b - a
    t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (p - (a + ab * t)).length


BONES = [
    ('root', (0, 0, 0), (0, 0, 1), None, False),
    ('pelvis', (0, 0, 8.7), (0, 0, 10.6), 'root', True),
    ('chest', (0, 0, 10.6), (0, .2, 15.35), 'pelvis', True),
    ('head', (0, .2, 15.35), (0, .2, 17.7), 'chest', True),
]
for side, sign in [('L', 1), ('R', -1)]:
    BONES += [
        (f'upper_arm.{side}', mirror(SHOULDER, sign), mirror(ELBOW, sign), 'chest', True),
        (f'forearm.{side}', mirror(ELBOW, sign), mirror(WRIST, sign), f'upper_arm.{side}', True),
        (f'hand.{side}', mirror(WRIST, sign), mirror(HAND_TIP, sign), f'forearm.{side}', True),
        (f'thigh.{side}', mirror(HIP, sign), mirror(KNEE, sign), 'pelvis', True),
        (f'shin.{side}', mirror(KNEE, sign), mirror(ANKLE, sign), f'thigh.{side}', True),
        (f'foot.{side}', mirror(ANKLE, sign), mirror(TOE, sign), f'shin.{side}', True),
        (f'skirt.{side}', mirror(HIP, sign), (sign * 2.6, -.6, 7.8), 'pelvis', True),
    ]
BONES.append(('rifle.R', RIFLE_GRIP, RIFLE_MUZZLE, 'hand.R', True))


def section(p):
    x, y, z = p; a = abs(x); side = 'L' if x > 0 else 'R'
    # Nothing but the rifle sits outboard of the right hip below the wrist;
    # above it the receiver is separated from the forearm by its depth.
    # The muzzle is the lowest rifle point (6.7 m); the boots reach x = -5.4
    # below 3 m, so the rifle region is bounded in height as well as width.
    if z > 5.5 and ((x < -4.2 and z < 9.6) or (x < -5.3 and z < 12.4 and segment_distance(p, RIFLE_REAR, RIFLE_MUZZLE) < 1.5 and y < -1.55)):
        return 'rifle.R'
    if x > 4.8 and z > 7.9 and x > shield_inner_edge(z) - .05:
        return 'shield.L'
    if z > 15.35 and a < 1.75 and y < 1.4:
        return 'head'
    if (a > 2.55 and z > 11.0) or (a > 4.3 and z > 9.0):
        q = Vector((a, y, z))
        if (q - Vector(WRIST)).dot(Vector(HAND_DIR)) > 0:
            return 'hand.' + side
        if (q - Vector(ELBOW)).dot(Vector(FOREARM_DIR)) > .3:
            return 'forearm.' + side
        return 'upper_arm.' + side
    if z > 10.6:
        return 'chest'
    if (a < .95 and z > 7.4) or z > 10.4 or (y > 1.35 and z > 7.4 and a < 2.6):
        return 'pelvis'
    if z > 7.9 and a < 3.7 and (y < -.9 or a > 2.2):
        return 'skirt.' + side
    if z > 6.45:
        return 'thigh.' + side
    if z > 2.3:
        return 'shin.' + side
    return 'foot.' + side


def group_of(label):
    return 'forearm.L' if label == 'shield.L' else label

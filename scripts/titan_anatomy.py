"""Rest-space anatomy measured from the preserved TITAN mesh (metres, Z up, -Y forward).

Left side is +X. Values come from output/titan-06/source-*.png renders and the
per-height vertex bands recorded during inspection.
"""
from mathutils import Vector

SHOULDER = (5.0, .3, 14.6)
ELBOW = (7.4, .2, 12.5)
WRIST = (10.2, -.3, 9.2)
HAND_TIP = (11.2, -2.3, 6.7)
HIP = (2.0, 0, 8.9)
KNEE = (2.8, 0, 6.1)
ANKLE = (3.4, .3, 2.6)
TOE = (3.6, -2.4, .3)
PAULDRON_CENTER = (5.4, .5, 15.0)
PAULDRON_RADII = (2.1, 2.45, 2.45)
CHEST_LENS = (0, -3.05, 13.15)
EYE = (.42, -1.36, 16.62)

FOREARM_DIR = tuple((Vector(WRIST) - Vector(ELBOW)).normalized())
HAND_DIR = tuple((Vector(HAND_TIP) - Vector(WRIST)).normalized())


def mirror(p, sign):
    return (p[0] * sign, p[1], p[2])


BONES = [
    ('root', (0, 0, 0), (0, 0, 1), None, False),
    ('pelvis', (0, 0, 8.7), (0, 0, 10.25), 'root', True),
    ('chest', (0, 0, 10.25), (0, .05, 15.45), 'pelvis', True),
    ('head', (0, .05, 15.45), (0, .05, 18.2), 'chest', True),
]
for side, sign in [('L', 1), ('R', -1)]:
    BONES += [
        (f'upper_arm.{side}', mirror(SHOULDER, sign), mirror(ELBOW, sign), 'chest', True),
        (f'forearm.{side}', mirror(ELBOW, sign), mirror(WRIST, sign), f'upper_arm.{side}', True),
        (f'hand.{side}', mirror(WRIST, sign), mirror(HAND_TIP, sign), f'forearm.{side}', True),
        (f'thigh.{side}', mirror(HIP, sign), mirror(KNEE, sign), 'pelvis', True),
        (f'shin.{side}', mirror(KNEE, sign), mirror(ANKLE, sign), f'thigh.{side}', True),
        (f'foot.{side}', mirror(ANKLE, sign), mirror(TOE, sign), f'shin.{side}', True),
    ]


def section(p):
    x, y, z = p; a = abs(x); sign = 1 if x > 0 else -1; side = 'L' if x > 0 else 'R'
    if z > 15.45 and a < 3.1:
        return 'head'
    c = PAULDRON_CENTER; r = PAULDRON_RADII
    if ((a - c[0]) / r[0]) ** 2 + ((y - c[1]) / r[1]) ** 2 + ((z - c[2]) / r[2]) ** 2 < 1:
        return 'upper_arm.' + side
    if (a > 4.6 and z > 6.0) or (a > 3.5 and z > 9.0):
        q = Vector((a, y, z))
        if (q - Vector(WRIST)).dot(Vector(HAND_DIR)) > .05 or (y < -1.3 and z < 9.6 and a > 9.0):
            return 'hand.' + side
        if (q - Vector(ELBOW)).dot(Vector(FOREARM_DIR)) > .25:
            return 'forearm.' + side
        return 'upper_arm.' + side
    if z > 10.25:
        return 'chest'
    if (a < 1.3 and z > 7.1) or z > 9.55:
        return 'pelvis'
    # The knee plate hangs from the thigh in front of the shin's upper end.
    if z > 6.1 or (z > 4.95 and y < -1.25):
        return 'thigh.' + side
    if z > 2.75:
        return 'shin.' + side
    return 'foot.' + side

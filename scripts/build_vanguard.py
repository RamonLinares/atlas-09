"""Rebuild VANGUARD-07 from its preserved Tripo retopology, entirely locally.

VANGUARD is a classic real-robot military frame: beam rifle in the right
hand, shield on the left forearm, articulated skirt plates and backpack
thrusters. Anatomy lives in vanguard_anatomy.py; motion in vanguard_motions.py.
"""
import sys
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from classic_mecha import build, material
from vanguard_anatomy import *  # noqa: F401,F403
from vanguard_motions import build_vanguard_motions


def green_optics(px):
    diff = np.minimum(px[:, 1] - px[:, 0], px[:, 1] - px[:, 2])
    return np.clip((diff - .10) * 8, 0, 1)


def hardware(hw, rig, obj):
    joint = material('VANGUARD graphite actuators', (.03, .035, .04, 1), .72, .36)
    trim = material('VANGUARD signal yellow trim', (.7, .5, .08, 1), .6, .35)
    glow = material('VANGUARD sensor emission', (.05, .35, .12, 1), .1, .3, emission=(.35, 1, .5, 1), strength=4)
    beam = material('VANGUARD beam emitter emission', (.45, .15, .5, 1), .1, .3, emission=(.85, .45, 1, 1), strength=5)
    for side, sign in [('L', 1), ('R', -1)]:
        for part, radius in [('upper_arm', .58), ('forearm', .52), ('hand', .4), ('thigh', .6), ('shin', .52), ('foot', .42)]:
            hw.sphere(rig.data.bones[f'{part}.{side}'].head_local, radius, f'{part}.{side}', joint)
        # Backpack vernier: nozzle ring plus emissive throat, one per side.
        t = Vector(mirror(THRUSTER, sign)); d = Vector(THRUSTER_DIR).normalized()
        hw.cylinder(t - d * .25, .34, .5, d, 'chest', joint)
        hw.cylinder(t - d * .02, .38, .1, d, 'chest', trim)
        hw.cylinder(t + d * .02, .26, .04, d, 'chest', glow)
        hw.muzzle(rig, 'chest', t + d * .08, d, f'Muzzle_Thruster_{side}')
    hw.sphere((0, 0, 10.6), .62, 'chest', joint); hw.sphere((0, .2, 15.35), .45, 'head', joint)
    # Beam rifle emitter at the muzzle, parented to the rifle bone.
    m = Vector(RIFLE_MUZZLE); d = Vector(RIFLE_DIR)
    hw.cylinder(m - d * .2, .2, .5, d, 'rifle.R', joint)
    hw.cylinder(m + d * .04, .16, .03, d, 'rifle.R', beam)
    hw.muzzle(rig, 'rifle.R', m + d * .1, d, 'Muzzle_Rifle')
    return {'joint_housings': 14, 'verniers': 2, 'rifle_emitter': 1,
            'muzzles': ['Muzzle_Thruster_L', 'Muzzle_Thruster_R', 'Muzzle_Rifle']}


SPEC = dict(
    id='vanguard-07', prefix='Vanguard', blender_name='VANGUARD_07', height=18.0, shift=SHIFT,
    material_name='VANGUARD white armor, cobalt chest and signal red',
    emission_mask=green_optics, emission_color=(.35, 1.0, .5), emission_strength=3.5, coat=.22,
    section=section, group_of=group_of, bones=BONES, hardware=hardware, motions=build_vanguard_motions,
    readme='VANGUARD-07, 18m classic real-robot mecha. Right-hand beam rifle, left-forearm shield, thigh-following skirt plates, backpack verniers. Seven baked motions.',
    beauty_clip=('RifleBurst', 45), world=(.12, .13, .15, 1),
)

if __name__ == '__main__':
    build(SPEC)

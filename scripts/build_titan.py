"""Rebuild TITAN-06 from its preserved Tripo retopology, entirely locally.

TITAN is a classic super-robot silhouette: huge pauldrons, cylindrical
forearm gauntlets with detachable rocket fists and a chest-mounted beam lens.
Joint centres below were measured from the normalized source renders and
vertex bands in output/titan-06/.
"""
import sys, math
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from classic_mecha import build, material
from titan_anatomy import *  # noqa: F401,F403
from titan_motions import build_titan_motions


def yellow_optics(px):
    # Only the saturated, bright yellow of the visor optics; gold trim is darker.
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    return np.clip((np.minimum(r, g) - b - .42) * 6, 0, 1) * np.clip(((r + g) * .5 - .78) * 9, 0, 1)


def hardware(hw, rig, obj):
    joint = material('TITAN graphite actuators', (.02, .03, .04, 1), .78, .34)
    trim = material('TITAN aged gold trim', (.55, .38, .12, 1), .85, .28)
    glow = material('TITAN reactor emission', (.35, .28, .02, 1), .1, .3, emission=(1.0, .78, .22, 1), strength=5)
    beam = material('TITAN chest lens emission', (.35, .28, .02, 1), .1, .3, emission=(1.0, .72, .25, 1), strength=6)
    for side, sign in [('L', 1), ('R', -1)]:
        for part, radius in [('upper_arm', .85), ('forearm', .95), ('hand', .62), ('thigh', .78), ('shin', .8), ('foot', .55)]:
            hw.sphere(rig.data.bones[f'{part}.{side}'].head_local, radius, f'{part}.{side}', joint)
        # Rocket-fist thruster: a nozzle recessed in the elbow end of the
        # gauntlet, only visible once the forearm launches.
        elbow = Vector(mirror(ELBOW, sign)); df = Vector(mirror(FOREARM_DIR, sign))
        cap = elbow + df * .35
        hw.cylinder(cap + df * .35, .62, .9, df, f'forearm.{side}', joint)
        hw.cylinder(cap + df * .02, .72, .14, df, f'forearm.{side}', trim)
        hw.cylinder(cap - df * .05, .5, .04, df, f'forearm.{side}', glow)
        hw.muzzle(rig, f'forearm.{side}', cap - df * .12, -df, f'Muzzle_Rocket_{side}')
        # Knuckle blaster at the fist tip, firing along the hand axis.
        tip = Vector(mirror(HAND_TIP, sign)); dh = Vector(mirror(HAND_DIR, sign))
        hw.cylinder(tip - dh * .3, .22, .5, dh, f'hand.{side}', joint)
        hw.cylinder(tip - dh * .06, .16, .03, dh, f'hand.{side}', glow)
        hw.muzzle(rig, f'hand.{side}', tip + dh * .05, dh, f'Muzzle_{side}')
    hw.sphere((0, 0, 10.25), .95, 'chest', joint); hw.sphere((0, .05, 15.45), .62, 'head', joint)
    # Chest beam lens seated at the centre of the golden crest.
    hw.cylinder(Vector(CHEST_LENS) + Vector((0, .18, 0)), .42, .42, (0, -1, 0), 'chest', trim)
    hw.cylinder(Vector(CHEST_LENS) - Vector((0, .04, 0)), .3, .05, (0, -1, 0), 'chest', beam)
    hw.muzzle(rig, 'chest', Vector(CHEST_LENS) - Vector((0, .1, 0)), (0, -1, 0), 'Muzzle_Chest')
    # Visor optics: the generated texture paints the eyes in the same dull
    # gold as the trim, so small emissive lenses restore the classic glow.
    for sign in (1, -1):
        hw.cylinder(Vector(EYE) * Vector((sign, 1, 1)) + Vector((0, .06, 0)), .17, .16, (0, -1, 0), 'head', glow, vertices=14)
    return {'joint_housings': 14, 'rocket_nozzles': 2, 'knuckle_blasters': 2, 'chest_lens': 1, 'eye_lenses': 2,
            'muzzles': ['Muzzle_Rocket_L', 'Muzzle_Rocket_R', 'Muzzle_L', 'Muzzle_R', 'Muzzle_Chest']}


SPEC = dict(
    id='titan-06', prefix='Titan', blender_name='TITAN_06', height=19.0, shift=(0, 0, 0),
    material_name='TITAN royal blue lacquer, crimson chest and gold',
    emission_mask=None, coat=.3,
    section=section, bones=BONES, hardware=hardware, motions=build_titan_motions,
    readme='TITAN-06, 19m classic super-robot mecha. Pauldrons ride the upper arms, gauntlets carry launchable rocket fists, chest lens fires a beam. Six baked motions.',
    beauty_clip=('ChestBeam', 60), world=(.10, .11, .16, 1),
)

if __name__ == '__main__':
    build(SPEC)

"""Validate rigid binding, anatomy isolation, UVs and swept motion geometry for TITAN-06 or VANGUARD-07.

Usage: blender -b --python scripts/validate_classic.py -- <character-id>
"""
import bpy, json, math, sys, numpy as np
from pathlib import Path
from mathutils import Quaternion

ROOT = Path(__file__).resolve().parents[1]
CHAR = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'titan-06'
OUT = ROOT / 'output' / CHAR

CHARACTERS = {
    'titan-06': dict(
        blend='TITAN_06', clips=['Sentinel', 'RocketPunch', 'ChestBeam', 'Run', 'KneelFire', 'Backflip'],
        domains=lambda p: {
            'head': (abs(p[:, 0]) < 1.3) & (p[:, 2] > 16.0) & (p[:, 2] < 18.0),
            'torso': (abs(p[:, 0]) < 1.0) & (p[:, 2] > 11.0) & (p[:, 2] < 14.5) & (p[:, 1] < 0),
            'left_arm': (p[:, 0] > 8.0) & (p[:, 2] > 7.0) & (p[:, 2] < 11.0),
            'right_arm': (p[:, 0] < -8.0) & (p[:, 2] > 7.0) & (p[:, 2] < 11.0),
            'legs': (abs(p[:, 0]) < 4.2) & (abs(p[:, 0]) > 1.6) & (p[:, 2] > 3.0) & (p[:, 2] < 5.0),
        },
        isolation=[('head', ['head']), ('upper_arm.L', ['left_arm']), ('upper_arm.R', ['right_arm']), ('thigh.L', ['legs']), ('thigh.R', ['legs'])],
        translating={'RocketPunch': ['forearm.R']},
        attacks={'RocketPunch': ('hand.R', 'y', 8.0, 45, 16), 'ChestBeam': ('hand.L', 'x', 2.0, 49, 25)},
        rear_parts=['foot.L', 'foot.R', 'thigh.R', 'shin.R'],
    ),
    'vanguard-07': dict(
        blend='VANGUARD_07', clips=['Sentinel', 'RifleBurst', 'ShieldGuard', 'BoostJump', 'Run', 'KneelFire', 'Backflip'],
        domains=lambda p: {
            'head': (abs(p[:, 0]) < .9) & (p[:, 2] > 16.0) & (p[:, 2] < 17.5) & (p[:, 1] < 1.2),
            'torso': (abs(p[:, 0]) < 1.0) & (p[:, 2] > 11.5) & (p[:, 2] < 14.5) & (p[:, 1] < -1.0),
            'left_arm': (p[:, 0] > 7.0) & (p[:, 2] > 9.0) & (p[:, 2] < 15.0),
            'right_arm': (p[:, 0] < -7.5) & (p[:, 2] > 7.0) & (p[:, 2] < 10.0),
            'legs': (abs(p[:, 0]) < 4.1) & (abs(p[:, 0]) > 1.7) & (p[:, 2] > 3.0) & (p[:, 2] < 5.5),
        },
        isolation=[('head', ['head']), ('upper_arm.L', ['left_arm']), ('upper_arm.R', ['right_arm']), ('thigh.L', ['legs']), ('thigh.R', ['legs'])],
        translating={},
        attacks={'RifleBurst': ('rifle.R', 'y', 3.0, 45, 22), 'ShieldGuard': ('forearm.L', 'y', 1.5, 40, 22), 'BoostJump': ('foot.L', 'z', 4.0, 55, None)},
        rear_parts=['foot.L', 'foot.R', 'thigh.R', 'shin.R'],
    ),
}
spec = CHARACTERS[CHAR]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender' / f'{spec["blend"]}.blend'))
o = bpy.data.objects[f'{spec["blend"]}_Armor']; rig = bpy.data.objects[f'{spec["blend"]}_RIG']; scene = bpy.context.scene

report = {
    'rigid_vertices': all(len(v.groups) == 1 and abs(v.groups[0].weight - 1) < 1e-6 for v in o.data.vertices),
    'rigid_faces': all(len({o.data.vertices[i].groups[0].group for i in f.vertices}) == 1 for f in o.data.polygons),
}
assert report['rigid_vertices'] and report['rigid_faces'], 'Non-rigid vertices or faces detected'
report['uv_maps'] = []
for uv in o.data.uv_layers:
    bad = zero = 0
    for face in o.data.polygons:
        p = [uv.data[i].uv[:] for i in face.loop_indices]
        bad += any(c < -.0001 or c > 1.0001 or not np.isfinite(c) for v in p for c in v)
        zero += abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) < 2e-12
    report['uv_maps'].append({'name': uv.name, 'out_of_bounds': int(bad), 'zero_area': int(zero)})
    assert not bad and not zero, report['uv_maps']

def clear():
    for b in rig.pose.bones: b.rotation_euler = (0, 0, 0); b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0); b.scale = (1, 1, 1)
def sample(frame=1):
    scene.frame_set(int(frame), subframe=frame - int(frame)); bpy.context.view_layer.update()
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    p = np.empty(len(m.vertices) * 3, dtype=np.float32); m.vertices.foreach_get('co', p); ev.to_mesh_clear(); return p.reshape((-1, 3))

rig.animation_data.action = None; clear(); p = sample()
domains = {k: np.where(v)[0] for k, v in spec['domains'](p).items()}
assert all(len(v) > 15 for v in domains.values()), {k: len(v) for k, v in domains.items()}
report['domain_sizes'] = {k: int(len(v)) for k, v in domains.items()}
report['isolation'] = []
for name, moved in spec['isolation']:
    clear(); rig.pose.bones[name].rotation_quaternion = Quaternion((1, 0, 0), .8); q = sample()
    movement = {key: float(np.linalg.norm(q[ids] - p[ids], axis=1).max()) for key, ids in domains.items()}
    for key, value in movement.items():
        if key not in moved: assert value < 1e-5, f'Cross-contamination: {name} moved {key} by {value:.6f}m'
    assert any(movement[k] > .2 for k in moved), f'{name} failed to move target {moved}'
    report['isolation'].append({'bone': name, 'displacement_m': movement})

clear(); edges = np.array([e.vertices[:] for e in o.data.edges]); report['animations'] = []; failures = []
part_ids = {name: np.array([v.index for v in o.data.vertices if o.vertex_groups[v.groups[0].group].name == name]) for name in spec['rear_parts'] + [a[0] for a in spec['attacks'].values()]}
def check_clip(name):
        rig.animation_data.action = bpy.data.actions[name]; start, end = map(int, rig.animation_data.action.frame_range)
        if name == 'KneelFire':
            hold = sample(100)
            report['kneel_contact_m'] = {k: float(hold[part_ids[k], 2].min()) for k in spec['rear_parts']}
            assert abs(report['kneel_contact_m']['foot.L']) < .05, 'Front boot floats during firing'
            assert min(report['kneel_contact_m']['thigh.R'], report['kneel_contact_m']['shin.R']) < .10, 'Rear leg does not rest on the floor'
        first = sample(start)
        if name in spec['attacks']:
            part, axis, minimum, frame, planted_from = spec['attacks'][name]; ids = part_ids[part]; peak = sample(frame); ai = 'xyz'.index(axis)
            reach = float(first[ids, ai].min() - peak[ids, ai].min()) if axis == 'y' else float(peak[ids, ai].max() - first[ids, ai].max())
            report.setdefault('attack_reach_m', {})[name] = reach
            assert reach > minimum, (name, 'Signature motion does not reach', reach)
            if planted_from:
                # The stance may widen while settling; once set, both boots stay put through the action.
                stance = sample(planted_from)
                for foot in ['foot.L', 'foot.R']:
                    foot_motion = float(np.linalg.norm(peak[part_ids[foot]] - stance[part_ids[foot]], axis=1).max())
                    assert foot_motion < .01, (name, foot, 'Foot moved during planted action', foot_motion)
        last = sample(end); base = np.linalg.norm(first[edges[:, 0]] - first[edges[:, 1]], axis=1)
        low = 1e9; stretch = 0; motion = 0; maxclear = 0; joint_error = 0; translation_error = 0; angular_step = 0; previous = None; largest = None
        for frame in np.arange(start, end + .1, .5):
            q = sample(float(frame)); assert np.isfinite(q).all()
            rotations = {b.name: b.matrix.to_quaternion() for b in rig.pose.bones}
            if previous:
                for k, v in rotations.items():
                    step = 2 * math.acos(min(1, abs(previous[k].dot(v))))
                    if step > angular_step: angular_step = step; largest = (float(frame), k)
            previous = rotations
            for b in rig.pose.bones:
                if b.name != 'root' and b.name not in spec['translating'].get(name, []): translation_error = max(translation_error, b.location.length)
                if b.parent and (b.bone.head_local - b.parent.bone.tail_local).length < 1e-5 and b.name.startswith(('shin.', 'foot.', 'forearm.', 'hand.')) and b.name not in spec['translating'].get(name, []) and b.parent.name not in spec['translating'].get(name, []):
                    joint_error = max(joint_error, (b.head - b.parent.tail).length)
            low = min(low, float(q[:, 2].min())); maxclear = max(maxclear, float(q[:, 2].min()))
            stretch = max(stretch, float(abs(np.linalg.norm(q[edges[:, 0]] - q[edges[:, 1]], axis=1) - base).max()))
            motion = max(motion, float(np.linalg.norm(q - first, axis=1).max()))
        closure = float(np.linalg.norm(first - last, axis=1).max())
        assert closure < .0001, (name, 'Loop discontinuity', closure)
        assert joint_error < .0001 and translation_error < .0001, (name, joint_error, translation_error)
        assert angular_step < .35, (name, 'Pose discontinuity', angular_step, largest)
        assert low > -.005 and stretch < .0001 and motion > .01, (name, low, stretch, motion)
        report['animations'].append({'name': name, 'joint_gap_m': joint_error, 'non_root_translation_m': translation_error,
                                     'max_half_frame_angular_step_rad': angular_step, 'lowest_vertex_m': low, 'rigid_edge_error_m': stretch,
                                     'loop_error_m': closure, 'max_displacement_m': motion, 'max_ground_clearance_m': maxclear})
for name in spec['clips']:
    try: check_clip(name)
    except AssertionError as error: failures.append(str(error)); print('CLIP_FAILURE', name, error)
report['packed_textures'] = all(im.packed_file for im in bpy.data.images if im.type == 'IMAGE' and im.name != 'Render Result')
assert report['packed_textures']
assert not failures, failures
(OUT / 'blender-validation.json').write_text(json.dumps(report, indent=2))
print('BLENDER_VALIDATION_SUCCESS', json.dumps({k: v for k, v in report.items() if k != 'animations'}, indent=2))

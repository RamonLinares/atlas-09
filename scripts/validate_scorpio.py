"""Validate rigid binding, anatomy isolation, UVs, and swept motion geometry for SCORPIO-05."""
import bpy, json, math, numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/scorpio-05'

bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/SCORPIO-05.blend'))
o = bpy.data.objects['SCORPIO_05_Armor']
rig = bpy.data.objects['SCORPIO_05_RIG']
scene = bpy.context.scene

report = {
    'rigid_vertices': all(len(v.groups) == 1 and abs(v.groups[0].weight - 1) < 1e-6 for v in o.data.vertices),
    'rigid_faces': all(len({o.data.vertices[i].groups[0].group for i in f.vertices}) == 1 for f in o.data.polygons)
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
    for b in rig.pose.bones:
        b.rotation_euler = (0, 0, 0)
        b.location = (0, 0, 0)
        b.scale = (1, 1, 1)

def sample(frame=1):
    scene.frame_set(int(frame), subframe=frame - int(frame))
    bpy.context.view_layer.update()
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh()
    p = np.empty(len(m.vertices) * 3, dtype=np.float32)
    m.vertices.foreach_get('co', p)
    ev.to_mesh_clear()
    return p.reshape((-1, 3))

rig.animation_data.action = None
clear()
p = sample()

domains = {
    'head': np.where((abs(p[:, 0]) < .8) & (p[:, 2] > 10.8) & (p[:, 2] < 11.6) & (p[:, 1] < -1.7))[0],
    'legs': np.where((abs(p[:, 0]) < 2.5) & (p[:, 2] > 2.0) & (p[:, 2] < 6.0) & (p[:, 1] > -3.0) & (p[:, 1] < 0))[0],
    'torso': np.where((abs(p[:, 0]) < 1.0) & (p[:, 2] > 9.0) & (p[:, 2] < 9.8) & (p[:, 1] < 0))[0],
    'left_arm': np.where((p[:, 0] > 4.5) & (p[:, 2] > 5.0) & (p[:, 2] < 8.0))[0],
    'right_arm': np.where((p[:, 0] < -4.5) & (p[:, 2] > 5.0) & (p[:, 2] < 8.0))[0],
    'tail': np.where((abs(p[:, 0]) < 1.5) & (p[:, 1] > 4.0) & (p[:, 2] > 9.0) & (p[:, 2] < 15.0))[0],
    'stinger': np.where((abs(p[:, 0]) < 1.5) & (p[:, 1] < -3.0) & (p[:, 2] > 13.5))[0]
}
assert all(len(v) > 15 for v in domains.values()), {k: len(v) for k, v in domains.items()}

report['isolation'] = []
isolation_tests = [
    ('head', ['head']),
    ('upper_arm.L', ['left_arm']),
    ('upper_arm.R', ['right_arm']),
    ('thigh.L', ['legs']),
    ('thigh.R', ['legs']),
    ('tail_02', ['tail', 'stinger']),
    ('stinger', ['stinger'])
]

for name, moved in isolation_tests:
    clear()
    rig.pose.bones[name].rotation_euler.x = .8
    q = sample()
    movement = {key: float(np.linalg.norm(q[ids] - p[ids], axis=1).max()) for key, ids in domains.items()}
    for key, value in movement.items():
        if key not in moved:
            assert value < 1e-5, f'Cross-contamination: {name} moved {key} by {value:.6f}m'
    assert any(movement[k] > .2 for k in moved), f'{name} failed to move target {moved}'
    report['isolation'].append({'bone': name, 'displacement_m': movement})

clear()
edges = np.array([e.vertices[:] for e in o.data.edges])
report['animations'] = []
part_ids = {name: np.array([v.index for v in o.data.vertices if o.vertex_groups[v.groups[0].group].name == name]) for name in ['foot.L','foot.R','thigh.R','shin.R']}

for name in ['Sentinel', 'StingerStrike', 'ClawSlash', 'Run', 'KneelFire', 'Backflip']:
    rig.animation_data.action = bpy.data.actions[name]
    start, end = map(int, rig.animation_data.action.frame_range)
    if name == 'KneelFire':
        hold=sample(100)
        report['kneel_contact_m']={k:float(hold[ids,2].min()) for k,ids in part_ids.items()}
        assert abs(report['kneel_contact_m']['foot.L']) < .03, 'Front boot floats during firing'
        assert abs(report['kneel_contact_m']['thigh.R']) < .03, 'Rear knee shield does not contact the floor'
    first = sample(start)
    if name in ['StingerStrike','ClawSlash']:
        part='stinger' if name == 'StingerStrike' else 'hand.R'
        ids=np.array([v.index for v in o.data.vertices if o.vertex_groups[v.groups[0].group].name == part])
        chest_rest=rig.pose.bones['chest'].matrix.to_quaternion()
        impact=sample(65 if name == 'StingerStrike' else 32)
        chest_turn=2*math.acos(min(1,abs(chest_rest.dot(rig.pose.bones['chest'].matrix.to_quaternion()))))
        report.setdefault('attack_torso_rotation_deg',{})[name]=math.degrees(chest_turn)
        assert chest_turn>.09, (name, 'Torso does not drive the strike')
        for foot in ['foot.L','foot.R']:
            foot_motion=float(np.linalg.norm(impact[part_ids[foot]]-first[part_ids[foot]],axis=1).max())
            assert foot_motion<.01, (name, foot, 'Foot moved during planted strike', foot_motion)
        reach=float(first[ids,1].min()-impact[ids,1].min())
        report.setdefault('attack_forward_reach_m',{})[name]=reach
        assert reach>2, (name, 'Strike does not reach forward', reach)
    last = sample(end)
    base = np.linalg.norm(first[edges[:, 0]] - first[edges[:, 1]], axis=1)
    low = 1e9
    stretch = 0
    motion = 0
    maxclear = 0
    joint_error = 0
    translation_error = 0
    angular_step = 0
    previous = None
    largest_step = None
    for frame in np.arange(start, end + .1, .5):
        q = sample(float(frame))
        assert np.isfinite(q).all()
        rotations = {b.name:b.matrix.to_quaternion() for b in rig.pose.bones}
        if previous:
            for k,v in rotations.items():
                step=2*math.acos(min(1,abs(previous[k].dot(v))))
                if step>angular_step: angular_step=step;largest_step=(float(frame),k)
        previous = rotations
        for b in rig.pose.bones:
            if b.name != 'root': translation_error = max(translation_error,b.location.length)
            if b.parent and (b.bone.head_local-b.parent.bone.tail_local).length < 1e-5 and (b.name.startswith(('tail_', 'shin.', 'foot.', 'forearm.', 'hand.')) or b.name == 'stinger'):
                joint_error = max(joint_error,(b.head-b.parent.tail).length)

        low = min(low, float(q[:, 2].min()))
        maxclear = max(maxclear, float(q[:, 2].min()))
        stretch = max(stretch, float(abs(np.linalg.norm(q[edges[:, 0]] - q[edges[:, 1]], axis=1) - base).max()))
        motion = max(motion, float(np.linalg.norm(q - first, axis=1).max()))
    closure = float(np.linalg.norm(first - last, axis=1).max())
    assert closure < .0001, (name, 'Loop discontinuity', closure)
    assert joint_error < .0001 and translation_error < .0001, (name, joint_error, translation_error)
    assert angular_step < .35, (name, 'Pose discontinuity', angular_step,largest_step)
    assert low > -.005 and stretch < .0001 and motion > .01, (name, low, stretch, motion)
    report['animations'].append({
        'name': name,
        'joint_gap_m': joint_error,
        'non_root_translation_m': translation_error,
        'max_half_frame_angular_step_rad': angular_step,
        'lowest_vertex_m': low,
        'rigid_edge_error_m': stretch,
        'loop_error_m': closure,
        'max_displacement_m': motion,
        'max_ground_clearance_m': maxclear
    })

report['packed_textures'] = all(im.packed_file for im in bpy.data.images if im.type == 'IMAGE' and im.name != 'Render Result')
assert report['packed_textures']

(OUT / 'blender-validation.json').write_text(json.dumps(report, indent=2))
print('BLENDER_VALIDATION_SUCCESS', json.dumps({k: v for k, v in report.items() if k != 'animations'}, indent=2))

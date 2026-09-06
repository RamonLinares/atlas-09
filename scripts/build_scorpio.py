"""Rebuild SCORPIO-05 from its preserved Tripo retopology, entirely locally."""
import bpy, bmesh, math, json, sys, runpy
import numpy as np
from pathlib import Path
from collections import defaultdict
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/scorpio-05'
TEX = ROOT / 'public/textures/scorpio-05'
OUT.mkdir(parents=True, exist_ok=True)
TEX.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'scripts'))
from scorpio_anatomy import section, TAIL_POINTS, TAIL_NAMES, BARREL_AXIS, STINGER_END, MUZZLE_CENTER

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

source = next((ROOT / 'assets/scorpio-05/retopo').glob('*model_url.glb'))
bpy.ops.import_scene.gltf(filepath=str(source))
obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
obj.name = 'SCORPIO_05_Armor'

coords = [Matrix.Rotation(-math.pi / 2, 4, 'Z') @ (obj.matrix_world @ v.co) for v in obj.data.vertices]
lo = min(p.z for p in coords)
scale = 17.0 / (max(p.z for p in coords) - lo)
for v, p in zip(obj.data.vertices, coords):
    v.co = (p - Vector((0, 0, lo))) * scale
obj.matrix_world = Matrix.Identity(4)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

mesh = obj.data
intake_triangles = sum(len(f.vertices) - 2 for f in mesh.polygons)
bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.00006)
zero_faces = [f for f in bm.faces if f.calc_area() < 1e-7]
bmesh.ops.delete(bm, geom=zero_faces, context='FACES_ONLY')
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(mesh)
bm.free()
mesh.update()

mesh.uv_layers.active.name = 'Scorpio_Surface'
mat = mesh.materials[0]
mat.name = 'SCORPIO blackened chitin, desert bronze — venom emission'
mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
base = None
textures = []

for n in list(mat.node_tree.nodes):
    if n.type != 'TEX_IMAGE' or not n.image:
        continue
    im = n.image
    semantic = 'BaseColor' if any(l.to_socket == bsdf.inputs['Base Color'] for l in n.outputs['Color'].links) else ('Normal' if 'normal' in im.name.lower() else 'ORM')
    if semantic == 'BaseColor':
        base = im
    ext = 'jpg' if im.packed_file and bytes(im.packed_file.data[:2]) == b'\xff\xd8' else 'png'
    im.filepath_raw = str(TEX / f'Scorpio_{semantic}.{ext}')
    im.file_format = 'JPEG' if ext == 'jpg' else 'PNG'
    im.save()
    im.pack()
    textures.append({'semantic': semantic, 'size': list(im.size), 'file': im.filepath_raw})
    uv = mat.node_tree.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'Scorpio_Surface'
    mat.node_tree.links.new(uv.outputs['UV'], n.inputs['Vector'])

bsdf.inputs['Coat Weight'].default_value = .28
bsdf.inputs['Coat Roughness'].default_value = .22

if base:
    w, h = base.size
    px = np.empty(w * h * 4, dtype=np.float32)
    base.pixels.foreach_get(px)
    px = px.reshape((-1, 4))
    # Extract green emission from optical sensors, vents, and stinger coils
    diff = np.minimum(px[:, 1] - px[:, 0], px[:, 1] - px[:, 2])
    mask = np.clip((diff - 0.04) * 9, 0, 1)
    out = np.zeros_like(px)
    out[:, :3] = mask[:, None] * np.array([0.32, 1.0, 0.45])
    out[:, 3] = 1.0
    em = bpy.data.images.new('Scorpio_Emission', width=w, height=h)
    em.pixels.foreach_set(out.ravel())
    em.filepath_raw = str(TEX / 'Scorpio_Emission.png')
    em.file_format = 'PNG'
    em.save()
    em.pack()
    en = mat.node_tree.nodes.new('ShaderNodeTexImage')
    en.image = em
    uv = mat.node_tree.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'Scorpio_Surface'
    mat.node_tree.links.new(uv.outputs['UV'], en.inputs['Vector'])
    mat.node_tree.links.new(en.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 3.5
    textures.append({'semantic': 'Emission', 'size': [w, h], 'file': em.filepath_raw})

labels = {f.index: section(f.center) for f in mesh.polygons}
parts = defaultdict(list)
for fi, name in labels.items():
    parts[name].append(fi)

old = mesh
verts = []
faces = []
uvs = []
mats = []
weights = defaultdict(list)

for name, indices in parts.items():
    remap = {}
    for fi in indices:
        f = old.polygons[fi]
        face = []
        mats.append(0)
        for li, vi in zip(f.loop_indices, f.vertices):
            if vi not in remap:
                remap[vi] = len(verts)
                verts.append(tuple(old.vertices[vi].co))
                weights[name].append(remap[vi])
            face.append(remap[vi])
            uvs.append(tuple(old.uv_layers['Scorpio_Surface'].data[li].uv))
        faces.append(face)

mesh = bpy.data.meshes.new('SCORPIO_RigidArmor')
mesh.from_pydata(verts, [], faces)
mesh.update()
obj.data = mesh
mesh.materials.append(mat)
uv = mesh.uv_layers.new(name='Scorpio_Surface')
for i, co in enumerate(uvs):
    uv.data[i].uv = co
for f, mi in zip(mesh.polygons, mats):
    f.material_index = mi
    f.use_smooth = True
for name, indices in weights.items():
    obj.vertex_groups.new(name=name).add(indices, 1, 'REPLACE')

# Armature & Rig
bpy.ops.object.armature_add(enter_editmode=True)
rig = bpy.context.object
rig.name = 'SCORPIO_05_RIG'
rig.show_in_front = True
eb = rig.data.edit_bones
eb.remove(eb[0])

def bone(name, head, tail, parent=None, deform=True):
    b = eb.new(name)
    b.head = head
    b.tail = tail
    b.use_deform = deform
    if parent:
        b.parent = eb[parent]
    return b

bone('root',(0,0,0),(0,0,1),deform=False)
bone('pelvis',(0,-1.45,6.80),(0,-1.65,8.55),'root')
bone('chest',(0,-1.65,8.55),(0,-2.10,10.30),'pelvis')
bone('head',(0,-2.10,10.30),(0,-2.05,11.85),'chest')
for sign,side in [(1,'L'),(-1,'R')]:
    bone('shoulder.'+side,(sign*1.80,-1.80,10.10),(sign*2.60,-1.60,9.70),'chest')
    bone('upper_arm.'+side,(sign*2.60,-1.60,9.70),(sign*3.65,-1.40,8.30),'shoulder.'+side)
    bone('forearm.'+side,(sign*3.65,-1.40,8.30),(sign*4.50,-1.95,7.65),'upper_arm.'+side)
    bone('hand.'+side,(sign*4.50,-1.95,7.65),(sign*7.35,-2.50,4.10),'forearm.'+side)
    bone('thigh.'+side,(sign*1.40,-1.45,6.80),(sign*2.50,-1.30,3.40),'pelvis')
    bone('shin.'+side,(sign*2.50,-1.30,3.40),(sign*3.10,-1.20,1.20),'thigh.'+side)
    bone('foot.'+side,(sign*3.10,-1.20,1.20),(sign*3.25,-2.80,.35),'shin.'+side)
for i,name in enumerate(TAIL_NAMES):
    bone(name,TAIL_POINTS[i],TAIL_POINTS[i+1],TAIL_NAMES[i-1] if i else 'pelvis')
bone('stinger',TAIL_POINTS[-1],STINGER_END,TAIL_NAMES[-1])

bpy.ops.object.mode_set(mode='OBJECT')
obj.parent = rig
mod = obj.modifiers.new('Rigid mechanical skin', 'ARMATURE')
mod.object = rig
for b in rig.pose.bones:
    b.rotation_mode = 'XYZ'

# Actuator joint housings and hardware
def material(name, color, metallic, roughness):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = color
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    return m

joint = material('SCORPIO graphite actuators', (.025, .038, .042, 1), .75, .32)
trim = material('SCORPIO desert bronze trim', (.45, .30, .12, 1), .82, .28)
glow = material('SCORPIO venom emission', (.05, .4, .1, 1), .1, .25)
g = glow.node_tree.nodes.get('Principled BSDF')
g.inputs['Emission Color'].default_value = (.32, 1.0, .45, 1)
g.inputs['Emission Strength'].default_value = 4.0

pieces = []
def bind(o, name, mat):
    o.data.materials.append(mat)
    o.vertex_groups.new(name=name).add(list(range(len(o.data.vertices))), 1, 'REPLACE')
    if o.data.uv_layers:
        o.data.uv_layers.active.name = 'Scorpio_Surface'
    else:
        o.data.uv_layers.new(name = 'Scorpio_Surface')
    for f in o.data.polygons:
        f.use_smooth = True
    pieces.append(o)

def sphere(center, radius, name):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=radius, location=center)
    bind(bpy.context.object, name, joint)

def cylinder(center, radius, length, direction, name, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius, depth=length, location=center)
    o = bpy.context.object
    o.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    bind(o, name, mat)

for side in ['L', 'R']:
    for name, radius in [('upper_arm', .42), ('forearm', .34), ('hand', .28), ('thigh', .48), ('shin', .38), ('foot', .26)]:
        sphere(rig.data.bones[name + '.' + side].head_local, radius, name + '.' + side)
sphere((0,-1.65,8.55),.40,'chest')
sphere((0,-2.10,10.30),.32,'head')

# Small internal couplings cover the rotating seams without replacing the
# source armor or extending a joint with bone translation.
for i,name in enumerate(TAIL_NAMES+['stinger']):
    sphere(TAIL_POINTS[i],.34 if i<len(TAIL_NAMES) else .38,name)

# The nozzle sits inside the source stinger's open prongs, along its barrel.
direction=BARREL_AXIS
center=MUZZLE_CENTER
cylinder(center,.15,.45,direction,'stinger',joint)
cylinder(center+direction*.225,.18,.08,direction,'stinger',trim)
cylinder(center+direction*.275,.13,.025,direction,'stinger',glow)

bpy.ops.object.empty_add(type='ARROWS', location=center + direction * .30)
muzzle = bpy.context.object
muzzle.name = 'Muzzle_Stinger'
muzzle.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()
world = muzzle.matrix_world.copy()
muzzle.parent = rig
muzzle.parent_type = 'BONE'
muzzle.parent_bone = 'stinger'
muzzle.matrix_world = world

bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
for o in pieces:
    o.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.join()

bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(obj.data)
bm.free()
obj.data.update()

mesh = obj.data
mesh.uv_layers.new(name='Scorpio_Lightmap')
mesh.uv_layers.active_index = 1
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.008, area_weight=.3, scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')
mesh.uv_layers.active_index = 0
mesh.uv_layers['Scorpio_Surface'].active_render = True

scene = bpy.context.scene
scene.render.fps = 30
rig.animation_data_create()

def neutral():
    for pb in rig.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)

from scorpio_motions import build_scorpio_motions
motion_report = build_scorpio_motions(rig, obj)
(OUT / 'bake-report.json').write_text(json.dumps(motion_report, indent=2))

rig['README'] = 'SCORPIO-05, 17m scorpion predator mecha. Articulated hydraulic claws and anatomically articulated plasma stinger tail. Six baked motions.'
neutral()
scene.frame_set(1)
scene.frame_start = 1
scene.frame_end = 181

bm = bmesh.new()
bm.from_mesh(mesh)
boundary = sum(e.is_boundary for e in bm.edges)
bm.free()

report = {
    'source': str(source.relative_to(ROOT)),
    'height_m': 17.0,
    'source_triangles': intake_triangles,
    'vertices': len(mesh.vertices),
    'triangles': sum(len(f.vertices) - 2 for f in mesh.polygons),
    'bones': len(rig.data.bones),
    'materials': [m.name for m in mesh.materials],
    'boundary_edges': boundary,
    'textures': textures,
    'animations': [{'name': a.name, 'frames': list(a.frame_range)} for a in bpy.data.actions]
}
(OUT / 'asset-report.json').write_text(json.dumps(report, indent=2))

# GLB export
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
rig.select_set(True)
muzzle.select_set(True)
bpy.context.view_layer.objects.active = rig
obj.parent = None
bpy.ops.export_scene.gltf(
    filepath=str(ROOT / 'public/models/scorpio-05.glb'),
    export_format='GLB',
    use_selection=True,
    export_animations=True,
    export_animation_mode='ACTIONS',
    export_anim_slide_to_zero=True,
    export_nla_strips=True,
    export_skins=True,
    export_yup=True,
    export_texcoords=True,
    export_normals=True,
    export_tangents=True,
    export_image_format='AUTO'
)
runpy.run_path(str(ROOT / 'scripts/fix_export_tangents.py'), init_globals={'ASSET_PATH': ROOT / 'public/models/scorpio-05.glb', 'REPORT_PATH': OUT / 'tangent-repairs.json'}, run_name='__main__')
obj.parent = rig

# Studio setup and Cycles beauty render
stage = bpy.data.collections.new('STUDIO — excluded from GLB')
scene.collection.children.link(stage)
def to_stage(o):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    stage.objects.link(o)

def aim(o):
    o.rotation_euler = (Vector((0, -1.5, 9.0)) - o.location).to_track_quat('-Z', 'Y').to_euler()

scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.12, .15, .16, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .5

bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 0, -.045))
floor = bpy.context.object
floor.name = 'Studio floor'
to_stage(floor)
floor.data.materials.append(material('Studio graphite', (.05, .065, .075, 1), .15, .8))

for pos, power, color in [((8, -14, 22), 3000, (.85, .95, .88)), ((-10, -8, 14), 2200, (.75, 1.0, .85)), ((8, 10, 20), 3800, (.7, .9, 1))]:
    bpy.ops.object.light_add(type='AREA', location=pos)
    l = bpy.context.object
    l.data.energy = power
    l.data.color = color
    l.data.shape = 'DISK'
    l.data.size = 8
    aim(l)
    to_stage(l)

bpy.ops.object.camera_add(location=(16, -32, 14))
cam = bpy.context.object
aim(cam)
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 26
cam.data.clip_end = 2000
scene.camera = cam
to_stage(cam)

scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'

bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
rig.animation_data.action = bpy.data.actions['StingerStrike']
scene.frame_set(1)

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'blender/SCORPIO-05.blend'))
scene.render.filepath = str(OUT / 'scorpio-05-beauty.png')
if '--skip-render' not in sys.argv:
    bpy.ops.render.render(write_still=True)
print('ASSET_REPORT', json.dumps(report))

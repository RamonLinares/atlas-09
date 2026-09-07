"""Rebuild RONIN-04 from its preserved Tripo retopology, entirely locally."""
import bpy, bmesh, math, json, sys, runpy
import numpy as np
from pathlib import Path
from collections import defaultdict
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/ronin-04';TEX=ROOT/'public/textures/ronin-04'
OUT.mkdir(parents=True,exist_ok=True);TEX.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'scripts'))
from motion_library import build_motions
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
source=next((ROOT/'assets/ronin-04/retopo').glob('*model_url.glb'))
bpy.ops.import_scene.gltf(filepath=str(source))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');obj.name='RONIN_04_Armor'
coords=[Matrix.Rotation(-math.pi/2,4,'Z')@(obj.matrix_world@v.co) for v in obj.data.vertices]
lo=min(p.z for p in coords);scale=16/(max(p.z for p in coords)-lo)
for v,p in zip(obj.data.vertices,coords):v.co=(p-Vector((0,0,lo)))*scale-Vector((.8,1.5,0))
obj.matrix_world=Matrix.Identity(4)
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
mesh=obj.data;intake_triangles=sum(len(f.vertices)-2 for f in mesh.polygons)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00006)
# Remove degenerate source faces before preserving the UVs.
zero_faces=[f for f in bm.faces if f.calc_area()<1e-7]
bmesh.ops.delete(bm,geom=zero_faces,context='FACES_ONLY')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
mesh.uv_layers.active.name='Ronin_Surface'
mat=mesh.materials[0];mat.name='RONIN crimson lacquer, aged gold and steel';mat.use_nodes=True
bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');base=None
textures=[]
for n in list(mat.node_tree.nodes):
 if n.type!='TEX_IMAGE' or not n.image:continue
 im=n.image
 semantic='BaseColor' if any(l.to_socket==bsdf.inputs['Base Color'] for l in n.outputs['Color'].links) else ('Normal' if 'normal' in im.name.lower() else 'ORM')
 if semantic=='BaseColor':base=im
 ext='jpg' if im.packed_file and bytes(im.packed_file.data[:2])==b'\xff\xd8' else 'png'
 im.filepath_raw=str(TEX/f'Ronin_{semantic}.{ext}');im.file_format='JPEG' if ext=='jpg' else 'PNG';im.save();im.pack()
 textures.append({'semantic':semantic,'size':list(im.size),'file':im.filepath_raw})
 uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='Ronin_Surface';mat.node_tree.links.new(uv.outputs['UV'],n.inputs['Vector'])
bsdf.inputs['Coat Weight'].default_value=.28;bsdf.inputs['Coat Roughness'].default_value=.22
# Boundaries measured in normalized front/side/back source views.
def section(p):
 x,y,z=p;a=abs(x);side='L' if x>0 else 'R'
 if x< -3.25-.32*max(0,6.8-z) and z<6.85:return 'sword.R'
 if z>13.05 and a<1.5:return 'head'
 # The sword pommel rises behind the right wrist; it belongs to the grip.
 if x< -2.8 and y>.9 and 7.5<z<8.5:return 'hand.R'
 # Follow the diagonal lower edge of the complete shoulder plate.
 if z>10.9 and a>max(1.65,1.7+.57*(13.7-z)):return 'shoulder.'+side
 arm_inner=min(2.95,1.8+.30*max(0,12-z))
 if a>arm_inner and z>6.1:
  if z>10.15:return 'upper_arm.'+side
  if z>8.0:return 'forearm.'+side
  return 'hand.'+side
 if z>10.0:return 'chest'
 if 7.1<z<9.4 and a>.78 and (y<-.85 or y>.85 or a>1.8):return 'skirt.'+side
 if z>8.65 or (z>7.4 and a<.78):return 'pelvis'
 if z>5.15:return 'thigh.'+side
 if z>1.25:return 'shin.'+side
 return 'foot.'+side
labels={f.index:section(f.center) for f in mesh.polygons}
repairs=[]
parts=defaultdict(list)
for fi,name in labels.items():parts[name].append(fi)
(OUT/'binding-repairs.json').write_text(json.dumps(repairs,indent=2))
old=mesh;verts=[];faces=[];uvs=[];mats=[];weights=defaultdict(list)
for name,indices in parts.items():
 remap={}
 for fi in indices:
  f=old.polygons[fi];face=[];mats.append(0)
  for li,vi in zip(f.loop_indices,f.vertices):
   if vi not in remap:remap[vi]=len(verts);verts.append(tuple(old.vertices[vi].co));weights[name].append(remap[vi])
   face.append(remap[vi]);uvs.append(tuple(old.uv_layers['Ronin_Surface'].data[li].uv))
  faces.append(face)
mesh=bpy.data.meshes.new('RONIN_RigidArmor');mesh.from_pydata(verts,[],faces);mesh.update();obj.data=mesh
mesh.materials.append(mat)
uv=mesh.uv_layers.new(name='Ronin_Surface')
for i,co in enumerate(uvs):uv.data[i].uv=co
for f,mi in zip(mesh.polygons,mats):f.material_index=mi;f.use_smooth=True
for name,indices in weights.items():obj.vertex_groups.new(name=name).add(indices,1,'REPLACE')

# Rest-space joints measured from front and side inspection renders (meters).
bpy.ops.object.armature_add(enter_editmode=True);rig=bpy.context.object;rig.name='RONIN_04_RIG';rig.show_in_front=True
eb=rig.data.edit_bones;eb.remove(eb[0])
def bone(name,head,tail,parent=None,deform=True):
 b=eb.new(name);b.head=head;b.tail=tail;b.use_deform=deform
 if parent:b.parent=eb[parent]
bone('root',(0,0,0),(0,0,1),deform=False)
bone('pelvis',(0,0,8.85),(0,0,10.0),'root')
bone('chest',(0,0,10.0),(0,.15,13.05),'pelvis')
bone('head',(0,.15,13.05),(0,.15,14.5),'chest')
for sign,side in [(1,'L'),(-1,'R')]:
 bone('shoulder.'+side,(sign*1.6,.15,12.6),(sign*2.3,.15,12.15),'chest')
 bone('upper_arm.'+side,(sign*2.3,.15,12.15),(sign*3.05,-.05,10.15),'shoulder.'+side)
 bone('forearm.'+side,(sign*3.05,-.05,10.15),(sign*3.55,-.25,8.0),'upper_arm.'+side)
 bone('hand.'+side,(sign*3.55,-.25,8.0),(sign*3.65,-.45,7.1),'forearm.'+side)
 bone('thigh.'+side,(sign*1.05,0,8.85),(sign*1.75,.05,5.15),'pelvis')
 bone('shin.'+side,(sign*1.75,.05,5.15),(sign*2.45,.15,1.25),'thigh.'+side)
 bone('foot.'+side,(sign*2.45,.15,1.25),(sign*2.55,-1.1,.4),'shin.'+side)
 bone('skirt.'+side,(sign*1.05,0,8.85),(sign*1.5,0,7.2),'pelvis')
bone('sword.R',(-3.65,-.45,7.1),(-5.8,-4.4,.85),'hand.R')
bpy.ops.object.mode_set(mode='OBJECT')
obj.parent=rig;mod=obj.modifiers.new('Rigid mechanical skin','ARMATURE');mod.object=rig
for b in rig.pose.bones:b.rotation_mode='XYZ'

# Compact actuator housings close the visual gaps under the separated armor.
def material(name,color,metallic,roughness):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color;p.inputs['Metallic'].default_value=metallic;p.inputs['Roughness'].default_value=roughness;return m
joint=material('RONIN graphite actuators',(.022,.042,.045,1),.7,.35)
trim=material('RONIN aged gold trim',(.5,.32,.10,1),.8,.26)
glow=material('RONIN wrist reactor emission',(.04,.25,.4,1),.1,.3)
g=glow.node_tree.nodes.get('Principled BSDF');g.inputs['Emission Color'].default_value=(.12,.65,1,1);g.inputs['Emission Strength'].default_value=3
pieces=[]
def bind(o,name,mat):
 o.data.materials.append(mat);o.vertex_groups.new(name=name).add(list(range(len(o.data.vertices))),1,'REPLACE')
 if o.data.uv_layers:o.data.uv_layers.active.name='Ronin_Surface'
 else:o.data.uv_layers.new(name='Ronin_Surface')
 for f in o.data.polygons:f.use_smooth=True
 pieces.append(o)
def sphere(center,radius,name):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=radius,location=center);bind(bpy.context.object,name,joint)
def cylinder(center,radius,length,direction,name,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=length,location=center);o=bpy.context.object;o.rotation_euler=direction.to_track_quat('Z','Y').to_euler();bind(o,name,mat)
for side in ['L','R']:
 for name,radius in [('upper_arm',.40),('forearm',.27),('thigh',.48),('shin',.38),('foot',.25)]:sphere(rig.data.bones[name+'.'+side].head_local,radius,name+'.'+side)
sphere((0,0,10),.45,'chest');sphere((0,.15,13.05),.32,'head')
from ronin_grip import add_sword_fingers
(OUT/'grip-repair.json').write_text(json.dumps(add_sword_fingers(bind,joint),indent=2))

# Pulse emitter integrated into the left wrist bracer.
direction=Vector((.22,-.09,-1)).normalized();center=Vector((3.92,-.3,8.55))
cylinder(center,.17,1.0,direction,'forearm.L',joint)
cylinder(center+direction*.5,.20,.12,direction,'forearm.L',trim)
cylinder(center+direction*.57,.14,.03,direction,'forearm.L',glow)
bpy.ops.object.empty_add(type='ARROWS',location=center+direction*.61);muzzle=bpy.context.object;muzzle.name='Muzzle_L'
muzzle.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();world=muzzle.matrix_world.copy();muzzle.parent=rig;muzzle.parent_type='BONE';muzzle.parent_bone='forearm.L';muzzle.matrix_world=world
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
for o in pieces:o.select_set(True)
bpy.context.view_layer.objects.active=obj;bpy.ops.object.join()
bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bm.to_mesh(obj.data);bm.free();obj.data.update()
mesh=obj.data
mesh.uv_layers.new(name='Ronin_Lightmap');mesh.uv_layers.active_index=1
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008,area_weight=.3,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
mesh.uv_layers.active_index=0;mesh.uv_layers['Ronin_Surface'].active_render=True

scene=bpy.context.scene;scene.render.fps=30
rig.animation_data_create()
def neutral():
 for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
from ronin_motions import build_ronin_motions
motion_report=build_ronin_motions(rig,obj)
(OUT/'bake-report.json').write_text(json.dumps(motion_report,indent=2))
rig['README']='RONIN-04, 16m samurai mecha. Articulated skirt, right-hand katana and left pulse bracer. Six baked motions. Source retopology remains a realtime prototype.'
neutral();scene.frame_set(1);scene.frame_start=1;scene.frame_end=181
bm=bmesh.new();bm.from_mesh(mesh);boundary=sum(e.is_boundary for e in bm.edges);bm.free()
report={'source':str(source.relative_to(ROOT)),'height_m':16,'source_triangles':intake_triangles,'vertices':len(mesh.vertices),'triangles':sum(len(f.vertices)-2 for f in mesh.polygons),'bones':len(rig.data.bones),'materials':[m.name for m in mesh.materials],'boundary_edges':boundary,'textures':textures,'animations':[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions]}
(OUT/'asset-report.json').write_text(json.dumps(report,indent=2))
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);rig.select_set(True);muzzle.select_set(True);bpy.context.view_layer.objects.active=rig
obj.parent=None
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/ronin-04.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_slide_to_zero=True,export_nla_strips=True,export_skins=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_image_format='AUTO')
runpy.run_path(str(ROOT/'scripts/fix_export_tangents.py'),init_globals={'ASSET_PATH':ROOT/'public/models/ronin-04.glb','REPORT_PATH':OUT/'tangent-repairs.json'},run_name='__main__')
obj.parent=rig

# A reusable studio for Blender inspection, excluded from the GLB selection.
stage=bpy.data.collections.new('STUDIO — excluded from GLB');scene.collection.children.link(stage)
def to_stage(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 stage.objects.link(o)
def aim(o):o.rotation_euler=(Vector((0,0,10))-o.location).to_track_quat('-Z','Y').to_euler()
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.16,.18,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-.045));floor=bpy.context.object;floor.name='Studio floor';to_stage(floor);floor.data.materials.append(material('Studio graphite',(.055,.07,.085,1),.15,.8))
for pos,power,color in [((7,-12,22),2600,(.85,.93,1)),((-9,-6,12),1900,(1,.95,.88)),((8,8,20),3500,(.7,.85,1))]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.color=color;l.data.shape='DISK';l.data.size=8;aim(l);to_stage(l)
bpy.ops.object.camera_add(location=(16,-32,14));cam=bpy.context.object;aim(cam);cam.data.type='ORTHO';cam.data.ortho_scale=25;cam.data.clip_end=2000;scene.camera=cam;to_stage(cam)
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=24;area.spaces.active.region_3d.view_location=(0,0,10);area.spaces.active.shading.type='MATERIAL'
rig.animation_data.action=bpy.data.actions['SwordSlash'];scene.frame_set(31)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/RONIN-04.blend'))
scene.render.filepath=str(OUT/'ronin-04-beauty.png')
if '--skip-render' not in sys.argv:bpy.ops.render.render(write_still=True)
print('ASSET_REPORT',json.dumps(report))

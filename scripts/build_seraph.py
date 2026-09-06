"""Rebuild SERAPH-03 from its preserved Tripo retopology, entirely locally."""
import bpy, bmesh, math, json, sys, runpy
import numpy as np
from pathlib import Path
from collections import defaultdict
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/seraph-03';TEX=ROOT/'public/textures/seraph-03'
OUT.mkdir(parents=True,exist_ok=True);TEX.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'scripts'))
from motion_library import build_motions
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
source=next((ROOT/'assets/seraph-03/retopo').glob('*model_url.glb'))
bpy.ops.import_scene.gltf(filepath=str(source))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');obj.name='SERAPH_03_Armor'
coords=[Matrix.Rotation(-math.pi/2,4,'Z')@(obj.matrix_world@v.co) for v in obj.data.vertices]
lo=min(p.z for p in coords);scale=20/(max(p.z for p in coords)-lo)
for v,p in zip(obj.data.vertices,coords):v.co=(p-Vector((0,0,lo)))*scale
obj.matrix_world=Matrix.Identity(4)
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
mesh=obj.data;intake_triangles=sum(len(f.vertices)-2 for f in mesh.polygons)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00006)
# Two collinear source triangles have zero geometric and UV area.
zero_faces=[f for f in bm.faces if f.calc_area()<1e-7]
bmesh.ops.delete(bm,geom=zero_faces,context='FACES_ONLY')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
mesh.uv_layers.active.name='Seraph_Surface'
mat=mesh.materials[0];mat.name='SERAPH titanium and silver — amber emission';mat.use_nodes=True
bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');base=None
textures=[]
for n in list(mat.node_tree.nodes):
 if n.type!='TEX_IMAGE' or not n.image:continue
 im=n.image
 semantic='BaseColor' if any(l.to_socket==bsdf.inputs['Base Color'] for l in n.outputs['Color'].links) else ('Normal' if 'normal' in im.name.lower() else 'ORM')
 if semantic=='BaseColor':base=im
 ext='jpg' if im.packed_file and bytes(im.packed_file.data[:2])==b'\xff\xd8' else 'png'
 im.filepath_raw=str(TEX/f'Seraph_{semantic}.{ext}');im.file_format='JPEG' if ext=='jpg' else 'PNG';im.save();im.pack()
 textures.append({'semantic':semantic,'size':list(im.size),'file':im.filepath_raw})
 uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='Seraph_Surface';mat.node_tree.links.new(uv.outputs['UV'],n.inputs['Vector'])
bsdf.inputs['Coat Weight'].default_value=.28;bsdf.inputs['Coat Roughness'].default_value=.22
if base:
 w,h=base.size;px=np.empty(w*h*4,dtype=np.float32);base.pixels.foreach_get(px);px=px.reshape((-1,4))
 mask=np.clip((np.minimum(px[:,0]-px[:,2],px[:,1]-px[:,2])-.06)*7,0,1)
 out=np.zeros_like(px);out[:,:3]=mask[:,None]*np.array([1,.42,.08]);out[:,3]=1
 em=bpy.data.images.new('Seraph_Emission',width=w,height=h);em.pixels.foreach_set(out.ravel());em.filepath_raw=str(TEX/'Seraph_Emission.png');em.file_format='PNG';em.save();em.pack()
 en=mat.node_tree.nodes.new('ShaderNodeTexImage');en.image=em;uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='Seraph_Surface'
 mat.node_tree.links.new(uv.outputs['UV'],en.inputs['Vector']);mat.node_tree.links.new(en.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=2.2
# Wing depth and limb boundaries measured in all three source views.
def section(p):
 x,y,z=p;a=abs(x);side='L' if x>0 else 'R'
 if y>1.45 and ((z>13.1 and a>1.25) or (z>10.4 and a>4.0)):
  return ('wing_outer.' if a>3.15 else 'wing_root.')+side
 if z>13.1 and a<1.35:return 'head'
 # The cannon joins the elbow on a plane perpendicular to its long axis;
 # a horizontal cut incorrectly split its tall rear housing.
 cannon_along=(Vector(p)-Vector((-3.15,.8,10.35))).dot(Vector((-.31,-.32,-.895)))
 if x< -2.1 and 9.1<z<11.65 and cannon_along>-.3:return 'forearm.R'
 # The cannon's inside edge slopes outward toward its muzzle, with a clear
 # empty gap from the right leg. Include the complete inner barrel surface.
 if z<10.35 and x<-(2.55+.17*max(0,10-z)):return 'forearm.R'
 arm_inner=min(2.75,1.65+.3*max(0,12.2-z))
 if (a>arm_inner and z>6.6) or (x< -4.0 and z>1.25):
  if z>11.65:return 'shoulder.'+side
  if z>10.35:return 'upper_arm.'+side
  if side=='R' or z>8.0:return 'forearm.'+side
  return 'hand.'+side
 if z>10.0:return 'chest'
 if z>9.05 or (z>7.7 and a<.7) or (z>8.3 and a<.9+.6*(z-8.3)):return 'pelvis'
 if z>6.55:return 'thigh.'+side
 if z>1.85:return 'shin.'+side
 return 'foot.'+side

# Inspect connected surface islands after the initial anatomical assignment.
# The wing's narrow lower feathers cross a shoulder silhouette in front view;
# their isolated islands belong to the wing assembly, not the shoulder plate.
labels={f.index:section(f.center) for f in mesh.polygons}
vertex_faces=defaultdict(set)
for f in mesh.polygons:
 for vi in f.vertices:vertex_faces[vi].add(f.index)
repairs=[]
for side in ['L','R']:
 for part in ['shoulder.','wing_outer.']:
  group=part+side;remaining={fi for fi,name in labels.items() if name==group};components=[]
  while remaining:
   pending=[remaining.pop()];component=set(pending)
   while pending:
    fi=pending.pop()
    for vi in mesh.polygons[fi].vertices:
     fresh=vertex_faces[vi]&remaining;remaining-=fresh;component|=fresh;pending.extend(fresh)
   components.append(component)
  components.sort(key=len,reverse=True)
  for component in components[1:]:
   coords=[mesh.vertices[vi].co for fi in component for vi in mesh.polygons[fi].vertices]
   if part=='shoulder.':target='wing_outer.'+side
   elif max(v.z for v in coords)<11.1 and side=='R':target='forearm.R'
   else:target='wing_root.'+side
   for fi in component:labels[fi]=target
   repairs.append({'from':group,'to':target,'faces':len(component)})
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
   face.append(remap[vi]);uvs.append(tuple(old.uv_layers['Seraph_Surface'].data[li].uv))
  faces.append(face)
mesh=bpy.data.meshes.new('SERAPH_RigidArmor');mesh.from_pydata(verts,[],faces);mesh.update();obj.data=mesh
mesh.materials.append(mat)
uv=mesh.uv_layers.new(name='Seraph_Surface')
for i,co in enumerate(uvs):uv.data[i].uv=co
for f,mi in zip(mesh.polygons,mats):f.material_index=mi;f.use_smooth=True
for name,indices in weights.items():obj.vertex_groups.new(name=name).add(indices,1,'REPLACE')

# Rest-space joints measured from front and side inspection renders (meters).
bpy.ops.object.armature_add(enter_editmode=True);rig=bpy.context.object;rig.name='SERAPH_03_RIG';rig.show_in_front=True
eb=rig.data.edit_bones;eb.remove(eb[0])
def bone(name,head,tail,parent=None,deform=True):
 b=eb.new(name);b.head=head;b.tail=tail;b.use_deform=deform
 if parent:b.parent=eb[parent]
bone('root',(0,0,0),(0,0,1),deform=False)
bone('pelvis',(0,.8,8.95),(0,.85,10.0),'root')
bone('chest',(0,.85,10.0),(0,1.3,13.1),'pelvis')
bone('head',(0,1.3,13.1),(0,1.3,15.1),'chest')
for sign,side in [(1,'L'),(-1,'R')]:
 bone('shoulder.'+side,(sign*1.35,1.1,12.7),(sign*2.3,1.1,12.25),'chest')
 bone('upper_arm.'+side,(sign*2.3,1.1,12.25),(sign*3.15,.8,10.35),'shoulder.'+side)
 bone('forearm.'+side,(sign*3.15,.8,10.35),(sign*3.75,.2,8.0),'upper_arm.'+side)
 bone('hand.'+side,(sign*3.75,.2,8.0),(sign*3.9,.0,6.9),'forearm.'+side)
 bone('thigh.'+side,(sign*1.05,.8,8.95),(sign*1.85,.9,6.55),'pelvis')
 bone('shin.'+side,(sign*1.85,.9,6.55),(sign*2.5,1.35,1.85),'thigh.'+side)
 bone('foot.'+side,(sign*2.5,1.35,1.85),(sign*2.6,-.5,.45),'shin.'+side)
 bone('wing_root.'+side,(sign*1.35,2.05,12.9),(sign*3.0,2.5,14.85),'chest')
 bone('wing_outer.'+side,(sign*3.0,2.5,14.85),(sign*6.7,2.5,17.2),'wing_root.'+side)
bpy.ops.object.mode_set(mode='OBJECT')
obj.parent=rig;mod=obj.modifiers.new('Rigid mechanical skin','ARMATURE');mod.object=rig
for b in rig.pose.bones:b.rotation_mode='XYZ'

# Compact actuator housings close the visual gaps under the separated armor.
def material(name,color,metallic,roughness):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color;p.inputs['Metallic'].default_value=metallic;p.inputs['Roughness'].default_value=roughness;return m
joint=material('SERAPH graphite actuators',(.022,.032,.045,1),.7,.35)
trim=material('SERAPH brushed white steel',(.7,.77,.83,1),.8,.26)
glow=material('SERAPH wrist reactor emission',(.03,.25,.4,1),.1,.3)
g=glow.node_tree.nodes.get('Principled BSDF');g.inputs['Emission Color'].default_value=(.12,.65,1,1);g.inputs['Emission Strength'].default_value=3
pieces=[]
def bind(o,name,mat):
 o.data.materials.append(mat);o.vertex_groups.new(name=name).add(list(range(len(o.data.vertices))),1,'REPLACE')
 if o.data.uv_layers:o.data.uv_layers.active.name='Seraph_Surface'
 else:o.data.uv_layers.new(name='Seraph_Surface')
 for f in o.data.polygons:f.use_smooth=True
 pieces.append(o)
def sphere(center,radius,name):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=radius,location=center);bind(bpy.context.object,name,joint)
def cylinder(center,radius,length,direction,name,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=length,location=center);o=bpy.context.object;o.rotation_euler=direction.to_track_quat('Z','Y').to_euler();bind(o,name,mat)
for side in ['L','R']:
 for name,radius in [('upper_arm',.40),('forearm',.27),('thigh',.48),('shin',.38),('foot',.25)]:sphere(rig.data.bones[name+'.'+side].head_local,radius,name+'.'+side)
sphere((0,.85,10),.55,'chest');sphere((0,1.3,13.1),.32,'head')
# The source cannon replaces the right forearm. Export a muzzle socket on
# its actual barrel mouth; the hand.R bone is a control without hand geometry.
direction=Vector((-.31,-.32,-.895)).normalized()
bpy.ops.object.empty_add(type='ARROWS',location=(-6.35,-2.85,2.3));muzzle=bpy.context.object;muzzle.name='Muzzle_R'
muzzle.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();world=muzzle.matrix_world.copy();muzzle.parent=rig;muzzle.parent_type='BONE';muzzle.parent_bone='forearm.R';muzzle.matrix_world=world
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
for o in pieces:o.select_set(True)
bpy.context.view_layer.objects.active=obj;bpy.ops.object.join()
bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bm.to_mesh(obj.data);bm.free();obj.data.update()
mesh=obj.data
mesh.uv_layers.new(name='Seraph_Lightmap');mesh.uv_layers.active_index=1
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008,area_weight=.3,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
mesh.uv_layers.active_index=0;mesh.uv_layers['Seraph_Surface'].active_render=True

scene=bpy.context.scene;scene.render.fps=30
rig.animation_data_create()
def neutral():
 for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
from seraph_motions import build_seraph_motions
motion_report=build_seraph_motions(rig,obj)
(OUT/'bake-report.json').write_text(json.dumps(motion_report,indent=2))
rig['README']='SERAPH-03, 20m wingtip height. Rigid metal wings and a right forearm cannon. Six baked motions. Source retopology remains a realtime prototype.'
neutral();scene.frame_set(1);scene.frame_start=1;scene.frame_end=181
bm=bmesh.new();bm.from_mesh(mesh);boundary=sum(e.is_boundary for e in bm.edges);bm.free()
report={'source':str(source.relative_to(ROOT)),'height_m':20,'source_triangles':intake_triangles,'vertices':len(mesh.vertices),'triangles':sum(len(f.vertices)-2 for f in mesh.polygons),'bones':len(rig.data.bones),'materials':[m.name for m in mesh.materials],'boundary_edges':boundary,'textures':textures,'animations':[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions]}
(OUT/'asset-report.json').write_text(json.dumps(report,indent=2))
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);rig.select_set(True);muzzle.select_set(True);bpy.context.view_layer.objects.active=rig
obj.parent=None
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/seraph-03.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_slide_to_zero=True,export_nla_strips=True,export_skins=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_image_format='AUTO')
runpy.run_path(str(ROOT/'scripts/fix_export_tangents.py'),init_globals={'ASSET_PATH':ROOT/'public/models/seraph-03.glb','REPORT_PATH':OUT/'tangent-repairs.json'},run_name='__main__')
obj.parent=rig

# A reusable studio for Blender inspection, excluded from the GLB selection.
stage=bpy.data.collections.new('STUDIO — excluded from GLB');scene.collection.children.link(stage)
def to_stage(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 stage.objects.link(o)
def aim(o):o.rotation_euler=(Vector((0,0,10))-o.location).to_track_quat('-Z','Y').to_euler()
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.16,.18,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-.035));floor=bpy.context.object;floor.name='Studio floor';to_stage(floor);floor.data.materials.append(material('Studio graphite',(.055,.07,.085,1),.15,.8))
for pos,power,color in [((7,-12,22),2600,(.85,.93,1)),((-9,-6,12),1900,(1,.95,.88)),((8,8,20),3500,(.7,.85,1))]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.color=color;l.data.shape='DISK';l.data.size=8;aim(l);to_stage(l)
bpy.ops.object.camera_add(location=(16,-32,14));cam=bpy.context.object;aim(cam);cam.data.type='ORTHO';cam.data.ortho_scale=25;cam.data.clip_end=2000;scene.camera=cam;to_stage(cam)
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=24;area.spaces.active.region_3d.view_location=(0,0,10);area.spaces.active.shading.type='MATERIAL'
rig.animation_data.action=bpy.data.actions['WingDeploy'];scene.frame_set(91)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/SERAPH-03.blend'))
scene.render.filepath=str(OUT/'seraph-03-beauty.png')
if '--skip-render' not in sys.argv:bpy.ops.render.render(write_still=True)
print('ASSET_REPORT',json.dumps(report))

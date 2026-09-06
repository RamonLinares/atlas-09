import bpy, math, json, os
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(next((ROOT/'assets/source').glob('*.glb'))))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
obj.rotation_mode='XYZ';obj.rotation_euler.z=-math.pi/2
bpy.context.view_layer.objects.active=obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
zs=[v.co.z for v in obj.data.vertices]; zmin=min(zs);factor=18/(max(zs)-zmin)
for v in obj.data.vertices: v.co*=factor;v.co.z-=zmin*factor
coords=[tuple(v.co) for v in obj.data.vertices]
print('MESH_BOUNDS',[(min(c[i] for c in coords),max(c[i] for c in coords)) for i in range(3)])
print('MATERIALS',[(m.name,[(n.type,n.image.name if n.type=='TEX_IMAGE' and n.image else '') for n in m.node_tree.nodes]) for m in obj.data.materials])
world=bpy.context.scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.15,.15,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6
def point(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for pos,power,size in [((10,-15,24),2200,12),((-12,-8,14),1800,10),((8,10,18),2400,8)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size;point(l,(0,0,9))
bpy.ops.object.camera_add(location=(0,-38,12));cam=bpy.context.object;point(cam,(0,0,9));cam.data.type='ORTHO';cam.data.ortho_scale=21
s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=16;s.render.resolution_x=800;s.render.resolution_y=900;s.render.resolution_percentage=100
s.render.filepath=str(ROOT/'output/mesh-front.png');bpy.ops.render.render(write_still=True)
cam.location=(32,-3,12);point(cam,(0,0,9));s.render.filepath=str(ROOT/'output/mesh-side.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/source-inspection.blend'))

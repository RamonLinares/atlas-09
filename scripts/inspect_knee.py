import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/ATLAS-09.blend'))
rig=bpy.data.objects['ATLAS_09_RIG'];obj=bpy.data.objects['ATLAS_09_Armor']
rig.animation_data.action=bpy.data.actions['KneelFire'];bpy.context.scene.frame_set(102);bpy.context.view_layer.update()
ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();groups={}
for v in mesh.vertices:
 name=obj.vertex_groups[obj.data.vertices[v.index].groups[0].group].name
 if name not in groups or v.co.z<groups[name]['z']:groups[name]={'z':v.co.z,'co':list(v.co),'index':v.index}
print('GROUP_MINIMA',json.dumps(sorted(groups.items(),key=lambda x:x[1]['z'])))
print('KNEE',list(rig.pose.bones['shin.R'].head),'FOOT',list(rig.pose.bones['foot.R'].head),'ROOT',list(rig.pose.bones['root'].matrix.translation))
ev.to_mesh_clear()

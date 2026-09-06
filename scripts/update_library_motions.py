"""Update only animation data in the saved Blender assets, preserving mesh/UVs."""
import bpy,sys,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from retarget_library import retarget_motions
names=['AETHER-02','ATLAS-09']
if '--aether-only' in sys.argv:names=['AETHER-02']
for name in names:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/{name}.blend'))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');obj=next(o for o in bpy.context.scene.objects if o.type=='MESH' and 'Armor' in o.name)
 rig.animation_data.action=None
 for track in list(rig.animation_data.nla_tracks):
  if track.name in ['Awaken','Walk','PunchCombo','Collapse']:rig.animation_data.nla_tracks.remove(track)
 for a in list(bpy.data.actions):
  if a.name in ['Awaken','Walk','PunchCombo','Collapse']:bpy.data.actions.remove(a)
 report=retarget_motions(rig,obj)
 rig['README']=rig.get('README','').replace('five baked clips','seven baked clips')
 rig['Imported motions']='Walk, PunchCombo and Collapse: Quaternius / Gonzalo Furnier CC0 Standard libraries; adapted for rigid armor, baked locally.'
 asset_report=ROOT/('output/aether-02/asset-report.json' if name=='AETHER-02' else 'output/asset-report.json')
 if asset_report.exists():
  metadata=json.loads(asset_report.read_text());metadata['animations']=[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions];metadata['limitations']=[x.replace('Five supplied clips','Seven supplied clips') for x in metadata.get('limitations',[])];asset_report.write_text(json.dumps(metadata,indent=2)+'\n')
 out=ROOT/'output/motion'/f'{name.lower()}-library-bake.json';out.write_text(json.dumps(report,indent=2)+'\n')
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);rig.select_set(True)
 for o in bpy.context.scene.objects:
  if o.name=='Muzzle_R':o.select_set(True)
 bpy.context.view_layer.objects.active=rig;obj.parent=None
 bpy.ops.export_scene.gltf(filepath=str(ROOT/f'public/models/{name.lower()}.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_slide_to_zero=True,export_nla_strips=True,export_skins=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_image_format='AUTO')
 runpy.run_path(str(ROOT/'scripts/fix_export_tangents.py'),init_globals={'ASSET_PATH':ROOT/f'public/models/{name.lower()}.glb','REPORT_PATH':ROOT/'output/motion'/f'{name.lower()}-library-tangent-repairs.json'},run_name='__main__')
 obj.parent=rig;rig.animation_data.action=bpy.data.actions['Sentinel'];bpy.context.scene.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'blender/{name}.blend'))
 print('RETARGET_REPORT',name,json.dumps(report))

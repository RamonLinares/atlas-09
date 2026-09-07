"""Check armor contact and arm continuity for the katana placement/retrieval."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/ronin-04'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/RONIN-04.blend'))
r=bpy.data.objects['RONIN_04_RIG'];o=bpy.data.objects['RONIN_04_Armor']
chest=o.vertex_groups['chest'].index
faces=[list(f.vertices) for f in o.data.polygons if f.material_index==0 and all(any(g.group==chest for g in o.data.vertices[i].groups) for i in f.vertices)]
surface=BVHTree.FromPolygons([v.co for v in o.data.vertices],faces)
mounts=json.loads((OUT/'magnetic-dock.json').read_text())['magnetic_mounts']
contact_error=max(surface.find_nearest(Vector(m['contact']))[3] for m in mounts)
assert contact_error<1e-4
assert all((Vector(m['base'])-Vector(m['contact'])).dot(Vector(m['face'])-Vector(m['contact']))<0 for m in mounts)
r.animation_data.action=bpy.data.actions['PunchCombo']
report={'mount_contact_error_m':contact_error,'maximum_wrist_bend_rad':0,'maximum_joint_step_rad':0,'placement_samples':289,'retrieval_samples':289}
for start in [0,9.4]:
    previous=None
    for i in range(289):
        t=start+i/120;frame=t*30+1
        bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
        wrist=r.pose.bones['hand.R'].rotation_euler.to_quaternion()
        report['maximum_wrist_bend_rad']=max(report['maximum_wrist_bend_rad'],min(wrist.angle,2*math.pi-wrist.angle))
        current=[r.pose.bones[n].matrix.to_quaternion() for n in ['upper_arm.R','forearm.R','hand.R']]
        if previous:report['maximum_joint_step_rad']=max(report['maximum_joint_step_rad'],max(2*math.acos(min(1,abs(a.dot(c)))) for a,c in zip(current,previous)))
        previous=current
assert report['maximum_wrist_bend_rad']<math.radians(30),report
assert report['maximum_joint_step_rad']<.08,report
(OUT/'stow-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('STOW_VALIDATION',json.dumps(report))

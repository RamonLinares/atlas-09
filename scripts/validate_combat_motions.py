"""Validate added combat clips on each evaluated, fully armored character."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
characters=['ATLAS-09','AETHER-02','SERAPH-03','RONIN-04']
if '--character' in sys.argv:characters=sys.argv[sys.argv.index('--character')+1].split(',')
for character in characters:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/{character}.blend'))
    rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');obj=next(o for o in bpy.context.scene.objects if o.type=='MESH' and 'Armor' in o.name)
    scene=bpy.context.scene;bones=rig.pose.bones;results=[]
    report=json.loads((ROOT/f'output/motion/{character.lower()}-combat-bake.json').read_text())
    edges=np.array([e.vertices[:] for e in obj.data.edges])
    def sample(frame):
        scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();p=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',p);ev.to_mesh_clear();return p.reshape((-1,3))
    for item in report['animations']:
        name=item['name'];action=bpy.data.actions[name];rig.animation_data.action=action;start,end=map(int,action.frame_range)
        first=sample(start);last=sample(end);base=np.linalg.norm(first[edges[:,0]]-first[edges[:,1]],axis=1)
        low=1e9;core_clearance=0;gap=0;stretch=0;motion=0;step=0;previous=None;head_low=1e9;torso_turn=0;first_chest=None;blade=[];wrist=0
        for frame in np.arange(start,end+.01,.5):
            p=sample(float(frame));assert np.isfinite(p).all()
            low=min(low,float(p[:,2].min()));
            if frame>=item['entry_frames']+1 and frame<=end-item['recovery_frames']-12:core_clearance=max(core_clearance,float(p[:,2].min()))
            motion=max(motion,float(np.linalg.norm(p-first,axis=1).max()))
            stretch=max(stretch,float(abs(np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1)-base).max()))
            for side in ['L','R']:
                for part in ['forearm','hand','shin','foot']:
                    b=bones[part+'.'+side];gap=max(gap,(b.head-b.parent.tail).length)
            current={n:bones[n].matrix.to_quaternion() for n in ['pelvis','chest','head','upper_arm.L','upper_arm.R','forearm.L','forearm.R']}
            if previous:step=max(step,max(2*math.acos(min(1,abs(q.dot(previous[n])))) for n,q in current.items()))
            previous=current;first_chest=first_chest or current['chest'];torso_turn=max(torso_turn,2*math.acos(min(1,abs(current['chest'].dot(first_chest)))))
            head_low=min(head_low,bones['head'].head.z)
            if character=='RONIN-04':
                angle=bones['hand.R'].rotation_euler.to_quaternion().angle;wrist=max(wrist,min(angle,abs(angle-2*math.pi)))
                blade.append(list(bones['sword.R'].tail))
        closure=float(np.linalg.norm(last-first,axis=1).max());hold=float(np.linalg.norm(sample(end)-sample(end-10),axis=1).max())
        assert low>-.004 and gap<1e-4 and stretch<.0002,(character,name,low,gap,stretch)
        assert motion>.2 and step<1.2,(character,name,motion,step)
        if name!='Knockback':assert closure<1e-4,(character,name,closure)
        else:assert hold<1e-4,(character,name,hold)
        if name=='DodgeRoll':
            assert torso_turn>2.5,(character,'roll did not rotate through the floor phase',torso_turn)
            assert core_clearance<.08,(character,'roll ground clearance',core_clearance)
        if character=='RONIN-04':assert min(wrist,abs(wrist-2*math.pi))<1e-4,(name,'weapon wrist unlocked',wrist)
        result={'clip':name,'floor_min_m':low,'max_core_ground_clearance_m':core_clearance,'joint_gap_m':gap,'edge_length_error_m':stretch,'max_displacement_m':motion,'half_frame_rotation_step_rad':step,'loop_error_m':closure if name!='Knockback' else None,'final_hold_error_m':hold,'minimum_head_height_m':head_low,'torso_turn_rad':torso_turn}
        if blade:result['blade_tip_sweep_m']=np.ptp(np.asarray(blade),axis=0).tolist()
        results.append(result);print('COMBAT_VALIDATED',character,name,flush=True)
    (ROOT/f'output/motion/{character.lower()}-combat-validation.json').write_text(json.dumps(results,indent=2)+'\n')

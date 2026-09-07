"""Fit additional CC0 combat clips to the four existing humanoid deliveries."""
import bpy,json,math,sys,runpy
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from retarget_library import MotionSource,retarget_motions
from append_glb_animations import append_animations
OUT=ROOT/'output/motion';OUT.mkdir(exist_ok=True)
sources={i:MotionSource(ROOT/f'assets/animations/quaternius/UAL{i}_selected.glb') for i in [1,2]}
definitions={'HitChest':(1,'Hit_Chest'),'HitHead':(1,'Hit_Head'),'Knockback':(2,'Hit_Knockback'),'DodgeRoll':(1,'Roll'),'SwordCombo':(2,'Sword_Regular_Combo'),'SwordBlock':(2,'Sword_Block')}
characters=['ATLAS-09','AETHER-02','SERAPH-03','RONIN-04']
if '--character' in sys.argv:characters=[sys.argv[sys.argv.index('--character')+1]]

def update():bpy.context.view_layer.update()
def curves(action):
    return [c for layer in action.layers for strip in layer.strips for bag in strip.channelbags for c in bag.fcurves]
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)

for character in characters:
    print('COMBAT_START',character,flush=True)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/{character}.blend'))
    scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');bones=rig.pose.bones
    obj=next(o for o in scene.objects if o.type=='MESH' and 'Armor' in o.name)
    rig.animation_data.action=bpy.data.actions['Sentinel'];scene.frame_set(1);update()
    neutral={b.name:(b.rotation_euler.to_quaternion().copy(),b.location.copy()) for b in bones}
    rig.animation_data.action=None
    names=['HitChest','HitHead','Knockback']+(['DodgeRoll'] if character=='AETHER-02' else [])+(['SwordCombo','SwordBlock'] if character=='RONIN-04' else [])
    if '--clips' in sys.argv:names=[n for n in names if n in sys.argv[sys.argv.index('--clips')+1].split(',')]
    for track in list(rig.animation_data.nla_tracks):
        if track.name in names:rig.animation_data.nla_tracks.remove(track)
    for action in list(bpy.data.actions):
        if action.name in names:bpy.data.actions.remove(action)
    context={};specs=[]
    for name in names:
        library,clip=definitions[name];source=sources[library];duration=source.duration(clip)
        if name=='Knockback':duration+=.6
        def sample(t,name=name,source=source,clip=clip):
            context['name']=name;context['t']=t
            return source.sample(clip,min(t,source.duration(clip)))
        specs.append((name,duration,sample))
    def aim(name,direction):
        b=bones[name];q=(b.bone.tail_local-b.bone.head_local).rotation_difference(direction)@b.bone.matrix_local.to_quaternion()
        b.matrix=Matrix.Translation(b.head)@q.to_matrix().to_4x4();update()
    def equipment():
        chest=bones['chest'].matrix.to_3x3()@bones['chest'].bone.matrix_local.to_3x3().inverted()
        if character=='SERAPH-03':
            # Keep the integrated cannon clear of the ribs during a flinch.
            aim('upper_arm.R',chest@Vector((-.30,-.20,-1)))
            aim('forearm.R',chest@Vector((-.14,-1,-.05)))
            for side in ['L','R']:
                for part in ['wing_root','wing_outer']:
                    name=part+'.'+side;bones[name].rotation_quaternion=neutral[name][0]
                    if context['name']=='Knockback':
                        unfold=smooth((context['t']-.1)/.5)
                        bones[name].rotation_quaternion=neutral[name][0].slerp(Quaternion(),unfold)
                        if part=='wing_root':
                            axis=bones[name].bone.matrix_local.to_3x3().inverted()@Vector((1,0,0))
                            bones[name].rotation_quaternion=Quaternion(axis,.18*unfold)@bones[name].rotation_quaternion
        elif character=='RONIN-04':
            if context['name']=='SwordCombo':
                # Replace the last inward cut with an outboard diagonal and
                # raised recovery. The whole arm carries the locked grip.
                t=context['t']
                weight=smooth((t-1.05)/.4)
                original={n:bones[n].rotation_quaternion.copy() for n in ['upper_arm.R','forearm.R']}
                aim('upper_arm.R',Vector((-.7,-.35,-1)))
                arm=bones['upper_arm.R'];arm.rotation_quaternion=original[arm.name].slerp(arm.rotation_quaternion,weight);update()
                cut=smooth((t-1.4)/.32);recover=smooth((t-2.1)/.9)
                direction=Vector((-.55,-.4,1)).lerp(Vector((-1,-.5,-.18)),cut).lerp(Vector((-.55,-.35,.9)),recover)
                forearm=bones['forearm.R']
                blade_axis=Vector((-.3402919,-.7154602,-.6101788))
                q=blade_axis.rotation_difference(direction)@forearm.bone.matrix_local.to_quaternion()
                forearm.matrix=Matrix.Translation(forearm.head)@q.to_matrix().to_4x4();update()
                forearm.rotation_quaternion=original[forearm.name].slerp(forearm.rotation_quaternion,weight)
            if context['name'] in ['HitChest','HitHead','Knockback']:
                aim('upper_arm.R',chest@Vector((-.5,-.3,-1)))
                aim('forearm.R',chest@Vector((-.4,-.8,-.2)))
            if context['name']=='SwordBlock':
                bones['forearm.R'].rotation_quaternion=bones['forearm.R'].rotation_quaternion@Quaternion((0,1,0),-.15)
            bones['hand.R'].rotation_quaternion=(1,0,0,0)
            bones['sword.R'].rotation_quaternion=(1,0,0,0);bones['sword.R'].location=(0,0,0)
            for side in ['L','R']:
                thigh=bones['thigh.'+side];skirt=bones['skirt.'+side]
                delta=thigh.matrix.to_3x3()@thigh.bone.matrix_local.to_3x3().inverted()
                skirt.matrix=Matrix.Translation(skirt.head)@delta.to_4x4()@skirt.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
        update()
    report=retarget_motions(rig,obj,timescale_override=1.2 if character=='ATLAS-09' else 1.0,pose_adjust=equipment,motion_specs=specs)
    bounds_path=ROOT/f'src/{character.lower().split("-")[0]}-combat-bounds.json'
    bounds=json.loads(bounds_path.read_text()) if bounds_path.exists() else {}
    for item in report:
        name=item['name'];action=bpy.data.actions[name];rig.animation_data.action=action;poses=[]
        for frame in range(1,item['frames']+1):
            scene.frame_set(frame);update();poses.append({b.name:(b.rotation_euler.to_quaternion().copy(),b.location.copy()) for b in bones})
        rig.animation_data.action=None
        for track in list(rig.animation_data.nla_tracks):
            if track.name==name:rig.animation_data.nla_tracks.remove(track)
        bpy.data.actions.remove(action)
        intro=round((.55 if name in ['SwordCombo','DodgeRoll'] else .25)*30)
        outro=0 if name=='Knockback' else round((.65 if name=='SwordCombo' else .45)*30)
        hold=12;sequence=[]
        def blended(a,b,f):return {n:(a[n][0].slerp(b[n][0],f),a[n][1].lerp(b[n][1],f)) for n in a}
        for i in range(intro):sequence.append(blended(neutral,poses[0],smooth(i/intro)))
        sequence+=poses
        if outro:
            for i in range(1,outro+1):sequence.append(blended(poses[-1],neutral,smooth(i/outro)))
        sequence.extend([sequence[-1]]*hold)
        previous={}
        for frame,pose in enumerate(sequence,1):
            for b in bones:
                q,loc=pose[b.name];b.rotation_euler=q.to_euler('XYZ',previous[b.name]) if b.name in previous else q.to_euler();b.location=loc
            update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear()
            if low<0:bones['root'].matrix=Matrix.Translation((0,0,-low+.002))@bones['root'].matrix;update()
            for b in bones:
                previous[b.name]=b.rotation_euler.copy();b.keyframe_insert('rotation_euler',frame=frame,group=b.name);b.keyframe_insert('location',frame=frame,group=b.name)
        action=rig.animation_data.action;action.name=name;action.use_fake_user=True
        for c in curves(action):
            for k in c.keyframe_points:k.interpolation='LINEAR'
        # Bound the complete swept silhouette and floor contact after adding
        # the entry/recovery poses, including interpolation between keys.
        lifts=[0.]*len(sequence);lo=Vector((1e9,1e9,1e9));hi=-lo;pose_boxes=[]
        for i in range(len(sequence)-1):
            for sub in [0,.25,.5,.75]:
                scene.frame_set(i+1,subframe=sub);update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
                floor=min(v.co.z for v in mesh.vertices)
                pose_min=[min(v.co[axis] for v in mesh.vertices) for axis in range(3)];pose_max=[max(v.co[axis] for v in mesh.vertices) for axis in range(3)]
                for axis in range(3):lo[axis]=min(lo[axis],pose_min[axis]);hi[axis]=max(hi[axis],pose_max[axis])
                if sub==0:pose_boxes.append({'min':pose_min,'max':pose_max})
                ev.to_mesh_clear()
                if floor<0:lifts[i]=max(lifts[i],-floor+.003);lifts[i+1]=max(lifts[i+1],-floor+.003)
        if name!='Knockback':lifts[0]=lifts[-1]=max(lifts[0],lifts[-1])
        up=bones['root'].bone.matrix_local.to_3x3().inverted()@Vector((0,0,1))
        for c in curves(action):
            if c.data_path=='pose.bones["root"].location':
                for k in c.keyframe_points:
                    lift=lifts[round(k.co.x)-1]*up[c.array_index];k.co.y+=lift;k.handle_left.y+=lift;k.handle_right.y+=lift
        if name=='DodgeRoll':
            # A ground roll keeps contact through the change from hands to
            # shoulders to boots. Dense root keys prevent the coarse support
            # envelope from lifting the entire body between those contacts.
            for tick in range(4,len(sequence)*4+1):
                frame=tick/4;scene.frame_set(int(frame),subframe=frame-int(frame));update()
                ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear()
                bones['root'].matrix=Matrix.Translation((0,0,.002-low))@bones['root'].matrix;update()
                bones['root'].keyframe_insert('location',frame=frame,group='root')
            for c in curves(action):
                for k in c.keyframe_points:k.interpolation='LINEAR'
        # Bounds include the small support envelope and a conservative margin.
        lo-=Vector((.06,.06,.06));hi+=Vector((.06,.06,max(lifts)+.06))
        bounds[name]={'min':list(lo),'max':list(hi),'poses':[{'min':[v-.10 for v in p['min']],'max':[v+.10+(max(lifts) if i==2 else 0) for i,v in enumerate(p['max'])]} for p in pose_boxes]}
        item.update(frames=len(sequence),duration=(len(sequence)-1)/30,source_clips=[definitions[name][1]],playback='once, hold final pose' if name=='Knockback' else 'loop',entry_frames=intro,recovery_frames=outro)
        rig.animation_data.action=None;track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,1,action);track.mute=True
        print('COMBAT_BAKED',character,name,item['duration'],flush=True)
    for b in bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
    update();bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);rig.select_set(True)
    for o in scene.objects:
        if o.name.startswith('Muzzle_'):o.select_set(True)
    bpy.context.view_layer.objects.active=rig
    temporary=Path('/tmp')/f'{character.lower()}-combat-export.glb'
    bpy.ops.export_scene.gltf(filepath=str(temporary),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=False,export_anim_slide_to_zero=True,export_skins=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_image_format='AUTO')
    runpy.run_path(str(ROOT/'scripts/normalize_animation_times.py'),init_globals={'ASSET_PATH':temporary,'REPORT_PATH':OUT/f'{character.lower()}-combat-times.json'})
    item=append_animations(ROOT/f'public/models/{character.lower()}.glb',temporary,names)
    report_path=OUT/f'{character.lower()}-combat-bake.json'
    previous_report=json.loads(report_path.read_text())['animations'] if report_path.exists() else []
    report=[x for x in previous_report if x['name'] not in names]+report
    report_path.write_text(json.dumps({'animations':report,'export':item},indent=2)+'\n')
    bounds_path=ROOT/f'src/{character.lower().split("-")[0]}-combat-bounds.json';bounds_path.write_text(json.dumps(bounds,indent=2)+'\n')
    metadata_path=ROOT/('output/asset-report.json' if character=='ATLAS-09' else f'output/{character.lower()}/asset-report.json')
    if metadata_path.exists():
        metadata=json.loads(metadata_path.read_text());metadata['animations']=[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions]
        metadata_path.write_text(json.dumps(metadata,indent=2)+'\n')
    rig['Additional combat motions']='Quaternius CC0 Standard libraries: '+', '.join(x['name'] for x in report)
    rig.animation_data.action=bpy.data.actions['Sentinel'];scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'blender/{character}.blend'))
    print('COMBAT_DONE',character,flush=True)

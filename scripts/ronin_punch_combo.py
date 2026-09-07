"""Magnetic katana stow around the same library combo used by Atlas and Aether."""
import math
from mathutils import Vector,Matrix,Quaternion
from ronin_equipment import ANCHOR,DOCK_ANCHOR,dock_rotation

DURATION=12.0

def make_punch_combo(rig,obj):
    b=rig.pose.bones
    rest={n:x.bone.matrix_local.copy() for n,x in b.items()}
    def update():
        import bpy
        bpy.context.view_layer.update()
    def smooth(x):
        x=max(0,min(1,x));return x*x*(3-2*x)
    dock_q=dock_rotation()
    dock=Matrix.Translation(DOCK_ANCHOR)@dock_q.to_matrix().to_4x4()@Matrix.Translation(-ANCHOR)
    dock_hand=dock@rest['hand.R'];dock_wrist=dock_hand.translation
    def set_q(name,q):
        bone=b[name];bone.matrix=Matrix.Translation(bone.head)@q.to_matrix().to_4x4();update()
    upper_rest=(rest['forearm.R'].translation-rest['upper_arm.R'].translation).normalized()
    lower_rest=(rest['hand.R'].translation-rest['forearm.R'].translation).normalized()
    rest_normal=upper_rest.cross(lower_rest).normalized()
    hand_relative=rest['forearm.R'].to_quaternion().inverted()@rest['hand.R'].to_quaternion()
    def hinge_frame(direction,normal):
        y=direction.normalized();x=y.cross(normal).normalized();z=x.cross(y)
        return Matrix((x,y,z)).transposed()
    def reach(target,progress):
        shoulder=rest['upper_arm.R'].translation;v=target-shoulder;axis=v.normalized()
        l1=b['upper_arm.R'].bone.length;l2=b['forearm.R'].bone.length
        length=min(l1+l2-.001,max(abs(l1-l2)+.001,v.length))
        guide_keys=[(0,rest['forearm.R'].translation),(.7,Vector((-4.1,-.5,10.8))),
                    (1.4,Vector((-4.3,-1.0,12.9))),(1.9,Vector((-4.0,-1.0,13.5))),
                    (2.4,Vector((-3.21,-1.12,13.63)))]
        guide=guide_keys[-1][1]
        for (ta,a),(tb,c) in zip(guide_keys,guide_keys[1:]):
            if progress*2.4<=tb:guide=a.lerp(c,smooth((progress*2.4-ta)/(tb-ta)));break
        pole=guide-shoulder;pole=(pole-axis*pole.dot(axis)).normalized()
        along=(l1*l1-l2*l2+length*length)/(2*length)
        elbow=shoulder+axis*along+pole*math.sqrt(max(0,l1*l1-along*along))
        upper=(elbow-shoulder).normalized();lower=(target-elbow).normalized();normal=upper.cross(lower).normalized()
        uq=(hinge_frame(upper,normal)@hinge_frame(upper_rest,rest_normal).inverted()).to_quaternion()@rest['upper_arm.R'].to_quaternion()
        fq=(hinge_frame(lower,normal)@hinge_frame(lower_rest,rest_normal).inverted()).to_quaternion()@rest['forearm.R'].to_quaternion()
        return uq,fq,lower
    # Share the grip adjustment between forearm pronation and a modest wrist
    # bend. The wrist follows the forearm throughout the lift.
    uq,fq,direction=reach(dock_wrist,1)
    wanted=dock_hand.to_quaternion()@hand_relative.inverted()
    aligned=(wanted@Vector((0,1,0))).rotation_difference(direction)@wanted
    delta=aligned@fq.inverted()
    twist=2*math.atan2(Vector((delta.x,delta.y,delta.z)).dot(direction),delta.w)
    twist=(twist+math.pi)%(2*math.pi)-math.pi
    final_forearm=Quaternion(direction,twist)@fq
    wrist_delta=(final_forearm@hand_relative).inverted()@dock_hand.to_quaternion()
    def carry(t):
        progress=max(0,min(1,t/2.4))
        keys=[(0,rest['hand.R'].translation),(.7,Vector((-3.8,-2.0,11.0))),
              (1.4,Vector((-2.9,-.7,14.0))),(1.9,Vector((-2.7,.5,13.8))),(2.4,dock_wrist)]
        target=keys[-1][1]
        for (ta,a),(tb,c) in zip(keys,keys[1:]):
            if t<=tb:target=a.lerp(c,smooth((t-ta)/(tb-ta)));break
        uq,fq,direction=reach(target,progress)
        pronation=smooth(progress)
        fq=Quaternion(direction,twist*pronation)@fq
        set_q('upper_arm.R',uq);set_q('forearm.R',fq)
        set_q('hand.R',fq@hand_relative@Quaternion().slerp(wrist_delta,pronation))
    def dock_weapon():
        chest_delta=b['chest'].matrix@rest['chest'].inverted()
        b['sword.R'].matrix=chest_delta@dock@rest['sword.R'];update()
        for side in ['L','R']:
            thigh=b['thigh.'+side];skirt=b['skirt.'+side]
            delta=thigh.matrix.to_3x3()@thigh.bone.matrix_local.to_3x3().inverted()
            skirt.matrix=Matrix.Translation(skirt.head)@delta.to_4x4()@rest[skirt.name].to_quaternion().to_matrix().to_4x4()
        update()
    # Retarget the exact same CC0 jab/cross/hook sequence, with Aether's timing,
    # using the shared calibration, armor clearance and foot-contact solver.
    import bpy,json
    from pathlib import Path
    from retarget_library import retarget_motions
    report=retarget_motions(rig,obj,clip_names=['PunchCombo'],timescale_override=1.0,pose_adjust=dock_weapon)
    action=bpy.data.actions['PunchCombo'];rig.animation_data.action=action
    samples=[]
    for frame in range(1,report[0]['frames']+1):
        bpy.context.scene.frame_set(frame);update()
        samples.append({bone.name:(bone.rotation_euler.to_quaternion().copy(),bone.location.copy()) for bone in b})
    rig.animation_data.action=None
    for track in list(rig.animation_data.nla_tracks):
        if track.name=='PunchCombo':rig.animation_data.nla_tracks.remove(track)
    bpy.data.actions.remove(action)
    (Path(__file__).resolve().parents[1]/'output/ronin-04/punch-library-source.json').write_text(json.dumps(report,indent=2))
    # Capture the final dock pose before blending into the source fighting guard.
    for bone in b:bone.rotation_euler=(0,0,0);bone.location=(0,0,0)
    update();carry(2.4)
    dock_pose={bone.name:(bone.rotation_euler.to_quaternion().copy(),bone.location.copy()) for bone in b}
    def pose(u):
        t=u*DURATION
        for bone in b:bone.rotation_euler=(0,0,0);bone.location=(0,0,0);bone.scale=(1,1,1)
        update()
        if t<2.8:
            carry(min(t,2.4))
        elif t>9.1:
            carry(max(0,2.4*(1-smooth((t-9.4)/2.4))))
        else:
            blend=smooth((t-2.8)/.7)*(1-smooth((t-8.4)/.7))
            frame=max(0,min(len(samples)-1,(t-4.0)*30))
            i=min(len(samples)-2,int(frame));f=frame-i
            for bone in b:
                q0,p0=dock_pose[bone.name];qa,pa=samples[i][bone.name];qc,pc=samples[i+1][bone.name]
                bone.rotation_euler=q0.slerp(qa.slerp(qc,f),blend).to_euler()
                bone.location=p0.lerp(pa.lerp(pc,f),blend)
            update()
        if 2.4<=t<=9.4:dock_weapon()
        else:
            b['sword.R'].rotation_euler=(0,0,0);b['sword.R'].location=(0,0,0);update()
    return pose

def refine_docked_keys(rig):
    """Bake subframe compensation while the sword is constrained to the chest."""
    import bpy
    b=rig.pose.bones;s=bpy.context.scene
    rig.animation_data.action=bpy.data.actions['PunchCombo']
    dock_q=dock_rotation()
    dock=Matrix.Translation(DOCK_ANCHOR)@dock_q.to_matrix().to_4x4()@Matrix.Translation(-ANCHOR)
    sword=b['sword.R'];previous=None
    # Its hierarchy still follows the hand during the other six clips. Dense
    # compensation prevents interpolation of that moving parent from making
    # the magnetically attached weapon swim against the stationary back mount.
    for tick in range(73*4,283*4+1):
        frame=tick/4;s.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
        chest_delta=b['chest'].matrix@b['chest'].bone.matrix_local.inverted()
        sword.matrix=chest_delta@dock@sword.bone.matrix_local;bpy.context.view_layer.update()
        if previous:sword.rotation_euler=sword.rotation_euler.to_quaternion().to_euler('XYZ',previous)
        previous=sword.rotation_euler.copy()
        sword.keyframe_insert('rotation_euler',frame=frame,group=sword.name)
        sword.keyframe_insert('location',frame=frame,group=sword.name)
    # Carry the refined Euler branch through retrieval. Equivalent identity
    # rotations such as (0,0,0) and (pi,pi,pi) must not interpolate into a flip.
    for frame in range(284,362):
        s.frame_set(frame);bpy.context.view_layer.update()
        sword.rotation_euler=sword.rotation_euler.to_quaternion().to_euler('XYZ',previous)
        previous=sword.rotation_euler.copy()
        sword.keyframe_insert('rotation_euler',frame=frame,group=sword.name)
    rig.animation_data.action=None

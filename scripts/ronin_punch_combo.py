"""Magnetic katana stow around the same library combo used by Atlas and Aether."""
import math
from mathutils import Vector,Matrix
from ronin_equipment import ANCHOR,HANDLE_AXIS,DOCK_ANCHOR,DOCK_AXIS

DURATION=12.0

def make_punch_combo(rig,obj):
    b=rig.pose.bones
    rest={n:x.bone.matrix_local.copy() for n,x in b.items()}
    def update():
        import bpy
        bpy.context.view_layer.update()
    def smooth(x):
        x=max(0,min(1,x));return x*x*(3-2*x)
    def curve(t,keys):
        if t<=keys[0][0]:return keys[0][1]
        for (ta,a),(tb,c) in zip(keys,keys[1:]):
            if t<=tb:return a+(c-a)*smooth((t-ta)/(tb-ta))
        return keys[-1][1]
    dock_q=HANDLE_AXIS.rotation_difference(DOCK_AXIS)
    dock=Matrix.Translation(DOCK_ANCHOR)@dock_q.to_matrix().to_4x4()@Matrix.Translation(-ANCHOR)
    dock_hand=dock@rest['hand.R'];dock_wrist=dock_hand.translation
    def direction_q(name,direction):
        bone=b[name].bone
        return (bone.tail_local-bone.head_local).rotation_difference(Vector(direction).normalized())@rest[name].to_quaternion()
    def set_q(name,q):
        bone=b[name];bone.matrix=Matrix.Translation(bone.head)@q.to_matrix().to_4x4();update()
    def carry(t):
        # Arc around the outside of the right shoulder, then settle onto the back.
        keys=[(0,rest['hand.R'].translation),(1.0,Vector((-5.0,.9,10.6))),
              (1.8,Vector((-4.0,2.9,12.5))),(2.4,dock_wrist)]
        target=keys[-1][1]
        for (ta,a),(tb,c) in zip(keys,keys[1:]):
            if t<=tb:target=a.lerp(c,smooth((t-ta)/(tb-ta)));break
        upper=b['upper_arm.R'];lower=b['forearm.R'];v=target-upper.head
        l1=upper.bone.length;l2=lower.bone.length;length=min(l1+l2-.001,max(abs(l1-l2)+.001,v.length));axis=v.normalized()
        pole=Vector((-1,-1,0));pole=(pole-axis*pole.dot(axis)).normalized()
        along=(l1*l1-l2*l2+length*length)/(2*length)
        elbow=upper.head+axis*along+pole*math.sqrt(max(0,l1*l1-along*along))
        set_q('upper_arm.R',direction_q('upper_arm.R',elbow-upper.head))
        set_q('forearm.R',direction_q('forearm.R',target-lower.head))
        q=rest['hand.R'].to_quaternion().slerp(dock_hand.to_quaternion(),smooth(t/2.4))
        set_q('hand.R',q)
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
    dock_q=HANDLE_AXIS.rotation_difference(DOCK_AXIS)
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

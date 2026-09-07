"""Baked magnetic katana stow, four-hit unarmed combo, and retrieval."""
import math
from mathutils import Vector,Matrix
from ronin_equipment import ANCHOR,HANDLE_AXIS,DOCK_ANCHOR,DOCK_AXIS

DURATION=12.0

def make_punch_combo(rig):
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
    # Capture the final dock arm orientation for smooth withdrawal/re-gripping.
    for bone in b:bone.rotation_euler=(0,0,0);bone.location=(0,0,0)
    update();carry(2.4)
    dock_arm={n:b[n].matrix.to_quaternion() for n in ['upper_arm.R','forearm.R','hand.R']}
    guard={}
    for sign,side in [(1,'L'),(-1,'R')]:
        guard['upper_arm.'+side]=direction_q('upper_arm.'+side,(sign*.38,-.28,-1))
        guard['forearm.'+side]=direction_q('forearm.'+side,(-sign*.08,-.80,.65))
    hand_guard=guard['forearm.R']@rest['forearm.R'].to_quaternion().inverted()@rest['hand.R'].to_quaternion()
    def pose(u):
        t=u*DURATION
        for bone in b:bone.rotation_euler=(0,0,0);bone.location=(0,0,0);bone.scale=(1,1,1)
        update()
        active=smooth((t-2.8)/.7)*(1-smooth((t-8.4)/.7))
        hits=[]
        for side,start,kind in [('L',4.05,'jab'),('R',4.95,'cross'),('L',5.85,'hook'),('R',6.85,'cross')]:
            hit=curve(t,[(0,0),(start,0),(start+.25,1),(start+.33,1),(start+.72,0),(12,0)])
            wind=curve(t,[(0,0),(start-.23,0),(start,1),(start+.25,0),(12,0)])
            hits.append((side,hit,wind,kind))
        yaw=sum((1 if side=='L' else -1)*(.29*hit-.065*wind) for side,hit,wind,kind in hits)
        pitch=.025*active+sum(.075*hit for _,hit,_,_ in hits)
        torso=Matrix.Rotation(yaw,3,'Z')@Matrix.Rotation(pitch,3,'X')
        set_q('chest',torso.to_quaternion()@rest['chest'].to_quaternion())
        b['head'].rotation_euler.y=-yaw*.35;update()
        if t<2.8:
            carry(min(t,2.4))
        elif t>9.1:
            carry(max(0,2.4*(1-smooth((t-9.4)/2.4))))
        else:
            for name in ['upper_arm.R','forearm.R']:
                q=dock_arm[name].slerp(guard[name],active)
                for side,hit,wind,kind in hits:
                    if side=='R':
                        target=( -.14,-1,-.1) if name.startswith('upper') else (-.03,-1,-.08)
                        q=q.slerp(direction_q(name,target),hit)
                set_q(name,torso.to_quaternion()@q)
            set_q('hand.R',torso.to_quaternion()@dock_arm['hand.R'].slerp(hand_guard,active))
            # Keep the striking wrist aligned with its forearm.
            if active>.999:
                set_q('hand.R',b['forearm.R'].matrix.to_quaternion()@rest['forearm.R'].to_quaternion().inverted()@rest['hand.R'].to_quaternion())
        for name in ['upper_arm.L','forearm.L']:
            q=rest[name].to_quaternion().slerp(guard[name],active)
            for side,hit,wind,kind in hits:
                if side=='L':
                    direction=((.75,-.7,-.3) if name.startswith('upper') else (-.75,-1,.04)) if kind=='hook' else ((.14,-1,-.1) if name.startswith('upper') else (.03,-1,-.08))
                    q=q.slerp(direction_q(name,direction),hit)
            set_q(name,torso.to_quaternion()@q)
        b['hand.L'].rotation_euler=(0,0,0);update()
        if 2.4<=t<=9.4:
            chest_delta=b['chest'].matrix@rest['chest'].inverted()
            b['sword.R'].matrix=chest_delta@dock@rest['sword.R'];update()
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
    rig.animation_data.action=None

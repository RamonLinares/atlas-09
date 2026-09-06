"""Rest-space anatomy measured from the preserved SCORPIO mesh (metres)."""
import numpy as np
from mathutils import Vector

# Joint centres follow the actual circular couplings around the dorsal arc.
TAIL_POINTS = [
    (-.17,-.10,6.80), (-.10,1.50,6.80), (.37,3.40,7.35),
    (.68,5.10,8.55), (.96,6.15,10.25), (1.08,6.30,12.10),
    (1.00,5.40,13.80), (.68,3.90,15.30), (.35,2.10,16.05),
    (.02,.35,16.10), (-.20,-1.45,15.75), (-.45,-3.10,14.80),
]
TAIL_NAMES = [f'tail_{i:02d}' for i in range(1,len(TAIL_POINTS))]
BARREL_AXIS = Vector((-.10,-.94,-.33)).normalized()
STINGER_END = Vector(TAIL_POINTS[-1]) + BARREL_AXIS*4.35
MUZZLE_CENTER = Vector((-.95,-6.50,13.40))
TAIL_PATH = np.array(TAIL_POINTS+[tuple(STINGER_END)],dtype=float)
TAIL_VECTORS = np.diff(TAIL_PATH,axis=0)
TAIL_LENGTH_SQ = (TAIL_VECTORS*TAIL_VECTORS).sum(axis=1)

def tail_section(p):
    p=np.array(p,dtype=float)
    t=np.clip(((p-TAIL_PATH[:-1])*TAIL_VECTORS).sum(axis=1)/TAIL_LENGTH_SQ,0,1)
    d=p-(TAIL_PATH[:-1]+t[:,None]*TAIL_VECTORS)
    i=int(np.argmin((d*d).sum(axis=1)))
    return (TAIL_NAMES+['stinger'])[i]

def section(p):
    x,y,z=p;a=abs(x);side='L' if x>0 else 'R'
    # Depth keeps the dorsal tail apart from the chest, head and backpack.
    if z>12.40 or (y>.80 and z>6.0 and a<2.10) or (y>-.05 and 6.1<z<7.65 and a<1.15):
        return tail_section(p)
    if z>10.30 and a<1.35 and y<-.70:
        return 'head'
    arm_inner=2.35+.35*max(0,9.5-z)
    if a>arm_inner and z>3.0:
        # The wrist plane includes the entire claw housing and both jaws.
        if a-z> -3.60 and a>3.60 and z<9.0:
            return 'hand.'+side
        if z>9.55:
            return 'shoulder.'+side
        # Oblique elbow boundary follows the forearm coupling.
        if (a-3.65)*.60+(8.30-z)*.80>0:
            return 'forearm.'+side
        return 'upper_arm.'+side
    if z>8.55:return 'chest'
    if z>6.65 or (a<.72 and z>5.30):return 'pelvis'
    # The knee shield ends at the knee hinge and travels with the thigh.
    # Preserve its projecting lower lip instead of cutting through its face.
    if z>3.40 or (z>3.0 and y< -2.20):return 'thigh.'+side
    if z>1.45:return 'shin.'+side
    return 'foot.'+side

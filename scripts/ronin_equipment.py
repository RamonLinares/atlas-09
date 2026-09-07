"""Independent katana bindings and two magnetic back mounts."""
import bpy,math
from mathutils import Vector

ANCHOR=Vector((-3.8378894,-.343671,6.803256))
HANDLE_AXIS=Vector((.3402919,.7154602,.6101788)).normalized()
DOCK_ANCHOR=Vector((-2.25,2.9,12.25))
DOCK_AXIS=Vector((-.40,0,.916515)).normalized()

def separate_katana_labels(mesh,labels):
    # Preserve the complete, disconnected source blade. The generated guard,
    # grip and glove share irregular fused surfaces, so rebuild those as clean
    # independent parts instead of leaving weapon fragments on a free fist.
    candidates={i for f in mesh.polygons if labels[f.index]=='sword.R' for i in f.vertices}
    adjacent=[[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a,b=edge.vertices;adjacent[a].append(b);adjacent[b].append(a)
    seed=min(candidates,key=lambda i:mesh.vertices[i].co.z)
    blade={seed};pending=[seed]
    while pending:
        for i in adjacent[pending.pop()]:
            if i not in blade:blade.add(i);pending.append(i)
    removed=0
    for f in mesh.polygons:
        label=labels[f.index]
        if f.vertices[0] in blade:labels[f.index]='sword.R';continue
        d=f.center-ANCHOR;t=d.dot(HANDLE_AXIS);radius=(d-HANDLE_AXIS*t).length
        shaft=label in ['hand.R','forearm.R'] and t>1.15 and radius<.36
        guard=label=='hand.R' and t<.48 and radius<.85 and f.center.z<7.35
        weapon=label=='sword.R' or shaft or guard
        glove=label in ['hand.R','hand.L'] and f.center.z<7.78
        if weapon or glove:labels[f.index]='discard';removed+=1
    return {'preserved_blade_vertices':len(blade),'replaced_fused_faces':removed,
            'rebuilt_parts':['guard','wrapped handle','pommel','left fist','right fist']}

def add_equipment(bind,joint,trim,glow):
    def cylinder(name,center,radius,depth,axis,driver,material,oval=1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=depth,location=center)
        o=bpy.context.object;o.name=name;o.scale.y=oval;o.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
        bind(o,driver,material)
    cylinder('Katana oval gold tsuba',ANCHOR,.62,.12,HANDLE_AXIS,'sword.R',trim,.76)
    cylinder('Katana dark tsuba inset',ANCHOR+HANDLE_AXIS*.065,.47,.025,HANDLE_AXIS,'sword.R',joint,.76)
    cylinder('Katana gold blade collar',ANCHOR-HANDLE_AXIS*.10,.21,.23,HANDLE_AXIS,'sword.R',trim,.70)
    cylinder('Katana independent wrapped grip',ANCHOR+HANDLE_AXIS*1.13,.17,2.15,HANDLE_AXIS,'sword.R',joint,.85)
    for i in range(15):
        cylinder('Katana raised grip wrap',ANCHOR+HANDLE_AXIS*(.13+i*.14),.19,.045,HANDLE_AXIS,'sword.R',joint,.85)
    cylinder('Katana gold pommel',ANCHOR+HANDLE_AXIS*2.24,.22,.14,HANDLE_AXIS,'sword.R',trim,.85)
    locations=[]
    for i,t in enumerate([1.2,3.25]):
        p=DOCK_ANCHOR-DOCK_AXIS*t;locations.append(list(p))
        cylinder(f'Magnetic dock {i+1} housing',p-Vector((0,.38,0)),.34,.68,Vector((0,1,0)),'chest',joint)
        cylinder(f'Magnetic dock {i+1} gold rim',p-Vector((0,.02,0)),.29,.10,Vector((0,1,0)),'chest',trim)
        cylinder(f'Magnetic dock {i+1} luminous core',p+Vector((0,.035,0)),.19,.025,Vector((0,1,0)),'chest',glow)
    return {'dock_anchor':list(DOCK_ANCHOR),'dock_axis':list(DOCK_AXIS),'magnetic_mounts':locations}

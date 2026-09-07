"""Independent katana bindings and two magnetic back mounts."""
import bpy,math
from mathutils import Vector,Quaternion

ANCHOR=Vector((-3.8378894,-.343671,6.803256))
HANDLE_AXIS=Vector((.3402919,.7154602,.6101788)).normalized()
DOCK_ANCHOR=Vector((-2.25,1.8,12.25))
DOCK_AXIS=Vector((-.40,0,.916515)).normalized()

def dock_rotation():
    # A slight blade roll permits a relaxed over-shoulder grip.
    return Quaternion(DOCK_AXIS,-math.pi/30)@HANDLE_AXIS.rotation_difference(DOCK_AXIS)

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

def add_equipment(bind,joint,trim,glow,armor):
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
    from mathutils.bvhtree import BVHTree
    chest=armor.vertex_groups['chest'].index
    faces=[list(f.vertices) for f in armor.data.polygons if all(any(g.group==chest for g in armor.data.vertices[i].groups) for i in f.vertices)]
    surface=BVHTree.FromPolygons([v.co for v in armor.data.vertices],faces)
    locations=[]
    for i,t in enumerate([1.2,2.0]):
        p=DOCK_ANCHOR-DOCK_AXIS*t
        hit,normal,index,distance=surface.ray_cast(p+Vector((0,5,0)),Vector((0,-1,0)))
        if hit is None:hit,normal,index,distance=surface.find_nearest(p)
        assert hit is not None,('No chest armor under magnet',list(p))
        support_axis=(p-hit).normalized()
        base=hit-support_axis*.18;front=p-Vector((0,.04,0))
        assert front.y>base.y
        locations.append({'contact':list(hit),'base':list(base),'face':list(p),'driver':'chest'})
        cylinder(f'Magnetic dock {i+1} embedded base',base,.46,.40,support_axis,'chest',trim)
        cylinder(f'Magnetic dock {i+1} housing',(base+front)/2,.34,(front-base).length,(front-base).normalized(),'chest',joint)
        cylinder(f'Magnetic dock {i+1} gold rim',p-Vector((0,.02,0)),.29,.10,Vector((0,1,0)),'chest',trim)
        cylinder(f'Magnetic dock {i+1} luminous core',p+Vector((0,.035,0)),.19,.025,Vector((0,1,0)),'chest',glow)
    return {'dock_anchor':list(DOCK_ANCHOR),'dock_axis':list(DOCK_AXIS),'magnetic_mounts':locations}

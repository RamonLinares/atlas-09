"""Clean mechanical fists that can release the independent katana."""
import bpy,math
from mathutils import Vector,Matrix
from ronin_equipment import ANCHOR,HANDLE_AXIS

def add_sword_fingers(bind,material):
    def uv_and_bind(o,name):
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.015,scale_to_bounds=True)
        bpy.ops.object.mode_set(mode='OBJECT');bind(o,name,material)
    def box(name,center,dimensions,frame,driver):
        bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name
        o.rotation_euler=frame.to_euler();o.scale=dimensions
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        bevel=o.modifiers.new('Machined rounded edges','BEVEL');bevel.width=.075;bevel.segments=3
        bpy.ops.object.modifier_apply(modifier=bevel.name);uv_and_bind(o,driver)
    for side,mirror in [('R',1),('L',-1)]:
        def flip(p):return Vector((p.x*mirror,p.y,p.z))
        anchor=flip(ANCHOR);axis=flip(HANDLE_AXIS)
        u=flip(Vector((-1,0,0)));u=(u-axis*u.dot(axis)).normalized();v=axis.cross(u).normalized()
        frame=Matrix((u,v,axis)).transposed()
        center=anchor+axis*.70
        box(f'RONIN {side} armored palm',center+u*.27,(.30,.58,.80),frame,'hand.'+side)
        box(f'RONIN {side} thumb',center+u*.06+v*.23,(.35,.22,.54),frame,'hand.'+side)
        for index,t in enumerate([.38,.62,.86]):
            curve=bpy.data.curves.new(f'RONIN {side} closed finger {index+1}','CURVE')
            curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=.12;curve.bevel_resolution=2;curve.use_fill_caps=True
            spline=curve.splines.new('POLY');spline.points.add(16)
            for j,point in enumerate(spline.points):
                angle=math.radians(35+290*j/16)
                p=anchor+axis*t+(u*math.cos(angle)+v*math.sin(angle))*.27
                point.co=(*p,1)
            obj=bpy.data.objects.new(curve.name,curve);bpy.context.collection.objects.link(obj)
            bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
            bpy.ops.object.convert(target='MESH');uv_and_bind(bpy.context.object,'hand.'+side)
        # Cover the source cuff's boundary with a compact rigid wrist housing.
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.32,location=flip(Vector((-3.55,-.25,7.78))))
        uv_and_bind(bpy.context.object,'hand.'+side)
    return {'closed_fingers_per_hand':3,'hilt_axis':list(HANDLE_AXIS),'hilt_anchor':list(ANCHOR),
            'independent_weapon':True,'hand_geometry':'armored palms, thumbs, and curved mechanical fingers'}

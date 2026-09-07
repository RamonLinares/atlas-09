"""Closed mechanical fingers around Ronin's measured sword hilt."""
import bpy,math
from mathutils import Vector

def add_sword_fingers(bind,material):
    # Source glove and sword are fused. Preserve them instead of moving vertices
    # across their shared boundary. These finger arcs close the relaxed glove.
    anchor=Vector((-3.78,-.47,6.89));axis=Vector((.70,1.78,1.42)).normalized()
    u=Vector((-1,0,0));u=(u-axis*u.dot(axis)).normalized();v=axis.cross(u).normalized()
    for index,t in enumerate([.42,.66,.90]):
        curve=bpy.data.curves.new(f'RONIN closed grip finger {index+1}','CURVE')
        curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=.115;curve.bevel_resolution=2;curve.use_fill_caps=True
        spline=curve.splines.new('POLY');spline.points.add(16)
        for j,point in enumerate(spline.points):
            angle=math.radians(30+300*j/16)
            p=anchor+axis*t+(u*math.cos(angle)+v*math.sin(angle))*.28
            point.co=(*p,1)
        obj=bpy.data.objects.new(curve.name,curve);bpy.context.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.object.convert(target='MESH');obj=bpy.context.object
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.015,scale_to_bounds=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bind(obj,'hand.R',material)
    return {'closed_fingers':3,'hilt_axis':list(axis),'hilt_anchor':list(anchor),'source_geometry_preserved':True,'binding':'hand.R'}

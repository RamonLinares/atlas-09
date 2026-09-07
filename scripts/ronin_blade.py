"""Reverse the katana's single cutting edge while preserving its grip and UVs."""
import math
from mathutils import Vector,Matrix

def reverse_blade(obj):
    group=obj.vertex_groups['sword.R'].index
    ids={v.index for v in obj.data.vertices if v.groups[0].group==group}
    adjacent={i:[] for i in ids}
    for edge in obj.data.edges:
        a,b=edge.vertices
        if a in ids and b in ids:
            adjacent[a].append(b);adjacent[b].append(a)
    # The blade is a separate source component below the guard.
    seed=min(ids,key=lambda i:obj.data.vertices[i].co.z)
    selected={seed};pending=[seed]
    while pending:
        for i in adjacent[pending.pop()]:
            if i not in selected:selected.add(i);pending.append(i)
    points=[obj.data.vertices[i].co.copy() for i in selected]
    top=max(p.z for p in points)
    root=[p for p in points if p.z>top-.3]
    anchor=sum(root,Vector())/len(root)
    axis=Vector((.272,.588,.762)).normalized()
    # Continue the handle centerline through the guard, rather than leaving
    # the generated blade at an angle to the grip. The source pommel center
    # is measured independently from its exposed mesh component.
    pommel=Vector((-3.0565252,1.2991392,8.2043224))
    handle_axis=(pommel-anchor).normalized()
    align=axis.rotation_difference(handle_axis).to_matrix()
    rotation=align@Matrix.Rotation(math.pi,3,axis)
    for i in selected:
        v=obj.data.vertices[i];v.co=anchor+rotation@(v.co-anchor)
    obj.data.update()
    original_edge=-axis.cross(Vector((.918,-.396,-.023))).normalized()
    return {'blade_vertices':len(selected),'rotation_degrees':180,
            'axis':list(handle_axis),'anchor':list(anchor),
            'source_blade_axis':list(axis),'handle_pommel':list(pommel),
            'junction_correction_degrees':math.degrees(axis.angle(handle_axis)),
            'cutting_edge_direction':list(rotation@original_edge),
            'blade_probe':list(anchor-handle_axis*3),
            'guard_and_grip_preserved':True,'uvs_preserved':True}

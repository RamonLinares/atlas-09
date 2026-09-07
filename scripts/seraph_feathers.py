"""Split Seraph's five connected wing plates into independently hinged feathers."""
import bpy,math,heapq,json
from collections import defaultdict
from mathutils import Vector

def articulate_feathers(obj,rig):
    if rig.get('Feather articulation'):return json.loads(rig['Feather articulation'])
    old=obj.data;old.calc_loop_triangles()
    adjacency=defaultdict(set)
    for edge in old.edges:
        a,b=edge.vertices;adjacency[a].add(b);adjacency[b].add(a)
    labels={p.index:obj.vertex_groups[old.vertices[p.vertices[0]].groups[0].group].name for p in old.polygons}
    specs=[]
    for side,sign in [('L',1),('R',-1)]:
        group=obj.vertex_groups['wing_outer.'+side].index
        ids={v.index for v in old.vertices if any(g.group==group for g in v.groups)}
        hub=Vector((sign*3.08,2.5,14.85))
        radius=lambda i:math.hypot(old.vertices[i].co.x-hub.x,old.vertices[i].co.z-hub.z)
        remaining={i for i in ids if radius(i)>3.2};branches=[]
        while remaining:
            seed=remaining.pop();pending=[seed];part={seed}
            while pending:
                fresh=adjacency[pending.pop()]&remaining;remaining-=fresh;part|=fresh;pending.extend(fresh)
            if len(part)>20:branches.append(part)
        assert len(branches)==5,(side,[len(x) for x in branches])
        branches.sort(key=lambda ids:sum(math.atan2(old.vertices[i].co.z-hub.z,sign*(old.vertices[i].co.x-hub.x)) for i in ids)/len(ids),reverse=True)
        distances={};owners={};queue=[]
        for index,part in enumerate(branches):
            for i in part:distances[i]=0;owners[i]=index;heapq.heappush(queue,(0,i,index))
        while queue:
            dist,i,owner=heapq.heappop(queue)
            if dist!=distances[i]:continue
            for j in adjacency[i]&ids:
                d=dist+(old.vertices[i].co-old.vertices[j].co).length
                if d<distances.get(j,1e9):distances[j]=d;owners[j]=owner;heapq.heappush(queue,(d,j,owner))
        for p in old.polygons:
            if labels[p.index]!='wing_outer.'+side:continue
            center=p.center
            if math.hypot(center.x-hub.x,center.z-hub.z)<.72:continue
            counts=defaultdict(int)
            for i in p.vertices:counts[owners[i]]+=1
            index=max(counts,key=lambda k:(counts[k],-sum(distances[i] for i in p.vertices if owners[i]==k)))
            labels[p.index]=f'feather_{index+1:02}.{side}'
        for index,branch in enumerate(branches):
            name=f'feather_{index+1:02}.{side}'
            tip_ids=sorted(branch,key=radius,reverse=True)[:6]
            tip=sum((old.vertices[i].co for i in tip_ids),Vector())/len(tip_ids)
            hinge=hub+Vector((sign*(4-index)*.5,0,0))
            direction=tip-hinge;angle=math.atan2(direction.z,sign*direction.x)
            specs.append({'name':name,'parent':'wing_outer.'+side,'side':side,'index':index,'head':list(hinge),'hub':list(hub),'tail':list(tip),'spread_angle_rad':angle})
    vertices=[];faces=[];mapping={};weights=defaultdict(list);original=[]
    for p in old.polygons:
        name=labels[p.index];face=[]
        for vi in p.vertices:
            key=(vi,name)
            if key not in mapping:
                mapping[key]=len(vertices);vertices.append(tuple(old.vertices[vi].co));original.append(vi);weights[name].append(mapping[key])
            face.append(mapping[key])
        faces.append(face)
    mesh=bpy.data.meshes.new('SERAPH_FeatherArmor');mesh.from_pydata(vertices,[],faces);mesh.update()
    for material in old.materials:mesh.materials.append(material)
    for src,dst in zip(old.polygons,mesh.polygons):dst.material_index=src.material_index;dst.use_smooth=src.use_smooth
    for layer in old.uv_layers:
        uv=mesh.uv_layers.new(name=layer.name)
        for src,dst in zip(layer.data,uv.data):dst.uv=src.uv
    obj.data=mesh
    obj.vertex_groups.clear()
    for name,ids in weights.items():obj.vertex_groups.new(name=name).add(ids,1,'REPLACE')
    attribute=mesh.attributes.new('original_vertex','INT','POINT')
    for item,index in zip(attribute.data,original):item.value=index
    bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    for item in specs:
        bone=rig.data.edit_bones.new(item['name']);bone.head=item['head'];bone.tail=item['tail'];bone.parent=rig.data.edit_bones[item['parent']]
    bpy.ops.object.mode_set(mode='OBJECT')
    for item in specs:rig.pose.bones[item['name']].rotation_mode='XYZ'
    rig['Feather articulation']=json.dumps(specs)
    return specs

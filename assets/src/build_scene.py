"""Headless Blender assembly, UV atlas, LOD chain and inventory studio."""
import json
import math
import subprocess
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"tools")]
from materials import SURFACES
from render_preview import render


def select(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]


def clean(mesh):
    bm=bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.dissolve_degenerate(bm,dist=1e-9,edges=list(bm.edges))
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def budget(obj,lower,upper):
    select([obj])
    while len(obj.data.polygons)<lower:
        mod=obj.modifiers.new("Split detail","SUBSURF")
        mod.subdivision_type="SIMPLE"
        mod.levels=1
        bpy.ops.object.modifier_apply(modifier=mod.name)
        clean(obj.data)
    if len(obj.data.polygons)>upper:
        mod=obj.modifiers.new("Silhouette reduction","DECIMATE")
        mod.ratio=upper/len(obj.data.polygons)
        mod.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        clean(obj.data)


def axis(spec):
    return Vector(tuple((1 if spec[0]!="-" else -1) if c==spec[-1] else 0 for c in "XYZ"))


def object_from_parts(name,parts,entry,cfg):
    vs=[]; faces=[]; mids=[]
    keys=list(SURFACES)
    for coords,polygons,mat in parts:
        offset=len(vs)
        vs.extend(coords)
        faces.extend([tuple(i+offset for i in p) for p in polygons])
        mids.extend([keys.index(mat)]*len(polygons))
    verts=np.array(vs,dtype=float)
    category=entry["category"]
    group=category if category in ("trade_goods","shields") else "weapons"
    origin=cfg["origins"][group]
    low,high=verts.min(axis=0),verts.max(axis=0)
    if origin=="base_center":
        verts-= [(low[0]+high[0])/2,(low[1]+high[1])/2,low[2]]
    elif origin=="bounds_center":
        verts-=(low+high)/2
    elif origin!="grip_center":
        raise ValueError(f"Unknown origin {origin}")
    orient=cfg["orientation"]
    z=axis(orient["weapon_tip"] if group=="weapons" else orient["up"])
    x=axis(orient["single_edge"]) if group=="weapons" else (-axis(orient["shield_face"])).cross(z)
    basis=Matrix([x,z.cross(x),z]).transposed()
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(),[],faces)
    mesh.transform(basis.to_4x4())
    for key in keys:
        mesh.materials.append(bpy.data.materials.get(key) or bpy.data.materials.new(key))
    mesh.polygons.foreach_set("material_index",mids)
    mesh.validate()
    clean(mesh)
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def unwrap(objs,ratios,cfg):
    """Atlas every exported surface together, with less texture area on distant LODs."""
    select(objs)
    settings=bpy.context.scene.tool_settings
    settings.use_uv_select_sync=True
    settings.mesh_select_mode=(False,False,True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    margin=cfg["texture"]["uv_padding_at_1024"]/1024
    bpy.ops.uv.smart_project(angle_limit=math.radians(50),island_margin=margin,
                             margin_method="FRACTION",area_weight=.25)
    bpy.ops.object.mode_set(mode="OBJECT")
    for obj in objs:
        scale=math.sqrt(ratios[obj.name])
        if scale!=1:
            for corner in obj.data.uv_layers.active.data:
                corner.uv*=scale
    # Smart projection can fold concave surfaces within one island. Separate
    # the affected triangles and repack the whole atlas at its final gutter.
    for attempt in range(3):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.pack_islands(shape_method="AABB",margin_method="FRACTION",margin=margin)
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.uv.select_overlap(extend=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        overlap=[(obj,face) for obj in objs for face in obj.data.polygons if face.select]
        if not overlap:
            return
        for index,(obj,face) in enumerate(overlap):
            offset=Vector((2+2*(index%32),2+2*(index//32)))
            layer=obj.data.uv_layers.active.data
            for loop in face.loop_indices:
                layer[loop].uv+=offset
    raise ValueError("Overlapping UVs after atlas repair")


def bake_input(objects,size,path):
    # Sample nearby self-occlusion per vertex on each independent display object.
    xyz=[]; uvs=[]; ao=[]; mids=[]
    for obj in objects:
        mesh=obj.data
        tree=BVHTree.FromPolygons([v.co for v in mesh.vertices],[p.vertices[:] for p in mesh.polygons],all_triangles=True)
        radius=max(obj.dimensions)*.075
        occ=[]
        for vert in mesh.vertices:
            n=vert.normal.normalized()
            side=n.orthogonal().normalized()
            other=n.cross(side)
            start=vert.co+n*max(.00003,radius*.001)
            hits=0
            for i in range(6):
                angle=i*2.39996
                v=(n*.70+side*math.cos(angle)+other*math.sin(angle)).normalized()
                hit=tree.ray_cast(start,v,radius)[3]
                if hit is not None:
                    hits+=1-hit/radius
            occ.append(1-.49*hits/6)
        layer=mesh.uv_layers.active.data
        for p in mesh.polygons:
            xyz.append([tuple(mesh.vertices[i].co) for i in p.vertices])
            uvs.append([tuple(layer[i].uv) for i in p.loop_indices])
            ao.append([occ[i] for i in p.vertices])
            mids.append(p.material_index)
    np.savez(path,xyz=np.float32(xyz),uvs=np.float32(uvs),ao=np.float32(ao),material=mids,keys=list(SURFACES),size=size)


def material(ident,directory,cfg):
    mat=bpy.data.materials.new(ident+"_surface")
    mat.use_nodes=True
    nodes=mat.node_tree.nodes; links=mat.node_tree.links
    shader=nodes.get("Principled BSDF")
    def tex(filename,space,position):
        node=nodes.new("ShaderNodeTexImage")
        node.image=bpy.data.images.load(str(directory/filename))
        node.image.colorspace_settings.name=space
        node.image.filepath="//"+filename
        node.location=position
        return node
    base=tex(ident+"_d.png",cfg["diffuse_space"],(-620,300))
    norm=tex("src_maps/normal.png" if cfg["normal_green_flip"] else ident+"_n.png",cfg["data_space"],(-620,-340))
    n=nodes.new("ShaderNodeNormalMap"); n.location=(-210,-330)
    links.new(norm.outputs["Color"],n.inputs["Color"]); links.new(n.outputs[0],shader.inputs["Normal"])
    packed=tex(ident+"_s.png",cfg["data_space"],(-620,0))
    sep=nodes.new("ShaderNodeSeparateColor"); sep.location=(-390,0)
    links.new(packed.outputs["Color"],sep.inputs[0])
    mix=nodes.new("ShaderNodeMixRGB"); mix.blend_type="MULTIPLY"; mix.inputs[0].default_value=.45; mix.location=(-30,260)
    links.new(base.outputs["Color"],mix.inputs[1]); links.new(mix.outputs[0],shader.inputs["Base Color"])
    for i,channel in enumerate(cfg["packing"]):
        val=sep.outputs[i]
        if channel.startswith("1-"):
            inv=nodes.new("ShaderNodeMath"); inv.operation="SUBTRACT"; inv.inputs[0].default_value=1
            links.new(val,inv.inputs[1]); val=inv.outputs[0]
        links.new(val,{"metallic":shader.inputs["Metallic"],"roughness":shader.inputs["Roughness"],"ao":mix.inputs[2]}[channel.removeprefix("1-")])
    nodes.active=base
    return mat


def metrics(obj):
    mesh=obj.data
    uv=mesh.uv_layers.active
    co=np.asarray([tuple(v.co) for v in mesh.vertices])
    xy=np.asarray([tuple(v.uv) for v in uv.data])
    used=set(k for p in mesh.polygons for k in p.vertices)
    return dict(tris=len(mesh.polygons),bbox_m=[co.min(axis=0).tolist(),co.max(axis=0).tolist()],
                dimensions_m=np.ptp(co,axis=0).tolist(),uv_bounds=[float(xy.min()),float(xy.max())],
                uv_sets=len(mesh.uv_layers),materials=len(mesh.materials),loose_vertices=len(co)-len(used),
                non_triangles=sum(len(p.vertices)!=3 for p in mesh.polygons),
                degenerate_faces=sum(p.area<=1e-14 for p in mesh.polygons),
                applied_transforms=obj.matrix_basis==Matrix.Identity(4))


def build(ident,python,dest,work):
    cfg=json.loads((ROOT/"conventions.json").read_text(encoding="utf-8-sig"))
    entry=next(e for e in json.loads((ROOT/"manifest.json").read_text(encoding="utf-8-sig"))["assets"] if e["id"]==ident)
    from importlib import import_module
    pieces=import_module({"trade_goods":"trade_goods","shields":"shields"}.get(entry["category"],"weapons")).generate(entry)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.world=bpy.data.worlds.new("Neutral studio")
    scene.unit_settings.system=cfg["units"]["system"]
    scene.unit_settings.scale_length=cfg["units"]["meters_per_unit"]
    scene["category"]=entry["category"]
    objs=[]; kinds={}
    for suffix,parts in pieces.items():
        obj=object_from_parts(ident+suffix,parts,entry,cfg)
        kind=suffix.lstrip("_") or entry["type"]
        lo,hi=cfg["limits"][kind]["triangles"]
        budget(obj,lo,hi-2)
        objs.append(obj); kinds[obj.name]=kind
    all_objs=[]; ratios={}
    for obj in objs:
        obj.name+=cfg["lods"][0]["suffix"]
        all_objs.append(obj); ratios[obj.name]=cfg["lods"][0]["ratio"]
        for level in cfg["lods"][1:]:
            lod=obj.copy(); lod.data=obj.data.copy()
            lod.name=obj.name+level["suffix"]
            scene.collection.objects.link(lod)
            budget(lod,0,max(4,int(len(obj.data.polygons)*level["ratio"])))
            all_objs.append(lod); ratios[lod.name]=level["ratio"]
    size=cfg["texture"]["rigid_size"]
    unwrap(all_objs,ratios,cfg)
    bake_input(all_objs,size,work/"atlas.npz")
    subprocess.run([python,str(ROOT/"src"/"bake_maps.py"),str(work/"atlas.npz"),str(dest)],check=True)
    mat=material(ident,dest,cfg["texture"])
    stats={}
    for obj in all_objs:
        obj.data.materials.clear(); obj.data.materials.append(mat)
        for p in obj.data.polygons:
            p.material_index=0
            p.use_smooth=True
        obj.data.set_sharp_from_angle(angle=math.radians(43))
        stats[obj.name]=metrics(obj)
    select(all_objs)
    options=dict(cfg["fbx"]); options.pop("version")
    options["object_types"]=set(options["object_types"])
    # FBX supports direct image channels. Restore the game's packed shader for the source scene.
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    shader=nodes.get("Principled BSDF")
    images=[node for node in nodes if node.type=="TEX_IMAGE"]
    paths={node.image:node.image.filepath for node in images}
    for image,rel in paths.items():
        image.filepath=str(dest/rel.removeprefix("//"))
    diffuse=next(node for node in images if node.image.filepath.endswith("_d.png"))
    original=shader.inputs["Base Color"].links[0].from_socket
    links.new(diffuse.outputs["Color"],shader.inputs["Base Color"])
    bpy.ops.export_scene.fbx(filepath=str(dest/(ident+".fbx")),use_selection=True,**options)
    links.new(original,shader.inputs["Base Color"])
    for image,rel in paths.items():
        image.filepath=rel
    for ob in all_objs:
        if ob not in objs:
            ob.hide_set(True); ob.hide_render=True
    select(objs)
    for area in bpy.context.screen.areas:
        if area.type=="VIEW_3D":
            space=area.spaces.active
            space.region_3d.view_distance=max(max(o.dimensions) for o in objs)*1.8
            space.region_3d.view_location=sum((Vector(o.bound_box[0])+Vector(o.bound_box[6]) for o in objs),Vector())/(2*len(objs))
            space.shading.color_type="TEXTURE"
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(dest/(ident+".blend")),relative_remap=False,compress=True)
    render(objs,dest/"preview.png",entry["category"])
    (work/"metrics.json").write_text(json.dumps({"objects":stats,"parts":kinds}),encoding="utf8")


if __name__=="__main__":
    ident,python,dest,work=sys.argv[sys.argv.index("--")+1:]
    build(ident,python,Path(dest),Path(work))


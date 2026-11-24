"""Blender camera and studio for the inventory previews.

Standalone: blender -b item.blend --python render_preview.py -- preview.png
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def render(objects, path, category):
    scene = bpy.context.scene
    weapons = category not in ("trade_goods","shields")
    direction = Vector((.24,-1,.23) if weapons else ((.37,-1,.19) if category=="shields" else (.82,-1,.63))).normalized()
    # Companions share the grip origin in the source. Arrange only for photography.
    shifts = []
    for obj in objects[1:]:
        shifts.append((obj,obj.location.copy()))
        obj.location.x += .24 if "sheath" in obj.name else .28
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ Vector(v) for obj in objects for v in obj.bound_box]
    centre = sum(points,Vector())/len(points)
    camdata = bpy.data.cameras.new("Inventory three-quarter")
    cam = bpy.data.objects.new(camdata.name,camdata)
    scene.collection.objects.link(cam)
    cam.rotation_euler = (-direction).to_track_quat("-Z","Y").to_euler()
    if weapons:
        cam.rotation_euler.rotate_axis("Z",math.radians(-32))
    rot = cam.rotation_euler.to_matrix()
    local = [rot.transposed() @ (p-centre) for p in points]
    low = Vector([min(p[i] for p in local) for i in range(3)])
    high = Vector([max(p[i] for p in local) for i in range(3)])
    centre += rot @ ((low+high)*.5)
    span = max(high.x-low.x,high.y-low.y,.05)
    cam.location = centre + direction*(span*3)
    camdata.type = "ORTHO"
    camdata.ortho_scale = span*1.13
    camdata.clip_start = .001
    scene.camera = cam
    def softbox(name, vector, energy, size, color):
        light = bpy.data.lights.new(name,"AREA")
        light.energy = energy*span*span
        light.shape = "DISK"
        light.size = size*span
        light.color=color
        ob = bpy.data.objects.new(name,light)
        scene.collection.objects.link(ob)
        ob.location = centre + Vector(vector)*span
        ob.rotation_euler = (centre-ob.location).to_track_quat("-Z","Y").to_euler()
    softbox("Large window",(-1.3,-1.65,1.8),90,1.7,(1,.91,.80))
    softbox("Soft fill",(1.5,-1,.58),62,1.4,(.78,.88,1))
    softbox("Rim",(.42,1.1,1.25),125,1.05,(1,.95,.84))
    scene.world.use_nodes=True
    world=scene.world.node_tree
    bg=world.nodes.get("Background")
    bg.inputs[0].default_value=(.45,.45,.45,1)
    bg.inputs[1].default_value=.7
    pathray=world.nodes.new("ShaderNodeLightPath")
    color=world.nodes.new("ShaderNodeMixRGB")
    color.inputs[1].default_value=(.55,.55,.55,1)
    color.inputs[2].default_value=(.145,.145,.145,1)
    world.links.new(pathray.outputs["Is Camera Ray"],color.inputs[0])
    world.links.new(color.outputs[0],bg.inputs[0])
    scene.render.engine="CYCLES"
    scene.cycles.samples=8
    scene.cycles.use_denoising=True
    scene.cycles.max_bounces=3
    prefs=bpy.context.preferences.addons["cycles"].preferences
    for backend in ("OPTIX","CUDA","HIP","METAL","ONEAPI"):
        try:
            prefs.compute_device_type=backend
            prefs.refresh_devices()
            gpu=[d for d in prefs.devices if d.type==backend]
            if gpu:
                for device in prefs.devices:
                    device.use=device in gpu
                scene.cycles.device="GPU"
                break
        except (TypeError,RuntimeError):
            continue
    scene.render.resolution_x=scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGB"
    scene.render.filepath=str(Path(path).resolve())
    bpy.ops.render.render(write_still=True)
    for obj,loc in shifts:
        obj.location=loc


if __name__=="__main__":
    path=sys.argv[sys.argv.index("--")+1]
    objs=[o for o in bpy.context.scene.objects if o.type=="MESH" and not o.hide_render]
    render(objs,path,bpy.context.scene["category"])

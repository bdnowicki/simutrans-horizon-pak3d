# Renders pak 3D models with Cycles on the CPU (no GPU needed, works in the blender-headless container), to look at
# a model without the game:
#   blender -b --factory-startup -P scripts/preview.py -- --out previews/esb.png --model models/empire_state.glb
#       [--model models/x.glb@dx,dy,turn_degrees ...] [--azimuth 225] [--elevation 30] [--ortho] [--night]
#       [--target x,y,z] [--distance d] [--size 900x900] [--samples 48]
# glTF axes (+Y up) come back as Blender's (+Z up); a ground plane of squares sits at z = 0.
# Author: bdnowicki. License: CC BY 4.0.
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--model", action="append", required=True, help="path[@dx,dy,turn] (squares, degrees about Z)")
ap.add_argument("--azimuth", type=float, default=225.0, help="camera direction, degrees from +X towards +Y (225 = from south-west)")
ap.add_argument("--elevation", type=float, default=30.0)
ap.add_argument("--ortho", action="store_true")
ap.add_argument("--night", action="store_true")
ap.add_argument("--target", default=None)
ap.add_argument("--distance", type=float, default=None)
ap.add_argument("--lens", type=float, default=50.0)
ap.add_argument("--size", default="900x900")
ap.add_argument("--samples", type=int, default=48)
ap.add_argument("--player1", default=None, help="r,g,b company colour for the material player1 (and player2 with --player2)")
ap.add_argument("--player2", default=None)
a = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
objs = []
for spec in a.model:
    path, _, place = spec.partition("@")
    dx, dy, turn = (float(v) for v in place.split(",")) if place else (0.0, 0.0, 0.0)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    for ob in set(bpy.data.objects) - before:
        if ob.parent is None:
            ob.rotation_euler.z += math.radians(turn)
            ob.location.x += dx
            ob.location.y += dy
        objs.append(ob)
bpy.context.view_layer.update()
# as in the dashboard: night lights off by day, company colours on player1/player2
for mat in bpy.data.materials:
    p = mat.node_tree.nodes.get("Principled BSDF") if mat.use_nodes else None
    if not p:
        continue
    if mat.name.startswith("night_emissive") and not a.night:
        p.inputs["Emission Strength"].default_value = 0.0
    for key, value in (("player1", a.player1), ("player2", a.player2)):
        if value and mat.name.startswith(key):
            p.inputs["Base Color"].default_value = (*[float(v) for v in value.split(",")], 1.0)
lo = Vector((1e9, 1e9, 1e9))
hi = -lo
for ob in objs:
    if ob.type == "MESH":
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
center = (lo + hi) / 2 if a.target is None else Vector(float(v) for v in a.target.split(","))
radius = (hi - lo).length / 2

# ground of squares
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.001))
ground = bpy.context.object
gm = bpy.data.materials.new("ground")
gm.use_nodes = True
nt = gm.node_tree
bsdf = nt.nodes["Principled BSDF"]
chk = nt.nodes.new("ShaderNodeTexChecker")
chk.inputs["Scale"].default_value = 40.0
chk.inputs["Color1"].default_value = (0.30, 0.32, 0.27, 1)
chk.inputs["Color2"].default_value = (0.27, 0.29, 0.24, 1)
nt.links.new(chk.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.95
ground.data.materials.append(gm)

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1) if a.night else (0.55, 0.65, 0.8, 1)
bg.inputs["Strength"].default_value = 0.6 if a.night else 0.9
sun = bpy.data.lights.new("sun", "SUN")
sun.energy = 0.05 if a.night else 3.2
sun.angle = math.radians(2)
so = bpy.data.objects.new("sun", sun)
so.rotation_euler = (math.radians(50), 0, math.radians(150))
scene.collection.objects.link(so)

cam = bpy.data.cameras.new("cam")
cam.lens = a.lens
co = bpy.data.objects.new("cam", cam)
scene.collection.objects.link(co)
scene.camera = co
az, el = math.radians(a.azimuth), math.radians(a.elevation)
d = a.distance or radius * (3.2 if not a.ortho else 4.0)
direction = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
co.location = center + direction * d
co.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
if a.ortho:
    cam.type = "ORTHO"
    cam.ortho_scale = radius * 2.3
cam.clip_end = 1000

w, h = (int(v) for v in a.size.split("x"))
scene.render.resolution_x, scene.render.resolution_y = w, h
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = a.samples
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
scene.render.filepath = os.path.abspath(a.out)
os.makedirs(os.path.dirname(scene.render.filepath), exist_ok=True)
bpy.ops.render.render(write_still=True)
print("PREVIEW", a.out)

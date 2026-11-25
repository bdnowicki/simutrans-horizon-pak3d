# Shared helpers of the model scripts: command line, an empty scene, a small mesh builder with explicit UVs and
# normals, PBR materials with generated textures, and the glTF export with the conventions of the pak 3D
# (Blender Z up -> glTF Y up, 1 unit = 1 square, building front -Y, vehicle front +X).
# Runs inside Blender (bpy, numpy). Author: bdnowicki. License: CC BY 4.0.
import argparse
import math
import os
import sys
import tempfile

import bpy
import numpy as np


def parse_args(extra=None):
    """arguments after "--": --out PATH [--lod N] plus the script's own (extra(parser))"""
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="the .glb to write")
    ap.add_argument("--lod", type=int, default=0, help="0 = full model, 1 = coarse model (at most a quarter of the triangles)")
    if extra:
        extra(ap)
    return ap.parse_args(argv)


def empty_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.objects):
        for block in list(coll):
            coll.remove(block)


# ---------------------------------------------------------------------------------------------------------------- mesh

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    length = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
    return (a[0] / length, a[1] / length, a[2] / length) if length > 1e-12 else (0.0, 0.0, 1.0)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


class Mesh:
    """Faces with their own corners (no shared vertices: the exporter welds equal ones), a material slot, UVs
    and normals per corner. Positions are given in model units and multiplied by `scale` when built, UVs are
    computed before scaling (textures can be laid out in metres)."""

    def __init__(self, name, scale=1.0):
        self.name, self.scale = name, scale
        self.faces = []  # (points, uvs, normals, material)
        self.materials = []

    def slot(self, mat):
        if mat not in self.materials:
            self.materials.append(mat)
        return self.materials.index(mat)

    def face(self, pts, mat, uvs=None, normals=None):
        if len(pts) < 3:
            return
        if uvs is None:
            uvs = auto_uv(pts, mat)
        if normals is None:
            n = face_normal(pts)
            normals = [n] * len(pts)
        self.faces.append((list(pts), list(uvs), list(normals), self.slot(mat)))

    def triangles(self):
        return sum(len(f[0]) - 2 for f in self.faces)

    def build(self, collection=None):
        verts, polys, loops_uv, loops_n, mats = [], [], [], [], []
        s = self.scale
        for pts, uvs, normals, m in self.faces:
            start = len(verts)
            verts.extend((p[0] * s, p[1] * s, p[2] * s) for p in pts)
            polys.append(tuple(range(start, start + len(pts))))
            loops_uv.extend(uvs)
            loops_n.extend(normals)
            mats.append(m)
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(verts, [], polys)
        for mat in self.materials:
            me.materials.append(mat.blender())
        me.polygons.foreach_set("material_index", mats)
        uv = me.uv_layers.new(name="UVMap")
        uv.data.foreach_set("uv", [c for t in loops_uv for c in t])
        me.polygons.foreach_set("use_smooth", [True] * len(polys))
        me.update()
        me.normals_split_custom_set([tuple(n) for n in loops_n])
        ob = bpy.data.objects.new(self.name, me)
        (collection or bpy.context.scene.collection).objects.link(ob)
        return ob

    # -------------------------------------------------------------------------------------------- primitives

    def quad(self, a, b, c, d, mat, uvs=None, normals=None):
        self.face([a, b, c, d], mat, uvs, normals)

    def box(self, x0, x1, y0, y1, z0, z1, mat, skip=(), mats=None):
        """axis-aligned box; skip = sides left out ('-x','+x','-y','+y','-z','+z'); mats = {side: material}"""
        mats = mats or {}
        sides = {
            "-x": [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
            "+x": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
            "-y": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            "+y": [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
            "-z": [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
            "+z": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        }
        for k, pts in sides.items():
            if k not in skip:
                self.face(pts, mats.get(k, mat))

    def prism(self, poly, z0, z1, side, top=None, bottom=None, u_origin="edge"):
        """vertical prism over a counter-clockwise polygon [(x, y)]; side faces get facade UVs (u from the start of
        each edge, v = height), top/bottom caps planar UVs; a None material leaves that part out"""
        n = len(poly)
        for i in range(n):
            (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
            if side is not None:
                pts = [(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)]
                self.face(pts, side, facade_uv(pts, side, (ax, ay)))
        if top is not None:
            self.face([(x, y, z1) for x, y in poly], top)
        if bottom is not None:
            self.face([(x, y, z0) for x, y in reversed(poly)], bottom)

    def extrude_x(self, profile, x0, x1, mats, smooth=None, u_len=None):
        """a closed or open profile [(y, z)] in the plane x = const swept from x0 to x1; mats[i] is the material of
        the edge i -> i+1 (None = left out); smooth[i] True gives vertex i the averaged normal of its two edges"""
        n = len(profile)
        closed = len(mats) == n
        edges = n if closed else n - 1
        en = []
        for i in range(edges):
            (ay, az), (by, bz) = profile[i], profile[(i + 1) % n]
            en.append(_norm((0.0, bz - az, -(by - ay))))

        def vnorm(i, e):
            if smooth and smooth[i % n]:
                prev = en[(i - 1) % edges] if (closed or i > 0) else en[0]
                nxt = en[i % edges] if (closed or i < edges) else en[-1]
                return _norm(tuple(p + q for p, q in zip(prev, nxt)))
            return en[e]
        acc = 0.0
        for i in range(edges):
            (ay, az), (by, bz) = profile[i], profile[(i + 1) % n]
            seg = math.hypot(by - ay, bz - az)
            m = mats[i]
            if m is not None:
                # outward for a profile running counter-clockwise seen from +x
                pts = [(x0, ay, az), (x0, by, bz), (x1, by, bz), (x1, ay, az)]
                na, nb = vnorm(i, i), vnorm(i + 1, i)
                su, sv = m.uv_size
                uvs = [(x0 / su, acc / sv), (x0 / su, (acc + seg) / sv), (x1 / su, (acc + seg) / sv), (x1 / su, acc / sv)]
                self.face(pts, m, uvs, [na, nb, nb, na])
            acc += seg

    def cylinder(self, c, r, h, segs, mat, axis="z", caps=(True, True), r2=None, phase=0.0):
        """a (truncated) cylinder from c along +axis by h, radius r at the start and r2 at the end"""
        r2 = r if r2 is None else r2
        ring = [(math.cos(phase + 2 * math.pi * k / segs), math.sin(phase + 2 * math.pi * k / segs)) for k in range(segs)]

        def at(u, v, t, rad):
            if axis == "z":
                return (c[0] + u * rad, c[1] + v * rad, c[2] + t)
            if axis == "x":
                return (c[0] + t, c[1] + u * rad, c[2] + v * rad)
            return (c[0] + v * rad, c[1] + t, c[2] + u * rad)
        slope = (r - r2) / h if h else 0.0
        for k in range(segs):
            (u0, v0), (u1, v1) = ring[k], ring[(k + 1) % segs]
            pts = [at(u0, v0, 0, r), at(u1, v1, 0, r), at(u1, v1, h, r2), at(u0, v0, h, r2)]
            n0 = _norm(_radial(axis, u0, v0, slope))
            n1 = _norm(_radial(axis, u1, v1, slope))
            self.face(pts, mat, None, [n0, n1, n1, n0])
        if caps[0]:
            self.face([at(u, v, 0, r) for u, v in reversed(ring)], mat)
        if caps[1] and r2 > 0:
            self.face([at(u, v, h, r2) for u, v in ring], mat)


def _radial(axis, u, v, slope):
    if axis == "z":
        return (u, v, slope)
    if axis == "x":
        return (slope, u, v)
    return (v, slope, u)


def face_normal(pts):
    n = (0.0, 0.0, 0.0)
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        n = (n[0] + (a[1] - b[1]) * (a[2] + b[2]), n[1] + (a[2] - b[2]) * (a[0] + b[0]), n[2] + (a[0] - b[0]) * (a[1] + b[1]))
    return _norm(n)


def auto_uv(pts, mat):
    """box mapping in model units by the face normal, scaled by the material's uv_size"""
    n = face_normal(pts)
    su, sv = mat.uv_size
    ax = max(range(3), key=lambda k: abs(n[k]))
    if ax == 2:
        return [(p[0] / su, p[1] / sv) for p in pts]
    if ax == 0:
        return [(p[1] / su, p[2] / sv) for p in pts]
    return [(p[0] / su, p[2] / sv) for p in pts]


def facade_uv(pts, mat, origin):
    """vertical face: u = distance along the bottom edge from origin, v = height (both in model units / uv_size)"""
    su, sv = mat.uv_size
    d = _norm(_sub(pts[1], pts[0]))
    o = (origin[0], origin[1], 0.0)
    return [(_dot(_sub((p[0], p[1], 0.0), o), d) / su + mat.uv_offset[0], p[2] / sv + mat.uv_offset[1]) for p in pts]


def rect_notched(hx, hy, notch):
    """counter-clockwise outline of a rectangle (half sizes hx, hy) with square notches cut out of the corners"""
    if notch <= 0:
        return [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    a, b = hx - notch, hy - notch
    return [(-a, -hy), (a, -hy), (a, -b), (hx, -b), (hx, b), (a, b), (a, hy), (-a, hy), (-a, b), (-hx, b), (-hx, -b), (-a, -b)]


def offset_poly(poly, d):
    """outline moved outwards by d (miter joins; for the rectilinear outlines above)"""
    n = len(poly)
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        e1 = _norm((p1[0] - p0[0], p1[1] - p0[1], 0.0))
        e2 = _norm((p2[0] - p1[0], p2[1] - p1[1], 0.0))
        n1, n2 = (e1[1], -e1[0]), (e2[1], -e2[0])
        bis = (n1[0] + n2[0], n1[1] + n2[1])
        bl = bis[0] * n1[0] + bis[1] * n1[1]
        out.append((p1[0] + bis[0] * d / bl, p1[1] + bis[1] * d / bl))
    return out


# ------------------------------------------------------------------------------------------------------- materials

class Material:
    """a glTF metallic-roughness material; textures are numpy arrays (rows top to bottom, RGB or RGBA, 0..1)"""

    def __init__(self, name, color=(0.8, 0.8, 0.8), roughness=0.7, metallic=0.0, uv_size=(1.0, 1.0), uv_offset=(0.0, 0.0),
                 base_tex=None, normal_tex=None, orm_tex=None, emissive_tex=None, emissive=(0.0, 0.0, 0.0), normal_strength=1.0,
                 tex_format="PNG"):
        assert metallic <= 0.3, "the dashboard has no environment map: keep metallic <= 0.3"
        self.name, self.color, self.roughness, self.metallic = name, color, roughness, metallic
        self.uv_size, self.uv_offset = uv_size, uv_offset
        self.base_tex, self.normal_tex, self.orm_tex, self.emissive_tex = base_tex, normal_tex, orm_tex, emissive_tex
        self.emissive, self.normal_strength, self.tex_format = emissive, normal_strength, tex_format
        self._bl = None

    def blender(self):
        if self._bl:
            return self._bl
        mat = bpy.data.materials.new(self.name)
        mat.use_nodes = True
        mat.use_backface_culling = True  # exported as doubleSided false
        nt = mat.node_tree
        for nd in list(nt.nodes):
            nt.nodes.remove(nd)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        bsdf.inputs["Base Color"].default_value = (*self.color, 1.0)
        bsdf.inputs["Roughness"].default_value = self.roughness
        bsdf.inputs["Metallic"].default_value = self.metallic
        if self.base_tex is not None:
            t = image_node(nt, image(self.name + "_color", self.base_tex, srgb=True, fmt=self.tex_format))
            nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
        if self.orm_tex is not None:
            t = image_node(nt, image(self.name + "_orm", self.orm_tex, srgb=False))
            sep = nt.nodes.new("ShaderNodeSeparateColor")
            nt.links.new(t.outputs["Color"], sep.inputs["Color"])
            nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
            nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
        if self.normal_tex is not None:
            t = image_node(nt, image(self.name + "_normal", self.normal_tex, srgb=False))
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nm.inputs["Strength"].default_value = self.normal_strength
            nt.links.new(t.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        if self.emissive_tex is not None:
            t = image_node(nt, image(self.name + "_emissive", self.emissive_tex, srgb=True))
            nt.links.new(t.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = 1.0
        elif any(self.emissive):
            bsdf.inputs["Emission Color"].default_value = (*self.emissive, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 1.0
        self._bl = mat
        return mat


_tmpdir = tempfile.mkdtemp(prefix="pak3d_")


def image(name, arr, srgb=True, fmt="PNG"):
    """a numpy image (rows top to bottom) as a file-backed Blender image, so the exporter embeds the file as it is"""
    arr = np.asarray(arr, dtype=np.float32)
    h, w = arr.shape[:2]
    if arr.shape[2] == 3:
        arr = np.concatenate([arr, np.ones((h, w, 1), np.float32)], axis=2)
    img = bpy.data.images.new(name, width=w, height=h, alpha=False, float_buffer=False)
    if not srgb:
        img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(np.ascontiguousarray(np.clip(arr[::-1], 0, 1)).ravel())
    ext = "jpg" if fmt == "JPEG" else "png"
    path = os.path.join(_tmpdir, "%s.%s" % (name, ext))
    img.filepath_raw = path
    img.file_format = fmt
    if fmt == "JPEG":
        try:
            img.save(filepath=path, quality=90)
        except TypeError:
            bpy.context.scene.render.image_settings.file_format = "JPEG"
            bpy.context.scene.render.image_settings.quality = 90
            img.save_render(path)
    else:
        img.save(filepath=path)
    img.filepath = path
    img.reload()
    if not srgb:
        img.colorspace_settings.name = "Non-Color"
    return img


def image_node(nt, img):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    t.extension = "REPEAT"
    t.interpolation = "Linear"
    return t


def normal_from_height(hgt, strength=2.0):
    """tangent space normal map (OpenGL convention, as glTF) from a height field (rows top to bottom), tileable"""
    dx = (np.roll(hgt, -1, axis=1) - np.roll(hgt, 1, axis=1)) * 0.5 * strength
    dy = (np.roll(hgt, 1, axis=0) - np.roll(hgt, -1, axis=0)) * 0.5 * strength  # +v points up the image
    nz = np.ones_like(hgt)
    length = np.sqrt(dx * dx + dy * dy + nz * nz)
    n = np.stack([-dx / length, -dy / length, nz / length], axis=2)
    return n * 0.5 + 0.5


def downsample(arr, f):
    """box filter by an integer factor"""
    h, w = arr.shape[:2]
    return arr.reshape(h // f, f, w // f, f, -1).mean(axis=(1, 3))


def value_noise(h, w, cells, rng, octaves=3):
    """tileable smooth noise 0..1"""
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cy, cx = cells[0] * 2 ** o, cells[1] * 2 ** o
        g = rng.random((cy, cx)).astype(np.float32)
        ys = np.linspace(0, cy, h, endpoint=False)
        xs = np.linspace(0, cx, w, endpoint=False)
        y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int)
        fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        y1, x1 = (y0 + 1) % cy, (x0 + 1) % cx
        a = g[y0][:, x0] * (1 - fx) + g[y0][:, x1] * fx
        b = g[y1][:, x0] * (1 - fx) + g[y1][:, x1] * fx
        out += amp * (a * (1 - fy) + b * fy)
        total += amp
        amp *= 0.5
    return out / total


# ----------------------------------------------------------------------------------------------------------- export

def export_glb(path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    want = dict(filepath=path, export_format="GLB", export_yup=True, export_apply=True, export_cameras=False,
                export_lights=False, export_normals=True, export_texcoords=True, export_tangents=False,
                export_materials="EXPORT", export_image_format="AUTO", export_animations=False, export_extras=False,
                export_draco_mesh_compression_enable=False, export_attributes=False, use_selection=False,
                export_copyright="bdnowicki, CC BY 4.0")
    known = set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
    bpy.ops.export_scene.gltf(**{k: v for k, v in want.items() if k in known})


def report(meshes, path):
    tris = sum(m.triangles() for m in meshes)
    mats = sorted({mt.name for m in meshes for mt in m.materials})
    print("PAK3D %s: %d triangles, materials %s, %d bytes" % (os.path.basename(path), tris, ",".join(mats), os.path.getsize(path)))
    return tris

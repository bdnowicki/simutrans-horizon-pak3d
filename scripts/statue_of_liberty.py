# Statue of Liberty (Liberty Enlightening the World, New York, 1886) for the pak 3D: 1 x 2 squares, its place on
# Liberty Island of the New York City map (squares 378,657 and 378,658, one square east to west, two north to
# south). The robed figure with the torch raised in her right hand, the crown of seven rays and the tablet in her
# left arm stands on Hunt's granite pedestal (base course, the shaft with a projecting bay and door on every face,
# the loggia band with columns, the frieze of discs, the balcony) on the concrete foundation inside the
# eleven-pointed star of Fort Wood, with a lawn, paths, two small squares and trees on the rest of the two squares.
# Modelled in metres from the published dimensions (ground to the tip of the flame 93 m: foundation 19.8 m,
# pedestal 27.1 m, statue 46 m; heel to the top of the head 33.9 m, head 5.3 m, right arm 12.8 m, tablet
# 7.2 x 4.1 x 0.6 m) and scaled to squares like the Empire State Building (1.88/129 squares per metre).
# Stylised so it reads at the dashboard's usual zoom and fits the square: the figure is drawn 14 % larger and the
# foundation 3.8 m lower (1.39 squares in all instead of 1.36; figure : pedestal 52 : 43 m instead of 46 : 47 m),
# the star of Fort Wood about two thirds of its real size (it has to fit into the one square of width), the crown
# rays a little longer.
# Orientation: the real statue faces south-east (bearing about 135 degrees), out over the Upper Bay towards the
# harbour entrance. The compass of this map comes from its labels (one square is about 42 m): Governors Island
# (427,632) lies due east of Liberty Island (378,657) on the real harbour but at 63 degrees from the map's north
# (-y), the Verrazano-Narrows Bridge (480,856) due south but at 153 degrees, and Bayonne Bridge -> Verrazano
# Bridge (real bearing 115 degrees) at 86 degrees: the map is turned by about 28 degrees, its north (-y) is true
# north-north-east, along the Manhattan street grid, +x is the map's east. So she faces 135 - 28 = 107 degrees
# clockwise from the map's north: towards (+0.96 x, +0.29 y) of the game, across the open water of the Upper Bay
# towards Red Hook and Gowanus Bay, with the Narrows 46 degrees to her right as on the real harbour. The
# dashboard's default iso camera (from +x, +y) then sees her from the classic three-quarter front: face, torch arm
# on the left, tablet on the right. In Blender X = +x of the game, Y = -y (north); the statue and its pedestal
# are built facing -Y and turned by 180 - 107 = 73 degrees about Z; the lawn and trees are not turned.
#   blender -b --factory-startup -P scripts/statue_of_liberty.py -- --out models/statue_of_liberty.glb [--lod 1]
# Author: bdnowicki. License: CC BY 4.0.
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pak3d_blender as pb  # noqa: E402

SCALE = 1.88 / 129.0           # squares per metre, as the Empire State Building
FOOT = (1, 2)                  # squares x, y
FACING = 107.0                 # degrees clockwise from the map's north (-y) towards its east (+x)
TURN = math.radians(180.0 - FACING)
STATUE_K = 1.14                # the figure, larger than real
STAR_H = 6.2                   # walls of Fort Wood
PED_BASE = 16.2                # top of the (lowered) foundation, foot of the granite pedestal
PED_TOP = PED_BASE + 26.94     # top of the pedestal, where the statue stands
HALF_X = FOOT[0] / 2 / SCALE   # footprint half sizes in metres
HALF_Y = FOOT[1] / 2 / SCALE


# ------------------------------------------------------------------------------------------------------- helpers

def smooth(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def gauss(x, s):
    return math.exp(-0.5 * (x / s) ** 2)


def adiff(a, b):
    return (a - b + math.pi) % (2.0 * math.pi) - math.pi


def norm(v):
    v = np.asarray(v, dtype=float)
    length = np.linalg.norm(v)
    return v / length if length > 1e-12 else v


def lin(*c):
    """an sRGB colour as the linear factor glTF stores (textures stay sRGB)"""
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def fold(x):
    """folds of cloth: broad rounded ridges, sharp valleys (-1..1)"""
    return 2.0 * abs(math.cos(0.5 * x)) - 1.0


def loft(m, rings, mat, caps=(False, False)):
    """quads between rings of equal point count (each ring counter-clockwise about the direction the rings advance
    in) with smooth normals; u runs around the rings, v along the loft (metres / uv_size)"""
    P = np.asarray(rings, dtype=float)
    R, N = P.shape[0], P.shape[1]
    du = np.roll(P, -1, axis=1) - np.roll(P, 1, axis=1)
    dv = np.empty_like(P)
    dv[1:-1] = P[2:] - P[:-2]
    dv[0] = P[1] - P[0]
    dv[-1] = P[-1] - P[-2]
    nrm = np.cross(du, dv)
    ln = np.linalg.norm(nrm, axis=2, keepdims=True)
    radial = P - P.mean(axis=1, keepdims=True)
    rl = np.maximum(np.linalg.norm(radial, axis=2, keepdims=True), 1e-12)
    nrm = np.where(ln > 1e-9, nrm / np.maximum(ln, 1e-12), radial / rl)
    su, sv = mat.uv_size
    per = np.linalg.norm(np.roll(P, -1, axis=1) - P, axis=2).sum(axis=1).mean()
    vl = np.concatenate([[0.0], np.cumsum(np.linalg.norm(P[1:] - P[:-1], axis=2).mean(axis=1))])
    for i in range(R - 1):
        v0, v1 = vl[i] / sv, vl[i + 1] / sv
        for j in range(N):
            k = (j + 1) % N
            u0, u1 = j / N * per / su, (j + 1) / N * per / su
            m.face([tuple(P[i, j]), tuple(P[i, k]), tuple(P[i + 1, k]), tuple(P[i + 1, j])], mat,
                   [(u0, v0), (u1, v0), (u1, v1), (u0, v1)],
                   [tuple(nrm[i, j]), tuple(nrm[i, k]), tuple(nrm[i + 1, k]), tuple(nrm[i + 1, j])])
    if caps[0]:
        m.face([tuple(p) for p in P[0][::-1]], mat)
    if caps[1]:
        m.face([tuple(p) for p in P[-1]], mat)


def ellipsoid(m, c, r, mat, nu=16, nv=10):
    """ellipsoid with analytic normals; fans at the poles"""
    def at(lat, lon):
        x, y, z = math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)
        return (c[0] + r[0] * x, c[1] + r[1] * y, c[2] + r[2] * z), tuple(norm((x / r[0], y / r[1], z / r[2])))

    def uv(p):
        su, sv = mat.uv_size
        return (math.atan2(p[1] - c[1], p[0] - c[0]) * max(r[0], r[1]) / su, p[2] / sv)
    lats = [-math.pi / 2 + math.pi * i / nv for i in range(nv + 1)]
    for i in range(nv):
        for j in range(nu):
            l0, l1 = 2 * math.pi * j / nu, 2 * math.pi * (j + 1) / nu
            a, b, cc, d = at(lats[i], l0), at(lats[i], l1), at(lats[i + 1], l1), at(lats[i + 1], l0)
            if i == 0:
                quad = [a, cc, d]
            elif i == nv - 1:
                quad = [a, b, cc]
            else:
                quad = [a, b, cc, d]
            m.face([q[0] for q in quad], mat, [uv(q[0]) for q in quad], [q[1] for q in quad])


def catmull(points, per_seg):
    """points of a Catmull-Rom curve through the control points"""
    P = [np.asarray(p, dtype=float) for p in points]
    P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per_seg):
            t = k / per_seg
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


def tube(m, ctrl, radii, mat, segs, per_seg=3, caps=(False, False)):
    """a tube along a Catmull-Rom curve through ctrl, radius interpolated from radii (one per control point)"""
    path = catmull(ctrl, per_seg)
    rad = np.interp(np.linspace(0, len(radii) - 1, len(path)), np.arange(len(radii)), radii)
    T = [norm(path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]) for i in range(len(path))]
    n1 = norm(np.cross(T[0], (0.0, 0.0, 1.0)) if abs(T[0][2]) < 0.9 else np.cross(T[0], (1.0, 0.0, 0.0)))
    rings = []
    for i, p in enumerate(path):
        n1 = norm(n1 - np.dot(n1, T[i]) * T[i])
        n2 = np.cross(T[i], n1)
        rings.append([tuple(p + rad[i] * (math.cos(2 * math.pi * k / segs) * n1 + math.sin(2 * math.pi * k / segs) * n2))
                      for k in range(segs)])
    loft(m, rings, mat, caps)


def transform(m, start, k=1.0, z_off=0.0):
    """scales the faces added since `start` by k, moves them up by z_off and turns them by TURN about Z"""
    c, s = math.cos(TURN), math.sin(TURN)
    for i in range(start, len(m.faces)):
        pts, uvs, nrms, slot = m.faces[i]
        pts = [((x * c - y * s) * k, (x * s + y * c) * k, z * k + z_off) for x, y, z in pts]
        nrms = [(x * c - y * s, x * s + y * c, z) for x, y, z in nrms]
        m.faces[i] = (pts, uvs, nrms, slot)


def turn_quarter(m, start, k):
    """turns the faces added since `start` by k quarter turns about Z (the four faces of the pedestal)"""
    c, s = round(math.cos(k * math.pi / 2)), round(math.sin(k * math.pi / 2))
    for i in range(start, len(m.faces)):
        pts, uvs, nrms, slot = m.faces[i]
        m.faces[i] = ([(x * c - y * s, x * s + y * c, z) for x, y, z in pts], uvs,
                      [(x * c - y * s, x * s + y * c, z) for x, y, z in nrms], slot)


def turned_xy(x, y):
    c, s = math.cos(TURN), math.sin(TURN)
    return x * c - y * s, x * s + y * c


def sq(h):
    return [(-h, -h), (h, -h), (h, h), (-h, h)]


def frustum(m, h0, h1, z0, z1, side, top=None):
    """square truncated pyramid: half size h0 at z0, h1 at z1"""
    b, t = sq(h0), sq(h1)
    for i in range(4):
        j = (i + 1) % 4
        pts = [(b[i][0], b[i][1], z0), (b[j][0], b[j][1], z0), (t[j][0], t[j][1], z1), (t[i][0], t[i][1], z1)]
        m.face(pts, side, pb.facade_uv(pts, side, b[i]))
    if top is not None:
        m.face([(x, y, z1) for x, y in t], top)


def star_outline(R, r, n=11, phase=-math.pi / 2):
    """counter-clockwise star: a point at angle `phase` (local -Y = the statue's front)"""
    return [((R if k % 2 == 0 else r) * math.cos(phase + math.pi * k / n), (R if k % 2 == 0 else r) * math.sin(phase + math.pi * k / n))
            for k in range(2 * n)]


# ------------------------------------------------------------------------------------------------------ textures
# colours of textures are sRGB (rows bottom to top here, flipped when handed over)

COPPER = (0.400, 0.640, 0.575)      # verdigris between #5f9e8f and #6fa999
GRANITE = (0.725, 0.698, 0.647)     # #b9b2a5, warm grey
CONCRETE = (0.770, 0.750, 0.700)
FORT = (0.800, 0.770, 0.710)
LAWN = (0.250, 0.400, 0.170)
PAVING = (0.640, 0.620, 0.580)


def patina_texture(rng, size):
    """verdigris copper: mottled blue-green, darker rain streaks running down, a little brown copper showing"""
    n1 = pb.value_noise(size, size, (6, 6), rng, 5)
    n2 = pb.value_noise(size, size, (16, 16), rng, 3)
    streak = pb.value_noise(size, size, (2, 40), rng, 3)
    a = np.array([0.373, 0.620, 0.561], np.float32)      # #5f9e8f
    b = np.array([0.435, 0.665, 0.600], np.float32)      # #6fa999
    col = a + (b - a) * n1[..., None]
    col *= (0.94 + 0.09 * n2)[..., None]
    col *= (1.0 - 0.22 * np.clip(streak - 0.55, 0, 1) * 2.2)[..., None]
    rust = np.clip(n2 - 0.80, 0, 1) * 3.0
    col = col * (1 - 0.3 * rust[..., None]) + np.array([0.42, 0.36, 0.26], np.float32) * 0.3 * rust[..., None]
    hgt = 0.5 + 0.35 * n2 + 0.15 * n1
    return np.clip(col, 0, 1), hgt


def ashlar_texture(rng, size, base, rows, cols, joint, dark):
    """stone blocks in courses (rows x cols per texture, alternate courses offset by half a block)"""
    n = pb.value_noise(size, size, (8, 8), rng, 5)
    y = np.arange(size)[:, None] / size * rows
    x = np.arange(size)[None, :] / size * cols + np.where((np.floor(y) % 2) == 1, 0.5, 0.0)
    jy, jx = np.abs(y - np.round(y)), np.abs(x - np.round(x))
    jxw = joint * rows / cols * 0.6
    j = (jy < joint) | (jx < jxw)
    block = (np.floor(y) * 7 + np.floor(x) * 13) % 5
    col = np.asarray(base, np.float32) * (0.93 + 0.09 * n + 0.02 * block)[..., None]
    col = np.where(j[..., None], col * dark, col)
    edge = np.minimum(jy / (joint * 3), 1) * np.minimum(jx / (jxw * 3), 1)
    hgt = np.where(j, 0.0, (0.6 + 0.4 * edge ** 0.4) * (0.88 + 0.12 * n))
    return np.clip(col, 0, 1), hgt


def lawn_texture(rng, size):
    n = pb.value_noise(size, size, (6, 6), rng, 5)
    m = pb.value_noise(size, size, (24, 24), rng, 2)
    col = np.array(LAWN, np.float32) * (0.86 + 0.22 * n + 0.08 * m)[..., None]
    return np.clip(col, 0, 1)


# ------------------------------------------------------------------------------------------------------ materials

def materials(lod, rng):
    if lod == 0:
        pc, ph = patina_texture(rng, 512)
        copper = pb.Material("liberty_copper", uv_size=(9.0, 9.0), base_tex=pc[::-1],
                             normal_tex=pb.normal_from_height(ph, 0.8)[::-1], roughness=0.55, metallic=0.2, tex_format="JPEG")
        gc, gh = ashlar_texture(rng, 512, GRANITE, 8, 4, 0.03, 0.82)
        granite = pb.Material("liberty_granite", uv_size=(6.0, 6.0), base_tex=gc[::-1],
                              normal_tex=pb.normal_from_height(gh, 1.2)[::-1], roughness=0.8, tex_format="JPEG")
        cc, chh = ashlar_texture(rng, 512, CONCRETE, 8, 1, 0.01, 0.92)
        concrete = pb.Material("liberty_concrete", uv_size=(8.0, 8.0), base_tex=cc[::-1],
                               normal_tex=pb.normal_from_height(chh, 0.6)[::-1], roughness=0.9, tex_format="JPEG")
        fc, fh = ashlar_texture(rng, 512, FORT, 6, 3, 0.025, 0.85)
        fort = pb.Material("liberty_fort", uv_size=(6.0, 6.0), base_tex=fc[::-1],
                           normal_tex=pb.normal_from_height(fh, 1.0)[::-1], roughness=0.85, tex_format="JPEG")
        lawn = pb.Material("liberty_lawn", uv_size=(24.0, 24.0), base_tex=lawn_texture(rng, 256)[::-1], roughness=0.95,
                           tex_format="JPEG")
    else:  # plain colours: the means of the textures above
        copper = pb.Material("liberty_copper", color=lin(0.39, 0.62, 0.56), roughness=0.55, metallic=0.2)
        granite = pb.Material("liberty_granite", color=lin(*[c * 0.95 for c in GRANITE]), roughness=0.8)
        concrete = pb.Material("liberty_concrete", color=lin(*[c * 0.97 for c in CONCRETE]), roughness=0.9)
        fort = pb.Material("liberty_fort", color=lin(*[c * 0.94 for c in FORT]), roughness=0.85)
        lawn = pb.Material("liberty_lawn", color=lin(*[c * 0.98 for c in LAWN]), roughness=0.95)
    flame = pb.Material("night_emissive", color=lin(0.88, 0.66, 0.20), roughness=0.35, metallic=0.3, emissive=lin(1.0, 0.72, 0.30))
    shadow = pb.Material("liberty_shadow", color=lin(0.20, 0.19, 0.18), roughness=0.9)
    paving = pb.Material("liberty_paving", color=lin(*PAVING), roughness=0.9)
    tree = pb.Material("liberty_tree", color=lin(0.17, 0.33, 0.13), roughness=0.9)
    trunk = pb.Material("liberty_trunk", color=lin(0.33, 0.25, 0.17), roughness=0.9)
    return dict(copper=copper, granite=granite, concrete=concrete, fort=fort, lawn=lawn, flame=flame, shadow=shadow,
                paving=paving, tree=tree, trunk=trunk)


# --------------------------------------------------------------------------------------------------------- statue
# Statue coordinates in metres (real size, scaled by STATUE_K when placed): origin at the middle of her feet on the
# top of the pedestal, front -Y, her left +X, her right (the torch arm) -X. Ring angles t run counter-clockwise from
# +X: 90 back, 180 her right, 270 front.

BODY = [  # z, half width (x), half depth (y), centre y (negative = forward)
    (0.0, 5.30, 4.45, -0.45),
    (0.6, 5.20, 4.35, -0.45),
    (2.0, 4.98, 4.12, -0.40),
    (5.0, 4.72, 3.84, -0.35),
    (9.0, 4.48, 3.60, -0.30),
    (13.0, 4.28, 3.40, -0.25),
    (17.0, 4.08, 3.20, -0.15),
    (20.0, 3.90, 3.00, -0.05),
    (21.2, 3.85, 2.95, -0.05),
    (22.6, 4.05, 3.15, -0.22),
    (24.2, 4.32, 3.05, -0.15),
    (25.4, 4.58, 2.85, -0.05),
    (26.1, 4.62, 2.70, 0.00),
    (26.7, 4.30, 2.48, 0.05),
    (27.15, 3.40, 2.05, 0.08),
    (27.5, 2.10, 1.55, 0.05),
    (27.8, 1.36, 1.28, 0.00),
    (29.4, 1.24, 1.20, -0.10),
    (30.2, 1.10, 1.15, -0.15),
]
HEAD_C, HEAD_R = (0.0, -0.3, 31.4), (1.66, 1.86, 2.5)
TORCH_X, TORCH_Y = -6.95, -0.6


def robe_offset(t, z, lod):
    """radial offset of the robe (metres) at angle t and height z: folds, legs, the overfold, the cloak, the belt"""
    off = 0.0
    low = 1.0 - smooth(2.0, 21.0, z)
    ph = 0.05 * z
    if lod == 0:
        off += 0.48 * low * (0.62 * fold(13 * t + 0.4 + ph) + 0.38 * fold(7 * t + 1.3 - ph))
    else:
        off += 0.25 * low * fold(7 * t + 1.3 - ph)
    off += 0.60 * gauss(adiff(t, math.radians(245)), 0.35) * gauss(z - 10.5, 2.6)        # right knee steps forward
    off += 0.28 * gauss(adiff(t, math.radians(298)), 0.22) * (1 - smooth(14.0, 18.0, z))  # straight left leg
    hem = 14.0 + 4.0 * math.cos(t - math.radians(200))                                   # overfold of the palla
    over = smooth(hem - 0.3, hem + 0.3, z)
    off += 0.36 * over * (1 - smooth(24.0, 27.0, z))
    if lod == 0:
        off += 0.15 * over * fold(9 * t + 0.45 * z) * (1 - smooth(20.0, 24.0, z))
    # the cloak falling from the left forearm straight down her left side
    off += 0.85 * gauss(adiff(t, 0.12), 0.42) * smooth(1.0, 5.0, z) * (1 - smooth(19.0, 21.0, z))
    off -= 0.16 * gauss(z - 21.2, 0.35)                                                   # belt under the bust
    if lod == 0:
        up = smooth(21.0, 23.0, z) * (1 - smooth(26.0, 27.5, z))
        off += 0.10 * up * math.sin(8 * t - 0.9 * z)
    return off


def body(m, mt, lod):
    if lod == 0:
        zs = [0.0, 0.4, 1.2, 2.2, 3.4, 4.8, 6.2, 7.6, 9.0, 10.2, 11.2, 12.0, 12.8, 13.6, 14.4, 15.2, 16.0, 16.8, 17.6, 18.4,
              19.2, 20.0, 20.8, 21.5, 22.2, 23.0, 23.8, 24.6, 25.4, 26.1, 26.5, 26.85, 27.15, 27.4, 27.65, 27.9, 28.4,
              29.1, 29.7, 30.2]
        N = 64
    else:
        zs = [0.0, 1.5, 5.0, 9.5, 13.0, 16.0, 18.5, 21.0, 23.0, 25.4, 26.3, 27.0, 27.5, 27.9, 30.2]
        N = 24
    key = np.array(BODY)
    rings = []
    for z in zs:
        a = np.interp(z, key[:, 0], key[:, 1])
        b = np.interp(z, key[:, 0], key[:, 2])
        cy = np.interp(z, key[:, 0], key[:, 3])
        ring = []
        for j in range(N):
            t = 2 * math.pi * j / N
            ex, ey = a * math.cos(t), b * math.sin(t)
            nx, ny = b * math.cos(t), a * math.sin(t)
            ln = math.hypot(nx, ny)
            d = robe_offset(t, z, lod)
            ring.append((ex + nx / ln * d, cy + ey + ny / ln * d, z))
        rings.append(ring)
    loft(m, rings, mt["copper"])


def head_and_crown(m, mt, lod):
    C = mt["copper"]
    ellipsoid(m, HEAD_C, HEAD_R, C, *((18, 12) if lod == 0 else (10, 7)))
    if lod == 0:
        ellipsoid(m, (0.0, 1.0, 30.5), (1.05, 0.8, 0.85), C, 10, 6)           # hair gathered at the nape
        ellipsoid(m, (0.0, -2.0, 31.1), (0.26, 0.24, 0.52), C, 6, 4)          # nose
    # diadem: higher at the front
    cx, cy = HEAD_C[0], HEAD_C[1]
    N = 28 if lod == 0 else 12
    rings = []
    for (rx, ry, zb, zf) in ((1.72, 1.92, 32.15, 32.35), (1.70, 1.90, 32.95, 33.45), (1.50, 1.72, 32.95, 33.45)):
        ring = []
        for j in range(N):
            t = 2 * math.pi * j / N
            front = max(0.0, -math.sin(t))
            ring.append((cx + rx * math.cos(t), cy + ry * math.sin(t), zb + (zf - zb) * front))
        rings.append(ring)
    loft(m, rings, C)
    # seven rays, steeper towards the front so the fan looks even from the front
    for alpha, beta in ((-95, 22), (-63, 42), (-32, 52), (0, 58), (32, 52), (63, 42), (95, 22)):
        t = math.radians(270 + alpha)
        front = max(0.0, -math.sin(t))
        base = np.array((cx + 1.6 * math.cos(t), cy + 1.8 * math.sin(t), 32.95 + 0.5 * front - 0.2))
        be = math.radians(beta)
        d = np.array((math.cos(be) * math.cos(t), math.cos(be) * math.sin(t), math.sin(be)))
        tt = np.array((-math.sin(t), math.cos(t), 0.0))
        v = norm(np.cross(d, tt))
        tip = base + 4.3 * d
        w, h = 0.62, 0.34
        corners = [base - w * tt - h * v, base + w * tt - h * v, base + w * tt + h * v, base - w * tt + h * v]
        if lod == 0:
            for i in range(4):
                m.face([tuple(corners[i]), tuple(corners[(i + 1) % 4]), tuple(tip)], C)
        else:
            for i, j in ((0, 1), (1, 3), (3, 0)):
                m.face([tuple(corners[i]), tuple(corners[j]), tuple(tip)], C)


def arms_torch_tablet(m, mt, lod):
    C, F = mt["copper"], mt["flame"]
    segs = 16 if lod == 0 else 7
    ps = 3 if lod == 0 else 1
    # right arm raised: sleeve bunched at the shoulder, bare forearm, the fist round the torch under its cup
    tube(m, [(-3.0, 0.1, 24.4), (-4.3, 0.0, 26.3), (-5.6, -0.25, 29.2), (-6.35, -0.45, 32.0), (-6.8, -0.55, 35.0),
             (TORCH_X, TORCH_Y, 37.7)], [1.9, 2.05, 1.72, 1.32, 1.08, 0.95], C, segs, ps, caps=(True, True))
    ellipsoid(m, (TORCH_X, TORCH_Y, 38.55), (1.02, 1.12, 1.3), C, *((12, 8) if lod == 0 else (6, 4)))
    # left arm down the side, forearm forward under the tablet, the hand at its foot
    tube(m, [(3.3, 0.3, 25.3), (4.45, 0.45, 24.8), (5.1, 0.7, 22.8), (5.35, 0.6, 20.8), (5.3, -0.6, 19.9), (5.05, -2.1, 19.8)],
         [1.9, 1.72, 1.42, 1.28, 1.12, 1.0], C, segs, ps, caps=(True, True))
    ellipsoid(m, (4.95, -2.65, 19.85), (0.85, 0.95, 0.72), C, *((10, 6) if lod == 0 else (5, 3)))
    if lod == 0:
        ellipsoid(m, (1.7, -5.15, 0.35), (0.75, 1.2, 0.5), C, 8, 4)          # the left foot under the hem
    # tablet: foot in the left hand, top leaning against the shoulder, its face to her left front
    B = np.array((5.3, -2.95, 19.4))
    L = norm(np.array((4.15, -2.15, 26.6)) - B) * 7.19
    W = norm(np.cross(L, (0.8, -0.6, 0.0)))
    Nn = norm(np.cross(W, L))
    cs = [B + sl * L + sw * 2.07 * W + sn * 0.31 * Nn for sl in (0, 1) for sw, sn in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    mid = B + 0.5 * L
    for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (3, 2, 1, 0)):
        pts = [tuple(cs[i]) for i in f]
        if np.dot(pb.face_normal(pts), np.mean(pts, axis=0) - mid) < 0:
            pts = pts[::-1]
        m.face(pts, C)
    # torch: handle through the fist, flared cup, the balcony with its railing, the flame
    ts = 12 if lod == 0 else 6
    m.cylinder((TORCH_X, TORCH_Y, 36.9), 0.42, 2.9, ts, C, caps=(True, False), r2=0.55)
    m.cylinder((TORCH_X, TORCH_Y, 39.7), 0.6, 1.3, ts, C, caps=(False, False), r2=1.45)
    bs = 18 if lod == 0 else 8
    m.cylinder((TORCH_X, TORCH_Y, 41.0), 2.2, 0.45, bs, C, caps=(True, True))
    if lod == 0:
        m.cylinder((TORCH_X, TORCH_Y, 41.45), 2.2, 0.75, bs, C, caps=(False, False))
        ring = [(math.cos(2 * math.pi * k / bs), math.sin(2 * math.pi * k / bs)) for k in range(bs)]
        for k in range(bs):
            (ca, sa), (cb, sb) = ring[k], ring[(k + 1) % bs]
            ia, ib = (TORCH_X + 2.08 * ca, TORCH_Y + 2.08 * sa), (TORCH_X + 2.08 * cb, TORCH_Y + 2.08 * sb)
            oa, ob = (TORCH_X + 2.2 * ca, TORCH_Y + 2.2 * sa), (TORCH_X + 2.2 * cb, TORCH_Y + 2.2 * sb)
            m.face([(ib[0], ib[1], 41.45), (ia[0], ia[1], 41.45), (ia[0], ia[1], 42.2), (ib[0], ib[1], 42.2)], C)  # inside
            m.face([(ia[0], ia[1], 42.2), (oa[0], oa[1], 42.2), (ob[0], ob[1], 42.2), (ib[0], ib[1], 42.2)], C)  # top
    # flame: lobed, tongues twisting up to the tip at 46.05 m
    prof = [(41.45, 1.15), (41.9, 1.45), (42.6, 1.52), (43.4, 1.30), (44.2, 1.0), (45.0, 0.64), (45.6, 0.33), (46.05, 0.05)]
    zs, N = (np.linspace(41.45, 46.05, 12), 20) if lod == 0 else (np.array([41.45, 42.6, 44.2, 46.05]), 7)
    pz, pr = np.array([p[0] for p in prof]), np.array([p[1] for p in prof])
    rings = []
    for z in zs:
        r0 = np.interp(z, pz, pr)
        lean = 0.12 * (z - 41.45)
        ring = []
        for j in range(N):
            t = 2 * math.pi * j / N
            r = r0 * (1 + (0.2 if lod == 0 else 0.0) * math.sin(4 * t + 1.6 * (z - 41.45)) * smooth(41.6, 43.0, z))
            ring.append((TORCH_X + r * math.cos(t) - 0.3 * lean, TORCH_Y + r * math.sin(t) - lean, z))
        rings.append(ring)
    loft(m, rings, F, caps=(False, True))


def statue(m, mt, lod):
    body(m, mt, lod)
    head_and_crown(m, mt, lod)
    arms_torch_tablet(m, mt, lod)


# ------------------------------------------------------------------------------------------------------- pedestal

def star_radius():
    """outer radius of the star (metres) so that its turned walls (with their batter) stay inside the square's width"""
    pts = star_outline(1.0, 0.79)
    worst = max(abs(turned_xy(x, y)[0]) for x, y in pts[::2])
    return min(31.5, ((FOOT[0] / 2 - 0.026) / SCALE - 0.9) / worst)


def fort(m, mt, lod):
    R = star_radius()
    top = star_outline(R, 0.79 * R)
    bot = star_outline(R + 0.9, 0.79 * R + 0.9)
    n = len(top)
    S, P = mt["fort"], mt["paving"]
    for i in range(n):
        j = (i + 1) % n
        pts = [(bot[i][0], bot[i][1], 0.0), (bot[j][0], bot[j][1], 0.0), (top[j][0], top[j][1], STAR_H), (top[i][0], top[i][1], STAR_H)]
        m.face(pts, S, pb.facade_uv(pts, S, bot[i]))
        if lod == 0:  # coping along the top of the walls
            c0, c1 = (top[i][0] * 1.012, top[i][1] * 1.012), (top[j][0] * 1.012, top[j][1] * 1.012)
            m.face([(c0[0], c0[1], STAR_H - 0.5), (c1[0], c1[1], STAR_H - 0.5), (c1[0], c1[1], STAR_H), (c0[0], c0[1], STAR_H)], P)
    # the top: grass on the bastions (the points), paving inside round the foundation
    for k in range(0, n, 2):
        a, p, c = top[k - 1], top[k], top[(k + 1) % n]
        m.face([(a[0], a[1], STAR_H), (p[0], p[1], STAR_H), (c[0], c[1], STAR_H)], mt["lawn"])
        m.face([(0.0, 0.0, STAR_H), (a[0], a[1], STAR_H), (c[0], c[1], STAR_H)], P)
    return R


def pedestal(m, mt, lod):
    G, K, D = mt["granite"], mt["concrete"], mt["shadow"]
    b = PED_BASE
    # steps round the foot of the foundation, the battered foundation, its cornice
    if lod == 0:
        for h, z0, z1 in ((16.0, STAR_H, 6.8), (15.3, 6.8, 7.4), (14.6, 7.4, 8.0)):
            m.box(-h, h, -h, h, z0, z1, K, skip=("-z",))
    else:
        m.box(-16.0, 16.0, -16.0, 16.0, STAR_H, 8.0, K, skip=("-z",))
    frustum(m, 13.0, 10.6, 8.0, b - 0.4, K)
    m.box(-10.9, 10.9, -10.9, 10.9, b - 0.4, b, K, skip=("-z",))
    # granite pedestal: base course and its wash
    m.box(-10.0, 10.0, -10.0, 10.0, b, b + 1.4, G, skip=("-z", "+z"))
    frustum(m, 10.0, 9.4, b + 1.4, b + 2.0, G)
    # the shaft (slight taper) with a projecting bay, a door and three windows on every face
    frustum(m, 9.1, 8.8, b + 2.0, b + 13.2, G)
    for ang in range(4):
        start = len(m.faces)
        m.box(-4.0, 4.0, -9.45, -8.7, b + 2.0, b + 12.4, G, skip=("+y", "-z"))
        m.box(-4.4, 4.4, -9.75, -8.7, b + 12.4, b + 13.2, G, skip=("+y", "-z"))
        m.face([(-1.7, -9.47, b + 2.0), (1.7, -9.47, b + 2.0), (1.7, -9.47, b + 7.4), (-1.7, -9.47, b + 7.4)], D)
        if lod == 0:
            for k in range(3):
                x = -2.3 + k * 2.3
                m.face([(x - 0.5, -9.47, b + 8.6), (x + 0.5, -9.47, b + 8.6), (x + 0.5, -9.47, b + 11.2), (x - 0.5, -9.47, b + 11.2)], D)
        turn_quarter(m, start, ang)
    m.box(-9.25, 9.25, -9.25, 9.25, b + 13.2, b + 13.8, G, skip=("-z",))
    # loggia: dark recess, corner piers, four columns on every face
    z0, z1, hp, pw, core = b + 13.8, b + 19.0, 9.0, 3.0, 7.7
    m.box(-core, core, -core, core, z0, z1, D, skip=("-z", "+z"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, x1 = sorted((sx * hp, sx * (hp - pw)))
            y0, y1 = sorted((sy * hp, sy * (hp - pw)))
            m.box(x0, x1, y0, y1, z0, z1, G, skip=("-z", "+z"))
    cs = 8 if lod == 0 else 4
    for ang in range(4):
        start = len(m.faces)
        for off in (-4.5, -1.5, 1.5, 4.5):
            m.cylinder((off, -(hp - 0.75), z0), 0.5, z1 - z0, cs, G, caps=(False, False), phase=math.pi / cs)
        turn_quarter(m, start, ang)
    # cornice, frieze with discs, top cornice, balcony parapet
    m.box(-9.5, 9.5, -9.5, 9.5, b + 19.0, b + 20.0, G, skip=("-z",))
    m.box(-8.7, 8.7, -8.7, 8.7, b + 20.0, b + 23.2, G, skip=("-z", "+z"))
    if lod == 0:
        for ang in range(4):
            start = len(m.faces)
            for off in (-5.6, -2.8, 0.0, 2.8, 5.6):
                m.cylinder((off, -8.98, b + 21.6), 0.68, 0.28, 8, G, axis="y", caps=(True, False))
            turn_quarter(m, start, ang)
    m.box(-9.2, 9.2, -9.2, 9.2, b + 23.2, b + 24.0, G, skip=("-z",))
    po, pi_, pz0, pz1 = 9.2, 8.6, b + 24.0, b + 25.5
    m.box(-po, po, -po, po, pz0, pz1, G, skip=("-z", "+z"))
    inner, outer = sq(pi_), sq(po)
    for i in range(4):
        j = (i + 1) % 4
        (ax, ay), (bx, by) = inner[i], inner[j]
        (cx_, cy_), (dx, dy) = outer[i], outer[j]
        if lod == 0:
            m.face([(bx, by, pz0), (ax, ay, pz0), (ax, ay, pz1), (bx, by, pz1)], G)
        m.face([(cx_, cy_, pz1), (dx, dy, pz1), (bx, by, pz1), (ax, ay, pz1)], G)
    # the block the statue stands on
    m.box(-7.6, 7.6, -7.6, 7.6, b + 24.0, b + 25.6, G, skip=("-z",))
    m.box(-7.0, 7.0, -7.0, 7.0, b + 25.6, PED_TOP, G, skip=("-z",))


# --------------------------------------------------------------------------------------------------------- island

def island(m, mt, R, lod, rng):
    """lawn over the two squares, paths to a small square at each end, a walk along the ends, trees (model
    coordinates, not turned)"""
    hx, hy, cr = HALF_X - 0.015 / SCALE, HALF_Y - 0.015 / SCALE, 0.12 / SCALE
    poly = []
    steps = 4 if lod == 0 else 2
    for (cx, cy, a0) in ((hx - cr, -hy + cr, -90), (hx - cr, hy - cr, 0), (-hx + cr, hy - cr, 90), (-hx + cr, -hy + cr, 180)):
        for k in range(steps + 1):
            a = math.radians(a0 + 90 * k / steps)
            poly.append((cx + cr * math.cos(a), cy + cr * math.sin(a)))
    P = mt["paving"]
    m.prism(poly, 0.0, 0.3, P, top=mt["lawn"])
    reach = R + 1.0
    for sgn in (-1, 1):
        pc = sgn * (hy * 0.72)
        m.cylinder((0.0, pc, 0.3), 6.5, 0.12, 14 if lod == 0 else 8, P, caps=(False, True))
        y0, y1 = sorted((sgn * reach * 0.8, pc - sgn * 6.0))
        m.box(-1.6, 1.6, y0, y1, 0.3, 0.42, P, skip=("-z",) if lod == 0 else ("-z", "-x", "+x", "-y", "+y"))
    # trees, not on the paths, the squares or the fort (the same places in both levels)
    placed = []
    tries = 0
    while len(placed) < 16 and tries < 3000:
        tries += 1
        x = rng.uniform(-hx + 4.5, hx - 4.5)
        y = rng.uniform(-hy + 9.0, hy - 9.0)
        if math.hypot(x, y) < R + 5.0 or abs(x) < 4.2 or math.hypot(x, abs(y) - hy * 0.72) < 10.0:
            continue
        if any(math.hypot(x - px, y - py) < 6.5 for px, py, _, _ in placed):
            continue
        placed.append((x, y, rng.uniform(7.0, 10.0), rng.uniform(2.6, 3.4)))
    for x, y, h, r in placed:
        zc = h * 0.35 + 0.3
        if lod == 0:
            m.cylinder((x, y, 0.3), 0.35, h * 0.4, 5, mt["trunk"], caps=(False, False))
            m.cylinder((x, y, zc), 0.4, h * 0.3, 7, mt["tree"], caps=(False, False), r2=r)
            m.cylinder((x, y, zc + h * 0.3), r, h * 0.38, 7, mt["tree"], caps=(False, False), r2=0.3)
        else:
            m.cylinder((x, y, 0.3), r * 0.85, h * 0.9, 4, mt["tree"], caps=(False, False), r2=0.2)


# ------------------------------------------------------------------------------------------------------------- build

def build(mt, lod):
    m = pb.Mesh("StatueOfLiberty" if lod == 0 else "StatueOfLiberty_lod1", SCALE)
    start = len(m.faces)
    statue(m, mt, lod)
    transform(m, start, k=STATUE_K, z_off=PED_TOP)
    start = len(m.faces)
    R = fort(m, mt, lod)
    pedestal(m, mt, lod)
    transform(m, start)
    island(m, mt, R, lod, np.random.default_rng(1886))
    return [m]


def main():
    a = pb.parse_args()
    pb.empty_scene()
    mt = materials(a.lod, np.random.default_rng(1886))
    meshes = build(mt, a.lod)
    for me in meshes:
        me.build()
    pb.export_glb(a.out)
    pb.report(meshes, a.out)


main()

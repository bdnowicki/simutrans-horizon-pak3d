# Empire State Building (New York, 1931) for the pak 3D: 1 x 2 squares, its place on the New York City map (one
# square east to west, two north to south between 33rd and 34th Street), front (33rd Street) towards -Y, 34th Street
# towards +Y, 5th Avenue towards +X. Modelled in metres from the setbacks of the real building (lot 129 x 60 m,
# its long side laid along the two squares, a quarter turn from the real one; roof of the 102nd floor at 381 m,
# antenna tip at 443 m) and scaled to squares.
#   blender -b --factory-startup -P scripts/empire_state.py -- --out models/empire_state.glb [--lod 1]
# Author: bdnowicki. License: CC BY 4.0.
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pak3d_blender as pb  # noqa: E402

LOT = 129.0                   # metres along 34th Street: the long side, along the two squares (y)
SCALE = 1.88 / LOT            # squares per metre: the lot spans 1.88 of the 2 squares
FOOT = (1, 2)                 # squares x, y
BAY, FLOOR = 3.0, 3.75        # facade grid in metres
TILE_BAYS, TILE_FLOORS = 16, 32

# setbacks: (half x, half y, corner notch, bottom, top) in metres; x across the lot (60 m), y along it (129 m)
PODIUM = (30.0, 64.5, 0.0, 0.0, 25.0)
TIERS = [
    (26.0, 54.0, 6.0, 25.0, 79.0),      # floors 6-21
    (24.5, 46.5, 6.0, 79.0, 94.0),      # 21-25
    (23.0, 39.0, 6.0, 94.0, 112.0),     # 25-30
    (21.0, 30.0, 6.0, 112.0, 270.0),    # the shaft, 30-72
    (16.5, 24.0, 4.5, 270.0, 304.0),    # 72-81
    (13.5, 18.0, 3.0, 304.0, 319.0),    # 81-85
]


# ------------------------------------------------------------------------------------------------------------ textures

def facade_textures(rng, size):
    """office facade, one tile of 16 bays x 32 floors: limestone piers, steel mullions, aluminium spandrels, windows.
    Returns base colour, ORM (G roughness, B metallic), height and night lights, rows bottom to top."""
    W = H = size
    bw, fh = W // TILE_BAYS, H // TILE_FLOORS
    xs = (np.arange(W) % bw) / bw          # 0..1 across a bay, pier centred on 0
    ys = (np.arange(H) % fh) / fh          # 0..1 up a floor
    col = np.zeros((H, W, 3), np.float32)
    rough = np.zeros((H, W), np.float32)
    metal = np.zeros((H, W), np.float32)
    hgt = np.zeros((H, W), np.float32)
    light = np.zeros((H, W, 3), np.float32)
    X, Y = np.meshgrid(xs, ys)
    pier = (X < 0.19) | (X > 0.81)
    mull = ~pier & ((X < 0.24) | (X > 0.76))
    win_x = ~pier & ~mull
    spandrel = win_x & (Y < 0.30)
    frame = win_x & ~spandrel & ((Y < 0.34) | (Y > 0.93) | (X < 0.27) | (X > 0.73) | (np.abs(X - 0.5) < 0.012))
    glass = win_x & ~spandrel & ~frame
    stone_noise = pb.value_noise(H, W, (8, 8), rng, 4)
    streak = pb.value_noise(H, W, (2, 48), rng, 2)
    lime = np.array([0.85, 0.81, 0.73], np.float32)
    col[pier] = lime
    shade = (0.93 + 0.12 * stone_noise - 0.07 * np.clip(streak - 0.55, 0, 1) * 3)[..., None]
    col = np.where(pier[..., None], col * shade, col)
    col[mull] = (0.80, 0.81, 0.83)
    al = 0.56 + 0.05 * stone_noise
    col[spandrel] = np.stack([al, al * 0.98, al * 0.94], axis=-1)[spandrel]
    # spandrel relief: two horizontal grooves
    groove = spandrel & ((np.abs(Y - 0.10) < 0.02) | (np.abs(Y - 0.20) < 0.02))
    col[groove] *= 0.72
    col[frame] = (0.42, 0.42, 0.43)
    # glass per window: tint, blinds, a soft reflection
    gx = np.arange(W) // bw
    gy = np.arange(H) // fh
    ID = (gy[:, None] * TILE_BAYS + gx[None, :])
    n_win = TILE_BAYS * TILE_FLOORS
    tint = rng.uniform(0.13, 0.27, n_win).astype(np.float32)
    blind = rng.random(n_win) < 0.22
    blind_h = rng.uniform(0.35, 0.95, n_win).astype(np.float32)
    lit_floor = rng.random(TILE_FLOORS) < 0.45
    lit = (rng.random(n_win) < np.where(np.repeat(lit_floor, TILE_BAYS), 0.75, 0.18))
    warm = rng.random(n_win) < 0.7
    level = rng.uniform(0.55, 1.0, n_win).astype(np.float32)
    t = tint[ID]
    gy_in = np.clip((Y - 0.34) / 0.59, 0, 1)
    refl = 0.10 * (1 - gy_in) + 0.06 * pb.value_noise(H, W, (4, 4), rng, 2)
    g = np.stack([t + refl, t + 0.03 + refl, t + 0.07 + refl], axis=-1)
    bl = blind[ID] & (gy_in > 1 - blind_h[ID])
    g = np.where(bl[..., None], np.array([0.60, 0.56, 0.48], np.float32) * (0.9 + 0.1 * stone_noise[..., None]), g)
    col = np.where(glass[..., None], g, col)
    lw = np.where(warm[ID][..., None], np.array([1.0, 0.83, 0.55], np.float32), np.array([0.82, 0.88, 1.0], np.float32))
    lv = (level[ID] * np.where(bl, 0.6, 1.0))[..., None]
    light = np.where((glass & lit[ID])[..., None], lw * lv, light)
    rough[pier], metal[pier] = 0.85, 0.0
    rough[mull], metal[mull] = 0.35, 0.3
    rough[spandrel], metal[spandrel] = 0.55, 0.25
    rough[frame], metal[frame] = 0.5, 0.1
    rough[glass] = np.where(bl[glass], 0.7, 0.12)
    hgt[pier] = 1.0 - 0.15 * (np.abs(X[pier] - np.round(X[pier])) / 0.19) ** 2
    hgt[mull] = 0.75
    hgt[spandrel] = 0.35
    hgt[groove] = 0.25
    hgt[frame] = 0.2
    hgt[glass] = 0.0
    orm = np.stack([np.ones_like(rough), rough, metal], axis=-1)
    return np.clip(col, 0, 1), orm, hgt, np.clip(light, 0, 1)


def stone_texture(rng, size):
    """limestone ashlar, 6 x 6 m: blocks 1.5 m x 0.75 m"""
    n = pb.value_noise(size, size, (6, 6), rng, 5)
    y = np.arange(size)[:, None] / size * 8
    x = np.arange(size)[None, :] / size * 4 + np.where((np.floor(y) % 2) == 1, 0.5, 0.0)
    joint = (np.abs(y - np.round(y)) < 0.03) | (np.abs(x - np.round(x)) < 0.015)
    base = np.array([0.80, 0.765, 0.69], np.float32)
    col = base * (0.9 + 0.16 * n)[..., None]
    col = np.where(joint[..., None], col * 0.78, col)
    hgt = np.where(joint, 0.0, 0.6 + 0.4 * n)
    return np.clip(col, 0, 1), hgt


def roof_texture(rng, size):
    n = pb.value_noise(size, size, (8, 8), rng, 5)
    g = 0.30 + 0.10 * n
    return np.stack([g, g * 0.99, g * 0.96], axis=-1)


def storefront_texture(rng, w, h):
    """ground floors, 12 m x 7.5 m: dark granite plinth, bronze framed shop windows, a band of transoms"""
    col = np.zeros((h, w, 3), np.float32)
    Y = (np.arange(h) / h)[:, None] * 7.5 * np.ones((1, w))
    X = (np.arange(w) / w)[None, :] * 12.0 * np.ones((h, 1))
    bay = X % 3.0
    col[:] = (0.80, 0.765, 0.69)
    pierm = (bay < 0.45) | (bay > 2.55)
    win = ~pierm & (Y > 0.6) & (Y < 4.6)
    trans = ~pierm & (Y > 4.9) & (Y < 6.6)
    col[win | trans] = (0.10, 0.11, 0.12)
    shop = win & (Y < 4.3) & (Y > 0.9) & (np.abs(bay - 1.5) < 0.98)
    n = pb.value_noise(h, w, (4, 8), rng, 3)
    col[shop] = np.stack([0.20 + 0.25 * n, 0.18 + 0.2 * n, 0.14 + 0.15 * n], axis=-1)[shop]
    col[(Y < 0.6) & ~pierm] = (0.13, 0.12, 0.12)
    col[pierm & (Y < 0.6)] = (0.15, 0.14, 0.14)
    bronze = (win | trans) & ((np.abs(bay - 1.5) > 0.98) | (np.abs(Y - 4.75) < 0.15) | (np.abs(Y - 0.75) < 0.15))
    col[bronze] = (0.34, 0.25, 0.15)
    return col


# ------------------------------------------------------------------------------------------------------------- model

def materials(lod, rng):
    if lod == 0:
        base, orm, hgt, light = facade_textures(rng, 1024)
        facade = pb.Material("night_emissive", uv_size=(TILE_BAYS * BAY, TILE_FLOORS * FLOOR), base_tex=base[::-1],
                             orm_tex=orm[::-1], normal_tex=pb.normal_from_height(hgt, 2.5)[::-1], emissive_tex=light[::-1],
                             roughness=1.0, metallic=0.0, tex_format="JPEG")
        sc, sh = stone_texture(rng, 512)
        stone = pb.Material("esb_limestone", uv_size=(6.0, 6.0), base_tex=sc[::-1], normal_tex=pb.normal_from_height(sh, 1.5)[::-1],
                            roughness=0.85, tex_format="JPEG")
        roof = pb.Material("esb_roof", uv_size=(12.0, 12.0), base_tex=roof_texture(rng, 256)[::-1], roughness=0.95, tex_format="JPEG")
        shop = pb.Material("esb_storefront", uv_size=(12.0, 7.5), base_tex=storefront_texture(rng, 512, 256)[::-1], roughness=0.35,
                           tex_format="JPEG")
    else:
        base, orm, hgt, light = facade_textures(rng, 1024)
        facade = pb.Material("night_emissive", uv_size=(TILE_BAYS * BAY, TILE_FLOORS * FLOOR),
                             base_tex=pb.downsample(base, 4)[::-1], emissive_tex=pb.downsample(light, 4)[::-1],
                             roughness=0.6, metallic=0.1, tex_format="JPEG")
        sc, _ = stone_texture(rng, 512)
        stone = pb.Material("esb_limestone", color=(0.62, 0.59, 0.53), roughness=0.85)
        roof = pb.Material("esb_roof", color=(0.13, 0.13, 0.125), roughness=0.95)
        shop = pb.Material("esb_storefront", color=(0.25, 0.23, 0.21), roughness=0.5)
    metal = pb.Material("esb_metal", color=(0.70, 0.71, 0.73), roughness=0.35, metallic=0.3)
    pave = pb.Material("esb_pavement", color=(0.58, 0.57, 0.55), roughness=0.9)
    green = pb.Material("esb_planting", color=(0.16, 0.27, 0.12), roughness=0.95)
    return dict(facade=facade, stone=stone, roof=roof, shop=shop, metal=metal, pave=pave, green=green)


def parapet(m, poly, z, h, t, mat, out=0.25):
    """a wall of thickness t around the edge of a roof at z, h high, its outside `out` beyond the facade"""
    outer = pb.offset_poly(poly, out)
    inner = pb.offset_poly(poly, out - t)
    m.prism(outer, z - 0.6, z + h, mat)
    m.prism(list(reversed(inner)), z, z + h, mat)
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        m.face([(outer[i][0], outer[i][1], z + h), (outer[j][0], outer[j][1], z + h),
                (inner[j][0], inner[j][1], z + h), (inner[i][0], inner[i][1], z + h)], mat)


def piers(m, poly, z0, z1, mat, width=1.2, depth=0.45, corner=1.7):
    """limestone piers on the bay lines of every face (the facade texture has them flat at the same places) and
    corner blocks on the outer corners"""
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        length = math.hypot(bx - ax, by - ay)
        dx, dy = (bx - ax) / length, (by - ay) / length
        nx, ny = dy, -dx
        k = 1
        while k * BAY < length - BAY * 0.5:
            s = k * BAY
            cx, cy = ax + dx * s, ay + dy * s
            p = [(cx - dx * width / 2, cy - dy * width / 2), (cx + dx * width / 2, cy + dy * width / 2)]
            q = [(x + nx * depth, y + ny * depth) for x, y in p]
            m.prism([q[0], q[1], p[1], p[0]], z0, z1, mat, top=mat)
            k += 1
        # outer corner block at the start of the edge if the corner is convex
        (px, py) = poly[i - 1]
        cross = (ax - px) * (by - ay) - (ay - py) * (bx - ax)
        if cross > 0:
            e1 = ((ax - px), (ay - py))
            l1 = math.hypot(*e1)
            e1 = (e1[0] / l1, e1[1] / l1)
            n1 = (e1[1], -e1[0])
            c = corner / 2
            o = (ax + (nx + n1[0]) * (depth - c), ay + (ny + n1[1]) * (depth - c))
            sq = [(o[0] - c, o[1] - c), (o[0] + c, o[1] - c), (o[0] + c, o[1] + c), (o[0] - c, o[1] + c)]
            m.prism(sq, z0, z1, mat, top=mat)


def rooftop_boxes(m, rng, hx, hy, z, mat, count, avoid):
    for _ in range(count):
        for _try in range(20):
            w, d, h = rng.uniform(3, 8), rng.uniform(3, 6), rng.uniform(1.5, 3.5)
            x = rng.uniform(-hx + w / 2 + 2, hx - w / 2 - 2)
            y = rng.uniform(-hy + d / 2 + 2, hy - d / 2 - 2)
            if abs(x) - w / 2 > avoid[0] or abs(y) - d / 2 > avoid[1]:
                m.box(x - w / 2, x + w / 2, y - d / 2, y + d / 2, z, z + h, mat, skip=("-z",))
                break


def build_lod0(mt, rng):
    m = pb.Mesh("EmpireState", SCALE)
    F, S, R = mt["facade"], mt["stone"], mt["roof"]
    # pavement and planters on the rest of the squares (no face at the ground itself)
    px, py = (FOOT[0] / 2 - 0.0125) / SCALE, (FOOT[1] / 2 - 0.025) / SCALE
    m.box(-px, px, -py, py, 0.0, 0.35, mt["pave"], skip=("-z",))
    hx, hy = PODIUM[0], PODIUM[1]
    for sx in (-1, 1):
        x = sx * (hx + 1.75)
        for k in range(4):
            for sy in (-1, 1):
                y = sy * (12 + k * 13)
                m.box(x - 1.2, x + 1.2, y - 2.5, y + 2.5, 0.35, 1.1, S, skip=("-z",))
                m.box(x - 0.9, x + 0.9, y - 2.2, y + 2.2, 1.1, 1.5, mt["green"], skip=("-z",))
    # podium: ground floor shops, offices above, cornice
    rect = pb.rect_notched(hx, hy, 0)
    m.prism(rect, 0.35, 7.5, mt["shop"])
    m.prism(pb.offset_poly(rect, 0.4), 7.5, 8.4, S, top=S)
    m.prism(rect, 8.4, PODIUM[4], F, top=R)
    parapet(m, rect, PODIUM[4], 1.3, 0.6, S)
    # entrances: 5th Avenue (+x) and 34th Street (+y)
    for axis in ("x", "y"):
        w, hgt, d = 9.0, 13.0, 1.2
        if axis == "x":
            m.box(hx, hx + d, -w / 2 - 1.5, w / 2 + 1.5, 0.35, hgt + 1.5, S, skip=("-x", "-z"))
            m.box(hx + d, hx + d + 0.05, -w / 2, w / 2, 0.35, hgt, mt["shop"], skip=("-x", "-z"))
        else:
            m.box(-w / 2 - 1.5, w / 2 + 1.5, hy, hy + d, 0.35, hgt + 1.5, S, skip=("-y", "-z"))
            m.box(-w / 2, w / 2, hy + d, hy + d + 0.05, 0.35, hgt, mt["shop"], skip=("-y", "-z"))
    rooftop_boxes(m, rng, hx, hy, PODIUM[4], R, 6, (TIERS[0][0] + 1, TIERS[0][1] + 1))
    # the tower tiers with their piers, roofs and parapets
    for k, (thx, thy, notch, z0, z1) in enumerate(TIERS):
        poly = pb.rect_notched(thx, thy, notch)
        m.prism(poly, z0, z1, F, top=R)
        piers(m, poly, z0, z1, S)
        parapet(m, poly, z1, 1.2, 0.5, S, out=0.6)
        if k + 1 < len(TIERS):
            nx, ny = TIERS[k + 1][0], TIERS[k + 1][1]
            rooftop_boxes(m, rng, thx - notch, thy - notch, z1, R, 3 if k < 3 else 1, (nx + 1, ny + 1))
    # 86th floor: observatory core, the terrace parapet is the last tier's
    z = TIERS[-1][4]
    core = pb.rect_notched(10.5, 13.5, 1.5)
    m.prism(core, z, z + 7.5, F, top=R)
    piers(m, core, z, z + 7.5, S, width=1.0, depth=0.35, corner=1.4)
    z += 7.5
    # mooring mast: base with four stepped buttresses, chamfered shaft with metal fins, 102nd floor drum, antenna
    m.prism(pb.rect_notched(8.25, 10.5, 2.0), z, z + 6.0, S, top=S)
    for ang in range(4):
        for step, (w, d, h) in enumerate([(5.0, 6.0, 3.0), (4.0, 4.0, 6.5), (3.0, 2.2, 10.0)]):
            ca, sa = round(math.cos(ang * math.pi / 2)), round(math.sin(ang * math.pi / 2))
            ex = (8.25 if ca else 10.5)
            cx, cy = ca * (ex + d / 2 - 0.5), sa * (ex + d / 2 - 0.5)
            hw = w / 2
            if ca:
                m.box(cx - d / 2, cx + d / 2, -hw, hw, z, z + h, S, skip=("-z",))
            else:
                m.box(-hw, hw, cy - d / 2, cy + d / 2, z, z + h, S, skip=("-z",))
    z += 6.0
    shaft = pb.rect_notched(7.5, 7.5, 2.4)
    top = z + 27.0
    m.prism(shaft, z, top, F, top=S)
    for (x, y) in shaft:
        m.box(x - 0.45, x + 0.45, y - 0.45, y + 0.45, z, top + 2.0, mt["metal"], skip=("-z",))
    for ang in range(4):
        ca, sa = round(math.cos(ang * math.pi / 2)), round(math.sin(ang * math.pi / 2))
        for off in (-2.6, 0.0, 2.6):
            if ca:
                x, y = ca * 7.5, off
                m.box(x - 0.5 if ca > 0 else x - 0.7, x + 0.7 if ca > 0 else x + 0.5, y - 0.3, y + 0.3, z, top + (1.5 if off == 0 else 0.6),
                      mt["metal"], skip=("-z",))
            else:
                x, y = off, sa * 7.5
                m.box(x - 0.3, x + 0.3, y - 0.5 if sa > 0 else y - 0.7, y + 0.7 if sa > 0 else y + 0.5, z, top + (1.5 if off == 0 else 0.6),
                      mt["metal"], skip=("-z",))
    z = top
    m.prism(pb.rect_notched(8.6, 8.6, 2.8), z, z + 1.6, S, top=S)
    z += 1.6
    m.cylinder((0, 0, z), 5.6, 9.5, 16, F, caps=(False, False), phase=math.pi / 16)
    m.cylinder((0, 0, z + 9.5), 6.0, 1.2, 16, S, caps=(True, True), phase=math.pi / 16)
    z += 10.7
    m.cylinder((0, 0, z), 4.2, 3.0, 16, S, caps=(False, False), r2=2.6, phase=math.pi / 16)
    z += 3.0
    m.cylinder((0, 0, z), 2.6, 8.0, 12, mt["metal"], caps=(False, True), r2=1.3)
    m.cylinder((0, 0, z + 8.0), 2.2, 0.5, 12, mt["metal"])
    z += 8.5
    m.cylinder((0, 0, z), 1.1, 14.0, 10, mt["metal"], caps=(False, True), r2=0.75)
    m.cylinder((0, 0, z + 14.0), 1.6, 0.6, 10, mt["metal"])
    z += 14.6
    m.cylinder((0, 0, z), 0.7, 443.0 - z, 8, mt["metal"], caps=(False, True), r2=0.18)
    return [m]


def build_lod1(mt):
    m = pb.Mesh("EmpireState_lod1", SCALE)
    F, S, R = mt["facade"], mt["stone"], mt["roof"]
    hx, hy = PODIUM[0], PODIUM[1]
    m.box(-hx, hx, -hy, hy, 0.35, 7.5, mt["shop"], skip=("-z", "+z"))
    m.box(-hx, hx, -hy, hy, 7.5, PODIUM[4], F, skip=("-z",), mats={"+z": R})
    for thx, thy, notch, z0, z1 in TIERS:
        m.box(-thx, thx, -thy, thy, z0, z1, F, skip=("-z",), mats={"+z": R})
    z = TIERS[-1][4]
    m.box(-10.5, 10.5, -13.5, 13.5, z, z + 7.5, F, skip=("-z",), mats={"+z": R})
    z += 7.5
    m.box(-8.25, 8.25, -10.5, 10.5, z, z + 6.0, S, skip=("-z",))
    z += 6.0
    m.box(-7.5, 7.5, -7.5, 7.5, z, z + 28.6, F, skip=("-z",), mats={"+z": S})
    z += 28.6
    m.cylinder((0, 0, z), 5.6, 13.7, 8, S, caps=(False, True), r2=3.0, phase=math.pi / 8)
    z += 13.7
    m.cylinder((0, 0, z), 2.0, 443.0 - z, 4, mt["metal"], caps=(False, False), r2=0.2, phase=math.pi / 4)
    return [m]


def main():
    a = pb.parse_args()
    pb.empty_scene()
    rng = np.random.default_rng(1931)
    mt = materials(a.lod, rng)
    meshes = build_lod0(mt, np.random.default_rng(34)) if a.lod == 0 else build_lod1(mt)
    for me in meshes:
        me.build()
    pb.export_glb(a.out)
    pb.report(meshes, a.out)


main()

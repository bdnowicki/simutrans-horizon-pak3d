# Metro car of the TMB class 6000 kind (a modern electric multiple unit) for the pak 3D: one car of 8/16 squares
# (0.5 squares long, front +X, origin in the middle on the rail surface). The body is in the company colour
# (material player1, the stripe player2), passenger windows light up at night (night_emissive).
#   blender -b --factory-startup -P scripts/tmb6000.py -- --out models/tmb6000_cab.glb --part cab [--lod 1]
#   --part cab: driving car (TMB_Class_6000, and TMB_Class_6000_Back, which the dashboard turns round at the end)
#   --part car: intermediate car (TMB_Class_6000_Car, TMB_Class_6000_Powered_Car)
# Proportions follow the dashboard's generated rail cars (rails at +-0.1 squares, floor 0.07, roof about 0.27).
# Author: bdnowicki. License: CC BY 4.0.
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pak3d_blender as pb  # noqa: E402

HALF = 0.243         # body ends (gangways reach 0.25)
X_NOSE = 0.150       # cab cars: where the cab begins
X_TIP = 0.247

# right half of the body section (y, z), bottom to top; the left half is mirrored
SECTION = [(0.000, 0.066), (0.100, 0.066), (0.108, 0.080), (0.112, 0.100), (0.112, 0.122), (0.112, 0.132), (0.112, 0.142),
           (0.109, 0.212), (0.107, 0.230), (0.099, 0.246), (0.084, 0.257), (0.058, 0.265), (0.030, 0.268)]
SMOOTH = [False, False, True, True, False, False, False, False, True, True, True, True, True]
# what each edge of the half section is: under, skirt, body, body, stripe, body, window band, body, cant, roof, roof, roof
BANDS = ["under", "under", "body", "body", "stripe", "body", "window", "body", "body", "roof", "roof", "roof"]
DOOR_BANDS = {2, 3, 4, 5, 6}   # edges a door covers (z 0.08 .. 0.212)


def materials(lod):
    return dict(
        body=pb.Material("player1", color=(0.93, 0.93, 0.92), roughness=0.38, metallic=0.05),
        stripe=pb.Material("player2", color=(0.78, 0.10, 0.12), roughness=0.4, metallic=0.05),
        window=pb.Material("night_emissive", color=(0.05, 0.06, 0.07), roughness=0.08, emissive=(1.0, 0.94, 0.80)),
        glass=pb.Material("tmb_windscreen", color=(0.03, 0.035, 0.045), roughness=0.05),
        black=pb.Material("tmb_black", color=(0.035, 0.035, 0.04), roughness=0.6),
        under=pb.Material("tmb_underframe", color=(0.10, 0.10, 0.11), roughness=0.7, metallic=0.3),
        roof=pb.Material("tmb_roof", color=(0.52, 0.53, 0.55), roughness=0.6, metallic=0.1),
        lamp=pb.Material("tmb_lamp", color=(0.95, 0.95, 0.9), roughness=0.2, emissive=(0.9, 0.88, 0.8)),
    )


def full_section(sec):
    """closed section, counter-clockwise seen from +X: right half bottom to top, then the left half top to bottom"""
    right = list(sec)
    left = [(-y, z) for y, z in reversed(sec)]
    return right + left


def edge_mats(mt, kind, cab_side=False, bands=None):
    """materials of the edges of the section strip (right half, top, left half) for a column of the given kind"""
    half = []
    for i, b in enumerate(bands or BANDS):
        if b == "window":
            m = mt["window"] if kind in ("window", "door") else mt["glass"] if kind == "cabwin" else mt["body"]
        elif b == "roof":
            m = mt["roof"]
        elif b == "under":
            m = mt["under"] if i == 0 else mt["body"] if cab_side else mt["under"]
        else:
            m = mt[b]
        half.append(m)
    # closed loop: right half edges 0..11, the top edge, left half edges 11..0
    return half + [mt["roof"]] + list(reversed(half))


def section_for(kind):
    """the section of a column: doors and windows are set in a little (their jambs show as dark lines)"""
    sec = list(SECTION)
    if kind == "door":
        sec = [(y - 0.0022, z) if 2 <= i <= 7 else (y, z) for i, (y, z) in enumerate(sec)]
    elif kind in ("window", "cabwin"):
        sec = [(y - 0.003, z) if i in (6, 7) else (y, z) for i, (y, z) in enumerate(sec)]
    return sec


def columns(x0, x1, doors, door_w=0.042, pillar=0.007):
    """columns along the side between x0 and x1: doors centred at `doors`, windows between, pillars around"""
    cols, x = [], x0
    for d in sorted(doors) + [None]:
        end = (d - door_w / 2) if d is not None else x1
        span = end - x
        if span > 3 * pillar:
            cols += [(x, x + pillar, "pillar"), (x + pillar, end - pillar, "window"), (end - pillar, end, "pillar")]
        elif span > 0:
            cols.append((x, end, "pillar"))
        if d is not None:
            cols.append((d - door_w / 2, d + door_w / 2, "door"))
            x = d + door_w / 2
    return cols


def body(m, mt, cols):
    full_smooth = SMOOTH + list(reversed(SMOOTH))
    prev = None
    for xa, xb, kind in cols:
        sec = section_for(kind)
        m.extrude_x(full_section(sec), xa, xb, edge_mats(mt, kind), smooth=full_smooth)
        # jambs where the section changes between columns: dark faces between the two outlines
        if prev is not None and prev != sec:
            jambs(m, mt, prev, sec, xa)
        prev = sec
    return prev


def jambs(m, mt, a, b, x):
    """step faces at x between the section a (columns before x) and b (after): towards +x where a is the outer one"""
    for side in (1, -1):
        for i in range(len(a) - 1):
            pa0, pa1, pb0, pb1 = a[i], a[i + 1], b[i], b[i + 1]
            if pa0 == pb0 and pa1 == pb1:
                continue
            outer_a = abs(pa0[0]) + abs(pa1[0]) > abs(pb0[0]) + abs(pb1[0])
            ring = [pa0, pa1, pb1, pb0] if outer_a else [pb0, pb1, pa1, pa0]
            pts = []
            for q in ring:
                if not pts or pts[-1] != q:
                    pts.append(q)
            if pts[0] == pts[-1]:
                pts.pop()
            if len(pts) < 3:
                continue
            pts = [(x, side * yy, zz) for yy, zz in pts]
            if outer_a == (side < 0):
                pts.reverse()
            m.face(pts, mt["black"])


def end_wall(m, mt, x, facing, sec, gangway=True):
    pts = [(x, y, z) for y, z in full_section(sec)[:-1]]
    if facing < 0:
        pts.reverse()
    m.face(pts, mt["body"])
    if gangway:
        x1 = x + facing * (0.25 - HALF)
        a, b = sorted((x, x1))
        m.box(a, b, -0.072, 0.072, 0.075, 0.238, mt["black"], skip=("-x" if facing > 0 else "+x",))


def bogies(m, mt, lod):
    for c in (-0.165, 0.165):
        m.box(c - 0.05, c + 0.05, -0.088, 0.088, 0.034, 0.062, mt["under"], skip=("+z",))
        if lod:
            continue
        for s in (-1, 1):
            m.box(c - 0.058, c + 0.058, s * 0.106 - 0.006, s * 0.106 + 0.006, 0.02, 0.05, mt["under"], skip=("+z",))
            for dx in (-0.032, 0.032):
                y0 = s * 0.094 if s > 0 else -0.106
                m.cylinder((c + dx, y0, 0.024), 0.024, 0.012, 10, mt["under"], axis="y", caps=(s < 0, s > 0))
            # springs / axle boxes
            for dx in (-0.032, 0.032):
                m.box(c + dx - 0.008, c + dx + 0.008, s * 0.114 - 0.004, s * 0.114 + 0.004, 0.018, 0.034, mt["black"], skip=("-z",))


def underframe(m, mt):
    for x0, x1, h in [(-0.11, -0.05, 0.03), (-0.04, 0.03, 0.026), (0.045, 0.11, 0.03)]:
        m.box(x0, x1, -0.078, 0.078, 0.066 - h, 0.066, mt["under"], skip=("+z",))


def roof_units(m, mt, cab):
    xs = (-0.14, 0.06) if cab else (-0.13, 0.13)
    for x in xs:
        m.box(x - 0.05, x + 0.05, -0.06, 0.06, 0.266, 0.284, mt["roof"], skip=("-z",))
        m.box(x - 0.042, x + 0.042, -0.05, 0.05, 0.284, 0.287, mt["under"], skip=("-z",))
    if cab:
        # single arm pantograph, lowered
        x = -0.04
        m.box(x - 0.03, x + 0.03, -0.04, 0.04, 0.267, 0.274, mt["under"], skip=("-z",))
        for s in (-1, 1):
            m.box(x - 0.006, x + 0.006, s * 0.03 - 0.003, s * 0.03 + 0.003, 0.274, 0.282, mt["black"], skip=("-z",))
        m.face([(x - 0.03, -0.004, 0.279), (x + 0.07, -0.004, 0.292), (x + 0.07, 0.004, 0.292), (x - 0.03, 0.004, 0.279)][::-1], mt["black"])
        m.face([(x - 0.03, -0.004, 0.279), (x + 0.07, -0.004, 0.292), (x + 0.07, 0.004, 0.292), (x - 0.03, 0.004, 0.279)], mt["black"])
        m.box(x + 0.065, x + 0.075, -0.045, 0.045, 0.29, 0.295, mt["black"])


def xf(y, z):
    """front surface of the cab: raked windscreen, rounded in plan"""
    t = min(1.0, abs(y) / 0.112)
    plan = 0.024 * t ** 2.4
    if z <= 0.135:
        base = X_TIP - 0.005 * (0.135 - z) / 0.069
    elif z <= 0.246:
        base = X_TIP - 0.030 * (z - 0.135) / 0.111
    else:
        base = X_TIP - 0.030 - 0.026 * (z - 0.246) / 0.022
    return base - plan


def nose(m, mt, lod, sec, bands):
    half_w = {z: y for y, z in sec[1:]}
    # side surfaces from the end of the passenger part to the front
    full = full_section(sec)
    mats = edge_mats(mt, "cabwin", cab_side=True, bands=bands)
    for i in range(len(full) - 1):
        (ay, az), (by, bz) = full[i], full[i + 1]
        pts = [(X_NOSE, ay, az), (X_NOSE, by, bz), (xf(by, bz), by, bz), (xf(ay, az), ay, az)]
        m.face(pts, mats[i])
    # the front itself: a grid over the section, materials by area
    zs = [z for _, z in sec[1:]]
    us = [-1, -0.93, -0.80, -0.62, -0.42, -0.2, 0, 0.2, 0.42, 0.62, 0.80, 0.93, 1] if lod == 0 else [-1, -0.93, -0.8, -0.42, 0.42, 0.8, 0.93, 1]
    for k in range(len(zs) - 1):
        z0, z1 = zs[k], zs[k + 1]
        for i in range(len(us) - 1):
            u0, u1 = us[i], us[i + 1]
            zc, uc = (z0 + z1) / 2, abs((u0 + u1) / 2)
            if 0.142 <= zc <= 0.246 and uc < 0.80:
                mat = mt["glass"]
            elif 0.132 <= zc <= 0.257 and uc < 0.93:
                mat = mt["black"]
            elif 0.100 <= zc <= 0.122 and 0.42 <= uc <= 0.80:
                mat = mt["lamp"]
            elif zc < 0.08:
                mat = mt["under"]
            elif zc < 0.132:
                mat = mt["stripe"]
            else:
                mat = mt["body"]
            p = []
            for (u, z) in ((u0, z0), (u1, z0), (u1, z1), (u0, z1)):
                y = u * half_w[z]
                p.append((xf(y, z), y, z))
            m.face(p, mat)
    if lod == 0:
        # coupler and anticlimber
        m.box(X_TIP - 0.012, X_TIP + 0.004, -0.02, 0.02, 0.062, 0.084, mt["under"])
        m.box(X_TIP - 0.01, X_TIP + 0.001, -0.075, 0.075, 0.084, 0.092, mt["black"], skip=("-x",))


# coarse section: bottom centre, bottom, skirt, stripe, window band, cant, roof
SIMPLE = [(0.0, 0.066), (0.104, 0.066), (0.111, 0.085), (0.112, 0.122), (0.112, 0.132), (0.112, 0.142), (0.109, 0.212),
          (0.106, 0.234), (0.090, 0.256), (0.030, 0.268)]
SIMPLE_BANDS = ["under", "body", "body", "stripe", "body", "window", "body", "roof", "roof"]
LIFT = 0.0015   # panes and lines stand this far off the body


def side_y(z):
    """half width of the coarse body at height z (window band and below)"""
    if z <= 0.142:
        return 0.112
    return 0.112 - 0.003 * (z - 0.142) / 0.070


def panes(m, mat, spans, z0=0.147, z1=0.207):
    for a, b in spans:
        for s in (1, -1):
            pts = [(a, s * (side_y(z0) + LIFT), z0), (b, s * (side_y(z0) + LIFT), z0), (b, s * (side_y(z1) + LIFT), z1),
                   (a, s * (side_y(z1) + LIFT), z1)]
            m.face(pts[::-1] if s > 0 else pts, mat)


def door_line(m, mat, x, w=0.0025):
    for s in (1, -1):
        for z0, z1 in ((0.088, 0.142), (0.142, 0.213)):
            pts = [(x - w / 2, s * (side_y(z0) + LIFT), z0), (x + w / 2, s * (side_y(z0) + LIFT), z0),
                   (x + w / 2, s * (side_y(z1) + LIFT), z1), (x - w / 2, s * (side_y(z1) + LIFT), z1)]
            m.face(pts[::-1] if s > 0 else pts, mat)


def build(part, lod, mt):
    m = pb.Mesh("TMB6000_" + part + ("_lod1" if lod else ""))
    sec, bands = SECTION, BANDS
    if lod == 0:
        if part == "cab":
            cols = columns(-HALF, X_NOSE - 0.035, [-0.185, -0.06, 0.065]) + [(X_NOSE - 0.035, X_NOSE - 0.03, "pillar"),
                                                                          (X_NOSE - 0.03, X_NOSE - 0.004, "cabwin"),
                                                                          (X_NOSE - 0.004, X_NOSE, "pillar")]
        else:
            cols = columns(-HALF, HALF, [-0.1875, -0.0625, 0.0625, 0.1875])
        body(m, mt, cols)
        bogies(m, mt, lod)
        underframe(m, mt)
        roof_units(m, mt, part == "cab")
    else:
        # coarse car (what the iso view shows even at its closest zoom): one body, windows and door lines laid on it
        x1 = X_NOSE if part == "cab" else HALF
        sec, bands = SIMPLE, SIMPLE_BANDS
        sm = [False, False, False, False, False, False, False, True, True, True]
        m.extrude_x(full_section(sec), -HALF, x1, edge_mats(mt, "pillar", bands=bands), smooth=sm + list(reversed(sm)))
        if part == "cab":
            doors, cols = [-0.185, -0.06, 0.065], columns(-HALF, X_NOSE - 0.035, [-0.185, -0.06, 0.065])
            panes(m, mt["glass"], [(X_NOSE - 0.03, X_NOSE - 0.004)])
        else:
            doors = [-0.1875, -0.0625, 0.0625, 0.1875]
            cols = columns(-HALF, HALF, doors)
        panes(m, mt["window"], [(a, b) for a, b, k in cols if k == "window"] + [(d - 0.013, d + 0.013) for d in doors])
        for d in doors:
            for e in (d - 0.021, d + 0.021):
                door_line(m, mt["black"], e)
        bogies(m, mt, lod)
        m.box(-0.11, 0.11, -0.078, 0.078, 0.038, 0.066, mt["under"], skip=("+z",))
        for x in ((-0.14, 0.06) if part == "cab" else (-0.13, 0.13)):
            m.box(x - 0.05, x + 0.05, -0.06, 0.06, 0.266, 0.284, mt["roof"], skip=("-z",))
    end_wall(m, mt, -HALF, -1, sec)
    if part == "cab":
        nose(m, mt, lod, sec, bands)
    else:
        end_wall(m, mt, HALF, 1, sec)
    return m


def main():
    a = pb.parse_args(lambda ap: ap.add_argument("--part", choices=("cab", "car"), default="cab"))
    pb.empty_scene()
    mt = materials(a.lod)
    m = build(a.part, a.lod, mt)
    m.build()
    pb.export_glb(a.out)
    pb.report([m], a.out)


main()

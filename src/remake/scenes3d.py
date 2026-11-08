#!/usr/bin/env python3
"""Tujuh adegan 3D KlikTahu — geometri asli, kamera bergerak, komponen bergerak."""
from __future__ import annotations

import math

import numpy as np

from geom3d import (Camera, M, Scene, annulus, box, cable, cyl, disc, fan_blades,
                    norm, pins, plane, render)

MAT = {
    "floor":    M((24, 33, 50), 0.04, 18),
    "shadow":   M((4, 8, 18), alpha=0.42),
    "case":     M((44, 52, 66), 0.55, 30, edge=0.30),
    "case2":    M((28, 34, 44), 0.40, 26),
    "alu":      M((132, 144, 160), 0.85, 46, edge=0.32),
    "alu_dark": M((72, 82, 98), 0.80, 40, edge=0.22),
    "steel":    M((100, 112, 128), 0.78, 38, edge=0.22),
    "plastic":  M((24, 28, 36), 0.30, 22),
    "black":    M((12, 15, 21), 0.25, 24),
    "glass":    M((90, 130, 170), 0.30, 60, alpha=0.10, edge=0.28),
    "pcb":      M((20, 42, 42), 0.22, 20, edge=0.18),
    "pcb2":     M((28, 56, 54), 0.25, 22),
    "trace":    M((56, 104, 98), 0.45, 30, emissive=0.24),
    "gold":     M((206, 166, 80), 0.90, 52),
    "blade":    M((52, 62, 76), 0.55, 28, edge=0.18),
    "blade2":   M((64, 76, 92), 0.60, 30, edge=0.18),
    "screen":   M((16, 22, 34), 0.12, 60),
    "screen_on":M((38, 116, 202), 0.15, 50, emissive=0.58),
    "window":   M((128, 196, 250), 0.10, 50, emissive=0.64),
    "white":    M((236, 244, 255), 0.20, 30, emissive=0.38),
}
ACCENT = {"cyan": (70, 208, 244), "yellow": (255, 199, 32), "green": (58, 222, 142),
          "blue": (70, 138, 255), "amber": (255, 166, 56)}


def led_mat(color, on):
    return M(color, 0.15, 30, emissive=0.92 * max(0.0, min(1.0, on)))


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def studio(s, cx=0.0, cz=0.0, rx=1.8, rz=1.4):
    s.add(plane((0, -0.065, 0), (1, 0, 0), (0, 0, 1), 18, 18), MAT["floor"], pre=True)
    pts = [[cx + rx * math.cos(i * 2 * math.pi / 20), -0.058,
            cz + rz * math.sin(i * 2 * math.pi / 20)] for i in range(28)]
    s.add([np.array(pts, np.float32)], MAT["shadow"], pre=True)


def add_fan(s, c, a, r, phase, blades=7, blade=None, hub=None, ring=None):
    a = norm(a)
    c = np.asarray(c, np.float32)
    bm = blade or MAT["blade"]
    hm = hub or MAT["alu_dark"]
    rm = ring or MAT["steel"]
    s.add(fan_blades(c, a, r * 0.24, r * 0.90, blades, phase, skew=r * 0.17), bm, post=True)
    s.add(cyl(c, a, r * 0.22, r * 0.11, n=11), hm, post=True)
    s.add(annulus(c + a * (r * 0.06), a, r * 0.19, r * 0.235, n=11), rm, post=True)
    s.add(annulus(c, a, r * 0.94, r * 1.13, n=12), rm)
    s.add(disc(c - a * (r * 0.055), a, r * 0.94, n=12), MAT["black"])


def add_monitor(s, c, on=False, u=0.0, w=2.45, h=1.48):
    x, y, z = c
    s.add(box((x, y, z), (w + 0.10, h + 0.10, 0.09)), MAT["plastic"])
    s.add(plane((x, y, z + 0.049), (1, 0, 0), (0, 1, 0), w, h),
          MAT["screen_on"] if on else MAT["screen"])
    s.add(box((x, y - h / 2 - 0.28, z), (0.16, 0.58, 0.14)), MAT["alu_dark"])
    s.add(box((x, y - h / 2 - 0.57, z + 0.06), (0.88, 0.05, 0.52)), MAT["alu_dark"])
    if on:
        wins = [(-0.48, 0.24, 0.86, 0.58), (0.42, 0.28, 0.92, 0.50),
                (0.10, -0.34, 0.62, 0.34)]
        for k, (wx, wy, ww, wh) in enumerate(wins):
            if u > 0.50 + k * 0.09:
                a = clamp((u - 0.50 - k * 0.09) / 0.10)
                s.add(plane((x + wx, y + wy, z + 0.051), (1, 0, 0), (0, 1, 0),
                            ww, wh * a), MAT["window"])


def add_tower(s, phase, led, press=0.0):
    s.add(box((0, 1.02, -0.88), (1.10, 2.04, 0.05)), MAT["case2"])
    s.add(box((-0.53, 1.02, 0), (0.05, 2.04, 1.80)), MAT["case2"])
    s.add(box((0, 2.02, 0), (1.10, 0.05, 1.80)), MAT["case"])
    s.add(box((0, 0.02, 0), (1.10, 0.05, 1.80)), MAT["case"])
    s.add(box((0, 1.02, 0.88), (1.10, 2.04, 0.05)), MAT["case2"])
    for x in (-0.53, 0.53):
        for z in (-0.88, 0.88):
            s.add(box((x, 1.02, z), (0.06, 2.04, 0.06)), MAT["alu_dark"])

    for y in (0.47, 1.02, 1.57):
        add_fan(s, (0, y, 0.915), (0, 0, 1), 0.255, phase + y * 2.0)

    s.add(box((0, 0.30, -0.06), (1.00, 0.56, 1.58)), MAT["case2"])
    s.add(box((-0.47, 1.40, -0.08), (0.035, 1.16, 1.30)), MAT["pcb"])
    for i in range(9):
        s.add(box((-0.446, 1.16, -0.60 + i * 0.13), (0.006, 0.30, 0.013)), MAT["trace"])
    for i in range(4):
        s.add(box((-0.425, 1.62, -0.44 + i * 0.13), (0.055, 0.52, 0.035)), MAT["alu_dark"])
        s.add(box((-0.425, 1.37, -0.44 + i * 0.13), (0.058, 0.035, 0.038)), MAT["gold"])
    s.add(box((-0.39, 1.52, 0.20), (0.19, 0.36, 0.36)), MAT["alu_dark"])
    add_fan(s, (-0.283, 1.52, 0.20), (1, 0, 0), 0.125, phase * 1.3, blades=7)
    s.add(box((-0.24, 0.98, 0.05), (0.48, 0.13, 1.12)), MAT["alu_dark"])
    s.add(box((-0.24, 0.908, 0.05), (0.44, 0.014, 1.04)), MAT["gold"])

    s.add(plane((0.545, 1.02, 0), (0, 1, 0), (0, 0, 1), 1.72, 1.96), MAT["glass"])
    for z in (-0.87, 0.87):
        s.add(box((0.552, 1.02, z), (0.03, 1.96, 0.05)), MAT["alu_dark"])
    for y in (0.045, 1.995):
        s.add(box((0.552, y, 0), (0.03, 0.05, 1.74)), MAT["alu_dark"])

    dy = -0.018 * press
    s.add(cyl((0.0, 2.056 + dy, 0.62), (0, 1, 0), 0.078, 0.032, n=12), MAT["alu"])
    s.add(annulus((0.0, 2.075 + dy, 0.62), (0, 1, 0), 0.052, 0.075, n=12),
          led_mat((70, 208, 244), led))
    s.add(cyl((0.0, 2.077 + dy, 0.62), (0, 1, 0), 0.028, 0.006, n=12),
          led_mat((196, 240, 255), led))


# ---------------------------------------------------------------- adegan 1
def scene_case(u, t):
    s = Scene(top=(7, 12, 25), bottom=(20, 30, 49))
    studio(s, 0.0, 0.0, 1.55, 1.35)
    led = smooth((u - 0.06) / 0.16)
    press = max(0.0, 1.0 - u * 14)
    add_tower(s, t * 2.6 + 0.25, led, press)
    add_monitor(s, (-1.98, 1.24, -0.72), on=False, w=1.95, h=1.20)
    cam = Camera((0.0, 1.03, -0.05), 0.96 + 0.16 * ease(u), 0.16 - 0.05 * u,
                 6.55 - 0.75 * ease(u), fov=40)
    return s, cam


# ---------------------------------------------------------------- adegan 2
def scene_psu(u, t):
    s = Scene(top=(8, 13, 25), bottom=(23, 30, 44))
    studio(s, 0.20, 0.0, 1.75, 1.30)
    phase = t * 3.0
    s.add(box((0, 0.46, 0), (1.62, 0.86, 1.42)), MAT["case"])
    s.add(box((0, 0.46, 0.715), (1.54, 0.78, 0.02)), MAT["case2"])
    s.add(box((0, 0.895, 0), (1.55, 0.02, 1.35)), MAT["case2"])
    add_fan(s, (0, 0.912, 0), (0, 1, 0), 0.44, phase, blades=9, blade=MAT["blade2"])
    s.add(annulus((0, 0.924, 0), (0, 1, 0), 0.30, 0.325, n=16), MAT["steel"])
    s.add(annulus((0, 0.924, 0), (0, 1, 0), 0.155, 0.175, n=16), MAT["steel"])
    s.add(box((0, 0.46, -0.718), (1.30, 0.66, 0.02)), MAT["black"])
    for i in range(6):
        s.add(box((-0.55 + i * 0.22, 0.46, -0.732), (0.13, 0.34, 0.012)), MAT["alu_dark"])

    for k in range(3):
        z = -0.30 + k * 0.28
        s.add(cable([(0.78, 0.46 + 0.10 * k, z), (1.15, 0.50 + 0.12 * k, z + 0.06),
                     (1.45, 0.36 + 0.06 * k, z - 0.10), (1.62, 0.30, z - 0.28)],
                    r=0.026, n=6), MAT["black"])
    s.add(box((1.70, 0.30, -0.28), (0.20, 0.30, 0.62)), MAT["plastic"])
    s.add(pins((1.705, 0.456, -0.28), (1, 0, 0), (0, 0, 1), 0.16, 0.54, 2, 10, 0.045),
          MAT["gold"])
    if u > 0.42:
        s.add(annulus((1.705, 0.462, -0.28), (0, 1, 0), 0.10, 0.13, n=12),
              led_mat((255, 190, 60), smooth((u - 0.42) / 0.18)))
    cam = Camera((0.55, 0.52, 0), -0.38 + 0.72 * ease(u), 0.48 - 0.14 * u,
                 7.10 - 0.80 * ease(u), fov=41)
    return s, cam


# ---------------------------------------------------------------- adegan 3
def scene_cpu(u, t):
    s = Scene(top=(7, 13, 26), bottom=(18, 31, 46))
    studio(s, 0.0, 0.0, 2.10, 2.00)
    s.add(box((0, 0.02, 0), (2.05, 0.07, 2.05)), MAT["pcb"])
    for i in range(14):
        s.add(box((-0.90 + i * 0.15, 0.058, -0.88), (0.012, 0.006, 0.72)), MAT["trace"])
        s.add(box((0.62, 0.058, -0.84 + i * 0.15), (0.34, 0.006, 0.012)), MAT["trace"])

    s.add(box((0, 0.105, 0), (1.52, 0.10, 1.52)), MAT["plastic"])
    s.add(box((0, 0.158, 0), (1.26, 0.008, 1.26)), MAT["pcb2"])
    s.add(pins((0, 0.164, 0), (1, 0, 0), (0, 0, 1), 1.16, 1.16, 15, 15, 0.056),
          MAT["gold"])
    for x in (-0.76, 0.76):
        s.add(box((x, 0.18, 0), (0.10, 0.13, 1.55)), MAT["alu_dark"])
    for z in (-0.76, 0.76):
        s.add(box((0, 0.18, z), (1.55, 0.13, 0.10)), MAT["alu_dark"])

    ang = -1.30 * ease(clamp((u - 0.04) / 0.50))
    cover = box((0, 0, 0), (0.94, 0.022, 0.94))
    s.add(_hinge(cover, ang), MAT["alu"])
    s.add(box((0, 0.24, -0.79), (0.30, 0.05, 0.09)), MAT["steel"])

    s.add(box((1.18, 0.11, -0.66), (0.42, 0.13, 0.32)), MAT["black"])
    for i in range(6):
        s.add(box((1.00 + i * 0.085, 0.075, -0.66), (0.045, 0.02, 0.34)), MAT["gold"])
    for x, z in [(-0.82, -0.78), (-0.82, 0.78), (0.82, -0.82), (0.82, 0.82)]:
        s.add(cyl((x, 0.16, z), (0, 1, 0), 0.10, 0.26, n=12), MAT["alu_dark"])
    cam = Camera((0, 0.10, 0), 0.34 + 0.42 * ease(u), 0.98 - 0.34 * u,
                 5.20 - 0.60 * ease(u), fov=40)
    return s, cam


def _hinge(polys, ang):
    """Engsel di z=-0.70; tutup soket terangkat memutar sumbu X."""
    from geom3d import rotmat
    R = rotmat(rx=ang)
    pivot = np.array([0, 0.25, -0.47], np.float32)
    lip = np.array([0, 0, 0.47], np.float32)
    return [(np.asarray(p, np.float32) + lip) @ R.T + pivot for p in polys]


# ---------------------------------------------------------------- adegan 4
def scene_post(u, t):
    s = Scene(top=(8, 14, 27), bottom=(19, 32, 45))
    studio(s, 0.0, 0.0, 2.05, 1.85)
    s.add(box((0, 0.04, 0), (2.75, 0.08, 2.35)), MAT["pcb"])
    for i in range(11):
        s.add(box((-1.24 + i * 0.24, 0.083, -1.02), (0.012, 0.006, 0.78)), MAT["trace"])
    for i in range(8):
        s.add(box((-0.30, 0.083, -1.00 + i * 0.24), (1.90, 0.006, 0.012)), MAT["trace"])

    s.add(box((-0.42, 0.22, -0.62), (0.86, 0.38, 0.86)), MAT["alu_dark"])
    add_fan(s, (-0.42, 0.425, -0.62), (0, 1, 0), 0.31, t * 2.4, blades=7)
    for i in range(4):
        s.add(box((0.38 + i * 0.17, 0.10, -0.30), (0.10, 0.05, 1.32)), MAT["black"])
        s.add(box((0.38 + i * 0.17, 0.42, -0.30), (0.085, 0.62, 1.20)), MAT["alu_dark"])
        s.add(box((0.38 + i * 0.17, 0.115, -0.30), (0.088, 0.026, 1.20)), MAT["gold"])
        s.add(box((0.38 + i * 0.17, 0.745, -0.30), (0.09, 0.02, 1.18)),
              led_mat(ACCENT["green"], 0.25 + 0.5 * u))

    s.add(box((-0.48, 0.28, 0.62), (1.62, 0.34, 0.52)), MAT["alu"])
    for x in (-0.88, 0.02):
        add_fan(s, (x, 0.462, 0.62), (0, 1, 0), 0.20, t * 3.0, blades=9)
    s.add(box((-0.48, 0.10, 0.62), (1.50, 0.02, 0.44)), MAT["gold"])

    s.add(box((1.22, 0.10, 0.92), (0.30, 0.16, 0.30)), MAT["black"])
    for i in range(4):
        on = smooth((u - 0.12 - i * 0.16) / 0.14)
        s.add(box((1.02, 0.187, 0.62 + i * 0.20), (0.10, 0.012, 0.09)),
              led_mat(ACCENT["green"], on) if on > 0.25 else led_mat((210, 70, 70), 0.55))
    cam = Camera((0.05, 0.30, 0), 0.48 + 0.48 * ease(u), 0.80 - 0.24 * u,
                 6.35 - 0.70 * ease(u), fov=41)
    return s, cam


# ---------------------------------------------------------------- adegan 5
def scene_ram(u, t):
    s = Scene(top=(8, 13, 27), bottom=(19, 31, 50))
    studio(s, 0.0, 0.0, 2.20, 1.55)
    s.add(box((0, 0.04, 0), (2.45, 0.08, 1.60)), MAT["pcb"])
    for i in range(7):
        s.add(box((-1.00, 0.083, -0.58 + i * 0.18), (1.55, 0.006, 0.012)), MAT["trace"])
    for i in range(4):
        s.add(box((0.20 + i * 0.28, 0.083, 0.62), (0.012, 0.006, 0.60)), MAT["trace"])

    s.add(box((-0.62, 0.12, -0.12), (1.48, 0.045, 0.44)), MAT["pcb2"])
    s.add(box((-1.40, 0.12, -0.12), (0.16, 0.048, 0.44)), MAT["gold"])
    for i in range(3):
        s.add(box((-0.92 + i * 0.42, 0.152, -0.12), (0.32, 0.022, 0.34)), MAT["black"])
    s.add(box((-0.62, 0.157, -0.12), (1.00, 0.008, 0.26)), MAT["white"])

    for i in range(4):
        drop = 0.55 * (1 - ease(clamp((u - 0.22 - i * 0.055) / 0.30)))
        x = 0.34 + i * 0.29
        s.add(box((x, 0.10, 0), (0.105, 0.05, 1.42)), MAT["black"])
        s.add(box((x, 0.45 + drop, 0), (0.09, 0.64, 1.20)), MAT["alu_dark"])
        s.add(box((x, 0.79 + drop, 0), (0.095, 0.028, 1.18)),
              led_mat(ACCENT["blue"], 0.30 + 0.4 * u))
        s.add(pins((x, 0.135 + drop, 0), (1, 0, 0), (0, 0, 1), 0.06, 1.20, 1, 16, 0.045),
              MAT["gold"])
    cam = Camera((0.15, 0.34, 0), 0.26 + 0.32 * ease(u), 0.68 - 0.22 * u,
                 7.80 - 0.85 * ease(u), fov=40)
    return s, cam


# ---------------------------------------------------------------- adegan 6
def scene_gpu(u, t):
    s = Scene(top=(7, 12, 24), bottom=(21, 30, 47))
    studio(s, 0.0, -0.25, 2.15, 1.45)
    on = u > 0.48
    add_monitor(s, (0, 1.32, -1.15), on=on, u=u, w=2.85, h=1.68)
    s.add(box((0, 1.02, 0.48), (2.55, 0.60, 0.30)), MAT["alu"])
    for x in (-0.60, 0.60):
        add_fan(s, (x, 1.02, 0.648), (0, 0, 1), 0.245, t * 3.2 + x, blades=9)
    s.add(box((0, 0.705, 0.48), (1.55, 0.045, 0.24)), MAT["gold"])
    s.add(box((0, 1.335, 0.48), (2.55, 0.035, 0.30)), MAT["alu_dark"])
    s.add(box((1.24, 1.02, 0.48), (0.06, 0.56, 0.34)), MAT["steel"])
    cam = Camera((0, 1.15, -0.30), 0.50 - 0.16 * u, 0.14 - 0.05 * u,
                 7.60 - 0.90 * ease(u), fov=42)
    return s, cam


# ---------------------------------------------------------------- adegan 7
def scene_loop(u, t):
    s = Scene(top=(7, 12, 25), bottom=(21, 31, 50))
    studio(s, 0.0, 0.0, 1.60, 1.40)
    led = 0.55 + 0.45 * math.sin(t * 2.2) ** 2
    add_tower(s, t * 2.6 + 0.25, led, 0.0)
    add_monitor(s, (-1.98, 1.24, -0.72), on=True, u=1.0, w=1.95, h=1.20)
    cam = Camera((0.0, 1.03, -0.05), 1.10 - 0.58 * ease(u), 0.17 + 0.08 * u,
                 6.30 + 0.60 * ease(u), fov=40)
    return s, cam


BUILDERS = {
    "case": scene_case, "psu": scene_psu, "cpu": scene_cpu, "post": scene_post,
    "ram": scene_ram, "gpu": scene_gpu, "loop": scene_loop,
}


def build(name, u, t, W=1080, H=1920, ss=1.5):
    s, cam = BUILDERS[name](clamp(u), t)
    return render(s, cam, W, H, ss)

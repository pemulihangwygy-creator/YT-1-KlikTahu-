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
    "screen_on":M((24, 68, 136), 0.12, 50, emissive=0.30),
    "window":   M((128, 196, 250), 0.10, 50, emissive=0.64),
    "white":    M((236, 244, 255), 0.20, 30, emissive=0.38),
    "chrome":   M((186, 198, 214), 0.95, 62, edge=0.20),
    "copper":   M((190, 118, 66), 0.88, 42),
    "chip":     M((26, 32, 38), 0.30, 26),
    "silk":     M((188, 198, 186), 0.18, 18, emissive=0.16),
    "smd":      M((22, 26, 30), 0.28, 22),
    "rubber":   M((18, 21, 27), 0.22, 18),
    "led_blue": M((56, 148, 255), 0.15, 30, emissive=0.88),
    "silver2":  M((176, 188, 204), 0.92, 58, edge=0.26),
    "navy":     M((30, 46, 72), 0.35, 30),
    "cream":    M((214, 218, 208), 0.22, 22, emissive=0.12),
    "floor":    M((17, 24, 39), 0.14, 28),
    "grid":     M((38, 52, 76), 0.28, 26, emissive=0.06),
    "wall":     M((13, 20, 36), 0.06, 18),
    "wall2":    M((19, 28, 47), 0.06, 18),
    "key":      M((36, 44, 58), 0.20, 22),
    "key_alt":  M((46, 68, 92), 0.26, 24),
    "key_hi":   M((226, 178, 40), 0.35, 30, emissive=0.22),
    "coffee":   M((48, 31, 22), 0.10, 20),
    "desk":     M((32, 42, 60), 0.30, 32),
    "panel":    M((34, 49, 72), 0.05, 18, emissive=0.16),
    "panel2":   M((58, 46, 42), 0.05, 18, emissive=0.12),
    "port":     M((8, 11, 17), 0.10, 20),
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


YAW = (0.0, 0.13, -0.09, 0.03)
PITCH = (0.0, -0.05, 0.05, 0.0)
DIST = (0.0, -0.30, 0.18, -0.08)


def beat(u, keys, t=0.0):
    """Tiga komposisi kamera per bab + parallax sinambung (bukan potongan kasar)."""
    p = u * 3.0
    i = min(2, int(p))
    f = p - i
    base = keys[i] + (keys[i + 1] - keys[i]) * smooth(f)
    return base + 0.014 * math.sin(t * 0.83 + 1.1) + 0.007 * math.sin(t * 0.37)


def cine_fov(base, t, u=0.0):
    """Dolly-zoom halus: fov bernapas mengikuti waktu, menyempit di akhir bab."""
    return (base + 1.35 * math.sin(t * 0.31 + 0.7) + 0.45 * math.sin(t * 0.13)
            - 0.9 * ease(u))


def screw(s, c, axis, r=0.032):
    a = norm(axis)
    c = np.asarray(c, np.float32)
    s.add(cyl(c, a, r, r * 0.45, n=12), MAT["chrome"])
    s.add(cyl(c + a * (r * 0.24), a, r * 0.52, r * 0.08, n=12), MAT["alu_dark"])


def studio(s, cx=0.0, cz=0.0, rx=1.8, rz=1.4):
    """Kontak gelap kecil; penumbra lebar dibakar di latar (lihat zrender._BG)."""
    for scale, a in ((0.42, 0.11), (0.26, 0.13)):
        pts = [[cx + rx * scale * math.cos(j * 2 * math.pi / 16), -0.076,
                cz + rz * scale * math.sin(j * 2 * math.pi / 16)] for j in range(16)]
        s.add([np.array(pts, np.float32)], M((4, 8, 18), alpha=a), pre=True)


def environment(s, tint=(9, 14, 27)):
    """Set studio: lantai bergrid, dinding cyclorama, garis horizon."""
    s.add(plane((0, -0.092, 0), (1, 0, 0), (0, 0, 1), 16, 16), MAT["floor"])
    for i in range(-7, 8):
        s.add(plane((i, -0.087, 0), (1, 0, 0), (0, 0, 1), 0.013, 16), MAT["grid"])
        s.add(plane((0, -0.087, i), (1, 0, 0), (0, 0, 1), 16, 0.013), MAT["grid"])
    s.add(plane((0, 3.8, -7.8), (1, 0, 0), (0, 1, 0), 26, 10), MAT["wall"])
    s.add(plane((0, 0.46, -7.76), (1, 0, 0), (0, 1, 0), 26, 0.92), MAT["wall2"])
    for px, py, w, h, mat in ((-5.6, 2.9, 2.4, 3.6, MAT["panel"]),
                              (5.2, 2.5, 1.5, 2.9, MAT["panel2"])):
        s.add(plane((px, py, -7.72), (1, 0, 0), (0, 1, 0), w, h), mat)
        s.add(plane((px, py - h / 2 - 0.05, -7.71), (1, 0, 0), (0, 1, 0),
                    w * 1.04, 0.05), MAT["wall2"])


def peripherals(s):
    """Elemen meja: keyboard, mouse, mug (geometri, bukan gambar)."""
    kz = 1.28
    s.add(box((-0.05, 0.048, kz), (1.46, 0.072, 0.50)), MAT["desk"])
    s.add(box((-0.05, 0.088, kz), (1.40, 0.008, 0.44)), MAT["case2"])
    for i in range(14):
        for j in range(4):
            m = MAT["key_hi"] if (i, j) == (0, 0) else (
                MAT["key_alt"] if (i + j) % 6 == 0 else MAT["key"])
            s.add(plane((-0.05 - 0.61 + i * 0.094, 0.094,
                         kz - 0.155 + j * 0.104),
                        (1, 0, 0), (0, 0, 1), 0.074, 0.082), m)
    s.add(box((1.00, 0.085, 1.34), (0.22, 0.10, 0.34)), MAT["plastic"])
    s.add(plane((1.00, 0.137, 1.27), (1, 0, 0), (0, 0, 1), 0.010, 0.10), MAT["led_blue"])
    s.add(cyl((-1.26, 0.17, 1.24), (0, 1, 0), 0.125, 0.30, n=18), MAT["cream"])
    s.add(annulus((-1.26, 0.325, 1.24), (0, 1, 0), 0.094, 0.125, n=18), MAT["cream"])
    s.add(disc((-1.26, 0.318, 1.24), (0, 1, 0), 0.094, n=18), MAT["coffee"])


def arc_ring(s, c, r, t, n=14):
    """Cincin pemuatan berputar — 14 segmen geometri, bukan partikel."""
    for i in range(n):
        a = 2 * math.pi * i / n
        u = (-math.sin(a), math.cos(a), 0)
        v = (math.cos(a), math.sin(a), 0)
        k = (i / n + t * 0.55) % 1.0
        s.add(plane((c[0] + r * v[0], c[1] + r * v[1], c[2]), u, v,
                    0.13, 0.030), led_mat((190, 232, 255), 0.10 + 0.85 * k))


def boot_bar(s, c, w, u):
    s.add(plane(c, (1, 0, 0), (0, 1, 0), w, 0.046), MAT["black"])
    q = clamp(u)
    s.add(plane((c[0] - w / 2 + w * q / 2, c[1], c[2] + 0.003),
                (1, 0, 0), (0, 1, 0), max(w * q, 0.001), 0.032),
          led_mat(ACCENT["cyan"], 0.62))


def detail_pcb(s, positions, y=0.09, r=0.055, h=0.14):
    """Kapasitor + chip kecil di atas papan."""
    for k, (x, z) in enumerate(positions):
        if k % 3 == 2:
            s.add(box((x, y + 0.035, z), (0.13, 0.07, 0.10)), MAT["chip"])
            s.add(box((x, y + 0.072, z), (0.09, 0.004, 0.07)), MAT["steel"])
        else:
            s.add(cyl((x, y + h / 2, z), (0, 1, 0), r, h, n=12), MAT["alu_dark"])
            s.add(cyl((x, y + h + 0.006, z), (0, 1, 0), r * 0.78, 0.012, n=12), MAT["chrome"])


def pcb_art(s, x0, z0, w, d, y, seed=0):
    """Silkscreen, komponen SMD, sekrup, dan jalur LED di tepi papan."""
    for i in range(18):
        x = x0 - w / 2 + 0.08 + i * (w - 0.16) / 17
        s.add(box((x, y, z0 + d / 2 - 0.07), (0.026, 0.004, 0.010)), MAT["silk"])
    for i in range(12):
        z = z0 - d / 2 + 0.10 + i * (d - 0.20) / 11
        s.add(box((x0 - w / 2 + 0.07, y, z), (0.010, 0.004, 0.026)), MAT["silk"])
    for i in range(8):
        f = (i * 0.6180339 + seed * 0.37) % 1.0
        x = x0 - w / 2 + 0.14 + f * (w - 0.28)
        z = z0 + d / 2 - 0.16
        s.add(box((x, y, z), (0.050, 0.014, 0.028)), MAT["smd"])
        s.add(box((x, y + 0.009, z), (0.040, 0.003, 0.020)), MAT["steel"])
    for sx in (-1, 1):
        for sz in (-1, 1):
            s.add(cyl((x0 + sx * (w / 2 - 0.07), y, z0 + sz * (d / 2 - 0.07)),
                      (0, 1, 0), 0.030, 0.008, n=10), MAT["chrome"])
    s.add(box((x0, y, z0 - d / 2 + 0.035), (w - 0.16, 0.006, 0.014)), MAT["led_blue"])


def vent_slots(s, c, size, n, axis="z"):
    for i in range(n):
        if axis == "z":
            s.add(box((c[0] - size[0] / 2 + (i + 0.5) * size[0] / n, c[1], c[2]),
                      (size[0] / n * 0.55, size[1], size[2])), MAT["black"])
        else:
            s.add(box((c[0], c[1], c[2] - size[2] / 2 + (i + 0.5) * size[2] / n),
                      (size[0], size[1], size[2] / n * 0.55)), MAT["black"])


def add_fan(s, c, a, r, phase, blades=7, blade=None, hub=None, ring=None):
    a = norm(a)
    c = np.asarray(c, np.float32)
    bm = blade or MAT["blade"]
    hm = hub or MAT["alu_dark"]
    rm = ring or MAT["steel"]
    s.add(fan_blades(c, a, r * 0.24, r * 0.90, blades, phase, skew=r * 0.17), bm, post=True)
    s.add(cyl(c, a, r * 0.22, r * 0.11, n=18), hm, post=True)
    s.add(annulus(c + a * (r * 0.06), a, r * 0.19, r * 0.235, n=18), rm, post=True)
    s.add(annulus(c, a, r * 0.94, r * 1.13, n=12), rm)
    s.add(disc(c - a * (r * 0.055), a, r * 0.94, n=12), MAT["black"])


def add_monitor(s, c, on=False, u=0.0, w=2.45, h=1.48, t=0.0):
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
        # UI boot generik di sepertiga atas layar (tidak tertutup kartu GPU)
        arc_ring(s, (x - w * 0.29, y + h * 0.29, z + 0.056), 0.135, t)
        boot_bar(s, (x + w * 0.20, y + h * 0.29, z + 0.056), w * 0.38, u)
        for k, bw in enumerate((0.34, 0.24, 0.30)):
            s.add(plane((x - w * 0.29 + (bw - 0.34) / 2,
                         y + h * 0.12 - k * 0.085, z + 0.056),
                        (1, 0, 0), (0, 1, 0), w * bw, 0.026), MAT["silk"])


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
        s.add(annulus((0, y, 0.930), (0, 0, 1), 0.240, 0.257, n=24),
              led_mat((70, 208, 244), 0.22 + 0.78 * led))

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
    # VRM, chipset, konektor ATX, slot PCIe, M.2, I/O belakang, ventilasi shroud
    for i in range(11):
        s.add(box((-0.420, 1.80, -0.62 + i * 0.075), (0.050, 0.17, 0.030)), MAT["alu_dark"])
    s.add(box((-0.420, 1.80, -0.19), (0.052, 0.035, 0.86)), MAT["silver2"])
    s.add(box((-0.420, 0.90, 0.40), (0.055, 0.22, 0.26)), MAT["alu_dark"])
    for i in range(7):
        s.add(box((-0.388, 0.90, 0.29 + i * 0.036), (0.012, 0.20, 0.012)), MAT["chrome"])
    s.add(box((-0.420, 1.06, -0.62), (0.060, 0.11, 0.34)), MAT["black"])
    for i in range(9):
        s.add(box((-0.386, 1.06, -0.75 + i * 0.037), (0.006, 0.055, 0.016)), MAT["gold"])
    for i in range(3):
        s.add(box((-0.420, 0.72 + i * 0.15, 0.10), (0.050, 0.045, 0.66)), MAT["black"])
        s.add(box((-0.418, 0.745 + i * 0.15, 0.10), (0.052, 0.008, 0.66)), MAT["silver2"])
    s.add(box((-0.418, 0.62, 0.52), (0.045, 0.012, 0.34)), MAT["pcb2"])
    for i in range(5):
        s.add(box((-0.392, 0.62, 0.39 + i * 0.065), (0.008, 0.016, 0.040)), MAT["chip"])
    screw(s, (-0.386, 0.62, 0.70), (1, 0, 0), 0.022)
    for i in range(4):
        s.add(box((-0.30 + i * 0.14, 1.76, -0.905), (0.085, 0.050, 0.012)), MAT["black"])
        s.add(box((-0.30 + i * 0.14, 1.745, -0.913), (0.060, 0.012, 0.006)), MAT["led_blue"])
    s.add(box((0.16, 1.76, -0.905), (0.14, 0.10, 0.012)), MAT["chrome"])
    for i in range(3):
        s.add(cyl((0.34 + i * 0.095, 1.72, -0.905), (0, 0, 1), 0.026, 0.010, n=12), MAT["gold"])
    for i in range(5):
        s.add(box((-0.32 + i * 0.15, 0.52, -0.905), (0.11, 0.30, 0.012)), MAT["alu_dark"])
        for j in range(4):
            s.add(box((-0.32 + i * 0.15, 0.42 + j * 0.065, -0.913), (0.060, 0.012, 0.004)), MAT["black"])
    for i in range(12):
        s.add(box((-0.38 + i * 0.065, 0.584, -0.30), (0.028, 0.006, 0.70)), MAT["black"])
    for z in (-0.82, 0.82):
        for y in (0.12, 1.92):
            screw(s, (0.565, y, z), (1, 0, 0), 0.028)

    for k in range(3):
        z = -0.55 + k * 0.32
        s.add(cable([(0.30, 0.42, z), (0.50, 0.64, z + 0.10),
                     (0.44, 1.06, z - 0.05), (0.06, 1.34, z - 0.24)],
                    r=0.023, n=6), MAT["rubber"])
    s.add(box((0.556, 1.02, -0.855), (0.012, 1.84, 0.014)), MAT["led_blue"])
    s.add(plane((0.545, 1.02, 0), (0, 1, 0), (0, 0, 1), 1.72, 1.96), MAT["glass"])
    for z in (-0.87, 0.87):
        s.add(box((0.552, 1.02, z), (0.03, 1.96, 0.05)), MAT["alu_dark"])
    for y in (0.045, 1.995):
        s.add(box((0.552, y, 0), (0.03, 0.05, 1.74)), MAT["alu_dark"])

    # panel I/O atas: 4 port USB, 2 jack audio, sisir kabel (quad, murah)
    for i in range(4):
        x = -0.36 + i * 0.13
        s.add(plane((x, 2.049, 0.30), (1, 0, 0), (0, 0, 1), 0.090, 0.042), MAT["port"])
        s.add(plane((x, 2.050, 0.30), (1, 0, 0), (0, 0, 1), 0.062, 0.012), MAT["silver2"])
    for i in range(2):
        s.add(annulus((0.22 + i * 0.12, 2.051, 0.30), (0, 1, 0),
                      0.018, 0.030, n=12), MAT["chrome"])
    for z in (-0.46, -0.12, 0.22):
        s.add(plane((0.42, 0.96, z), (0, 1, 0), (0, 0, 1), 0.14, 0.20), MAT["black"])
        for j in range(3):
            s.add(plane((0.423, 0.90 + j * 0.06, z), (0, 1, 0), (0, 0, 1),
                        0.008, 0.020), MAT["alu_dark"])

    dy = -0.018 * press
    s.add(cyl((0.0, 2.056 + dy, 0.62), (0, 1, 0), 0.078, 0.032, n=12), MAT["alu"])
    s.add(annulus((0.0, 2.075 + dy, 0.62), (0, 1, 0), 0.052, 0.075, n=12),
          led_mat((70, 208, 244), led))
    s.add(cyl((0.0, 2.077 + dy, 0.62), (0, 1, 0), 0.028, 0.006, n=12),
          led_mat((196, 240, 255), led))


# ---------------------------------------------------------------- adegan 1
def scene_case(u, t):
    s = Scene(top=(7, 12, 25), bottom=(22, 33, 54))
    studio(s, 0.0, 0.0, 1.55, 1.35)
    environment(s)
    led = smooth((u - 0.06) / 0.16)
    press = max(0.0, 1.0 - u * 14)
    add_tower(s, t * 2.6 + 0.25, led, press)
    add_monitor(s, (-1.98, 1.24, -0.72), on=False, w=1.95, h=1.20, t=t)
    peripherals(s)
    cam = Camera((0.0, 1.03, -0.05),
                 0.96 + 0.16 * ease(u) + beat(u, YAW, t),
                 0.16 - 0.05 * u + beat(u, PITCH, t),
                 6.55 - 0.75 * ease(u) + beat(u, DIST, t), fov=cine_fov(40, t, u))
    return s, cam


# ---------------------------------------------------------------- adegan 2
def scene_psu(u, t):
    s = Scene(top=(9, 12, 28), bottom=(27, 26, 48))
    studio(s, 0.20, 0.0, 1.75, 1.30)
    environment(s)
    phase = t * 3.0
    s.add(box((0, 0.46, 0), (1.62, 0.86, 1.42)), MAT["case"])
    s.add(box((0, 0.46, 0.715), (1.54, 0.78, 0.02)), MAT["case2"])
    s.add(box((0, 0.895, 0), (1.55, 0.02, 1.35)), MAT["case2"])
    add_fan(s, (0, 0.912, 0), (0, 1, 0), 0.44, phase, blades=9, blade=MAT["blade2"])
    s.add(annulus((0, 0.924, 0), (0, 1, 0), 0.30, 0.325, n=16), MAT["steel"])
    s.add(annulus((0, 0.924, 0), (0, 1, 0), 0.155, 0.175, n=16), MAT["steel"])
    s.add(box((0, 0.46, -0.718), (1.30, 0.66, 0.02)), MAT["black"])
    vent_slots(s, (0, 0.46, -0.732), (1.10, 0.44, 0.012), 9)
    for x in (-0.72, 0.72):
        for y in (0.14, 0.78):
            s.add(cyl((x, y, 0.725), (0, 0, 1), 0.035, 0.014, n=10), MAT["chrome"])
    for i in range(6):
        s.add(box((-0.55 + i * 0.22, 0.46, -0.732), (0.13, 0.34, 0.012)), MAT["alu_dark"])
    # pelat label + koil tembaga + kapasitor pada panel depan
    s.add(box((-0.28, 0.44, 0.732), (0.74, 0.40, 0.008)), MAT["case2"])
    for i in range(6):
        s.add(box((-0.56 + i * 0.11, 0.52 + 0.035 * (i % 2), 0.739),
                  (0.072, 0.007, 0.004)), MAT["silk"])
    s.add(annulus((0.44, 0.47, 0.739), (0, 0, 1), 0.12, 0.20, n=20), MAT["copper"])
    s.add(disc((0.44, 0.47, 0.741), (0, 0, 1), 0.11, n=20), MAT["black"])
    s.add(cyl((-0.45, 0.30, 0.741), (0, 0, 1), 0.075, 0.014, n=14), MAT["alu_dark"])
    s.add(disc((-0.45, 0.30, 0.750), (0, 0, 1), 0.055, n=14), MAT["alu"])
    # potongan panel: PCB, kapasitor, transformator, sirip, gril kipas
    s.add(box((-0.28, 0.44, 0.738), (0.70, 0.34, 0.006)), MAT["pcb"])
    for i in range(9):
        s.add(box((-0.58 + i * 0.075, 0.36, 0.744), (0.010, 0.16, 0.004)), MAT["trace"])
    for k in range(3):
        s.add(cyl((-0.50 + k * 0.19, 0.55, 0.752), (0, 0, 1), 0.068, 0.045, n=14), MAT["navy"])
        s.add(disc((-0.50 + k * 0.19, 0.55, 0.777), (0, 0, 1), 0.052, n=14), MAT["silver2"])
        s.add(box((-0.50 + k * 0.19, 0.55, 0.780), (0.070, 0.006, 0.006)), MAT["black"])
    s.add(box((0.34, 0.44, 0.752), (0.24, 0.30, 0.030)), MAT["copper"])
    for i in range(8):
        s.add(box((0.23 + i * 0.030, 0.44, 0.770), (0.010, 0.28, 0.010)), MAT["silver2"])
    for r in (0.20, 0.27, 0.34, 0.41):
        s.add(annulus((0, 0.936, 0), (0, 1, 0), r, r + 0.010, n=20), MAT["steel"])
    for x in (-0.60, 0.60):
        for y in (0.12, 0.80):
            screw(s, (x, y, 0.730), (0, 0, 1), 0.030)

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
    cam = Camera((0.55, 0.52, 0), -0.38 + 0.72 * ease(u) + beat(u, YAW, t),
                 0.48 - 0.14 * u + beat(u, PITCH, t),
                 7.10 - 0.80 * ease(u) + beat(u, DIST, t), fov=cine_fov(41, t, u))
    return s, cam


# ---------------------------------------------------------------- adegan 3
def scene_cpu(u, t):
    s = Scene(top=(6, 20, 27), bottom=(14, 38, 44))
    studio(s, 0.0, 0.0, 2.10, 2.00)
    environment(s)
    s.add(box((0, 0.02, 0), (2.05, 0.07, 2.05)), MAT["pcb"])
    for i in range(14):
        s.add(box((-0.90 + i * 0.15, 0.058, -0.88), (0.012, 0.006, 0.72)), MAT["trace"])
        s.add(box((0.62, 0.058, -0.84 + i * 0.15), (0.34, 0.006, 0.012)), MAT["trace"])
    pcb_art(s, 0, 0, 2.05, 2.05, 0.064, seed=1)

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
    detail_pcb(s, [(0.82, 0.30), (0.82, 0.52), (-0.82, 0.30), (-0.82, 0.52),
                   (0.30, -0.86), (0.52, -0.86), (-0.30, -0.86), (0.30, 0.86)], y=0.055)
    s.add(cyl((-0.79, 0.20, 0.0), (0, 0, 1), 0.022, 1.58, n=10), MAT["chrome"])
    # IHS, VRM di dua sisi, chip BIOS berkaki, LED debug, sekrup papan
    s.add(box((0, 0.178, 0), (0.62, 0.012, 0.62)), MAT["silver2"])
    for i in range(4):
        s.add(box((-0.24 + i * 0.16, 0.186, 0), (0.012, 0.004, 0.40)), MAT["alu_dark"])
    for i in range(12):
        s.add(box((-0.92 + i * 0.048, 0.20, -0.95), (0.024, 0.12, 0.055)), MAT["alu_dark"])
    for i in range(8):
        s.add(box((0.98, 0.20, -0.78 + i * 0.048), (0.055, 0.12, 0.024)), MAT["alu_dark"])
    s.add(box((1.18, 0.20, -0.66), (0.34, 0.05, 0.26)), MAT["chip"])
    for i in range(6):
        s.add(box((1.04 + i * 0.055, 0.075, -0.81), (0.028, 0.014, 0.05)), MAT["gold"])
        s.add(box((1.04 + i * 0.055, 0.075, -0.51), (0.028, 0.014, 0.05)), MAT["gold"])
    for i in range(4):
        s.add(box((-0.60 + i * 0.12, 0.067, 0.92), (0.060, 0.012, 0.030)),
              led_mat(ACCENT["cyan"], 0.30 + 0.55 * smooth((u - i * 0.10) / 0.22)))
    for x in (-0.88, 0.88):
        for z in (-0.88, 0.88):
            screw(s, (x, 0.075, z), (0, 1, 0), 0.032)
    cam = Camera((0, 0.10, 0), 0.34 + 0.42 * ease(u) + beat(u, YAW, t),
                 0.98 - 0.34 * u + beat(u, PITCH, t),
                 5.20 - 0.60 * ease(u) + beat(u, DIST, t), fov=cine_fov(40, t, u))
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
    s = Scene(top=(10, 13, 29), bottom=(26, 24, 52))
    studio(s, 0.0, 0.0, 2.05, 1.85)
    environment(s)
    s.add(box((0, 0.04, 0), (2.75, 0.08, 2.35)), MAT["pcb"])
    for i in range(11):
        s.add(box((-1.24 + i * 0.24, 0.083, -1.02), (0.012, 0.006, 0.78)), MAT["trace"])
    for i in range(8):
        s.add(box((-0.30, 0.083, -1.00 + i * 0.24), (1.90, 0.006, 0.012)), MAT["trace"])
    pcb_art(s, 0, 0, 2.75, 2.35, 0.089, seed=2)

    s.add(box((-0.42, 0.22, -0.62), (0.86, 0.38, 0.86)), MAT["alu_dark"])
    for i in range(9):
        s.add(box((-0.80 + i * 0.095, 0.425, -0.62), (0.022, 0.05, 0.80)), MAT["chrome"])
    add_fan(s, (-0.42, 0.455, -0.62), (0, 1, 0), 0.31, t * 2.4, blades=7)
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
    s.add(box((-1.20, 0.11, 0.72), (0.20, 0.14, 0.56)), MAT["black"])
    detail_pcb(s, [(-1.05, -0.92), (-0.85, -0.92), (1.18, -0.86), (1.18, -0.66),
                   (1.18, 0.10), (1.18, 0.30)], y=0.085, r=0.045, h=0.11)
    for i in range(6):
        s.add(box((-0.90 + i * 0.30, 0.095, 1.02), (0.16, 0.03, 0.12)), MAT["alu"])
    for i in range(4):
        on = smooth((u - 0.12 - i * 0.16) / 0.14)
        s.add(box((1.02, 0.187, 0.62 + i * 0.20), (0.10, 0.012, 0.09)),
              led_mat(ACCENT["green"], on) if on > 0.25 else led_mat((210, 70, 70), 0.55))
    # display POST 7-seg, tombol power, buzzer, sekrup papan
    s.add(box((1.22, 0.192, 0.92), (0.22, 0.012, 0.13)), MAT["black"])
    for i in range(3):
        s.add(box((1.14 + i * 0.07, 0.200, 0.92), (0.045, 0.006, 0.075)),
              led_mat((255, 92, 60), 0.42 + 0.5 * smooth((u - i * 0.12) / 0.2)))
    s.add(cyl((-1.20, 0.20, 0.72), (0, 1, 0), 0.085, 0.030, n=14), MAT["black"])
    s.add(annulus((-1.20, 0.218, 0.72), (0, 1, 0), 0.055, 0.080, n=14), MAT["silver2"])
    for x in (-1.28, 1.28):
        for z in (-1.06, 1.06):
            screw(s, (x, 0.095, z), (0, 1, 0), 0.030)
    cam = Camera((0.05, 0.30, 0), 0.48 + 0.48 * ease(u) + beat(u, YAW, t),
                 0.80 - 0.24 * u + beat(u, PITCH, t),
                 6.35 - 0.70 * ease(u) + beat(u, DIST, t), fov=cine_fov(41, t, u))
    return s, cam


# ---------------------------------------------------------------- adegan 5
def scene_ram(u, t):
    s = Scene(top=(6, 15, 31), bottom=(16, 32, 58))
    studio(s, 0.0, 0.0, 2.20, 1.55)
    environment(s)
    s.add(box((0, 0.04, 0), (2.45, 0.08, 1.60)), MAT["pcb"])
    for i in range(7):
        s.add(box((-1.00, 0.083, -0.58 + i * 0.18), (1.55, 0.006, 0.012)), MAT["trace"])
    for i in range(4):
        s.add(box((0.20 + i * 0.28, 0.083, 0.62), (0.012, 0.006, 0.60)), MAT["trace"])
    pcb_art(s, 0, 0, 2.45, 1.60, 0.089, seed=3)

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
        for j in range(4):
            s.add(box((x + 0.05, 0.45 + drop, -0.42 + j * 0.28),
                      (0.012, 0.42, 0.20)), MAT["chip"])
    s.add(cyl((-0.05, 0.155, -0.12), (0, 1, 0), 0.045, 0.018, n=10), MAT["chrome"])
    detail_pcb(s, [(0.95, -0.62), (0.95, 0.62), (-1.12, 0.62)], y=0.085, r=0.04, h=0.09)
    # heatspreader berlekuk, tab slot, chip SPD, sekrup papan
    for i in range(4):
        x = 0.34 + i * 0.29
        s.add(box((x + 0.053, 0.45, 0), (0.008, 0.58, 1.04)), MAT["navy"])
        for j in range(5):
            s.add(box((x + 0.058, 0.26 + j * 0.12, 0), (0.006, 0.050, 0.86)), MAT["silver2"])
        for z in (-0.66, 0.66):
            s.add(box((x, 0.10, z), (0.14, 0.10, 0.06)), MAT["plastic"])
    for i in range(4):
        s.add(box((-0.92 + i * 0.42, 0.172, -0.12), (0.24, 0.010, 0.24)), MAT["chip"])
    for x in (-1.10, 1.10):
        for z in (-0.68, 0.68):
            screw(s, (x, 0.09, z), (0, 1, 0), 0.028)
    for i in range(6):
        s.add(plane((-0.72 + i * 0.24, 0.29, 0.72), (1, 0, 0), (0, 0, 1),
                    0.15, 0.10), MAT["chip"])
        s.add(plane((-0.72 + i * 0.24, 0.291, 0.72), (1, 0, 0), (0, 0, 1),
                    0.10, 0.010), MAT["silk"])
    cam = Camera((0.15, 0.34, 0), 0.26 + 0.32 * ease(u) + beat(u, YAW, t),
                 0.68 - 0.22 * u + beat(u, PITCH, t),
                 7.80 - 0.85 * ease(u) + beat(u, DIST, t), fov=cine_fov(40, t, u))
    return s, cam


# ---------------------------------------------------------------- adegan 6
def scene_gpu(u, t):
    s = Scene(top=(7, 12, 24), bottom=(23, 32, 50))
    studio(s, 0.0, -0.25, 2.15, 1.45)
    environment(s)
    on = u > 0.48
    add_monitor(s, (0, 1.32, -1.15), on=on, u=u, w=2.85, h=1.68, t=t)
    s.add(box((0, 1.02, 0.48), (2.55, 0.60, 0.30)), MAT["alu"])
    for x in (-0.60, 0.60):
        add_fan(s, (x, 1.02, 0.648), (0, 0, 1), 0.245, t * 3.2 + x, blades=9)
        s.add(annulus((x, 1.02, 0.662), (0, 0, 1), 0.230, 0.246, n=24),
              led_mat((70, 150, 255), 0.30 + 0.55 * u))
    s.add(box((0, 0.705, 0.48), (1.55, 0.045, 0.24)), MAT["gold"])
    s.add(box((0, 1.335, 0.48), (2.55, 0.035, 0.30)), MAT["alu_dark"])
    s.add(box((1.24, 1.02, 0.48), (0.06, 0.56, 0.34)), MAT["steel"])
    for i in range(12):
        s.add(box((-1.15 + i * 0.21, 1.35, 0.34), (0.018, 0.028, 0.24)), MAT["chrome"])
    s.add(box((-1.30, 1.02, 0.34), (0.05, 0.52, 0.30)), MAT["chrome"])
    for y in (0.86, 1.18):
        s.add(cyl((-1.335, y, 0.34), (1, 0, 0), 0.032, 0.012, n=10), MAT["copper"])
    # port display, heatpipe tembaga, ventilasi shroud, konektor daya, sekrup
    for i in range(3):
        s.add(box((-1.346, 0.90 + i * 0.11, 0.34), (0.012, 0.065, 0.16)), MAT["black"])
        s.add(box((-1.352, 0.90 + i * 0.11, 0.34), (0.006, 0.040, 0.12)), MAT["silver2"])
    for i in range(2):
        s.add(cable([(0.95, 0.80 + i * 0.22, 0.30), (0.40, 0.78 + i * 0.22, 0.28),
                     (-0.40, 0.78 + i * 0.22, 0.28), (-0.95, 0.80 + i * 0.22, 0.30)],
                    r=0.020, n=6), MAT["copper"])
    for i in range(18):
        s.add(box((-1.10 + i * 0.125, 1.345, 0.60), (0.055, 0.008, 0.030)), MAT["black"])
    s.add(box((1.10, 1.36, 0.48), (0.26, 0.08, 0.20)), MAT["black"])
    for i in range(4):
        s.add(box((1.02 + i * 0.055, 1.406, 0.48), (0.030, 0.014, 0.14)), MAT["gold"])
    for x in (-1.18, -0.60, 0.60, 1.18):
        for y in (0.80, 1.24):
            screw(s, (x, y, 0.642), (0, 0, 1), 0.024)
    cam = Camera((0, 1.15, -0.30), 0.50 - 0.16 * u + beat(u, YAW, t),
                 0.14 - 0.05 * u + beat(u, PITCH, t),
                 7.60 - 0.90 * ease(u) + beat(u, DIST, t), fov=cine_fov(42, t, u))
    return s, cam


# ---------------------------------------------------------------- adegan 7
def scene_loop(u, t):
    s = Scene(top=(9, 15, 30), bottom=(27, 38, 60))
    studio(s, 0.0, 0.0, 1.60, 1.40)
    environment(s)
    led = 0.55 + 0.45 * math.sin(t * 2.2) ** 2
    add_tower(s, t * 2.6 + 0.25, led, 0.0)
    add_monitor(s, (-1.98, 1.24, -0.72), on=True, u=1.0, w=1.95, h=1.20, t=t)
    peripherals(s)
    cam = Camera((-0.38, 1.00, -0.08), 0.88 - 0.40 * ease(u) + beat(u, YAW, t),
                 0.19 + 0.06 * u + beat(u, PITCH, t),
                 7.35 + 0.45 * ease(u) + beat(u, DIST, t), fov=cine_fov(40, t, u))
    return s, cam


BUILDERS = {
    "case": scene_case, "psu": scene_psu, "cpu": scene_cpu, "post": scene_post,
    "ram": scene_ram, "gpu": scene_gpu, "loop": scene_loop,
}


def build(name, u, t, W=1080, H=1920, ss=1.0):
    import zrender
    s, cam = BUILDERS[name](clamp(u), t)
    return zrender.render(s, cam, W, H, ss)

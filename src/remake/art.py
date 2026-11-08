#!/usr/bin/env python3
"""Mesin gambar KlikTahu — semua visual dilukis dengan kode (Pillow + numpy + cv2).

Tidak ada frame, foto, atau aset dari video referensi. Semua adegan, tipografi,
progress bar, partikel, dan watermark KlikTahu digenerasi deterministik di sini.
"""

from __future__ import annotations

import math
import random
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from script_kliktahu import BRAND, COLORS, H, STEPS, TAGLINE, W, WATERMARK

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "assets" / "fonts"

BASE_SCALE = 1.15
BW, BH = int(W * BASE_SCALE), int(H * BASE_SCALE)

_FONT_FILES = {
    "Regular": "Poppins-Regular.ttf",
    "Medium": "Poppins-Medium.ttf",
    "SemiBold": "Poppins-SemiBold.ttf",
    "Bold": "Poppins-Bold.ttf",
    "ExtraBold": "Poppins-ExtraBold.ttf",
}


@lru_cache(maxsize=128)
def F(size: int, weight: str = "Bold") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / _FONT_FILES[weight]), size)


def C(name: str) -> tuple[int, int, int]:
    return COLORS[name]


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def gradient(w, h, top, bottom):
    t = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    a = np.array(top, np.float32)[None, None, :]
    b = np.array(bottom, np.float32)[None, None, :]
    arr = a * (1 - t) + b * t
    return np.repeat(arr, w, axis=1).astype(np.uint8)


def glows(size, spots):
    """spots: (cx, cy, radius, (r,g,b), strength 0..1)"""
    w, h = size
    out = np.zeros((h, w, 4), np.float32)
    for cx, cy, r, color, strength in spots:
        x0, x1 = max(0, int(cx - r)), min(w, int(cx + r))
        y0, y1 = max(0, int(cy - r)), min(h, int(cy + r))
        if x1 <= x0 or y1 <= y0:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d2 = ((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)
        fall = np.clip(1 - d2, 0, 1) ** 2 * strength
        patch = out[y0:y1, x0:x1]
        for k in range(3):
            patch[..., k] += fall * color[k]
        patch[..., 3] = np.maximum(patch[..., 3], fall * 255)
    return Image.fromarray(np.uint8(np.clip(out, 0, 255)), "RGBA")


def rr(d, box, r, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def txt(d, xy, s, size, color, weight="Bold", anchor="la", stroke=0, stroke_color=None):
    d.text(
        xy, s, font=F(size, weight), fill=color, anchor=anchor,
        stroke_width=stroke, stroke_fill=stroke_color or (0, 0, 0, 180),
    )


def iso_box(d, x, y, w, h, dep, front, top, side, edge=None):
    """Kotak isometris sederhana: depan + atas + sisi kanan."""
    dx, dy = dep, -dep * 0.62
    top_face = [(x, y), (x + dx, y + dy), (x + w + dx, y + dy), (x + w, y)]
    side_face = [(x + w, y), (x + w + dx, y + dy), (x + w + dx, y + h + dy), (x + w, y + h)]
    d.polygon(top_face, fill=top)
    d.polygon(side_face, fill=side)
    rr(d, (x, y, x + w, y + h), 10, front, outline=edge, width=2)
    return (x, y, x + w, y + h)


def fan(d, cx, cy, r, phase, rim, blade, glow=None):
    if glow:
        d.ellipse((cx - r * 1.18, cy - r * 1.18, cx + r * 1.18, cy + r * 1.18), fill=glow)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(8, 14, 28), outline=rim, width=max(2, int(r * 0.07)))
    for k in range(7):
        a = phase + k * (2 * math.pi / 7)
        pts = []
        for rad, off in ((r * 0.18, -0.30), (r * 0.82, -0.16), (r * 0.86, 0.30), (r * 0.22, 0.46)):
            aa = a + off
            pts.append((cx + math.cos(aa) * rad, cy + math.sin(aa) * rad))
        d.polygon(pts, fill=blade)
    d.ellipse((cx - r * 0.20, cy - r * 0.20, cx + r * 0.20, cy + r * 0.20), fill=rim)


def traces(d, box, seed, color, n=34, alpha=70):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(y0, y1)
        length = rnd.uniform(60, 320)
        path = [(x, y), (x + length * 0.45, y), (x + length * 0.45 + 28, y + 28), (x + length, y + 28)]
        d.line(path, fill=rgba(color, alpha), width=2)
        d.ellipse((x + length - 4, y + 24, x + length + 4, y + 32), fill=rgba(color, min(255, alpha + 60)))


def pill(d, box, label, fill, text_color, size=26, weight="Bold"):
    rr(d, box, (box[3] - box[1]) // 2, fill)
    txt(d, ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2), label, size, text_color, weight, "mm")


# ---------------------------------------------------------------------------
# ADEGAN: kanvas dasar 1242x2208 (1.15x) supaya zoom kamera tetap tajam.
# ---------------------------------------------------------------------------

def _backdrop():
    img = Image.fromarray(gradient(BW, BH, C("bg_top"), C("bg_bottom")), "RGB").convert("RGBA")
    img = Image.alpha_composite(img, glows((BW, BH), [
        (BW * 0.22, BH * 0.16, 720, C("blue"), 0.30),
        (BW * 0.86, BH * 0.52, 660, C("cyan"), 0.16),
        (BW * 0.50, BH * 0.92, 760, C("bg_bottom"), 0.45),
    ]))
    d = ImageDraw.Draw(img, "RGBA")
    # lantai perspektif
    for i in range(15):
        y = BH * 0.72 + i * i * 5.2
        d.line((0, y, BW, y), fill=rgba(C("panel_light"), 22), width=2)
    for i in range(-9, 10):
        x0 = BW / 2 + i * 95
        d.line((BW / 2 + i * 22, BH * 0.72, x0, BH), fill=rgba(C("panel_light"), 18), width=2)
    rnd = random.Random(7)
    for _ in range(150):
        x, y = rnd.uniform(0, BW), rnd.uniform(0, BH * 0.78)
        r = rnd.uniform(0.8, 2.4)
        d.ellipse((x - r, y - r, x + r, y + r), fill=rgba(C("white"), rnd.randint(18, 70)))
    return img


def _tower(d, x, y, w, h, accent, label=True):
    dep = 46
    iso_box(d, x, y, w, h, dep, (17, 28, 52), (30, 48, 82), (10, 19, 38), edge=(72, 96, 138, 255))
    # panel kaca
    gx0, gy0, gx1, gy1 = x + 34, y + 92, x + w - 34, y + h - 60
    rr(d, (gx0, gy0, gx1, gy1), 16, (12, 22, 42, 235), outline=(86, 120, 170, 150), width=3)
    d.line((gx0 + 16, gy0 + 20, gx0 + 16, gy1 - 30), fill=rgba(accent, 130), width=5)
    # komponen internal
    rr(d, (gx0 + 60, gy0 + 150, gx0 + 300, gy0 + 430), 12, (28, 44, 74, 255), outline=(96, 130, 180, 120), width=2)
    rr(d, (gx0 + 70, gy0 + 470, gx0 + 300, gy0 + 630), 8, (20, 34, 60, 255))
    for i in range(6):
        d.line((gx0 + 80, gy0 + 490 + i * 22, gx0 + 290, gy0 + 490 + i * 22), fill=rgba(C("cyan"), 60), width=2)
    # kipas statis (bilah berputar digambar di layer dinamis)
    for i, fy in enumerate((gy0 + 120, gy0 + 340, gy0 + 560)):
        fan(d, gx1 - 105, fy, 74, i * 0.7, (60, 88, 130, 255), (34, 54, 88, 255), rgba(accent, 30))
    # tombol power
    bx, by, br = x + w - 84, y + 600, 26
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=(10, 18, 36), outline=rgba(accent, 230), width=5)
    d.arc((bx - 13, by - 13, bx + 13, by + 13), -90, 90, fill=rgba(accent, 255), width=4)
    d.line((bx, by - 18, bx, by - 2), fill=rgba(accent, 255), width=4)
    if label:
        txt(d, (gx0 + 60, gy1 - 74), "KlikTahu", 30, rgba(C("white"), 150), "SemiBold")
        txt(d, (gx0 + 60, gy1 - 38), "LAB • 2026", 20, rgba(accent, 170), "Medium")


def _monitor(d, x, y, w, h, accent, desktop=False):
    rr(d, (x, y, x + w, y + h), 22, (14, 22, 42), outline=(88, 116, 164), width=5)
    sx0, sy0, sx1, sy1 = x + 20, y + 20, x + w - 20, y + h - 20
    if desktop:
        d.rectangle((sx0, sy0, sx1, sy1), fill=(24, 74, 158))
        d.rectangle((sx0, sy0, sx1, sy0 + 190), fill=(18, 56, 124))
        rr(d, (sx0 + 60, sy0 + 70, sx0 + 250, sy0 + 150), 10, (235, 245, 255, 235))
        rr(d, (sx0 + 280, sy0 + 70, sx1 - 60, sy0 + 150), 10, (12, 32, 70, 220))
        rr(d, (sx0 + 90, sy0 + 240, sx0 + 400, sy0 + 480), 14, (240, 247, 255, 240))
        rr(d, (sx0 + 90, sy0 + 240, sx0 + 400, sy0 + 288), 14, (218, 232, 250, 255))
        d.rectangle((sx0 + 90, sy0 + 270, sx0 + 400, sy0 + 288), fill=(218, 232, 250, 255))
        d.rectangle((sx0, sy1 - 54, sx1, sy1), fill=(10, 24, 56, 235))
        for i in range(5):
            d.rounded_rectangle((sx0 + 40 + i * 78, sy1 - 42, sx0 + 96 + i * 78, sy1 - 12), 6, fill=(235, 245, 255, 210))
    else:
        d.rectangle((sx0, sy0, sx1, sy1), fill=(6, 12, 26))
        d.polygon(((sx0, sy0), (sx0 + 190, sy0), (sx0 + 60, sy1), (sx0, sy1)), fill=(24, 42, 76, 120))
        d.line((sx0, sy1 - 1, sx1, sy1 - 1), fill=rgba(accent, 90), width=3)
    d.rectangle((x + w / 2 - 16, y + h, x + w / 2 + 16, y + h + 74), fill=(30, 44, 70))
    rr(d, (x + w / 2 - 130, y + h + 70, x + w / 2 + 130, y + h + 92), 10, (30, 44, 70))


def _pcb(d, x, y, w, h, accent):
    rr(d, (x, y, x + w, y + h), 18, (18, 48, 58), outline=(48, 92, 104), width=4)
    traces(d, (x + 20, y + 20, x + w - 20, y + h - 20), 11, accent, 40, 85)
    # soket CPU
    cx, cy, s = x + w * 0.46, y + h * 0.42, 240
    rr(d, (cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2), 12, (32, 44, 62), outline=(120, 146, 180), width=4)
    rr(d, (cx - s / 2 + 26, cy - s / 2 + 26, cx + s / 2 - 26, cy + s / 2 - 26), 8, (74, 88, 110))
    for i in range(9):
        for j in range(9):
            d.ellipse((cx - 96 + j * 22, cy - 96 + i * 22, cx - 92 + j * 22, cy - 92 + i * 22), fill=(168, 182, 205))
    # chip BIOS
    rr(d, (x + 54, y + 86, x + 234, y + 166), 8, (12, 20, 34), outline=(90, 120, 160), width=2)
    txt(d, (x + 144, y + 126), "KlikTahu", 22, rgba(C("white"), 220), "SemiBold", "mm")
    txt(d, (x + 144, y + 150), "BIOS", 17, rgba(accent, 230), "Medium", "mm")
    # slot RAM
    for i in range(4):
        rx = x + w * 0.70 + i * 46
        rr(d, (rx, y + 70, rx + 30, y + h - 90), 5, (12, 24, 40), outline=(70, 100, 140), width=2)
        rr(d, (rx - 5, y + 120, rx + 35, y + h - 150), 5, (24, 60, 78), outline=rgba(accent, 150), width=2)
    # M.2
    rr(d, (x + 60, y + h - 150, x + 360, y + h - 96), 6, (14, 28, 44), outline=(80, 110, 150), width=2)
    txt(d, (x + 78, y + h - 122), "M.2  •  KlikTahu NVMe", 18, rgba(C("white"), 170), "Medium")


def _base_case():
    img = _backdrop()
    d = ImageDraw.Draw(img, "RGBA")
    _tower(d, 90, 250, 660, 1620, C("cyan"))
    # kartu grafis + kabel di dalam panel kaca
    rr(d, (160, 980, 560, 1092), 14, (26, 44, 74, 255), outline=(90, 130, 180, 170), width=3)
    for k in range(4):
        d.line((182, 1010 + k * 20, 538, 1010 + k * 20), fill=rgba(C("cyan"), 70), width=2)
    txt(d, (180, 1108), "KlikTahu GPU", 22, rgba(C("white"), 170), "SemiBold")
    d.line(((560, 700), (640, 770), (640, 900), (568, 966)), fill=rgba(C("yellow"), 120), width=9, joint="curve")
    d.line(((180, 900), (130, 980), (130, 1420), (190, 1500)), fill=rgba(C("cyan"), 90), width=7, joint="curve")
    _monitor(d, 790, 480, 420, 620, C("cyan"))
    txt(d, (1000, 790), "NO SIGNAL", 26, rgba(C("muted"), 150), "SemiBold", "mm")
    rr(d, (790, 1210, 1210, 1290), 16, (24, 38, 66), outline=(70, 96, 140), width=3)
    for i in range(12):
        rr(d, (808 + i * 32, 1226, 832 + i * 32, 1246), 4, rgba(C("white"), 90))
    return img


def _base_psu():
    img = _backdrop()
    d = ImageDraw.Draw(img, "RGBA")
    # gelombang AC kiri
    x0, y0 = 80, 620
    d.line((x0, y0, 520, y0), fill=rgba(C("muted"), 90), width=2)
    pts = [(x0 + i * 4, y0 + math.sin(i * 0.16) * 96) for i in range(111)]
    d.line(pts, fill=rgba(C("yellow"), 230), width=6, joint="curve")
    txt(d, (80, 440), "220 V AC", 46, rgba(C("yellow"), 255), "ExtraBold")
    txt(d, (80, 504), "dari listrik rumah", 26, rgba(C("muted"), 255), "Medium")
    # kotak PSU
    iso_box(d, 110, 940, 560, 700, 52, (20, 32, 56), (38, 58, 94), (12, 22, 42), edge=(96, 124, 168, 255))
    fan(d, 390, 1290, 190, 0.2, (70, 96, 138), (30, 48, 80), rgba(C("yellow"), 28))
    txt(d, (160, 1000), "KlikTahu", 40, rgba(C("white"), 240), "ExtraBold")
    txt(d, (160, 1052), "PSU  •  650 W", 26, rgba(C("yellow"), 230), "SemiBold")
    txt(d, (160, 1092), "80 PLUS GOLD", 20, rgba(C("muted"), 220), "Medium")
    # rail DC kanan
    for i, (label, col) in enumerate((("+12 V", C("cyan")), ("+5 V", C("green")), ("+3,3 V", C("yellow")))):
        yy = 900 + i * 230
        d.line((700, yy, 1160, yy), fill=rgba(col, 170), width=7)
        pill(d, (700, yy - 84, 900, yy - 30), label, rgba(col, 235), C("ink"), 26)
    pill(d, (740, 1660, 1140, 1730), "POWER GOOD", rgba(C("green"), 235), C("ink"), 30)
    return img


def _base_cpu():
    img = _backdrop()
    d = ImageDraw.Draw(img, "RGBA")
    _pcb(d, 90, 360, 1060, 1400, C("cyan"))
    pill(d, (120, 1820, 560, 1900), "INSTRUKSI PERTAMA", rgba(C("cyan"), 235), C("ink"), 28)
    pill(d, (600, 1820, 1140, 1900), "KlikTahu • BIOS", rgba(C("panel_light"), 255), C("white"), 28)
    return img


def _base_post():
    img = _backdrop()
    d = ImageDraw.Draw(img, "RGBA")
    rr(d, (110, 380, 1130, 1640), 28, (14, 27, 52, 245), outline=(80, 112, 160, 180), width=4)
    txt(d, (160, 430), "POWER-ON SELF TEST", 44, rgba(C("white"), 255), "ExtraBold")
    txt(d, (160, 492), "KlikTahu diagnostics", 25, rgba(C("muted"), 255), "Medium")
    for i, name in enumerate(STEPS):
        yy = 600 + i * 158
        rr(d, (150, yy, 1090, yy + 118), 16, (24, 42, 74, 235), outline=(70, 100, 145, 120), width=2)
        txt(d, (210, yy + 59), f"{i + 1:02d}", 34, rgba(C("cyan"), 255), "Bold", "lm")
        txt(d, (290, yy + 59), name, 38, rgba(C("white"), 245), "SemiBold", "lm")
    pill(d, (150, 1540, 620, 1610), "DEBUG LED", rgba(C("yellow"), 235), C("ink"), 28)
    return img


def _base_ram():
    img = _backdrop()
    d = ImageDraw.Draw(img, "RGBA")
    # SSD kiri
    iso_box(d, 80, 700, 420, 300, 40, (20, 34, 58), (40, 62, 96), (12, 22, 42), edge=(90, 120, 165, 255))
    txt(d, (120, 760), "SSD", 48, rgba(C("white"), 255), "ExtraBold")
    txt(d, (120, 824), "permanen, tapi lambat", 24, rgba(C("muted"), 255), "Medium")
    # RAM kanan
    for i in range(4):
        xx = 720 + i * 120
        rr(d, (xx, 640, xx + 92, 1060), 10, (22, 62, 80), outline=rgba(C("blue"), 220), width=3)
        for k in range(5):
            rr(d, (xx + 14, 690 + k * 66, xx + 78, 726 + k * 66), 4, (12, 30, 52))
        txt(d, (xx + 46, 1090), "DDR5", 18, rgba(C("cyan"), 220), "SemiBold", "ma")
    # bus
    d.line((500, 870, 720, 870), fill=rgba(C("cyan"), 170), width=10)
    d.polygon(((720, 852), (760, 870), (720, 888)), fill=rgba(C("cyan"), 230))
    txt(d, (610, 800), "SALIN", 26, rgba(C("cyan"), 255), "Bold", "mm")
    # progress bar besar
    rr(d, (110, 1320, 1130, 1420), 22, (18, 32, 60), outline=(80, 112, 160), width=3)
    txt(d, (110, 1240), "MEMUAT SISTEM", 40, rgba(C("white"), 255), "ExtraBold")
    # cincin loading
    d.ellipse((470, 1560, 770, 1860), outline=rgba(C("panel_light"), 220), width=22)
    txt(d, (620, 1710), "RAM", 44, rgba(C("cyan"), 255), "ExtraBold", "mm")
    return img


def _base_gpu():
    img = _backdrop()
    d = ImageDraw.Draw(img, "RGBA")
    _monitor(d, 130, 250, 980, 1080, C("amber"), desktop=True)
    # kartu grafis
    iso_box(d, 190, 1460, 860, 340, 44, (18, 30, 54), (38, 58, 94), (10, 20, 40), edge=(96, 124, 168, 255))
    fan(d, 400, 1630, 120, 0.4, (70, 96, 138), (30, 48, 80), rgba(C("amber"), 30))
    fan(d, 760, 1630, 120, 1.1, (70, 96, 138), (30, 48, 80), rgba(C("amber"), 30))
    txt(d, (240, 1490), "KlikTahu GPU", 34, rgba(C("white"), 235), "ExtraBold")
    return img


def _base_loop():
    img = _backdrop()
    d = ImageDraw.Draw(img, "RGBA")
    _tower(d, 240, 420, 760, 1400, C("yellow"), label=True)
    return img


_BASES = {
    "case": _base_case, "psu": _base_psu, "cpu": _base_cpu,
    "post": _base_post, "ram": _base_ram, "gpu": _base_gpu, "loop": _base_loop,
}


@lru_cache(maxsize=8)
def scene_base(scene: str) -> np.ndarray:
    img = _BASES[scene]().convert("RGB")
    return np.asarray(img)


# ---------------------------------------------------------------------------
# KAMERA
# ---------------------------------------------------------------------------

def camera(base: np.ndarray, p: float, mode: str):
    """p = 0..1 progres adegan. Kembalikan (view RGB, fungsi pemetaan basis->layar)."""
    p = clamp(p)
    if mode == "push":
        z, dx, dy = 1.0 + 0.15 * ease(p), 0.0, -18 * p
    elif mode == "pull":
        z, dx, dy = 1.15 - 0.15 * ease(p), 0.0, 18 * p
    elif mode == "pan_right":
        z, dx, dy = 1.09, 70 * (p - 0.5), -14 * p
    elif mode == "pan_left":
        z, dx, dy = 1.09, -70 * (p - 0.5), -14 * p
    else:
        z, dx, dy = 1.05, 0.0, 0.0
    cw, ch = BW / z, BH / z
    cx = clamp(BW / 2 + dx, cw / 2, BW - cw / 2)
    cy = clamp(BH / 2 + dy, ch / 2, BH - ch / 2)
    x0, y0 = cx - cw / 2, cy - ch / 2
    x1, y1 = int(x0 + cw), int(y0 + ch)
    crop = base[int(y0):y1, int(x0):x1]
    view = cv2.resize(crop, (W, H), interpolation=cv2.INTER_LINEAR)

    def P(bx, by):
        return ((bx - x0) * W / cw, (by - y0) * H / ch)

    return view, P


# ---------------------------------------------------------------------------
# LAPISAN DINAMIS (per frame)
# ---------------------------------------------------------------------------

def dynamic(frame: Image.Image, scene: str, p: float, t_abs: float, P):
    d = ImageDraw.Draw(frame, "RGBA")
    pulse = 0.5 + 0.5 * math.sin(t_abs * 2.6)

    if scene == "case":
        for i, (bx, by) in enumerate(((611, 462), (611, 682), (611, 902))):
            cx, cy = P(bx, by)
            fan(d, cx, cy, 74, t_abs * (2.2 + i * 0.15), rgba(C("cyan"), 210), rgba(C("panel_light"), 190))
        cx, cy = P(666, 850)
        r = 30 + 8 * pulse
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(C("cyan"), 200), width=5)
        d.ellipse((cx - r * 1.7, cy - r * 1.7, cx + r * 1.7, cy + r * 1.7), outline=rgba(C("cyan"), 70), width=3)

    elif scene == "psu":
        for i, col in enumerate((C("cyan"), C("green"), C("yellow"))):
            by = 900 + i * 230
            for k in range(7):
                q = (p * 2.2 + k / 7 + i * 0.13) % 1.0
                bx = 700 + q * 460
                x, y = P(bx, by)
                r = 9
                d.ellipse((x - r, y - r, x + r, y + r), fill=rgba(col, 235))
        x, y = P(940, 1695)
        if p > 0.55:
            d.ellipse((x - 26, y - 26, x + 26, y + 26), fill=rgba(C("green"), int(160 + 90 * pulse)))

    elif scene == "cpu":
        for k in range(16):
            q = (p * 1.7 + k / 16) % 1.0
            x, y = P(140 + q * 960, 420 + (k % 4) * 300)
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=rgba(C("cyan"), 190))
        x, y = P(620, 948)
        r = 150 + 18 * pulse
        d.ellipse((x - r, y - r, x + r, y + r), outline=rgba(C("cyan"), 110), width=6)

    elif scene == "post":
        done = min(6, int(p * 7.4))
        for i in range(done):
            x, y = P(1035, 659 + i * 158)
            r = 24
            d.ellipse((x - r, y - r, x + r, y + r), fill=rgba(C("green"), 235))
            d.line((x - 11, y, x - 2, y + 10), fill=C("ink"), width=5)
            d.line((x - 2, y + 10, x + 13, y - 11), fill=C("ink"), width=5)
        for k in range(3):
            x, y = P(700 + k * 90, 1575)
            col = C("green") if p > 0.4 else C("yellow") if k == 0 else C("panel_light")
            d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=rgba(col, 230))

    elif scene == "ram":
        x0, y0 = P(110, 1320)
        x1, y1 = P(1130, 1420)
        prog = clamp(p * 1.18)
        rr(d, (x0 + 10, y0 + 10, x0 + 10 + (x1 - x0 - 20) * prog, y1 - 10), 16, rgba(C("cyan"), 225))
        cx, cy = P(620, 1710)
        start = -90 + p * 720
        d.arc((cx - 150, cy - 150, cx + 150, cy + 150), start, start + 250, fill=rgba(C("cyan"), 255), width=22)
        for k in range(22):
            q = (p * 2.4 + k / 22) % 1.0
            x, y = P(500 + q * 220, 870 + math.sin(q * 8 + k) * 18)
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=rgba(C("yellow"), 220))

    elif scene == "gpu":
        for i in range(10):
            for j in range(16):
                q = p * 1.35 - (i * 16 + j) / 220
                if q < 0 or q > 1:
                    continue
                x, y = P(150 + j * 60, 270 + i * 100)
                d.rounded_rectangle((x, y, x + 52, y + 88), 6, fill=rgba(C("cyan"), int(35 + 90 * (1 - q))))
        for i, bx in enumerate((400, 760)):
            x, y = P(bx, 1630)
            fan(d, x, y, 112, t_abs * (2.4 + i * 0.2), rgba(C("amber"), 220), rgba(C("panel_light"), 190))

    elif scene == "loop":
        cx, cy = P(620, 1100)
        r = 150 + 12 * pulse
        d.arc((cx - r, cy - r, cx + r, cy + r), t_abs * 60, t_abs * 60 + 280, fill=rgba(C("yellow"), 220), width=10)

    # partikel debu global
    rnd = random.Random(int(t_abs * 6) // 1)
    for _ in range(34):
        x = rnd.uniform(0, W)
        y = (rnd.uniform(0, H) + t_abs * 22) % H
        a = rnd.randint(16, 60)
        d.ellipse((x - 1.6, y - 1.6, x + 1.6, y + 1.6), fill=rgba(C("white"), a))


# ---------------------------------------------------------------------------
# CHROME: judul, progress, subtitle per-kata, watermark, kartu intro/outro
# ---------------------------------------------------------------------------

def chip_bar(d, step: float, accent):
    y0, y1 = 330, 400
    x0, x1 = 54, W - 54
    gap = 12
    cw = (x1 - x0 - gap * (len(STEPS) - 1)) / len(STEPS)
    for i, name in enumerate(STEPS):
        xa = x0 + i * (cw + gap)
        box = (xa, y0, xa + cw, y1)
        q = clamp(step - i)
        if q >= 1:
            fill, fg = rgba(C("green"), 240), C("ink")
        elif q > 0:
            fill, fg = rgba(accent, 240), C("ink")
        else:
            fill, fg = rgba((232, 240, 252), 235), C("ink")
        rr(d, box, 16, fill)
        txt(d, (xa + cw / 2, y0 + 27), name, 19, fg, "Bold", "mm")
        if q > 0:
            d.rounded_rectangle((xa + 8, y1 - 10, xa + 8 + (cw - 16) * q, y1 - 5), 2, fill=rgba(C("ink"), 150))
    # garis progres tipis
    d.rounded_rectangle((x0, y1 + 14, x1, y1 + 20), 3, fill=rgba(C("white"), 45))
    d.rounded_rectangle((x0, y1 + 14, x0 + (x1 - x0) * clamp(step / 6), y1 + 20), 3, fill=rgba(accent, 230))


def title_block(d, seg, p):
    slide = ease(min(1.0, p * 6))
    off = int((1 - slide) * -70)
    alpha = int(255 * slide)
    x = 60 + off
    txt(d, (x, 96), seg["eyebrow"], 26, rgba(C("cyan"), int(alpha * 0.9)), "SemiBold")
    txt(d, (x, 142), seg["title"][0], 58, rgba(C("white"), alpha), "ExtraBold")
    txt(d, (x, 210), seg["title"][1], 58, rgba(C(seg["accent"]), alpha), "ExtraBold")
    d.rounded_rectangle((x, 288, x + 96, 294), 3, fill=rgba(C(seg["accent"]), alpha))


def watermark(d, t_abs, alpha=210):
    pulse = 0.86 + 0.14 * math.sin(t_abs * 1.8)
    x, y = W - 62, H - 78
    d.rounded_rectangle((x - 306, y - 44, x + 8, y + 26), 18, fill=rgba(C("ink"), int(alpha * 0.55)))
    d.polygon(((x - 286, y - 24), (x - 262, y - 24), (x - 276, y - 2), (x - 252, y - 2),
               (x - 290, y + 18), (x - 278, y - 6), (x - 298, y - 6)), fill=rgba(C("yellow"), int(alpha * pulse)))
    txt(d, (x - 240, y - 9), WATERMARK, 34, rgba(C("white"), alpha), "ExtraBold", "lm")


def captions(d, words, active, window, accent, fade=1.0):
    """Subtitle per-kata: kata aktif disorot, baris otomatis dibungkus agar tidak keluar layar."""
    if active is None or not window or fade <= 0:
        return
    shown = [(window[0] + i, w) for i, w in enumerate(words[window[0]:window[1]])]
    if not shown:
        return
    font = F(44, "Bold")
    gap, maxw = 16, W - 180
    lines, cur, curw = [], [], 0
    for idx, word in shown:
        wd = d.textbbox((0, 0), word, font=font)[2]
        add = wd + (gap if cur else 0)
        if cur and curw + add > maxw:
            lines.append(cur)
            cur, curw = [], 0
            add = wd
        cur.append((idx, word, wd))
        curw += add
    lines.append(cur)

    line_h = 66
    total_h = len(lines) * line_h
    y0 = H - 470 - total_h / 2
    d.rounded_rectangle(
        (50, y0 - 18, W - 50, y0 + total_h + 2), 22,
        fill=rgba(C("ink"), int(210 * fade)),
        outline=rgba(C("white"), int(40 * fade)), width=2,
    )
    for li, line in enumerate(lines):
        lw = sum(wd for _, _, wd in line) + gap * (len(line) - 1)
        x = (W - lw) / 2
        y = y0 + li * line_h
        for idx, word, wd in line:
            if idx == active:
                d.rounded_rectangle((x - 8, y - 4, x + wd + 8, y + 58), 10,
                                    fill=rgba(accent, int(255 * fade)))
                txt(d, (x, y), word, 44, rgba(C("ink"), int(255 * fade)), "Bold")
            else:
                txt(d, (x, y), word, 44, rgba(C("white"), int(242 * fade)), "Bold")
            x += wd + gap


def intro_card(d, p, accent):
    a = int(255 * smooth(min(1.0, p * 3.5)) * (1 - smooth(max(0, (p - 0.78) / 0.22))))
    cx, cy = W / 2, H / 2 - 60
    d.rounded_rectangle((cx - 400, cy - 210, cx + 400, cy + 210), 40,
                        fill=rgba(C("ink"), int(a * 0.72)), outline=rgba(C("yellow"), a), width=5)
    txt(d, (cx, cy - 80), BRAND, 108, rgba(C("white"), a), "ExtraBold", "mm")
    txt(d, (cx, cy + 40), TAGLINE, 32, rgba(C("yellow"), a), "SemiBold", "mm")
    txt(d, (cx, cy + 120), "EP. 01  •  TOMBOL POWER", 26, rgba(C("muted"), a), "Medium", "mm")


def outro_card(d, p, accent):
    a = int(255 * smooth(min(1.0, p * 3.0)))
    cx, cy = W / 2, H / 2 - 40
    d.rounded_rectangle((cx - 430, cy - 260, cx + 430, cy + 260), 44,
                        fill=rgba(C("ink"), int(a * 0.80)), outline=rgba(C("yellow"), a), width=5)
    txt(d, (cx, cy - 150), BRAND, 92, rgba(C("white"), a), "ExtraBold", "mm")
    txt(d, (cx, cy - 40), "Simpan video ini", 44, rgba(C("yellow"), a), "Bold", "mm")
    txt(d, (cx, cy + 26), "Ikuti untuk tahu hal sehari-hari", 30, rgba(C("white"), a), "Medium", "mm")
    txt(d, (cx, cy + 140), "SAMPAI EPISODE BERIKUTNYA", 24, rgba(C("muted"), a), "SemiBold", "mm")


_VIG = None
_NOISE = np.random.default_rng(7).normal(0.0, 1.5, (2304, 2304)).astype(np.float32)


def finish(view: np.ndarray, frame_i: int) -> np.ndarray:
    """Vignette + grain halus. Vignette & noise di-cache agar 60 fps tercapai."""
    global _VIG
    h, w = view.shape[:2]
    if _VIG is None or _VIG.shape[:2] != (h, w):
        yy, xx = np.mgrid[0:h, 0:w]
        nx = (xx - w / 2) / (w / 2)
        ny = (yy - h / 2) / (h / 2)
        _VIG = np.clip(1 - 0.30 * (nx ** 2 + ny ** 2), 0.70, 1.0).astype(np.float32)[..., None]
    oy, ox = (frame_i * 7) % 384, (frame_i * 13) % 384
    out = view.astype(np.float32) * _VIG
    out += _NOISE[oy:oy + h, ox:ox + w, None]
    return np.uint8(np.clip(out, 0, 255))

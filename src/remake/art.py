#!/usr/bin/env python3
"""Tipografi & UI di atas frame 3D. Tanpa partikel, grain, glow, atau efek lain."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import ImageDraw, ImageFont

from script_kliktahu import BRAND

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "assets" / "fonts"
_FILES = {"Regular": "Poppins-Regular.ttf", "Medium": "Poppins-Medium.ttf",
          "SemiBold": "Poppins-SemiBold.ttf", "Bold": "Poppins-Bold.ttf",
          "ExtraBold": "Poppins-ExtraBold.ttf"}

COLORS = {
    "white": (245, 249, 255), "muted": (158, 178, 206), "yellow": (255, 199, 32),
    "amber": (255, 158, 46), "cyan": (62, 214, 255), "green": (46, 214, 145),
    "blue": (86, 146, 255), "red": (255, 92, 92), "ink": (8, 15, 30),
}


@lru_cache(maxsize=128)
def F(size, weight="Bold"):
    return ImageFont.truetype(str(FONT_DIR / _FILES[weight]), size)


def C(name):
    return COLORS[name]


def rgba(c, a=255):
    return (c[0], c[1], c[2], int(a))


def txt(d, xy, s, size, color, weight="Bold", anchor="la", stroke=0):
    d.text(xy, s, font=F(size, weight), fill=color, anchor=anchor,
           stroke_width=stroke, stroke_fill=(6, 12, 26, 220))


def scrims(d):
    """Gelap tipis agar teks terbaca; bukan efek dekoratif."""
    from script_kliktahu import H, W
    for i in range(14):
        a = int(140 * (1 - i / 14) ** 1.5)
        d.rectangle((0, i * 30, W, (i + 1) * 30), fill=(6, 12, 26, a))
    for i in range(16):
        y = H - 800 + i * 50
        a = int(185 * (i / 16) ** 1.3)
        d.rectangle((0, y, W, y + 50), fill=(6, 12, 26, a))


def chip_bar(d, step, accent):
    from script_kliktahu import STEPS, W
    x0, y, gap = 60, 322, 8
    cw = (W - 120 - gap * 5) / 6
    for i, label in enumerate(STEPS):
        x = x0 + i * (cw + gap)
        active = min(5, int(step))
        done = i < active
        cur = i == active
        fill = rgba(accent, 235) if done or cur else (34, 48, 72, 205)
        d.rounded_rectangle((x, y, x + cw, y + 48), 12, fill=fill,
                            outline=rgba(accent, 190) if cur else (70, 88, 118, 130), width=2)
        col = (10, 18, 32, 255) if done or cur else rgba(C("muted"), 205)
        f = F(19, "Bold")
        w = d.textlength(label, font=f)
        d.text(((x + cw / 2), y + 24), label, font=f, fill=col, anchor="mm")


def title_block(d, seg, p):
    from script_kliktahu import W
    accent = C(seg["accent"])
    a = int(230 * min(1.0, p / 0.10))
    txt(d, (60, 84), seg["eyebrow"], 26, rgba(accent, a), "Bold")
    txt(d, (60, 132), seg["title"][0], 62, rgba(C("white"), a), "ExtraBold", stroke=2)
    txt(d, (60, 208), seg["title"][1], 62, rgba(C("white"), a), "ExtraBold", stroke=2)
    d.rectangle((60, 296, 60 + 118 * min(1.0, p / 0.28), 300), fill=rgba(accent, a))


def captions(d, words, active, window, accent, fade=1.0):
    from script_kliktahu import H, W
    fade = max(0.0, min(1.0, fade))
    if fade <= 0.01:
        return
    lo, hi = window
    font = F(56, "Bold")
    space = d.textlength(" ", font=font)
    maxw = W - 150
    lines, cur, curw = [], [], 0.0
    for k in range(lo, hi):
        w = words[k]
        tw = d.textlength(w, font=font)
        if cur and curw + space + tw > maxw:
            lines.append(cur)
            cur, curw = [], 0.0
        cur.append((k, w, tw))
        curw += tw + space
    if cur:
        lines.append(cur)
    lh = 82
    y0 = H - 610 - (len(lines) - 1) * lh / 2
    for li, line in enumerate(lines):
        total = sum(tw for _, _, tw in line) + space * (len(line) - 1)
        x = (W - total) / 2
        y = y0 + li * lh
        for k, w, tw in line:
            if k == active:
                d.rounded_rectangle((x - 14, y - 10, x + tw + 14, y + 70), 14,
                                    fill=rgba(accent, int(62 * fade)))
                col = rgba(accent, int(255 * fade))
            else:
                col = rgba(C("white"), int(238 * fade))
            d.text((x, y), w, font=font, fill=col,
                   stroke_width=2, stroke_fill=(5, 11, 24, int(220 * fade)))
            x += tw + space


def watermark(d, t, alpha=225):
    from script_kliktahu import W, H
    x, y = W - 62, H - 92
    f = F(38, "ExtraBold")
    w = d.textlength(BRAND, font=f)
    d.text((x, y), BRAND, font=f, fill=rgba(C("white"), alpha), anchor="ra",
           stroke_width=2, stroke_fill=(6, 12, 26, alpha))
    d.rounded_rectangle((x - w - 14, y - 8, x - w - 6, y + 6), 3, fill=rgba(C("yellow"), alpha))


def outro_cta(d, p, accent):
    from script_kliktahu import W, H
    a = min(1.0, p / 0.22)
    w, h = 880, 300
    x, y = (W - w) / 2, H / 2 - 190
    d.rounded_rectangle((x, y, x + w, y + h), 36,
                        fill=(8, 16, 34, int(205 * a)),
                        outline=rgba(accent, int(230 * a)), width=5)
    txt(d, (W / 2, y + 82), "IKUTI KLIKTAHU!", 76, rgba(C("white"), int(255 * a)),
        "ExtraBold", anchor="mm", stroke=2)
    txt(d, (W / 2, y + 180), "Tahu hal yang kamu pakai tiap hari", 34,
        rgba(C("muted"), int(245 * a)), "Medium", anchor="mm")
    txt(d, (W / 2, y + 244), "TOMBOL POWER  ·  EP. 01", 26,
        rgba(accent, int(235 * a)), "Bold", anchor="mm")

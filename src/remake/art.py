#!/usr/bin/env python3
"""Tipografi & UI native-resolusi di atas frame 3D. Tanpa efek dekoratif."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from script_kliktahu import BRAND, H, STEPS, W

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "assets" / "fonts"
_FILES = {"Regular": "Poppins-Regular.ttf", "Medium": "Poppins-Medium.ttf",
          "SemiBold": "Poppins-SemiBold.ttf", "Bold": "Poppins-Bold.ttf",
          "ExtraBold": "Poppins-ExtraBold.ttf"}
SC = W / 1080.0

COLORS = {
    "white": (245, 249, 255), "muted": (158, 178, 206), "yellow": (252, 189, 10),
    "amber": (255, 158, 46), "cyan": (62, 214, 255), "green": (46, 214, 145),
    "blue": (86, 146, 255), "red": (255, 92, 92), "ink": (8, 15, 30),
}
UI = {
    "card": (238, 243, 250), "card_line": (196, 208, 224),
    "chip_idle": (226, 232, 240), "chip_done": (23, 138, 94),
    "chip_on": (252, 189, 10), "chip_ink": (14, 22, 36),
    "chip_muted": (94, 108, 128), "blue": (27, 79, 216),
    "yellow": (252, 189, 10), "green": (46, 214, 145),
    "pill": (244, 248, 255), "black": (9, 12, 20),
}


def q(v):
    return int(round(v * SC))


def fs(v):
    return max(1, int(round(v * SC)))


@lru_cache(maxsize=128)
def F(size, weight="Bold"):
    return ImageFont.truetype(str(FONT_DIR / _FILES[weight]), fs(size))


def C(name):
    return COLORS[name]


def rgba(c, a=255):
    return (c[0], c[1], c[2], int(a))


def txt(d, xy, s, size, color, weight="Bold", anchor="la", stroke=0):
    d.text((q(xy[0]), q(xy[1])), s, font=F(size, weight), fill=color, anchor=anchor,
           stroke_width=max(1, q(stroke)) if stroke else 0,
           stroke_fill=(6, 12, 26, 220))


def scrims(d):
    for i in range(14):
        a = int(140 * (1 - i / 14) ** 1.5)
        d.rectangle((0, q(i * 30), W, q((i + 1) * 30)), fill=(6, 12, 26, a))
    for i in range(16):
        y = q(H / SC - 800 + i * 50)
        a = int(185 * (i / 16) ** 1.3)
        d.rectangle((0, y, W, y + q(50)), fill=(6, 12, 26, a))


def chip_icon(d, cx, cy, i, col, alpha=255):
    """Ikon garis kecil untuk tiap chip (vektor, bukan gambar)."""
    c = rgba(col, alpha)
    lw = max(1, q(1.6))
    if i == 0:                                   # motherboard
        d.rounded_rectangle((cx - q(11), cy - q(9), cx + q(11), cy + q(9)), q(2),
                            outline=c, width=lw)
        d.rectangle((cx - q(5), cy - q(4), cx + q(5), cy + q(4)), outline=c, width=lw)
        for dx in (-7, 0, 7):
            d.line((cx + q(dx), cy - q(9), cx + q(dx), cy - q(12)), fill=c, width=lw)
    elif i == 1:                                 # PSU / kipas
        d.rounded_rectangle((cx - q(11), cy - q(9), cx + q(11), cy + q(9)), q(2),
                            outline=c, width=lw)
        d.ellipse((cx - q(6), cy - q(6), cx + q(6), cy + q(6)), outline=c, width=lw)
        d.ellipse((cx - q(1.5), cy - q(1.5), cx + q(1.5), cy + q(1.5)), fill=c)
    elif i == 2:                                 # CPU
        d.rectangle((cx - q(8), cy - q(8), cx + q(8), cy + q(8)), outline=c, width=lw)
        d.rectangle((cx - q(3), cy - q(3), cx + q(3), cy + q(3)), outline=c, width=lw)
        for k in (-6, 0, 6):
            d.line((cx + q(k), cy - q(8), cx + q(k), cy - q(11)), fill=c, width=lw)
            d.line((cx + q(k), cy + q(8), cx + q(k), cy + q(11)), fill=c, width=lw)
    elif i == 3:                                 # RAM
        d.rounded_rectangle((cx - q(12), cy - q(7), cx + q(12), cy + q(7)), q(2),
                            outline=c, width=lw)
        for k in range(4):
            d.rectangle((cx - q(9) + k * q(5.5), cy - q(3),
                         cx - q(6) + k * q(5.5), cy + q(3)), fill=c)
    elif i == 4:                                 # GPU
        d.rounded_rectangle((cx - q(12), cy - q(8), cx + q(12), cy + q(8)), q(2),
                            outline=c, width=lw)
        for k in (-5.5, 5.5):
            d.ellipse((cx + q(k - 3), cy - q(3), cx + q(k + 3), cy + q(3)),
                      outline=c, width=lw)
    else:                                        # storage
        d.rounded_rectangle((cx - q(12), cy - q(8), cx + q(12), cy + q(8)), q(2),
                            outline=c, width=lw)
        d.line((cx - q(7), cy, cx + q(3), cy), fill=c, width=lw)
        d.ellipse((cx + q(6), cy - q(2), cx + q(9), cy + q(2)), outline=c, width=lw)


def chip_bar(d, step, accent, extra_done=()):
    """Kartu putih 6 chip: hijau = selesai, kuning = aktif, abu = belum."""
    x0, y, gap = q(52), q(316), q(6)
    card_h = q(92)
    d.rounded_rectangle((x0, y, W - x0, y + card_h), q(20),
                        fill=rgba(UI["card"], 252),
                        outline=rgba(UI["card_line"], 220), width=max(1, q(2)))
    ix, iy = x0 + q(9), y + q(9)
    ih = card_h - q(18)
    cw = (W - 2 * ix - gap * 5) / 6
    for i, label in enumerate(STEPS):
        x = ix + i * (cw + gap)
        done, cur = (i < step or i in extra_done) and i != step, i == step
        fill = UI["chip_done"] if done else UI["chip_on"] if cur else UI["chip_idle"]
        fg = (245, 249, 255) if done else UI["chip_ink"] if cur else UI["chip_muted"]
        d.rounded_rectangle((x, iy, x + cw, iy + ih), q(12), fill=rgba(fill, 255),
                            outline=rgba((255, 255, 255), 150 if cur else 110),
                            width=max(1, q(1)))
        chip_icon(d, x + cw / 2, iy + q(26), i, fg)
        d.text((x + cw / 2, iy + q(56)), label, font=F(15, "Bold"),
               fill=rgba(fg, 255), anchor="mm")


def title_block(d, seg, p):
    accent = C(seg["accent"])
    a = 255
    txt(d, (60, 84), seg["eyebrow"], 26, rgba(accent, a), "Bold")
    txt(d, (60, 132), seg["title"][0], 62, rgba(C("white"), a), "ExtraBold", stroke=2)
    txt(d, (60, 208), seg["title"][1], 62, rgba(UI["yellow"], a), "ExtraBold", stroke=2)
    d.rectangle((q(60), q(296), q(60 + 118 * min(1.0, p / 0.28)), q(300)),
                fill=rgba(accent, a))


def captions(d, words, active, window, accent, fade=1.0):
    fade = max(0.0, min(1.0, fade))
    if fade <= 0.01:
        return
    lo, hi = window
    font = F(56, "Bold")
    space = d.textlength(" ", font=font)
    maxw = W - q(150)
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
    lh = q(86)
    y0 = H - q(600) - (len(lines) - 1) * lh / 2
    widths = [sum(tw for _, _, tw in ln) + space * (len(ln) - 1) for ln in lines]
    box_w = max(widths) + q(58)
    box_h = len(lines) * lh + q(34)
    bx, by = (W - box_w) / 2, y0 - q(26)
    d.rounded_rectangle((bx, by, bx + box_w, by + box_h), q(22),
                        fill=(9, 12, 20, int(230 * fade)))
    for li, line in enumerate(lines):
        x = (W - widths[li]) / 2
        y = y0 + li * lh
        for k, w, tw in line:
            if k == active:
                d.rounded_rectangle((x - q(12), y - q(8), x + tw + q(12), y + q(74)),
                                    q(14), fill=rgba(UI["yellow"], int(255 * fade)))
                col = rgba(UI["black"], int(255 * fade))
            else:
                col = rgba(C("white"), int(248 * fade))
            d.text((x, y), w, font=font, fill=col)
            x += tw + space


def pill(d, x, y, text, fill, fg, size=20, alpha=255, shift=0, h=46, pad=18):
    """Pil label: kuning/biru/putih dengan teks uppercase."""
    f = F(size, "Bold")
    tw = d.textlength(text, font=f)
    w, hh = tw + q(pad * 2), q(h)
    px, py = q(x) - shift, q(y)
    d.rounded_rectangle((px, py, px + w, py + hh), hh / 2,
                        fill=rgba(fill, int(alpha)))
    d.text((px + w / 2, py + hh / 2), text, font=f,
           fill=rgba(fg, int(alpha)), anchor="mm")
    return w, hh


def leader(d, x, y, text, target, alpha=1.0, shift=0):
    """Pil putih + garis penunjuk ke titik komponen."""
    c = (232, 240, 252, int(215 * alpha))
    w, hh = pill(d, x, y, text, UI["pill"], UI["black"], size=19,
                 alpha=int(248 * alpha), shift=shift, h=42, pad=14)
    sx, sy = q(x) - shift, q(y)
    start = (sx, sy + hh / 2)
    elbow = (sx - q(30), sy + hh / 2 + q(26))
    end = (q(target[0]), q(target[1]))
    d.line((start, elbow, end), fill=c, width=max(1, q(1.6)), joint="curve")
    r = q(6)
    d.ellipse((end[0] - r, end[1] - r, end[0] + r, end[1] + r),
              outline=c, width=max(1, q(2)))
    d.ellipse((end[0] - q(1.5), end[1] - q(1.5), end[0] + q(1.5), end[1] + q(1.5)),
              fill=c)


def callouts(d, item, alpha):
    a = max(0.0, min(1.0, alpha))
    if a <= 0.01:
        return
    shift = int(q(30) * (1 - a))
    pill(d, 60, 1096, item["tag"], UI["yellow"], UI["black"], size=20,
         alpha=int(255 * a), shift=shift)
    pill(d, 60, 1188, item["info"], UI["blue"], (255, 255, 255), size=18,
         alpha=int(240 * a), shift=shift)
    leader(d, 600, 920, item["lead"], item["pt"], alpha=a, shift=shift)


def loading_bar(d, pct, alpha):
    a = max(0.0, min(1.0, alpha))
    if a <= 0.01:
        return
    x, y, w, h = q(60), q(860), W - q(120), q(16)
    d.rounded_rectangle((x, y, x + w, y + h), h / 2,
                        fill=(18, 30, 56, int(225 * a)))
    d.rounded_rectangle((x, y, x + w * pct / 100.0, y + h), h / 2,
                        fill=rgba(UI["blue"], int(255 * a)))
    pill(d, 60, 790, f"MEMUAT SISTEM  {int(pct):02d}%", UI["blue"], (255, 255, 255),
         size=20, alpha=int(245 * a), h=46)


def stamp(frame, alpha):
    a = max(0.0, min(1.0, alpha))
    if a <= 0.01:
        return
    text = "SIAP DIPAKAI!"
    f = F(60, "ExtraBold")
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    tw = probe.textlength(text, font=f)
    tmp = Image.new("RGBA", (int(tw) + q(70), q(130)), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    td.text((tmp.width / 2, tmp.height / 2), text, font=f,
            fill=rgba(UI["green"], int(255 * a)), anchor="mm",
            stroke_width=max(1, q(2)), stroke_fill=(5, 20, 16, int(230 * a)))
    rot = tmp.rotate(9, expand=True, resample=Image.BICUBIC)
    frame.paste(rot, (int((W - rot.width) / 2), q(688)), rot)


def watermark(d, t, alpha=225):
    x, y = W - q(62), H - q(92)
    f = F(38, "ExtraBold")
    w = d.textlength(BRAND, font=f)
    d.text((x, y), BRAND, font=f, fill=rgba(C("white"), alpha), anchor="ra",
           stroke_width=max(1, q(2)), stroke_fill=(6, 12, 26, alpha))
    d.rounded_rectangle((x - w - q(14), y - q(8), x - w - q(6), y + q(6)),
                        q(3), fill=rgba(C("yellow"), alpha))


def outro_cta(d, p, accent):
    a = min(1.0, p / 0.22)
    w, h = q(880), q(300)
    x, y = (W - w) / 2, H / 2 - q(190)
    d.rounded_rectangle((x, y, x + w, y + h), q(36),
                        fill=(8, 16, 34, int(205 * a)),
                        outline=rgba(accent, int(230 * a)), width=max(1, q(5)))
    txt(d, (W / 2 / SC, (y + q(82)) / SC), "IKUTI KLIKTAHU!", 76,
        rgba(C("white"), int(255 * a)), "ExtraBold", anchor="mm", stroke=2)
    txt(d, (W / 2 / SC, (y + q(180)) / SC), "Tahu hal yang kamu pakai tiap hari", 34,
        rgba(C("muted"), int(245 * a)), "Medium", anchor="mm")
    txt(d, (W / 2 / SC, (y + q(244)) / SC), "TOMBOL POWER  ·  KLIKTAHU", 26,
        rgba(accent, int(235 * a)), "Bold", anchor="mm")

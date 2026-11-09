#!/usr/bin/env python3
"""Renderer 3D dengan z-buffer per-piksel (C), perspektif benar, Gouraud, SSAA.

Geometri & shading-divvektorisasi di numpy, loop piksel ada di raster.c.
Depth test per-piksel = tidak ada objek yang saling tembus.
"""
from __future__ import annotations

import ctypes
import math
import subprocess
from pathlib import Path

import cv2
import numpy as np

import geom3d as G
import ssao

USE_SSAO = True          # SSAO Numba (normal rekonstruksi + 16 sampel hemisfer)
ENV_N = 64               # resolusi matcap studio (prosedural, bukan gambar)

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "remake" / "raster.c"
LIB = ROOT / "build" / "raster.so"

_L1, _L2 = G._L1, G._L2
_KEY, _RIM, _SPEC = G._KEY, G._RIM, G._SPEC
_FILL = np.array([0.80, 0.88, 1.00], np.float32)
_LIB = None
_BG = {}


def _make_env(n=ENV_N):
    """Matcap studio prosedural: langit, lantai, 3 softbox, rim hangat.

    Dihitung sekali dari rumus (bukan aset gambar), dipakai sebagai pantulan
    image-based lighting untuk permukaan logam di rasterizer C.
    """
    x = (np.arange(n, dtype=np.float32) + 0.5) / n * 2 - 1
    y = 1 - (np.arange(n, dtype=np.float32) + 0.5) / n * 2
    NX, NY = np.meshgrid(x, y)
    NZ = np.sqrt(np.clip(1 - NX * NX - NY * NY, 0, 1))
    up = np.clip(NY * 0.5 + 0.5, 0, 1)
    env = np.stack([0.045 + 0.145 * up + 0.055 * NZ,
                    0.075 + 0.205 * up + 0.075 * NZ,
                    0.125 + 0.320 * up + 0.105 * NZ], axis=-1)

    def soft(cx, cy, sx, sy, power=2.0):
        d = ((NX - cx) / sx) ** 2 + ((NY - cy) / sy) ** 2
        return np.exp(-np.clip(d ** power, 0, 60))

    key = soft(-0.40, 0.56, 0.30, 0.44)
    fill = soft(0.56, 0.16, 0.24, 0.60)
    strip = soft(0.02, -0.58, 0.78, 0.11)
    rim = soft(0.78, 0.62, 0.20, 0.30)
    env += key[..., None] * np.array([1.00, 1.04, 1.12], np.float32) * 0.92
    env += fill[..., None] * np.array([1.10, 0.90, 0.70], np.float32) * 0.42
    env += strip[..., None] * np.array([0.55, 0.92, 1.18], np.float32) * 0.30
    env += rim[..., None] * np.array([1.12, 0.82, 0.58], np.float32) * 0.26
    env *= 1.0 - 0.42 * np.clip((-NY - 0.45) / 0.55, 0, 1)[..., None]
    return np.ascontiguousarray(np.clip(env, 0, 1.25), dtype=np.float32)


ENV = _make_env()


def _lib():
    if not LIB.exists():
        LIB.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["gcc", "-O3", "-march=native", "-ffast-math", "-shared", "-fPIC",
                        "-o", str(LIB), str(SRC), "-lm"], check=True)
    lib = ctypes.CDLL(str(LIB))
    lib.raster.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int] + [ctypes.c_void_p] * 13
    lib.raster.restype = None
    lib.post.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
    lib.post.restype = None
    return lib


def _collect(scene):
    """Bayangan di awal, opaque di tengah, kaca/transparan di akhir."""
    first, opaque, last = [], [], []
    for lst, late in ((scene.pre, False), (scene.faces, True), (scene.post, True)):
        for polys, mat in lst:
            for poly in polys:
                p = np.asarray(poly, np.float32)
                m = len(p)
                if m < 3:
                    continue
                # Poligon besar dipecah jadi kipas segitiga di sekitar centroid:
                # bounding box tiap segitiga kecil -> loop C jauh lebih sedikit.
                if m >= 5:
                    ctr = p.mean(axis=0)
                    parts = [np.array([ctr, p[i], p[(i + 1) % m]], np.float32)
                             for i in range(m)]
                else:
                    parts = [p]
                for part in parts:
                    item = (part, mat)
                    if mat[3] < 0.999:
                        (last if late else first).append(item)
                    else:
                        opaque.append(item)
    return first + opaque + last


def build_triangles(scene, cam, RW, RH):
    global _LIB
    pos, B, _ = G._basis(cam)
    f = (RH / 2) / math.tan(math.radians(cam.fov) / 2)
    cx, cy = RW / 2, RH / 2
    faces = _collect(scene)
    F = len(faces)
    if not F:
        return 0, None

    polys = [p for p, _ in faces]
    counts = np.array([len(p) for p in polys], np.int32)
    starts = np.concatenate([[0], np.cumsum(counts)[:-1]])
    V = np.concatenate(polys, axis=0)
    rep = np.repeat(np.arange(F), counts)

    # normal per muka + normal rata-rata per titik (smooth untuk silinder,
    # tetap tajam untuk sisi kotak)
    fn = np.cross(V[starts + 1] - V[starts], V[starts + 2] - V[starts])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-6)
    keys = np.round(V, 4)
    _uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    acc = np.zeros((_uniq.shape[0], 3), np.float32)
    np.add.at(acc, inv, fn[rep])
    acc /= np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-6)
    avg = acc[inv]
    d = np.sum(fn[rep] * avg, axis=1)
    VN = np.where((d > 0.72)[:, None], avg, fn[rep])

    base = np.stack([m[0] for _, m in faces])
    metal = np.array([m[1] for _, m in faces], np.float32)
    shine = np.array([m[2] for _, m in faces], np.float32)
    alpha = np.array([m[3] for _, m in faces], np.float32)
    emis = np.array([m[5] for _, m in faces], np.float32)
    BASE, METAL, SHINE, ALPHA, EMIS = (x[rep] for x in (base, metal, shine, alpha, emis))

    # pencahayaan per titik (satu operasi array untuk semua titik)
    to = pos - V
    to /= np.maximum(np.linalg.norm(to, axis=1, keepdims=True), 1e-6)
    flip = np.sum(VN * to, axis=1) < 0
    VN = np.where(flip[:, None], -VN, VN)
    d1 = np.maximum(0.0, VN @ _L1)
    d2 = np.maximum(0.0, VN @ _L2)
    df = np.maximum(0.0, np.sum(VN * to, axis=1))
    term = (0.27 + 1.05 * d1[:, None] * _KEY[None, :]
            + 0.62 * d2[:, None] * _RIM[None, :]
            + 0.26 * df[:, None] * _FILL[None, :])
    col = BASE * term
    h = G.norm(_L1 + to.mean(axis=0))
    spec = (METAL[:, None] * np.maximum(0.0, (VN @ h)[:, None]) ** SHINE[:, None]
            if np.any(METAL) else 0.0)
    fres = METAL * 0.22 * (1.0 - df) ** 2
    col = col + (0.30 * spec + 0.25 * fres[:, None]) * _SPEC[None, :]
    col = col * (1 - EMIS[:, None]) + np.minimum(BASE * 1.55, 1.0) * EMIS[:, None]
    RGB = np.clip(col * 1.12, 0, 1) ** 0.92 * 255.0

    # proyeksi perspektif
    camv = (V - pos) @ B.T
    z = camv[:, 2]
    sx = cx + f * camv[:, 0] / np.maximum(z, 1e-6)
    sy = cy - f * camv[:, 1] / np.maximum(z, 1e-6)
    iz = 1.0 / np.maximum(z, 1e-6)
    zmin = np.minimum.reduceat(z, starts)
    good = (zmin > 0.06) & np.isfinite(zmin)

    tri = []
    for fi in range(F):
        if not good[fi]:
            continue
        st, m = starts[fi], counts[fi]
        for i in range(1, m - 1):
            tri.append((st, st + i, st + i + 1))
    if not tri:
        return 0, None
    T = np.asarray(tri, np.int32)
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    area = ((sx[b] - sx[a]) * (sy[c] - sy[a])
            - (sx[c] - sx[a]) * (sy[b] - sy[a]))
    keep = np.abs(area) > 1e-7
    a, b, c, area = a[keep], b[keep], c[keep], area[keep]
    neg = area < 0
    bb, cc = np.where(neg, c, b), np.where(neg, b, c)
    n = len(a)
    if not n:
        return 0, None

    # Mikro-tekstur prosedural: pola dipilih dari sifat material per muka.
    r, g, b_ = base[:, 0], base[:, 1], base[:, 2]
    mx = base.max(axis=1)
    pat = np.zeros(F, np.float32)
    opaque = (alpha > 0.99) & (emis < 0.15)
    pat[(mx < 0.13) & opaque] = 3
    pat[(mx >= 0.13) & (mx < 0.50) & (metal < 0.55) & opaque] = 4
    pat[(metal > 0.65) & opaque] = 1
    pat[(g > r * 1.25) & (g > b_ * 1.08) & (r < 0.22) & opaque] = 2
    PM = np.stack([metal, shine, pat], axis=1)
    pm = np.ascontiguousarray(PM[rep[a]], dtype=np.float32)

    # Normal & posisi dunia diskalakan 1/z -> interpolasi perspektif-benar.
    vn_scaled = (VN @ B.T) * iz[:, None]
    vp_scaled = V * iz[:, None]
    toview = np.array([0.0, 0.0, -1.0], np.float32)
    h1 = G.norm(G._L1 @ B.T + toview)
    h2 = G.norm(G._L2 @ B.T + toview)
    lit = np.concatenate([h1, h2, G._SPEC]).astype(np.float32)

    vx = np.stack([sx[a], sx[bb], sx[cc]], axis=1).ravel()
    vy = np.stack([sy[a], sy[bb], sy[cc]], axis=1).ravel()
    viz = np.stack([iz[a], iz[bb], iz[cc]], axis=1).ravel()
    vc = np.stack([RGB[a], RGB[bb], RGB[cc]], axis=1).reshape(-1, 3).ravel()
    vn = np.stack([vn_scaled[a], vn_scaled[bb], vn_scaled[cc]], axis=1).reshape(-1, 3).ravel()
    vp = np.stack([vp_scaled[a], vp_scaled[bb], vp_scaled[cc]], axis=1).reshape(-1, 3).ravel()
    va = np.round(ALPHA[a] * 255).astype(np.uint8)
    vb = (ALPHA[a] < 0.999).astype(np.uint8)

    def ct(x, dt):
        return np.ascontiguousarray(x, dtype=dt)
    return n, (ct(vx, np.float32), ct(vy, np.float32), ct(viz, np.float32),
               ct(vc, np.float32), ct(vn, np.float32), ct(vp, np.float32),
               va, vb, pm, ct(lit, np.float32), ENV)


def render(scene, cam, W, H, ss=1.0, zbuf=None):
    global _LIB
    if _LIB is None:
        _LIB = _lib()
    RW, RH = (W, H) if ss == 1.0 else (int(W * ss), int(H * ss))

    global _BG
    key = (RW, RH, tuple(scene.top.tolist()), tuple(scene.bottom.tolist()))
    if key not in _BG:
        t = np.linspace(0, 1, RH, dtype=np.float32)[:, None, None]
        bg = scene.top[None, None, :] * (1 - t) + scene.bottom[None, None, :] * t
        # Penumbra area-light dibakar SEKALI ke latar: gratis per frame,
        # jauh lebih murah daripada 14 poligon bayangan transparan.
        yy = np.linspace(0, 1, RH, dtype=np.float32)[:, None]
        xx = np.linspace(0, 1, RW, dtype=np.float32)[None, :]
        d = ((xx - 0.50) / 0.36) ** 2 + ((yy - 0.80) / 0.115) ** 2
        shade = (1.0 - 0.40 * np.exp(-np.clip(d, 0, 25)))[..., None]
        _BG[key] = np.ascontiguousarray(
            np.clip(bg * shade, 0, 255).astype(np.uint8))
    rgb = _BG[key].copy()
    if zbuf is None or zbuf.size != RW * RH:
        zbuf = np.zeros(RW * RH, np.float32)
    else:
        zbuf.fill(0)

    n, tri = build_triangles(scene, cam, RW, RH)
    if n:
        vx, vy, viz, vc, vn, vp, va, vb, pm, lit, env = tri
        _LIB.raster(RW, RH, n, vx.ctypes.data, vy.ctypes.data, viz.ctypes.data,
                    vc.ctypes.data, vn.ctypes.data, vp.ctypes.data,
                    va.ctypes.data, vb.ctypes.data, pm.ctypes.data, lit.ctypes.data,
                    env.ctypes.data, zbuf.ctypes.data, rgb.ctypes.data)
    ao_map = None
    if USE_SSAO:
        ao_map = ssao.compute(zbuf, RW, RH, cam.fov)
    else:
        _LIB.post(RW, RH, zbuf.ctypes.data, rgb.ctypes.data)
    if ss != 1.0:
        rgb = cv2.resize(rgb, (W, H), interpolation=cv2.INTER_AREA)
    if ao_map is not None:
        rgb = ssao.apply(rgb, ao_map, W, H)
    return np.ascontiguousarray(rgb)

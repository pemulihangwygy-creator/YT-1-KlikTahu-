#!/usr/bin/env python3
"""Screen-space ambient occlusion (Numba JIT) dari z-buffer perspektif.

Normal view-space direkonstruksi dari gradien kedalaman, lalu 16 sampel
hemisfer cosine-weighted diuji terhadap kedalaman scene. Hasilnya di-blur
dan dipakai sebagai faktor pencahayaan. Berjalan di CPU tanpa GPU/OpenGL.
"""
from __future__ import annotations

import math

import cv2
import numpy as np
from numba import njit, prange

STEP = 6
SAMPLES = 16
ROTS = 8
GOLDEN = 2.39996322972865332


def _directions():
    """Tabel arah hemisfer cosine-weighted, 8 rotasi (tanpa trig di kernel)."""
    d = np.zeros((ROTS, SAMPLES, 3), np.float32)
    for r in range(ROTS):
        rot = r * 0.61803398875 * 6.28318530718
        for k in range(SAMPLES):
            rr = math.sqrt((k + 0.5) / SAMPLES)
            a = k * GOLDEN + rot
            d[r, k, 0] = rr * math.cos(a)
            d[r, k, 1] = rr * math.sin(a)
            d[r, k, 2] = math.sqrt(max(0.0, 1.0 - rr * rr))
    return d


_DIRS = _directions()


@njit(parallel=True, fastmath=True, cache=True)
def _kernel(iz, dirs, W, H, f, cx, cy, radius, strength, out):
    HW = W // STEP
    HH = H // STEP
    for hy in prange(HH):
        y = hy * STEP + STEP // 2
        for hx in range(HW):
            x = hx * STEP + STEP // 2
            idx = y * W + x
            if iz[idx] <= 1e-6:
                out[hy, hx] = 1.0
                continue
            zc = 1.0 / iz[idx]
            zl = 1.0 / iz[idx - 2] if iz[idx - 2] > 1e-6 else zc
            zr = 1.0 / iz[idx + 2] if iz[idx + 2] > 1e-6 else zc
            zu = 1.0 / iz[idx - 2 * W] if iz[idx - 2 * W] > 1e-6 else zc
            zd = 1.0 / iz[idx + 2 * W] if iz[idx + 2 * W] > 1e-6 else zc
            dxz = (zr - zl) * 0.25
            dyz = (zd - zu) * 0.25
            ox = (x - cx) / f
            oy = -(y - cy) / f

            # dP/dx, dP/dy dalam koordinat kamera
            tx0 = zc / f + ox * dxz
            tx1 = oy * dxz
            tx2 = dxz
            ty0 = ox * dyz
            ty1 = -zc / f + oy * dyz
            ty2 = dyz
            nx = tx1 * ty2 - tx2 * ty1
            ny = tx2 * ty0 - tx0 * ty2
            nz = tx0 * ty1 - tx1 * ty0
            ln = math.sqrt(nx * nx + ny * ny + nz * nz)
            if ln < 1e-8:
                out[hy, hx] = 1.0
                continue
            nx /= ln
            ny /= ln
            nz /= ln
            if nz < 0.0:
                nx, ny, nz = -nx, -ny, -nz

            # basis tangen untuk hemisfer
            ax, ay, az = 0.0, 0.0, 1.0
            if nz > 0.85:
                ax, ay, az = 0.0, 1.0, 0.0
            ux = ay * nz - az * ny
            uy = az * nx - ax * nz
            uz = ax * ny - ay * nx
            ul = math.sqrt(ux * ux + uy * uy + uz * uz)
            if ul < 1e-8:
                out[hy, hx] = 1.0
                continue
            ux /= ul
            uy /= ul
            uz /= ul
            bx = ny * uz - nz * uy
            by = nz * ux - nx * uz
            bz = nx * uy - ny * ux

            px, py = ox * zc, oy * zc
            rot = (x * 3 + y * 5) % ROTS
            occ = 0.0
            for k in range(SAMPLES):
                hxv, hyv, hzv = dirs[rot, k, 0], dirs[rot, k, 1], dirs[rot, k, 2]
                r = math.sqrt(hxv * hxv + hyv * hyv)
                dx = ux * hxv + bx * hyv + nx * hzv
                dy = uy * hxv + by * hyv + ny * hzv
                dz = uz * hxv + bz * hyv + nz * hzv
                scale = radius * (0.25 + 0.75 * r)
                sx = px + dx * scale
                sy = py + dy * scale
                sz = zc + dz * scale
                if sz < 0.05:
                    continue
                u = cx + f * sx / sz
                v = cy - f * sy / sz
                iu = int(u + 0.5)
                iv = int(v + 0.5)
                if iu < 0 or iu >= W or iv < 0 or iv >= H:
                    continue
                s_iz = iz[iv * W + iu]
                if s_iz <= 1e-6:
                    continue
                sz_sample = 1.0 / s_iz
                diff = sz - sz_sample
                if diff > 0.012:
                    falloff = 1.0 - min(1.0, diff / (radius * 1.5))
                    occ += hzv * falloff
            ao = 1.0 - strength * occ / SAMPLES
            out[hy, hx] = 0.55 if ao < 0.55 else (1.0 if ao > 1.0 else ao)


@njit(parallel=True, fastmath=True, cache=True)
def _apply(flat_rgb, a, flat_out):
    H, W = a.shape
    for y in prange(H):
        row = y * W
        for x in range(W):
            v = a[y, x]
            i = (row + x) * 3
            r = flat_rgb[i] * v
            g = flat_rgb[i + 1] * v
            b = flat_rgb[i + 2] * v
            flat_out[i] = 255 if r > 255 else (0 if r < 0 else int(r))
            flat_out[i + 1] = 255 if g > 255 else (0 if g < 0 else int(g))
            flat_out[i + 2] = 255 if b > 255 else (0 if b < 0 else int(b))


def apply(rgb, ao_map, W, H):
    """Naikkan resolusi peta AO, haluskan, lalu kalikan ke warna (Numba)."""
    a = cv2.resize(ao_map, (W, H), interpolation=cv2.INTER_LINEAR)
    a = cv2.GaussianBlur(a, (0, 0), 1.1)
    # Permukaan terang / emissive jangan diredupkan AO (layar, LED, jendela).
    small = cv2.resize(rgb, (max(1, W // 4), max(1, H // 4)),
                       interpolation=cv2.INTER_AREA)
    lum = small.max(axis=2).astype(np.float32) / 255.0
    pres = cv2.resize(lum, (W, H), interpolation=cv2.INTER_LINEAR)
    np.maximum(a, pres, out=a)
    flat = np.ascontiguousarray(rgb).ravel()
    out = np.empty_like(flat)
    _apply(flat, np.ascontiguousarray(a, dtype=np.float32), out)
    return out.reshape(rgb.shape)


def compute(iz, W, H, fov_deg, radius=0.17, strength=1.35):
    """Kembalikan peta AO float32 berukuran (H/STEP, W/STEP)."""
    f = (H / 2.0) / math.tan(math.radians(fov_deg) / 2.0)
    z = np.ascontiguousarray(iz.reshape(H, W), dtype=np.float32).ravel()
    out = np.ones((H // STEP, W // STEP), np.float32)
    _kernel(z, _DIRS, W, H, f, W / 2.0, H / 2.0, radius, strength, out)
    return out

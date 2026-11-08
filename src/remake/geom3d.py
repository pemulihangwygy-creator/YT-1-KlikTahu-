#!/usr/bin/env python3
"""Rasterizer 3D software: kamera perspektif, shading, z-sort, supersampling.

Semua geometri dibangun dari primitif (box, silinder, cincin, bilah kipas).
Tidak ada tekstur, foto, atau aset gambar eksternal.
"""
from __future__ import annotations

import math

import cv2
import numpy as np


def norm(v):
    v = np.asarray(v, np.float32)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else v


def M(rgb, metal=0.0, shine=24, alpha=1.0, edge=0.0, emissive=0.0):
    """Material: warna, kilau logam, alpha, garis tepi, emisi (LED/layar)."""
    return (np.asarray(rgb, np.float32) / 255.0, float(metal), float(shine),
            float(alpha), float(edge), float(emissive))


def rotmat(rx=0.0, ry=0.0, rz=0.0):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], np.float32)
            @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], np.float32)
            @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], np.float32))


def transform(polys, rot=(0, 0, 0), shift=(0, 0, 0)):
    R = rotmat(*rot)
    s = np.asarray(shift, np.float32)
    return [np.asarray(p, np.float32) @ R.T + s for p in polys]


_BOX_FACES = ((4, 5, 6, 7), (1, 0, 3, 2), (5, 1, 2, 6),
              (0, 4, 7, 3), (7, 6, 2, 3), (0, 1, 5, 4))


def box(c, s, rot=(0, 0, 0)):
    hx, hy, hz = np.asarray(s, np.float32) / 2
    v = np.array([[-hx, -hy, -hz], [hx, -hy, -hz], [hx, hy, -hz], [-hx, hy, -hz],
                  [-hx, -hy, hz], [hx, -hy, hz], [hx, hy, hz], [-hx, hy, hz]], np.float32)
    return transform([v[list(i)] for i in _BOX_FACES], rot, c)


def cyl(c, a, r, length, n=12, caps=True, phase=0.0):
    axis = norm(a)
    ref = np.array([0, 1, 0], np.float32) if abs(axis[1]) < 0.9 else np.array([1, 0, 0], np.float32)
    u = norm(np.cross(axis, ref))
    v = np.cross(axis, u)
    th = np.arange(n, dtype=np.float32) * (2 * math.pi / n) + phase
    ring = np.cos(th)[:, None] * u[None, :] + np.sin(th)[:, None] * v[None, :]
    c = np.asarray(c, np.float32)
    r0 = c - axis * (length / 2) + r * ring
    r1 = c + axis * (length / 2) + r * ring
    out = [np.array([r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]], np.float32)
           for i in range(n)]
    if caps:
        out += [r0[::-1].copy(), r1.copy()]
    return out


def annulus(c, a, r0, r1, n=14, phase=0.0):
    axis = norm(a)
    ref = np.array([0, 1, 0], np.float32) if abs(axis[1]) < 0.9 else np.array([1, 0, 0], np.float32)
    u = norm(np.cross(axis, ref))
    v = np.cross(axis, u)
    th = np.arange(n, dtype=np.float32) * (2 * math.pi / n) + phase
    cs = np.cos(th)[:, None] * u[None, :] + np.sin(th)[:, None] * v[None, :]
    c = np.asarray(c, np.float32)
    inner, outer = c + r0 * cs, c + r1 * cs
    return [np.array([inner[i], outer[i], outer[(i + 1) % n], inner[(i + 1) % n]], np.float32)
            for i in range(n)]


def disc(c, a, r, n=16, phase=0.0):
    axis = norm(a)
    ref = np.array([0, 1, 0], np.float32) if abs(axis[1]) < 0.9 else np.array([1, 0, 0], np.float32)
    u = norm(np.cross(axis, ref))
    v = np.cross(axis, u)
    th = np.arange(n, dtype=np.float32) * (2 * math.pi / n) + phase
    c = np.asarray(c, np.float32)
    return [c + r * (np.cos(th)[:, None] * u[None, :] + np.sin(th)[:, None] * v[None, :])]


def plane(c, u, v, w, h):
    u, v = norm(u), norm(v)
    c = np.asarray(c, np.float32)
    return [np.array([c - u * (w / 2) - v * (h / 2), c + u * (w / 2) - v * (h / 2),
                      c + u * (w / 2) + v * (h / 2), c - u * (w / 2) + v * (h / 2)], np.float32)]


def pins(c, u, v, w, h, nx, nz, cell=0.055):
    """Kisi kontak emas: banyak quad sekali gambar."""
    u, v = norm(u), norm(v)
    c = np.asarray(c, np.float32)
    out = []
    for i in range(nx):
        for j in range(nz):
            p = c + u * (-w / 2 + (i + 0.5) * w / nx) + v * (-h / 2 + (j + 0.5) * h / nz)
            a, b = u * (cell / 2), v * (cell / 2)
            out.append(np.array([p - a - b, p + a - b, p + a + b, p - a + b], np.float32))
    return out


def fan_blades(c, a, r_hub, r_tip, blades=7, phase=0.0, skew=0.055, twist=0.72):
    axis = norm(a)
    ref = np.array([0, 1, 0], np.float32) if abs(axis[1]) < 0.9 else np.array([1, 0, 0], np.float32)
    u = norm(np.cross(axis, ref))
    v = np.cross(axis, u)
    c = np.asarray(c, np.float32)
    out = []
    for i in range(blades):
        th = phase + i * 2 * math.pi / blades
        def pt(r, ang, lift):
            return c + r * (math.cos(ang) * u + math.sin(ang) * v) + axis * lift
        out.append(np.array([
            pt(r_hub, th, -skew * 0.35),
            pt(r_tip, th + twist * 0.42, skew),
            pt(r_tip, th + twist, skew * 0.55),
            pt(r_hub, th + twist * 0.78, -skew * 0.35),
        ], np.float32))
    return out


def cable(points, r=0.022, n=6):
    out = []
    for p, q in zip(points[:-1], points[1:]):
        p, q = np.asarray(p, np.float32), np.asarray(q, np.float32)
        d = q - p
        out += cyl((p + q) / 2, d, r, float(np.linalg.norm(d)), n=n, caps=False)
    return out


class Scene:
    def __init__(self, top=(8, 13, 26), bottom=(20, 30, 48)):
        self.faces = []
        self.pre = []
        self.post = []
        self.top = np.asarray(top, np.float32)
        self.bottom = np.asarray(bottom, np.float32)

    def add(self, polys, mat, rot=(0, 0, 0), shift=(0, 0, 0), pre=False, post=False):
        if isinstance(polys, np.ndarray) and polys.ndim == 2:
            polys = [polys]
        if any(rot) or any(shift):
            polys = transform(polys, rot, shift)
        (self.pre if pre else self.post if post else self.faces).append((polys, mat))


_L1 = norm([-0.55, 0.90, 0.68])
_L2 = norm([0.86, 0.32, -0.52])
_KEY = np.array([0.88, 0.95, 1.00], np.float32)
_RIM = np.array([1.00, 0.76, 0.47], np.float32)
_SPEC = np.array([0.94, 0.97, 1.00], np.float32)


class Camera:
    def __init__(self, target, yaw, pitch, dist, fov=42.0):
        self.target = np.asarray(target, np.float32)
        self.yaw, self.pitch, self.dist, self.fov = yaw, pitch, dist, fov


def _basis(cam):
    d = np.array([math.cos(cam.pitch) * math.sin(cam.yaw), math.sin(cam.pitch),
                  math.cos(cam.pitch) * math.cos(cam.yaw)], np.float32)
    pos = cam.target + cam.dist * d
    fwd = -d
    right = norm(np.cross(fwd, np.array([0, 1, 0], np.float32)))
    up = np.cross(right, fwd)
    return pos, np.stack([right, up, fwd], axis=0), fwd


def _shade(polys, mat, pos):
    base, metal, shine, _alpha, _edge, emis = mat
    p = polys[0]
    n = norm(np.cross(p[1] - p[0], p[2] - p[0]))
    centroid = np.concatenate(polys, axis=0).mean(axis=0)
    to_eye = norm(pos - centroid)
    if float(np.dot(n, to_eye)) < 0:
        n = -n
    d1 = max(0.0, float(np.dot(n, _L1)))
    d2 = max(0.0, float(np.dot(n, _L2)))
    df = max(0.0, float(np.dot(n, to_eye)))
    col = (base * 0.31 + base * (0.88 * d1) * _KEY
           + base * (0.54 * d2) * _RIM
           + base * (0.24 * df) * np.array([0.80, 0.88, 1.00], np.float32))
    if metal:
        h = norm(_L1 + to_eye)
        spec = metal * max(0.0, float(np.dot(n, h))) ** shine
        fres = metal * 0.16 * (1.0 - df) ** 2
        col = col + (spec * 0.62 + fres * 0.75) * _SPEC
    if emis:
        col = col * (1 - emis) + np.minimum(base * 1.40, 1.0) * emis
    col = np.clip(col * 1.10, 0, 1) ** 0.93
    return (tuple(int(v * 255) for v in col),
            tuple(int(v * 255) for v in np.clip(col * 1.08 + 0.006, 0, 1)))


def _draw(img, sp, color, alpha, edge, edge_color):
    if alpha >= 0.999:
        for poly in sp:
            cv2.fillPoly(img, [poly], color, lineType=cv2.LINE_8)
    else:
        allp = np.concatenate(sp, axis=0)
        x0 = max(0, int(allp[:, 0].min()) - 2)
        y0 = max(0, int(allp[:, 1].min()) - 2)
        x1 = min(img.shape[1], int(allp[:, 0].max()) + 3)
        y1 = min(img.shape[0], int(allp[:, 1].max()) + 3)
        if x1 <= x0 or y1 <= y0:
            return
        shifted = [p - np.array([x0, y0], np.int32) for p in sp]
        mask = np.zeros((y1 - y0, x1 - x0), np.uint8)
        for poly in shifted:
            cv2.fillPoly(mask, [poly], 255)
        m = mask.astype(np.float32) * (alpha / 255.0)
        roi = img[y0:y1, x0:x1].astype(np.float32)
        roi[:] = roi * (1 - m[..., None]) + np.array(color, np.float32) * m[..., None]
        img[y0:y1, x0:x1] = np.uint8(np.clip(roi, 0, 255))
    if edge > 0:
        cv2.polylines(img, sp, True, edge_color, max(1, int(round(edge))), cv2.LINE_AA)


def render(scene: Scene, cam: Camera, W: int, H: int, ss: float = 1.5):
    RW, RH = int(W * ss), int(H * ss)
    t = np.linspace(0, 1, RH, dtype=np.float32)[:, None, None]
    bg = scene.top[None, None, :] * (1 - t) + scene.bottom[None, None, :] * t
    img = np.repeat(bg, RW, axis=1).astype(np.uint8)

    pos, B, _fwd = _basis(cam)
    f = (RH / 2) / math.tan(math.radians(cam.fov) / 2)
    cx, cy = RW / 2, RH / 2
    near = 0.06

    def project(faces, out):
        for polys, mat in faces:
            v = np.concatenate(polys, axis=0)
            vc = (v - pos) @ B.T
            z = vc[:, 2]
            if z.min() <= near or not np.all(np.isfinite(z)):
                continue
            sx = cx + f * vc[:, 0] / z
            sy = cy - f * vc[:, 1] / z
            if not (np.all(np.isfinite(sx)) and np.all(np.isfinite(sy))):
                continue
            if np.max(np.abs(sx)) > RW * 40 or np.max(np.abs(sy)) > RH * 40:
                continue
            pts = np.stack([sx, sy], axis=1)
            lens = [len(p) for p in polys]
            sp, k = [], 0
            for L in lens:
                sp.append(np.int32(np.round(pts[k:k + L])))
                k += L
            color, edge_color = _shade(polys, mat, pos)
            out.append((float(z.mean()), sp, color, mat[3], mat[4], edge_color))
        return out

    pre = project(scene.pre, [])
    for item in sorted(pre, key=lambda q: -q[0]):
        _draw(img, item[1], item[2], item[3], item[4], item[5])

    items = project(scene.faces, [])
    items.sort(key=lambda q: -q[0])
    for item in items:
        _draw(img, item[1], item[2], item[3], item[4], item[5])

    late = project(scene.post, [])
    late.sort(key=lambda q: -q[0])
    for item in late:
        _draw(img, item[1], item[2], item[3], item[4], item[5])

    if ss != 1.0:
        img = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)
    return img

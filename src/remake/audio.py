#!/usr/bin/env python3
"""Tata suara KlikTahu — VO baru + SFX prosedural + mastering -14 LUFS.

Semua efek suara disintesis dari numpy (tanpa pustaka audio berlisensi).
Tidak ada_audio, musik, atau VO dari video referensi.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 48000
ROOT = Path(__file__).resolve().parents[2]


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def read_audio(path: Path) -> np.ndarray:
    """Decode VO ke mono float32 48 kHz + sedikit atempo untuk pacing padat."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import script_kliktahu as S
    raw = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", str(path),
         "-af", f"atempo={S.VO_ATEMPO}", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(raw, dtype="<f4").copy()


def _env(n, a=0.01, r=0.08, sr=SR):
    e = np.ones(n, np.float32)
    na, nr = min(n, max(1, int(a * sr))), min(n, max(1, int(r * sr)))
    e[:na] = np.linspace(0, 1, na, dtype=np.float32)
    e[-nr:] = np.minimum(e[-nr:], np.linspace(1, 0, nr, dtype=np.float32))
    return e


def _tone(freq, dur, amp=0.4, kind="sine", sr=SR):
    n = int(dur * sr)
    t = np.arange(n, dtype=np.float32) / sr
    if kind == "sine":
        x = np.sin(2 * np.pi * freq * t)
    elif kind == "square":
        x = np.sign(np.sin(2 * np.pi * freq * t)) * 0.6
    elif kind == "tri":
        x = 2 * np.abs(2 * (freq * t % 1) - 1) - 1
    else:
        x = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    return (x * amp * _env(n)).astype(np.float32)


def _noise(dur, amp=0.3, seed=0, cutoff=0.0, sr=SR):
    n = int(dur * sr)
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n).astype(np.float32)
    if cutoff:
        a = math.exp(-2 * math.pi * cutoff / sr)
        y = np.empty_like(x)
        acc = 0.0
        for i, v in enumerate(x):
            acc = a * acc + (1 - a) * v
            y[i] = acc
        x = y / (np.std(y) + 1e-6)
    return (x / (np.std(x) + 1e-6) * amp * _env(n, 0.005, min(0.2, dur * 0.5))).astype(np.float32)


def _mix(*xs):
    """Gabungkan beberapa buffer audio dengan panjang berbeda."""
    n = max(len(x) for x in xs)
    out = np.zeros(n, np.float32)
    for x in xs:
        out[:len(x)] += x
    return out


def _place(dst, src, at, gain=1.0):
    i = int(at * SR)
    if i < 0 or i >= len(dst):
        return
    n = min(len(src), len(dst) - i)
    dst[i:i + n] += src[:n] * gain


def sfx(name: str) -> np.ndarray:
    """Satu efek suara prosedural; durasi bervariasi 0.1–3.0 detik."""
    if name == "power_click":
        x = _mix(_noise(0.14, 0.55, 1, 2600), _tone(78, 0.18, 0.45, "tri"))
        return x
    if name == "fan_spin":
        n = int(1.9 * SR)
        t = np.arange(n) / SR
        spin = 110 + 240 * np.clip(t / 1.6, 0, 1)
        x = (0.12 * np.sin(2 * np.pi * spin * t) + 0.10 * _noise(1.9, 1.0, 2, 900))
        return (x * _env(n, 0.25, 0.6)).astype(np.float32)
    if name == "whoosh":
        return _noise(0.75, 0.22, 3, 1500)
    if name == "relay":
        return _mix(_noise(0.10, 0.5, 4, 3000), _tone(190, 0.16, 0.28, "square"))
    if name == "hum":
        n = int(2.6 * SR)
        t = np.arange(n) / SR
        x = 0.10 * np.sin(2 * np.pi * 60 * t) + 0.05 * np.sin(2 * np.pi * 120 * t)
        return (x * _env(n, 0.4, 1.0)).astype(np.float32)
    if name == "power_good":
        return np.concatenate((_tone(880, 0.13, 0.34), np.zeros(int(0.06 * SR)), _tone(1320, 0.20, 0.32)))
    if name == "cpu_wake":
        n = int(1.1 * SR)
        t = np.arange(n) / SR
        f = 180 + 780 * (t / 1.1) ** 2
        return (0.22 * np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.1, 0.4)).astype(np.float32)
    if name == "data_blips":
        out = np.zeros(int(0.9 * SR), np.float32)
        for k in range(9):
            _place(out, _tone(520 + k * 95, 0.055, 0.20), k * 0.09)
        return out
    if name == "post_beep":
        return _tone(1040, 0.14, 0.34, "square")
    if name == "error_hint":
        return np.concatenate((_tone(320, 0.16, 0.26), np.zeros(int(0.10 * SR)), _tone(320, 0.16, 0.26)))
    if name == "post_ok":
        return _mix(_tone(660, 0.42, 0.26), _tone(990, 0.42, 0.18), _tone(1320, 0.42, 0.10))
    if name == "data_stream":
        out = np.zeros(int(2.1 * SR), np.float32)
        for k in range(26):
            _place(out, _tone(420 + (k % 8) * 110, 0.035, 0.13), k * 0.075)
        return out
    if name == "loading":
        n = int(3.0 * SR)
        t = np.arange(n) / SR
        x = (0.10 * np.sin(2 * np.pi * 220 * t) + 0.06 * np.sin(2 * np.pi * 330 * t)) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.1 * t))
        return (x * _env(n, 0.4, 1.0)).astype(np.float32)
    if name == "pixel_reveal":
        return _noise(1.3, 0.16, 5, 4200)
    if name == "chime":
        return _mix(_tone(523, 0.9, 0.20), _tone(659, 0.9, 0.15), _tone(784, 0.9, 0.12))
    if name == "outro_pad":
        return _mix(_tone(196, 2.6, 0.16), _tone(294, 2.6, 0.12), _tone(392, 2.6, 0.09))
    return np.zeros(int(0.2 * SR), np.float32)


def ambient(total: float) -> np.ndarray:
    n = int(total * SR)
    t = np.arange(n, dtype=np.float32) / SR
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.13 * t)
    bed = (0.022 * np.sin(2 * np.pi * 55 * t) + 0.012 * np.sin(2 * np.pi * 110 * t)) * lfo
    bed += _noise(total, 0.012, 99, 420)[:n]
    return (bed * _env(n, 1.2, 1.8)).astype(np.float32)


def build_master(timeline: list[dict], vo_paths: list[Path], out_wav: Path) -> float:
    total = timeline[-1]["end"] + timeline[-1].get("outro", 0.0)
    n = int((total + 0.5) * SR)
    vo = np.zeros(n, np.float32)
    fx = np.zeros(n, np.float32)

    for seg, path in zip([s for s in timeline if s["kind"] == "segment"], vo_paths):
        clip = read_audio(path)
        _place(vo, clip * np.float32(0.95), seg["vo_start"])
        names = seg["sfx"]
        for k, nm in enumerate(names):
            at = seg["start"] + 0.12 + k * (seg["dur"] - 0.5) / max(1, len(names))
            _place(fx, sfx(nm), at, 0.85)

    # ducking: bed + SFX turun saat VO aktif
    win = int(0.12 * SR)
    kernel = np.ones(win, np.float32) / win
    level = np.convolve(np.abs(vo), kernel, mode="same")
    level = np.clip(level / (np.percentile(level[level > 0], 92) + 1e-6), 0, 1) if np.any(level > 0) else level
    duck = 1.0 - 0.55 * level
    mix = vo + (ambient(total + 0.5)[:n] + fx) * duck

    # limiter lunak + headroom
    mix = np.tanh(mix * 1.25) * 0.92
    peak = float(np.max(np.abs(mix))) or 1.0
    mix *= min(1.0, 0.89 / peak)

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    return n / SR


def normalize(wav: Path, m4a: Path) -> dict:
    """Two-pass EBU R128 loudnorm -> -14 LUFS, true peak -1.5 dBTP, AAC 192k."""
    ff = ffmpeg_exe()
    base = "loudnorm=I=-14:TP=-1.5:LRA=11"
    p1 = subprocess.run(
        [ff, "-hide_banner", "-nostats", "-i", str(wav),
         "-af", base + ":print_format=json", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    blocks = re.findall(r"\{\s*\"input_i\".*?\}", p1.stderr, re.S)
    if not blocks:
        raise RuntimeError("loudnorm pass-1 gagal: " + p1.stderr[-500:])
    m = json.loads(blocks[-1])
    params = ":".join([
        f"measured_I={m['input_i']}", f"measured_TP={m['input_tp']}",
        f"measured_LRA={m['input_lra']}", f"measured_thresh={m['input_thresh']}",
        f"offset={m['target_offset']}", "linear=true", "print_format=summary",
    ])
    subprocess.run(
        [ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav),
         "-af", base + ":" + params, "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(m4a)],
        check=True,
    )
    return {"target": "-14 LUFS / -1.5 dBTP", "measured": m}

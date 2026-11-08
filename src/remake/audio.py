#!/usr/bin/env python3
"""Tata suara: VO + SFX yang dipicu tepat pada kata yang diucapkan, mastered -14 LUFS."""
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


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def read_audio(path):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import script_kliktahu as S
    raw = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", str(path),
         "-af", f"atempo={S.VO_ATEMPO}", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4").copy()


# ------------------------------------------------------------------ sintesis
def _noise(dur, seed=0):
    n = max(1, int(dur * SR))
    x = np.random.default_rng(seed).standard_normal(n).astype(np.float32)
    return x / (np.std(x) + 1e-6)


def _filter(x, lo, hi, order=4):
    n = len(x)
    X = np.fft.rfft(x)
    fq = np.fft.rfftfreq(n, 1 / SR)
    lp = 1 / np.sqrt(1 + (fq / max(hi, 1)) ** (2 * order))
    hp = (fq / lo) / np.sqrt(1 + (fq / lo) ** 2) if lo > 0 else np.ones_like(fq)
    y = np.fft.irfft(X * lp * hp, n)
    return y / (np.std(y) + 1e-6)


def _env(n, attack=0.003, release=0.04, decay=0.0):
    e = np.ones(n, np.float32)
    na, nr = int(attack * SR), int(release * SR)
    if na > 0:
        e[:na] = np.linspace(0, 1, na, dtype=np.float32) ** 1.4
    if nr > 0:
        e[-nr:] *= np.linspace(1, 0, nr, dtype=np.float32) ** 1.2
    if decay > 0:
        e *= np.exp(-np.arange(n, dtype=np.float32) / SR / decay)
    return e


def _osc(f, dur, amp=1.0, square=False):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    if not square:
        x = np.sin(2 * math.pi * f * t)
    else:
        x = sum(np.sin(2 * math.pi * (2 * k + 1) * f * t) / (2 * k + 1) for k in range(5)) * 0.55
    return x * amp


def _chirp(f0, f1, dur, amp=1.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = f0 + (f1 - f0) * (t / dur)
    return np.sin(2 * math.pi * np.cumsum(f) / SR) * amp


def _bell(f, dur, amp=0.3, tau=0.38):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    x = (np.sin(2 * math.pi * f * t) + 0.28 * np.sin(4 * math.pi * f * t)
         + 0.11 * np.sin(6 * math.pi * f * t)) * np.exp(-t / tau)
    return x * amp * _env(n, 0.004, min(0.10, dur * 0.3))


def _room(x, taps=((17, 0.24), (31, 0.15), (53, 0.08))):
    out = x.astype(np.float32).copy()
    for ms, g in taps:
        d = int(ms * SR / 1000)
        if d < len(x):
            out[d:] += x[:-d] * g
    return out


def _place(dst, src, at, gain=1.0):
    i = int(at * SR)
    if i < 0 or i >= len(dst):
        return
    n = min(len(src), len(dst) - i)
    dst[i:i + n] += src[:n] * gain


def _mix(*xs):
    n = max(len(x) for x in xs)
    out = np.zeros(n, np.float32)
    for x in xs:
        out[:len(x)] += x
    return out


def _tick(freq=1650, amp=0.35):
    n = int(0.042 * SR)
    x = _filter(_noise(0.042, 7), 900, 7000) * _env(n, 0.0008, 0.012, decay=0.010)
    return (x + _osc(freq, 0.042, 0.55) * _env(n, 0.0008, 0.014, decay=0.012)) * amp


def _spin(dur, seed, f0, f1, bright, amp):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    nz = _filter(_noise(dur, seed), 55, bright)
    rate = 11 + 32 * np.clip(t / (dur * 0.7), 0, 1)
    mod = 0.70 + 0.30 * np.sin(2 * math.pi * np.cumsum(rate) / SR)
    motor = _chirp(f0, f1, dur, 1.0)
    x = (0.40 * nz * mod + 0.28 * motor) * _env(n, 0.55, dur * 0.32) * np.clip(t / (dur * 0.38), 0, 1)
    return x * amp


def sfx(name):
    if name == "power_click":
        n = int(0.20 * SR)
        click = _filter(_noise(0.20, 11), 700, 9000) * _env(n, 0.001, 0.02, decay=0.013)
        thunk = _chirp(170, 52, 0.20, 1.0) * _env(n, 0.001, 0.06, decay=0.048)
        return _room((0.52 * click + 0.50 * thunk) * 0.85)
    if name == "fan_spin":
        return _spin(2.3, 21, 48, 104, 1700, 0.55)
    if name == "gpu_fans":
        return _spin(1.5, 23, 70, 138, 2400, 0.48)
    if name == "led_on":
        return _mix(_bell(1180, 0.16, 0.20, 0.07), _bell(2360, 0.11, 0.07, 0.045)) * 0.8
    if name == "screen_off":
        n = int(0.30 * SR)
        return (_chirp(96, 41, 0.30, 0.55) * _env(n, 0.002, 0.10, decay=0.075)
                + _filter(_noise(0.30, 12), 80, 700) * _env(n, 0.004, 0.12, decay=0.06) * 0.16)
    if name == "tick":
        return _tick(1650, 0.30)
    if name == "relay":
        n = int(0.26 * SR)
        click = _filter(_noise(0.26, 31), 1500, 11000) * _env(n, 0.001, 0.02, decay=0.009)
        coil = _osc(100, 0.26, 0.40, square=True) * _env(n, 0.002, 0.10, decay=0.055)
        return (click * 0.60 + coil * 0.34) * 0.85
    if name == "mains_hum":
        dur = 2.8
        n = int(dur * SR)
        t = np.arange(n, dtype=np.float32) / SR
        x = (0.55 * np.sin(2 * math.pi * 50 * t) + 0.22 * np.sin(2 * math.pi * 100 * t)
             + 0.09 * np.sin(2 * math.pi * 150 * t))
        return x * _env(n, 0.40, 1.0) * 0.17
    if name == "power_good":
        a = _bell(660, 0.20, 0.26, 0.14)
        b = _bell(990, 0.30, 0.24, 0.20)
        out = _mix(a, np.zeros(int(0.11 * SR)), b)
        return _room(out * 0.9)
    if name == "cpu_wake":
        n = int(1.0 * SR)
        x = _chirp(95, 430, 1.0, 0.42) * _env(n, 0.10, 0.35)
        x += 0.10 * _chirp(190, 860, 1.0, 1.0) * _env(n, 0.12, 0.35)
        for k, f in enumerate([1400, 1800, 2200]):
            _place(x, _tick(f, 0.22), 0.16 + k * 0.16)
        return x
    if name == "bios_read":
        out = np.zeros(int(0.62 * SR), np.float32)
        for k, f in enumerate([1450, 1700, 1950, 2200]):
            _place(out, _tick(f, 0.26), 0.03 + k * 0.115)
        return out
    if name == "post_beep":
        n = int(0.20 * SR)
        return _room(_osc(1000, 0.20, 0.50, square=True) * _env(n, 0.002, 0.05, decay=0.075))
    if name == "error_beeps":
        out = np.zeros(int(0.62 * SR), np.float32)
        for at in (0.0, 0.22):
            _place(out, _osc(310, 0.16, 0.28, square=True) * _env(int(0.16 * SR), 0.002, 0.04), at)
        return out * 0.75
    if name == "post_ok":
        beep = _osc(1000, 0.11, 0.26, square=True) * _env(int(0.11 * SR), 0.002, 0.03)
        chord = _mix(_bell(523, 0.70, 0.16, 0.34), _bell(659, 0.70, 0.13, 0.34),
                     _bell(784, 0.70, 0.11, 0.34))
        return _room(_mix(beep, np.zeros(int(0.10 * SR)), chord * 0.8))
    if name == "monitor_on":
        n = int(0.60 * SR)
        deg = _chirp(78, 40, 0.34, 0.55) * _env(int(0.34 * SR), 0.001, 0.10, decay=0.09)
        sh = _filter(_noise(0.60, 41), 1800, 8500) * _env(n, 0.006, 0.30, decay=0.14) * 0.13
        return _mix(deg, np.zeros(int(0.02 * SR)), sh, _bell(880, 0.50, 0.12, 0.24) * 0.7)
    if name == "ssd_access":
        out = np.zeros(int(0.95 * SR), np.float32)
        for k in range(15):
            f = 1750 if k % 2 == 0 else 2250
            _place(out, _tick(f, 0.15), 0.02 + k * 0.058)
        return out
    if name == "data_stream":
        dur = 1.9
        n = int(dur * SR)
        out = np.zeros(n, np.float32)
        t = np.arange(n, dtype=np.float32) / SR
        sh = np.clip(np.sin(math.pi * t / dur) ** 1.2, 0, 1)
        for k in range(40):
            f = 1350 + (k % 6) * 190
            _place(out, _tick(f, 0.11), 0.02 + k * 0.046)
        bed = _filter(_noise(dur, 51), 180, 1400) * _env(n, 0.20, 0.45) * 0.055
        return out * sh + bed
    if name == "loading":
        dur = 2.3
        n = int(dur * SR)
        t = np.arange(n, dtype=np.float32) / SR
        pulse = (0.5 + 0.5 * np.sin(2 * math.pi * 1.35 * t)) ** 2
        return (_bell(294, dur, 0.10, 1.2) + _bell(440, dur, 0.07, 1.2)) * pulse
    if name == "pixel_reveal":
        n = int(0.70 * SR)
        sh = _filter(_noise(0.70, 61), 900, 9000) * _env(n, 0.05, 0.28, decay=0.20) * 0.16
        return _mix(sh, _bell(1046, 0.60, 0.10, 0.30), _bell(1568, 0.50, 0.06, 0.24))
    if name == "chime":
        return _room(_mix(_bell(523, 1.1, 0.17, 0.50), _bell(659, 1.1, 0.13, 0.50),
                          _bell(784, 1.1, 0.11, 0.50)))
    if name == "loop_pad":
        return _mix(_bell(196, 3.2, 0.075, 1.6), _bell(294, 3.2, 0.060, 1.6),
                    _bell(392, 3.2, 0.050, 1.6), _bell(494, 3.2, 0.032, 1.6))
    if name == "brand_chime":
        a = _bell(784, 0.30, 0.18, 0.20)
        b = _bell(1046, 0.55, 0.16, 0.32)
        return _room(_mix(a, np.zeros(int(0.14 * SR)), b))
    return np.zeros(int(0.1 * SR), np.float32)


def ambient(total):
    n = int(total * SR)
    t = np.arange(n, dtype=np.float32) / SR
    h = _filter(_noise(total, 77), 25, 260) * 0.016
    hum = 0.009 * np.sin(2 * math.pi * 50 * t) + 0.004 * np.sin(2 * math.pi * 100 * t)
    return (h + hum) * _env(n, 1.0, 1.6)


def build_master(timeline, vo_paths, out_wav):
    total = timeline[-1]["end"]
    n = int((total + 0.5) * SR)
    vo = np.zeros(n, np.float32)
    fx = np.zeros(n, np.float32)
    for entry, path in zip([e for e in timeline if e["kind"] == "segment"], vo_paths):
        _place(vo, read_audio(path) * 0.95, entry["vo_start"])
        for at, name, gain in entry["cue_times"]:
            _place(fx, sfx(name), at, gain)

    win = int(0.12 * SR)
    level = np.convolve(np.abs(vo), np.ones(win, np.float32) / win, mode="same")
    ref = np.percentile(level[level > 0], 92) if np.any(level > 0) else 1.0
    level = np.clip(level / (ref + 1e-6), 0, 1)
    duck = 1.0 - 0.40 * level

    mix = vo + (ambient(total + 0.5)[:n] + fx) * duck
    mix = np.tanh(mix * 1.18) * 0.94
    peak = float(np.max(np.abs(mix))) or 1.0
    mix *= min(1.0, 0.89 / peak)

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    return n / SR


def normalize(wav, m4a):
    ff = ffmpeg_exe()
    base = "loudnorm=I=-14:TP=-1.5:LRA=11"
    p1 = subprocess.run([ff, "-hide_banner", "-nostats", "-i", str(wav),
                         "-af", base + ":print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True)
    blocks = re.findall(r"\{\s*\"input_i\".*?\}", p1.stderr, re.S)
    if not blocks:
        raise RuntimeError("loudnorm pass-1 gagal: " + p1.stderr[-500:])
    m = json.loads(blocks[-1])
    params = ":".join([f"measured_I={m['input_i']}", f"measured_TP={m['input_tp']}",
                       f"measured_LRA={m['input_lra']}", f"measured_thresh={m['input_thresh']}",
                       f"offset={m['target_offset']}", "linear=true", "print_format=summary"])
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav),
                    "-af", base + ":" + params, "-ar", "48000",
                    "-c:a", "aac", "-b:a", "192k", str(m4a)], check=True)
    return m

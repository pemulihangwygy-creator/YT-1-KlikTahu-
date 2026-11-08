#!/usr/bin/env python3
"""Render KlikTahu 3D: 1080x1920 @ 60 fps, hard cut, audio tersinkron kata.

    python src/remake/engine.py --stills
    python src/remake/engine.py --render
"""
from __future__ import annotations

import argparse
import bisect
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import art as A                 # noqa: E402
import audio as AU              # noqa: E402
import scenes3d as S3           # noqa: E402
import script_kliktahu as S     # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build"
OUT = ROOT / "output"
VO_DIR = ROOT / "assets" / "vo"
FINAL = OUT / "KlikTahu_TombolPower_4K_60fps.mp4"
SS = 1.0
VO_NAMES = [s["id"] + ".mp3" for s in S.SEGMENTS]


def vo_paths():
    return [VO_DIR / n for n in VO_NAMES]


def word_schedule(text, vo_dur):
    words = S.words_of(text)
    weights = [1.0 + 0.55 * len(w) for w in words]
    scale = (vo_dur * 0.94) / sum(weights)
    sched, cur = [], vo_dur * 0.02
    for wt in weights:
        d = wt * scale
        sched.append((cur, cur + d))
        cur += d
    return words, sched


def resolve_cues(entry):
    words, sched = entry["words"], entry["sched"]
    out = []
    for kw, name, gain in S.CUES[entry["seg"]["id"]]:
        k = kw.lower()
        i = next((j for j, w in enumerate(words) if k in w.lower()), None)
        if i is None:
            continue
        out.append((max(0.0, entry["vo_start"] + sched[i][0] - 0.035), name, gain))
    return out


def build_timeline(paths):
    durs = [len(AU.read_audio(p)) / AU.SR if p.exists() else 13.0 for p in paths]
    tl, t = [], 0.0
    for seg, d in zip(S.SEGMENTS, durs):
        dur = max(S.MIN_SEGMENT_S, S.LEAD_IN_S + d + S.TAIL_S)
        words, sched = word_schedule(seg["narration"], d)
        e = {"kind": "segment", "seg": seg, "start": t, "end": t + dur,
             "dur": dur, "vo_dur": d, "vo_start": t + S.LEAD_IN_S,
             "words": words, "sched": sched}
        e["cue_times"] = resolve_cues(e)
        tl.append(e)
        t += dur
    total = t + S.OUTRO_S
    tl.append({"kind": "outro", "start": t, "end": total, "dur": S.OUTRO_S, "scene": "loop"})
    return tl, total


def active_caption(entry, t):
    tr = t - entry["vo_start"]
    if tr < 0 or tr > entry["vo_dur"] * 1.03:
        return None, None, 0.0
    ends = [b for _, b in entry["sched"]]
    idx = min(bisect.bisect_right(ends, tr), len(entry["words"]) - 1)
    window = (max(0, idx - 2), min(len(entry["words"]), idx + 4))
    fade = min(1.0, tr / 0.18, max(0.0, (entry["vo_dur"] - tr) / 0.28))
    return idx, window, max(0.0, fade)


def render_frame(t, tl, total):
    entry = next((e for e in tl if e["start"] <= t < e["end"]), tl[-1])
    if entry["kind"] == "outro":
        p = (t - entry["start"]) / entry["dur"]
        rgb = S3.build("loop", 1.0, t, S.W, S.H, SS)
        frame = Image.fromarray(rgb)
        d = ImageDraw.Draw(frame, "RGBA")
        A.scrims(d)
        A.chip_bar(d, 6.0, A.C("yellow"))
        A.outro_cta(d, p, A.C("yellow"))
        A.watermark(d, t)
        return np.asarray(frame)

    seg = entry["seg"]
    u = (t - entry["start"]) / entry["dur"]
    accent = A.C(seg["accent"])
    rgb = S3.build(seg["scene"], u, t, S.W, S.H, SS)
    frame = Image.fromarray(rgb)
    d = ImageDraw.Draw(frame, "RGBA")
    A.scrims(d)
    A.chip_bar(d, seg["step"] + u, accent)
    A.title_block(d, seg, u)
    idx, window, fade = active_caption(entry, t)
    if idx is not None:
        A.captions(d, entry["words"], idx, window, accent, fade)
    A.watermark(d, t)
    n = S.SEGMENTS.index(seg) + 1
    A.txt(d, (60, S.H / A.SC - 92), f"{n:02d} / 07  ·  KLIKTAHU", 24,
          A.rgba(A.C("muted"), 180), "SemiBold")
    return np.asarray(frame)


def render_stills(tl, total):
    dst = BUILD / "stills3d"
    dst.mkdir(parents=True, exist_ok=True)
    times = [1.0, 7.0, 22.0, 42.0, 61.0, 80.0, 102.0, 118.0, total - 1.4]
    for i, t in enumerate(times):
        t = min(t, total - 0.05)
        Image.fromarray(render_frame(t, tl, total)).save(dst / f"{i:02d}_{t:06.1f}s.png")
        print(f"  still {t:6.1f}s", flush=True)
    print(f"  -> {dst}")


def render_video(tl, total, silent_mp4, fps, crf, preset):
    cmd = [AU.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{S.W}x{S.H}", "-r", str(fps),
           "-i", "-", "-an", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-level:v", "5.2",
           "-movflags", "+faststart", str(silent_mp4)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(total * fps)
    t0 = time.time()
    for i in range(n):
        arr = render_frame(i / fps, tl, total)
        proc.stdin.write(arr.tobytes())
        if i % 600 == 0:
            print(f"  frame {i:5d}/{n}  {i/fps:6.1f}s  {time.time()-t0:6.1f}s", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("encoder ffmpeg gagal")
    print(f"  {n} frame selesai dalam {time.time()-t0:.1f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--fps", type=int, default=S.FPS)
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--preset", default="veryfast")
    ap.add_argument("--only-video", action="store_true")
    args = ap.parse_args()
    if not args.stills and not args.render:
        args.stills = args.render = True

    paths = vo_paths()
    if args.render and [p.name for p in paths if not p.exists()]:
        raise SystemExit("VO belum lengkap")
    tl, total = build_timeline(paths)
    print(f"Timeline {len(S.SEGMENTS)} bab, total {total:.2f}s @ {args.fps} fps, SS={SS}")
    for e in tl:
        if e["kind"] == "segment":
            print(f"  {e['start']:6.2f}s  {e['seg']['id']:10s} {e['dur']:5.2f}s  "
                  f"VO {e['vo_dur']:5.2f}s  cue {len(e['cue_times'])}")

    if args.stills:
        render_stills(tl, total)
    if not args.render:
        return

    BUILD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    wav, m4a = BUILD / "mix3d.wav", BUILD / "mix3d_master.m4a"
    silent = BUILD / "video4k_silent.mp4"
    if not args.only_video or not m4a.exists():
        print("[1/3] Audio: VO + SFX tersinkron ...")
        print(f"  mix {AU.build_master(tl, paths, wav):.2f}s")
        print("[2/3] Mastering -14 LUFS ...")
        m = AU.normalize(wav, m4a)
        print(f"  input {m.get('input_i')} LUFS")
    print("[3/3] Render 3D + encode ...")
    render_video(tl, total, silent, args.fps, args.crf, args.preset)
    subprocess.run([AU.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(silent), "-i", str(m4a),
                    "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", "-shortest",
                    "-movflags", "+faststart", str(FINAL)], check=True)
    print(f"SELESAI -> {FINAL}  ({FINAL.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()

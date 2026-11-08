#!/usr/bin/env python3
"""Renderer utama KlikTahu Ep. "Tombol Power" — 1080x1920 @ 60 fps.

    python src/remake/engine.py --stills     # pratinjau 9 frame + storyboard
    python src/remake/engine.py --render     # audio + video + mux final

Semua piksel dibuat dari kode (art.py), semua suara dari VO baru + SFX
prosedural (audio.py). Tidak ada byte dari video referensi di hasil akhir.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import art as A                     # noqa: E402
import audio as AU                  # noqa: E402
import script_kliktahu as S         # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build"
OUT = ROOT / "output"
VO_DIR = ROOT / "assets" / "vo"
FINAL = OUT / "KlikTahu_TombolPower_REMAKE_1080x1920_60fps.mp4"
VO_NAMES = [s["id"] + ".mp3" for s in S.SEGMENTS]


def vo_paths() -> list[Path]:
    return [VO_DIR / n for n in VO_NAMES]


def word_schedule(text: str, vo_dur: float):
    words = S.words_of(text)
    weights = [1.0 + 0.55 * len(w) for w in words]
    scale = (vo_dur * 0.94) / sum(weights)
    sched, cur = [], vo_dur * 0.02
    for wt in weights:
        d = wt * scale
        sched.append((cur, cur + d))
        cur += d
    return words, sched


def build_timeline(paths: list[Path]) -> tuple[list[dict], float]:
    durs = []
    for p in paths:
        if p.exists():
            durs.append(len(AU.read_audio(p)) / AU.SR)
        else:
            durs.append(13.0)  # estimasi untuk mode --stills sebelum VO ada
    tl: list[dict] = [{
        "kind": "intro", "start": 0.0, "end": S.INTRO_S,
        "dur": S.INTRO_S, "scene": "case",
    }]
    t = S.INTRO_S
    for seg, d in zip(S.SEGMENTS, durs):
        dur = max(S.MIN_SEGMENT_S, S.LEAD_IN_S + d + S.TAIL_S)
        words, sched = word_schedule(seg["narration"], d)
        tl.append({
            "kind": "segment", "seg": seg, "start": t, "end": t + dur, "dur": dur,
            "vo_dur": d, "vo_start": t + S.LEAD_IN_S, "words": words, "sched": sched,
            "sfx": seg["sfx"],
        })
        t += dur
    total = t + S.OUTRO_S
    tl.append({"kind": "outro", "start": t, "end": total, "dur": S.OUTRO_S, "scene": "loop"})
    return tl, total


def scrims(d):
    for i in range(12):
        d.rectangle((0, i * 36, S.W, (i + 1) * 36), fill=(6, 12, 28, int(125 * (1 - i / 12))))
    for i in range(12):
        y = S.H - 620 + i * 52
        d.rectangle((0, y, S.W, y + 52), fill=(6, 12, 28, int(175 * (i / 12))))


def active_caption(entry, t):
    tr = t - entry["vo_start"]
    if tr < 0 or tr > entry["vo_dur"] * 1.03:
        return None, None, 0.0
    ends = [b for _, b in entry["sched"]]
    idx = min(bisect.bisect_right(ends, tr), len(entry["words"]) - 1)
    window = (max(0, idx - 2), min(len(entry["words"]), idx + 4))
    fade = min(1.0, tr / 0.18, max(0.0, (entry["vo_dur"] - tr) / 0.28))
    return idx, window, max(0.0, fade)


def render_frame(t: float, tl: list[dict], total: float, frame_i: int) -> np.ndarray:
    entry = next((e for e in tl if e["start"] <= t < e["end"]), tl[-1])
    kind = entry["kind"]

    if kind == "intro":
        p = (t - entry["start"]) / entry["dur"]
        base = A.scene_base("case")
        view, P = A.camera(base, 0.0, "push")
        frame = Image.fromarray(view)
        A.dynamic(frame, "case", 0.0, t, P)
        d = ImageDraw.Draw(frame, "RGBA")
        scrims(d)
        A.intro_card(d, p, A.C("yellow"))
        A.watermark(d, t, alpha=150)
    elif kind == "outro":
        p = (t - entry["start"]) / entry["dur"]
        base = A.scene_base("loop")
        view, P = A.camera(base, 1.0, "pull")
        frame = Image.fromarray(view)
        A.dynamic(frame, "loop", 1.0, t, P)
        d = ImageDraw.Draw(frame, "RGBA")
        scrims(d)
        A.chip_bar(d, 6.0, A.C("yellow"))
        A.outro_card(d, p, A.C("yellow"))
        A.watermark(d, t, alpha=150)
    else:
        seg = entry["seg"]
        p = (t - entry["start"]) / entry["dur"]
        accent = A.C(seg["accent"])
        base = A.scene_base(seg["scene"])
        view, P = A.camera(base, p, seg["camera"])
        frame = Image.fromarray(view)
        A.dynamic(frame, seg["scene"], p, t, P)
        d = ImageDraw.Draw(frame, "RGBA")
        scrims(d)
        A.chip_bar(d, max(0.0, seg["step"] - 0.5) + p, accent)
        A.title_block(d, seg, p)
        idx, window, fade = active_caption(entry, t)
        if idx is not None:
            A.captions(d, entry["words"], idx, window, accent, fade)
        A.watermark(d, t)
        nomor = S.SEGMENTS.index(seg) + 1
        A.txt(d, (60, S.H - 92), f"{nomor:02d} / 07  ·  KLIKTAHU", 24,
              A.rgba(A.C("muted"), 175), "SemiBold")
        # transisi cepat di batas bab
        q = (t - entry["start"]) / 0.26
        if q < 1:
            d.rectangle((0, 0, S.W, S.H), fill=(8, 16, 34, int(135 * (1 - q))))
            d.rectangle((0, 0, S.W, 6), fill=A.rgba(accent, 220))
        q2 = (entry["end"] - t) / 0.20
        if q2 < 1:
            d.rectangle((0, 0, S.W, S.H), fill=(8, 16, 34, int(120 * (1 - max(0, q2)))))

    return A.finish(np.asarray(frame), frame_i)


def render_video(tl, total, silent_mp4: Path, fps: int, crf: int, preset: str):
    cmd = [
        AU.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{S.W}x{S.H}", "-r", str(fps),
        "-i", "-", "-an", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
        str(silent_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(total * fps)
    t0 = time.time()
    for i in range(n):
        t = i / fps
        arr = render_frame(t, tl, total, i)
        proc.stdin.write(arr.tobytes())
        if i % 600 == 0:
            print(f"  frame {i:5d}/{n}  {t:6.1f}s  {time.time() - t0:5.1f}s", flush=True)
    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg encoder keluar {rc}")
    print(f"  selesai {n} frame dalam {time.time() - t0:.1f}s", flush=True)


def render_stills(tl, total):
    stills = BUILD / "stills"
    stills.mkdir(parents=True, exist_ok=True)
    times = [1.2, 7.0, 18.0, 32.0, 48.0, 64.0, 82.0, 98.0, total - 1.6]
    times = [min(t, total - 0.05) for t in times]
    imgs = []
    for i, t in enumerate(times):
        arr = render_frame(t, tl, total, int(t * S.FPS))
        im = Image.fromarray(arr)
        im.save(stills / f"{i:02d}_{t:06.1f}s.png")
        imgs.append((t, im))
        print(f"  still {t:6.1f}s", flush=True)
    # storyboard 3x3
    tw, th = 300, 533
    sheet = Image.new("RGB", (tw * 3, th * 3), (8, 14, 30))
    dd = ImageDraw.Draw(sheet)
    for i, (t, im) in enumerate(imgs):
        x, y = (i % 3) * tw, (i // 3) * th
        sheet.paste(im.resize((tw, th)), (x, y))
        dd.rectangle((x, y, x + 86, y + 26), fill=(0, 0, 0))
        dd.text((x + 5, y + 5), f"{t:05.1f}s", fill=(255, 210, 50))
    OUT.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT / "KlikTahu_REMAKE_storyboard.jpg", quality=90)
    # thumbnail 1080x1920 dari frame hook + judul besar
    base = A.scene_base("case")
    view, _ = A.camera(base, 0.35, "push")
    thumb = Image.fromarray(A.finish(view.copy(), 999))
    td = ImageDraw.Draw(thumb, "RGBA")
    td.rectangle((0, 0, S.W, S.H), fill=(6, 12, 28, 165))
    td.rounded_rectangle((60, 120, 1020, 620), 40, fill=(8, 16, 36, 215), outline=A.rgba(A.C("yellow"), 235), width=6)
    A.txt(td, (90, 170), "APA YANG TERJADI", 72, A.rgba(A.C("white"), 255), "ExtraBold")
    A.txt(td, (90, 260), "SAAT KAMU PENCET", 72, A.rgba(A.C("white"), 255), "ExtraBold")
    A.txt(td, (90, 350), "TOMBOL POWER?", 78, A.rgba(A.C("yellow"), 255), "ExtraBold")
    A.txt(td, (90, 500), S.BRAND, 62, A.rgba(A.C("white"), 255), "ExtraBold")
    A.txt(td, (90, 570), S.TAGLINE, 28, A.rgba(A.C("muted"), 255), "Medium")
    thumb.save(OUT / "KlikTahu_REMAKE_thumbnail.jpg", quality=92)
    print(f"  storyboard + thumbnail -> {OUT}")


def stamp(t: float) -> str:
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def write_metadata(tl, total, loudness: dict):
    segs = [e for e in tl if e["kind"] == "segment"]
    meta = {
        "episode": "KlikTahu! — Apa yang Terjadi Saat Kamu Pencet Tombol Power",
        "status": "Video buatan sendiri. Bukan salinan, bukan remake frame referensi.",
        "file": FINAL.name,
        "technical": {
            "width": S.W, "height": S.H, "aspect_ratio": "9:16",
            "fps": S.FPS, "duration_seconds": round(total, 2),
            "video_codec": "H.264 High / yuv420p",
            "audio_codec": "AAC-LC 192 kb/s 48 kHz",
            "loudness": "-14 LUFS / -1.5 dBTP (two-pass EBU R128)",
            "watermark": S.WATERMARK,
        },
        "youtube": {
            "title": "Apa yang Terjadi Saat Kamu Pencet Tombol Power Komputer? #Shorts #KlikTahu",
            "description": (
                "Kipas muter, lampu nyala, tapi layar masih gelap. Rusak? Belum tentu.\n\n"
                "KlikTahu bongkar urutan lengkapnya: tombol power -> motherboard -> PSU -> "
                "sinyal daya siap -> CPU bangun -> BIOS -> POST -> SSD ke RAM -> GPU -> "
                "tampilan utama. Semua cuma beberapa detik, dan terulang tiap kali kamu "
                "menyalakan komputer.\n\n"
                + "\n".join(f"{stamp(e['start'])} {e['seg']['title'][0]} {e['seg']['title'][1]}" for e in segs)
                + "\n\n#Shorts #KlikTahu #Komputer #Teknologi #Edukasi"
            ),
            "tags": ["KlikTahu", "tombol power", "komputer", "motherboard", "PSU", "BIOS",
                     "POST", "RAM", "SSD", "GPU", "booting", "teknologi", "edukasi", "shorts"],
            "hashtags": ["#Shorts", "#KlikTahu", "#Komputer", "#Teknologi", "#Edukasi"],
            "category_id": 28, "language": "id", "made_for_kids": False,
            "chapters": [{"start": stamp(e["start"]), "title": " ".join(e["seg"]["title"])} for e in segs],
        },
        "chapters": [{"start": round(e["start"], 2), "title": " ".join(e["seg"]["title"]), "scene": e["seg"]["scene"]} for e in segs],
        "loudnorm_pass1": loudness.get("measured", {}),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "KlikTahu_REMAKE_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--fps", type=int, default=S.FPS)
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--preset", default="veryfast")
    args = ap.parse_args()
    if not args.stills and not args.render:
        args.stills = args.render = True

    paths = vo_paths()
    missing = [p.name for p in paths if not p.exists()]
    if missing and args.render:
        raise SystemExit(f"VO belum lengkap: {missing}")
    tl, total = build_timeline(paths)
    print(f"Timeline: {len([e for e in tl if e['kind']=='segment'])} bab, intro {S.INTRO_S}s, "
          f"outro {S.OUTRO_S}s, total {total:.2f}s @ {args.fps} fps")
    for e in tl:
        if e["kind"] == "segment":
            print(f"  {stamp(e['start'])}  {e['seg']['id']:10s} dur {e['dur']:5.2f}s  VO {e['vo_dur']:5.2f}s")

    if args.stills:
        print("[1/4] Render stills + storyboard + thumbnail ...")
        render_stills(tl, total)
    if not args.render:
        return

    BUILD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    wav, m4a = BUILD / "mix.wav", BUILD / "mix_master.m4a"
    silent = BUILD / "video_silent.mp4"
    print("[2/4] Bangun audio: VO + SFX prosedural ...")
    au_len = AU.build_master(tl, paths, wav)
    print(f"  mix.wav {au_len:.2f}s")
    print("[3/4] Mastering -14 LUFS (two-pass loudnorm) ...")
    loud = AU.normalize(wav, m4a)
    print(f"  measured I={loud['measured'].get('input_i')} LUFS")
    print("[4/4] Render frame + encode H.264 ...")
    render_video(tl, total, silent, args.fps, args.crf, args.preset)
    subprocess.run([
        AU.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(silent), "-i", str(m4a),
        "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", "-shortest",
        "-movflags", "+faststart", str(FINAL),
    ], check=True)
    meta = write_metadata(tl, total, loud)
    print(f"\nSELESAI -> {FINAL}")
    print(f"  {S.W}x{S.H} @ {args.fps}fps, {total:.2f}s, {FINAL.stat().st_size/1e6:.1f} MB")
    print(f"  metadata: {OUT / 'KlikTahu_REMAKE_metadata.json'}")


if __name__ == "__main__":
    main()

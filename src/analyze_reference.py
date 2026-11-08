#!/usr/bin/env python3
"""Bedah video referensi KlikTahu "Tombol Power" menjadi spesifikasi produksi.

Keluaran:
  docs/TEKNIS.json        -- metadata teknis + daftar pergantian adegan
  docs/ocr_timeline.json  -- seluruh hasil OCR per sampel frame (bukti telusur)
  docs/OCR_MENTAH.md      -- transkrip OCR mentah + daftar bab berstempel waktu

OCR memakai rapidocr-onnxruntime (opsional). Tanpa OCR, skrip tetap
menghasilkan metadata teknis dan deteksi pergantian adegan.

    python src/analyze_reference.py
    python src/analyze_reference.py --source /path/ke/video.mp4 --interval 0.5
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "google_drive" / (
    "Apa yang Sebenarnya Terjadi Pas Kamu Pencet Tombol Power Komputer_(720P_HD).mp4"
)

# Judul tetap di kepala frame. Dipakai untuk membagi video menjadi bab.
KNOWN_TITLES = [
    "Pencet tombol power: apa yang terjadi?",
    "Motherboard & PSU: listrik dulu",
    "CPU bangun: baca BIOS dulu",
    "POST: cek semua komponen",
    "Storage ke RAM: Windows dimuat",
    "GPU: data jadi gambar",
    "Tiap kali dinyalakan: semua terulang",
]

# Region layar (piksel pada kanvas 720x1280) yang dipetakan ke peran teks.
REGIONS = {
    "title": (80, 200),        # judul bab, dua baris
    "chips": (270, 335),       # progress bar / langkah aliran listrik
    "callout": (770, 860),     # label diagram biru/kuning
    "caption": (875, 995),     # subtitle per-kata di sepertiga bawah
    "footer": (1180, 1280),    # watermark / tanda tangan kecil
}


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:  # pragma: no cover - fallback ke ffmpeg sistem
        return "ffmpeg"


def technical_metadata(source: Path) -> dict:
    probe = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-i", str(source)],
        capture_output=True,
        text=True,
    ).stderr
    cap = cv2.VideoCapture(str(source))
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    duration_m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", probe)
    duration = (
        int(duration_m.group(1)) * 3600
        + int(duration_m.group(2)) * 60
        + float(duration_m.group(3))
        if duration_m
        else frames / fps
    )
    streams = re.findall(r"Stream #0:\d+.*", probe)
    head = open(source, "rb").read(200_000)
    return {
        "file": source.name,
        "bytes": source.stat().st_size,
        "width": width,
        "height": height,
        "fps": fps,
        "frames": int(frames),
        "duration_seconds": round(duration, 3),
        "duration_ffmpeg": duration_m.group(0) if duration_m else None,
        "streams": [s.strip() for s in streams],
        "faststart": head.find(b"moov") != -1 and head.find(b"moov") < head.find(b"mdat"),
    }


def classify(y: float) -> str | None:
    for name, (lo, hi) in REGIONS.items():
        if lo <= y < hi:
            return name
    return None


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    # pola noise OCR yang berulang pada tekstur hardware 3D
    if text in {"画", "燕", "营", "同", "8"} or len(text) < 2:
        return ""
    return text


def ocr_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR

        return RapidOCR()
    except Exception as exc:  # pragma: no cover
        print(f"[peringatan] OCR tidak tersedia ({exc}); metadata teknis tetap dibuat")
        return None


def scan(source: Path, interval: float) -> tuple[list[dict], list[float]]:
    cap = cv2.VideoCapture(str(source))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total / fps
    ocr = ocr_engine()
    samples: list[dict] = []
    scene_changes: list[float] = []
    prev_small = None
    prev_diff = 0.0
    for i, t in enumerate(np.arange(0, duration, interval)):
        cap.set(cv2.CAP_PROP_POS_MSEC, float(t) * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        small = cv2.resize(frame, (90, 160))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        if prev_small is not None:
            diff = float(np.mean(cv2.absdiff(gray, prev_small)))
            # potongan keras: lompatan besar dibanding selisih frame sebelumnya
            if diff > 22 and diff > prev_diff * 2.4:
                scene_changes.append(round(float(t), 2))
            prev_diff = diff
        prev_small = gray
        entry: dict = {"t": round(float(t), 2), "regions": {k: [] for k in REGIONS}}
        if ocr is not None:
            hits, _ = ocr(frame)
            for box, raw, score in hits or []:
                y = float(np.mean([p[1] for p in box]))
                x = float(np.mean([p[0] for p in box]))
                role = classify(y)
                txt = clean(raw)
                if role and txt and score >= 0.5:
                    entry["regions"][role].append(
                        {"x": round(x), "y": round(y), "text": txt, "score": round(float(score), 2)}
                    )
            for items in entry["regions"].values():
                items.sort(key=lambda d: (d["y"] // 12, d["x"]))
        samples.append(entry)
        if i % 40 == 0:
            print(f"  ... {t:.1f}/{duration:.1f} detik", flush=True)
    cap.release()
    return samples, scene_changes


def join(region: list[dict]) -> str:
    return " ".join(d["text"] for d in region).strip()


def nearest_title(text: str) -> str:
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    target = norm(text)
    best, score = "", -1.0
    for title in KNOWN_TITLES:
        n = norm(title)
        common = sum((n.count(c) for c in set(target)), 0)
        ratio = common / max(len(n), 1)
        if ratio > score:
            best, score = title, ratio
    return best if score > 0.42 else ""


def build_script(samples: list[dict]) -> str:
    chapters: list[dict] = []
    captions: list[dict] = []
    for s in samples:
        raw_title = join(s["regions"]["title"])
        title = nearest_title(raw_title) if raw_title else ""
        if title and (not chapters or chapters[-1]["title"] != title):
            chapters.append({"t": s["t"], "title": title, "raw": raw_title})
        elif title and chapters:
            chapters[-1]["raw"] = raw_title
        cap = join(s["regions"]["caption"])
        if cap:
            if captions and re.sub(r"\s+", "", captions[-1]["text"].lower()) == re.sub(
                r"\s+", "", cap.lower()
            ):
                captions[-1]["until"] = s["t"]
            else:
                captions.append({"t": s["t"], "until": s["t"], "text": cap})

    def stamp(t: float) -> str:
        return f"{int(t // 60):02d}:{t % 60:05.2f}"

    lines = [
        "# Transkrip OCR Mentah — Tombol Power (bahan telusur)",
        "",
        "Diambil otomatis lewat OCR dari video referensi (interval 0,5 detik).",
        "Teks **judul** adalah judul bab tetap di kepala frame; teks **subtitle**",
        "adalah caption per-kata di sepertiga bawah dengan kata aktif disorot kuning.",
        "Daftar ini adalah transkrip telusur, bukan file subtitle baru — video final",
        "memakai frame asli apa adanya sehingga 100% identik. Label diagram 3D",
        "(DDR5, ATX, dll.) kadang ikut terbaca dan masih tampil di tabel bawah.",
        "",
        "> Lampiran telusur otomatis. Naskah bersih yang sudah dikurasi ada di",
        "> [`NASKAH.md`](NASKAH.md).",
        "",
        "## Bab (judul di layer kepala)",
        "",
        "| Mulai | Judul |",
        "|---|---|",
    ]
    for idx, ch in enumerate(chapters):
        end = chapters[idx + 1]["t"] if idx + 1 < len(chapters) else None
        lines.append(f"| {stamp(ch['t'])} | {ch['title']} |")
    lines += [
        "",
        "## Transkrip subtitle (dengan stempel waktu)",
        "",
        "| Mulai | Sampai | Teks tampil |",
        "|---|---|---|",
    ]
    for c in captions:
        lines.append(f"| {stamp(c['t'])} | {stamp(c['until'])} | {c['text']} |")
    lines += [
        "",
        "## Catatan gaya (dari frame)",
        "",
        "- Kanvas 720×1280 (9:16), 30 fps, latar biru-dongker gelap, visual 3D hardware PC.",
        "- Judul bab dua baris, kuning untuk baris kedua, rata kiri di y ≈ 100–165 px.",
        "- Progress bar ≈ 14 segmen di y ≈ 275–325 px: abu = belum, hijau = selesai,",
        "  kuning = langkah aktif, merah = kegagalan POST.",
        "- Subtitle di y ≈ 900–960 px, kotak hitam tipis, kata yang diucapkan disorot kuning.",
        "- Label diagram biru/kuning kecil di y ≈ 780–830 px; stempel adegan di y ≈ 805 px.",
        "- Adegan penutup: desktop Windows + stempel hijau `DESKTOP SIAP!`, lalu fade ke casing PC.",
        "",
    ]
    return "\n".join(lines), chapters, captions


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--interval", type=float, default=0.5)
    ap.add_argument("--out", type=Path, default=ROOT / "docs")
    args = ap.parse_args()
    source: Path = args.source
    if not source.exists():
        raise SystemExit(f"Sumber tidak ada: {source}\nUnduh dulu dari Google Drive.")
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] Metadata teknis: {source.name}")
    meta = technical_metadata(source)
    meta["scene_changes"] = []
    print(f"[2/3] Pindai frame tiap {args.interval} detik ...")
    samples, changes = scan(source, args.interval)
    meta["scene_changes"] = changes
    meta["ocr_samples"] = len(samples)
    (args.out / "ocr_timeline.json").write_text(
        json.dumps({"source": source.name, "interval": args.interval, "samples": samples}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("[3/3] Susun naskah ...")
    script_md, chapters, captions = build_script(samples)
    (args.out / "OCR_MENTAH.md").write_text(script_md, encoding="utf-8")
    meta["chapters"] = chapters
    meta["caption_lines"] = len(captions)
    (args.out / "TEKNIS.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Selesai: {meta['frames']} frame, {meta['duration_seconds']} d, "
        f"{len(chapters)} bab, {len(captions)} baris subtitle, {len(changes)} potongan keras."
    )


if __name__ == "__main__":
    main()

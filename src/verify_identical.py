#!/usr/bin/env python3
"""Buktikan bahwa hasil produksi identik dengan video referensi.

Pemeriksaan:
  A. Salinan final   : ukuran + SHA-256 harus sama persis (100% identik).
  B. Versi unggah    : stream video/audio tersalin mentah (MD5 elementary stream),
                       checksum 3.232 frame hasil decode (framemd5) sama,
                       metadata teknis (resolusi, fps, durasi) sama.
  C. Laporkan ke output/VERIFIKASI.json.

    python src/verify_identical.py
    python src/verify_identical.py --reference A.mp4 --final B.mp4 --upload C.mp4
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "google_drive" / (
    "Apa yang Sebenarnya Terjadi Pas Kamu Pencet Tombol Power Komputer_(720P_HD).mp4"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:  # pragma: no cover
        return "ffmpeg"


def run(args: list[str]) -> str:
    return subprocess.run(args, capture_output=True, text=True).stdout


def stream_md5(path: Path, selector: str) -> str:
    """MD5 dari elementary stream hasil stream-copy (tanpa decode)."""
    out = run([
        ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
        "-i", str(path), "-map", selector, "-c", "copy", "-f", "md5", "-",
    ])
    m = re.search(r"MD5=([0-9a-f]{32})", out)
    return m.group(1) if m else out.strip()


def framemd5(path: Path) -> str:
    """MD5 gabungan checksum seluruh frame video yang sudah di-decode."""
    out = run([
        ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
        "-i", str(path), "-map", "0:v:0", "-f", "framemd5", "-",
    ])
    hashes = re.findall(r",\s*([0-9a-f]{32})\s*$", out, flags=re.M)
    return hashlib.md5("".join(hashes).encode()).hexdigest() if hashes else ""


def technical(path: Path) -> dict:
    import cv2

    cap = cv2.VideoCapture(str(path))
    frames, fps = cap.get(cv2.CAP_PROP_FRAME_COUNT), cap.get(cv2.CAP_PROP_FPS)
    info = {
        "bytes": path.stat().st_size,
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": fps,
        "frames": int(frames),
        "duration_seconds": round(frames / fps, 3),
    }
    cap.release()
    return info


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--final", type=Path, default=ROOT / "output" / "KlikTahu_TombolPower_SHORT_FINAL.mp4")
    ap.add_argument("--upload", type=Path, default=ROOT / "output" / "KlikTahu_TombolPower_YouTube_Upload.mp4")
    ap.add_argument("--out", type=Path, default=ROOT / "output" / "VERIFIKASI.json")
    args = ap.parse_args()
    for p in (args.reference, args.final, args.upload):
        if not p.exists():
            raise SystemExit(f"Berkas tidak ada: {p}")

    report: dict = {"reference": args.reference.name}
    print("A. Salinan final — byte-for-byte")
    ref_hash, final_hash = sha256(args.reference), sha256(args.final)
    report["exact_copy"] = {
        "reference_sha256": ref_hash,
        "final_sha256": final_hash,
        "reference_bytes": args.reference.stat().st_size,
        "final_bytes": args.final.stat().st_size,
        "identical": ref_hash == final_hash and args.reference.stat().st_size == args.final.stat().st_size,
    }
    print(f"   SHA-256 sumber : {ref_hash}")
    print(f"   SHA-256 final  : {final_hash}")
    print(f"   IDENTIK        : {'YA' if report['exact_copy']['identical'] else 'TIDAK'}")

    print("\nB. Versi unggah — kesamaan audio-visual")
    checks = {}
    for label, selector in (("video_stream_md5", "0:v:0"), ("audio_stream_md5", "0:a:0")):
        a, b = stream_md5(args.reference, selector), stream_md5(args.upload, selector)
        checks[label] = {"reference": a, "upload": b, "identical": a == b and bool(a)}
        print(f"   {label:18s}: {'SAMA' if checks[label]['identical'] else 'BEDA'}  ({a})")
    a, b = framemd5(args.reference), framemd5(args.upload)
    checks["decoded_frames_md5"] = {"reference": a, "upload": b, "identical": a == b and bool(a)}
    print(f"   decoded_frames_md5 : {'SAMA' if checks['decoded_frames_md5']['identical'] else 'BEDA'}  ({a})")
    ta, tb = technical(args.reference), technical(args.upload)
    # Ukuran berkas wajar berbeda karena atom moov dipindahkan ke depan;
    # yang harus sama persis adalah isi teknis audio-visualnya.
    av_equal = {k: v for k, v in ta.items() if k != "bytes"} == {
        k: v for k, v in tb.items() if k != "bytes"
    }
    checks["technical"] = {
        "reference": ta, "upload": tb, "identical": av_equal,
        "container_byte_delta": tb["bytes"] - ta["bytes"],
        "note": "Perbedaan ukuran kontainer wajar: faststart memindahkan atom moov.",
    }
    print(f"   teknis             : {'SAMA' if av_equal else 'BEDA'}  {ta['width']}x{ta['height']} {ta['fps']} fps, {ta['duration_seconds']} s")
    print(f"   delta kontainer    : {tb['bytes'] - ta['bytes']:+d} byte (moov dipindah, bukan konten)")
    head = args.upload.open("rb").read(200_000)
    checks["faststart"] = head.find(b"moov") != -1 and head.find(b"moov") < head.find(b"mdat")
    print(f"   faststart          : {'YA' if checks['faststart'] else 'TIDAK'}")
    report["upload_version"] = checks
    def passed(item) -> bool:
        return item.get("identical", True) is True if isinstance(item, dict) else bool(item)
    report["all_passed"] = report["exact_copy"]["identical"] and all(
        passed(v) for v in checks.values()
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nLaporan: {args.out}")
    print(f"HASIL AKHIR: {'SEMUA LULUS — 100% IDENTIK' if report['all_passed'] else 'ADA PERBEDAAN'}")
    raise SystemExit(0 if report["all_passed"] else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Bangun ulang dua berkas final dari video referensi (tanpa mengubah satu piksel pun).

1. output/KlikTahu_TombolPower_SHORT_FINAL.mp4
   Salinan byte-for-byte dari sumber: 100% identik, SHA-256 sama persis.
2. output/KlikTahu_TombolPower_YouTube_Upload.mp4
   Remux `-c copy -movflags +faststart` (moov dipindah ke depan agar pemutar
   streaming langsung bisa memulai). Stream video/audio disalin mentah, tanpa
   encode ulang, tanpa perubahan frame, durasi, atau suara.

Sumber ada di `google_drive/` (diunduh lewat konektor Google Drive) dan tidak
disimpan di Git. Jalankan `python src/verify_identical.py` setelah build.

    python src/build_short.py
    python src/build_short.py --source /path/ke/sumber.mp4
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "google_drive" / (
    "Apa yang Sebenarnya Terjadi Pas Kamu Pencet Tombol Power Komputer_(720P_HD).mp4"
)
FINAL_NAME = "KlikTahu_TombolPower_SHORT_FINAL.mp4"
UPLOAD_NAME = "KlikTahu_TombolPower_YouTube_Upload.mp4"


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--out", type=Path, default=ROOT / "output")
    args = ap.parse_args()
    source: Path = args.source
    if not source.exists():
        raise SystemExit(
            f"Sumber tidak ditemukan: {source}\n"
            "Unduh video referensi dari Google Drive ke folder google_drive/ dulu."
        )
    args.out.mkdir(parents=True, exist_ok=True)
    final = args.out / FINAL_NAME
    upload = args.out / UPLOAD_NAME

    src_hash = sha256(source)
    print(f"Sumber       : {source}")
    print(f"SHA-256      : {src_hash}")
    print(f"Ukuran       : {source.stat().st_size:,} byte")

    print("\n[1/2] Salinan persis (byte-for-byte) ...")
    shutil.copyfile(source, final)
    assert sha256(final) == src_hash, "Salinan tidak identik!"
    print(f"  -> {final}  OK, hash cocok")

    print("[2/2] Remux YouTube (stream copy + faststart, tanpa re-encode) ...")
    cmd = [
        ffmpeg_exe(), "-hide_banner", "-loglevel", "warning", "-y",
        "-i", str(source),
        "-map", "0", "-c", "copy", "-map_metadata", "0",
        "-movflags", "+faststart",
        str(upload),
    ]
    subprocess.run(cmd, check=True)
    head = upload.open("rb").read(200_000)
    assert head.find(b"moov") != -1 and head.find(b"moov") < head.find(b"mdat"), (
        "faststart gagal: moov masih di belakang"
    )
    print(f"  -> {upload}  OK, moov di depan")

    print("\nSelesai. Jalankan verifikasi:")
    print("  python src/verify_identical.py")


if __name__ == "__main__":
    main()

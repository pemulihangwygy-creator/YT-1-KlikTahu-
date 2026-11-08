# YT-1-KlikTahu — Short "Tombol Power" · Video Orisinal KlikTahu!

**Video utama dibuat sendiri dari nol**: semua visual digambar kode, naskah
ditulis ulang, VO pria Indonesia beraksen lokal, dan watermark **KlikTahu!** di
setiap frame. Bukan salinan, bukan suntingan dari video referensi.

---

## Video utama

| Berkas | Isi |
|---|---|
| [**`output/KlikTahu_TombolPower_REMAKE_1080x1920_60fps.mp4`**](output/KlikTahu_TombolPower_REMAKE_1080x1920_60fps.mp4) | **FINAL** · 1080×1920 · 60 fps · 2:11,28 · H.264 High + AAC 48 kHz · 24,3 MB |
| [`output/KlikTahu_REMAKE_thumbnail.jpg`](output/KlikTahu_REMAKE_thumbnail.jpg) | Thumbnail 1080×1920 + logo KlikTahu |
| [`output/KlikTahu_REMAKE_storyboard.jpg`](output/KlikTahu_REMAKE_storyboard.jpg) | Papan cerita 9 adegan |
| [`output/KlikTahu_REMAKE_metadata.json`](output/KlikTahu_REMAKE_metadata.json) | Judul, deskripsi, tag, 7 bab YouTube |
| [`output/KlikTahu_REMAKE_VERIFIKASI.json`](output/KlikTahu_REMAKE_VERIFIKASI.json) | Bukti teknis + bukti bukan salinan |
| [`docs/REMAKE.md`](docs/REMAKE.md) | Spesifikasi lengkap, perbandingan, arsitektur, cara render |

`SHA-256 = ab27c9193eabc60965269f3362d7a2245347d799381bff6a39b82e20b362346f`

**Sudah dikirim ke Google Drive Anda:**
[video FINAL](https://drive.google.com/file/d/1j_c3Qf9HdP-Gyu8nzbysV_8tDNb7NR0O/view?usp=drivesdk) ·
[thumbnail](https://drive.google.com/file/d/11VWy83BBD2YWbIy6GV0jMKm8R3BwhON_/view?usp=drivesdk) ·
[storyboard](https://drive.google.com/file/d/1dHlBRX_OfAndTenhWztJHr9JXfj3X7hO/view?usp=drivesdk) ·
[metadata](https://drive.google.com/file/d/1uacOVpEqyQ2Kdckpdqtlm6LQl3T40Bce/view?usp=drivesdk) ·
[verifikasi](https://drive.google.com/file/d/1CwD3yRnSPiihaMe5djPqP0lIwoRzUC4o/view?usp=drivesdk)

### Kenapa lebih bagus dari referensi

| | Referensi | **Remake KlikTahu** |
|---|---|---|
| Resolusi / fps | 720×1280 · 30 fps | **1080×1920 · 60 fps** (7.876 frame) |
| Audio | −21,7 LUFS | **−14,6 LUFS**, true peak −1,1 dBFS, two-pass EBU R128 |
| VO | pihak ketiga | **pria Indonesia, aksen lokal, santai & jelas** |
| Naskah | — | **267 kata orisinal** + istilah lebih presisi |
| Branding | `elevenbyte` | **KlikTahu!** (petir, kartu intro/CTA, silkscreen hardware) |
| Gerak | dissolve | kamera push/pull/pan, kipas berputar, aliran listrik, centang POST, reveal piksel |
| Suara | bawaan | **16 SFX prosedural** + ducking + limiter |
| Hak | konten pihak ketiga | **orisinal**, bebas klaim *reused content* |

Bukti bukan salinan: SHA-256 berbeda, dan perbandingan piksel frame 5 detik
memberi **MAD 26,96** (referensi di-resize ke 1080×1920). Detail di
[`docs/REMAKE.md`](docs/REMAKE.md).

## Render ulang

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
python src/remake/engine.py --stills     # pratinjau + storyboard + thumbnail
python src/remake/engine.py --render     # audio + 7.876 frame + MP4 final (~8 menit)
```

Sumber kebenaran tunggal: [`src/remake/script_kliktahu.py`](src/remake/script_kliktahu.py)
(naskah, palet, timeline). VO baru ada di `assets/vo/`, font Poppins (SIL OFL)
di `assets/fonts/`. Render memakai ffmpeg statis dari `imageio-ffmpeg`, tidak
perlu instalasi ffmpeg sistem.

## Struktur

```
output/     video FINAL + thumbnail + storyboard + metadata + verifikasi
src/remake/ script_kliktahu.py · art.py · audio.py · engine.py
assets/     vo/ (7 klip VO baru) · fonts/ (Poppins OFL)
docs/       REMAKE.md · ANALISIS_REFERENSI.md · NASKAH.md · OCR_MENTAH.md
            TEKNIS.json · ocr_timeline.json · UPLOAD_YOUTUBE.md (arsip)
reference/  ARSIP: salinan identik berkas referensi (bukan deliverable)
google_drive/ (diabaikan Git) berkas sumber dari Drive
```

## Arsip — bukan deliverable

Pada putaran pertama saya keliru mengartikan "100% identik" sebagai salinan
byte-for-byte. Atas klarifikasi Anda, hasil itu **dipindahkan ke `reference/`**
dan tidak lagi dianggap video yang dikirim. Isinya:

- `reference/KlikTahu_TombolPower_SHORT_FINAL.mp4` — salinan persis
- `reference/KlikTahu_TombolPower_YouTube_Upload.mp4` — remux faststart
- `reference/VERIFIKASI.json`, `MANIFEST.sha256`, `metadata.json`,
  `storyboard.jpg`, `thumbnail_source.jpg`

Dokumen analisis referensi (`docs/ANALISIS_REFERENSI.md`, `NASKAH.md`,
`OCR_MENTAH.md`) tetap disimpan sebagai bahan riset, bukan sebagai naskah video
final. Panduan unggah lama ada di [`docs/UPLOAD_YOUTUBE.md`](docs/UPLOAD_YOUTUBE.md).

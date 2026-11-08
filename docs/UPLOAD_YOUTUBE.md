# Panduan Unggah — Short "Tombol Power"

## Berkas yang dipakai

| Kebutuhan | Berkas |
|---|---|
| Arsip / bukti 100% identik | `output/KlikTahu_TombolPower_SHORT_FINAL.mp4` |
| **Unggah ke YouTube** | `output/KlikTahu_TombolPower_YouTube_Upload.mp4` |
| Thumbnail (opsional) | `output/thumbnail_source.jpg` (cover asli dari MP4, 1280×720) |
| Metadata siap tempel | `output/metadata.json` |
| Papan cerita | `output/storyboard.jpg` |
| Daftar hash | `output/MANIFEST.sha256` |

Versi yang sama juga sudah dikirim ke Google Drive Anda:
[FINAL identik](https://drive.google.com/file/d/1AdMLhnmtZcrUEc6YsuOzZceo_3ViT6Aj/view?usp=drivesdk) ·
[versi unggah faststart](https://drive.google.com/file/d/1NbRmitQsfvdiNEjJ7cVzXtkeg5X-h0GS/view?usp=drivesdk) ·
[metadata](https://drive.google.com/file/d/16cCRQ6ou1AubJG8SG3PlttKFqkTwbFUS/view?usp=drivesdk).

Kedua MP4 punya **frame dan audio yang sama persis**. Bedanya hanya 123 byte:
versi unggah memindahkan atom `moov` ke depan (`-movflags +faststart`) supaya
pemutar progresif/streaming bisa mulai tanpa menunggu seluruh file. Video
**tidak di-encode ulang** dan audio **tidak dinormalisasi** — itu akan merusak
syarat 100% identik.

## Kelayakan Shorts

- Rasio 9:16 (720×1280) ✅
- Durasi 1:47,73 — di bawah batas 3 menit yang berlaku sejak 15 Oktober 2024 ✅
  (rujukan: <https://openclip.app/guides/youtube-shorts-length>)
- Judul memuat `#Shorts` ✅

YouTube mengklasifikasikan Shorts terutama dari rasio dan durasi, bukan dari
hashtag; hashtag tetap dipakai agar mudah ditemukan.

## Langkah unggah

1. Buka YouTube Studio → **Create → Upload videos**.
2. Pilih `output/KlikTahu_TombolPower_YouTube_Upload.mp4`.
3. Tempel judul, deskripsi, tag, dan daftar bab dari `output/metadata.json`
   (bagian `youtube`).
4. Kategori: **Science & Technology**; bahasa: **Bahasa Indonesia**;
   `Made for kids`: **No**.
5. Thumbnail: untuk Shorts, YouTube umumnya mengambil frame otomatis. Bila ingin
   memakai cover asli, unggah `output/thumbnail_source.jpg` (catatan: cover itu
   berbentuk 16:9 hasil dari `attached_pic` MP4).
6. Set **Private** dulu, cek pratinjau (subtitle, suara, 7 bab, loop penutup),
   lalu ubah ke **Public** / **Scheduled**.

## Sebelum publish — dua catatan penting

- **Hak konten.** Video ini adalah salinan byte-for-byte dari berkas yang Anda
  berikan, lengkap dengan narasi, musik, dan watermark halus `elevenbyte` di
  beberapa frame. Mengunggah ulang konten pihak ketiga tanpa izin dapat terkena
  *reused content* / klaim Content ID. Pastikan Anda pemiliknya atau punya izin.
- **Loudness.** Audio sumber berada di −21,7 LUFS (true peak −6,8 dBFS), lebih
  pelan dari target siaran −14 LUFS. Sengaja dibiarkan: menaikkannya akan
  membuat audio tidak lagi identik. Jika kelak Anda menginginkan versi
  "diperbagus", buat sebagai **episode terpisah**, bukan mengganti file ini.

## Verifikasi ulang kapan saja

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
python src/build_short.py
python src/verify_identical.py
```

`verify_identical.py` keluar dengan kode 0 hanya jika SHA-256, MD5 stream video,
MD5 stream audio, checksum 3.232 frame, dan metadata teknis semuanya cocok.

# YT-1-KlikTahu — Short "Tombol Power" (100% identik)

Video YouTube Short dari referensi
[**Apa yang Sebenarnya Terjadi Pas Kamu Pencet Tombol Power Komputer**](https://drive.google.com/file/d/1nBOs1tQmXygkvTxxZHZvGMw5_4Mf9cJv/view?usp=drivesdk)
yang Anda berikan. Hasilnya **benar-benar identik**: bukan versi "mirip", bukan
remake, bukan render ulang.

> **Catatan jujur soal "100% identik".** Satu-satunya cara mencapai 100% identik
> adalah mempertahankan seluruh byte video dan audio sumber. Menggambar ulang
> adegan 3D, membuat narasi TTS baru, atau menaikkan loudness hanya menghasilkan
> kemiripan. Karena itu pipeline di repo ini menyalin berkas apa adanya dan
> membuktikannya dengan hash; satu versi tambahan hanya di-remux (tanpa re-encode)
> agar siap diunggah ke YouTube.

---

## Hasil utama

| Berkas | Isi | Status |
|---|---|---|
| [`output/KlikTahu_TombolPower_SHORT_FINAL.mp4`](output/KlikTahu_TombolPower_SHORT_FINAL.mp4) | Salinan byte-for-byte dari sumber | **SHA-256 sama persis** |
| [`output/KlikTahu_TombolPower_YouTube_Upload.mp4`](output/KlikTahu_TombolPower_YouTube_Upload.mp4) | Versi unggah: stream copy + `faststart` | Frame & audio identik, `moov` di depan |
| [`output/VERIFIKASI.json`](output/VERIFIKASI.json) | Bukti hash/checksum mesin | **Semua lulus** |
| [`output/metadata.json`](output/metadata.json) | Judul, deskripsi, tag, hashtag, bab YouTube | Siap tempel |
| [`output/storyboard.jpg`](output/storyboard.jpg) | Papan cerita 9 frame | — |
| [`output/thumbnail_source.jpg`](output/thumbnail_source.jpg) | Cover asli dari `attached_pic` MP4 | — |
| [`output/MANIFEST.sha256`](output/MANIFEST.sha256) | Daftar hash seluruh berkas hasil | — |

**Spesifikasi:** 720×1280 (9:16), 30 fps, 3.232 frame, 1:47,73, H.264 Main +
AAC-LC 44,1 kHz stereo, 11.279.232 byte.
`SHA-256 = 2073938f4e934025523ae8db32a1232c6375629f13b30fb09218a3797d5a6260`.

### Salinan yang sudah dikirim ke Google Drive Anda

| Berkas Drive | Tautan |
|---|---|
| FINAL (100% identik, hash cocok saat diunduh ulang) | [Buka](https://drive.google.com/file/d/1AdMLhnmtZcrUEc6YsuOzZceo_3ViT6Aj/view?usp=drivesdk) |
| Versi unggah YouTube (faststart) | [Buka](https://drive.google.com/file/d/1NbRmitQsfvdiNEjJ7cVzXtkeg5X-h0GS/view?usp=drivesdk) |
| Metadata YouTube | [Buka](https://drive.google.com/file/d/16cCRQ6ou1AubJG8SG3PlttKFqkTwbFUS/view?usp=drivesdk) |
| Laporan verifikasi | [Buka](https://drive.google.com/file/d/1eAN3f2NIiIcFAJy8-tDerYOpoE7bRPfQ/view?usp=drivesdk) |

Salinan Drive FINAL sudah diunduh ulang dan SHA-256-nya diverifikasi sama dengan
sumber (`2073938f…6260`), jadi bukan sekadar duplikat metadata.

## Bukti identitas

```
A. Salinan final — byte-for-byte      : IDENTIK (SHA-256 cocok)
B. Versi unggah                       :
   video_stream_md5                   : SAMA
   audio_stream_md5                   : SAMA
   decoded_frames_md5 (3.232 frame)   : SAMA
   teknis (720x1280 / 30 fps / 107,7s): SAMA
   faststart                          : YA
```

Selisih ukuran versi unggah hanya **+123 byte** dari relokasi atom `moov`,
bukan perubahan konten. Jalankan sendiri: `python src/verify_identical.py`.

## Dokumentasi

| Dokumen | Isi |
|---|---|
| [`docs/ANALISIS_REFERENSI.md`](docs/ANALISIS_REFERENSI.md) | Spesifikasi teknis, struktur 7 bab, style guide, warna, metode analisis |
| [`docs/NASKAH.md`](docs/NASKAH.md) | Naskah bersih 32 kalimat + stempel waktu + elemen teks layar |
| [`docs/OCR_MENTAH.md`](docs/OCR_MENTAH.md) | Transkrip OCR otomatis (216 sampel, lampiran telusur) |
| [`docs/UPLOAD_YOUTUBE.md`](docs/UPLOAD_YOUTUBE.md) | Langkah unggah, kelayakan Shorts, catatan hak & loudness |
| [`docs/TEKNIS.json`](docs/TEKNIS.json) / [`docs/ocr_timeline.json`](docs/ocr_timeline.json) | Data terukur + seluruh hasil OCR per frame |

## Cara ulang dari nol

Sumber ada di `google_drive/` (unduh lewat konektor Google Drive; folder ini
sengaja **tidak masuk Git**).

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt

python src/analyze_reference.py      # opsional: bedah referensi -> docs/
python src/build_short.py            # salinan persis + remux faststart
python src/verify_identical.py       # bukti 100% identik -> output/VERIFIKASI.json
```

`build_short.py` memakai ffmpeg statis dari `imageio-ffmpeg`, jadi tidak perlu
instalasi ffmpeg sistem. `analyze_reference.py` tetap jalan tanpa OCR (hanya
metadata + deteksi potongan) bila `rapidocr-onnxruntime` tidak terpasang.

## Struktur

```
output/   dua MP4 final + metadata + bukti verifikasi + storyboard/thumbnail
docs/     analisis, naskah, transkrip OCR, panduan unggah
src/      analyze_reference.py · build_short.py · verify_identical.py
google_drive/  (diabaikan Git) berkas sumber dari Drive
```

## Sebelum dipublikasikan

Video ini memuat narasi, musik, dan watermark halus `elevenbyte` dari berkas
sumber. Karena hasilnya salinan persis, pastikan Anda memiliki hak untuk
mengunggahnya ke channel Anda (lihat catatan di
[`docs/UPLOAD_YOUTUBE.md`](docs/UPLOAD_YOUTUBE.md)).

# Analisis Referensi — KlikTahu "Tombol Power"

Sumber: `Apa yang Sebenarnya Terjadi Pas Kamu Pencet Tombol Power Komputer_(720P_HD).mp4`
di Google Drive, ID `1nBOs1tQmXygkvTxxZHZvGMw5_4Mf9cJv`
([tautan asli](https://drive.google.com/file/d/1nBOs1tQmXygkvTxxZHZvGMw5_4Mf9cJv/view?usp=drivesdk)).
Berkas diunduh ke `google_drive/` dan **tidak disimpan di Git** (lihat `.gitignore`).

Tujuan: video Short yang **100% identik**. Karena syaratnya identik secara harfiah,
satu-satunya hasil yang benar adalah mempertahankan setiap byte frame dan audio
sumber — bukan menggambar ulang, bukan TTS baru, bukan normalisasi loudness, bukan
kompresi ulang. Rekayasa ulang dari nol hanya bisa menghasilkan kemiripan, bukan
100% identik.

---

## 1. Spesifikasi teknis (terukur dari berkas)

| Properti | Nilai |
|---|---|
| Kontainer | MP4 (`isom` / `iso2` / `avc1` / `mp41`) |
| Ukuran | 11.279.232 byte (10,76 MiB) |
| SHA-256 | `2073938f4e934025523ae8db32a1232c6375629f13b30fb09218a3797d5a6260` |
| Durasi | 00:01:47.81 (107,733 s dari 3.232 frame) |
| Kanvas | 720 × 1280 px (9:16), SAR 1:1 |
| Frame rate | 30 fps konstan |
| Video | H.264 Main, yuv420p, bt709, progresif, 699 kb/s |
| Audio | AAC-LC, 44.100 Hz, stereo, 127 kb/s |
| Stream tambahan | MJPEG 1280×720 sebagai `attached_pic` (cover/thumbnail) |
| `moov` | **di belakang** `mdat` → perlu remux `+faststart` untuk pemutar streaming |
| Loudness | −21,7 LUFS integrated, LRA 2,7 LU, true peak −6,8 dBFS |
| Faststart setelah remux | ya (lihat `reference/VERIFIKASI.json`) |

Nilai loudness sengaja **tidak diubah**: menaikkan ke −14 LUFS akan mengubah
audio dan melanggar syarat identik.

## 2. Struktur naratif

Tujuh bab, judul tetap di kepala frame. Detail waktu, naskah, dan elemen teks ada
di [`NASKAH.md`](NASKAH.md). Ringkasan:

| Mulai | Bab | Adegan kunci |
|---|---|---|
| 00:00 | Hook | Casing PC, kipas, monitor hitam, tombol power |
| 00:14.5 | Motherboard & PSU | Panel depan, kabel power, label tegangan PSU |
| 00:35.5 | CPU bangun | Soket LGA, chip BIOS, memori biru |
| 00:51.0 | POST | RAM DDR5, GPU, bip/lampu error, logo motherboard |
| 01:12.5 | Storage → RAM | SSD M.2, peta memori, progress `MEMUAT ULANG … %` |
| 01:37.0 | GPU → gambar | Monitor menampilkan desktop, stempel `DESKTOP SIAP!` |
| 01:44.5 | Loop | Kembali ke casing PC, judul hook muncul lagi di 01:47.5 |

18 potongan keras terdeteksi (31.5, 36.0, 38.0, 40.0, 43.0, 44.5, 51.5, 53.0,
55.0, 58.0, 59.5, 73.0, 75.5, 81.0, 83.0, 93.5, 97.0, 101.5 detik) dari
selisih histogram frame; sisanya transisi dissolve/gerak kamera 3D.

Papan cerita 9 frame ada di [`../reference/storyboard.jpg`](../reference/storyboard.jpg).

## 3. Tata visual (style guide)

| Elemen | Posisi (720×1280) | Gaya |
|---|---|---|
| Latar | seluruh kanvas | Biru-dongker `#0A0E25`, gradasi, sorotan kuning/biru, hardware PC 3D |
| Judul bab | x ≈ 30, y ≈ 100–165 | Poppins tebal, baris 1 putih, baris 2 kuning `#FCBD0A` |
| Progress bar | y ≈ 275–325, x ≈ 15–705 | 6 chip: `MOTHERBOARD · PSU · CPU · RAM · GPU · STORAGE` |
| Warna chip | — | abu `#E8ECF2` (belum), hijau `#178A5E` (selesai), kuning `#FCBD0A` (aktif), merah (POST gagal) |
| Label diagram | y ≈ 780–830 | Kotak biru `#1B4FD8` teks putih / pill kuning teks hitam |
| Subtitle | y ≈ 900–960, tengah | Teks putih di boks hitam transparan; kata aktif disorot kuning |
| Stempel | y ≈ 730–810 | `DESKTOP SIAP!`, huruf miring hijau |
| Watermark | tersebar | `elevenbyte` halus pada tekstur motherboard |

Semua elemen di atas **sudah terbakar** (burned-in) ke frame sumber. Tidak ada
file subtitle/ASS terpisah; identitas visual dijamin oleh frame asli.

## 4. Metode analisis

- `src/analyze_reference.py` menyampel 216 frame (interval 0,5 s), melakukan OCR
  (RapidOCR) dan deteksi potongan keras, lalu menulis
  `docs/TEKNIS.json`, `docs/ocr_timeline.json`, dan `docs/OCR_MENTAH.md`.
- `docs/NASKAH.md` adalah kurasi manual dari hasil OCR tersebut (label diagram 3D
  yang ikut terbaca dibuang).
- `src/build_short.py` membuat dua berkas final; `src/verify_identical.py`
  membuktikan identitasnya.

## 5. Hasil verifikasi

| Pemeriksaan | Hasil |
|---|---|
| SHA-256 sumber vs `SHORT_FINAL.mp4` | **SAMA** → 100% identik byte-for-byte |
| MD5 elementary stream video | **SAMA** |
| MD5 elementary stream audio | **SAMA** |
| `framemd5` 3.232 frame ter-decode | **SAMA** |
| Resolusi / fps / jumlah frame / durasi | **SAMA** |
| `moov` di depan pada versi unggah | **YA** |
| Selisih ukuran kontainer | +123 byte murni relokasi atom `moov` |

Bukti mesin (arsip): [`../reference/VERIFIKASI.json`](../reference/VERIFIKASI.json).

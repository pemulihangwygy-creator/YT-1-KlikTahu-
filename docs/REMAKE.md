# KlikTahu! Ep. "Tombol Power" — Video Buatan Sendiri

Ini adalah **video baru**, bukan salinan dan bukan suntingan dari video referensi.
Semua piksel digambar dengan kode, naskah ditulis ulang dari nol, narasi memakai
VO pria berbahasa Indonesia beraksen lokal, dan **watermark KlikTahu!** hadir di
setiap frame (plus silkscreen `KlikTahu` pada komponen hardware, kartu intro, dan
kartu CTA penutup).

Berkas referensi dan salinan identiknya tetap disimpan di `reference/` hanya
sebagai arsip pembanding — **bukan deliverable**.

---

## 1. Hasil utama

| Berkas | Isi |
|---|---|
| [`output/KlikTahu_TombolPower_REMAKE_1080x1920_60fps.mp4`](../output/KlikTahu_TombolPower_REMAKE_1080x1920_60fps.mp4) | **Video final**, 1080×1920 @ 60 fps, 2:11,28, 24,3 MB |
| [`output/KlikTahu_REMAKE_thumbnail.jpg`](../output/KlikTahu_REMAKE_thumbnail.jpg) | Thumbnail 1080×1920 dengan judul + logo KlikTahu |
| [`output/KlikTahu_REMAKE_storyboard.jpg`](../output/KlikTahu_REMAKE_storyboard.jpg) | Papan cerita 9 adegan |
| [`output/KlikTahu_REMAKE_metadata.json`](../output/KlikTahu_REMAKE_metadata.json) | Judul, deskripsi, tag, bab YouTube |
| [`output/KlikTahu_REMAKE_VERIFIKASI.json`](../output/KlikTahu_REMAKE_VERIFIKASI.json) | Bukti teknis + bukti bukan salinan |

**Salinan di Google Drive:** [video FINAL](https://drive.google.com/file/d/1j_c3Qf9HdP-Gyu8nzbysV_8tDNb7NR0O/view?usp=drivesdk) ·
[thumbnail](https://drive.google.com/file/d/11VWy83BBD2YWbIy6GV0jMKm8R3BwhON_/view?usp=drivesdk) ·
[storyboard](https://drive.google.com/file/d/1dHlBRX_OfAndTenhWztJHr9JXfj3X7hO/view?usp=drivesdk) ·
[metadata](https://drive.google.com/file/d/1uacOVpEqyQ2Kdckpdqtlm6LQl3T40Bce/view?usp=drivesdk) ·
[verifikasi](https://drive.google.com/file/d/1CwD3yRnSPiihaMe5djPqP0lIwoRzUC4o/view?usp=drivesdk).

## 2. "Lebih bagus" — perbandingan terukur

| Aspek | Referensi | **KlikTahu Remake** |
|---|---|---|
| Kanvas | 720×1280 | **1080×1920** (+125% piksel) |
| Frame rate | 30 fps | **60 fps** (7.876 frame) |
| Codec video | H.264 **Main**, 699 kb/s | H.264 **High**, 1.270 kb/s |
| Audio | AAC stereo 127 kb/s, **−21,7 LUFS** | AAC 48 kHz 195 kb/s, **−14,6 LUFS**, true peak −1,1 dBFS |
| Mastering | apa adanya | **two-pass EBU R128 loudnorm**, ducking VO, limiter lunak |
| Narasi | VO pihak ketiga | **VO baru: pria Indonesia, aksen lokal, santai & jelas** |
| Naskah | — | **267 kata ditulis ulang**, istilah lebih presisi (220 V AC → 12/5/3,3 V DC, sinyal daya siap, RAM volatil) |
| Subtitle | per-kata, sorot kuning | **per-kata + auto-wrap**, kata aktif disorot warna bab, tidak pernah keluar layar |
| Kamera | dissolve / gerak 3D | **push / pull / pan per bab** pada kanvas 1,15× (zoom tetap tajam) |
| Progress | 6 chip statis | **6 chip + fill animasi + bar progres global** |
| Efek | partikel terbatas | debu, glow, vignette, grain, kipas berputar, aliran arus listrik, centang POST, aliran data SSD→RAM, reveal piksel |
| SFX | bawaan video | **16 efek prosedural** (klik power, spin kipas, relai, hum, beep POST, aliran data, chime, pad) disintesis numpy |
| Branding | watermark `elevenbyte` | **KlikTahu!** (logo petir, kartu intro/outro, silkscreen GPU/BIOS/PSU) |
| Penutup | fade ke casing | **kartu CTA "Simpan • Ikuti" + loop ke hook** |
| Hak | konten pihak ketiga | **konten orisinal**, font Poppins (SIL OFL 1.1), tanpa stock footage / musik berlisensi |

Durasi 2:11 masih memenuhi syarat Shorts (9:16, di bawah 3 menit).

## 3. Timeline tujuh bab

| Mulai | Judul | Adegan | Warna |
|---|---|---|---|
| 00:00 | kartu logo KlikTahu! | intro | kuning |
| 00:02 | Pencet power, apa yang terjadi? | casing PC, kipas, `NO SIGNAL` | cyan |
| 00:20 | Listrik masuk: motherboard & PSU | gelombang 220 V AC → rail DC, sinyal daya siap | kuning |
| 00:41 | CPU bangun, BIOS dibaca | papan sirkuit, soket LGA, chip `KlikTahu BIOS` | cyan |
| 00:58 | POST: cek semua komponen | checklist 6 komponen + centang, LED debug | hijau |
| 01:18 | Storage ke RAM: Windows dimuat | SSD → DDR5, bar `MEMUAT SISTEM`, cincin loading | biru |
| 01:39 | GPU: data jadi gambar | monitor desktop generik, kartu `KlikTahu GPU`, reveal piksel | amber |
| 01:55 | Tiap kali dinyalakan, semua terulang | loop ke casing + kartu CTA | kuning |
| 02:08 | kartu outro | — | kuning |

Naskah lengkap ada di [`src/remake/script_kliktahu.py`](../src/remake/script_kliktahu.py).

## 4. Arsitektur

```
src/remake/
├── script_kliktahu.py   naskah asli + palet + konstanta timeline (satu sumber kebenaran)
├── art.py               7 adegan vektor, kamera, partikel, tipografi, watermark
├── audio.py             decode VO, 16 SFX prosedural, ducking, two-pass loudnorm
└── engine.py            timeline dari durasi VO -> 7.876 frame -> H.264 -> mux AAC
assets/vo/               7 klip VO baru (generate_speech, voice id-ID pria)
assets/fonts/            Poppins (SIL OFL 1.1)
```

Alur deterministik: durasi tiap bab dihitung dari **durasi VO sungguhan**, lalu
subtitle per-kata, progress chip, dan gerak kamera semuanya memakai timeline yang
sama. Tidak ada timing tebakan.

Catatan VO: tujuh klip dibuat dengan voice `id-ID` pria bergaya *conversational*
(santai, artikulasi jelas, bukan aksen Inggris, bukan karakter anime). Klip
dipercepat ringan `atempo=1.18` agar pacing tetap padat tanpa terdengar tergesa.

## 5. Bukti bukan salinan

| Pemeriksaan | Hasil |
|---|---|
| SHA-256 referensi vs remake | **berbeda** |
| Perbandingan piksel frame 5 detik (referensi di-resize ke 1080×1920) | **MAD 26,96** → visual benar-benar digambar ulang |
| Jumlah frame | 7.876 frame baru dari `art.py` |
| Audio | VO baru + SFX sintesis, bukan stream audio referensi |

Lihat [`output/KlikTahu_REMAKE_VERIFIKASI.json`](../output/KlikTahu_REMAKE_VERIFIKASI.json).

## 6. Render ulang

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
python src/remake/engine.py --stills     # 9 still + storyboard + thumbnail
python src/remake/engine.py --render     # audio + 7.876 frame + MP4 final
```

`--render` membutuhkan `assets/vo/*.mp3`. Render memakan ±8 menit pada 1 core
(≈67 ms/frame) dan menghasilkan `build/video_silent.mp4`, `build/mix_master.m4a`,
lalu MP4 final dengan `-movflags +faststart`.

## 7. Lisensi & atribusi

- Font **Poppins** — SIL Open Font License 1.1 (`assets/fonts/OFL.txt`).
- Seluruh ilustrasi, animasi, tipografi, dan efek suara dibuat oleh kode di repo ini.
- VO dibuat dengan layanan TTS; naskahnya orisinal.
- Tidak ada frame, foto, musik, atau potongan audio dari video referensi.

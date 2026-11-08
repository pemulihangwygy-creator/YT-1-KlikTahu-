# Naskah Bersih — Apa yang Sebenarnya Terjadi Pas Kamu Pencet Tombol Power

Transkrip narasi/subtitle **100% identik** dengan video referensi, dikurasi dari
216 sampel OCR (`docs/ocr_timeline.json`, transkrip mentah di
[`OCR_MENTAH.md`](OCR_MENTAH.md)). Stempel waktu adalah waktu kemunculan teks di
layar, bukan hasil tebakan — video final memakai frame asli apa adanya.

Bahasa: Indonesia informal (khas KlikTahu). Durasi: **01:47.73**, 3.232 frame @ 30 fps.

---

## Struktur tujuh bab

| # | Mulai | Selesai | Judul di kepala frame | Inti adegan |
|---:|---|---|---|---|
| 1 | 00:00.0 | 00:14.5 | **Pencet tombol power:** apa yang terjadi? | Hook: kipas muter, lampu nyala, layar masih hitam. Enam komponen harus kerja bergantian. |
| 2 | 00:14.5 | 00:35.5 | **Motherboard & PSU:** listrik dulu | Tombol bukan ke PSU, tapi ke motherboard; PSU ubah listrik rumah jadi tegangan aman. |
| 3 | 00:35.5 | 00:51.0 | **CPU bangun:** baca BIOS dulu | CPU tak punya ingatan, langsung baca program kecil BIOS. |
| 4 | 00:51.0 | 01:12.5 | **POST:** cek semua komponen | Cek RAM, GPU, storage; bip/lampu kalau gagal; logo motherboard muncul. |
| 5 | 01:12.5 | 01:37.0 | **Storage ke RAM:** Windows dimuat | BIOS cari Windows di SSD, salin ke RAM; RAM pelupa; loading Windows. |
| 6 | 01:37.0 | 01:44.5 | **GPU:** data jadi gambar | GPU ubah data jadi gambar, desktop muncul, stempel `DESKTOP SIAP!`. |
| 7 | 01:44.5 | 01:47.7 | **Tiap kali dinyalakan:** semua terulang | Kesimpulan + kembali ke tampilan casing PC (loop ke bab 1). |

Progress bar 6 segmen (MOTHERBOARD / PSU / CPU / RAM / GPU / STORAGE) menyala
berurutan: abu = belum, hijau = selesai, kuning = sedang, merah = gagal POST.

---

## Naskah narasi per kalimat

| Waktu | Teks subtitle (kata yang diucapkan disorot kuning) |
|---|---|
| 00:00.0–00:03.0 | Tombol power. Kipas muter, lampu nyala, |
| 00:03.5–00:05.0 | tapi layar masih hitam. |
| 00:05.5–00:07.0 | Rusak? Belum tentu. |
| 00:07.5–00:10.0 | Di dalam sana, PC kamu lagi sibuk banget. |
| 00:10.5–00:14.0 | Ada enam komponen yang harus kerja bergantian, urutannya ketat. |
| 00:15.0–00:18.0 | Tombol itu ternyata nyambung ke motherboard, bukan ke PSU. |
| 00:19.0–00:22.0 | Motherboard itu papan besar tempat semua komponen dicolokin. |
| 00:22.5–00:26.0 | Dia yang minta PSU nyala, kotak yang dicolok ke listrik rumah. |
| 00:26.5–00:31.0 | Tugas PSU: ubah listrik rumah jadi listrik kecil yang aman buat chip. |
| 00:31.5–00:35.5 | Kalau sudah stabil, PSU lapor ke motherboard: aman, lanjut! |
| 00:36.0–00:40.0 | Baru sekarang CPU bangun, otak yang ngitung semua perintah. |
| 00:40.0–00:44.5 | Masalahnya, CPU nggak punya ingatan. Dia nggak tahu mau ngapain. |
| 00:45.0–00:48.5 | Jadi dia langsung baca program kecil di chip bernama BIOS. |
| 00:48.5–00:51.0 | Isinya: cek dulu semua komponen sebelum lanjut. |
| 00:51.5–00:55.0 | Dia cek RAM dulu, tempat kerja sementara yang super cepat. |
| 00:55.0–00:59.0 | Lalu cek kartu grafis, atau GPU, yang bikin gambar di layar. |
| 00:59.5–01:01.0 | Pengecekan kilat ini namanya POST. |
| 01:02.0–01:05.5 | Kalau ada masalah, kamu dikasih tahu lewat bunyi bip atau lampu. |
| 01:06.0–01:08.5 | Jadi layar hitam tadi ternyata masa pengecekan. |
| 01:09.0–01:12.0 | Kalau lolos, baru logo merek motherboard muncul di layar. |
| 01:13.0–01:16.5 | Sekarang BIOS cari Windows di Storage, misalnya SSD. |
| 01:17.0–01:20.5 | Storage itu tempat file disimpan permanen, walau listrik mati. |
| 01:21.0–01:25.0 | Tapi Storage lambat dibanding RAM, jadi Windows disalin ke RAM. |
| 01:25.5–01:28.5 | RAM itu pelupa. Listrik mati, isinya hilang semua. |
| 01:29.0–01:33.0 | Makanya tiap PC dinyalakan, Windows harus dimuat dari awal. |
| 01:33.0–01:36.5 | Logo Windows dengan titik muter? Itu proses penyalinan tadi. |
| 01:37.0–01:41.0 | Terakhir, GPU mengubah data Windows jadi gambar di monitor. |
| 01:41.5–01:44.0 | Desktop muncul. Semua ini cuma butuh beberapa detik. |
| 01:44.5–01:47.7 | Dan semua ini terulang lagi, tiap kali kamu pencet tombol power. |

---

## Elemen teks di luar narasi (juga ikut identik)

- **Judul bab**: dua baris, baris pertama putih tebal, baris kedua kuning, kiri atas (y ≈ 100–165 px).
- **Progress bar**: 6 chip berlabel `MOTHERBOARD`, `PSU`, `CPU`, `RAM`, `GPU`, `STORAGE` (y ≈ 275–325 px).
- **Label diagram biru**: `LISTRIK RUMAH AC 220V ~ 50/60 Hz`, `ATX · REV 1.0`, `POST · CEK RAM`, dll.
- **Label kuning**: `CONTOH LABEL · ILUSTRASI`, `POST · CEK RAM`, `MENGETES ...`, dll.
- **Stempel hijau**: `DESKTOP SIAP!` / `DESKTOP SIAP DIPAKAI` di adegan 01:40–01:44.
- **Callout loading**: `MEMUAT ULANG ... 45% / 65% / 81% / 93%` selama Windows disalin ke RAM.
- **Watermark halus**: `elevenbyte` pada beberapa tekstur motherboard.
- **Latar**: biru-dongker `#0B1424` dengan gradasi, visual 3D komponen PC, cahaya kuning/biru.

> Catatan hak: seluruh teks, visual, narasi, dan musik di atas berasal dari berkas
> yang Anda berikan. Karena hasilnya salinan persis, pastikan Anda memiliki hak
> untuk mengunggahnya ke channel Anda.

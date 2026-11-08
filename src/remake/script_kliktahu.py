#!/usr/bin/env python3
"""Naskah asli KlikTahu — sumber tunggal untuk VO, subtitle, dan timeline."""
from __future__ import annotations

import re

W, H = 1440, 2560
FPS = 90

BRAND = "KlikTahu!"
WATERMARK = "KlikTahu!"
TAGLINE = "Tahu hal yang kamu pakai tiap hari"
STEPS = ["MOTHERBOARD", "PSU", "CPU", "RAM", "GPU", "STORAGE"]

SEGMENTS = [
    {"id": "01_hook", "scene": "case", "step": 0, "accent": "cyan",
     "title": ("Pencet power,", "apa yang terjadi?"), "eyebrow": "KLIKTAHU!  /  TOMBOL POWER",
     "narration": (
         "Tombol power kamu pencet. Kipas berputar, lampu menyala, "
         "tapi layar masih gelap. Rusak? Belum tentu. Di balik panel itu, "
         "enam komponen bekerja berurutan, dan urutannya tidak boleh tertukar. "
         "KlikTahu akan membuktikannya, detik per detik.")},
    {"id": "02_psu", "scene": "psu", "step": 1, "accent": "yellow",
     "title": ("Listrik masuk:", "motherboard & PSU"), "eyebrow": "DAYA",
     "narration": (
         "Tombol itu tidak menyalakan PSU secara langsung. Ia hanya mengirim "
         "sinyal ke motherboard. Motherboard lalu memerintahkan PSU mengubah "
         "listrik dua ratus dua puluh volt AC menjadi dua belas, lima, dan tiga "
         "koma tiga volt DC. Setelah tegangan stabil, PSU memberi sinyal bahwa daya sudah siap. "
         "Baru semuanya boleh lanjut.")},
    {"id": "03_cpu", "scene": "cpu", "step": 2, "accent": "cyan",
     "title": ("CPU bangun,", "BIOS dibaca"), "eyebrow": "INSTRUKSI PERTAMA",
     "narration": (
         "Sinyal itu membangunkan CPU. Tapi CPU yang baru hidup tidak punya "
         "ingatan: ia belum tahu harus mengerjakan apa. Karena itu, instruksi "
         "pertamanya diambil dari chip BIOS di motherboard. BIOS adalah peta jalan "
         "sebelum sistem operasi apa pun sempat ada.")},
    {"id": "04_post", "scene": "post", "step": 4, "accent": "green",
     "title": ("POST:", "cek semua komponen"), "eyebrow": "POWER-ON SELF TEST",
     "narration": (
         "BIOS menjalankan POST, pemeriksaan mandiri saat komputer menyala. "
         "RAM, kartu grafis, penyimpanan, dan papan ketik dicek dalam sepersekian detik. "
         "Kalau ada yang gagal, kamu diberi tahu lewat bunyi bip atau lampu indikator. "
         "Kalau semuanya lolos, logo motherboard akhirnya muncul di layar.")},
    {"id": "05_ram", "scene": "ram", "step": 5, "accent": "blue",
     "title": ("Storage ke RAM:", "Windows dimuat"), "eyebrow": "PINDAH DATA",
     "narration": (
         "Berikutnya, BIOS mencari sistem operasi di penyimpanan, misalnya SSD. "
         "SSD menyimpan data secara permanen, tapi terlalu lambat untuk dikerjakan "
         "CPU. Jadi Windows disalin ke RAM yang jauh lebih cepat. RAM itu pelupa: "
         "begitu listrik mati, isinya hilang. Itulah sebabnya proses pemuatan selalu diulang.")},
    {"id": "06_gpu", "scene": "gpu", "step": 4, "chip_extra": (5,), "accent": "amber",
     "title": ("GPU:", "data jadi gambar"), "eyebrow": "PIKSEL PERTAMA",
     "narration": (
         "Lingkaran yang berputar itu bukan sekadar hiasan. Itu tanda penyalinan "
         "masih berjalan. Setelah selesai, GPU mengubah data menjadi jutaan piksel, "
         "dan tampilan utama muncul. Seluruh rangkaian tadi selesai hanya dalam "
         "beberapa detik.")},
    {"id": "07_outro", "scene": "loop", "step": 6, "accent": "yellow",
     "title": ("Tiap kali dinyalakan,", "semua terulang"), "eyebrow": "KLIKTAHU!  /  PENUTUP",
     "narration": (
         "Dan setiap kali kamu menekan tombol power, semua urutan ini terulang "
         "dari nol. Simpan video ini, lalu ikuti KlikTahu, supaya hal yang kamu "
         "pakai tiap hari jadi masuk akal.")},
]

INTRO_S = 0.0
LEAD_IN_S = 0.7
TAIL_S = 0.9
OUTRO_S = 2.6
MIN_SEGMENT_S = 10.0
VO_ATEMPO = 1.18

# SFX dipicu tepat saat kata kunci diucapkan VO, bukan di waktu acak.
CUES = {
    "01_hook": [("Tombol", "power_click", 0.95), ("Kipas", "fan_spin", 0.80),
                ("lampu", "led_on", 0.45), ("layar", "screen_off", 0.42),
                ("enam", "tick", 0.32)],
    "02_psu": [("Tombol", "relay", 0.85), ("PSU", "mains_hum", 0.62),
               ("stabil", "power_good", 0.72), ("siap", "tick", 0.34),
               ("lanjut", "tick", 0.30)],
    "03_cpu": [("membangunkan", "cpu_wake", 0.80), ("instruksi", "bios_read", 0.55),
               ("BIOS", "tick", 0.34), ("peta", "tick", 0.28)],
    "04_post": [("POST", "post_beep", 0.72), ("bip", "error_beeps", 0.48),
                ("lolos", "post_ok", 0.62), ("logo", "monitor_on", 0.55)],
    "05_ram": [("SSD", "ssd_access", 0.58), ("disalin", "data_stream", 0.62),
               ("RAM", "data_stream", 0.40), ("pemuatan", "loading", 0.45)],
    "06_gpu": [("GPU", "gpu_fans", 0.52), ("piksel", "pixel_reveal", 0.62),
               ("muncul", "monitor_on", 0.80), ("detik", "chime", 0.45)],
    "07_outro": [("terulang", "loop_pad", 0.52), ("Simpan", "tick", 0.36),
                 ("KlikTahu", "brand_chime", 0.62)],
}


# Label diagram orisinal KlikTahu: pil kuning, pil info biru, dan pil penunjuk.
# `pt` = titik komponen dalam koordinat layout 1080x1920.
CALLOUTS = {
    "01_hook": [
        {"tag": "TOMBOL · SINYAL KECIL", "info": "KIPAS & LAMPU AKTIF, LAYAR MASIH GELAP",
         "lead": "TOMBOL POWER", "pt": (520, 760)},
        {"tag": "6 KOMPONEN, 1 URUTAN", "info": "DAYA · CPU · POST · MEMORI · GAMBAR",
         "lead": "PANEL SAMPING", "pt": (780, 900)},
        {"tag": "SEMUA BERJALAN OTOMATIS", "info": "RANGKAIAN SELESAI DALAM BEBERAPA DETIK",
         "lead": "KIPAS DEPAN", "pt": (300, 1050)},
    ],
    "02_psu": [
        {"tag": "TOMBOL → MOTHERBOARD", "info": "BUKAN SAKELAR LISTRIK LANGSUNG",
         "lead": "PANEL DEPAN", "pt": (300, 800)},
        {"tag": "AC 220V → DC", "info": "12V · 5V · 3,3V UNTUK CHIP",
         "lead": "KAPASITOR", "pt": (520, 930)},
        {"tag": "POWER GOOD", "info": "TEGANGAN STABIL, BARU BOLEH LANJUT",
         "lead": "KABEL ATX", "pt": (820, 1050)},
    ],
    "03_cpu": [
        {"tag": "RESET → CPU AKTIF", "info": "BELUM PUNYA INGATAN SAMA SEKALI",
         "lead": "SOKET LGA", "pt": (520, 900)},
        {"tag": "INSTRUKSI PERTAMA", "info": "DIAMBIL DARI CHIP BIOS",
         "lead": "CHIP BIOS", "pt": (800, 1000)},
        {"tag": "PETA JALAN SISTEM", "info": "ADA SEBELUM SISTEM OPERASI",
         "lead": "PAD KONTAK", "pt": (420, 1080)},
    ],
    "04_post": [
        {"tag": "POST DIMULAI", "info": "RAM · GPU · SSD · KEYBOARD",
         "lead": "SLOT RAM", "pt": (700, 900)},
        {"tag": "KALAU ADA YANG GAGAL", "info": "BIP ATAU LAMPU INDIKATOR",
         "lead": "LED DEBUG", "pt": (860, 1050)},
        {"tag": "SEMUA LOLOS", "info": "LOGO MOTHERBOARD MUNCUL",
         "lead": "HEATSINK", "pt": (400, 800)},
    ],
    "05_ram": [
        {"tag": "CARI SISTEM OPERASI", "info": "BIOS MEMINDAI SSD",
         "lead": "SSD M.2", "pt": (300, 950)},
        {"tag": "SALIN KE RAM", "info": "SSD LAMBAT, RAM JAUH LEBIH CEPAT",
         "lead": "CHIP MEMORI", "pt": (700, 900)},
        {"tag": "RAM ITU PELUPA", "info": "LISTRIK MATI, ISINYA HILANG",
         "lead": "MODUL DDR", "pt": (760, 1060)},
    ],
    "06_gpu": [
        {"tag": "DATA → PIKSEL", "info": "GPU MENERJEMAHKAN DATA MENJADI GAMBAR",
         "lead": "KARTU GRAFIS", "pt": (500, 1050)},
        {"tag": "TAMPILAN UTAMA", "info": "JUTAAN PIKSEL DIKIRIM KE MONITOR",
         "lead": "MONITOR", "pt": (540, 700)},
        {"tag": "RANGKAIAN SELESAI", "info": "SEMUANYA HANYA BEBERAPA DETIK",
         "lead": "DESKTOP", "pt": (540, 820)},
    ],
    "07_outro": [
        {"tag": "TOMBOL POWER LAGI", "info": "URUTAN INI TERULANG DARI NOL",
         "lead": "KIPAS DEPAN", "pt": (300, 1000)},
        {"tag": "SETIAP KALI DINYALAKAN", "info": "DAYA · CPU · POST · RAM · GPU",
         "lead": "PANEL SAMPING", "pt": (760, 900)},
        {"tag": "KLIKTAHU", "info": "PAHAMI HAL YANG KAMU PAKAI TIAP HARI",
         "lead": "TOMBOL POWER", "pt": (520, 760)},
    ],
}


def words_of(text):
    return [w for w in re.sub(r"[^\w\s]", " ", text).split() if w]

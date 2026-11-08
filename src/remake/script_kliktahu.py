#!/usr/bin/env python3
"""Naskah asli KlikTahu — Ep. "Tombol Power" (BUKAN salinan referensi).

Ditulis ulang dari nol: kalimat baru, urutan baru, istilah lebih presisi
(220 V AC -> 12/5/3,3 V DC, sinyal POWER GOOD, POST, RAM volatil), ditambah
identitas merek KlikTahu dan CTA. Struktur 7 bab tetap terinspirasi format
edukasi vertikal, tanpa menyalin satu kalimat pun dari video referensi.

Semua timing dihitung dari durasi VO hasil TTS, jadi naskah ini adalah satu
sumber kebenaran untuk audio, subtitle per-kata, dan timeline visual.
"""

from __future__ import annotations

W, H = 1080, 1920
FPS = 60

BRAND = "KlikTahu!"
TAGLINE = "Tahu hal yang kamu pakai tiap hari"
WATERMARK = "KlikTahu!"

# Palet (lebih kaya dari referensi, tetap biru-dongker khas sains-tech)
COLORS = {
    "bg_top": (9, 16, 38),
    "bg_bottom": (16, 33, 66),
    "panel": (24, 42, 76),
    "panel_light": (38, 63, 105),
    "steel": (86, 107, 138),
    "ink": (11, 18, 36),
    "white": (245, 249, 255),
    "muted": (150, 170, 200),
    "yellow": (255, 199, 32),
    "amber": (255, 158, 46),
    "cyan": (62, 214, 255),
    "green": (46, 214, 145),
    "red": (255, 92, 92),
    "blue": (56, 116, 255),
}

STEPS = ["MOTHERBOARD", "PSU", "CPU", "RAM", "GPU", "STORAGE"]

SEGMENTS = [
    {
        "id": "01_hook",
        "scene": "case",
        "step": 0,
        "title": ("Pencet power,", "apa yang terjadi?"),
        "eyebrow": "KLIKTAHU!  /  EP. 01",
        "accent": "cyan",
        "camera": "push",
        "sfx": ["power_click", "fan_spin", "whoosh"],
        "narration": (
            "Tombol power kamu pencet. Kipas berputar, lampu menyala, "
            "tapi layar masih gelap. Rusak? Belum tentu. Di balik panel itu, "
            "enam komponen bekerja berurutan, dan urutannya tidak boleh tertukar. "
            "KlikTahu akan membuktikannya, detik per detik."
        ),
    },
    {
        "id": "02_psu",
        "scene": "psu",
        "step": 1,
        "title": ("Listrik masuk:", "motherboard & PSU"),
        "eyebrow": "TAHAP 01  /  DAYA",
        "accent": "yellow",
        "camera": "pan_right",
        "sfx": ["relay", "hum", "power_good", "whoosh"],
        "narration": (
            "Tombol itu tidak menyalakan PSU secara langsung. Ia hanya mengirim "
            "sinyal ke motherboard. Motherboard lalu memerintahkan PSU mengubah "
            "listrik dua ratus dua puluh volt AC menjadi dua belas, lima, dan tiga "
            "koma tiga volt DC. Setelah tegangan stabil, PSU memberi sinyal bahwa daya sudah siap. "
            "Baru semuanya boleh lanjut."
        ),
    },
    {
        "id": "03_cpu",
        "scene": "cpu",
        "step": 2,
        "title": ("CPU bangun,", "BIOS dibaca"),
        "eyebrow": "TAHAP 02  /  INSTRUKSI PERTAMA",
        "accent": "cyan",
        "camera": "push",
        "sfx": ["cpu_wake", "data_blips", "whoosh"],
        "narration": (
            "Sinyal itu membangunkan CPU. Tapi CPU yang baru hidup tidak punya "
            "ingatan: ia belum tahu harus mengerjakan apa. Karena itu, instruksi "
            "pertamanya diambil dari chip BIOS di motherboard. BIOS adalah peta jalan "
            "sebelum sistem operasi apa pun sempat ada."
        ),
    },
    {
        "id": "04_post",
        "scene": "post",
        "step": 3,
        "title": ("POST:", "cek semua komponen"),
        "eyebrow": "TAHAP 03  /  POWER-ON SELF TEST",
        "accent": "green",
        "camera": "pan_left",
        "sfx": ["post_beep", "error_hint", "post_ok", "whoosh"],
        "narration": (
            "BIOS menjalankan POST, pemeriksaan mandiri saat komputer menyala. "
            "RAM, kartu grafis, penyimpanan, dan papan ketik dicek dalam sepersekian detik. "
            "Kalau ada yang gagal, kamu diberi tahu lewat bunyi bip atau lampu indikator. "
            "Kalau semuanya lolos, logo motherboard akhirnya muncul di layar."
        ),
    },
    {
        "id": "05_ram",
        "scene": "ram",
        "step": 4,
        "title": ("Storage ke RAM:", "Windows dimuat"),
        "eyebrow": "TAHAP 04  /  PINDAH DATA",
        "accent": "blue",
        "camera": "pan_right",
        "sfx": ["data_stream", "loading", "whoosh"],
        "narration": (
            "Berikutnya, BIOS mencari sistem operasi di penyimpanan, misalnya SSD. "
            "SSD menyimpan data secara permanen, tapi terlalu lambat untuk dikerjakan "
            "CPU. Jadi Windows disalin ke RAM yang jauh lebih cepat. RAM itu pelupa: "
            "begitu listrik mati, isinya hilang. Itulah sebabnya proses pemuatan selalu diulang."
        ),
    },
    {
        "id": "06_gpu",
        "scene": "gpu",
        "step": 5,
        "title": ("GPU:", "data jadi gambar"),
        "eyebrow": "TAHAP 05  /  PIKSEL PERTAMA",
        "accent": "amber",
        "camera": "pull",
        "sfx": ["pixel_reveal", "chime", "whoosh"],
        "narration": (
            "Lingkaran yang berputar itu bukan sekadar hiasan. Itu tanda penyalinan "
            "masih berjalan. Setelah selesai, GPU mengubah data menjadi jutaan piksel, "
            "dan tampilan utama muncul. Seluruh rangkaian tadi selesai hanya dalam "
            "beberapa detik."
        ),
    },
    {
        "id": "07_outro",
        "scene": "loop",
        "step": 6,
        "title": ("Tiap kali dinyalakan,", "semua terulang"),
        "eyebrow": "KLIKTAHU!  /  PENUTUP",
        "accent": "yellow",
        "camera": "pull",
        "sfx": ["outro_pad", "power_click"],
        "narration": (
            "Dan setiap kali kamu menekan tombol power, semua urutan ini terulang "
            "dari nol. Simpan video ini, lalu ikuti KlikTahu, supaya hal yang kamu "
            "pakai tiap hari jadi masuk akal."
        ),
    },
]

INTRO_S = 2.2          # kartu logo KlikTahu
LEAD_IN_S = 0.7        # jeda sebelum VO tiap bab
TAIL_S = 0.9           # jeda setelah VO tiap bab
OUTRO_S = 3.2          # kartu CTA
MIN_SEGMENT_S = 10.0
VO_ATEMPO = 1.18       # sedikit dipercepat supaya pacing tetap padat (natural)


def words_of(text: str) -> list[str]:
    import re
    return [w for w in re.sub(r"[^\w\s]", " ", text).split() if w]


if __name__ == "__main__":
    total = sum(len(words_of(s["narration"])) for s in SEGMENTS)
    chars = sum(len(s["narration"]) for s in SEGMENTS)
    print(f"{len(SEGMENTS)} bab, {total} kata, {chars} karakter naskah asli.")

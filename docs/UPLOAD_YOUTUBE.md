# Arsip — Panduan unggah salinan identik (BUKAN video utama)

> **Dokumen ini untuk arsip.** Putaran pertama saya keliru mengartikan
> "100% identik" sebagai salinan byte-for-byte. Setelah klarifikasi, video utama
> adalah **KlikTahu buatan sendiri** di
> [`output/KlikTahu_TombolPower_REMAKE_1080x1920_60fps.mp4`](../output/KlikTahu_TombolPower_REMAKE_1080x1920_60fps.mp4);
> spesifikasi dan metadata Upload-nya ada di [`REMAKE.md`](REMAKE.md) dan
> [`../output/KlikTahu_REMAKE_metadata.json`](../output/KlikTahu_REMAKE_metadata.json).
> Berkas salinan di bawah **hanya arsip pembanding**, jangan diunggah.

## Berkas arsip

| Kebutuhan | Berkas |
|---|---|
| Salinan persis | `reference/KlikTahu_TombolPower_SHORT_FINAL.mp4` |
| Remux faststart | `reference/KlikTahu_TombolPower_YouTube_Upload.mp4` |
| Cover asli MP4 | `reference/thumbnail_source.jpg` |
| Metadata lama | `reference/metadata.json` |
| Bukti hash lama | `reference/VERIFIKASI.json`, `reference/MANIFEST.sha256` |
| Papan cerita referensi | `reference/storyboard.jpg` |

Salinan yang sama juga sempat dikirim ke Google Drive Anda:
[FINAL identik](https://drive.google.com/file/d/1AdMLhnmtZcrUEc6YsuOzZceo_3ViT6Aj/view?usp=drivesdk) ·
[versi faststart](https://drive.google.com/file/d/1NbRmitQsfvdiNEjJ7cVzXtkeg5X-h0GS/view?usp=drivesdk) ·
[metadata lama](https://drive.google.com/file/d/16cCRQ6ou1AubJG8SG3PlttKFqkTwbFUS/view?usp=drivesdk).

## Catatan hak (tetap berlaku untuk arsip)

Salinan ini memuat narasi, musik, dan watermark halus `elevenbyte` dari berkas
sumber. Mengunggah ulang konten pihak ketiga tanpa izin dapat terkena kebijakan
*reused content* / klaim Content ID. Karena itu video utama project ini sengaja
dibuat ulang sepenuhnya dengan naskah, VO, visual, dan efek suara orisinal.

## Verifikasi ulang arsip

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
python src/build_short.py --out reference
python src/verify_identical.py --final reference/KlikTahu_TombolPower_SHORT_FINAL.mp4 \
       --upload reference/KlikTahu_TombolPower_YouTube_Upload.mp4 \
       --out reference/VERIFIKASI.json
```

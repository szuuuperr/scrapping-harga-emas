# PantauEmas: Proyek Pekan ke-12 Scripting Language

Proyek end-to-end pemantau harga emas harian yang merangkai materi P11–P16:

```
harga-emas.org ──► scraper.py ──► data/emas.db ──► analisis.py ──► laporan.py ──► output/*.xlsx, *.pdf
   (sumber)         (P11–P12)      (SQLite, P12)    (Pandas +        (Excel + PDF,
                                                      Matplotlib, P14)  P15)
                                          │
                                          ├──► bot.py  (bot Telegram, P16)
                                          └──► app.py  (dashboard Streamlit, P16)
```

`main.py` menjalankan seluruh pipeline dan bisa dijadwalkan setiap hari.

## Sumber data dan izin

- Sumber: [harga-emas.org](https://harga-emas.org), situs informasi harga emas Indonesia.
- robots.txt: diperiksa otomatis oleh `scraper.py` sebelum scraping dimulai.
- Etika: jeda 1 detik antar-request, User-Agent jujur, retry dengan backoff, tidak ada data pribadi.
- Data: harga emas Antam per denominasi (0.5g–1000g), harga buyback, harga emas dunia.
  Kolom: `tanggal, berat_gram, harga_jual, harga_per_gram, harga_buyback, harga_dunia_usd_oz, kurs_usd_idr, pertama_dilihat, terakhir_dilihat`.

## Struktur folder

| File | Lapisan | Isi |
| --- | --- | --- |
| `config.py` | - | Pengaturan dan pembacaan `.env` |
| `scraper.py` | Pengambilan | `EmasScraper`: tabel harga, buyback, Session, retry, logging |
| `db.py` | Penyimpanan | Tabel `emas` (tanpa duplikat) dan `riwayat_harga` (pemantauan) |
| `analisis.py` | Analisis | Pembersihan, 3 pertanyaan, 3 grafik PNG, kalimat temuan |
| `laporan.py` | Laporan | Excel berformat (openpyxl) dan PDF (reportlab) |
| `main.py` | Orkestrasi | Pipeline, argumen baris perintah, penjadwalan, log ke `logs/` |
| `pesan.py` | Bot | Teks balasan bot (fungsi murni, mudah diuji) |
| `bot.py` | Penyajian | Bot Telegram dengan 8 perintah dan laporan harian |
| `app.py` | Penyajian | Dashboard Streamlit: filter, 4 metrik, grafik, tabel, unduh CSV |
| `tests/` | - | 13+ tes pytest yang berjalan tanpa internet |

## Cara menjalankan

1. Buat virtual environment dan pasang pustaka:

   | Windows (PowerShell) | macOS / Linux |
   | --- | --- |
   | `python -m venv venv` | `python3 -m venv venv` |
   | `venv\Scripts\activate` | `source venv/bin/activate` |
   | `pip install -r requirements.txt` | `pip install -r requirements.txt` |

2. Salin `.env.example` menjadi `.env`, lalu isi `BOT_TOKEN` dari @BotFather (hanya untuk bot).
3. Uji: `python -m pytest -v` → harus semua `passed`.
4. Jalankan pipeline:

   ```
   python main.py                     # scrape 7 hari terakhir (default, sekitar 10 detik)
   python main.py --maks-hari 3       # uji cepat, 3 hari terakhir
   python main.py --semua-hari        # scrape semua tanggal yang tersedia di kalender
   python main.py --tanpa-scrape      # buat ulang grafik dan laporan dari database
   python main.py --jadwal            # jalan setiap hari pukul 07:00 (biarkan terminal terbuka)
   ```

   Hasil: `data/emas.db`, `output/grafik_*.png`, `output/laporan_YYYY-MM-DD.xlsx` dan `.pdf`, serta `logs/pipeline.log`.

5. Jalankan bot: `python bot.py`, lalu kirim `/start` ke bot di Telegram.
6. Jalankan dashboard: `streamlit run app.py`, buka http://localhost:8501.

Bot dan dashboard membaca database yang sama, jadi jalankan `main.py` minimal sekali terlebih dahulu.

## Perintah bot

| Perintah | Fungsi |
| --- | --- |
| `/ringkas` | Ringkasan harga emas dan 3 temuan |
| `/harga <berat>` | Riwayat harga denominasi tertentu (misal: `/harga 5`) |
| `/tren` | Grafik tren harga 1 gram |
| `/spread` | Grafik spread per denominasi |
| `/grafik` | Kirim semua grafik analisis |
| `/berubah` | Denominasi yang harganya berubah |
| `/langganan`, `/berhenti` | Mulai atau hentikan laporan harian pukul 07:00 WIB |

## Pertanyaan analisis

1. Bagaimana tren harga emas 1 gram dalam beberapa hari terakhir?
2. Berapa spread (selisih jual–buyback) rata-rata per denominasi?
3. Denominasi mana yang harga per gramnya paling efisien (termurah)?

Kalimat temuan dibuat otomatis oleh `analisis.temuan()` dan muncul di log, PDF, dan bot.

## Pembagian peran (contoh)

| Anggota | Bagian |
| --- | --- |
| Anggota 1 | `scraper.py`, `db.py` |
| Anggota 2 | `analisis.py`, `laporan.py` |
| Anggota 3 | `bot.py`, `pesan.py` |
| Anggota 4 | `app.py`, `main.py`, README, tes |

## Penggunaan AI

Contoh pernyataan: "Kerangka kode dibuat dengan bantuan asisten AI, lalu diuji dan disesuaikan oleh anggota kelompok." Tuliskan bagian mana saja yang dibantu.

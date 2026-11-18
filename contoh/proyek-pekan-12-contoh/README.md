# PantauBuku: Contoh Proyek Pekan ke-12 Scripting Language

Contoh Proyek Pekan ke-12, sebuah proyek end-to-end yang merangkai materi P11–P16:

```
books.toscrape.com ──► scraper.py ──► data/buku.db ──► analisis.py ──► laporan.py ──► output/*.xlsx, *.pdf
   (sumber)            (P11–P12)       (SQLite, P12)    (Pandas +        (Excel + PDF,
                                                         Matplotlib, P14)  P15)
                                              │
                                              ├──► bot.py  (bot Telegram, P16)
                                              └──► app.py  (dashboard Streamlit, P16)
```

`main.py` menjalankan seluruh pipeline dan bisa dijadwalkan setiap hari.

## Sumber data dan izin

- Sumber: [books.toscrape.com](https://books.toscrape.com), situs latihan yang memang dibuat untuk dipakai belajar scraping.
- robots.txt: diperiksa otomatis oleh `scraper.py` sebelum scraping dimulai.
- Etika: jeda 1 detik antar-request, User-Agent jujur, retry dengan backoff, tidak ada data pribadi.
- Data: sekitar 1000 buku dari 50 kategori, kolom `url, judul, kategori, harga, rating, tersedia, pertama_dilihat, terakhir_dilihat`.

## Struktur folder

| File | Lapisan | Isi |
| --- | --- | --- |
| `config.py` | - | Pengaturan dan pembacaan `.env` |
| `scraper.py` | Pengambilan | `BookScraper`: kategori + pagination, Session, retry, logging |
| `db.py` | Penyimpanan | Tabel `buku` (tanpa duplikat) dan `riwayat_harga` (pemantauan) |
| `analisis.py` | Analisis | Pembersihan, 3 pertanyaan, 3 grafik PNG, kalimat temuan |
| `laporan.py` | Laporan | Excel berformat (openpyxl) dan PDF (reportlab) |
| `main.py` | Orkestrasi | Pipeline, argumen baris perintah, penjadwalan, log ke `logs/` |
| `pesan.py` | Bot | Teks balasan bot (fungsi murni, mudah diuji) |
| `bot.py` | Penyajian | Bot Telegram dengan 8 perintah dan laporan harian |
| `app.py` | Penyajian | Dashboard Streamlit: 5 filter, 4 metrik, grafik, tabel, unduh CSV |
| `tests/` | - | 13 tes pytest yang berjalan tanpa internet |

## Cara menjalankan

1. Buat virtual environment dan pasang pustaka:

   | Windows (PowerShell) | macOS / Linux |
   | --- | --- |
   | `python -m venv venv` | `python3 -m venv venv` |
   | `venv\Scripts\activate` | `source venv/bin/activate` |
   | `pip install -r requirements.txt` | `pip install -r requirements.txt` |

2. Salin `.env.example` menjadi `.env`, lalu isi `BOT_TOKEN` dari @BotFather (hanya untuk bot).
3. Uji: `python -m pytest -v` → harus `13 passed`.
4. Jalankan pipeline:

   ```
   python main.py --maks-kategori 3   # uji cepat, sekitar 15 detik
   python main.py                     # semua kategori, sekitar 1–2 menit
   python main.py --tanpa-scrape      # buat ulang grafik dan laporan dari database
   python main.py --jadwal            # jalan setiap hari pukul 07:00 (biarkan terminal terbuka)
   ```

   Hasil: `data/buku.db`, `output/grafik_*.png`, `output/laporan_YYYY-MM-DD.xlsx` dan `.pdf`, serta `logs/pipeline.log`.

5. Jalankan bot: `python bot.py`, lalu kirim `/start` ke bot di Telegram.
6. Jalankan dashboard: `streamlit run app.py`, buka http://localhost:8501.

Bot dan dashboard membaca database yang sama, jadi jalankan `main.py` minimal sekali terlebih dahulu.

## Perintah bot

| Perintah | Fungsi |
| --- | --- |
| `/ringkas` | Ringkasan katalog dan 3 temuan |
| `/cari <kata>` | 5 buku termurah yang judulnya mengandung kata tersebut |
| `/kategori <nama>` | 5 buku termurah di satu kategori |
| `/grafik` | Mengirim 3 grafik analisis |
| `/berubah` | Buku yang harganya berubah sejak scrape sebelumnya |
| `/langganan`, `/berhenti` | Mulai atau hentikan laporan harian pukul 07:00 WIB |

## Pertanyaan analisis

1. Kategori apa yang paling banyak bukunya?
2. Apakah buku dengan rating lebih tinggi lebih mahal?
3. Kategori apa yang rata-rata harganya paling mahal (minimal 5 buku)?

Kalimat temuan dibuat otomatis oleh `analisis.temuan()` dan muncul di log, PDF, dan bot.

Catatan: harga di books.toscrape.com tidak pernah berubah, jadi fitur pemantauan harga (`/berubah`, tab "Perubahan harga") baru menunjukkan hasil pada sumber data yang harganya bergerak. Untuk mencobanya, ubah satu harga di tabel `buku` lewat DB Browser for SQLite, lalu jalankan `main.py` lagi.

## Ide pengembangan untuk proyek kalian

- Ganti sumber data dengan topik kelompok sendiri. Biasanya cukup mengubah `scraper.py` dan nama kolom di `db.py`.
- Tambah kolom dari halaman detail (stok, UPC, deskripsi) seperti di P12.
- Kirim laporan PDF lewat email (P15) atau lewat bot dengan `reply_document`.
- Deploy dashboard ke Streamlit Community Cloud.

## Pembagian peran (contoh)

| Anggota | Bagian |
| --- | --- |
| Anggota 1 | `scraper.py`, `db.py` |
| Anggota 2 | `analisis.py`, `laporan.py` |
| Anggota 3 | `bot.py`, `pesan.py` |
| Anggota 4 | `app.py`, `main.py`, README, tes |

## Penggunaan AI

Contoh pernyataan: "Kerangka kode dibuat dengan bantuan asisten AI, lalu diuji dan disesuaikan oleh anggota kelompok." Tuliskan bagian mana saja yang dibantu.

"""
Titik masuk pipeline: scraping -> SQLite -> analisis -> grafik -> laporan.

Contoh:
  python main.py                    # jalankan sekali, semua kategori (sekitar 1-2 menit)
  python main.py --maks-kategori 3  # uji cepat, 3 kategori saja
  python main.py --tanpa-scrape     # pakai data yang sudah ada di database
  python main.py --jadwal           # jalan setiap hari pukul JAM_JADWAL (P15)
"""
import argparse
import logging
import time

import schedule

import analisis
import config
import db
import laporan
from scraper import BookScraper

config.LOG_DIR.mkdir(exist_ok=True)
config.DATA_DIR.mkdir(exist_ok=True)
config.OUTPUT_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_DIR / "pipeline.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("pipeline")


def jalankan_pipeline(maks_kategori=None, tanpa_scrape=False):
    log.info("Pipeline mulai")
    mulai = time.time()
    try:
        if not tanpa_scrape:
            data = BookScraper().jalankan(maks_kategori)
            baru = db.simpan(data)
            log.info("Tersimpan %d buku (%d baru)", len(data), baru)

        df = analisis.bersihkan(db.baca_buku())
        if df.empty:
            log.error("Database kosong. Jalankan tanpa --tanpa-scrape dulu.")
            return None
        grafik = analisis.buat_grafik(df)
        xlsx = laporan.buat_excel(df, grafik)
        pdf = laporan.buat_pdf(df, grafik)
        for t in analisis.temuan(df):
            log.info("Temuan: %s", t)

        berubah = db.perubahan_harga()
        if not berubah.empty:
            log.info("%d buku berubah harga sejak scrape sebelumnya", len(berubah))
        log.info("Pipeline selesai dalam %.0f detik: %s, %s",
                 time.time() - mulai, xlsx.name, pdf.name)
        return xlsx, pdf
    except Exception:
        log.exception("Pipeline gagal")  # simpan traceback lengkap di log
        return None


def main():
    p = argparse.ArgumentParser(description="Pipeline pemantau katalog buku")
    p.add_argument("--maks-kategori", type=int, help="batasi jumlah kategori (uji cepat)")
    p.add_argument("--tanpa-scrape", action="store_true", help="lewati scraping")
    p.add_argument("--jadwal", action="store_true", help="jalankan setiap hari")
    a = p.parse_args()

    if a.jadwal:
        schedule.every().day.at(config.JAM_JADWAL).do(jalankan_pipeline, a.maks_kategori)
        log.info("Terjadwal setiap hari pukul %s. Ctrl+C untuk berhenti.", config.JAM_JADWAL)
        while True:
            schedule.run_pending()
            time.sleep(30)
    else:
        jalankan_pipeline(a.maks_kategori, a.tanpa_scrape)


if __name__ == "__main__":
    main()

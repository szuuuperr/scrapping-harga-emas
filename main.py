"""
Titik masuk pipeline: scraping -> SQLite -> analisis -> grafik -> laporan.

Contoh:
  python main.py                    # jalankan riwayat 7 hari terakhir (sekitar 7 detik)
  python main.py --maks-hari 3      # uji cepat, 3 hari terakhir
  python main.py --semua-hari       # ambil seluruh riwayat yang tersedia di kalender
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
from scraper import EmasScraper

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


def jalankan_pipeline(maks_hari=7, tanpa_scrape=False):
    log.info("Pipeline mulai (maks_hari=%s)", maks_hari)
    mulai = time.time()
    try:
        if not tanpa_scrape:
            data = EmasScraper().jalankan(maks_hari=maks_hari)
            baru = db.simpan(data)
            log.info("Tersimpan %d record (%d baru)", len(data), baru)

        df = analisis.bersihkan(db.baca_emas())
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
            log.info("%d denominasi berubah harga sejak scrape sebelumnya", len(berubah))
        log.info("Pipeline selesai dalam %.0f detik: %s, %s",
                 time.time() - mulai, xlsx.name, pdf.name)
        return xlsx, pdf
    except Exception:
        log.exception("Pipeline gagal")  # simpan traceback lengkap di log
        return None


def main():
    p = argparse.ArgumentParser(description="Pipeline pemantau harga emas")
    p.add_argument("--maks-hari", type=int, default=7,
                   help="jumlah hari riwayat yang diambil (default 7)")
    p.add_argument("--semua-hari", action="store_true",
                   help="ambil seluruh riwayat tanggal yang tersedia")
    p.add_argument("--tanpa-scrape", action="store_true", help="lewati scraping")
    p.add_argument("--jadwal", action="store_true", help="jalankan setiap hari")
    a = p.parse_args()

    maks = None if a.semua_hari else a.maks_hari

    if a.jadwal:
        schedule.every().day.at(config.JAM_JADWAL).do(jalankan_pipeline, 1)
        log.info("Terjadwal setiap hari pukul %s. Ctrl+C untuk berhenti.", config.JAM_JADWAL)
        while True:
            schedule.run_pending()
            time.sleep(30)
    else:
        jalankan_pipeline(maks, a.tanpa_scrape)


if __name__ == "__main__":
    main()

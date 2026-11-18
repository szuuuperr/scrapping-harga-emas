"""
Lapisan 2: PENYIMPANAN (P12).

Dua tabel:
- emas          : satu baris per denominasi per tanggal (PRIMARY KEY: tanggal + berat_gram).
- riwayat_harga : satu baris per denominasi per kali scrape, untuk memantau perubahan.

Menjalankan pipeline berulang kali TIDAK membuat duplikat di tabel emas.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime

import pandas as pd

import config


@contextmanager
def koneksi(path=config.DB_PATH):
    """Buka database, commit jika sukses (rollback jika error), lalu tutup."""
    con = sqlite3.connect(path)
    try:
        with con:
            yield con
    finally:
        con.close()


def siapkan(path=config.DB_PATH):
    """Buat tabel jika belum ada."""
    with koneksi(path) as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS emas (
                tanggal          TEXT,
                berat_gram       REAL,
                harga_jual       REAL,
                harga_per_gram   REAL,
                harga_buyback    REAL,
                harga_dunia_usd_oz REAL,
                kurs_usd_idr     REAL,
                pertama_dilihat  TEXT,
                terakhir_dilihat TEXT,
                PRIMARY KEY (tanggal, berat_gram)
            );
            CREATE TABLE IF NOT EXISTS riwayat_harga (
                tanggal      TEXT,
                berat_gram   REAL,
                waktu_scrape TEXT,
                harga_jual   REAL,
                harga_buyback REAL,
                PRIMARY KEY (tanggal, berat_gram, waktu_scrape)
            );
            """
        )


def simpan(data, waktu=None, path=config.DB_PATH):
    """Simpan list dict hasil scraper. Kembalikan jumlah record baru."""
    waktu = waktu or datetime.now().isoformat(timespec="seconds")
    siapkan(path)
    with koneksi(path) as con:
        sebelum = con.execute("SELECT COUNT(*) FROM emas").fetchone()[0]
        con.executemany(
            """INSERT INTO emas (tanggal, berat_gram, harga_jual, harga_per_gram,
                                 harga_buyback, harga_dunia_usd_oz, kurs_usd_idr,
                                 pertama_dilihat, terakhir_dilihat)
               VALUES (:tanggal, :berat_gram, :harga_jual, :harga_per_gram,
                        :harga_buyback, :harga_dunia_usd_oz, :kurs_usd_idr,
                        :waktu, :waktu)
               ON CONFLICT(tanggal, berat_gram) DO UPDATE SET
                   harga_jual = excluded.harga_jual,
                   harga_per_gram = excluded.harga_per_gram,
                   harga_buyback = excluded.harga_buyback,
                   harga_dunia_usd_oz = excluded.harga_dunia_usd_oz,
                   kurs_usd_idr = excluded.kurs_usd_idr,
                   terakhir_dilihat = excluded.terakhir_dilihat""",
            [{**e, "waktu": waktu} for e in data],
        )
        con.executemany(
            """INSERT OR IGNORE INTO riwayat_harga
               (tanggal, berat_gram, waktu_scrape, harga_jual, harga_buyback)
               VALUES (?, ?, ?, ?, ?)""",
            [(e["tanggal"], e["berat_gram"], waktu,
              e["harga_jual"], e.get("harga_buyback")) for e in data],
        )
        sesudah = con.execute("SELECT COUNT(*) FROM emas").fetchone()[0]
    return sesudah - sebelum


def baca_emas(path=config.DB_PATH):
    """Seluruh tabel emas sebagai DataFrame (dipakai analisis, bot, dashboard)."""
    siapkan(path)
    with koneksi(path) as con:
        return pd.read_sql("SELECT * FROM emas ORDER BY tanggal DESC, berat_gram", con)


def cari(berat, batas=5, path=config.DB_PATH):
    """Cari harga emas berdasarkan berat. Parameter ? mencegah SQL injection."""
    with koneksi(path) as con:
        return pd.read_sql(
            "SELECT tanggal, berat_gram, harga_jual, harga_per_gram, harga_buyback "
            "FROM emas WHERE berat_gram = ? ORDER BY tanggal DESC LIMIT ?",
            con, params=[berat, batas],
        )


def harga_terakhir(berat=1.0, path=config.DB_PATH):
    """Harga terakhir untuk denominasi tertentu."""
    with koneksi(path) as con:
        return pd.read_sql(
            "SELECT * FROM emas WHERE berat_gram = ? ORDER BY tanggal DESC LIMIT 1",
            con, params=[berat],
        )


def perubahan_harga(path=config.DB_PATH):
    """Denominasi yang harganya berbeda antara dua tanggal terakhir."""
    siapkan(path)
    with koneksi(path) as con:
        return pd.read_sql(
            """
            WITH urut AS (
                SELECT tanggal, berat_gram, harga_jual,
                       ROW_NUMBER() OVER (PARTITION BY berat_gram ORDER BY tanggal DESC) AS ke
                FROM emas
            )
            SELECT baru.berat_gram,
                   lama.harga_jual AS harga_lama,
                   baru.harga_jual AS harga_baru,
                   ROUND(baru.harga_jual - lama.harga_jual, 0) AS selisih,
                   lama.tanggal AS tanggal_lama,
                   baru.tanggal AS tanggal_baru
            FROM urut baru
            JOIN urut lama ON lama.berat_gram = baru.berat_gram AND lama.ke = 2
            WHERE baru.ke = 1 AND baru.harga_jual <> lama.harga_jual
            ORDER BY baru.berat_gram
            """,
            con,
        )


def riwayat(path=config.DB_PATH):
    """Seluruh riwayat harga (untuk grafik tren di dashboard)."""
    siapkan(path)
    with koneksi(path) as con:
        return pd.read_sql(
            "SELECT * FROM emas ORDER BY tanggal, berat_gram",
            con,
        )

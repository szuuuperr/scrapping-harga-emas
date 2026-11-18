"""
Lapisan 2: PENYIMPANAN (P12).

Dua tabel:
- buku          : satu baris per buku (url sebagai PRIMARY KEY), kondisi terakhir.
- riwayat_harga : satu baris per buku per kali scrape, untuk memantau perubahan.

Menjalankan pipeline berulang kali TIDAK membuat duplikat di tabel buku.
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
            CREATE TABLE IF NOT EXISTS buku (
                url              TEXT PRIMARY KEY,
                judul            TEXT NOT NULL,
                kategori         TEXT,
                harga            REAL,
                rating           INTEGER,
                tersedia         INTEGER,     -- 1 = In stock, 0 = habis
                pertama_dilihat  TEXT,        -- waktu scrape pertama
                terakhir_dilihat TEXT         -- waktu scrape terakhir
            );
            CREATE TABLE IF NOT EXISTS riwayat_harga (
                url          TEXT,
                waktu_scrape TEXT,
                harga        REAL,
                tersedia     INTEGER,
                PRIMARY KEY (url, waktu_scrape)
            );
            """
        )


def simpan(data, waktu=None, path=config.DB_PATH):
    """Simpan list dict hasil scraper. Kembalikan jumlah buku baru."""
    waktu = waktu or datetime.now().isoformat(timespec="seconds")
    siapkan(path)
    with koneksi(path) as con:
        sebelum = con.execute("SELECT COUNT(*) FROM buku").fetchone()[0]
        con.executemany(
            """INSERT INTO buku (url, judul, kategori, harga, rating, tersedia,
                                 pertama_dilihat, terakhir_dilihat)
               VALUES (:url, :judul, :kategori, :harga, :rating, :tersedia, :waktu, :waktu)
               ON CONFLICT(url) DO UPDATE SET
                   judul = excluded.judul,
                   kategori = excluded.kategori,
                   harga = excluded.harga,
                   rating = excluded.rating,
                   tersedia = excluded.tersedia,
                   terakhir_dilihat = excluded.terakhir_dilihat""",
            [{**b, "tersedia": int(b["tersedia"]), "waktu": waktu} for b in data],
        )
        con.executemany(
            """INSERT OR IGNORE INTO riwayat_harga (url, waktu_scrape, harga, tersedia)
               VALUES (?, ?, ?, ?)""",
            [(b["url"], waktu, b["harga"], int(b["tersedia"])) for b in data],
        )
        sesudah = con.execute("SELECT COUNT(*) FROM buku").fetchone()[0]
    return sesudah - sebelum


def baca_buku(path=config.DB_PATH):
    """Seluruh tabel buku sebagai DataFrame (dipakai analisis, bot, dashboard)."""
    siapkan(path)
    with koneksi(path) as con:
        return pd.read_sql("SELECT * FROM buku", con)


def cari(kata, batas=5, path=config.DB_PATH):
    """Cari buku berdasarkan judul. Parameter ? mencegah SQL injection."""
    with koneksi(path) as con:
        return pd.read_sql(
            "SELECT judul, kategori, harga, rating FROM buku "
            "WHERE judul LIKE ? ORDER BY harga LIMIT ?",
            con, params=[f"%{kata}%", batas],
        )


def perubahan_harga(path=config.DB_PATH):
    """Buku yang harganya berbeda antara dua scrape terakhir."""
    siapkan(path)
    with koneksi(path) as con:
        return pd.read_sql(
            """
            WITH urut AS (
                SELECT url, waktu_scrape, harga,
                       ROW_NUMBER() OVER (PARTITION BY url ORDER BY waktu_scrape DESC) AS ke
                FROM riwayat_harga
            )
            SELECT b.judul, b.kategori, lama.harga AS harga_lama, baru.harga AS harga_baru,
                   ROUND(baru.harga - lama.harga, 2) AS selisih
            FROM urut baru
            JOIN urut lama ON lama.url = baru.url AND lama.ke = 2
            JOIN buku b ON b.url = baru.url
            WHERE baru.ke = 1 AND baru.harga <> lama.harga
            ORDER BY selisih
            """,
            con,
        )


def riwayat(path=config.DB_PATH):
    """Seluruh riwayat harga (untuk grafik tren di dashboard)."""
    siapkan(path)
    with koneksi(path) as con:
        return pd.read_sql(
            "SELECT r.*, b.judul, b.kategori FROM riwayat_harga r JOIN buku b USING (url)",
            con,
        )

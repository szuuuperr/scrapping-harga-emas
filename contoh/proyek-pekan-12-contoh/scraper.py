"""
Lapisan 1: PENGAMBILAN DATA (P11-P12).

Mengambil semua buku di books.toscrape.com dengan menelusuri setiap kategori
beserta pagination-nya, sehingga kolom kategori didapat tanpa membuka
1000 halaman detail.

Alur: robots.txt -> daftar kategori -> halaman kategori (page-1, page-2, ...)
      -> kartu buku -> data bersih (dict)
"""
import logging
import random
import re
import time
from urllib import robotparser
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

import config

log = logging.getLogger(__name__)

RATING = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


# ---------- Fungsi murni: parse dan bersihkan (mudah diuji tanpa internet) ----------
def harga_ke_float(teks):
    """'£51.77' -> 51.77"""
    m = re.search(r"\d+(?:\.\d+)?", teks or "")
    return float(m.group()) if m else None


def parse_kategori(html, url_halaman):
    """Ambil daftar (nama, url) kategori dari sidebar halaman utama."""
    soup = BeautifulSoup(html, "html.parser")
    hasil = []
    for a in soup.select("div.side_categories ul li ul li a"):
        hasil.append((a.get_text(strip=True), urljoin(url_halaman, a["href"])))
    return hasil


def parse_buku(html, url_halaman, kategori):
    """Ambil semua kartu buku pada satu halaman kategori, sudah dibersihkan."""
    soup = BeautifulSoup(html, "html.parser")
    hasil = []
    for art in soup.select("article.product_pod"):
        link = art.select_one("h3 a")
        rating = art.select_one("p.star-rating")
        harga = art.select_one("p.price_color")
        stok = art.select_one("p.availability")
        if not link:
            continue  # kartu rusak: lewati, jangan hentikan seluruh scraping
        hasil.append({
            "url": urljoin(url_halaman, link["href"]),
            "judul": link.get("title", link.get_text(strip=True)).strip(),
            "kategori": kategori,
            "harga": harga_ke_float(harga.get_text() if harga else ""),
            "rating": RATING.get(rating["class"][1], 0) if rating else 0,
            "tersedia": bool(stok and "In stock" in stok.get_text()),
        })
    return hasil


def url_halaman_berikut(html, url_halaman):
    """URL tombol 'next', atau None jika sudah halaman terakhir."""
    nxt = BeautifulSoup(html, "html.parser").select_one("li.next a")
    return urljoin(url_halaman, nxt["href"]) if nxt else None


# ---------- Kelas scraper: urusan jaringan ----------
class BookScraper:
    def __init__(self, base_url=config.BASE_URL, jeda=config.JEDA_DETIK):
        self.base_url = base_url
        self.jeda = jeda
        self.session = requests.Session()  # koneksi dipakai ulang (P12)
        self.session.headers.update({"User-Agent": config.USER_AGENT})
        self.jumlah_request = 0
        self.gagal = []  # URL yang tetap gagal setelah retry

    def boleh_diambil(self, url):
        """Periksa robots.txt sebelum mulai (etika scraping, P11)."""
        rp = robotparser.RobotFileParser(urljoin(self.base_url, "/robots.txt"))
        try:
            rp.read()
        except Exception as e:  # robots.txt tidak bisa dibaca
            log.warning("robots.txt tidak terbaca (%s); lanjut dengan hati-hati", e)
            return True
        return rp.can_fetch(config.USER_AGENT, url)

    def get_html(self, url):
        """GET dengan timeout, retry, backoff eksponensial, dan jeda sopan (P12)."""
        for ke in range(1, config.MAKS_COBA + 1):
            try:
                time.sleep(self.jeda)
                r = self.session.get(url, timeout=config.TIMEOUT_DETIK)
                self.jumlah_request += 1
                if r.status_code == 429:
                    raise RequestException("429 terlalu banyak request")
                r.raise_for_status()
                r.encoding = "utf-8"  # agar simbol £ terbaca benar
                return r.text
            except RequestException as e:
                tunggu = 2 ** ke + random.random()
                log.warning("Gagal %s (percobaan %d): %s; tunggu %.1f s", url, ke, e, tunggu)
                time.sleep(tunggu)
        log.error("Menyerah mengambil %s", url)
        self.gagal.append(url)
        return None

    def daftar_kategori(self):
        html = self.get_html(self.base_url)
        if html is None:
            raise RuntimeError(f"Halaman utama {self.base_url} tidak bisa diambil")
        return parse_kategori(html, self.base_url)

    def iter_buku(self, maks_kategori=None):
        """Generator: hasilkan buku satu per satu dari semua kategori."""
        if not self.boleh_diambil(self.base_url):
            raise PermissionError("robots.txt melarang situs ini diambil")
        kategori = self.daftar_kategori()
        log.info("Ditemukan %d kategori", len(kategori))
        for nama, url in kategori[:maks_kategori]:
            halaman = 0
            while url:
                html = self.get_html(url)
                if html is None:
                    break  # lewati sisa kategori ini, lanjut kategori lain
                halaman += 1
                yield from parse_buku(html, url, nama)
                url = url_halaman_berikut(html, url)
            log.info("Kategori %-20s selesai (%d halaman)", nama, halaman)

    def jalankan(self, maks_kategori=None):
        """Ambil semua buku sebagai list. Jika maks_kategori diisi, hanya sebagian."""
        data = list(self.iter_buku(maks_kategori))
        log.info("Scraping selesai: %d buku, %d request, %d gagal",
                 len(data), self.jumlah_request, len(self.gagal))
        return data


if __name__ == "__main__":
    # Uji cepat: python scraper.py  (hanya 2 kategori)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for b in BookScraper().jalankan(maks_kategori=2)[:5]:
        print(b)

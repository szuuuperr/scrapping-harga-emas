"""
Lapisan 1: PENGAMBILAN DATA (P11-P12).

Mengambil harga emas harian dari harga-emas.org:
  - Tabel harga emas Antam per denominasi (0.5g–1000g)
  - Harga buyback Antam
  - Harga emas dunia (USD/oz)

Alur: robots.txt -> halaman utama -> tabel harga -> data bersih (dict)
"""
import logging
import random
import re
import time
from datetime import date
from urllib import robotparser
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

import config

log = logging.getLogger(__name__)


# ---------- Fungsi murni: parse dan bersihkan (mudah diuji tanpa internet) ----------
def berat_ke_float(teks):
    """'0.5' -> 0.5, '1' -> 1.0, '1000' -> 1000.0"""
    if not teks:
        return None
    teks = teks.strip().replace(",", ".")
    m = re.search(r"\d+(?:\.\d+)?", teks)
    return float(m.group()) if m else None


def rupiah_ke_float(teks):
    """'Rp1.885.000' atau '1.885.000' -> 1885000.0, 'Rp2.247.973,47' -> 2247973.47"""
    if not teks:
        return None
    bersih = re.sub(r"[^\d,.]", "", teks.strip())
    if not bersih:
        return None
    # Format Indonesia: titik = ribuan, koma = desimal
    if "," in bersih:
        bersih = bersih.replace(".", "").replace(",", ".")
    else:
        bersih = bersih.replace(".", "")
    try:
        return float(bersih)
    except ValueError:
        return None


def parse_harga_antam(html):
    """Ambil tabel harga emas Antam per denominasi dari halaman utama."""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    # Cari tabel khusus Antam terlebih dahulu
    target_tables = [t for t in tables if "antam" in t.get_text().lower()]
    if not target_tables:
        target_tables = tables

    for table in target_tables:
        table_rows = []
        for row in table.find_all("tr"):
            cols = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if len(cols) < 2:
                continue
            berat = berat_ke_float(cols[0])
            if berat is None or berat <= 0 or berat > 1000:
                continue
            harga = rupiah_ke_float(cols[1])
            if harga is None or harga < 100000:
                continue
            table_rows.append({
                "berat_gram": berat,
                "harga_jual": harga,
                "harga_per_gram": round(harga / berat, 2) if berat > 0 else None,
            })
        if table_rows:
            return table_rows
    return []


def parse_harga_buyback(html):
    """Ambil harga buyback (jual kembali / pembelian kembali) emas Antam."""
    soup = BeautifulSoup(html, "html.parser")
    teks = soup.get_text()

    # Pola teks langsung: 'pembelian kembali: Rp2.421.000' atau 'buyback: Rp1.325.000'
    m = re.search(r"(?:pembelian kembali|beli kembali|buyback)\s*[:\s]*[^\d]*([\d.,]+)", teks, re.I)
    if m:
        val = rupiah_ke_float(m.group(1))
        if val and val > 100000:
            return val

    # Fallback: cari dari tag HTML
    for tag in soup.find_all(string=re.compile(r"buyback|beli kembali|pembelian kembali", re.I)):
        parent = tag.find_parent("tr") or tag.find_parent("div") or tag.find_parent("td")
        if parent:
            angka = re.findall(r"[\d.]+", parent.get_text())
            for a in angka:
                val = rupiah_ke_float(a)
                if val and val > 100000:
                    return val
    return None


def parse_ringkasan_halaman(html):
    """Ambil ringkasan informasi: harga emas dunia (USD/oz) dan kurs USD/IDR."""
    soup = BeautifulSoup(html, "html.parser")
    info = {}

    for row in soup.find_all("tr"):
        row_teks = row.get_text().lower()
        cols = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if not cols:
            continue
        if ("ounce" in row_teks or "oz" in row_teks) and len(cols) >= 2:
            m = re.search(r"([\d.,]+)", cols[1])
            if m:
                val_str = m.group(1).replace(".", "").replace(",", ".")
                try:
                    info["harga_dunia_usd_oz"] = float(val_str)
                except ValueError:
                    pass
        if cols[0].upper() == "USD" and len(cols) >= 3:
            # Kolom beli/jual bank
            m = re.search(r"([\d.,]+)", cols[1])
            if m:
                try:
                    val = float(m.group(1).replace(".", "").replace(",", "."))
                    if val < 1000:
                        val *= 1000  # penyesuaian jika tertulis dalam ribuan desimal
                    info["kurs_usd_idr"] = round(val, 2)
                except ValueError:
                    pass

    return info


BULAN_ID = {
    "januari": "01", "februari": "02", "maret": "03", "april": "04",
    "mei": "05", "juni": "06", "juli": "07", "agustus": "08",
    "september": "09", "oktober": "10", "november": "11", "desember": "12",
}


def parse_daftar_tanggal(html, base_url):
    """Ambil daftar (tanggal, url) dari kalender riwayat harga di /history-harga."""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return [(date.today().isoformat(), base_url)]

    daftar = []
    # Kalender adalah tabel pertama
    for a in tables[0].find_all("a", href=True):
        href = a["href"]
        m = re.search(r"/history-harga/(\d{4})/([A-Za-z]+)/(\d{1,2})", href)
        if m:
            thn, bln, tgl = m.groups()
            bln_num = BULAN_ID.get(bln.lower(), "01")
            tgl_str = f"{thn}-{bln_num}-{int(tgl):02d}"
            daftar.append((tgl_str, urljoin(base_url, href)))
        elif href == "/history-harga" or href.endswith("/history-harga"):
            daftar.append((date.today().isoformat(), urljoin(base_url, href)))

    hasil = sorted(list(set(daftar)), key=lambda x: x[0])
    return hasil if hasil else [(date.today().isoformat(), base_url)]


# ---------- Kelas scraper: urusan jaringan ----------
class EmasScraper:
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
                r.encoding = "utf-8"
                return r.text
            except RequestException as e:
                tunggu = 2 ** ke + random.random()
                log.warning("Gagal %s (percobaan %d): %s; tunggu %.1f s", url, ke, e, tunggu)
                time.sleep(tunggu)
        log.error("Menyerah mengambil %s", url)
        self.gagal.append(url)
        return None

    def daftar_riwayat_tanggal(self):
        """Ambil daftar tanggal yang tersedia di kalender /history-harga."""
        url_history = urljoin(self.base_url, "/history-harga")
        html = self.get_html(url_history)
        if html is None:
            return [(date.today().isoformat(), self.base_url)]
        return parse_daftar_tanggal(html, self.base_url)

    def iter_emas(self, maks_hari=None):
        """Generator: hasilkan data emas per denominasi dari tanggal-tanggal riwayat."""
        if not self.boleh_diambil(self.base_url):
            raise PermissionError("robots.txt melarang situs ini diambil")

        daftar = self.daftar_riwayat_tanggal()
        # Jika maks_hari diberikan, ambil N hari terakhir
        if maks_hari is not None and maks_hari > 0:
            daftar = daftar[-maks_hari:]

        log.info("Akan mengambil data untuk %d tanggal", len(daftar))
        for tanggal, url in daftar:
            html = self.get_html(url)
            if html is None:
                continue
            denominasi = parse_harga_antam(html)
            buyback = parse_harga_buyback(html)
            info = parse_ringkasan_halaman(html)

            for d in denominasi:
                item = d.copy()
                item["tanggal"] = tanggal
                item["harga_buyback"] = buyback
                item["harga_dunia_usd_oz"] = info.get("harga_dunia_usd_oz")
                item["kurs_usd_idr"] = info.get("kurs_usd_idr")
                yield item

            log.info("Tanggal %s: %d denominasi diambil", tanggal, len(denominasi))

    def jalankan(self, maks_hari=None):
        """Ambil harga emas sebagai list. Jika maks_hari diisi, ambil N hari terakhir."""
        data = list(self.iter_emas(maks_hari))
        log.info("Scraping selesai: %d record, %d request, %d gagal",
                 len(data), self.jumlah_request, len(self.gagal))
        return data


if __name__ == "__main__":
    # Uji cepat: python scraper.py
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for b in EmasScraper().jalankan()[:5]:
        print(b)

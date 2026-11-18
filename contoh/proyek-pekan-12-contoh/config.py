"""
Pengaturan proyek di satu tempat.

Nilai rahasia (token bot) dibaca dari file .env, bukan ditulis di kode (P15).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # baca .env ke os.environ (jika file ada)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
LOG_DIR = ROOT / "logs"

DB_PATH = DATA_DIR / "buku.db"

# Sumber data. Boleh diganti lewat .env, misalnya untuk uji dengan server lokal.
BASE_URL = os.getenv("BASE_URL", "https://books.toscrape.com/")
USER_AGENT = "PantauBuku/1.0 (Proyek Pekan ke-12 Scripting Language UNY)"
JEDA_DETIK = float(os.getenv("JEDA_DETIK", "1.0"))  # jeda sopan antar-request
TIMEOUT_DETIK = 10
MAKS_COBA = 3  # retry jika request gagal

# Bot Telegram (opsional, hanya dibutuhkan bot.py)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Jadwal pipeline harian (WIB)
JAM_JADWAL = os.getenv("JAM_JADWAL", "07:00")

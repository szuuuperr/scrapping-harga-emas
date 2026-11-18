import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HTML_HARGA_EMAS = """
<html>
<body>
<h2>Harga Emas Antam Hari Ini</h2>
<table>
<thead><tr><th>Gram</th><th>Harga Jual</th></tr></thead>
<tbody>
<tr><td>0.5</td><td>Rp742.500</td></tr>
<tr><td>1</td><td>Rp1.385.000</td></tr>
<tr><td>2</td><td>Rp2.710.000</td></tr>
<tr><td>5</td><td>Rp6.625.000</td></tr>
<tr><td>10</td><td>Rp13.150.000</td></tr>
<tr><td>25</td><td>Rp32.625.000</td></tr>
<tr><td>50</td><td>Rp65.100.000</td></tr>
<tr><td>100</td><td>Rp129.950.000</td></tr>
<tr><td>250</td><td>Rp324.375.000</td></tr>
<tr><td>500</td><td>Rp648.500.000</td></tr>
<tr><td>1000</td><td>Rp1.296.750.000</td></tr>
</tbody>
</table>

<div>Harga Buyback / Beli Kembali: <b>Rp1.325.000</b></div>

<p>Harga emas dunia 2.750,30 USD/oz | Kurs IDR/USD 15.800</p>
</body>
</html>
"""

HTML_TANPA_BUYBACK = """
<html>
<body>
<table>
<thead><tr><th>Gram</th><th>Harga</th></tr></thead>
<tbody>
<tr><td>1</td><td>Rp1.385.000</td></tr>
<tr><td>5</td><td>Rp6.625.000</td></tr>
</tbody>
</table>
</body>
</html>
"""

HTML_KALENDER = """
<table>
<thead><tr><th>Prev</th><th>November 2026</th><th>Next</th></tr></thead>
<tbody>
<tr>
  <td><a href="/history-harga/2026/November/15">15</a></td>
  <td><a href="/history-harga/2026/November/16">16</a></td>
  <td><a href="/history-harga/2026/November/17">17</a></td>
</tr>
</tbody>
</table>
"""


@pytest.fixture
def contoh_emas():
    return [
        {"tanggal": "2026-11-17", "berat_gram": 1.0, "harga_jual": 1385000.0,
         "harga_per_gram": 1385000.0, "harga_buyback": 1325000.0,
         "harga_dunia_usd_oz": None, "kurs_usd_idr": None},
        {"tanggal": "2026-11-17", "berat_gram": 5.0, "harga_jual": 6625000.0,
         "harga_per_gram": 1325000.0, "harga_buyback": 1325000.0,
         "harga_dunia_usd_oz": None, "kurs_usd_idr": None},
        {"tanggal": "2026-11-17", "berat_gram": 10.0, "harga_jual": 13150000.0,
         "harga_per_gram": 1315000.0, "harga_buyback": 1325000.0,
         "harga_dunia_usd_oz": None, "kurs_usd_idr": None},
    ]


@pytest.fixture
def contoh_emas_hari2():
    """Data hari kedua dengan harga berbeda untuk tes perubahan."""
    return [
        {"tanggal": "2026-11-18", "berat_gram": 1.0, "harga_jual": 1390000.0,
         "harga_per_gram": 1390000.0, "harga_buyback": 1330000.0,
         "harga_dunia_usd_oz": None, "kurs_usd_idr": None},
        {"tanggal": "2026-11-18", "berat_gram": 5.0, "harga_jual": 6625000.0,
         "harga_per_gram": 1325000.0, "harga_buyback": 1330000.0,
         "harga_dunia_usd_oz": None, "kurs_usd_idr": None},
        {"tanggal": "2026-11-18", "berat_gram": 10.0, "harga_jual": 13200000.0,
         "harga_per_gram": 1320000.0, "harga_buyback": 1330000.0,
         "harga_dunia_usd_oz": None, "kurs_usd_idr": None},
    ]


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "uji.db"

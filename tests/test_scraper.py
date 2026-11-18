from scraper import (
    berat_ke_float,
    parse_daftar_tanggal,
    parse_harga_antam,
    parse_harga_buyback,
    rupiah_ke_float,
)

from .conftest import HTML_HARGA_EMAS, HTML_KALENDER, HTML_TANPA_BUYBACK


def test_rupiah_ke_float():
    assert rupiah_ke_float("Rp1.385.000") == 1385000.0
    assert rupiah_ke_float("1.385.000") == 1385000.0
    assert rupiah_ke_float("742.500") == 742500.0
    assert rupiah_ke_float("") is None
    assert rupiah_ke_float(None) is None


def test_rupiah_ke_float_dengan_koma():
    assert rupiah_ke_float("Rp2.247.973,47") == 2247973.47


def test_parse_harga_antam():
    data = parse_harga_antam(HTML_HARGA_EMAS)
    assert len(data) == 11  # 0.5g sampai 1000g
    # Cek denominasi 1 gram
    satu_gram = [d for d in data if d["berat_gram"] == 1.0]
    assert len(satu_gram) == 1
    assert satu_gram[0]["harga_jual"] == 1385000.0
    assert satu_gram[0]["harga_per_gram"] == 1385000.0
    # Cek denominasi 5 gram
    lima_gram = [d for d in data if d["berat_gram"] == 5.0]
    assert len(lima_gram) == 1
    assert lima_gram[0]["harga_jual"] == 6625000.0
    assert lima_gram[0]["harga_per_gram"] == 1325000.0


def test_parse_harga_buyback():
    buyback = parse_harga_buyback(HTML_HARGA_EMAS)
    assert buyback == 1325000.0


def test_parse_buyback_tidak_ada():
    buyback = parse_harga_buyback(HTML_TANPA_BUYBACK)
    assert buyback is None


def test_parse_daftar_tanggal():
    daftar = parse_daftar_tanggal(HTML_KALENDER, "https://harga-emas.org/")
    assert len(daftar) == 3
    assert daftar[0][0] == "2026-11-15"
    assert daftar[1][0] == "2026-11-16"
    assert daftar[2][0] == "2026-11-17"
    assert daftar[0][1] == "https://harga-emas.org/history-harga/2026/November/15"

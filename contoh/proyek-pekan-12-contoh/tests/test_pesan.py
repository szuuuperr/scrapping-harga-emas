import pandas as pd

import pesan


def test_cocokkan_kategori():
    semua = ["Travel", "Mystery", "Historical Fiction", "History"]
    assert pesan.cocokkan_kategori("travel", semua) == "Travel"
    assert pesan.cocokkan_kategori("myst", semua) == "Mystery"
    assert pesan.cocokkan_kategori("hist", semua) is None  # ambigu
    assert pesan.cocokkan_kategori("history", semua) == "History"


def test_format_daftar_buku():
    df = pd.DataFrame({"judul": ["A"], "harga": [10.5], "rating": [3]})
    assert "1. A - £10.50 (★★★)" in pesan.format_daftar_buku(df, "Hasil:")
    assert pesan.format_daftar_buku(df.iloc[0:0], "x") == "Tidak ada buku yang cocok."


def test_format_perubahan():
    df = pd.DataFrame({"judul": ["A"], "harga_lama": [10.0], "harga_baru": [8.0], "selisih": [-2.0]})
    assert "turun" in pesan.format_perubahan(df)
    assert "Belum ada" in pesan.format_perubahan(df.iloc[0:0])

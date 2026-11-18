import pandas as pd

import pesan


def test_cocokkan_berat():
    semua = [0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0]
    assert pesan.cocokkan_berat("1", semua) == 1.0
    assert pesan.cocokkan_berat("5g", semua) == 5.0
    assert pesan.cocokkan_berat("10 gram", semua) == 10.0
    assert pesan.cocokkan_berat("0.5", semua) == 0.5
    assert pesan.cocokkan_berat("abc", semua) is None
    assert pesan.cocokkan_berat("99", semua) is None


def test_format_rupiah():
    assert pesan.format_rupiah(1385000) == "Rp1.385.000"
    assert pesan.format_rupiah(None) == "-"


def test_format_daftar_harga():
    df = pd.DataFrame({
        "berat_gram": [1.0],
        "harga_jual": [1385000.0],
        "harga_per_gram": [1385000.0],
    })
    hasil = pesan.format_daftar_harga(df, "Harga:")
    assert "1.0g" in hasil
    assert "Rp" in hasil
    assert pesan.format_daftar_harga(df.iloc[0:0], "x") == "Tidak ada data harga."


def test_format_perubahan():
    df = pd.DataFrame({
        "berat_gram": [1.0],
        "harga_lama": [1385000.0],
        "harga_baru": [1390000.0],
        "selisih": [5000.0],
    })
    assert "naik" in pesan.format_perubahan(df)

    df_turun = pd.DataFrame({
        "berat_gram": [1.0],
        "harga_lama": [1390000.0],
        "harga_baru": [1385000.0],
        "selisih": [-5000.0],
    })
    assert "turun" in pesan.format_perubahan(df_turun)
    assert "Belum ada" in pesan.format_perubahan(df.iloc[0:0])

import pandas as pd

import analisis


def test_ringkasan_dan_pertanyaan(contoh_buku):
    df = analisis.bersihkan(pd.DataFrame(contoh_buku))
    r = analisis.ringkasan(df)
    assert r["jumlah_buku"] == 3
    assert r["harga_rata"] == 20.0
    assert analisis.q1_kategori_terbanyak(df)["kategori"].iloc[0] == "Travel"
    assert analisis.q2_harga_per_rating(df)["rating"].tolist() == [1, 3, 5]
    t3 = analisis.q3_kategori_termahal(df, minimal_buku=1)
    assert t3["kategori"].iloc[0] == "Mystery"
    assert len(analisis.temuan(df)) == 3


def test_bersihkan_membuang_baris_rusak(contoh_buku):
    contoh_buku.append({**contoh_buku[0]})  # duplikat
    contoh_buku.append({**contoh_buku[1], "url": "u9", "harga": None})
    df = analisis.bersihkan(pd.DataFrame(contoh_buku))
    assert len(df) == 3


def test_buat_grafik(contoh_buku, tmp_path):
    df = analisis.bersihkan(pd.DataFrame(contoh_buku * 2).assign(url=lambda d: d.index))
    path = analisis.buat_grafik(df, folder=tmp_path)
    assert all(p.exists() for p in path.values())

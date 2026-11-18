import pandas as pd

import analisis


def test_ringkasan(contoh_emas):
    df = analisis.bersihkan(pd.DataFrame(contoh_emas))
    r = analisis.ringkasan(df)
    assert r["jumlah_data"] == 3
    assert r["harga_1g_terakhir"] == 1385000.0
    assert r["buyback_terakhir"] == 1325000.0
    assert r["spread_1g"] == 60000.0


def test_q1_tren_harga(contoh_emas):
    df = analisis.bersihkan(pd.DataFrame(contoh_emas))
    tren = analisis.q1_tren_harga(df, berat=1.0)
    assert len(tren) == 1
    assert tren["harga_jual"].iloc[0] == 1385000.0


def test_q2_spread(contoh_emas):
    df = analisis.bersihkan(pd.DataFrame(contoh_emas))
    spread = analisis.q2_spread_per_denominasi(df)
    assert len(spread) == 3
    # Spread 1g = 1385000 - 1325000 = 60000
    sp_1g = spread[spread["berat_gram"] == 1.0]
    assert sp_1g["rata_rata"].iloc[0] == 60000.0


def test_q3_harga_per_gram(contoh_emas):
    df = analisis.bersihkan(pd.DataFrame(contoh_emas))
    h = analisis.q3_harga_per_gram(df)
    assert len(h) == 3
    # 10g paling efisien (1315000 per gram)
    paling_murah = h.loc[h["harga_per_gram"].idxmin()]
    assert paling_murah["berat_gram"] == 10.0


def test_temuan(contoh_emas):
    df = analisis.bersihkan(pd.DataFrame(contoh_emas))
    t = analisis.temuan(df)
    assert len(t) == 3
    assert "1.385.000" in t[0]  # harga 1 gram
    assert "60.000" in t[1]     # spread


def test_temuan_multi_tanggal(contoh_emas, contoh_emas_hari2):
    gabung = contoh_emas + contoh_emas_hari2
    df = analisis.bersihkan(pd.DataFrame(gabung))
    t = analisis.temuan(df)
    assert len(t) == 4  # 3 dasar + 1 temuan tren
    assert "Tren harga 1 gram" in t[3]
    assert "naik" in t[3]


def test_bersihkan_membuang_baris_rusak(contoh_emas):
    contoh_emas.append({**contoh_emas[0]})  # duplikat
    contoh_emas.append({**contoh_emas[1], "berat_gram": 99, "harga_jual": None})
    df = analisis.bersihkan(pd.DataFrame(contoh_emas))
    assert len(df) == 3


def test_buat_grafik(contoh_emas, tmp_path):
    df = analisis.bersihkan(pd.DataFrame(contoh_emas))
    path = analisis.buat_grafik(df, folder=tmp_path)
    assert all(p.exists() for p in path.values())
    assert len(path) == 3

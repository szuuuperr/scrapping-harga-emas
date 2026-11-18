import db


def test_simpan_tanpa_duplikat(contoh_buku, db_path):
    assert db.simpan(contoh_buku, "2026-11-10T07:00:00", path=db_path) == 3
    assert db.simpan(contoh_buku, "2026-11-11T07:00:00", path=db_path) == 0  # tidak ada buku baru
    df = db.baca_buku(db_path)
    assert len(df) == 3
    assert set(df["pertama_dilihat"]) == {"2026-11-10T07:00:00"}
    assert set(df["terakhir_dilihat"]) == {"2026-11-11T07:00:00"}


def test_cari_aman_dari_sql_injection(contoh_buku, db_path):
    db.simpan(contoh_buku, path=db_path)
    assert db.cari("python", path=db_path)["judul"].tolist() == ["Buku B Python"]
    assert db.cari("' OR 1=1 --", path=db_path).empty


def test_perubahan_harga(contoh_buku, db_path):
    db.simpan(contoh_buku, "2026-11-10T07:00:00", path=db_path)
    assert db.perubahan_harga(db_path).empty
    contoh_buku[0]["harga"] = 8.5
    db.simpan(contoh_buku, "2026-11-11T07:00:00", path=db_path)
    berubah = db.perubahan_harga(db_path)
    assert berubah["judul"].tolist() == ["Buku A"]
    assert berubah["selisih"].iloc[0] == -1.5

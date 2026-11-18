import db


def test_simpan_tanpa_duplikat(contoh_emas, db_path):
    assert db.simpan(contoh_emas, "2026-11-17T07:00:00", path=db_path) == 3
    assert db.simpan(contoh_emas, "2026-11-17T08:00:00", path=db_path) == 0  # tidak ada record baru
    df = db.baca_emas(db_path)
    assert len(df) == 3
    assert set(df["pertama_dilihat"]) == {"2026-11-17T07:00:00"}
    assert set(df["terakhir_dilihat"]) == {"2026-11-17T08:00:00"}


def test_cari_aman_dari_sql_injection(contoh_emas, db_path):
    db.simpan(contoh_emas, path=db_path)
    hasil = db.cari(1.0, path=db_path)
    assert len(hasil) == 1
    assert hasil["berat_gram"].iloc[0] == 1.0
    # SQL injection tidak boleh lolos
    assert db.cari(0, path=db_path).empty


def test_perubahan_harga(contoh_emas, contoh_emas_hari2, db_path):
    db.simpan(contoh_emas, "2026-11-17T07:00:00", path=db_path)
    assert db.perubahan_harga(db_path).empty  # belum ada perbandingan
    db.simpan(contoh_emas_hari2, "2026-11-18T07:00:00", path=db_path)
    berubah = db.perubahan_harga(db_path)
    # 1g naik 5000, 5g tetap, 10g naik 50000 -> 2 yang berubah
    assert len(berubah) == 2
    berat_berubah = sorted(berubah["berat_gram"].tolist())
    assert berat_berubah == [1.0, 10.0]

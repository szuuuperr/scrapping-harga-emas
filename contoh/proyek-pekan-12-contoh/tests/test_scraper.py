from scraper import harga_ke_float, parse_buku, parse_kategori, url_halaman_berikut

from .conftest import HTML_BERANDA, HTML_KATEGORI, URL_KATEGORI


def test_harga_ke_float():
    assert harga_ke_float("£51.77") == 51.77
    assert harga_ke_float("Â£12.00") == 12.0  # encoding salah tetap terbaca
    assert harga_ke_float("") is None


def test_parse_kategori_mengabaikan_induk_books():
    kat = parse_kategori(HTML_BERANDA, "https://books.toscrape.com/")
    assert [k for k, _ in kat] == ["Travel", "Mystery"]
    assert kat[0][1] == URL_KATEGORI


def test_parse_buku():
    buku = parse_buku(HTML_KATEGORI, URL_KATEGORI, "Travel")
    assert len(buku) == 2
    b = buku[0]
    assert b["judul"] == "It's Only the Himalayas"  # judul lengkap dari atribut title
    assert b["harga"] == 45.17
    assert b["rating"] == 3
    assert b["tersedia"] is True
    assert b["kategori"] == "Travel"
    assert b["url"] == "https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html"
    assert buku[1]["tersedia"] is False


def test_halaman_berikut():
    assert url_halaman_berikut(HTML_KATEGORI, URL_KATEGORI).endswith("travel_2/page-2.html")
    assert url_halaman_berikut("<html></html>", URL_KATEGORI) is None

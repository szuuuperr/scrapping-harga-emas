import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HTML_BERANDA = """
<div class="side_categories"><ul><li><a href="catalogue/category/books_1/index.html">Books</a>
<ul>
  <li><a href="catalogue/category/books/travel_2/index.html">Travel</a></li>
  <li><a href="catalogue/category/books/mystery_3/index.html">Mystery</a></li>
</ul></li></ul></div>
"""

HTML_KATEGORI = """
<ol class="row">
<li><article class="product_pod">
  <p class="star-rating Three"></p>
  <h3><a href="../../../its-only-the-himalayas_981/index.html" title="It's Only the Himalayas">It's Only the...</a></h3>
  <div class="product_price"><p class="price_color">£45.17</p>
  <p class="instock availability"><i class="icon-ok"></i> In stock</p></div>
</article></li>
<li><article class="product_pod">
  <p class="star-rating Five"></p>
  <h3><a href="../../../full-moon_980/index.html" title="Full Moon over Noah's Ark">Full Moon...</a></h3>
  <div class="product_price"><p class="price_color">£49.43</p>
  <p class="availability">Out of stock</p></div>
</article></li>
</ol>
<ul class="pager"><li class="next"><a href="page-2.html">next</a></li></ul>
"""

URL_KATEGORI = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"


@pytest.fixture
def contoh_buku():
    return [
        {"url": "u1", "judul": "Buku A", "kategori": "Travel", "harga": 10.0, "rating": 3, "tersedia": True},
        {"url": "u2", "judul": "Buku B Python", "kategori": "Travel", "harga": 20.0, "rating": 5, "tersedia": False},
        {"url": "u3", "judul": "Buku C", "kategori": "Mystery", "harga": 30.0, "rating": 1, "tersedia": True},
    ]


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "uji.db"

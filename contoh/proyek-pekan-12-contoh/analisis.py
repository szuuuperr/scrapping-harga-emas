"""
Lapisan 3: ANALISIS DAN VISUALISASI (P14).

Tiga pertanyaan analisis:
  1. Kategori apa yang paling banyak bukunya?
  2. Apakah buku dengan rating lebih tinggi lebih mahal?
  3. Kategori apa yang rata-rata harganya paling mahal?
"""
import matplotlib

matplotlib.use("Agg")  # simpan grafik ke file tanpa membuka jendela
import matplotlib.pyplot as plt
import pandas as pd

import config

WARNA = "#2563EB"


def bersihkan(df):
    """Pastikan tipe data benar dan buang baris yang tidak lengkap."""
    df = df.copy()
    df["harga"] = pd.to_numeric(df["harga"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").astype("Int64")
    df["tersedia"] = df["tersedia"].astype(bool)
    df = df.dropna(subset=["judul", "harga"]).drop_duplicates(subset="url")
    return df


def ringkasan(df):
    """Angka-angka utama untuk laporan, bot, dan dashboard."""
    return {
        "jumlah_buku": len(df),
        "jumlah_kategori": df["kategori"].nunique(),
        "harga_rata": round(df["harga"].mean(), 2),
        "harga_min": df["harga"].min(),
        "harga_maks": df["harga"].max(),
        "persen_tersedia": round(100 * df["tersedia"].mean(), 1),
        "rating_rata": round(df["rating"].astype(float).mean(), 2),
    }


def q1_kategori_terbanyak(df, n=10):
    return (df.groupby("kategori").size().sort_values(ascending=False)
              .head(n).rename("jumlah_buku").reset_index())


def q2_harga_per_rating(df):
    return (df.groupby("rating")["harga"]
              .agg(jumlah="count", rata_rata="mean", median="median")
              .round(2).reset_index())


def q3_kategori_termahal(df, n=10, minimal_buku=5):
    """Kategori dengan buku < minimal_buku diabaikan agar rata-rata tidak menyesatkan."""
    g = df.groupby("kategori")["harga"].agg(jumlah="count", rata_rata="mean")
    g = g[g["jumlah"] >= minimal_buku]
    return g.sort_values("rata_rata", ascending=False).head(n).round(2).reset_index()


def _barh(ax, label, nilai, judul, xlabel, fmt="{:.0f}"):
    ax.barh(label, nilai, color=WARNA)
    ax.invert_yaxis()  # nilai terbesar di atas
    ax.set_title(judul, loc="left", fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.bar_label(ax.containers[0], labels=[fmt.format(v) for v in nilai], padding=3)
    ax.spines[["top", "right"]].set_visible(False)


def buat_grafik(df, folder=config.OUTPUT_DIR):
    """Simpan 3 grafik PNG, kembalikan dict {nama: path}."""
    folder.mkdir(parents=True, exist_ok=True)
    path = {}

    t1 = q1_kategori_terbanyak(df)
    fig, ax = plt.subplots(figsize=(8, 5))
    _barh(ax, t1["kategori"], t1["jumlah_buku"], "10 kategori dengan buku terbanyak", "Jumlah buku")
    fig.tight_layout()
    path["kategori"] = folder / "grafik_kategori.png"
    fig.savefig(path["kategori"], dpi=150)
    plt.close(fig)

    t2 = q2_harga_per_rating(df)
    fig, ax = plt.subplots(figsize=(8, 5))
    data = [df.loc[df["rating"] == r, "harga"] for r in t2["rating"]]
    ax.boxplot(data, tick_labels=[f"{r} bintang" for r in t2["rating"]], patch_artist=True,
               boxprops={"facecolor": "#BFDBFE"}, medianprops={"color": WARNA, "linewidth": 2})
    ax.set_title("Sebaran harga menurut rating", loc="left", fontweight="bold")
    ax.set_ylabel("Harga (£)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path["rating"] = folder / "grafik_rating.png"
    fig.savefig(path["rating"], dpi=150)
    plt.close(fig)

    t3 = q3_kategori_termahal(df)
    fig, ax = plt.subplots(figsize=(8, 5))
    _barh(ax, t3["kategori"], t3["rata_rata"], "10 kategori dengan rata-rata harga tertinggi",
          "Rata-rata harga (£), kategori dengan minimal 5 buku", fmt="£{:.2f}")
    fig.tight_layout()
    path["termahal"] = folder / "grafik_termahal.png"
    fig.savefig(path["termahal"], dpi=150)
    plt.close(fig)

    return path


def temuan(df):
    """Kalimat temuan otomatis untuk laporan dan bot."""
    t1, t2, t3 = q1_kategori_terbanyak(df, 1), q2_harga_per_rating(df), q3_kategori_termahal(df, 1)
    if t3.empty:  # data sedikit (misal hasil filter): pakai semua kategori
        t3 = q3_kategori_termahal(df, 1, minimal_buku=1)
    selisih = t2["rata_rata"].iloc[-1] - t2["rata_rata"].iloc[0]
    arah = "lebih mahal" if selisih > 0 else "lebih murah"
    return [
        f"Kategori terbanyak adalah {t1['kategori'].iloc[0]} dengan {t1['jumlah_buku'].iloc[0]} buku.",
        f"Buku rating {t2['rating'].iloc[-1]} rata-rata £{abs(selisih):.2f} {arah} "
        f"daripada buku rating {t2['rating'].iloc[0]}.",
        f"Kategori dengan rata-rata harga tertinggi adalah {t3['kategori'].iloc[0]} "
        f"(£{t3['rata_rata'].iloc[0]:.2f}).",
    ]

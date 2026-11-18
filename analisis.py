"""
Lapisan 3: ANALISIS DAN VISUALISASI (P14).

Tiga pertanyaan analisis:
  1. Bagaimana tren harga emas 1 gram dalam beberapa hari terakhir?
  2. Berapa spread (selisih jual–buyback) rata-rata per denominasi?
  3. Denominasi mana yang harga per gramnya paling efisien (termurah)?
"""
import matplotlib

matplotlib.use("Agg")  # simpan grafik ke file tanpa membuka jendela
import matplotlib.pyplot as plt
import pandas as pd

import config

WARNA = "#D4A017"  # warna emas
WARNA2 = "#B8860B"


def bersihkan(df):
    """Pastikan tipe data benar dan buang baris yang tidak lengkap."""
    df = df.copy()
    df["harga_jual"] = pd.to_numeric(df["harga_jual"], errors="coerce")
    df["harga_per_gram"] = pd.to_numeric(df["harga_per_gram"], errors="coerce")
    df["harga_buyback"] = pd.to_numeric(df["harga_buyback"], errors="coerce")
    df["berat_gram"] = pd.to_numeric(df["berat_gram"], errors="coerce")
    df = df.dropna(subset=["harga_jual", "berat_gram"]).drop_duplicates(
        subset=["tanggal", "berat_gram"]
    )
    return df


def ringkasan(df):
    """Angka-angka utama untuk laporan, bot, dan dashboard."""
    df1g = df[df["berat_gram"] == 1.0]
    harga_1g = df1g["harga_jual"].iloc[0] if not df1g.empty else None
    buyback = df1g["harga_buyback"].iloc[0] if not df1g.empty else None
    return {
        "jumlah_data": len(df),
        "jumlah_tanggal": df["tanggal"].nunique(),
        "jumlah_denominasi": df["berat_gram"].nunique(),
        "harga_1g_terakhir": harga_1g,
        "buyback_terakhir": buyback,
        "spread_1g": round(harga_1g - buyback, 0) if harga_1g and buyback else None,
        "harga_min": df["harga_jual"].min(),
        "harga_maks": df["harga_jual"].max(),
    }


def q1_tren_harga(df, berat=1.0):
    """Tren harga harian untuk denominasi tertentu."""
    f = df[df["berat_gram"] == berat].sort_values("tanggal")
    return f[["tanggal", "harga_jual", "harga_buyback"]].reset_index(drop=True)


def q2_spread_per_denominasi(df):
    """Selisih harga jual – buyback rata-rata per denominasi."""
    f = df.dropna(subset=["harga_buyback"]).copy()
    if f.empty:
        return pd.DataFrame(columns=["berat_gram", "rata_rata", "minimum", "maksimum"])
    f["spread"] = f["harga_jual"] - f["harga_buyback"]
    return (f.groupby("berat_gram")["spread"]
              .agg(rata_rata="mean", minimum="min", maksimum="max")
              .round(0).reset_index()
              .sort_values("berat_gram"))


def q3_harga_per_gram(df):
    """Harga per gram per denominasi — cari yang paling efisien."""
    terbaru = df[df["tanggal"] == df["tanggal"].max()]
    return (terbaru[["berat_gram", "harga_jual", "harga_per_gram"]]
            .sort_values("berat_gram").reset_index(drop=True))


def _format_rupiah(x, _=None):
    """Format angka ke rupiah singkat untuk label grafik."""
    if x >= 1_000_000_000:
        return f"Rp{x/1e9:.1f}M"
    if x >= 1_000_000:
        return f"Rp{x/1e6:.1f}jt"
    if x >= 1_000:
        return f"Rp{x/1e3:.0f}rb"
    return f"Rp{x:.0f}"


def buat_grafik(df, folder=config.OUTPUT_DIR):
    """Simpan 3 grafik PNG, kembalikan dict {nama: path}."""
    folder.mkdir(parents=True, exist_ok=True)
    path = {}

    # Grafik 1: Tren harga 1 gram
    t1 = q1_tren_harga(df)
    fig, ax = plt.subplots(figsize=(10, 5))
    if not t1.empty:
        ax.plot(t1["tanggal"], t1["harga_jual"], marker="o", color=WARNA,
                linewidth=2, label="Harga Jual")
        if t1["harga_buyback"].notna().any():
            ax.plot(t1["tanggal"], t1["harga_buyback"], marker="s", color=WARNA2,
                    linewidth=2, linestyle="--", label="Buyback")
        ax.legend()
    ax.set_title("Tren Harga Emas Antam 1 Gram", loc="left", fontweight="bold")
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Harga (Rp)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(_format_rupiah))
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    path["tren"] = folder / "grafik_tren.png"
    fig.savefig(path["tren"], dpi=150)
    plt.close(fig)

    # Grafik 2: Spread per denominasi
    t2 = q2_spread_per_denominasi(df)
    fig, ax = plt.subplots(figsize=(10, 5))
    if not t2.empty:
        label = [f"{b}g" for b in t2["berat_gram"]]
        ax.barh(label, t2["rata_rata"], color=WARNA)
        ax.invert_yaxis()
        ax.bar_label(ax.containers[0],
                     labels=[_format_rupiah(v) for v in t2["rata_rata"]], padding=3)
    ax.set_title("Rata-rata Spread (Jual - Buyback) per Denominasi",
                 loc="left", fontweight="bold")
    ax.set_xlabel("Spread (Rp)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path["spread"] = folder / "grafik_spread.png"
    fig.savefig(path["spread"], dpi=150)
    plt.close(fig)

    # Grafik 3: Harga per gram per denominasi
    t3 = q3_harga_per_gram(df)
    fig, ax = plt.subplots(figsize=(10, 5))
    if not t3.empty:
        label = [f"{b}g" for b in t3["berat_gram"]]
        ax.bar(label, t3["harga_per_gram"], color=WARNA)
        ax.bar_label(ax.containers[0],
                     labels=[_format_rupiah(v) for v in t3["harga_per_gram"]], padding=3)
    ax.set_title("Harga per Gram Menurut Denominasi (semakin besar semakin murah?)",
                 loc="left", fontweight="bold")
    ax.set_xlabel("Denominasi")
    ax.set_ylabel("Harga per Gram (Rp)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(_format_rupiah))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path["efisiensi"] = folder / "grafik_efisiensi.png"
    fig.savefig(path["efisiensi"], dpi=150)
    plt.close(fig)

    return path


def temuan(df):
    """Kalimat temuan otomatis untuk laporan dan bot."""
    r = ringkasan(df)
    hasil = []

    # Temuan 1: Harga terkini
    if r["harga_1g_terakhir"]:
        h1 = f"{r['harga_1g_terakhir']:,.0f}".replace(",", ".")
        hasil.append(
            f"Harga emas Antam 1 gram saat ini Rp{h1}."
        )

    # Temuan 2: Spread
    if r.get("spread_1g") is not None and pd.notna(r["spread_1g"]):
        sp = f"{r['spread_1g']:,.0f}".replace(",", ".")
        hasil.append(
            f"Spread (selisih jual-buyback) emas 1 gram adalah Rp{sp}."
        )

    # Temuan 3: Denominasi paling efisien
    t3 = q3_harga_per_gram(df)
    if not t3.empty:
        paling_murah = t3.loc[t3["harga_per_gram"].idxmin()]
        pm_h = f"{paling_murah['harga_per_gram']:,.0f}".replace(",", ".")
        hasil.append(
            f"Denominasi paling efisien (harga per gram termurah) adalah "
            f"{paling_murah['berat_gram']:.0f}g dengan harga per gram "
            f"Rp{pm_h}."
        )

    # Temuan 4: Tren perubahan harga jika ada data lebih dari 1 tanggal
    t1 = q1_tren_harga(df)
    if len(t1) >= 2:
        awal = t1["harga_jual"].iloc[0]
        akhir = t1["harga_jual"].iloc[-1]
        selisih = akhir - awal
        arah = "naik" if selisih > 0 else "turun"
        tgl_awal = t1["tanggal"].iloc[0]
        tgl_akhir = t1["tanggal"].iloc[-1]
        selisih_str = f"Rp{abs(selisih):,.0f}".replace(",", ".")
        hasil.append(
            f"Tren harga 1 gram dari {tgl_awal} ke {tgl_akhir} {arah} {selisih_str}."
        )

    return hasil

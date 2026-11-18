"""
Lapisan 4c: DASHBOARD STREAMLIT (P16).

Jalankan: streamlit run app.py   -> http://localhost:8501
"""
import streamlit as st

import analisis
import db

st.set_page_config(page_title="Dashboard Katalog Buku", layout="wide")


@st.cache_data(ttl=600)  # data dimuat ulang paling sering 10 menit sekali
def muat():
    return analisis.bersihkan(db.baca_buku()), db.riwayat(), db.perubahan_harga()


df, riwayat, berubah = muat()
st.title("Dashboard Katalog Buku")

if df.empty:
    st.warning("Database masih kosong. Jalankan `python main.py` dulu.")
    st.stop()

st.caption(f"Sumber: books.toscrape.com · data terakhir {df['terakhir_dilihat'].max()}")

# ---------- Filter di sidebar ----------
st.sidebar.header("Filter")
semua_kategori = sorted(df["kategori"].unique())
pilih_kategori = st.sidebar.multiselect("Kategori", semua_kategori,
                                        placeholder="Semua kategori")
lo, hi = float(df["harga"].min()), float(df["harga"].max())
rentang = st.sidebar.slider("Rentang harga (£)", lo, hi, (lo, hi))
rating_min = st.sidebar.select_slider("Rating minimal", options=[1, 2, 3, 4, 5], value=1)
hanya_tersedia = st.sidebar.checkbox("Hanya yang tersedia")
kata = st.sidebar.text_input("Cari judul")

f = df[df["harga"].between(*rentang) & (df["rating"] >= rating_min)]
if pilih_kategori:
    f = f[f["kategori"].isin(pilih_kategori)]
if hanya_tersedia:
    f = f[f["tersedia"]]
if kata:
    f = f[f["judul"].str.contains(kata, case=False, regex=False)]

if f.empty:
    st.info("Tidak ada buku yang cocok dengan filter.")
    st.stop()

# ---------- Metrik ----------
r = analisis.ringkasan(f)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Jumlah buku", f"{r['jumlah_buku']:,}")
selisih = r["harga_rata"] - df["harga"].mean()
c2.metric("Harga rata-rata", f"£{r['harga_rata']:.2f}",
          delta=f"{selisih:+.2f} dari semua buku" if len(f) < len(df) else None,
          delta_color="off")
c3.metric("Rating rata-rata", f"{r['rating_rata']:.2f} ★")
c4.metric("Tersedia", f"{r['persen_tersedia']}%")

# ---------- Grafik dan tabel ----------
tab1, tab2, tab3, tab4 = st.tabs(["Kategori", "Rating", "Data", "Perubahan harga"])
with tab1:
    kiri, kanan = st.columns(2)
    kiri.subheader("Kategori terbanyak")
    kiri.bar_chart(analisis.q1_kategori_terbanyak(f), x="kategori", y="jumlah_buku",
                   horizontal=True, sort="-jumlah_buku")
    kanan.subheader("Rata-rata harga tertinggi")
    kanan.bar_chart(analisis.q3_kategori_termahal(f, minimal_buku=1), x="kategori",
                    y="rata_rata", horizontal=True, sort="-rata_rata")
with tab2:
    st.subheader("Harga menurut rating")
    st.dataframe(analisis.q2_harga_per_rating(f), hide_index=True)
    st.bar_chart(analisis.q2_harga_per_rating(f), x="rating", y="rata_rata")
with tab3:
    kolom = ["judul", "kategori", "harga", "rating", "tersedia"]
    st.dataframe(f[kolom].sort_values("harga"), hide_index=True, width="stretch",
                 column_config={"harga": st.column_config.NumberColumn("harga (£)", format="£%.2f")})
    st.download_button("Unduh CSV hasil filter", f[kolom].to_csv(index=False).encode("utf-8"),
                       file_name="buku_terfilter.csv", mime="text/csv")
with tab4:
    jumlah_scrape = riwayat["waktu_scrape"].nunique()
    st.write(f"Data sudah diambil {jumlah_scrape} kali.")
    if berubah.empty:
        st.info("Belum ada perubahan harga. Jalankan pipeline beberapa kali (misalnya harian) "
                "untuk melihat perubahan.")
    else:
        st.dataframe(berubah, hide_index=True, width="stretch")
        tren = riwayat.groupby("waktu_scrape")["harga"].mean().rename("harga rata-rata")
        st.line_chart(tren)

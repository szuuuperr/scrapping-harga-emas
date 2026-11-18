"""
Lapisan 4c: DASHBOARD STREAMLIT (P16).

Jalankan: streamlit run app.py   -> http://localhost:8501
"""
import streamlit as st

import analisis
import db

st.set_page_config(page_title="Dashboard Harga Emas", layout="wide", page_icon="🪙")


@st.cache_data(ttl=600)  # data dimuat ulang paling sering 10 menit sekali
def muat():
    return analisis.bersihkan(db.baca_emas()), db.riwayat(), db.perubahan_harga()


df, riwayat, berubah = muat()
st.title("🪙 Dashboard Harga Emas")

if df.empty:
    st.warning("Database masih kosong. Jalankan `python main.py` dulu.")
    st.stop()

st.caption(f"Sumber: harga-emas.org · data terakhir {df['terakhir_dilihat'].max()}")

# ---------- Filter di sidebar ----------
st.sidebar.header("Filter")
semua_berat = sorted(df["berat_gram"].unique())
pilih_berat = st.sidebar.multiselect(
    "Denominasi (gram)", semua_berat,
    placeholder="Semua denominasi",
    format_func=lambda x: f"{x}g")

semua_tanggal = sorted(df["tanggal"].unique())
if len(semua_tanggal) > 1:
    pilih_tanggal = st.sidebar.select_slider(
        "Rentang tanggal",
        options=semua_tanggal,
        value=(semua_tanggal[0], semua_tanggal[-1]))
else:
    pilih_tanggal = (semua_tanggal[0], semua_tanggal[0])

kata = st.sidebar.text_input("Cari (tanggal/denominasi)")

f = df[df["tanggal"].between(*pilih_tanggal)]
if pilih_berat:
    f = f[f["berat_gram"].isin(pilih_berat)]
if kata:
    f = f[f.apply(lambda row: kata.lower() in str(row.values).lower(), axis=1)]

if f.empty:
    st.info("Tidak ada data yang cocok dengan filter.")
    st.stop()

# ---------- Metrik ----------
r = analisis.ringkasan(f)
c1, c2, c3, c4 = st.columns(4)

harga_1g = r["harga_1g_terakhir"]
c1.metric("Harga 1g", f"Rp{harga_1g:,.0f}" if harga_1g else "-")

buyback = r["buyback_terakhir"]
c2.metric("Buyback 1g", f"Rp{buyback:,.0f}" if buyback else "-")

spread = r["spread_1g"]
c3.metric("Spread 1g", f"Rp{spread:,.0f}" if spread else "-")

c4.metric("Jumlah Data", f"{r['jumlah_data']:,}")

# ---------- Grafik dan tabel ----------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Tren Harga", "💎 Spread", "📊 Data", "🔄 Perubahan Harga"])

with tab1:
    st.subheader("Tren Harga Emas 1 Gram")
    tren_df = analisis.q1_tren_harga(f)
    if not tren_df.empty:
        st.line_chart(tren_df.set_index("tanggal")[["harga_jual", "harga_buyback"]])
    else:
        st.info("Belum cukup data untuk tren.")

    st.subheader("Harga per Gram per Denominasi")
    efisiensi = analisis.q3_harga_per_gram(f)
    if not efisiensi.empty:
        st.bar_chart(efisiensi.assign(
            denominasi=lambda d: d["berat_gram"].apply(lambda x: f"{x}g")
        ).set_index("denominasi")["harga_per_gram"])

with tab2:
    st.subheader("Spread (Jual - Buyback) per Denominasi")
    spread_df = analisis.q2_spread_per_denominasi(f)
    if not spread_df.empty:
        st.dataframe(spread_df.assign(
            berat=lambda d: d["berat_gram"].apply(lambda x: f"{x}g")
        ), hide_index=True)
        st.bar_chart(spread_df.assign(
            denominasi=lambda d: d["berat_gram"].apply(lambda x: f"{x}g")
        ).set_index("denominasi")["rata_rata"])
    else:
        st.info("Data buyback belum tersedia.")

with tab3:
    kolom = ["tanggal", "berat_gram", "harga_jual", "harga_per_gram", "harga_buyback"]
    kolom_ada = [k for k in kolom if k in f.columns]
    st.dataframe(
        f[kolom_ada].sort_values(["tanggal", "berat_gram"], ascending=[False, True]),
        hide_index=True, use_container_width=True,
        column_config={
            "harga_jual": st.column_config.NumberColumn("Harga Jual", format="Rp%,.0f"),
            "harga_per_gram": st.column_config.NumberColumn("Per Gram", format="Rp%,.0f"),
            "harga_buyback": st.column_config.NumberColumn("Buyback", format="Rp%,.0f"),
        })
    st.download_button("Unduh CSV", f[kolom_ada].to_csv(index=False).encode("utf-8"),
                       file_name="harga_emas.csv", mime="text/csv")

with tab4:
    jumlah_tanggal = df["tanggal"].nunique()
    st.write(f"Data tersedia untuk {jumlah_tanggal} tanggal.")
    if berubah.empty:
        st.info("Belum ada perubahan harga. Jalankan pipeline beberapa kali (misalnya harian) "
                "untuk melihat perubahan.")
    else:
        st.dataframe(berubah, hide_index=True, use_container_width=True)
        # Tren rata-rata harga per tanggal
        tren_rata = riwayat.groupby("tanggal")["harga_jual"].mean().rename("rata-rata harga jual")
        st.line_chart(tren_rata)

"""
Teks balasan bot. Fungsi murni (tanpa Telegram) agar mudah diuji dengan pytest,
sama seperti logika.py di praktikum bot.
"""
import re

BANTUAN = (
    "Perintah yang tersedia:\n"
    "/ringkas - ringkasan harga emas terkini\n"
    "/harga <berat> - harga emas per denominasi (misal: /harga 5)\n"
    "/tren - grafik tren harga emas\n"
    "/spread - spread jual-buyback per denominasi\n"
    "/berubah - denominasi yang harganya berubah\n"
    "/langganan - laporan harian pukul 07.00 WIB\n"
    "/berhenti - hentikan laporan harian\n"
    "/help - bantuan ini"
)


def format_rupiah(angka):
    """Format angka ke string Rupiah."""
    if angka is None:
        return "-"
    return f"Rp{angka:,.0f}".replace(",", ".")


def format_ringkasan(r, temuan):
    baris = [
        "📊 Ringkasan Harga Emas",
        f"Harga 1 gram   : {format_rupiah(r['harga_1g_terakhir'])}",
        f"Buyback 1 gram : {format_rupiah(r['buyback_terakhir'])}",
        f"Spread 1 gram  : {format_rupiah(r['spread_1g'])}",
        f"Jumlah data    : {r['jumlah_data']}",
        f"Denominasi     : {r['jumlah_denominasi']}",
        "",
        "🔍 Temuan:",
    ]
    baris += [f"{i}. {t}" for i, t in enumerate(temuan, 1)]
    return "\n".join(baris)


def format_daftar_harga(df, judul):
    """df berisi kolom berat_gram, harga_jual, harga_per_gram. Kembalikan teks."""
    if df.empty:
        return "Tidak ada data harga."
    baris = [judul]
    for _, b in df.iterrows():
        baris.append(
            f"• {b['berat_gram']:.1f}g — Jual: {format_rupiah(b['harga_jual'])} "
            f"(per gram: {format_rupiah(b.get('harga_per_gram'))})"
        )
    return "\n".join(baris)


def format_perubahan(df, batas=10):
    if df.empty:
        return "Belum ada perubahan harga sejak scrape sebelumnya."
    baris = [f"💰 {len(df)} denominasi berubah harga:"]
    for _, b in df.head(batas).iterrows():
        arah = "📉 turun" if b["selisih"] < 0 else "📈 naik"
        baris.append(
            f"• {b['berat_gram']:.1f}g: {format_rupiah(b['harga_lama'])} → "
            f"{format_rupiah(b['harga_baru'])} ({arah} {format_rupiah(abs(b['selisih']))})"
        )
    return "\n".join(baris)


def cocokkan_berat(teks, semua_berat):
    """Cari berat denominasi dari input teks. None jika tidak cocok."""
    teks = teks.strip().lower()
    # Bersihkan imbuhan kata seperti gram, gr, g
    teks = re.sub(r"\b(gram|gr)\b", "", teks)
    teks = re.sub(r"(?<=\d)g\b", "", teks)
    teks = teks.replace(",", ".").strip()
    try:
        berat = float(teks)
    except ValueError:
        return None
    for b in semua_berat:
        if abs(b - berat) < 0.01:
            return b
    return None

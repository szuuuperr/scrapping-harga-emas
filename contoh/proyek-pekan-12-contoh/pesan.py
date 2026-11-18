"""
Teks balasan bot. Fungsi murni (tanpa Telegram) agar mudah diuji dengan pytest,
sama seperti logika.py di praktikum bot.
"""
BANTUAN = (
    "Perintah yang tersedia:\n"
    "/ringkas - ringkasan katalog\n"
    "/cari <kata> - cari buku berdasarkan judul\n"
    "/kategori <nama> - 5 buku termurah di kategori\n"
    "/grafik - kirim grafik analisis\n"
    "/berubah - buku yang harganya berubah\n"
    "/langganan - laporan harian pukul 07.00 WIB\n"
    "/berhenti - hentikan laporan harian\n"
    "/help - bantuan ini"
)


def format_ringkasan(r, temuan):
    baris = [
        "Ringkasan katalog buku",
        f"Jumlah buku    : {r['jumlah_buku']}",
        f"Kategori       : {r['jumlah_kategori']}",
        f"Harga rata-rata: £{r['harga_rata']:.2f}",
        f"Rentang harga  : £{r['harga_min']:.2f} - £{r['harga_maks']:.2f}",
        f"Tersedia       : {r['persen_tersedia']}%",
        "",
        "Temuan:",
    ]
    baris += [f"{i}. {t}" for i, t in enumerate(temuan, 1)]
    return "\n".join(baris)


def format_daftar_buku(df, judul):
    """df berisi kolom judul, harga, rating. Kembalikan teks bernomor."""
    if df.empty:
        return "Tidak ada buku yang cocok."
    baris = [judul]
    for i, b in enumerate(df.itertuples(), 1):
        baris.append(f"{i}. {b.judul} - £{b.harga:.2f} ({'★' * int(b.rating)})")
    return "\n".join(baris)


def format_perubahan(df, batas=10):
    if df.empty:
        return "Belum ada perubahan harga sejak scrape sebelumnya."
    baris = [f"{len(df)} buku berubah harga:"]
    for b in df.head(batas).itertuples():
        arah = "turun" if b.selisih < 0 else "naik"
        baris.append(f"• {b.judul}: £{b.harga_lama:.2f} → £{b.harga_baru:.2f} ({arah})")
    return "\n".join(baris)


def cocokkan_kategori(nama, semua):
    """Cari nama kategori tanpa peduli huruf besar/kecil. None jika tidak ada."""
    nama = nama.strip().lower()
    for k in semua:
        if k.lower() == nama:
            return k
    awalan = [k for k in semua if k.lower().startswith(nama)]
    return awalan[0] if len(awalan) == 1 else None

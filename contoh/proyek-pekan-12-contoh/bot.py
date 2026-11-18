"""
Lapisan 4b: BOT TELEGRAM (P16) - asisten data katalog buku.

Bot membaca database yang sama dengan pipeline (data/buku.db),
jadi jalankan main.py minimal sekali sebelum menyalakan bot.

Jalankan: python bot.py   (hentikan dengan Ctrl+C)
"""
import datetime
import logging
from zoneinfo import ZoneInfo

from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import analisis
import config
import db
import pesan

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("pantaubuku")

WIB = ZoneInfo("Asia/Jakarta")


def muat():
    """Baca data terbaru setiap kali dipakai, agar hasil pipeline baru langsung terlihat."""
    return analisis.bersihkan(db.baca_buku())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nama = update.effective_user.first_name
    await update.message.reply_text(
        f"Halo, {nama}! Aku PantauBuku, asisten data katalog buku.\n\n" + pesan.BANTUAN)


async def bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pesan.BANTUAN)


async def ringkas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = muat()
    if df.empty:
        await update.message.reply_text("Data belum ada. Jalankan python main.py dulu.")
        return
    await update.message.reply_text(
        pesan.format_ringkasan(analisis.ringkasan(df), analisis.temuan(df)))


async def cari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Contoh: /cari python")
        return
    kata = " ".join(context.args)
    hasil = db.cari(kata, batas=5)
    await update.message.reply_text(pesan.format_daftar_buku(hasil, f'Hasil pencarian "{kata}":'))


async def kategori(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = muat()
    semua = sorted(df["kategori"].unique())
    if not context.args:
        await update.message.reply_text("Contoh: /kategori travel\n\nKategori: " + ", ".join(semua))
        return
    nama = pesan.cocokkan_kategori(" ".join(context.args), semua)
    if nama is None:
        await update.message.reply_text("Kategori tidak ditemukan. Ketik /kategori untuk daftarnya.")
        return
    termurah = df[df["kategori"] == nama].nsmallest(5, "harga")
    await update.message.reply_text(pesan.format_daftar_buku(termurah, f"5 buku termurah di {nama}:"))


async def grafik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = muat()
    if df.empty:
        await update.message.reply_text("Data belum ada. Jalankan python main.py dulu.")
        return
    path = analisis.buat_grafik(df)
    for kunci, keterangan in [("kategori", "Kategori terbanyak"),
                              ("rating", "Harga menurut rating"),
                              ("termahal", "Kategori termahal")]:
        with open(path[kunci], "rb") as f:
            await update.message.reply_photo(f, caption=keterangan)


async def berubah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pesan.format_perubahan(db.perubahan_harga()))


# ---------- Notifikasi otomatis dengan JobQueue ----------
async def kirim_harian(context: ContextTypes.DEFAULT_TYPE):
    df = muat()
    teks = pesan.format_ringkasan(analisis.ringkasan(df), analisis.temuan(df))
    teks += "\n\n" + pesan.format_perubahan(db.perubahan_harga(), batas=5)
    await context.bot.send_message(chat_id=context.job.chat_id, text=teks)


async def langganan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    for job in context.job_queue.get_jobs_by_name(f"harian-{chat_id}"):
        job.schedule_removal()  # hindari langganan ganda
    jam, menit = map(int, config.JAM_JADWAL.split(":"))
    context.job_queue.run_daily(kirim_harian, time=datetime.time(jam, menit, tzinfo=WIB),
                                chat_id=chat_id, name=f"harian-{chat_id}")
    await update.message.reply_text(f"Siap! Laporan dikirim setiap hari pukul {config.JAM_JADWAL} WIB.")


async def berhenti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jobs = context.job_queue.get_jobs_by_name(f"harian-{update.effective_chat.id}")
    for job in jobs:
        job.schedule_removal()
    await update.message.reply_text("Langganan dihentikan." if jobs else "Kamu belum berlangganan.")


async def tak_dikenal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Perintah tidak dikenal. Ketik /help.")


async def saat_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Error saat memproses update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Maaf, terjadi kesalahan. Coba lagi.")


async def setelah_mulai(app: Application):
    await app.bot.set_my_commands([
        BotCommand("ringkas", "Ringkasan katalog"),
        BotCommand("cari", "Cari buku berdasarkan judul"),
        BotCommand("kategori", "Buku termurah per kategori"),
        BotCommand("grafik", "Grafik analisis"),
        BotCommand("berubah", "Buku yang berubah harga"),
        BotCommand("langganan", "Laporan harian"),
        BotCommand("help", "Bantuan"),
    ])


def buat_aplikasi(token):
    app = Application.builder().token(token).post_init(setelah_mulai).build()
    for nama, fungsi in [("start", start), ("help", bantuan), ("ringkas", ringkas),
                         ("cari", cari), ("kategori", kategori), ("grafik", grafik),
                         ("berubah", berubah), ("langganan", langganan), ("berhenti", berhenti)]:
        app.add_handler(CommandHandler(nama, fungsi))
    app.add_handler(MessageHandler(filters.COMMAND, tak_dikenal))  # paling akhir
    app.add_error_handler(saat_error)
    return app


def main():
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN belum diisi. Salin .env.example menjadi .env lalu isi tokennya.")
    app = buat_aplikasi(config.BOT_TOKEN)
    log.info("Bot berjalan. Tekan Ctrl+C untuk berhenti.")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()

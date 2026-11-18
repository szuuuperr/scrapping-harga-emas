"""
Lapisan 4a: LAPORAN OTOMATIS (P15) - Excel dan PDF di folder output/.
"""
from datetime import date

import pandas as pd
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XlImage
from openpyxl.styles import Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import analisis
import config


def buat_excel(df, grafik, folder=config.OUTPUT_DIR):
    nama = folder / f"laporan_{date.today():%Y-%m-%d}.xlsx"
    r = analisis.ringkasan(df)
    with pd.ExcelWriter(nama, engine="openpyxl") as w:
        pd.DataFrame(list(r.items()), columns=["Ukuran", "Nilai"]).to_excel(
            w, sheet_name="Ringkasan", index=False)
        analisis.q1_kategori_terbanyak(df).to_excel(w, sheet_name="Q1 Kategori", index=False)
        analisis.q2_harga_per_rating(df).to_excel(w, sheet_name="Q2 Rating", index=False)
        analisis.q3_kategori_termahal(df).to_excel(w, sheet_name="Q3 Termahal", index=False)
        df.sort_values("judul").to_excel(w, sheet_name="Data", index=False)

    # Rapikan tampilan dengan openpyxl
    wb = load_workbook(nama)
    for ws in wb.worksheets:
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="2563EB")
        ws.freeze_panes = "A2"
        for kolom in ws.columns:
            lebar = max(len(str(c.value or "")) for c in kolom[:200])
            ws.column_dimensions[kolom[0].column_letter].width = min(lebar + 2, 60)
    for sheet, kunci in [("Q1 Kategori", "kategori"), ("Q2 Rating", "rating"),
                         ("Q3 Termahal", "termahal")]:
        img = XlImage(grafik[kunci])
        img.width, img.height = 640, 400
        wb[sheet].add_image(img, "F2")
    wb.save(nama)
    return nama


def _tabel(df):
    t = Table([df.columns.tolist()] + df.astype(str).values.tolist(), hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    return t


def buat_pdf(df, grafik, folder=config.OUTPUT_DIR):
    nama = folder / f"laporan_{date.today():%Y-%m-%d}.pdf"
    g = getSampleStyleSheet()
    r = analisis.ringkasan(df)
    story = [
        Paragraph("Laporan Pemantauan Katalog Buku", g["Title"]),
        Paragraph(f"Tanggal: {date.today():%d-%m-%Y} &middot; Sumber: books.toscrape.com", g["Normal"]),
        Spacer(1, 10),
        Paragraph(
            f"Total {r['jumlah_buku']} buku dalam {r['jumlah_kategori']} kategori. "
            f"Harga rata-rata £{r['harga_rata']:.2f} (rentang £{r['harga_min']:.2f} sampai "
            f"£{r['harga_maks']:.2f}); {r['persen_tersedia']}% buku tersedia.", g["Normal"]),
        Spacer(1, 10),
        Paragraph("Temuan utama", g["Heading2"]),
    ]
    story += [Paragraph(f"{i}. {t}", g["Normal"]) for i, t in enumerate(analisis.temuan(df), 1)]
    for judul, kunci, tabel in [
        ("1. Kategori dengan buku terbanyak", "kategori", analisis.q1_kategori_terbanyak(df, 5)),
        ("2. Harga menurut rating", "rating", analisis.q2_harga_per_rating(df)),
        ("3. Kategori dengan rata-rata harga tertinggi", "termahal", analisis.q3_kategori_termahal(df, 5)),
    ]:
        story += [Spacer(1, 12), Paragraph(judul, g["Heading2"]),
                  Image(str(grafik[kunci]), width=420, height=262), Spacer(1, 6), _tabel(tabel)]
    SimpleDocTemplate(str(nama), pagesize=A4, title="Laporan Katalog Buku").build(story)
    return nama

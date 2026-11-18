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
        analisis.q1_tren_harga(df).to_excel(w, sheet_name="Q1 Tren", index=False)
        analisis.q2_spread_per_denominasi(df).to_excel(w, sheet_name="Q2 Spread", index=False)
        analisis.q3_harga_per_gram(df).to_excel(w, sheet_name="Q3 Efisiensi", index=False)
        df.sort_values(["tanggal", "berat_gram"], ascending=[False, True]).to_excel(
            w, sheet_name="Data", index=False)

    # Rapikan tampilan dengan openpyxl
    wb = load_workbook(nama)
    for ws in wb.worksheets:
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="D4A017")
        ws.freeze_panes = "A2"
        for kolom in ws.columns:
            lebar = max(len(str(c.value or "")) for c in kolom[:200])
            ws.column_dimensions[kolom[0].column_letter].width = min(lebar + 2, 60)
    for sheet, kunci in [("Q1 Tren", "tren"), ("Q2 Spread", "spread"),
                         ("Q3 Efisiensi", "efisiensi")]:
        img = XlImage(grafik[kunci])
        img.width, img.height = 640, 400
        wb[sheet].add_image(img, "F2")
    wb.save(nama)
    return nama


def _tabel(df):
    t = Table([df.columns.tolist()] + df.astype(str).values.tolist(), hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D4A017")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    return t


def buat_pdf(df, grafik, folder=config.OUTPUT_DIR):
    nama = folder / f"laporan_{date.today():%Y-%m-%d}.pdf"
    g = getSampleStyleSheet()
    r = analisis.ringkasan(df)
    harga_1g = f"Rp{r['harga_1g_terakhir']:,.0f}" if r["harga_1g_terakhir"] else "-"
    buyback = f"Rp{r['buyback_terakhir']:,.0f}" if r["buyback_terakhir"] else "-"
    story = [
        Paragraph("Laporan Pemantauan Harga Emas", g["Title"]),
        Paragraph(f"Tanggal: {date.today():%d-%m-%Y} &middot; Sumber: harga-emas.org",
                  g["Normal"]),
        Spacer(1, 10),
        Paragraph(
            f"Total {r['jumlah_data']} data dari {r['jumlah_tanggal']} tanggal, "
            f"{r['jumlah_denominasi']} denominasi. "
            f"Harga emas 1 gram: {harga_1g} (buyback: {buyback}).",
            g["Normal"]),
        Spacer(1, 10),
        Paragraph("Temuan utama", g["Heading2"]),
    ]
    story += [Paragraph(f"{i}. {t}", g["Normal"])
              for i, t in enumerate(analisis.temuan(df), 1)]
    for judul, kunci, tabel in [
        ("1. Tren Harga Emas 1 Gram", "tren", analisis.q1_tren_harga(df).tail(10)),
        ("2. Spread per Denominasi", "spread", analisis.q2_spread_per_denominasi(df)),
        ("3. Harga per Gram per Denominasi", "efisiensi", analisis.q3_harga_per_gram(df)),
    ]:
        story += [Spacer(1, 12), Paragraph(judul, g["Heading2"]),
                  Image(str(grafik[kunci]), width=420, height=262),
                  Spacer(1, 6), _tabel(tabel)]
    SimpleDocTemplate(str(nama), pagesize=A4, title="Laporan Harga Emas").build(story)
    return nama

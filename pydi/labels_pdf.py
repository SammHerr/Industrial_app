"""Etiquetas A4 imprimibles de códigos persistentes; reimprimir nunca escribe DB."""

from io import BytesIO
from pathlib import Path

from reportlab.graphics.barcode.code128 import Code128
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from pydi.code_generator import normalize_code, qr_png
from pydi.inventory_service import InventoryError, get_record


def _font() -> str:
    for path in (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ):
        if path.is_file():
            if "IndustrialAppSans" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("IndustrialAppSans", str(path)))
            return "IndustrialAppSans"
    return "Helvetica"


def _fit(value: str, font: str, size: float, width: float) -> str:
    text = str(value or "")
    while text and pdfmetrics.stringWidth(text, font, size) > width:
        text = text[:-1]
    return text if text == value else text.rstrip() + "..."


def labels_pdf(codes: list[str], *, path: Path | None = None) -> bytes:
    unique = list(dict.fromkeys(normalize_code(code) for code in codes))
    if not unique or len(unique) > 200:
        raise InventoryError("Seleccione entre 1 y 200 códigos por PDF.")
    rows = []
    for code in unique:
        row = get_record(code, path)
        if row is None:
            raise InventoryError(f"Código inexistente para etiqueta: {code}.")
        rows.append(row)
    rows.sort(key=lambda row: (row["category"], row["name"], row["presentation"] or "", row["lot_code"] or "", row["code"]))
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4, pageCompression=1)
    pdf.setTitle("Etiquetas internas Industrial App")
    font = _font()
    page_w, page_h = A4
    margin_x, margin_y, gap_x, gap_y = 10 * mm, 11 * mm, 4 * mm, 4 * mm
    cell_w = (page_w - 2 * margin_x - gap_x) / 2
    cell_h = (page_h - 2 * margin_y - 4 * gap_y) / 5
    for index, row in enumerate(rows):
        if index and index % 10 == 0:
            pdf.showPage()
        slot = index % 10
        col, line = slot % 2, slot // 2
        x = margin_x + col * (cell_w + gap_x)
        y = page_h - margin_y - (line + 1) * cell_h - line * gap_y
        pdf.setStrokeColor(colors.Color(0.18, 0.25, 0.32))
        pdf.setLineWidth(0.4)
        pdf.rect(x, y, cell_w, cell_h)
        right_x = x + 38 * mm
        right_w = cell_w - 41 * mm
        pdf.setFont(font, 8.5)
        pdf.drawString(x + 3 * mm, y + cell_h - 6 * mm, _fit(row["name"], font, 8.5, cell_w - 6 * mm))
        pdf.setFont(font, 7)
        description = row["presentation"] or row["category"]
        pdf.drawString(x + 3 * mm, y + cell_h - 11 * mm, _fit(description, font, 7, cell_w - 6 * mm))
        lot = f"Lote: {row['lot_code']}" if row["lot_code"] else "Activo físico" if row["category"] == "Maquinaria" else "Sin lote"
        pdf.drawString(x + 3 * mm, y + cell_h - 15 * mm, _fit(lot, font, 7, cell_w - 6 * mm))
        pdf.drawImage(ImageReader(BytesIO(qr_png(row["code"]))), x + 3 * mm, y + 3 * mm, width=30 * mm, height=30 * mm)
        barcode = Code128(row["code"], barWidth=0.28 * mm, barHeight=13 * mm, humanReadable=False)
        scale = min(1.0, right_w / barcode.width)
        pdf.saveState()
        pdf.translate(right_x + (right_w - barcode.width * scale) / 2, y + 15 * mm)
        pdf.scale(scale, 1)
        barcode.drawOn(pdf, 0, 0)
        pdf.restoreState()
        pdf.setFont(font, 7.2)
        pdf.drawCentredString(right_x + right_w / 2, y + 10 * mm, row["code"])
        pdf.setFont(font, 6)
        pdf.drawString(right_x, y + 5 * mm, "Código interno Code 128 / QR")
    pdf.save()
    return output.getvalue()

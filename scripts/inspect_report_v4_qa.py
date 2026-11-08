"""Inspección reproducible de los dos PDF V4, sin acceder a SQLite."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

from pydi.reporting.sections import SECTION_SPECS


def inspect_pdf(path: Path, output: Path) -> tuple[int, int]:
    doc = pymupdf.open(path)
    assert doc.is_pdf and doc.page_count > 39, path
    assert not doc.is_encrypted, path
    texts = [page.get_text() for page in doc]
    full = "\n".join(texts)
    for spec in SECTION_SPECS:
        assert f"{spec.number}. {spec.title}" in full, (path, spec.number)
    assert "Índice" in full and "Resumen ejecutivo" in full
    assert "Glosario y bibliografía metodológica" in full
    assert all(len(text.strip()) > 250 for text in texts), path
    # El texto normal y sus rótulos deben permanecer en la caja de impresión A4.
    for page_number, page in enumerate(doc, 1):
        assert abs(page.rect.width - 595.28) < 1 and abs(page.rect.height - 841.89) < 1
        for block in page.get_text("blocks"):
            if block[6] != 0:
                continue
            x0, y0, x1, y1 = block[:4]
            assert x0 >= 16 and x1 <= page.rect.width - 15, (path, page_number, block[:4])
            assert y0 >= 16 and y1 <= page.rect.height - 15, (path, page_number, block[:4])
    output.mkdir(parents=True, exist_ok=True)
    for first in range(0, doc.page_count, 12):
        pages = list(range(first, min(first + 12, doc.page_count)))
        sheet = Image.new("RGB", (4 * 310, 3 * 460), "#e8eef2")
        draw = ImageDraw.Draw(sheet)
        for slot, index in enumerate(pages):
            pix = doc[index].get_pixmap(matrix=pymupdf.Matrix(0.7, 0.7), alpha=False)
            thumb = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            thumb.thumbnail((292, 414))
            x = (slot % 4) * 310 + (310 - thumb.width) // 2
            y = (slot // 4) * 460 + 20
            sheet.paste(thumb, (x, y))
            draw.text(((slot % 4) * 310 + 10, (slot // 4) * 460 + 438), f"{path.stem} · p. {index + 1}", fill="#17324d")
        sheet.save(output / f"{path.stem}_contacto_{first // 12 + 1:02d}.png")
    return doc.page_count, min(len(text.strip()) for text in texts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for mode in ("Base", "Personalizado"):
        path = args.input / f"Industrial_App_V4_{mode}.pdf"
        pages, minimum = inspect_pdf(path, args.output)
        print(f"{path.name}: {pages} páginas; mínimo {minimum} caracteres/página; {math.ceil(pages / 12)} hojas de contacto")


if __name__ == "__main__":
    main()

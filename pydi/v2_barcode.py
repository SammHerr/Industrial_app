"""Etiqueta Code 128 vectorial para identificadores de demostración o capturados."""

from io import BytesIO

from barcode import Code128
from barcode.writer import SVGWriter


def code128_svg(value: str) -> bytes:
    """Codifica texto no vacío como SVG legible por lector Code 128."""
    if not value or not value.strip():
        raise ValueError("El identificador Code 128 no puede estar vacío.")
    output = BytesIO()
    Code128(value, writer=SVGWriter()).write(output, options={"write_text": True})
    return output.getvalue()

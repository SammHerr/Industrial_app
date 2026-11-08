"""Etiqueta Code 128 vectorial para identificadores de demostración o capturados."""

from io import BytesIO

from barcode import Code128
from barcode.writer import ImageWriter, SVGWriter


def _validated(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("El identificador Code 128 no puede estar vacío.")
    return value


def code128_svg(value: str) -> bytes:
    """Codifica texto no vacío como SVG legible por lector Code 128."""
    output = BytesIO()
    Code128(_validated(value), writer=SVGWriter()).write(output, options={"write_text": True})
    return output.getvalue()


def code128_preview_png(value: str) -> bytes:
    """Genera una vista previa raster que Streamlit y Pillow pueden abrir."""
    output = BytesIO()
    Code128(_validated(value), writer=ImageWriter()).write(output, options={"write_text": True})
    return output.getvalue()

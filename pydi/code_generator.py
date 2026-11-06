"""IDs internos opacos y representaciones QR/Code 128 del mismo texto."""

import re
import secrets
from io import BytesIO

import qrcode
from barcode import Code128
from barcode.writer import ImageWriter

PREFIX = {"Producto terminado": "PT", "Materia prima": "MP", "Maquinaria": "MQ"}
CODE_PATTERN = re.compile(r"^(PT|MP|MQ)-[0-9A-F]{20}$")


def new_code(category: str) -> str:
    if category not in PREFIX:
        raise ValueError("Categoría de trazabilidad desconocida.")
    return f"{PREFIX[category]}-{secrets.token_hex(10).upper()}"


def normalize_code(raw: str) -> str:
    code = raw.strip().upper() if isinstance(raw, str) else ""
    if not CODE_PATTERN.fullmatch(code):
        raise ValueError("Código inválido. Use el ID interno PT/MP/MQ de la etiqueta.")
    return code


def qr_png(code: str) -> bytes:
    code = normalize_code(code)
    image = qrcode.make(code, box_size=8, border=4)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def code128_png(code: str) -> bytes:
    code = normalize_code(code)
    output = BytesIO()
    Code128(code, writer=ImageWriter()).write(output, options={"write_text": True, "module_height": 12})
    return output.getvalue()

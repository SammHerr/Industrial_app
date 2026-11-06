"""Extrae únicamente tablas del caso para una semilla versionada y verificable."""

import json
from pathlib import Path

from docx import Document

SOURCE = Path("Paquete_Codex_Industrial_App_V2_SHA/referencias_v2/Proyecto PYDI (1)(1).docx")
TARGET = Path("pydi/data/word_tables.json")
TABLES = (0, 8, 9, 10, 11, 12, 16, 17, 18, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35)


def main() -> None:
    doc = Document(SOURCE)
    payload = {
        "source": str(SOURCE),
        "note": "Transcripción literal de celdas; revisar tipo y unidad antes de calcular.",
        "tables": {
            str(number): [[cell.text for cell in row.cells] for row in doc.tables[number].rows]
            for number in TABLES
        },
    }
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(TABLES)} tablas guardadas en {TARGET}")


if __name__ == "__main__":
    main()

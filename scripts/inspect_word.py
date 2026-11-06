"""Inspección reproducible de tablas y ecuaciones del Word PYDI, sin modificarlo."""

import argparse
from pathlib import Path

from docx import Document

DEFAULT = Path(
    "Paquete_Codex_Industrial_App_V2_SHA/referencias_v2/Proyecto PYDI (1)(1).docx"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=DEFAULT)
    parser.add_argument("--table", type=int)
    parser.add_argument("--find")
    parser.add_argument("--equations", action="store_true")
    args = parser.parse_args()
    document = Document(args.file)
    equations = document.element.xpath(".//*[local-name()='oMath']")
    print(f"Párrafos: {len(document.paragraphs)} | tablas: {len(document.tables)} | OMML: {len(equations)}")
    if args.table is not None:
        table = document.tables[args.table]
        for index, row in enumerate(table.rows):
            print(index, " | ".join(cell.text.replace("\n", " / ") for cell in row.cells))
    elif args.find:
        needle = args.find.casefold()
        for index, paragraph in enumerate(document.paragraphs):
            if needle in paragraph.text.casefold():
                print("P", index, paragraph.text[:500])
        for index, table in enumerate(document.tables):
            if needle in " ".join(cell.text for row in table.rows for cell in row.cells).casefold():
                print("T", index, len(table.rows), len(table.columns))
    elif args.equations:
        for index, equation in enumerate(equations):
            print(index, " ".join(equation.itertext())[:500])
    else:
        for index, table in enumerate(document.tables):
            sample = " | ".join(
                " / ".join(cell.text.replace("\n", " ")[:45] for cell in row.cells[:4])
                for row in table.rows[:2]
            )
            print(index, len(table.rows), len(table.columns), sample[:280])


if __name__ == "__main__":
    main()

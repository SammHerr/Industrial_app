"""Genera muestras reproducibles V4 sin abrir SQLite.

Uso: python -m scripts.generate_report_v4_qa --output RUTA_TEMPORAL
Los valores personalizados son sintéticos y solo sirven para la QA del PDF.
"""

import argparse
from pathlib import Path

import pandas as pd

from pydi.reporting import ReportInfo, build_report_pdf, select_case
from pydi.reporting.validation import BASE_MODE, CUSTOM_MODE
from pydi.v2_model import make_empty_case, make_example_case


def make_custom_qa_case():
    case = make_example_case()
    case.tables["ingredientes"].loc[0, "kg_lote"] = 4.0
    case.tables["ingredientes"].loc[1, "kg_lote"] = 5.8
    case.params.update({"lotes_propuestos_dia": 8.0, "precio_250_mxn": 36.0,
                        "cvu_250_mxn": 12.0, "ciclo_s": 9800.0,
                        "horizonte_anios": 5, "tasa_descuento": .10})
    case.tables["rutas_base"].loc[0, "distancia_m"] += 2.0
    case.tables["rutas_propuestas"].loc[0, "distancia_m"] -= 1.0
    case.tables["pareto"].loc[0, "min_dia"] = 80.0
    case.tables["cinco_s"].loc[:, "puntaje"] = 2.0
    case.tables["ishikawa"].loc[0, ["causa", "rutas_pareto"]] = ["Dosificación sin báscula calibrada", "B3, B4"]
    case.tables["ishikawa"].loc[1, ["causa", "rutas_pareto"]] = ["Traslado manual de charolas", "B5"]
    values = {
        "A": (100_000, 50_000, 8_000, 0, 5_000, 1_000, 0),
        "B": (130_000, 36_000, 7_000, 0, 8_000, 1_000, 20_000),
        "C": (120_000, 42_000, 7_500, 0, 6_000, 1_000, 10_000),
    }
    columns = ("inversion_mxn", "operacion_anual_mxn", "mantenimiento_anual_mxn",
               "reinversion_mxn", "residual_mxn", "disposicion_mxn", "ahorro_neto_anual_mxn")
    for index, row in case.tables["alternativas"].iterrows():
        for column, value in zip(columns, values[row["alternativa"]]):
            case.tables["alternativas"].at[index, column] = value
    case.tables["cualitativa"] = pd.DataFrame([
        ("Higiene", .6, 70, 90, 80, "0-100", "[M] QA sintética"),
        ("Ergonomía", .4, 65, 85, 75, "0-100", "[M] QA sintética"),
    ], columns=case.tables["cualitativa"].columns)
    case.tables["cronograma"].loc[:, "duracion_semanas"] = [2, 2, 1, 1, 2, 1, 1]
    case.tables["cronograma"].loc[:, "predecesoras"] = ["", "C1", "C1", "C2,C3", "C4", "C5", "C6"]
    case.tables["auditoria"].loc[0, ["numerador", "denominador"]] = [98, 100]
    case.modified_params.update({"lotes_propuestos_dia", "precio_250_mxn", "cvu_250_mxn", "ciclo_s"})
    case.modified_tables.update({"ingredientes", "rutas_base", "rutas_propuestas", "pareto", "cinco_s",
                                 "ishikawa", "alternativas", "cualitativa", "cronograma", "auditoria"})
    return case


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path, help="Carpeta de QA fuera del árbol versionado")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = (("Base", BASE_MODE, select_case(BASE_MODE, make_empty_case())),
             ("Personalizado", CUSTOM_MODE, select_case(CUSTOM_MODE, make_custom_qa_case())))
    for label, mode, case in cases:
        path = args.output / f"Industrial_App_V4_{label}.pdf"
        path.write_bytes(build_report_pdf(case, mode, ReportInfo(observations="Datos sintéticos de QA" if label == "Personalizado" else "")))
        print(f"{path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

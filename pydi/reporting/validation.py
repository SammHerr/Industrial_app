"""Selección pura del escenario y control de vigencia de descargas."""

import hashlib
import json

from pydi.v2_model import Case, make_example_case

BASE_MODE = "Datos base PYDI"
CUSTOM_MODE = "Datos personalizados actuales"


def select_case(mode: str, current: Case) -> Case:
    """Devuelve una copia independiente, sin cambiar la sesión de Streamlit."""
    if mode == BASE_MODE:
        return make_example_case()
    if mode == CUSTOM_MODE:
        selected = current.copy()
        selected.mode = "Resultado calculado"
        return selected
    raise ValueError("Modalidad de reporte desconocida.")


def case_fingerprint(case: Case) -> str:
    """Detecta ediciones de parámetros, tablas y escenario antes de descargar."""
    payload = {
        "mode": case.mode,
        "version": case.version,
        "illustrative": case.illustrative,
        "params": case.params,
        "tables": {name: table.to_json(orient="split", date_format="iso", force_ascii=False)
                   for name, table in sorted(case.tables.items())},
        "modified_params": sorted(case.modified_params),
        "modified_tables": sorted(case.modified_tables),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()

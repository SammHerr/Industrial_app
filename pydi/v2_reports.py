"""Exportación integral desde el estado canónico y su snapshot actual."""

from io import BytesIO

import pandas as pd

from pydi.v2_model import Case
from pydi.v2_results import Snapshot, alerts_frame

SHEET_NAMES = {
    "ingredientes": "01 Ingredientes", "proceso": "02 Proceso", "localizacion": "03 Localización",
    "terrenos": "03 Terrenos", "emergencias": "03 Emergencias", "costos_fijos": "04 Costos fijos",
    "elementos": "05 Elementos", "siete_r": "06 Siete R", "pq": "07 PQ entradas",
    "fichas": "08 Fichas", "cargas": "09 Cargas", "contenedores": "10 Contenedores",
    "rutas_base": "12 Rutas base", "rutas_propuestas": "12 Rutas propuesta", "areas": "13 Áreas",
    "desperdicios": "14 Desperdicios", "mejoras": "15 Mejoras", "pareto": "16 Pareto entradas",
    "ishikawa": "17 Ishikawa", "cinco_s": "18 Cinco S", "principios": "19 Principios",
    "equipos": "20 Equipos", "dedicado": "21 Dedicado", "aleatorio": "22 Aleatorio",
    "estructuras": "23 Estructuras", "pedidos": "24 Pedidos", "identificaciones": "25 Identificación",
    "eventos": "26 Eventos", "muelles": "27 Muelles", "auxiliar": "28 Auxiliar",
    "operacion": "29 Operación", "planes": "30 Planes SHA", "metodos": "32 Métodos",
    "alternativas": "34 Alternativas", "cualitativa": "36 Cualitativa",
    "cronograma": "38 Cronograma", "auditoria": "39 Auditoría", "pdca": "39 PDCA",
}

PARAM_ORIGINS = {
    "turno_s": "[D] Word §2 p.11", "preparacion_s": "[D] Word §2 p.11",
    "comida_s": "[D] Word §2 p.11", "ciclo_s": "[D] Word §2 p.11",
    "lote_objetivo_kg": "[D] Word §1–2", "lotes_propuestos_dia": "[D] Word §12",
    "dias_mes": "[D] Word §2", "bolsas_250_lote": "[D] Word §2",
    "bolsas_500_lote": "[D] Word §2", "empaque_lote_mxn": "[D] Word §1 p.8", "cvu_250_mxn": "[D] Word §4",
    "precio_250_mxn": "[D] Word §4", "velocidad_m_s": "[S] Word §12",
    "carga_base_s": "[S] Word §12", "carga_propuesta_s": "[S] Word §12",
    "retorno_vacio_viajes": "[D] Word §31", "retorno_vacio_m": "[D] Word §31",
    "tarima_largo_cm": "[D] Word §10", "tarima_ancho_cm": "[D] Word §10",
    "caja_largo_cm": "[D] Word §10", "caja_ancho_cm": "[D] Word §10",
    "cajas_capa": "[D] Word §11", "capas": "[D] Word §11",
    "capacidad_tarima_kg": "[U] ficha de proveedor pendiente",
    "horizonte_anios": "[D] Word §34", "tasa_descuento": "[M/U] requerida para VPN",
    "tasa_sens_min": "[M] límite inferior ilustrativo", "tasa_sens_max": "[M] límite superior ilustrativo",
    "semana_referencia": "[D] Word §38", "factor_abc_a": "[M] umbral configurable",
    "factor_abc_b": "[M] umbral configurable",
}

FORMULAS = pd.DataFrame([
    ("§2", "T_disponible = T_turno - T_preparación - T_comida", "s/turno", "[D] OMML p.11"),
    ("§2", "Lotes_base = T_disponible / T_ciclo", "lotes/turno", "[D] OMML p.11"),
    ("§3", "P_j = suma(w_i × s_ij)", "puntos", "[D] OMML pp.18–19"),
    ("§4", "Qe = CF / (P - CVU)", "bolsas 250 g/mes", "[D] OMML pp.25–26"),
    ("§7", "kg/mes = kg/lote × lotes/día × días/mes", "kg/mes", "[D] tabla p.33"),
    ("§12", "T.W. = I × d", "kg·m/día", "[D] Word p.41"),
    ("§12", "D = viajes × d", "m/día", "[D] Word p.41"),
    ("§12", "T = viajes × (2d/v + carga)", "s/día", "[D/S] Word p.41"),
    ("§16", "% = minutos/total × 100; acumulado = suma de %", "%", "[C] álgebra del Pareto"),
    ("§18", "5S = puntos/40 × 100, solo con 20 respuestas", "%", "[D] Word pp.49–51"),
    ("§24", "cajas = techo(bolsas / capacidad de caja)", "cajas", "[M] complemento"),
    ("§27", "vehículos/turno = piso(T_operativo/T_servicio) × posiciones", "vehículos/turno", "[M] complemento"),
    ("§34", "LCC nominal = I0 + n(O+M) + R - residual + disposición", "MXN", "[M] complemento"),
    ("§34", "LCC descontado = I0 + suma((O+M)/(1+r)^t) + (R+disposición-residual)/(1+r)^n", "MXN presentes", "[M] complemento"),
    ("§35", "VPN = -I_adicional + suma(flujo_t/(1+r)^t)", "MXN presentes", "[M] complemento"),
    ("§35", "Payback = I_adicional/ahorro neto anual positivo", "años", "[M] complemento"),
    ("§36", "Puntuación = suma(peso × calificación)", "puntos", "[M] complemento"),
    ("§38", "CPM: ES/EF/LS/LF y holgura en grafo acíclico", "semanas", "[M] complemento"),
], columns=["apartado", "fórmula", "unidad", "procedencia"])


def export_xlsx(case: Case, snapshot: Snapshot) -> bytes:
    output = BytesIO()
    metadata = pd.DataFrame([
        ("Versión semilla", case.version, "[D]"),
        ("Escenario", case.mode, "[U]"),
        ("Ilustrativos activos", case.illustrative, "[M]"),
        ("Estado", "Sin datos" if not snapshot.metrics else "Parcial o calculado", "[C]"),
    ], columns=["campo", "valor", "origen"])
    params = pd.DataFrame([
        (key, value, "[U] editado; base " + PARAM_ORIGINS[key] if key in case.modified_params else PARAM_ORIGINS[key])
        for key, value in case.params.items()
    ], columns=["parámetro", "valor", "origen"])
    edits = pd.DataFrame(
        [("parámetro", key) for key in sorted(case.modified_params)]
        + [("tabla", key) for key in sorted(case.modified_tables)],
        columns=["tipo", "nombre"],
    )
    metric_rows = []
    for key, value in snapshot.metrics.items():
        if isinstance(value, (int, float, str)):
            metric_rows.append((key, value, "[C]"))
    sheets = {"00 Estado": metadata, "00 Parámetros": params, "00 Alertas": alerts_frame(snapshot), "00 Indicadores": pd.DataFrame(metric_rows, columns=["indicador", "valor", "origen"]), "00 Fórmulas": FORMULAS, "00 Ediciones": edits}
    for key, table in case.tables.items():
        sheets[SHEET_NAMES[key]] = table.copy()
    for name, table in snapshot.tables.items():
        sheet = "C " + name
        sheets[sheet[:31]] = table.copy()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, table in sheets.items():
            table.to_excel(writer, sheet_name=name[:31], index=False, na_rep="")
            ws = writer.sheets[name[:31]]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for column in ws.columns:
                values = [len(str(cell.value or "")) for cell in column[:100]]
                ws.column_dimensions[column[0].column_letter].width = min(55, max(12, max(values, default=10) + 2))
    return output.getvalue()

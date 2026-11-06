"""Estado canónico editable y fábricas puras de escenarios PYDI V2."""

import json
import re
from copy import deepcopy
from dataclasses import dataclass, field
from importlib.resources import files

import pandas as pd

from pydi import datos

SEED_VERSION = "PYDI-V2-2026-11-05"
SOURCE = "Proyecto PYDI (1)(1).docx"

TABLE_COLUMNS = {
    "ingredientes": ["codigo", "nombre", "kg_lote", "costo_kg_mxn", "origen"],
    "proceso": ["etapa", "duracion_s", "origen", "observacion"],
    "localizacion": ["factor", "peso", "Union Juarez", "Cacahoatan", "Tapachula", "origen"],
    "terrenos": ["terreno", "ubicacion", "costo_mxn", "area_m2", "origen"],
    "emergencias": ["servicio", "distancia_estimada_km", "tiempo_estimado_min", "importancia", "origen"],
    "costos_fijos": ["concepto", "mxn_mes", "origen"],
    "elementos": ["codigo", "nombre", "tipo", "unidad", "presentacion", "peso_aprox", "cantidad_utilizada", "ubicacion", "cantidad_actual", "origen"],
    "siete_r": ["criterio", "aplicacion", "situacion_base", "estado", "mejora", "evidencia", "origen"],
    "pq": ["material", "kg_mes_reportado", "kg_lote_equiv", "origen"],
    "fichas": ["codigo", "elemento", "categoria", "especificacion", "dato_pendiente", "origen"],
    "cargas": ["clave", "carga", "composicion", "peso_bruto", "dimensiones", "equipo", "justificacion", "origen"],
    "contenedores": ["elemento", "dimensiones", "capacidad", "material", "cantidad", "justificacion", "origen"],
    "rutas_base": ["id", "movimiento", "origen_area", "destino_area", "kg_lote_equiv", "intensidad_manual_kg_dia", "viajes_dia", "distancia_m", "origen"],
    "rutas_propuestas": ["id", "movimiento", "origen_area", "destino_area", "kg_lote_equiv", "intensidad_manual_kg_dia", "viajes_dia", "distancia_m", "origen"],
    "areas": ["area", "clave", "superficie_m2", "funcion", "x_m", "y_m", "origen_posicion"],
    "desperdicios": ["desperdicio", "situacion_base", "evidencia", "accion_propuesta", "estado_implantacion", "origen"],
    "mejoras": ["aspecto", "base", "propuesta", "resultado_documental", "estado", "origen"],
    "pareto": ["causa", "min_dia", "rutas", "origen"],
    "ishikawa": ["categoria", "causa", "efecto", "rutas_pareto", "origen"],
    "cinco_s": ["numero", "s", "criterio", "puntaje", "observaciones", "origen"],
    "principios": ["principio", "definicion", "situacion", "aplicacion", "estado", "evidencia", "origen"],
    "equipos": ["codigo", "equipo", "cantidad_documental", "especificacion", "justificacion", "costo_mxn", "origen"],
    "dedicado": ["ubicacion", "material", "posiciones_totales", "posiciones_ocupadas", "alergeno", "regla_rotacion", "origen"],
    "aleatorio": ["ubicacion", "lote", "posiciones_totales", "posiciones_ocupadas", "fecha_entrada", "origen"],
    "estructuras": ["estructura", "largo_m", "fondo_m", "alto_m", "capacidad_nominal_kg", "carga_prevista_kg", "origen"],
    "pedidos": ["pedido", "bolsas_250", "bolsas_500", "cajas_250", "cajas_500", "distancia_m", "origen"],
    "identificaciones": ["codigo", "lote", "ubicacion", "tipo", "origen"],
    "eventos": ["evento", "fecha", "codigo", "lote", "origen_area", "destino_area", "cantidad", "unidad", "origen"],
    "muelles": ["muelle", "posiciones", "tiempo_operativo_s", "tiempo_vehiculo_s", "demanda_vehiculos", "ancho_m", "origen"],
    "auxiliar": ["equipo", "cantidad", "capacidad", "mantenimiento", "costo_mxn", "origen"],
    "operacion": ["etapa", "responsable", "metodo", "frecuencia", "regla", "riesgo", "origen"],
    "planes": ["alternativa", "metodo", "equipo", "restricciones", "estado", "origen"],
    "metodos": ["ruta", "equipo_candidato", "capacidad_kg", "higiene_verificada", "ergonomia_verificada", "costo_mxn", "justificacion", "origen"],
    "alternativas": ["alternativa", "inversion_mxn", "operacion_anual_mxn", "mantenimiento_anual_mxn", "reinversion_mxn", "residual_mxn", "disposicion_mxn", "ahorro_neto_anual_mxn", "origen"],
    "cualitativa": ["factor", "peso", "A", "B", "C", "escala", "origen"],
    "cronograma": ["id", "actividad", "duracion_semanas", "predecesoras", "inicio_referencia", "fin_referencia", "origen"],
    "auditoria": ["indicador", "formula", "meta", "sentido", "frecuencia", "responsable", "accion", "numerador", "denominador", "medicion", "origen"],
    "pdca": ["hallazgo", "responsable", "fecha_compromiso", "accion", "verificacion", "estado", "origen"],
}

PARAM_NAMES = (
    "turno_s", "preparacion_s", "comida_s", "ciclo_s", "lote_objetivo_kg",
    "lotes_propuestos_dia", "dias_mes", "bolsas_250_lote", "bolsas_500_lote",
    "empaque_lote_mxn", "cvu_250_mxn", "precio_250_mxn", "velocidad_m_s", "carga_base_s",
    "carga_propuesta_s", "retorno_vacio_viajes", "retorno_vacio_m",
    "tarima_largo_cm", "tarima_ancho_cm", "caja_largo_cm", "caja_ancho_cm",
    "cajas_capa", "capas", "capacidad_tarima_kg", "horizonte_anios",
    "tasa_descuento", "tasa_sens_min", "tasa_sens_max", "semana_referencia", "factor_abc_a", "factor_abc_b",
)


@dataclass
class Case:
    mode: str
    params: dict[str, float | None]
    tables: dict[str, pd.DataFrame]
    version: str = SEED_VERSION
    illustrative: bool = False
    modified_params: set[str] = field(default_factory=set)
    modified_tables: set[str] = field(default_factory=set)

    def copy(self) -> "Case":
        return deepcopy(self)


def make_empty_case() -> Case:
    return Case(
        mode="Nuevo estudio",
        params={name: None for name in PARAM_NAMES},
        tables={name: pd.DataFrame(columns=columns) for name, columns in TABLE_COLUMNS.items()},
    )


def _word() -> dict[str, list[list[str]]]:
    path = files("pydi").joinpath("data/word_tables.json")
    return json.loads(path.read_text(encoding="utf-8"))["tables"]


def _number(value: str) -> float:
    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", value.replace("$", ""))
    if not match:
        raise ValueError(f"No se pudo interpretar el número documental: {value!r}")
    return float(match.group().replace(",", ""))


def _frame(rows: list, name: str) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=TABLE_COLUMNS[name])


def make_example_case() -> Case:
    """Semilla determinista: cifras [D/S] y plantillas [M] explícitas."""
    w = _word()
    case = make_empty_case()
    case.mode = "Documento (valores reportados)"
    case.illustrative = True
    case.params.update({
        "turno_s": 30600.0, "preparacion_s": 600.0, "comida_s": 1800.0,
        "ciclo_s": 10200.0, "lote_objetivo_kg": 10.0,
        "lotes_propuestos_dia": 7.75, "dias_mes": 26.0,
        "bolsas_250_lote": 32.0, "bolsas_500_lote": 4.0,
        "empaque_lote_mxn": 30.0, "cvu_250_mxn": 11.38, "precio_250_mxn": 35.0,
        "velocidad_m_s": 0.9, "carga_base_s": 30.0, "carga_propuesta_s": 45.0,
        "retorno_vacio_viajes": 2.0, "retorno_vacio_m": 31.5,
        "tarima_largo_cm": 120.0, "tarima_ancho_cm": 100.0,
        "caja_largo_cm": 40.0, "caja_ancho_cm": 33.0,
        "cajas_capa": 9.0, "capas": 5.0,
        "horizonte_anios": 8.0, "tasa_sens_min": 0.0, "tasa_sens_max": 0.2,
        "semana_referencia": 12.0,
        "factor_abc_a": 80.0, "factor_abc_b": 95.0,
    })
    case.tables["ingredientes"] = _frame([
        ("ASO-MP-001", "Avena", 3.5, 25.0, "[D] Word tabla 1 p.8"),
        ("ASO-MP-002", "Soya", 6.0, 40.0, "[D] Word tabla 1 p.8"),
        ("ASO-MP-003", "Cacahuate", 2.0, 45.0, "[D] Word tabla 1 p.8"),
        ("ASO-MP-004", "Canela", 0.25, 30.0, "[D] Word tabla 1 p.8"),
    ], "ingredientes")
    case.tables["proceso"] = _frame([
        (name, None, "[D] Word §2 pp.9–11", "Duración individual pendiente de desagregar")
        for name in ("Recepción", "Preparación", "Tostado", "Molienda", "Empaque", "Pesado", "Almacén PT")
    ], "proceso")
    case.tables["localizacion"] = _frame([
        (row[1], _number(row[2]), *(_number(x) for x in row[3:6]), "[D] Word §3 pp.18–19")
        for row in w["8"][2:7]
    ], "localizacion")
    case.tables["terrenos"] = _frame([
        (str(index), row[2].strip(), _number(row[3]), None, "[D] Word §3 pp.20–23")
        for index, row in enumerate(w["9"][2:5], 1)
    ], "terrenos")
    case.tables["emergencias"] = _frame([
        (row[0], row[1], row[2], row[3], "[S] Word §3 tabla distancias")
        for row in w["10"][2:]
    ], "emergencias")
    case.tables["costos_fijos"] = _frame([
        (row[0], _number(row[1]), "[D] Word §4 p.23") for row in w["16"][2:10]
    ], "costos_fijos")
    case.tables["elementos"] = _frame([
        (row[0], row[1], row[2], row[3], row[4], row[5], row[6], "", None, "[D/S] Word §5 pp.28–31")
        for row in w["17"][1:]
    ], "elementos")
    case.tables["siete_r"] = _frame([
        (row[0], row[1], row[2], row[3], row[4], "", "[D] Word §6 pp.31–33")
        for row in w["18"][1:]
    ], "siete_r")
    case.tables["pq"] = _frame([
        (row[0], _number(row[1]), _number(row[1]) / (7.75 * 26), "[D/C] Word §7 p.33")
        for row in w["19"][1:8]
    ], "pq")
    case.tables["fichas"] = _frame([
        (r[0], r[1], "Ingrediente", f"{r[2]} kg/lote; ${r[3]:g}/kg", "Ficha técnica completa", "[D] Word §1")
        for r in case.tables["ingredientes"].itertuples(index=False, name=None)
    ] + [
        (row[0], row[1], "Máquina", row[3], "Marca, modelo y ficha de proveedor", "[D/S] Word §20 pp.53–55")
        for row in w["31"][1:]
    ], "fichas")
    case.tables["cargas"] = _frame([(*row[:7], "[D/S] Word §9 pp.34–36") for row in w["20"][1:]], "cargas")
    case.tables["contenedores"] = _frame([(*row[:6], "[D/S] Word §10 pp.36–38") for row in w["21"][1:]], "contenedores")
    for key, index, method in (("rutas_base", "22", "Base"), ("rutas_propuestas", "23", "Propuesto")):
        ref = datos.rutas_iniciales(method).set_index("id")
        case.tables[key] = _frame([
            (row[0], row[1], ref.loc[row[0], "origen"], ref.loc[row[0], "destino"],
             _number(row[2]) / 7.75, None, _number(row[3]), _number(row[4]), "[D/C] Word §12 pp.40–43")
            for row in w[index][1:10]
        ], key)
    illustrative_positions = {
        "REC": (2, 16), "AMP": (7, 16), "PRE": (12, 16), "TOS": (17, 16),
        "MOL": (22, 16), "EMP": (25, 10), "APT": (20, 4), "EMB": (13, 4),
        "AIE": (28, 4), "—": (5, 5),
    }
    case.tables["areas"] = _frame([
        (row[0], row[1], _number(row[2]), row[3],
         illustrative_positions.get(row[1], (None, None))[0],
         illustrative_positions.get(row[1], (None, None))[1],
         "[M] posición ilustrativa; superficie [D]")
        for row in w["25"][1:]
    ], "areas")
    case.tables["desperdicios"] = _frame([
        (row[0], row[1], row[2], row[3], "No evaluado", "[D/S] Word §14 pp.45–46")
        for row in w["26"][1:]
    ], "desperdicios")
    case.tables["mejoras"] = _frame([
        (row[0], row[1], row[2], row[3], "No verificado", "[D] Word §15 pp.46–47")
        for row in w["27"][1:]
    ], "mejoras")
    case.tables["pareto"] = _frame([
        (row[0], _number(row[1]), re.search(r"\((B[^)]*)\)", row[0]).group(1) if "(B" in row[0] else "", "[D] Word §16 pp.47–48")
        for row in w["28"][1:8]
    ], "pareto")
    case.tables["ishikawa"] = _frame([
        (category, "", "Manejo lento y riesgo de merma", "", "[M] plantilla; causalidad no verificada")
        for category in ("Método", "Maquinaria/equipo", "Mano de obra", "Materiales", "Medición", "Medio ambiente")
    ], "ishikawa")
    categories = ("Seiri", "Seiton", "Seiso", "Seiketsu", "Shitsuke")
    case.tables["cinco_s"] = _frame([
        (index, categories[(index - 1) // 4], row[2], None, "", "[D] Word §18 pp.49–51")
        for index, row in enumerate(w["29"][1:21], 1)
    ], "cinco_s")
    case.tables["principios"] = _frame([
        (row[0], row[1], row[2], row[3], "No evaluado", "", "[D/S] Word §19 pp.51–53")
        for row in w["30"][1:]
    ], "principios")
    case.tables["equipos"] = _frame([
        (row[0], row[1], row[2], row[3], row[4], None, "[D/S] Word §20 pp.53–55")
        for row in w["31"][1:]
    ] + [
        (f"MAN-{i:02d}", row[0], row[1], row[2], row[4], None, "[D/S] Word §20 pp.53–55")
        for i, row in enumerate(w["32"][1:], 1)
    ], "equipos")
    case.tables["dedicado"] = _frame([
        (f"AMP-{name}", name, None, None, name in ("Soya", "Cacahuate"), "PEPS [M]", "[M] plantilla, sin inventario")
        for name in ("Soya", "Avena", "Cacahuate", "Canela")
    ], "dedicado")
    case.tables["aleatorio"] = _frame([("APT-A", "", None, None, "", "[M] plantilla")], "aleatorio")
    case.tables["estructuras"] = _frame([("Rack selectivo", None, None, None, None, None, "[M] medición pendiente")], "estructuras")
    case.tables["pedidos"] = _frame([], "pedidos")
    case.tables["identificaciones"] = _frame([
        ("ASO-PT-016", "PYDI-DEMO", "APT-A", "Code 128", "[M] etiqueta demostrativa; no es lote real")
    ], "identificaciones")
    case.tables["eventos"] = _frame([], "eventos")
    case.tables["muelles"] = _frame([("Muelle 1", None, None, None, None, None, "[M] ilustrativo, sin datos")], "muelles")
    case.tables["auxiliar"] = _frame([
        (row[0], row[1], row[2], "Pendiente", None, "[D/S] Word §20; mantenimiento pendiente")
        for row in w["32"][1:]
    ], "auxiliar")
    case.tables["operacion"] = _frame([
        (name, "Por asignar", "Propuesto", "Por definir", "PEPS/FEFO [M]", "Por evaluar", "[M] plantilla")
        for name in ("Recepción", "Preparación", "Tostado", "Molienda", "Empaque", "Almacén", "Embarque")
    ], "operacion")
    case.tables["planes"] = _frame([
        ("A", "Base", "Manejo actual", "Pendiente", "Documental", "[D] Word §37"),
        ("B", "Manual asistido", "Cargas unitarias y código de barras", "Cotizaciones pendientes", "Recomendada en Word", "[D] Word §37"),
        ("C", "Alternativa por evaluar", "Por definir", "Datos pendientes", "Sin evaluación", "[M] plantilla"),
    ], "planes")
    case.tables["metodos"] = _frame([], "metodos")
    case.tables["alternativas"] = _frame([
        (name, None, None, None, None, None, None, None, "[M] plantilla; cifras del Word no verificables")
        for name in ("A", "B", "C")
    ], "alternativas")
    case.tables["cualitativa"] = _frame([], "cualitativa")
    activities = ("Compra de equipo", "Instalación de rack", "Codificación", "Registro de inventarios", "Capacitación", "Prueba piloto", "Auditoría inicial")
    windows = ((1, 3), (3, 5), (5, 6), (6, 8), (8, 10), (10, 11), (12, 12))
    case.tables["cronograma"] = _frame([
        (f"C{i}", activity, None, "", start, end, "[M] ventana ilustrativa; 12 semanas [D]; red CPM pendiente")
        for i, (activity, (start, end)) in enumerate(zip(activities, windows), 1)
    ], "cronograma")
    case.tables["auditoria"] = _frame([
        (row[0], row[1], row[2], "≤" if "≤" in row[2] or row[2].strip().startswith("0") else "≥", row[3], row[4], row[5], None, None, None, "[D] Word §39 pp.59–61")
        for row in w["34"][1:]
    ], "auditoria")
    case.tables["pdca"] = _frame([], "pdca")
    return case


def without_illustrative_values(source: Case) -> Case:
    """Descarta plantillas [M] y campos ilustrativos sin tocar los datos [D/S]."""
    case = source.copy()
    for name, table in case.tables.items():
        if "origen" in table.columns:
            case.tables[name] = table.loc[~table["origen"].astype(str).str.startswith("[M]")].reset_index(drop=True)
    case.tables["areas"][["x_m", "y_m"]] = None
    case.tables["cronograma"][["inicio_referencia", "fin_referencia"]] = None
    case.params["factor_abc_a"] = None
    case.params["factor_abc_b"] = None
    case.params["tasa_sens_min"] = None
    case.params["tasa_sens_max"] = None
    case.illustrative = False
    return case

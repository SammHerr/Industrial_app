"""Relación declarativa entre los 39 apartados y el estado canónico."""

from dataclasses import dataclass

from pydi.section_catalog import SECTIONS


@dataclass(frozen=True)
class SectionSpec:
    number: int
    title: str
    inputs: tuple[str, ...]
    params: tuple[str, ...]
    results: tuple[str, ...]
    metrics: tuple[str, ...]
    charts: tuple[str, ...]
    interpretation: str


INPUTS = {
    1: ("ingredientes",), 2: ("proceso",), 3: ("localizacion", "terrenos", "emergencias"),
    4: ("costos_fijos",), 5: ("elementos",), 6: ("siete_r",), 7: ("pq",),
    8: ("fichas",), 9: ("cargas",), 10: ("contenedores",), 12: ("rutas_base", "rutas_propuestas"),
    13: ("areas",), 14: ("desperdicios",), 15: ("mejoras",), 16: ("pareto",),
    17: ("ishikawa",), 18: ("cinco_s",), 19: ("principios",), 20: ("equipos",),
    21: ("dedicado",), 22: ("aleatorio",), 23: ("estructuras",), 24: ("pedidos",),
    25: ("identificaciones",), 26: ("eventos",), 27: ("muelles",), 28: ("auxiliar",),
    29: ("operacion",), 30: ("planes",), 31: ("rutas_propuestas",), 32: ("metodos",),
    33: ("areas",), 34: ("alternativas",), 35: ("alternativas",), 36: ("cualitativa",),
    37: ("planes",), 38: ("cronograma",), 39: ("auditoria", "pdca"),
}

PARAMS = {
    1: ("lote_objetivo_kg", "empaque_lote_mxn"),
    2: ("turno_s", "preparacion_s", "comida_s", "ciclo_s", "lotes_propuestos_dia", "dias_mes", "bolsas_250_lote", "bolsas_500_lote"),
    4: ("cvu_250_mxn", "precio_250_mxn"),
    7: ("factor_abc_a", "factor_abc_b", "lotes_propuestos_dia", "dias_mes"),
    11: ("tarima_largo_cm", "tarima_ancho_cm", "caja_largo_cm", "caja_ancho_cm", "cajas_capa", "capas", "capacidad_tarima_kg"),
    12: ("lotes_propuestos_dia", "velocidad_m_s", "carga_base_s", "carga_propuesta_s"),
    27: (), 31: ("retorno_vacio_viajes", "retorno_vacio_m"),
    34: ("horizonte_anios", "tasa_descuento", "tasa_sens_min", "tasa_sens_max"),
    35: ("horizonte_anios", "tasa_descuento"), 38: ("semana_referencia",),
}

RESULTS = {
    1: ("Ingredientes calculados",), 3: ("Localización calculada",),
    7: ("P-Q calculado",), 12: ("TW base calculado", "TW propuesto calculado", "Comparación transporte"),
    15: ("Comparación transporte",), 16: ("Pareto calculado",),
    24: ("Picking calculado",), 30: ("PQRST consolidado",),
    31: ("TW propuesto calculado",), 34: ("LCC calculado", "Sensibilidad LCC"),
    36: ("Evaluación calculada",), 38: ("CPM calculado",), 39: ("Auditoría evaluada",),
}

METRICS = {
    1: ("masa_entrada_kg", "costo_ingredientes_mxn", "costo_total_lote_mxn"),
    2: ("capacidad", "produccion"), 3: ("localizacion",),
    4: ("costo_fijo_mxn_mes", "equilibrio"), 6: ("siete_r",),
    7: ("pq",), 11: ("estiba",), 12: ("comparacion_transporte",),
    16: ("pareto",), 18: ("cinco_s",), 24: ("picking",),
    34: (), 35: ("payback_b_vs_a_anios", "vpn_b_vs_a_mxn"),
    36: ("multicriterio",), 38: ("cpm",),
}

CHARTS = {
    2: ("production",), 3: ("location",), 4: ("equilibrium",),
    6: ("seven_r",), 7: ("pq",), 11: ("pallet",),
    12: ("transport",), 13: ("distance_intensity",), 16: ("pareto",),
    17: ("ishikawa",), 18: ("five_s",), 33: ("layout",),
    34: ("lcc", "sensitivity"), 36: ("qualitative",),
    38: ("gantt",), 39: ("audit",),
}

INTERPRETATIONS = {
    1: "La masa calculada procede de la receta capturada; la diferencia respecto al lote objetivo requiere explicación experimental.",
    2: "La capacidad base secuencial y la producción propuesta son escenarios distintos; no deben confundirse.",
    3: "La puntuación ponderada depende de los pesos y calificaciones capturados; las distancias de emergencia son estimaciones documentales.",
    4: "El punto de equilibrio se aplica únicamente a la bolsa de 250 g con precio y costo variable conocidos.",
    5: "El catálogo identifica elementos; una cantidad sin medición no equivale a inventario físico confirmado.",
    6: "Los estados de las 7 R describen la evaluación registrada, no certifican la implantación de mejoras.",
    7: "El P-Q calculado usa la receta y el ritmo actual del escenario; los umbrales ABC son complementarios.",
    8: "Las fichas incompletas requieren datos de proveedor antes de validar especificaciones.",
    9: "Las cargas unitarias son referencias de manejo que deben verificarse en operación.",
    10: "Las dimensiones y capacidades deben cotejarse con fichas técnicas del proveedor.",
    11: "La rejilla comprueba cabida geométrica; no certifica resistencia, estabilidad ni inocuidad.",
    12: "T.W., distancia y tiempo se recalculan por ruta con la intensidad y parámetros actuales.",
    13: "El diagrama distancia-intensidad usa las rutas calculadas; las coordenadas del plano son conceptuales.",
    14: "Las evidencias y acciones son registros; el estado de implantación exige seguimiento.",
    15: "Las reducciones cuantificadas proceden de las rutas recalculadas; los beneficios narrativos requieren verificación.",
    16: "El Pareto ordena los minutos capturados y calcula porcentajes sobre su total.",
    17: "Las ramas 6M representan hipótesis editables; no prueban causalidad.",
    18: "El porcentaje 5S solo es calculable con los veinte criterios puntuados.",
    19: "Los diez principios requieren evidencia de aplicación para declarar cumplimiento.",
    20: "Los equipos documentales no representan compras confirmadas ni costos cotizados.",
    21: "La ocupación requiere posiciones totales y ocupadas medidas en cada ubicación.",
    22: "La asignación abierta requiere ubicaciones, lotes y fechas capturados.",
    23: "La carga prevista debe compararse con la capacidad nominal verificada.",
    24: "El picking convierte bolsas en cajas enteras según las capacidades documentales.",
    25: "El código V2 es demostrativo y permanece separado de los identificadores físicos V3.",
    26: "La bitácora local no acredita integración con WMS o ERP externos.",
    27: "La capacidad de muelle es un modelo determinista; no incluye colas ni variabilidad.",
    28: "La selección de equipo auxiliar requiere capacidad, mantenimiento y costo verificados.",
    29: "La estrategia registra roles y reglas propuestas; su implantación requiere evidencia.",
    30: "P/Q/R/S/T se consolida desde el escenario actual; una celda pendiente no se completa con la semilla.",
    31: "La clasificación distancia-intensidad se aplica a rutas actuales; el retorno vacío se informa aparte.",
    32: "Un equipo solo se considera evaluable con capacidad, higiene y ergonomía comprobadas.",
    33: "El plano conceptual ilustra relaciones; sus posiciones no sustituyen una medición de distancias reales.",
    34: "El LCC complementario exige inversión y costos completos; las cifras del Word son referencia no auditada.",
    35: "VPN y recuperación requieren inversión incremental y ahorro; el VPN también necesita tasa y horizonte.",
    36: "La puntuación cualitativa requiere pesos que sumen uno y calificaciones completas.",
    37: "La recomendación documental B solo puede confirmarse para el escenario actual con costos y factores completos.",
    38: "El CPM requiere duraciones y predecesoras válidas; las ventanas semanales son ilustrativas.",
    39: "Las metas documentales no son mediciones; el semáforo se calcula solo con datos observados.",
}


SECTION_SPECS = tuple(
    SectionSpec(
        number, title, INPUTS.get(number, ()), PARAMS.get(number, ()),
        RESULTS.get(number, ()), METRICS.get(number, ()), CHARTS.get(number, ()),
        INTERPRETATIONS[number],
    )
    for number, title in SECTIONS.items()
)

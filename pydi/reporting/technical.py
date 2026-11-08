"""Artefactos técnicos trazables para los 39 apartados del informe.

Las tablas se proyectan del caso y de ``compute_case``. Esta capa no recalcula
las fórmulas industriales ni consulta la base de inventario.
"""

from dataclasses import dataclass

import pandas as pd

from pydi.v2_model import Case
from pydi.v2_results import Snapshot


@dataclass(frozen=True)
class TechnicalTable:
    title: str
    frame: pd.DataFrame
    source: str
    note: str = ""


@dataclass(frozen=True)
class SectionProfile:
    objective: str
    method: str
    references: str


# La referencia Rn identifica una obra en la bibliografía, no una figura copiada.
PROFILES = {
    1: SectionProfile("Documentar producto, receta y presentaciones configuradas.", "Balance de masa y ficha de composición por lote.", "R4, R5"),
    2: SectionProfile("Registrar la secuencia productiva y sus tiempos.", "Diagrama secuencial; capacidad = tiempo disponible / ciclo.", "R3, R4, R7"),
    3: SectionProfile("Comparar ubicaciones con factores explícitos.", "Suma ponderada de calificaciones registradas.", "R4, R8"),
    4: SectionProfile("Separar costos fijos y variables y estimar equilibrio.", "Qe = costo fijo / (precio unitario - costo variable unitario).", "R8"),
    5: SectionProfile("Inventariar elementos del análisis P-Q-R-S-T.", "Hoja SHA de producto, cantidad, ruta, servicios y tiempo.", "R1, R2"),
    6: SectionProfile("Evaluar las siete condiciones de manejo.", "Matriz criterio, estado y evidencia.", "R1, R5"),
    7: SectionProfile("Priorizar materiales según volumen mensual.", "P-Q ordenado y acumulado ABC del motor.", "R2, R3"),
    8: SectionProfile("Identificar especificaciones verificadas y faltantes.", "Ficha por material y procedencia.", "R1, R5"),
    9: SectionProfile("Comparar cargas unitarias declaradas.", "Composición, peso, dimensiones y equipo asociado.", "R5"),
    10: SectionProfile("Registrar contenedores y tarimas disponibles.", "Ficha dimensional y capacidad documentada.", "R4, R5"),
    11: SectionProfile("Evaluar la cabida geométrica de cajas en tarima.", "Rejilla 2D; resistencia y estabilidad requieren verificación aparte.", "R5"),
    12: SectionProfile("Cuantificar cada traslado en escenario base y propuesto.", "Matriz desde-hacia; T.W. = intensidad × distancia.", "R1, R6"),
    13: SectionProfile("Examinar recorridos y clases de manejo.", "Dispersión distancia-intensidad y red topológica sin escala.", "R1, R2"),
    14: SectionProfile("Registrar desperdicios observados o propuestos.", "Matriz de evidencia, acción y estado de implantación.", "R7"),
    15: SectionProfile("Contrastar transporte, espera e inventario.", "Comparación con igual unidad y horizonte; ahorro solo calculado.", "R1, R7"),
    16: SectionProfile("Priorizar causas de tiempo registradas.", "Pareto descendente, acumulado y referencia 80 %.", "R7"),
    17: SectionProfile("Organizar hipótesis causales capturadas.", "Ishikawa solo con causas escritas; no atribuye causalidad.", "R7"),
    18: SectionProfile("Evaluar los veinte criterios de 5S.", "Checklist por S; porcentaje solo con puntuación completa.", "R7"),
    19: SectionProfile("Revisar principios de manejo de materiales.", "Matriz de cumplimiento y evidencia.", "R5, R6"),
    20: SectionProfile("Comparar equipos y restricciones documentadas.", "Ficha técnica de capacidad, cantidad y costo capturado.", "R4, R5, R6"),
    21: SectionProfile("Medir ocupación de posiciones dedicadas.", "Ocupación = ocupadas / totales, solo con conteos reales.", "R5, R6"),
    22: SectionProfile("Describir asignación aleatoria de posiciones.", "Matriz ubicación-lote-fecha con reglas de rotación.", "R5"),
    23: SectionProfile("Verificar estructuras frente a su capacidad nominal.", "Dimensiones, carga prevista y verificación de seguridad.", "R5"),
    24: SectionProfile("Describir preparación de pedidos.", "Secuencia pedido-ubicación-cajas derivadas.", "R5, R6"),
    25: SectionProfile("Separar identificación documental y trazabilidad V3.", "Flujo lógico registro-código-consulta-evento; sin inventario ficticio.", "R6"),
    26: SectionProfile("Identificar entradas y salidas de información.", "Mapa de datos locales; integración externa solo si se acredita.", "R6"),
    27: SectionProfile("Contrastar capacidad de muelle con demanda.", "Vehículos por turno = posiciones × tiempo / servicio.", "R5"),
    28: SectionProfile("Comparar equipo auxiliar y mantenimiento.", "Matriz de uso, capacidad y costo verificado.", "R5"),
    29: SectionProfile("Definir política operativa por etapa.", "Matriz responsable, método, frecuencia y riesgo.", "R1, R5"),
    30: SectionProfile("Consolidar el diagnóstico SHA.", "P-Q-R-S-T, carga de rutas y alternativas documentadas.", "R1, R2"),
    31: SectionProfile("Clasificar movimientos por distancia e intensidad.", "Clases del motor calculadas con los umbrales documentales.", "R1"),
    32: SectionProfile("Relacionar ruta, método y equipo candidato.", "Evaluación condicionada a capacidad, higiene y ergonomía.", "R1, R5"),
    33: SectionProfile("Representar flujo y proximidad sin inventar planta.", "Red topológica y relación A/E/I/O/U; X solo con incompatibilidad documentada.", "R1, R2, R6"),
    34: SectionProfile("Comparar costos de ciclo de vida.", "CAPEX y OPEX por horizonte; LCC solo con entradas completas.", "R3, R8"),
    35: SectionProfile("Evaluar inversión y recuperación incremental.", "Flujo neto anual, VPN y payback solo con flujos/tasa suficientes.", "R8"),
    36: SectionProfile("Evaluar factores cualitativos ponderados.", "Pesos normalizados y puntuaciones completas.", "R2, R8"),
    37: SectionProfile("Comparar alternativas con criterios explícitos.", "Ranking solo si costos y factores son comparables.", "R1, R2"),
    38: SectionProfile("Programar implantación verificable.", "Gantt/CPM solo con duración y precedencias completas.", "R2, R7"),
    39: SectionProfile("Definir seguimiento continuo.", "Indicador, fórmula, meta, frecuencia y medición observada.", "R5, R7"),
}


# Cada fila selecciona los campos técnicos esenciales; los datos crudos siguen
# disponibles en la aplicación y en los anexos/exportaciones existentes.
TABLE_PLANS = {
    1: (("Composición de la receta", "input", "ingredientes", ("nombre", "kg_lote", "costo_kg_mxn", "origen")),),
    2: (("Secuencia y tiempos por etapa", "input", "proceso", ("etapa", "duracion_s", "observacion", "origen")),),
    3: (("Matriz de factores de localización", "input", "localizacion", ("factor", "peso", "Union Juarez", "Cacahoatan", "Tapachula")),
        ("Puntuación ponderada", "result", "Localización calculada", ("municipio", "puntuacion"))),
    4: (("Costos fijos mensuales", "input", "costos_fijos", ("concepto", "mxn_mes", "origen")),),
    5: (("Hoja P-Q-R-S-T", "result", "PQRST consolidado", ("elemento", "valor", "origen")),),
    6: (("Conformidad de las 7 R", "input", "siete_r", ("criterio", "estado", "evidencia", "mejora")),),
    7: (("P-Q y clases ABC", "result", "P-Q calculado", ("material", "kg_mes_calculado", "porcentaje", "acumulado_pct", "clase_abc_m")),),
    8: (("Fichas de materiales y equipos", "input", "fichas", ("elemento", "categoria", "especificacion", "dato_pendiente")),),
    9: (("Diseño de cargas unitarias", "input", "cargas", ("clave", "carga", "composicion", "peso_bruto", "dimensiones", "equipo")),),
    10: (("Contenedores y tarimas", "input", "contenedores", ("elemento", "dimensiones", "capacidad", "cantidad", "material")),),
    11: (),
    12: (("Rutas base: intensidad por distancia", "result", "TW base calculado", ("id", "origen_area", "destino_area", "intensidad_kg_dia", "distancia_m", "tw_kg_m_dia")),
         ("Rutas propuestas: intensidad por distancia", "result", "TW propuesto calculado", ("id", "origen_area", "destino_area", "intensidad_kg_dia", "distancia_m", "tw_kg_m_dia"))),
    13: (("Datos de dispersión D-I", "result", "TW propuesto calculado", ("id", "distancia_m", "intensidad_kg_dia", "clase_di")),),
    14: (("Evidencia de desperdicios", "input", "desperdicios", ("desperdicio", "evidencia", "accion_propuesta", "estado_implantacion")),),
    15: (("Comparación de transporte calculada", "result", "Comparación transporte", ("indicador", "base", "propuesto", "reduccion_pct", "unidad")),
         ("Acciones de mejora registradas", "input", "mejoras", ("aspecto", "propuesta", "estado"))),
    16: (("Tiempos y acumulado de Pareto", "result", "Pareto calculado", ("causa", "min_dia", "porcentaje", "acumulado_pct", "rutas")),),
    17: (("Causas capturadas", "input", "ishikawa", ("categoria", "causa", "efecto", "rutas_pareto")),),
    18: (("Checklist 5S", "input", "cinco_s", ("numero", "s", "criterio", "puntaje", "observaciones")),),
    19: (("Principios CIC-MHE", "input", "principios", ("principio", "estado", "evidencia", "aplicacion")),),
    20: (("Especificación de equipos", "input", "equipos", ("equipo", "cantidad_documental", "especificacion", "costo_mxn")),),
    21: (("Ocupación dedicada", "input", "dedicado", ("ubicacion", "material", "posiciones_totales", "posiciones_ocupadas", "regla_rotacion")),),
    22: (("Asignación aleatoria", "input", "aleatorio", ("ubicacion", "lote", "posiciones_totales", "posiciones_ocupadas", "fecha_entrada")),),
    23: (("Estructuras y cargas", "input", "estructuras", ("estructura", "largo_m", "fondo_m", "alto_m", "capacidad_nominal_kg", "carga_prevista_kg")),),
    24: (("Secuencia de pedidos", "input", "pedidos", ("pedido", "bolsas_250", "bolsas_500", "distancia_m")),
         ("Cajas de picking calculadas", "result", "Picking calculado", ("pedido", "cajas_250", "cajas_500"))),
    25: (("Identificadores documentales", "input", "identificaciones", ("codigo", "lote", "ubicacion", "tipo", "origen")),),
    26: (("Eventos de información", "input", "eventos", ("evento", "fecha", "codigo", "origen_area", "destino_area")),),
    27: (("Datos de muelles", "input", "muelles", ("muelle", "posiciones", "tiempo_operativo_s", "tiempo_vehiculo_s", "demanda_vehiculos", "ancho_m")),),
    28: (("Equipamiento auxiliar", "input", "auxiliar", ("equipo", "cantidad", "capacidad", "mantenimiento", "costo_mxn")),),
    29: (("Política operativa por etapa", "input", "operacion", ("etapa", "responsable", "metodo", "frecuencia", "regla", "riesgo")),),
    30: (("P-Q-R-S-T del escenario", "result", "PQRST consolidado", ("elemento", "valor", "origen")),
         ("Alternativas SHA", "input", "planes", ("alternativa", "metodo", "equipo", "restricciones", "estado"))),
    31: (("Clasificación de movimientos", "result", "TW propuesto calculado", ("id", "movimiento", "distancia_m", "intensidad_kg_dia", "clase_di")),),
    32: (("Asignación método-equipo-ruta", "input", "metodos", ("ruta", "equipo_candidato", "capacidad_kg", "higiene_verificada", "ergonomia_verificada", "costo_mxn")),),
    33: (("Áreas declaradas", "input", "areas", ("area", "clave", "superficie_m2", "origen_posicion")),),
    34: (("CAPEX y OPEX capturados", "input", "alternativas", ("alternativa", "inversion_mxn", "operacion_anual_mxn", "mantenimiento_anual_mxn", "reinversion_mxn", "residual_mxn")),
         ("LCC calculado", "result", "LCC calculado", ("alternativa", "lcc_nominal_mxn", "lcc_descontado_mxn"))),
    35: (("Flujos de alternativas", "input", "alternativas", ("alternativa", "inversion_mxn", "ahorro_neto_anual_mxn", "operacion_anual_mxn")),),
    36: (("Factores y ponderaciones", "input", "cualitativa", ("factor", "peso", "A", "B", "C", "escala")),
         ("Puntuación calculada", "result", "Evaluación calculada", ("alternativa", "puntuacion"))),
    37: (("Planes comparados", "input", "planes", ("alternativa", "metodo", "equipo", "restricciones", "estado")),),
    38: (("Tareas y precedencias", "input", "cronograma", ("id", "actividad", "duracion_semanas", "predecesoras", "inicio_referencia", "fin_referencia")),
         ("CPM calculado", "result", "CPM calculado", ("id", "actividad", "ES", "EF", "critica"))),
    39: (("Control continuo", "input", "auditoria", ("indicador", "formula", "meta", "frecuencia", "responsable", "medicion")),
         ("Estado de indicadores", "result", "Auditoría evaluada", ("indicador", "valor_evaluado", "estado"))),
}


def _project(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    selected = [column for column in columns if column in frame]
    return frame.loc[:, selected].copy() if selected else pd.DataFrame()


def relation_pairs(snap: Snapshot, limit: int = 6) -> pd.DataFrame:
    """Proximidad analítica derivada de flujo, sin afirmar restricciones X."""
    routes = snap.tables.get("TW propuesto calculado")
    columns = ["desde", "hacia", "intensidad_kg_dia", "grado", "motivo"]
    if routes is None or routes.empty:
        return pd.DataFrame(columns=columns)
    directed = routes.groupby(["origen_area", "destino_area"], dropna=True)["intensidad_kg_dia"].sum()
    scores: dict[str, float] = {}
    for (origin, target), value in directed.items():
        scores[str(origin)] = scores.get(str(origin), 0) + float(value)
        scores[str(target)] = scores.get(str(target), 0) + float(value)
    nodes = sorted(scores, key=lambda node: (-scores[node], node))[:limit]
    pairs = {}
    for (origin, target), value in directed.items():
        key = tuple(sorted((str(origin), str(target))))
        pairs[key] = pairs.get(key, 0) + float(value)
    maximum = max(pairs.values(), default=0)
    rows = []
    for i, origin in enumerate(nodes):
        for target in nodes[i + 1:]:
            amount = pairs.get(tuple(sorted((origin, target))), 0.0)
            ratio = amount / maximum if maximum else 0
            grade = "A" if ratio >= .8 else "E" if ratio >= .6 else "I" if ratio >= .4 else "O" if ratio >= .2 else "U"
            reason = f"Flujo calculado {amount:,.2f} kg/día" if amount else "Sin flujo registrado"
            rows.append((origin, target, amount, grade, reason))
    return pd.DataFrame(rows, columns=columns)


def tables_for_section(number: int, case: Case, snap: Snapshot) -> list[TechnicalTable]:
    tables = []
    for title, kind, key, columns in TABLE_PLANS[number]:
        source = case.tables if kind == "input" else snap.tables
        frame = _project(source.get(key, pd.DataFrame()), columns)
        if number == 17 and not frame.empty:
            frame = frame.loc[frame["causa"].fillna("").astype(str).str.strip().ne("")]
        provenance = "Escenario capturado [D/S/M/U]" if kind == "input" else "Motor compute_case [C]"
        tables.append(TechnicalTable(title, frame, provenance))
    if number == 1:
        rows = [(f"Bolsa {grams} g", case.params.get(f"bolsas_{grams}_lote"), "bolsas/lote") for grams in (250, 500)]
        tables.insert(0, TechnicalTable("Presentaciones configuradas", pd.DataFrame(rows, columns=["presentación", "cantidad", "unidad"]), "Parámetros del escenario [D/U]", "Una tercera presentación se informa solo si se configura en el sistema."))
    elif number == 5:
        elements = case.tables["elementos"]
        grouped = elements.groupby(["tipo", "unidad"], dropna=False).agg(
            elementos=("codigo", "count"), cantidades_sin_medición=("cantidad_actual", lambda values: int(values.isna().sum()))
        ).reset_index()
        tables.append(TechnicalTable("Inventario analítico por tipo y unidad", grouped,
                                     "Catálogo PYDI del escenario [D/S/M/U]",
                                     "La relación individual permanece en el catálogo y en la exportación XLSX; no equivale a existencias físicas V3."))
    elif number == 4 and "equilibrio" in snap.metrics:
        result = snap.metrics["equilibrio"]
        frame = pd.DataFrame([
            ("Costo fijo", snap.metrics.get("costo_fijo_mxn_mes"), "MXN/mes"),
            ("Precio 250 g", case.params.get("precio_250_mxn"), "MXN/bolsa"),
            ("Costo variable 250 g", case.params.get("cvu_250_mxn"), "MXN/bolsa"),
            ("Equilibrio continuo", result["bolsas_reales"], "bolsas/mes"),
            ("Equilibrio entero", result["bolsas_enteras"], "bolsas/mes"),
        ], columns=["concepto", "valor", "unidad"])
        tables.append(TechnicalTable("Hoja de equilibrio 250 g", frame, "Motor compute_case [C]", "El redondeo entero se conserva; no extrapolar a 500 g."))
    elif number in (12, 30):
        rows = []
        for name, label in (("TW base calculado", "Base"), ("TW propuesto calculado", "Propuesto")):
            frame = snap.tables.get(name)
            if frame is not None and not frame.empty:
                rows.append((label, frame["tw_kg_m_dia"].sum(), "kg·m/día", len(frame)))
        if rows:
            tables.append(TechnicalTable("Suma de trabajo de transporte", pd.DataFrame(rows, columns=["escenario", "T.W. total", "unidad", "rutas"]), "Suma de filas de compute_case [C]"))
    elif number == 33:
        tables.append(TechnicalTable("Relaciones SLP propuestas por flujo", relation_pairs(snap), "Intensidad calculada del escenario [C/M]", "Grados A/E/I/O/U por intensidad relativa. X exige incompatibilidad documentada y no se infiere."))
    elif number == 35:
        value = snap.metrics.get("payback_b_vs_a_anios")
        if value is not None:
            tables.append(TechnicalTable("Recuperación incremental B frente a A", pd.DataFrame([("Payback", value, "años")], columns=["indicador", "valor", "unidad"]), "Motor compute_case [C]"))
    return tables


def required_data(number: int, case: Case, snap: Snapshot) -> str:
    """Explica faltantes metodológicos que no se deben suplir con dibujos."""
    if number == 11 and case.params.get("capacidad_tarima_kg") is None:
        return "Capacidad nominal, estabilidad y dimensiones de altura pendientes; solo se muestra cabida en planta."
    if number == 17 and case.tables["ishikawa"]["causa"].fillna("").astype(str).str.strip().eq("").all():
        return "Capturar causas específicas y su evidencia para dibujar Ishikawa; no se completan ramas 6M genéricas."
    if number == 18 and case.tables["cinco_s"]["puntaje"].isna().any():
        return "Capturar los veinte puntajes 5S para calcular subtotales y generar gráfica."
    if number == 33:
        return "ESQUEMA NO A ESCALA. Las posiciones ilustrativas no se usan como coordenadas físicas; X requiere incompatibilidad documentada."
    if number in (34, 35) and "LCC calculado" not in snap.tables:
        return "Inversión, operación, mantenimiento, reinversión, residual y flujos anuales pendientes; no se publica VAN/TIR/LCC no calculado."
    if number == 38 and "CPM calculado" not in snap.tables:
        return "Duraciones y precedencias incompletas; no se dibuja Gantt ni se afirma ruta crítica."
    if number in (21, 22, 23, 24, 27, 32, 36, 37):
        return "Los campos vacíos del escenario se mantienen pendientes; no se infieren medidas, costos ni decisiones."
    return ""

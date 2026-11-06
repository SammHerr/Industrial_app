"""Interfaz Streamlit V2 organizada por dominios, con 39 apartados navegables."""

import pandas as pd
import plotly.express as px
import streamlit as st

from pydi.calculations.storage_finance import dock_capacity
from pydi.calculations.transport_quality import occupancy
from pydi.v2_barcode import code128_svg
from pydi.v2_charts import (
    di_chart,
    equilibrium_chart,
    five_s_chart,
    gantt_chart,
    ishikawa_chart,
    layout_chart,
    pallet_chart,
    pareto_chart,
    pq_chart,
    production_chart,
    simple_bars,
    tw_chart,
)
from pydi.v2_model import (
    Case,
    make_empty_case,
    make_example_case,
    without_illustrative_values,
)
from pydi.v2_reports import SHEET_NAMES, export_xlsx
from pydi.v2_results import alerts_frame, compute_case
from pydi.v3_ui import clear_transient_state
from pydi.v3_ui import render as render_inventory

GROUPS = (
    "Inicio y calidad de datos", "1–2 Producto y proceso", "3 Localización",
    "4 Costos y equilibrio", "5–8 Elementos, 7R y P-Q", "9–11 Cargas y estiba",
    "12–13 Transporte y plano", "14–17 Mejora y causas", "18–20 Calidad y equipos",
    "21–28 Almacén y logística", "29–33 Plan SHA", "34–37 Economía y selección",
    "38–39 Cronograma y auditoría", "Exportación integral", "Códigos e inventario V3",
)

SECTIONS = {
    1: "Descripción del producto", 2: "Descripción del proceso", 3: "Ubicación geográfica",
    4: "Costos de producción", 5: "Identificación y registro formal de elementos",
    6: "Cumplimiento de las 7 R", 7: "Análisis producto-cantidad P-Q",
    8: "Fichas técnicas", 9: "Carga unitaria", 10: "Contenedores y palets",
    11: "Estibado e integridad", 12: "Trabajo de manejo T.W.",
    13: "Hilos y distancia-intensidad", 14: "Siete desperdicios",
    15: "Reducción de transporte, esperas e inventario", 16: "Pareto",
    17: "Ishikawa", 18: "Checklist 5S", 19: "Principios CIC-MHE",
    20: "Especificación de equipos", 21: "Almacenamiento dedicado",
    22: "Almacenamiento aleatorio", 23: "Estructuras de almacenaje",
    24: "Preparación de pedidos", 25: "Tecnología de identificación",
    26: "Sistemas de información", 27: "Área de muelles", 28: "Equipamiento auxiliar",
    29: "Estrategia de operación", 30: "Consolidación SHA",
    31: "Clasificación de movimiento", 32: "Asignación de métodos y equipos",
    33: "Plano de flujo", 34: "Costo del ciclo de vida",
    35: "Inversión, costos y recuperación", 36: "Evaluación cualitativa",
    37: "Selección del sistema", 38: "Cronograma de instalación",
    39: "Plan de auditoría continua",
}

NUMERIC_COLUMNS = {
    "kg_lote", "costo_kg_mxn", "duracion_s", "peso", "Union Juarez", "Cacahoatan", "Tapachula",
    "costo_mxn", "area_m2", "mxn_mes", "cantidad_actual", "kg_mes_reportado", "kg_lote_equiv",
    "intensidad_manual_kg_dia", "viajes_dia", "distancia_m", "superficie_m2", "x_m", "y_m",
    "min_dia", "puntaje", "posiciones_totales", "posiciones_ocupadas", "largo_m", "fondo_m",
    "alto_m", "capacidad_nominal_kg", "carga_prevista_kg", "bolsas_250", "bolsas_500",
    "cajas_250", "cajas_500", "cantidad", "posiciones", "tiempo_operativo_s", "tiempo_vehiculo_s",
    "demanda_vehiculos", "ancho_m", "capacidad_kg", "inversion_mxn", "operacion_anual_mxn",
    "mantenimiento_anual_mxn", "reinversion_mxn", "residual_mxn", "disposicion_mxn",
    "ahorro_neto_anual_mxn", "A", "B", "C", "duracion_semanas", "inicio_referencia",
    "fin_referencia", "numerador", "denominador", "medicion",
}


def _load_example() -> None:
    st.session_state.case = make_example_case()
    st.session_state.revision = st.session_state.get("revision", 0) + 1
    st.session_state.scenario_choice = "Documento (valores reportados)"
    st.session_state.pop("undo_case", None)


def _clear_case() -> None:
    st.session_state.undo_case = st.session_state.case.copy()
    st.session_state.case = make_empty_case()
    st.session_state.revision += 1
    st.session_state.scenario_choice = "Nuevo estudio"
    clear_transient_state()


def _undo_clear() -> None:
    st.session_state.case = st.session_state.undo_case.copy()
    st.session_state.revision += 1
    st.session_state.scenario_choice = st.session_state.case.mode
    del st.session_state.undo_case


def _without_model() -> None:
    st.session_state.case = without_illustrative_values(st.session_state.case)
    st.session_state.revision += 1


def _scenario_change() -> None:
    choice = st.session_state.scenario_choice
    if choice == "Nuevo estudio":
        _clear_case()
    elif choice == "Documento (valores reportados)":
        _load_example()
    else:
        st.session_state.case.mode = choice
        st.session_state.revision += 1


def _case() -> Case:
    return st.session_state.case


def _snapshot():
    return compute_case(_case())


def _section(number: int, source: str, note: str = "") -> None:
    st.subheader(f"{number}. {SECTIONS[number]}")
    st.caption(f"{source} · {note}" if note else source)


def _numeric(name: str, label: str, source: str, *, unit: str = "", positive: bool = False):
    key = f"input_{st.session_state.revision}_{name}"
    value = _case().params[name]
    result = st.number_input(
        f"{label}{f' ({unit})' if unit else ''}", min_value=0.000001 if positive else 0.0,
        value=value, step=1.0, key=key, help=source,
    )
    if result != value:
        _case().modified_params.add(name)
    _case().params[name] = result
    return result


def _editor(name: str, description: str, *, source: str = "[D/S] Word; cambios [U]") -> pd.DataFrame:
    st.markdown(f"**{description}**")
    st.caption(source)
    table = _case().tables[name]
    config = {column: st.column_config.NumberColumn(column.replace("_", " "), min_value=0.0) for column in table.columns if column in NUMERIC_COLUMNS}
    if name == "siete_r":
        config["estado"] = st.column_config.SelectboxColumn("Estado", options=["Cumple", "Parcial", "No cumple", "No evaluado"])
    if name == "cinco_s":
        config["puntaje"] = st.column_config.SelectboxColumn("Puntaje", options=[0, 1, 2])
    result = st.data_editor(table, key=f"editor_{st.session_state.revision}_{name}", num_rows="dynamic", width="stretch", hide_index=True, column_config=config)
    if not result.equals(table):
        _case().modified_tables.add(name)
    _case().tables[name] = result.copy()
    st.download_button(
        f"CSV · {description}", result.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{name}.csv", mime="text/csv", key=f"csv_{st.session_state.revision}_{name}",
    )
    return result


def _result_table(snapshot, name: str, *, title: str = "Resultado calculado [C]") -> None:
    if name in snapshot.tables:
        st.markdown(f"**{title}**")
        st.dataframe(snapshot.tables[name].round(3), width="stretch", hide_index=True)
    else:
        st.info("Sin datos suficientes para calcular este resultado.")


def _domain_alerts(snapshot, prefix: str) -> None:
    matches = [(level, message) for level, section, message in snapshot.alerts if section.startswith(prefix)]
    for level, message in matches:
        if level == "Error":
            st.error(message)
        elif level == "Advertencia":
            st.warning(message)
        elif level == "Pendiente":
            st.info(message)
        else:
            st.caption(message)


def _home() -> None:
    st.header("Estado del estudio")
    case, snapshot = _case(), _snapshot()
    st.write(f"**Escenario:** {case.mode} · **Semilla:** {case.version}")
    st.caption("[D] declarado en Word · [S] supuesto del Word · [C] calculado · [M] complemento o ejemplo ilustrativo · [U] editado por el usuario")
    if case.illustrative:
        st.warning("Hay posiciones y plantillas [M] ilustrativas. No proceden del Word ni prueban el desempeño de la planta.")
    st.dataframe(alerts_frame(snapshot), width="stretch", hide_index=True)
    st.subheader("Cobertura del índice real")
    coverage = pd.DataFrame([
        (number, title, "Cálculo/visual" if number in (2, 3, 4, 6, 7, 9, 11, 12, 13, 16, 18, 24, 27, 31, 34, 35, 36, 38, 39) else "Registro/método editable", "[D/S]" if number <= 20 or number in (31, 37, 38, 39) else "[M] complementario")
        for number, title in SECTIONS.items()
    ], columns=["número", "apartado", "cobertura", "procedencia"])
    st.dataframe(coverage, width="stretch", hide_index=True)
    st.caption("Las secciones con solo título en el Word son formularios [M]; sus resultados quedan pendientes hasta capturar entradas.")


def _production() -> None:
    _section(1, "[D] Word §1 pp.6–8", "La receta no se normaliza automáticamente.")
    _numeric("lote_objetivo_kg", "Masa objetivo del lote", "[D] Word §1–2: 10 kg", unit="kg", positive=True)
    _numeric("empaque_lote_mxn", "Empaque por lote", "[D] Word §1: $30/lote; separado de kg de ingredientes", unit="MXN/lote")
    _editor("ingredientes", "Formulación e insumos por lote")
    snap = _snapshot()
    _result_table(snap, "Ingredientes calculados")
    if "masa_entrada_kg" in snap.metrics:
        st.metric("Masa de entrada [C]", f"{snap.metrics['masa_entrada_kg']:.2f} kg/lote")
    if "costo_total_lote_mxn" in snap.metrics:
        st.metric("Ingredientes + empaque [C]", f"${snap.metrics['costo_total_lote_mxn']:,.2f} MXN/lote")
    _domain_alerts(snap, "1 ")
    _section(2, "[D] Word §2 pp.9–11; ecuaciones OMML", "Capacidad base secuencial y propuesta separadas.")
    columns = st.columns(4)
    with columns[0]:
        _numeric("turno_s", "Turno", "[D] 30,600 s", unit="s", positive=True)
        _numeric("ciclo_s", "Ciclo base secuencial", "[D] 10,200 s/lote", unit="s/lote", positive=True)
    with columns[1]:
        _numeric("preparacion_s", "Preparación", "[D] 600 s", unit="s")
        _numeric("comida_s", "Comida", "[D] 1,800 s", unit="s")
    with columns[2]:
        _numeric("lotes_propuestos_dia", "Lotes propuestos", "[D] 7.75 lotes/día", unit="lotes/día", positive=True)
        _numeric("dias_mes", "Días del mes", "[D] 26 días/mes", unit="días", positive=True)
    with columns[3]:
        _numeric("bolsas_250_lote", "Bolsas de 250 g", "[D] 32 por lote", unit="pzas/lote")
        _numeric("bolsas_500_lote", "Bolsas de 500 g", "[D] 4 por lote; alternativa 40 × 250 g en §4", unit="pzas/lote")
    _editor("proceso", "Secuencia de operaciones y duración individual", source="[D] Etapas Word §2. Duraciones individuales no desagregadas; captura [U].")
    snap = _snapshot()
    if "capacidad" in snap.metrics:
        cap = snap.metrics["capacidad"]
        cols = st.columns(3)
        cols[0].metric("Tiempo disponible [C]", f"{cap['disponible_s']:,.0f} s/turno")
        cols[1].metric("Capacidad continua [C]", f"{cap['lotes_continuos']:.4f} lotes/turno")
        cols[2].metric("Lotes completos [C]", f"{cap['lotes_completos']:.0f} lotes/turno")
    if "produccion" in snap.metrics:
        prod = snap.metrics["produccion"]
        st.write(f"**[C] Propuesta:** {prod['lotes_mes']:g} lotes/mes; {prod['bolsas_250_mes']:,.0f} bolsas de 250 g y {prod['bolsas_500_mes']:,.0f} de 500 g; {prod['kg_empacados_lote']:g} kg/lote.")
        st.plotly_chart(production_chart(prod, snap.metrics.get("capacidad")), width="stretch")
    _domain_alerts(snap, "2 ")


def _location() -> None:
    _section(3, "[D/S] Word §3 pp.16–23", "Ponderación declarada; distancias de emergencia estimadas.")
    _editor("localizacion", "Factores y pesos de municipios")
    snap = _snapshot()
    if "localizacion" in snap.metrics:
        values = snap.metrics["localizacion"]
        st.dataframe(pd.DataFrame(values.items(), columns=["municipio", "puntuación [C]"]).round(2), width="stretch", hide_index=True)
        st.plotly_chart(simple_bars(pd.DataFrame(values.items(), columns=["municipio", "puntuacion"]), "municipio", "puntuacion", "Ponderación de municipios [C]"), width="stretch")
    _domain_alerts(snap, "3 ")
    _editor("terrenos", "Comparación de terrenos", source="[D] Costos/ubicaciones Word §3; área sin dato validado.")
    _editor("emergencias", "Servicios de emergencia", source="[S] Rangos de distancia y tiempo estimados en Word; no se calculan rutas reales.")


def _costs() -> None:
    _section(4, "[D] Word §4 pp.23–27; Qe en ecuación OMML", "El equilibrio aplica solo a bolsas de 250 g.")
    _editor("costos_fijos", "Costos fijos mensuales")
    c1, c2 = st.columns(2)
    with c1:
        _numeric("cvu_250_mxn", "Costo variable unitario 250 g", "[D] Word: $11.38", unit="MXN/bolsa")
    with c2:
        _numeric("precio_250_mxn", "Precio 250 g", "[D] Word: $35", unit="MXN/bolsa", positive=True)
    snap = _snapshot()
    if "costo_fijo_mxn_mes" in snap.metrics:
        st.metric("Costo fijo [C]", f"${snap.metrics['costo_fijo_mxn_mes']:,.2f} MXN/mes")
    if "equilibrio" in snap.metrics:
        qe = snap.metrics["equilibrio"]
        cols = st.columns(3)
        cols[0].metric("Qe continuo [C]", f"{qe['bolsas_reales']:,.4f} bolsas")
        cols[1].metric("Unidades enteras [C]", f"{qe['bolsas_enteras']:,} bolsas")
        cols[2].metric("Word [D]", "8,055 bolsas")
        st.plotly_chart(equilibrium_chart(snap.metrics["costo_fijo_mxn_mes"], _case().params["cvu_250_mxn"], _case().params["precio_250_mxn"], qe["bolsas_reales"]), width="stretch")
        st.caption("[C] Ingreso = P × Q; costo total = CF + CVU × Q. No se extrapola margen a la presentación 500 g.")
    _domain_alerts(snap, "4 ")


def _elements_pq() -> None:
    _section(5, "[D/S] Word §5 pp.28–31", "42 elementos codificados. Cantidad actual sin inventario medido.")
    _editor("elementos", "Catálogo ASO")
    table = _case().tables["elementos"]
    if not table.empty and (table["codigo"].isna().any() or table["codigo"].astype(str).str.strip().str.casefold().duplicated().any()):
        st.error("Elementos: códigos vacíos o duplicados.")
    _section(6, "[D] Word §6 pp.31–33", "Cinco Parcial y dos No cumple en el método base.")
    _editor("siete_r", "Evaluación de las 7 R")
    snap = _snapshot()
    if "siete_r" in snap.metrics:
        states = snap.metrics["siete_r"]
        st.dataframe(pd.DataFrame(states.items(), columns=["estado", "cantidad"]), width="stretch", hide_index=True)
        st.plotly_chart(simple_bars(pd.DataFrame(states.items(), columns=["estado", "cantidad"]), "estado", "cantidad", "7 R · estado actual [D/U]"), width="stretch")
    _domain_alerts(snap, "6 ")
    _section(7, "[D/C] Word §7 pp.33–34", "Factores kg/lote inferidos de la tabla para empaques; ingredientes ligados a la receta.")
    _editor("pq", "P-Q reportado y factor editable kg/lote")
    c1, c2 = st.columns(2)
    with c1:
        _numeric("factor_abc_a", "Umbral A [M]", "[M] Clasificación configurable; no equivale a Muther", unit="%")
    with c2:
        _numeric("factor_abc_b", "Umbral B [M]", "[M] Clasificación configurable; no equivale a Muther", unit="%")
    snap = _snapshot()
    _result_table(snap, "P-Q calculado")
    if "P-Q calculado" in snap.tables:
        st.plotly_chart(pq_chart(snap.tables["P-Q calculado"]), width="stretch")
    _domain_alerts(snap, "7 ")
    _section(8, "[D/S] Word §8 p.34", "El Word no aporta fichas completas de proveedor.")
    _editor("fichas", "Fichas de materiales y máquinas")


def _loads() -> None:
    _section(9, "[D/S] Word §9 pp.34–36", "Siete cargas unitarias documentales.")
    _editor("cargas", "CU-1 a CU-7")
    _section(10, "[D/S] Word §10 pp.36–38", "Dimensiones y capacidades a verificar con proveedor.")
    _editor("contenedores", "Contenedores, tarimas y cajas")
    _section(11, "[D] geometría Word §11 pp.38–39; [C] comprobación rectangular", "No certifica estabilidad, resistencia ni inocuidad.")
    cols = st.columns(3)
    with cols[0]:
        _numeric("tarima_largo_cm", "Largo tarima", "[D] 120 cm", unit="cm", positive=True)
        _numeric("tarima_ancho_cm", "Ancho tarima", "[D] 100 cm", unit="cm", positive=True)
    with cols[1]:
        _numeric("caja_largo_cm", "Largo caja", "[D] 40 cm", unit="cm", positive=True)
        _numeric("caja_ancho_cm", "Ancho caja", "[D] 33 cm", unit="cm", positive=True)
    with cols[2]:
        _numeric("cajas_capa", "Cajas por cama", "[D] 9", unit="cajas", positive=True)
        _numeric("capas", "Camas", "[D] 5", unit="camas", positive=True)
        _numeric("capacidad_tarima_kg", "Capacidad nominal", "[U] Requiere ficha de proveedor", unit="kg")
    snap = _snapshot()
    if "estiba" in snap.metrics:
        info = snap.metrics["estiba"]
        st.write(f"**[C]** Máximo en rejilla: {info['cajas_capa_max_rejilla']}; diseño: {info['cajas_tarima']:g} cajas/tarima. Geometría: {'cabe' if info['cabe_geometria'] else 'NO cabe'}.")
        if info["cabe_geometria"]:
            st.plotly_chart(pallet_chart(_case().params, int(info["cajas_capa_max_rejilla"])), width="stretch")
    _domain_alerts(snap, "11 ")


def _transport() -> None:
    _section(12, "[D/S] Word §12 pp.40–43", "Intensidad = factor kg/lote × lotes/día, salvo override manual [U].")
    cols = st.columns(3)
    with cols[0]:
        _numeric("velocidad_m_s", "Velocidad", "[S] Word: 0.9 m/s", unit="m/s", positive=True)
    with cols[1]:
        _numeric("carga_base_s", "Carga base", "[S] Word: 30 s/viaje", unit="s/viaje")
    with cols[2]:
        _numeric("carga_propuesta_s", "Carga propuesta", "[S] Word: 45 s/viaje", unit="s/viaje")
    _editor("rutas_base", "Rutas B1–B9")
    _editor("rutas_propuestas", "Rutas P1–P9")
    snap = _snapshot()
    _result_table(snap, "Comparación transporte")
    if "TW base calculado" in snap.tables and "TW propuesto calculado" in snap.tables:
        base, proposed = snap.tables["TW base calculado"], snap.tables["TW propuesto calculado"]
        st.plotly_chart(tw_chart(base, proposed), width="stretch")
        _section(13, "[D] Word §13 pp.44–45", "Umbrales D-I del §31; no son distancias geográficas.")
        st.plotly_chart(di_chart(base, proposed), width="stretch")
        _section(31, "[D] Word §31 pp.56–57", "Retorno vacío separado del T.W. con producto.")
        st.dataframe(proposed[["id", "distancia_m", "intensidad_kg_dia", "clase_di"]].round(3), width="stretch", hide_index=True)
    _domain_alerts(snap, "12 ")
    _numeric("retorno_vacio_viajes", "Retorno vacío", "[D] 2 viajes/día; separado", unit="viajes/día")
    _numeric("retorno_vacio_m", "Distancia retorno vacío", "[D] 31.5 m", unit="m")
    if _case().params["retorno_vacio_viajes"] is not None and _case().params["retorno_vacio_m"] is not None:
        st.write(f"[C] Retorno vacío: {_case().params['retorno_vacio_viajes'] * _case().params['retorno_vacio_m']:.1f} m/día, excluido del T.W. con producto.")
    _section(33, "[M] Plano conceptual; áreas [D] Word §13", "Posiciones ilustrativas editables, sin inferir distancias reales de las rutas.")
    _editor("areas", "Áreas y coordenadas conceptuales 30 × 20 m")
    area = _case().tables["areas"]
    if not area.empty and area[["x_m", "y_m"]].notna().any().any():
        try:
            st.plotly_chart(layout_chart(area, snap.tables.get("TW propuesto calculado")), width="stretch")
        except (ValueError, TypeError) as exc:
            st.error(f"Plano: {exc}")


def _improvement() -> None:
    _section(14, "[D/S] Word §14 pp.45–46", "Evidencia y propuesta documentales; estado de implantación requiere evaluación [U].")
    _editor("desperdicios", "Siete desperdicios Lean")
    _section(15, "[D] Word §15 pp.46–47", "Resultados narrativos; verificar antes de tratarlos como medición de planta.")
    _editor("mejoras", "Plan de mejoras")
    _section(16, "[D] Word §16 pp.47–48", "La gráfica usa exclusivamente minutos visibles y editados.")
    _editor("pareto", "Causas de tiempo de manejo")
    snap = _snapshot()
    _result_table(snap, "Pareto calculado")
    if "Pareto calculado" in snap.tables:
        st.plotly_chart(pareto_chart(snap.tables["Pareto calculado"]), width="stretch")
    _domain_alerts(snap, "16 ")
    _section(17, "[D] esquema 6M Word §17 pp.48–49; [M] editor", "Las causas anotadas son hipótesis, sin frecuencia ni causalidad probada.")
    _editor("ishikawa", "Causas por categoría 6M")
    st.plotly_chart(ishikawa_chart(_case().tables["ishikawa"]), width="stretch")


def _quality() -> None:
    _section(18, "[D] Word §18 pp.49–51", "20 criterios × 2 puntos. Blanco significa pendiente.")
    _editor("cinco_s", "Checklist 5S")
    snap = _snapshot()
    if "cinco_s" in snap.metrics:
        result = snap.metrics["cinco_s"]
        st.metric("Cumplimiento 5S [C/U]", f"{result['puntos']:.0f}/40 · {result['porcentaje']:.1f} %")
        st.plotly_chart(five_s_chart(_case().tables["cinco_s"]), width="stretch")
    else:
        st.info("Sin puntuación 5S hasta completar los 20 criterios.")
    _domain_alerts(snap, "18 ")
    _section(19, "[D/S] Word §19 pp.51–53", "Diez principios, evidencia y seguimiento editables.")
    _editor("principios", "Principios CIC-MHE")
    _section(20, "[D/S] Word §20 pp.53–55", "Sin marca, modelo o cotización no se presenta costo de compra.")
    _editor("equipos", "Máquinas y equipos de manejo")


def _warehouse() -> None:
    _section(21, "[M] formulario para título Word §21 p.55", "Posiciones y alérgenos deben medirse y verificarse.")
    _editor("dedicado", "Posiciones dedicadas de materia prima")
    dedicated = _case().tables["dedicado"]
    if not dedicated.empty:
        rows = []
        for row in dedicated.itertuples():
            if pd.notna(row.posiciones_totales) and pd.notna(row.posiciones_ocupadas):
                try:
                    rows.append((row.ubicacion, occupancy(row.posiciones_totales, row.posiciones_ocupadas)))
                except ValueError as exc:
                    st.error(str(exc))
        if rows:
            st.dataframe(pd.DataFrame(rows, columns=["ubicacion", "ocupacion_pct [M/C]"]), width="stretch", hide_index=True)
    _section(22, "[M] formulario para título Word §22 p.55", "Sin ubicaciones capturadas no se asignan posiciones.")
    _editor("aleatorio", "Ubicaciones abiertas y lotes")
    _section(23, "[M] formulario para título Word §23 p.55", "La carga nominal debe venir de ficha de proveedor.")
    _editor("estructuras", "Estructuras de almacenaje")
    structures = _case().tables["estructuras"]
    if not structures.empty:
        for row in structures.itertuples():
            if pd.notna(row.capacidad_nominal_kg) and pd.notna(row.carga_prevista_kg) and row.carga_prevista_kg > row.capacidad_nominal_kg:
                st.error(f"{row.estructura}: carga prevista mayor que capacidad nominal.")
    _section(24, "[M] picking; 24 × 250 g y 12 × 500 g [D] Word §9", "Cajas enteras con redondeo hacia arriba.")
    _editor("pedidos", "Pedidos y surtido")
    snap = _snapshot()
    _result_table(snap, "Picking calculado")
    _domain_alerts(snap, "24 ")
    _section(25, "[D] Code 128 propuesto en Word §25; [M] registro", "Identificador demostrativo; no hay lector físico integrado.")
    _editor("identificaciones", "Identificadores y lotes")
    identifiers = _case().tables["identificaciones"]
    if not identifiers.empty and identifiers["codigo"].notna().any():
        sample = identifiers.iloc[0]
        label = f"{sample['codigo']}|{sample['lote']}|{sample['ubicacion']}"
        st.code(label, language="text")
        barcode = code128_svg(label)
        st.image(barcode, caption="Code 128 [M] generado desde el primer registro")
        st.download_button("Descargar etiqueta SVG", barcode, "etiqueta_code128.svg", "image/svg+xml")
    _section(26, "[M] registro para título Word §26 p.55", "Eventos locales; no hay conexión WMS/ERP.")
    _editor("eventos", "Movimientos y trazabilidad")
    _section(27, "[M] modelo de capacidad de muelle; título Word §27 p.55", "Vehículos/turno = piso(tiempo operativo / tiempo por vehículo) × posiciones; no modela colas.")
    _editor("muelles", "Muelle y demanda")
    docks = _case().tables["muelles"]
    if not docks.empty:
        for row in docks.itertuples():
            try:
                cap = dock_capacity(row.posiciones, row.tiempo_operativo_s, row.tiempo_vehiculo_s, row.demanda_vehiculos)
                st.write(f"{row.muelle}: {cap['vehiculos_turno']:.0f} vehículos/turno [M/C]; margen {cap['margen_vehiculos']:.0f}.")
            except ValueError:
                st.info(f"{row.muelle}: capacidad pendiente de parámetros.")
    _section(28, "[D/S] equipos Word §20; [M] ficha de mantenimiento", "Capacidad y costo sin cotización permanecen pendientes.")
    _editor("auxiliar", "Equipamiento auxiliar")


def _sha_plan() -> None:
    _section(29, "[M] formulario para título Word §29 p.55", "Secuencia, rol, frecuencia, PEPS/FEFO y riesgo editables.")
    _editor("operacion", "Estrategia operativa")
    _section(30, "[M] consolidación para título Word §30 p.56", "P/Q/R/S/T y restricciones sincronizados con el escenario.")
    snap = _snapshot()
    _result_table(snap, "PQRST consolidado")
    _editor("planes", "Planes generales A/B/C")
    _section(32, "[M] matriz para título Word §32 p.57", "No se asigna equipo automáticamente sin capacidad e higiene verificadas.")
    _editor("metodos", "Candidatos por ruta y restricciones")
    candidates = _case().tables["metodos"]
    if not candidates.empty:
        tested = []
        for row in candidates.itertuples():
            adequate = pd.notna(row.capacidad_kg) and row.higiene_verificada == True and row.ergonomia_verificada == True
            tested.append((row.ruta, row.equipo_candidato, "Apto según campos capturados [M]" if adequate else "No evaluable / restricción pendiente"))
        st.dataframe(pd.DataFrame(tested, columns=["ruta", "equipo", "evaluacion"]), width="stretch", hide_index=True)


def _economics() -> None:
    _section(34, "[M] LCC complementario; Word §34 p.57 solo reporta resultados", "Word [D]: base $424,267; propuesta $289,135 a 8 años. No recalculados sin flujos.")
    c1, c2 = st.columns(2)
    with c1:
        _numeric("horizonte_anios", "Horizonte", "[D] referencia 8 años", unit="años", positive=True)
    with c2:
        _numeric("tasa_descuento", "Tasa anual", "[M/U] Fracción, ej. 0.10; dejar blanco si no hay dato", unit="fracción")
    c3, c4 = st.columns(2)
    with c3:
        _numeric("tasa_sens_min", "Sensibilidad: tasa mínima", "[M] límite ilustrativo editable, fracción anual", unit="fracción")
    with c4:
        _numeric("tasa_sens_max", "Sensibilidad: tasa máxima", "[M] límite ilustrativo editable, fracción anual", unit="fracción")
    _editor("alternativas", "Inversión y costos por alternativa", source="[M] Plantilla ilustrativa sin cifras. Capture cotizaciones y flujos reales [U].")
    snap = _snapshot()
    _result_table(snap, "LCC calculado", title="LCC nominal y descontado [M/C], separados")
    if "LCC calculado" in snap.tables:
        st.plotly_chart(simple_bars(snap.tables["LCC calculado"], "alternativa", "lcc_nominal_mxn", "Costo de ciclo de vida nominal [M/C]"), width="stretch")
    _result_table(snap, "Sensibilidad LCC", title="Sensibilidad del LCC descontado a la tasa [M/C]")
    if "Sensibilidad LCC" in snap.tables:
        fig = px.line(snap.tables["Sensibilidad LCC"], x="tasa", y="lcc_descontado_mxn", color="alternativa", markers=True, title="Sensibilidad del LCC descontado [M/C]")
        fig.update_xaxes(tickformat=".0%", title="Tasa anual")
        fig.update_yaxes(title="MXN presentes")
        st.plotly_chart(fig, width="stretch")
    _section(35, "[M] payback/VPN complementarios; Word §35 p.57", "Word [D]: VPN $135,132 y recuperación 2.43 años, sin flujos suficientes para auditar.")
    if "payback_b_vs_a_anios" in snap.metrics:
        st.metric("Payback B vs A [M/C]", f"{snap.metrics['payback_b_vs_a_anios']:.2f} años")
    else:
        st.info("Payback: no calculable sin inversión incremental y ahorro neto anual positivo.")
    if "vpn_b_vs_a_mxn" in snap.metrics:
        st.metric("VPN B vs A [M/C]", f"${snap.metrics['vpn_b_vs_a_mxn']:,.2f}")
    else:
        st.info("VPN: no calculable sin inversión, flujos y tasa.")
    _section(36, "[M] matriz configurable; Word §36 p.57 solo título", "Los pesos deben sumar 1 y las calificaciones estar entre 0 y 100.")
    _editor("cualitativa", "Factores, pesos y calificaciones")
    snap = _snapshot()
    _result_table(snap, "Evaluación calculada")
    if "Evaluación calculada" in snap.tables:
        st.plotly_chart(simple_bars(snap.tables["Evaluación calculada"], "alternativa", "puntuacion", "Evaluación cualitativa [M/C]"), width="stretch")
    _section(37, "[D] Word §37 pp.57–58", "El texto recomienda B manual asistido; escenarios nuevos requieren decisión basada en sus insumos.")
    if "Evaluación calculada" in snap.tables and "LCC calculado" in snap.tables:
        quality = snap.tables["Evaluación calculada"].set_index("alternativa")["puntuacion"]
        costs = snap.tables["LCC calculado"].set_index("alternativa")["lcc_nominal_mxn"]
        if quality.idxmax() == costs.idxmin():
            st.success(f"Alternativa {quality.idxmax()} domina en puntaje y costo nominal según los datos capturados [M/C]. Verifique restricciones técnicas.")
        else:
            st.info("La mejor puntuación y el menor costo corresponden a alternativas distintas; decisión multicriterio pendiente.")
    else:
        st.info("Selección calculada pendiente de costos y factores completos. Recomendación documental: B [D].")
    _domain_alerts(snap, "34 ")
    _domain_alerts(snap, "35 ")
    _domain_alerts(snap, "36 ")


def _schedule_audit() -> None:
    _section(38, "[D] Word §38 p.58: 12 semanas; [M] ventanas ilustrativas", "CPM requiere duración y predecesoras completas, sin ciclos.")
    _numeric("semana_referencia", "Plazo de referencia", "[D] 12 semanas", unit="semanas", positive=True)
    _editor("cronograma", "Actividades, duraciones y dependencias")
    snap = _snapshot()
    _result_table(snap, "CPM calculado")
    if "CPM calculado" in snap.tables:
        st.plotly_chart(gantt_chart(snap.tables["CPM calculado"], computed=True), width="stretch")
    elif not _case().tables["cronograma"].empty and _case().tables["cronograma"]["inicio_referencia"].notna().any():
        st.plotly_chart(gantt_chart(_case().tables["cronograma"]), width="stretch")
    _domain_alerts(snap, "38 ")
    _section(39, "[D] Word §39 pp.59–61", "Metas documentales; semáforo solo para mediciones [U].")
    _editor("auditoria", "Diez indicadores y mediciones")
    _editor("pdca", "Bitácora de acciones correctivas PDCA", source="[M] Registro de seguimiento; captura del usuario [U].")
    snap = _snapshot()
    _result_table(snap, "Auditoría evaluada")
    if "Auditoría evaluada" in snap.tables:
        measured = snap.tables["Auditoría evaluada"].dropna(subset=["valor_evaluado"])
        if not measured.empty:
            st.plotly_chart(simple_bars(measured, "indicador", "valor_evaluado", "Mediciones capturadas [U]"), width="stretch")
    _domain_alerts(snap, "39 ")


def _export() -> None:
    st.header("Exportación integral del escenario activo")
    case, snap = _case(), _snapshot()
    st.caption("Excel actual: entradas, origen, alertas y cálculos disponibles. Los faltantes quedan en blanco; sin datos no se reutilizan resultados antiguos.")
    workbook = export_xlsx(case, snap)
    st.download_button("Descargar informe XLSX", workbook, "industrial_app_v2_sha.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
    st.write(f"{len(SHEET_NAMES)} hojas de entradas, {len(snap.tables)} de cálculos, más estado, parámetros y alertas.")
    if snap.tables:
        choice = st.selectbox("CSV de tabla calculada", sorted(snap.tables))
        st.download_button("Descargar CSV calculado", snap.tables[choice].to_csv(index=False).encode("utf-8-sig"), f"{choice.lower().replace(' ', '_')}.csv", "text/csv")
    else:
        st.info("Sin tablas calculadas. El XLSX contiene las entradas vacías y el estado pendiente.")


def run() -> None:
    st.set_page_config(page_title="Industrial App V3 · PYDI SHA", page_icon="🏭", layout="wide")
    if "case" not in st.session_state:
        st.session_state.case = make_example_case()
        st.session_state.revision = 0
        st.session_state.scenario_choice = "Documento (valores reportados)"
    st.title("Industrial App V3 · Estudio SHA de avena con soya")
    st.caption("Caso PYDI · 39 apartados V2 + trazabilidad persistente V3")
    with st.sidebar:
        st.header("Control global")
        st.button("Cargar datos de ejemplo (Proyecto PYDI)", on_click=_load_example, width="stretch")
        st.button("Limpiar todos los datos / Empezar desde cero", on_click=_clear_case, width="stretch")
        if "undo_case" in st.session_state:
            st.button("Deshacer limpieza", on_click=_undo_clear, width="stretch")
        st.button("Desactivar valores ilustrativos [M]", on_click=_without_model, width="stretch")
        st.selectbox(
            "Escenario", ["Documento (valores reportados)", "Resultado calculado", "Nuevo estudio"],
            key="scenario_choice", on_change=_scenario_change,
        )
        group = st.selectbox("Grupo de apartados", GROUPS)
        st.caption("Los botones globales afectan solo formularios V2; inventario y ventas permanecen en SQLite.")
    handlers = (
        _home, _production, _location, _costs, _elements_pq, _loads, _transport,
        _improvement, _quality, _warehouse, _sha_plan, _economics, _schedule_audit, _export, render_inventory,
    )
    handlers[GROUPS.index(group)]()

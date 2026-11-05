"""Simulador académico SHA del caso PYDI, ejecutable con Streamlit."""

import pandas as pd
import streamlit as st

from pydi import datos, graficas
from pydi.calculos import (
    ESTADOS_7R,
    calcular_pareto,
    calcular_pq,
    calcular_rutas,
    exportar_xlsx,
    resumir_7r,
    totales_rutas,
    validar_materiales,
    validar_produccion,
)

st.set_page_config(page_title="Simulador SHA | PYDI", page_icon="🏭", layout="wide")
st.title("Simulador SHA · Planta de avena con soya")
st.caption("Caso académico PYDI · Planeación y diseño de instalaciones · Datos iniciales del Word de referencia")


def estado_inicial() -> None:
    valores = {
        "materiales": datos.materiales_iniciales,
        "siete_r": datos.siete_r_iniciales,
        "pq": datos.pq_inicial,
        "produccion": datos.produccion_inicial,
        "rutas_base": lambda: datos.rutas_iniciales("Base"),
        "rutas_propuestas": lambda: datos.rutas_iniciales("Propuesto"),
        "pareto": datos.pareto_inicial,
    }
    for clave, creador in valores.items():
        if clave not in st.session_state:
            st.session_state[clave] = creador()


def editar(clave: str, columnas: dict | None = None) -> pd.DataFrame:
    tabla = st.data_editor(
        st.session_state[clave], key=f"editor_{clave}", num_rows="dynamic",
        width="stretch", hide_index=True, column_config=columnas,
    )
    st.session_state[clave] = tabla
    return tabla


def intentar(funcion, *args):
    try:
        return funcion(*args), None
    except (ValueError, TypeError, KeyError) as error:
        return None, str(error)


estado_inicial()

resumen, elementos, pq_tab, transporte, graficas_tab, exportacion = st.tabs(
    ["Resumen", "Elementos y 7 R", "Análisis P-Q", "Trabajo de transporte", "Gráficas SHA", "Exportación"]
)

with resumen:
    st.header("Caso y alcance")
    st.write(f"**Producto:** {datos.PRODUCTO}")
    st.write("**Proceso:** producción por lotes; recepción, preparación, tostado, molienda, empaque y almacén.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lote declarado", f"{datos.LOTE_DECLARADO_KG:g} kg")
    c2.metric("Bolsas por lote", "32 × 250 g + 4 × 500 g")
    c3.metric("Propuesta", f"{datos.LOTES_PROPUESTOS_DIA:g} lotes/día")
    c4.metric("Días de operación", f"{datos.DIAS_MES} al mes")
    st.info("Los 7.75 lotes/día corresponden al método propuesto. No representan el ciclo secuencial del método base.")
    st.subheader("Cifras de contexto reportadas")
    c1, c2, c3 = st.columns(3)
    c1.metric("Costo fijo mensual", f"${datos.COSTO_FIJO_MENSUAL:,.2f}")
    c2.metric("Costo variable · bolsa 250 g", f"${datos.COSTO_VARIABLE_250:,.2f}")
    c3.metric("Precio · bolsa 250 g", f"${datos.PRECIO_250:,.2f}")
    st.caption("No se extrapolan precio ni costo unitario a la presentación de 500 g.")
    st.caption(f"Fuente documental: {datos.FUENTE}. Las tablas editables son escenarios hipotéticos a partir de datos reportados; todos los indicadores son cálculos derivados.")
    st.warning("Simulador académico: sus resultados no acreditan el desempeño de una planta en operación.")

with elementos:
    st.header("Registro elemental de materiales")
    st.caption("Consumo y costo por lote reportados. Las 36 bolsas por lote se derivan de las dos presentaciones declaradas.")
    materiales = editar("materiales", {
        "consumo_por_lote": st.column_config.NumberColumn("Consumo por lote", min_value=0.0),
        "costo_por_lote": st.column_config.NumberColumn("Costo por lote ($)", min_value=0.0),
    })
    materiales_ok, error_materiales = intentar(validar_materiales, materiales)
    if error_materiales:
        st.error(error_materiales)
    else:
        masa = materiales_ok.loc[materiales_ok["unidad"].str.lower() == "kg", "consumo_por_lote"].sum()
        costo = materiales_ok["costo_por_lote"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Masa de ingredientes", f"{masa:,.2f} kg/lote")
        c2.metric("Costo de materiales", f"${costo:,.2f}/lote")
        if abs(masa - datos.LOTE_DECLARADO_KG) > 1e-9:
            st.warning(f"Inconsistencia documental: ingredientes {masa:g} kg vs lote declarado {datos.LOTE_DECLARADO_KG:g} kg. No se ajustó la formulación.")
        if abs(costo - datos.COSTO_LOTE_REPORTADO) > 0.01:
            st.warning(f"El costo editado (${costo:,.2f}) difiere de los ${datos.COSTO_LOTE_REPORTADO:,.2f} reportados por lote.")
    st.subheader("Diagnóstico documental de las 7 R")
    siete_r = editar("siete_r", {
        "estado": st.column_config.SelectboxColumn("Estado", options=list(ESTADOS_7R), required=True),
        "notas": st.column_config.TextColumn("Notas"),
    })
    resultado_7r, error_7r = intentar(resumir_7r, siete_r)
    if error_7r:
        st.error(error_7r)
    else:
        _, resumen_7r = resultado_7r
        st.dataframe(resumen_7r, width="stretch", hide_index=True)
        st.caption("Estados iniciales transcritos del Word. Los cambios hechos aquí son evaluaciones hipotéticas editables.")

with pq_tab:
    st.header("Producto y cantidad mensual")
    st.caption("Masa por material reportada en el Word. Porcentajes y acumulados se recalculan con cada edición.")
    pq_entrada = editar("pq", {"kg_mes": st.column_config.NumberColumn("kg/mes", min_value=0.0)})
    pq_ok, error_pq = intentar(calcular_pq, pq_entrada)
    if error_pq:
        st.error(error_pq)
    else:
        st.metric("Masa mensual calculada", f"{pq_ok['kg_mes'].sum():,.1f} kg/mes")
        st.dataframe(pq_ok, width="stretch", hide_index=True)
        st.plotly_chart(graficas.pq_masa(pq_ok), width="stretch")
        st.caption("El total se obtiene de las filas redondeadas; puede diferir de cualquier total textual del documento.")
    st.subheader("Producto terminado")
    produccion_entrada = editar("produccion", {
        "bolsas_mes": st.column_config.NumberColumn("Bolsas/mes", min_value=0.0)
    })
    produccion_ok, error_produccion = intentar(validar_produccion, produccion_entrada)
    if error_produccion:
        st.error(error_produccion)
    else:
        st.plotly_chart(graficas.produccion(produccion_ok), width="stretch")

with transporte:
    st.header("Trabajo de transporte")
    st.latex(r"T.W._i = I_i \times D_i \quad [\mathrm{kg\cdot m/día}]")
    st.caption("Distancia con carga = viajes × distancia. Tiempo = viajes × (2 × distancia / velocidad + carga/descarga).")
    c1, c2, c3 = st.columns(3)
    with c1:
        metodo = st.selectbox("Rutas visibles", ["Base", "Propuesto"])
    with c2:
        velocidad = st.number_input("Velocidad (m/s)", min_value=0.01, value=0.9, step=0.05)
    with c3:
        carga_base = st.number_input("Carga/descarga base (s)", min_value=0.0, value=30.0, step=1.0)
    carga_propuesta = st.number_input("Carga/descarga propuesta (s)", min_value=0.0, value=45.0, step=1.0)
    clave_visible = "rutas_base" if metodo == "Base" else "rutas_propuestas"
    st.caption("Puedes añadir, quitar o modificar rutas. Las rutas del otro método conservan su estado editable.")
    editar(clave_visible, {
        "intensidad_kg_dia": st.column_config.NumberColumn("kg/día", min_value=0.0),
        "viajes_dia": st.column_config.NumberColumn("Viajes/día", min_value=0.0),
        "distancia_m": st.column_config.NumberColumn("Distancia (m)", min_value=0.0),
    })
    base_ok, error_base = intentar(calcular_rutas, st.session_state["rutas_base"], velocidad, carga_base)
    propuesta_ok, error_propuesta = intentar(calcular_rutas, st.session_state["rutas_propuestas"], velocidad, carga_propuesta)
    if error_base:
        st.error(f"Método base: {error_base}")
    if error_propuesta:
        st.error(f"Método propuesto: {error_propuesta}")
    comparacion_ok = None
    if base_ok is not None and propuesta_ok is not None:
        visible = base_ok if metodo == "Base" else propuesta_ok
        st.dataframe(visible, width="stretch", hide_index=True)
        tot_base = totales_rutas(base_ok)
        tot_propuesta = totales_rutas(propuesta_ok)
        comparacion_ok = pd.DataFrame([
            ("T.W. (kg·m/día)", tot_base["tw_kg_m_dia"], tot_propuesta["tw_kg_m_dia"]),
            ("Distancia con carga (m/día)", tot_base["distancia_con_carga_m_dia"], tot_propuesta["distancia_con_carga_m_dia"]),
            ("Tiempo de manejo (min/día)", tot_base["tiempo_manejo_min_dia"], tot_propuesta["tiempo_manejo_min_dia"]),
        ], columns=["indicador", "Base", "Propuesto"])
        st.subheader("Comparación de métodos")
        st.dataframe(comparacion_ok, width="stretch", hide_index=True)
        st.caption("Las diferencias con las referencias redondeadas del Word provienen de las cifras de ruta transcritas.")

with graficas_tab:
    st.header("Gráficas del escenario actual")
    st.caption("Pareto inicial reportado en el Word. Puedes editar sus minutos para analizar otro escenario.")
    pareto_entrada = editar("pareto", {"min_dia": st.column_config.NumberColumn("min/día", min_value=0.0)})
    pareto_ok, error_pareto = intentar(calcular_pareto, pareto_entrada)
    if error_pareto:
        st.error(error_pareto)
    else:
        st.dataframe(pareto_ok, width="stretch", hide_index=True)
        st.plotly_chart(graficas.pareto(pareto_ok), width="stretch")
    if base_ok is not None and propuesta_ok is not None and comparacion_ok is not None:
        st.plotly_chart(graficas.distancia_intensidad(base_ok, propuesta_ok), width="stretch")
        st.plotly_chart(graficas.comparacion(comparacion_ok), width="stretch")
    else:
        st.warning("Corrige las rutas para ver las gráficas de transporte.")

with exportacion:
    st.header("Descargar escenario actual")
    errores = [e for e in (error_materiales, error_7r, error_pq, error_produccion, error_base, error_propuesta, error_pareto) if e]
    if errores:
        st.error("Corrige los datos inválidos antes de exportar: " + " · ".join(errores))
    else:
        parametros = {
            "producto": datos.PRODUCTO,
            "fuente": datos.FUENTE,
            "lote_declarado_kg": datos.LOTE_DECLARADO_KG,
            "lotes_propuestos_dia": datos.LOTES_PROPUESTOS_DIA,
            "dias_mes": datos.DIAS_MES,
            "costo_fijo_mensual": datos.COSTO_FIJO_MENSUAL,
            "costo_variable_bolsa_250": datos.COSTO_VARIABLE_250,
            "precio_bolsa_250": datos.PRECIO_250,
            "velocidad_m_s": velocidad,
            "carga_base_s": carga_base,
            "carga_propuesta_s": carga_propuesta,
            "nota": "Escenario académico editable; cálculos derivados de las tablas actuales.",
        }
        libro, error_libro = intentar(
            exportar_xlsx, parametros, materiales_ok, siete_r, pq_ok, produccion_ok,
            base_ok, propuesta_ok, comparacion_ok, pareto_ok,
        )
        if error_libro:
            st.error(error_libro)
        else:
            st.download_button(
                "Descargar XLSX", libro, file_name="simulador_sha_pydi.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )
            st.caption("Incluye parámetros, materiales, 7 R, P-Q, producción, rutas, cálculos, resumen y Pareto.")

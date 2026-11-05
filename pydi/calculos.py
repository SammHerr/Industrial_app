"""Validaciones, fórmulas y exportación; sin dependencia de Streamlit."""

import math
from io import BytesIO

import pandas as pd

ESTADOS_7R = ("Cumple", "Parcial", "No cumple", "No evaluado")


def _tabla(df: pd.DataFrame, columnas: tuple[str, ...], nombre: str) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError(f"{nombre}: la tabla está vacía.")
    faltan = set(columnas) - set(df.columns)
    if faltan:
        raise ValueError(f"{nombre}: faltan columnas: {', '.join(sorted(faltan))}.")
    return df.copy().reset_index(drop=True)


def _texto(df: pd.DataFrame, columnas: tuple[str, ...], nombre: str) -> None:
    for columna in columnas:
        if df[columna].isna().any() or df[columna].astype(str).str.strip().eq("").any():
            raise ValueError(f"{nombre}: faltan valores en «{columna}».")


def _numeros(df: pd.DataFrame, columnas: tuple[str, ...], nombre: str) -> None:
    for columna in columnas:
        valores = pd.to_numeric(df[columna], errors="coerce")
        if valores.isna().any() or not valores.map(math.isfinite).all():
            raise ValueError(f"{nombre}: «{columna}» requiere números finitos.")
        if (valores < 0).any():
            raise ValueError(f"{nombre}: «{columna}» no admite negativos.")
        df[columna] = valores.astype(float)


def _unicos(df: pd.DataFrame, columna: str, nombre: str) -> None:
    if df[columna].astype(str).str.strip().str.casefold().duplicated().any():
        raise ValueError(f"{nombre}: hay valores duplicados en «{columna}».")


def validar_materiales(df: pd.DataFrame) -> pd.DataFrame:
    columnas = ("codigo", "nombre", "tipo", "unidad", "consumo_por_lote", "costo_por_lote")
    datos = _tabla(df, columnas, "Materiales")
    _texto(datos, columnas[:4], "Materiales")
    _unicos(datos, "codigo", "Materiales")
    _numeros(datos, columnas[4:], "Materiales")
    return datos


def resumir_7r(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    datos = _tabla(df, ("criterio", "estado", "notas"), "7 R")
    _texto(datos, ("criterio", "estado"), "7 R")
    _unicos(datos, "criterio", "7 R")
    if not datos["estado"].isin(ESTADOS_7R).all():
        raise ValueError("7 R: hay estados fuera de las cuatro opciones permitidas.")
    datos["notas"] = datos["notas"].fillna("").astype(str)
    resumen = pd.DataFrame(
        {"estado": ESTADOS_7R, "cantidad": [int((datos["estado"] == e).sum()) for e in ESTADOS_7R]}
    )
    return datos, resumen


def calcular_pq(df: pd.DataFrame) -> pd.DataFrame:
    datos = _tabla(df, ("material", "kg_mes"), "P-Q")
    _texto(datos, ("material",), "P-Q")
    _unicos(datos, "material", "P-Q")
    _numeros(datos, ("kg_mes",), "P-Q")
    total = datos["kg_mes"].sum()
    if total <= 0:
        raise ValueError("P-Q: el total de masa debe ser mayor que cero.")
    datos = datos.sort_values("kg_mes", ascending=False, kind="stable").reset_index(drop=True)
    datos["porcentaje"] = datos["kg_mes"] / total * 100
    datos["acumulado_pct"] = datos["porcentaje"].cumsum()
    return datos


def validar_produccion(df: pd.DataFrame) -> pd.DataFrame:
    datos = _tabla(df, ("presentacion", "bolsas_mes"), "Producción")
    _texto(datos, ("presentacion",), "Producción")
    _unicos(datos, "presentacion", "Producción")
    _numeros(datos, ("bolsas_mes",), "Producción")
    return datos


def calcular_rutas(df: pd.DataFrame, velocidad_m_s: float, carga_s: float) -> pd.DataFrame:
    datos = _tabla(
        df,
        ("id", "origen", "destino", "intensidad_kg_dia", "viajes_dia", "distancia_m"),
        "Rutas",
    )
    _texto(datos, ("id", "origen", "destino"), "Rutas")
    _unicos(datos, "id", "Rutas")
    _numeros(datos, ("intensidad_kg_dia", "viajes_dia", "distancia_m"), "Rutas")
    if not math.isfinite(velocidad_m_s) or velocidad_m_s <= 0:
        raise ValueError("La velocidad debe ser finita y mayor que cero.")
    if not math.isfinite(carga_s) or carga_s < 0:
        raise ValueError("El tiempo de carga/descarga debe ser finito y no negativo.")
    datos["tw_kg_m_dia"] = datos["intensidad_kg_dia"] * datos["distancia_m"]
    datos["distancia_con_carga_m_dia"] = datos["viajes_dia"] * datos["distancia_m"]
    datos["tiempo_manejo_min_dia"] = (
        datos["viajes_dia"] * (2 * datos["distancia_m"] / velocidad_m_s + carga_s) / 60
    )
    return datos


def totales_rutas(df: pd.DataFrame) -> dict[str, float]:
    datos = _tabla(
        df, ("tw_kg_m_dia", "distancia_con_carga_m_dia", "tiempo_manejo_min_dia"), "Cálculos de rutas"
    )
    _numeros(datos, ("tw_kg_m_dia", "distancia_con_carga_m_dia", "tiempo_manejo_min_dia"), "Cálculos de rutas")
    return {columna: float(datos[columna].sum()) for columna in (
        "tw_kg_m_dia", "distancia_con_carga_m_dia", "tiempo_manejo_min_dia"
    )}


def calcular_pareto(df: pd.DataFrame) -> pd.DataFrame:
    datos = _tabla(df, ("causa", "min_dia"), "Pareto")
    _texto(datos, ("causa",), "Pareto")
    _unicos(datos, "causa", "Pareto")
    _numeros(datos, ("min_dia",), "Pareto")
    total = datos["min_dia"].sum()
    if total <= 0:
        raise ValueError("Pareto: el tiempo total debe ser mayor que cero.")
    datos = datos.sort_values("min_dia", ascending=False, kind="stable").reset_index(drop=True)
    datos["porcentaje"] = datos["min_dia"] / total * 100
    datos["acumulado_pct"] = datos["porcentaje"].cumsum()
    return datos


def exportar_xlsx(
    parametros: dict, materiales: pd.DataFrame, siete_r: pd.DataFrame,
    pq: pd.DataFrame, produccion: pd.DataFrame, rutas_base: pd.DataFrame,
    rutas_propuestas: pd.DataFrame, comparacion: pd.DataFrame, pareto: pd.DataFrame,
) -> bytes:
    """Genera el libro desde un conjunto ya validado y calculado en el rerun actual."""
    if not parametros:
        raise ValueError("Faltan parámetros para exportar.")
    hojas = {
        "Parámetros": pd.DataFrame(parametros.items(), columns=["parámetro", "valor"]),
        "Materiales": validar_materiales(materiales),
        "7R": resumir_7r(siete_r)[0],
        "P-Q": calcular_pq(pq[["material", "kg_mes"]]),
        "Producción": validar_produccion(produccion),
        "Rutas base": _tabla(rutas_base, ("id", "tw_kg_m_dia"), "Rutas base"),
        "Rutas propuestas": _tabla(rutas_propuestas, ("id", "tw_kg_m_dia"), "Rutas propuestas"),
        "Resumen": _tabla(comparacion, ("indicador", "Base", "Propuesto"), "Resumen"),
        "Pareto": calcular_pareto(pareto[["causa", "min_dia"]]),
    }
    salida = BytesIO()
    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        for nombre, tabla in hojas.items():
            tabla.to_excel(writer, sheet_name=nombre, index=False)
            hoja = writer.sheets[nombre]
            hoja.freeze_panes = "A2"
            hoja.auto_filter.ref = hoja.dimensions
            for columna in hoja.columns:
                ancho = min(50, max(12, max(len(str(celda.value or "")) for celda in columna) + 2))
                hoja.column_dimensions[columna[0].column_letter].width = ancho
    return salida.getvalue()

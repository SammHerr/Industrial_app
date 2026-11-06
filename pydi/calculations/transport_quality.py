"""T.W., D-I, Pareto, 7R, 5S y auditoría."""

import re

import pandas as pd

from .common import frame, number, reduction, unique_text


def routes(df: pd.DataFrame, lots_day: float | None, speed: float | None, load_s: float | None) -> pd.DataFrame:
    data = frame(df, ("id", "origen_area", "destino_area", "kg_lote_equiv", "intensidad_manual_kg_dia", "viajes_dia", "distancia_m"), "Rutas")
    unique_text(data, "id", "Rutas")
    v = number(speed, "Velocidad", positive=True)
    load = number(load_s, "Carga/descarga")
    per_day = number(lots_day, "Lotes/día", positive=True)
    for col in ("origen_area", "destino_area"):
        if data[col].isna().any() or data[col].astype(str).str.strip().eq("").any():
            raise ValueError(f"Rutas: {col} vacío.")
    intensities = []
    origins = []
    for row in data.itertuples():
        if pd.notna(row.intensidad_manual_kg_dia) and row.intensidad_manual_kg_dia != "":
            intensities.append(number(row.intensidad_manual_kg_dia, f"Intensidad {row.id}"))
            origins.append("[U] manual")
        else:
            intensities.append(number(row.kg_lote_equiv, f"kg/lote {row.id}") * per_day)
            origins.append("[C] kg/lote × lotes/día")
    data["intensidad_kg_dia"] = intensities
    data["origen_intensidad"] = origins
    data["viajes_dia"] = [number(x, "Viajes/día") for x in data["viajes_dia"]]
    data["distancia_m"] = [number(x, "Distancia") for x in data["distancia_m"]]
    data["tw_kg_m_dia"] = data["intensidad_kg_dia"] * data["distancia_m"]
    data["distancia_con_carga_m_dia"] = data["viajes_dia"] * data["distancia_m"]
    data["tiempo_manejo_s_dia"] = data["viajes_dia"] * (2 * data["distancia_m"] / v + load)
    data["tiempo_manejo_min_dia"] = data["tiempo_manejo_s_dia"] / 60
    data["clase_di"] = data.apply(
        lambda row: ("Manejo simple" if row.distancia_m <= 15 else "Transporte simple")
        if row.intensidad_kg_dia < 1000 else "Fuera del criterio documental", axis=1,
    )
    return data


def route_summary(base: pd.DataFrame, proposed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, label, unit in (
        ("tw_kg_m_dia", "Trabajo de transporte", "kg·m/día"),
        ("distancia_con_carga_m_dia", "Distancia con carga", "m/día"),
        ("tiempo_manejo_s_dia", "Tiempo de manejo", "s/día"),
        ("viajes_dia", "Viajes", "viajes/día"),
    ):
        b, p = float(base[col].sum()), float(proposed[col].sum())
        rows.append((label, b, p, reduction(b, p), unit, "[C] Word §12"))
    return pd.DataFrame(rows, columns=["indicador", "base", "propuesto", "reduccion_pct", "unidad", "origen"])


def pareto(df: pd.DataFrame) -> pd.DataFrame:
    data = frame(df, ("causa", "min_dia"), "Pareto")
    unique_text(data, "causa", "Pareto")
    data["min_dia"] = [number(x, "Minutos Pareto") for x in data["min_dia"]]
    total = data["min_dia"].sum()
    if total <= 0:
        raise ValueError("Pareto: el total debe ser positivo.")
    data = data.sort_values("min_dia", ascending=False, kind="stable").reset_index(drop=True)
    data["porcentaje"] = data["min_dia"] / total * 100
    data["acumulado_pct"] = data["porcentaje"].cumsum()
    return data


def five_s(df: pd.DataFrame) -> dict[str, float]:
    data = frame(df, ("numero", "s", "criterio", "puntaje"), "5S")
    if len(data) != 20:
        raise ValueError("5S: se necesitan exactamente 20 criterios.")
    if data["puntaje"].isna().any() or data["puntaje"].astype(str).str.strip().eq("").any():
        raise ValueError("5S: auditoría incompleta; los blancos no cuentan como cero.")
    points = [number(x, "Puntaje 5S") for x in data["puntaje"]]
    if any(x not in (0, 1, 2) for x in points):
        raise ValueError("5S: cada puntaje debe ser 0, 1 o 2.")
    return {"puntos": sum(points), "maximo": 40, "porcentaje": sum(points) / 40 * 100}


def seven_r(df: pd.DataFrame) -> dict[str, int]:
    data = frame(df, ("criterio", "estado"), "7 R")
    unique_text(data, "criterio", "7 R")
    allowed = ("Cumple", "Parcial", "No cumple", "No evaluado")
    if not data["estado"].isin(allowed).all():
        raise ValueError("7 R: estado inválido.")
    return {state: int((data["estado"] == state).sum()) for state in allowed}


def occupancy(total: float | None, occupied: float | None) -> float:
    t = number(total, "Posiciones totales", positive=True)
    o = number(occupied, "Posiciones ocupadas")
    if o > t:
        raise ValueError("Ocupación: las posiciones ocupadas exceden las disponibles.")
    return o / t * 100


def audit_measurements(df: pd.DataFrame) -> pd.DataFrame:
    """Evalúa solo mediciones [U], no metas ni simulaciones como observaciones."""
    data = frame(df, ("indicador", "meta", "sentido", "numerador", "denominador", "medicion"), "Auditoría")
    unique_text(data, "indicador", "Auditoría")
    values, statuses = [], []
    ratios = {"Exactitud de inventario", "Cumplimiento PEPS/FEFO", "Merma por manejo", "Cumplimiento 5S", "Mantenimiento de equipo de manejo", "Ocupación de almacenes"}
    for row in data.itertuples():
        value = row.medicion
        if pd.isna(value) or value == "":
            if pd.notna(row.numerador) and pd.notna(row.denominador) and row.numerador != "" and row.denominador != "":
                top = number(row.numerador, f"Numerador {row.indicador}")
                bottom = number(row.denominador, f"Denominador {row.indicador}", positive=True)
                value = top / bottom * 100 if row.indicador in ratios else top / bottom
            else:
                values.append(None)
                statuses.append("Sin medición")
                continue
        value = number(value, f"Medición {row.indicador}")
        match = re.search(r"\d+(?:\.\d+)?", str(row.meta))
        if not match or row.sentido not in ("≤", "≥"):
            raise ValueError(f"Auditoría: meta o sentido inválido de {row.indicador}.")
        target = float(match.group())
        passed = value <= target if row.sentido == "≤" else value >= target
        values.append(value)
        statuses.append("Cumple" if passed else "Fuera de meta")
    data["valor_evaluado"] = values
    data["estado"] = statuses
    return data

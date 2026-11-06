"""Disponibilidad, capacidad y presentaciones: Word §2, pp.9–11."""

import math

import pandas as pd

from .common import frame, number, unique_text


def capacity(params: dict) -> dict[str, float]:
    shift = number(params.get("turno_s"), "Turno", positive=True)
    setup = number(params.get("preparacion_s"), "Preparación")
    meal = number(params.get("comida_s"), "Comida")
    cycle = number(params.get("ciclo_s"), "Ciclo", positive=True)
    lot_kg = number(params.get("lote_objetivo_kg"), "Lote", positive=True)
    available = shift - setup - meal
    if available <= 0:
        raise ValueError("Capacidad: el tiempo disponible debe ser mayor que cero.")
    lots = available / cycle
    return {
        "disponible_s": available,
        "lotes_continuos": lots,
        "lotes_completos": math.floor(lots),
        "kg_continuos": lots * lot_kg,
    }


def production(params: dict) -> dict[str, float]:
    lots = number(params.get("lotes_propuestos_dia"), "Lotes propuestos/día", positive=True)
    days = number(params.get("dias_mes"), "Días/mes", positive=True)
    bags_250 = number(params.get("bolsas_250_lote"), "Bolsas 250 g/lote")
    bags_500 = number(params.get("bolsas_500_lote"), "Bolsas 500 g/lote")
    lot_kg = number(params.get("lote_objetivo_kg"), "Lote", positive=True)
    packed_kg = bags_250 * 0.25 + bags_500 * 0.5
    return {
        "lotes_mes": lots * days,
        "bolsas_250_mes": lots * days * bags_250,
        "bolsas_500_mes": lots * days * bags_500,
        "bolsas_total_mes": lots * days * (bags_250 + bags_500),
        "kg_empacados_lote": packed_kg,
        "diferencia_empaque_kg": packed_kg - lot_kg,
    }


def ingredients(df: pd.DataFrame) -> pd.DataFrame:
    data = frame(df, ("codigo", "nombre", "kg_lote", "costo_kg_mxn"), "Ingredientes")
    unique_text(data, "codigo", "Ingredientes")
    unique_text(data, "nombre", "Ingredientes")
    for col in ("kg_lote", "costo_kg_mxn"):
        data[col] = [number(value, col) for value in data[col]]
    data["costo_lote_mxn"] = data["kg_lote"] * data["costo_kg_mxn"]
    return data


def pq(df: pd.DataFrame, ingredients_df: pd.DataFrame, params: dict) -> pd.DataFrame:
    data = frame(df, ("material", "kg_mes_reportado", "kg_lote_equiv"), "P-Q")
    unique_text(data, "material", "P-Q")
    lots = number(params.get("lotes_propuestos_dia"), "Lotes propuestos/día", positive=True)
    days = number(params.get("dias_mes"), "Días/mes", positive=True)
    ing = {str(row.nombre).casefold(): row.kg_lote for row in ingredients_df.itertuples()}
    per_lot = []
    for row in data.itertuples():
        factor = ing.get(str(row.material).casefold())
        if factor is None:
            factor = number(row.kg_lote_equiv, f"P-Q: factor {row.material}")
        per_lot.append(factor)
    data["kg_lote_aplicado"] = per_lot
    data["kg_mes_calculado"] = data["kg_lote_aplicado"] * lots * days
    total = data["kg_mes_calculado"].sum()
    if total <= 0:
        raise ValueError("P-Q: el total calculado debe ser positivo.")
    data["kg_mes_reportado"] = [number(value, "Masa reportada") for value in data["kg_mes_reportado"]]
    data = data.sort_values("kg_mes_calculado", ascending=False, kind="stable").reset_index(drop=True)
    data["porcentaje"] = data["kg_mes_calculado"] / total * 100
    data["acumulado_pct"] = data["porcentaje"].cumsum()
    a = params.get("factor_abc_a")
    b = params.get("factor_abc_b")
    if a is not None and b is not None:
        a = number(a, "Límite ABC A")
        b = number(b, "Límite ABC B")
        if not 0 < a < b < 100:
            raise ValueError("ABC [M]: se requieren 0 < límite A < límite B < 100.")
        data["clase_abc_m"] = data["acumulado_pct"].map(
            lambda x: "A" if x <= a else ("B" if x <= b else "C")
        )
    return data

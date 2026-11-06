"""Ponderación §3 y punto de equilibrio §4 del Word."""

import math

import pandas as pd

from .common import frame, number, unique_text


def location_scores(df: pd.DataFrame) -> dict[str, float]:
    data = frame(df, ("factor", "peso", "Union Juarez", "Cacahoatan", "Tapachula"), "Localización")
    unique_text(data, "factor", "Localización")
    weights = [number(x, "Peso") for x in data["peso"]]
    if abs(sum(weights) - 1) > 1e-6:
        raise ValueError("Localización: los pesos deben sumar 1.0000 (100 %).")
    result = {}
    for name in ("Union Juarez", "Cacahoatan", "Tapachula"):
        scores = [number(x, f"Calificación de {name}") for x in data[name]]
        if any(x > 100 for x in scores):
            raise ValueError(f"Localización: {name} tiene calificación mayor que 100.")
        result[name] = sum(w * score for w, score in zip(weights, scores))
    return result


def fixed_costs(df: pd.DataFrame) -> float:
    data = frame(df, ("concepto", "mxn_mes"), "Costos fijos")
    unique_text(data, "concepto", "Costos fijos")
    return sum(number(x, "Costo fijo mensual") for x in data["mxn_mes"])


def break_even(fixed_mxn: float, price: float | None, variable: float | None) -> dict[str, float]:
    cf = number(fixed_mxn, "Costo fijo")
    p = number(price, "Precio 250 g", positive=True)
    cvu = number(variable, "Costo variable 250 g")
    if p <= cvu:
        raise ValueError("Punto de equilibrio: el precio debe superar al costo variable unitario.")
    exact = cf / (p - cvu)
    return {"bolsas_reales": exact, "bolsas_enteras": math.ceil(exact), "ventas_equilibrio_mxn": exact * p}

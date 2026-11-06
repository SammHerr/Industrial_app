"""Complementos [M]: estiba, picking, muelles, LCC, VPN y multicriterio."""

import math

import pandas as pd

from .common import frame, number, unique_text


def pallet_geometry(params: dict) -> dict[str, float | bool]:
    pl = number(params.get("tarima_largo_cm"), "Largo tarima", positive=True)
    pw = number(params.get("tarima_ancho_cm"), "Ancho tarima", positive=True)
    bl = number(params.get("caja_largo_cm"), "Largo caja", positive=True)
    bw = number(params.get("caja_ancho_cm"), "Ancho caja", positive=True)
    boxes = number(params.get("cajas_capa"), "Cajas/cama", positive=True)
    layers = number(params.get("capas"), "Camas", positive=True)
    if boxes != int(boxes) or layers != int(layers):
        raise ValueError("Estiba: cajas/cama y camas deben ser enteros.")
    fit_straight = math.floor(pl / bl) * math.floor(pw / bw)
    fit_rotated = math.floor(pl / bw) * math.floor(pw / bl)
    fit = max(fit_straight, fit_rotated)
    return {"cajas_capa_max_rejilla": fit, "cabe_geometria": boxes <= fit, "cajas_tarima": boxes * layers}


def picking(df: pd.DataFrame) -> pd.DataFrame:
    data = frame(df, ("pedido", "bolsas_250", "bolsas_500", "distancia_m"), "Picking")
    unique_text(data, "pedido", "Picking")
    for col in ("bolsas_250", "bolsas_500"):
        data[col] = [number(x, col) for x in data[col]]
        if any(x != int(x) for x in data[col]):
            raise ValueError(f"Picking: {col} requiere unidades enteras.")
    data["cajas_250_calculadas"] = data["bolsas_250"].map(lambda x: math.ceil(x / 24))
    data["cajas_500_calculadas"] = data["bolsas_500"].map(lambda x: math.ceil(x / 12))
    return data


def dock_capacity(positions, shift_s, service_s, demand) -> dict[str, float]:
    p = number(positions, "Posiciones de muelle", positive=True)
    shift = number(shift_s, "Tiempo operativo", positive=True)
    service = number(service_s, "Tiempo por vehículo", positive=True)
    d = number(demand, "Demanda de vehículos")
    cap = math.floor(shift / service) * p
    return {"vehiculos_turno": cap, "margen_vehiculos": cap - d}


def life_cycle(row: pd.Series | dict, years, rate=None) -> dict[str, float]:
    n = number(years, "Horizonte", positive=True)
    if n != int(n):
        raise ValueError("LCC: horizonte en años enteros.")
    investment = number(row["inversion_mxn"], "Inversión", positive=True)
    operating = number(row["operacion_anual_mxn"], "Operación anual")
    maintenance = number(row["mantenimiento_anual_mxn"], "Mantenimiento anual")
    reinvestment = number(row["reinversion_mxn"], "Reinversión")
    residual = number(row["residual_mxn"], "Residual")
    disposal = number(row["disposicion_mxn"], "Disposición")
    nominal = investment + n * (operating + maintenance) + reinvestment - residual + disposal
    result = {"lcc_nominal_mxn": nominal}
    if rate is not None:
        r = number(rate, "Tasa")
        if r > 1:
            raise ValueError("Tasa: use fracción anual, por ejemplo 0.10.")
        annuity = sum((operating + maintenance) / (1 + r) ** year for year in range(1, int(n) + 1))
        result["lcc_descontado_mxn"] = investment + annuity + (reinvestment + disposal - residual) / (1 + r) ** n
    return result


def payback(investment, annual_saving) -> float:
    inv = number(investment, "Inversión incremental", positive=True)
    saving = number(annual_saving, "Ahorro neto anual", positive=True)
    return inv / saving


def npv(investment, cashflows: list[float], rate) -> float:
    inv = number(investment, "Inversión incremental", positive=True)
    r = number(rate, "Tasa")
    if r > 1 or not cashflows:
        raise ValueError("VPN: tasa en fracción y flujos anuales necesarios.")
    flows = [number(x, "Flujo neto") for x in cashflows]
    return -inv + sum(flow / (1 + r) ** year for year, flow in enumerate(flows, 1))


def multicriteria(df: pd.DataFrame) -> dict[str, float]:
    data = frame(df, ("factor", "peso", "A", "B", "C"), "Evaluación cualitativa")
    unique_text(data, "factor", "Evaluación cualitativa")
    weights = [number(x, "Peso") for x in data["peso"]]
    if abs(sum(weights) - 1) > 1e-6:
        raise ValueError("Evaluación cualitativa: pesos deben sumar 1.0000.")
    result = {}
    for name in ("A", "B", "C"):
        scores = [number(x, f"Puntuación {name}") for x in data[name]]
        if any(x > 100 for x in scores):
            raise ValueError("Evaluación cualitativa: escala máxima 100.")
        result[name] = sum(w * score for w, score in zip(weights, scores))
    return result

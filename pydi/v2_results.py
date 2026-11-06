"""Calcula un snapshot coherente desde un único Case; nunca usa cachés obsoletos."""

from dataclasses import dataclass, field

import pandas as pd

from pydi.calculations.location_costs import break_even, fixed_costs, location_scores
from pydi.calculations.production import capacity, ingredients, pq, production
from pydi.calculations.schedule import cpm
from pydi.calculations.storage_finance import (
    life_cycle,
    multicriteria,
    npv,
    pallet_geometry,
    payback,
    picking,
)
from pydi.calculations.transport_quality import (
    audit_measurements,
    five_s,
    pareto,
    route_summary,
    routes,
    seven_r,
)
from pydi.v2_model import Case


@dataclass
class Snapshot:
    metrics: dict[str, object] = field(default_factory=dict)
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    alerts: list[tuple[str, str, str]] = field(default_factory=list)

    def alert(self, severity: str, section: str, message: str) -> None:
        self.alerts.append((severity, section, message))


def compute_case(case: Case) -> Snapshot:
    """Resultados por dominio; una sección inválida no detiene las demás."""
    snap = Snapshot()
    if all(table.empty for table in case.tables.values()) and all(v is None for v in case.params.values()):
        snap.alert("Información", "Inicio", "Sin datos. Capture entradas o cargue el ejemplo PYDI.")
        return snap

    def attempt(section: str, key: str, function, *args):
        try:
            value = function(*args)
        except (ValueError, TypeError, KeyError, ZeroDivisionError) as exc:
            snap.alert("Pendiente", section, str(exc))
            return None
        snap.metrics[key] = value
        return value

    ing = attempt("1 Producto", "ingredientes", ingredients, case.tables["ingredientes"])
    if ing is not None:
        snap.tables["Ingredientes calculados"] = ing
        mass = float(ing["kg_lote"].sum())
        cost = float(ing["costo_lote_mxn"].sum())
        snap.metrics["masa_entrada_kg"] = mass
        snap.metrics["costo_ingredientes_mxn"] = cost
        packaging = case.params.get("empaque_lote_mxn")
        if packaging is not None:
            if packaging < 0:
                snap.alert("Error", "1 Producto", "El costo del empaque por lote no puede ser negativo.")
            else:
                snap.metrics["costo_total_lote_mxn"] = cost + packaging
        target = case.params.get("lote_objetivo_kg")
        if target is not None and abs(mass - target) > 1e-6:
            snap.alert("Advertencia", "1 Producto", f"Ingredientes {mass:g} kg/lote [C] frente a lote declarado {target:g} kg [D]. Diferencia sin atribución experimental de merma.")
    attempt("2 Proceso", "capacidad", capacity, case.params)
    prod = attempt("2 Proceso", "produccion", production, case.params)
    if prod is not None and abs(prod["diferencia_empaque_kg"]) > 1e-6:
        snap.alert("Advertencia", "2 Proceso", "La masa en bolsas no coincide con el lote objetivo.")
    product = "Polvo de avena con soya" if not case.tables["ingredientes"].empty else "Pendiente"
    days = case.params.get("dias_mes")
    snap.tables["PQRST consolidado"] = pd.DataFrame([
        ("P", product, "[D/U]"),
        ("Q", f"{prod['lotes_mes']:.3f} lotes/mes" if prod is not None else "Pendiente", "[C]"),
        ("R", f"{len(case.tables['rutas_propuestas'])} rutas propuestas" if not case.tables["rutas_propuestas"].empty else "Pendiente", "[D/U]"),
        ("S", "Manual asistido" if case.mode.startswith("Documento") else "Por definir", "[D/M]"),
        ("T", f"{days:g} días/mes" if days is not None else "Pendiente", "[D/U]"),
    ], columns=["elemento", "valor", "origen"])
    scores = attempt("3 Localización", "localizacion", location_scores, case.tables["localizacion"])
    if scores is not None:
        snap.tables["Localización calculada"] = pd.DataFrame(scores.items(), columns=["municipio", "puntuacion"])
    fixed = attempt("4 Costos", "costo_fijo_mxn_mes", fixed_costs, case.tables["costos_fijos"])
    if fixed is not None:
        qe = attempt("4 Costos", "equilibrio", break_even, fixed, case.params.get("precio_250_mxn"), case.params.get("cvu_250_mxn"))
        if qe is not None and case.mode.startswith("Documento") and qe["bolsas_enteras"] != 8055:
            snap.alert("Advertencia", "4 Costos", f"Word: 8,055 bolsas [D]; recomputado: {qe['bolsas_reales']:.4f} y {qe['bolsas_enteras']} bolsas enteras [C].")
    if ing is not None:
        pq_table = attempt("7 P-Q", "pq", pq, case.tables["pq"], ing, case.params)
        if pq_table is not None:
            snap.tables["P-Q calculado"] = pq_table
            if case.mode.startswith("Documento"):
                reported = float(pq_table["kg_mes_reportado"].sum())
                if abs(reported - 2553.0) > 0.01:
                    snap.alert("Advertencia", "7 P-Q", f"Word total: 2,553.0 kg [D]; suma de filas redondeadas: {reported:,.1f} kg [C].")
    base = attempt("12 Transporte", "rutas_base", routes, case.tables["rutas_base"], case.params.get("lotes_propuestos_dia"), case.params.get("velocidad_m_s"), case.params.get("carga_base_s"))
    proposed = attempt("12 Transporte", "rutas_propuestas", routes, case.tables["rutas_propuestas"], case.params.get("lotes_propuestos_dia"), case.params.get("velocidad_m_s"), case.params.get("carga_propuesta_s"))
    if base is not None:
        snap.tables["TW base calculado"] = base
    if proposed is not None:
        snap.tables["TW propuesto calculado"] = proposed
    if base is not None and proposed is not None:
        comparison = route_summary(base, proposed)
        snap.metrics["comparacion_transporte"] = comparison
        snap.tables["Comparación transporte"] = comparison
        if case.mode.startswith("Documento"):
            for column, label, reference in (
                ("tw_kg_m_dia", "T.W. base", 8417.6),
                ("distancia_con_carga_m_dia", "Distancia base", 2388.2),
                ("tiempo_manejo_s_dia", "Tiempo base", 9911.4),
            ):
                current = float(base[column].sum())
                if abs(current - reference) > 0.05:
                    snap.alert("Información", "12 Transporte", f"{label}: {current:,.2f} recalculado vs {reference:,.1f} reportado; rutas redondeadas.")
    par = attempt("16 Pareto", "pareto", pareto, case.tables["pareto"])
    if par is not None:
        snap.tables["Pareto calculado"] = par
        if case.mode.startswith("Documento"):
            total = float(par["min_dia"].sum())
            if abs(total - 165.2) > 0.01:
                snap.alert("Advertencia", "16 Pareto", f"Causas redondeadas: {total:.1f} min/día [C]; total textual Word: 165.2 [D].")
    attempt("6 Siete R", "siete_r", seven_r, case.tables["siete_r"])
    attempt("18 Cinco S", "cinco_s", five_s, case.tables["cinco_s"])
    geometry = attempt("11 Estiba", "estiba", pallet_geometry, case.params)
    if geometry is not None:
        if not geometry["cabe_geometria"]:
            snap.alert("Error", "11 Estiba", "La cantidad de cajas por cama no cabe en la rejilla rectangular calculada.")
        if case.params.get("capacidad_tarima_kg") is None:
            snap.alert("Pendiente", "11 Estiba", "Capacidad nominal de tarima sin dato; integridad estructural no verificada.")
    if not case.tables["pedidos"].empty:
        pick = attempt("24 Picking", "picking", picking, case.tables["pedidos"])
        if pick is not None:
            snap.tables["Picking calculado"] = pick
    if not case.tables["cualitativa"].empty:
        qualitative = attempt("36 Evaluación", "multicriterio", multicriteria, case.tables["cualitativa"])
        if qualitative is not None:
            snap.tables["Evaluación calculada"] = pd.DataFrame(qualitative.items(), columns=["alternativa", "puntuacion"])
    else:
        snap.alert("Pendiente", "36 Evaluación", "Sin factores y pesos: no hay recomendación calculada.")
    if not case.tables["cronograma"].empty:
        schedule = attempt("38 Cronograma", "cpm", cpm, case.tables["cronograma"])
        if schedule is not None:
            snap.tables["CPM calculado"] = schedule
    alternatives = case.tables["alternativas"]
    finance_rows = []
    if not alternatives.empty:
        for _, row in alternatives.iterrows():
            try:
                result = life_cycle(row, case.params.get("horizonte_anios"), case.params.get("tasa_descuento"))
                finance_rows.append({"alternativa": row["alternativa"], **result, "origen": "[M] complemento metodológico"})
            except (ValueError, KeyError, TypeError) as exc:
                snap.alert("Pendiente", "34 Economía", f"Alternativa {row.get('alternativa', '?')}: {exc}")
        if finance_rows:
            snap.tables["LCC calculado"] = pd.DataFrame(finance_rows)
        low = case.params.get("tasa_sens_min")
        high = case.params.get("tasa_sens_max")
        if low is not None and high is not None:
            if not (0 <= low <= high <= 1):
                snap.alert("Error", "34 Economía", "Sensibilidad: tasas en fracción entre 0 y 1, mínimo ≤ máximo.")
            else:
                sensitivity = []
                for _, row in alternatives.iterrows():
                    for index in range(11):
                        rate = low + (high - low) * index / 10
                        try:
                            result = life_cycle(row, case.params.get("horizonte_anios"), rate)
                            sensitivity.append({"alternativa": row["alternativa"], "tasa": rate, "lcc_descontado_mxn": result["lcc_descontado_mxn"], "origen": "[M/C] 11 puntos uniformes"})
                        except (ValueError, KeyError, TypeError):
                            break
                if sensitivity:
                    snap.tables["Sensibilidad LCC"] = pd.DataFrame(sensitivity)
        by_name = alternatives.set_index("alternativa") if "alternativa" in alternatives else pd.DataFrame()
        if "A" in by_name.index and "B" in by_name.index:
            a, b = by_name.loc["A"], by_name.loc["B"]
            try:
                incremental = float(b["inversion_mxn"]) - float(a["inversion_mxn"])
                annual = b["ahorro_neto_anual_mxn"]
                snap.metrics["payback_b_vs_a_anios"] = payback(incremental, annual)
                if case.params.get("tasa_descuento") is not None:
                    years = int(case.params["horizonte_anios"])
                    snap.metrics["vpn_b_vs_a_mxn"] = npv(incremental, [annual] * years, case.params["tasa_descuento"])
            except (ValueError, TypeError, KeyError):
                snap.alert("Pendiente", "35 Payback", "Inversión incremental y ahorro neto positivo necesarios; VPN requiere además tasa.")
    if case.mode.startswith("Documento"):
        snap.alert("Información", "34–35 Economía", "Word: LCC base $424,267, propuesta $289,135, VPN $135,132 y payback 2.43 años [D]; faltan flujos para recalcular.")
    if case.tables["auditoria"].empty:
        snap.alert("Pendiente", "39 Auditoría", "Sin indicadores ni mediciones.")
    else:
        audit = attempt("39 Auditoría", "auditoria", audit_measurements, case.tables["auditoria"])
        if audit is not None:
            snap.tables["Auditoría evaluada"] = audit
        if audit is not None and (audit["estado"] == "Sin medición").all():
            snap.alert("Pendiente", "39 Auditoría", "Metas documentales cargadas; aún no hay mediciones reales.")
    return snap


def alerts_frame(snapshot: Snapshot) -> pd.DataFrame:
    return pd.DataFrame(snapshot.alerts, columns=["nivel", "apartado", "detalle"])

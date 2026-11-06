from io import BytesIO

import pandas as pd
import pytest

from pydi.calculations.location_costs import break_even, location_scores
from pydi.calculations.schedule import cpm
from pydi.calculations.storage_finance import (
    dock_capacity,
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
    occupancy,
    routes,
    seven_r,
)
from pydi.v2_barcode import code128_svg
from pydi.v2_charts import layout_chart, pq_chart, tw_chart
from pydi.v2_model import (
    TABLE_COLUMNS,
    make_empty_case,
    make_example_case,
    without_illustrative_values,
)
from pydi.v2_reports import export_xlsx
from pydi.v2_results import compute_case


def test_seed_coverage_and_capacity():
    case = make_example_case()
    result = compute_case(case)
    assert len(case.tables) == len(TABLE_COLUMNS) == 38
    assert len(case.tables["elementos"]) == 42
    assert len(case.tables["cinco_s"]) == 20
    assert result.metrics["capacidad"]["disponible_s"] == 28200
    assert result.metrics["capacidad"]["lotes_continuos"] == pytest.approx(28200 / 10200)
    assert result.metrics["capacidad"]["lotes_completos"] == 2
    assert result.metrics["masa_entrada_kg"] == pytest.approx(11.75)
    assert result.metrics["produccion"]["kg_empacados_lote"] == 10
    assert result.metrics["costo_ingredientes_mxn"] == 425
    assert result.metrics["costo_total_lote_mxn"] == 455


def test_equilibrium_and_word_discrepancy():
    result = compute_case(make_example_case())
    assert result.metrics["costo_fijo_mxn_mes"] == 190300
    assert result.metrics["equilibrio"]["bolsas_reales"] == pytest.approx(8056.7315834)
    assert result.metrics["equilibrio"]["bolsas_enteras"] == 8057
    assert any("8,055" in message for _, _, message in result.alerts)
    with pytest.raises(ValueError, match="precio"):
        break_even(190300, 10, 11.38)


def test_location_weights_and_scores():
    case = make_example_case()
    assert location_scores(case.tables["localizacion"]) == {
        "Union Juarez": 54.75, "Cacahoatan": 70.0, "Tapachula": 86.0,
    }
    case.tables["localizacion"].loc[0, "peso"] = 0.2
    with pytest.raises(ValueError, match="sumar"):
        location_scores(case.tables["localizacion"])


def test_production_pq_and_reactivity():
    case = make_example_case()
    first = compute_case(case)
    assert first.metrics["produccion"]["bolsas_250_mes"] == 6448
    assert first.metrics["produccion"]["bolsas_500_mes"] == 806
    assert first.metrics["produccion"]["bolsas_total_mes"] == 7254
    assert case.tables["pq"]["kg_mes_reportado"].sum() == pytest.approx(2553.1)
    assert any("2,553.0" in message for _, _, message in first.alerts)
    old_mass = first.tables["P-Q calculado"].loc[lambda d: d.material == "Soya", "kg_mes_calculado"].iloc[0]
    old_chart = pq_chart(first.tables["P-Q calculado"]).data[0].y[0]
    case.params["lotes_propuestos_dia"] = 8.0
    updated = compute_case(case)
    new_mass = updated.tables["P-Q calculado"].loc[lambda d: d.material == "Soya", "kg_mes_calculado"].iloc[0]
    assert new_mass > old_mass
    assert pq_chart(updated.tables["P-Q calculado"]).data[0].y[0] > old_chart
    case.tables["ingredientes"].loc[case.tables["ingredientes"].nombre == "Soya", "kg_lote"] = 7
    assert compute_case(case).tables["P-Q calculado"].loc[lambda d: d.material == "Soya", "kg_mes_calculado"].iloc[0] == 7 * 8 * 26


def test_transport_totals_classification_and_override():
    case = make_example_case()
    snap = compute_case(case)
    comparison = snap.tables["Comparación transporte"].set_index("indicador")
    assert comparison.loc["Trabajo de transporte", "base"] == pytest.approx(8417.6, abs=1)
    assert comparison.loc["Trabajo de transporte", "propuesto"] == pytest.approx(5048.3, abs=1)
    assert comparison.loc["Distancia con carga", "base"] == pytest.approx(2388.2, abs=1)
    assert comparison.loc["Tiempo de manejo", "base"] == pytest.approx(9911.4, abs=1)
    assert snap.tables["TW propuesto calculado"]["clase_di"].value_counts()["Manejo simple"] == 8
    assert case.params["retorno_vacio_viajes"] * case.params["retorno_vacio_m"] == 63
    before = snap.tables["TW base calculado"].loc[0, "tw_kg_m_dia"]
    case.tables["rutas_base"].loc[0, "intensidad_manual_kg_dia"] = 120
    after = compute_case(case).tables["TW base calculado"].loc[0, "tw_kg_m_dia"]
    assert after == 120 * 6.5 and after > before
    assert tw_chart(snap.tables["TW base calculado"], snap.tables["TW propuesto calculado"]).data[0].y[0] == before
    bad = case.tables["rutas_base"].copy()
    bad.loc[1, "id"] = bad.loc[0, "id"]
    with pytest.raises(ValueError, match="duplicado"):
        routes(bad, 7.75, 0.9, 30)


def test_pareto_7r_5s_missing_and_complete():
    case = make_example_case()
    snap = compute_case(case)
    assert snap.tables["Pareto calculado"]["min_dia"].sum() == pytest.approx(165.1)
    assert snap.tables["Pareto calculado"]["acumulado_pct"].iloc[-1] == pytest.approx(100)
    assert seven_r(case.tables["siete_r"])["Parcial"] == 5
    assert seven_r(case.tables["siete_r"])["No cumple"] == 2
    with pytest.raises(ValueError, match="incompleta"):
        five_s(case.tables["cinco_s"])
    case.tables["cinco_s"]["puntaje"] = [2] * 20
    assert five_s(case.tables["cinco_s"])["porcentaje"] == 100


def test_storage_picking_docks_boundaries():
    case = make_example_case()
    geo = pallet_geometry(case.params)
    assert geo["cabe_geometria"] is True and geo["cajas_tarima"] == 45
    case.params["cajas_capa"] = 10
    assert pallet_geometry(case.params)["cabe_geometria"] is False
    assert occupancy(10, 8) == 80
    with pytest.raises(ValueError, match="exceden"):
        occupancy(10, 11)
    orders = pd.DataFrame({"pedido": ["P1"], "bolsas_250": [25], "bolsas_500": [13], "distancia_m": [10]})
    picked = picking(orders)
    assert picked["cajas_250_calculadas"].iloc[0] == 2
    assert picked["cajas_500_calculadas"].iloc[0] == 2
    assert dock_capacity(2, 28800, 3600, 10)["vehiculos_turno"] == 16


def test_finance_requires_inputs_and_separates_discounting():
    case = make_example_case()
    snap = compute_case(case)
    assert "LCC calculado" not in snap.tables
    assert "payback_b_vs_a_anios" not in snap.metrics
    assert "vpn_b_vs_a_mxn" not in snap.metrics
    row = {"inversion_mxn": 1000, "operacion_anual_mxn": 100, "mantenimiento_anual_mxn": 10, "reinversion_mxn": 0, "residual_mxn": 50, "disposicion_mxn": 0}
    result = life_cycle(row, 8, 0.1)
    assert result["lcc_nominal_mxn"] == 1830
    assert result["lcc_descontado_mxn"] != result["lcc_nominal_mxn"]
    assert payback(1000, 200) == 5
    assert npv(1000, [300] * 5, 0.1) > 0
    with pytest.raises(ValueError):
        payback(1000, 0)
    case.tables["alternativas"].loc[0, ["inversion_mxn", "operacion_anual_mxn", "mantenimiento_anual_mxn", "reinversion_mxn", "residual_mxn", "disposicion_mxn"]] = [1000, 100, 10, 0, 50, 0]
    updated = compute_case(case)
    assert len(updated.tables["Sensibilidad LCC"]) == 11
    assert updated.tables["Sensibilidad LCC"]["lcc_descontado_mxn"].iloc[0] == 1830


def test_multicriteria_and_cpm_cycles():
    factors = pd.DataFrame({"factor": ["Costo", "Higiene"], "peso": [0.6, 0.4], "A": [60, 70], "B": [80, 90], "C": [90, 60]})
    assert multicriteria(factors)["B"] == 84
    factors.loc[0, "peso"] = 0.8
    with pytest.raises(ValueError, match="sumar"):
        multicriteria(factors)
    tasks = pd.DataFrame({"id": ["A", "B", "C"], "actividad": ["a", "b", "c"], "duracion_semanas": [2, 3, 1], "predecesoras": ["", "A", "A"]})
    result = cpm(tasks)
    assert result.loc[result.id == "B", "EF"].iloc[0] == 5
    assert result.loc[result.id == "B", "critica"].iloc[0]
    tasks.loc[0, "predecesoras"] = "B"
    with pytest.raises(ValueError, match="cíclicas"):
        cpm(tasks)


def test_auditoria_only_user_measurements():
    case = make_example_case()
    report = audit_measurements(case.tables["auditoria"])
    assert (report["estado"] == "Sin medición").all()
    case.tables["auditoria"].loc[0, ["numerador", "denominador"]] = [99, 100]
    report = audit_measurements(case.tables["auditoria"])
    assert report.loc[0, "valor_evaluado"] == 99
    assert report.loc[0, "estado"] == "Cumple"


def test_edit_clear_reload_export_no_stale_data():
    original = make_example_case()
    modified = original.copy()
    modified.tables["pq"].loc[0, "kg_lote_equiv"] = 9
    modified.params["lotes_propuestos_dia"] = 9
    changed_snapshot = compute_case(modified)
    changed_book = export_xlsx(modified, changed_snapshot)
    empty = make_empty_case()
    assert all(frame.empty for frame in empty.tables.values())
    assert all(value is None for value in empty.params.values())
    empty_snap = compute_case(empty)
    assert not empty_snap.metrics and not empty_snap.tables
    empty_book = export_xlsx(empty, empty_snap)
    assert empty_book != changed_book
    excel = pd.ExcelFile(BytesIO(empty_book))
    assert len(excel.sheet_names) >= 40
    assert pd.read_excel(BytesIO(empty_book), sheet_name="07 PQ entradas").empty
    assert pd.read_excel(BytesIO(empty_book), sheet_name="00 Indicadores").empty
    restored = make_example_case()
    assert restored.tables["pq"].equals(original.tables["pq"])
    assert restored.params == original.params
    assert compute_case(restored).metrics["produccion"]["bolsas_250_mes"] == 6448
    assert pd.read_excel(BytesIO(changed_book), sheet_name="00 Indicadores").loc[lambda d: d.indicador == "masa_entrada_kg", "valor"].iloc[0] == 11.75


def test_illustrative_values_can_be_removed():
    case = make_example_case()
    clean = without_illustrative_values(case)
    assert not clean.illustrative
    assert clean.tables["operacion"].empty
    assert clean.tables["elementos"].shape[0] == 42
    assert clean.tables["areas"]["x_m"].isna().all()
    assert clean.params["factor_abc_a"] is None


def test_code128_layout_and_pqrst_export():
    case = make_example_case()
    svg = code128_svg("ASO-PT-016|PYDI-DEMO|APT-A")
    assert b"<svg" in svg and b"ASO-PT-016" in svg
    with pytest.raises(ValueError):
        code128_svg("")
    assert len(layout_chart(case.tables["areas"], case.tables["rutas_propuestas"]).data) > 1
    snap = compute_case(case)
    assert snap.tables["PQRST consolidado"].set_index("elemento").loc["Q", "valor"] == "201.500 lotes/mes"
    workbook = pd.ExcelFile(BytesIO(export_xlsx(case, snap)))
    assert "C PQRST consolidado" in workbook.sheet_names

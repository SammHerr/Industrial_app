"""Concordancia metodológica y aislamiento del reporte V4."""

from io import BytesIO

import pandas as pd
import pytest
from pypdf import PdfReader

from pydi.reporting import build_report_pdf, select_case
from pydi.reporting.report_snapshot import ReportSnapshot
from pydi.reporting.sections import SECTION_SPECS
from pydi.reporting.technical import (
    PROFILES,
    TABLE_PLANS,
    relation_pairs,
    tables_for_section,
)
from pydi.reporting.technical_figures import figures_for_section
from pydi.reporting.validation import BASE_MODE, CUSTOM_MODE, case_fingerprint
from pydi.v2_model import make_empty_case, make_example_case
from pydi.v2_results import compute_case
from scripts.generate_report_v4_qa import make_custom_qa_case


def test_artifact_registry_covers_all_39_sections():
    expected = set(range(1, 40))
    assert {spec.number for spec in SECTION_SPECS} == expected
    assert set(PROFILES) == set(TABLE_PLANS) == expected
    assert all(PROFILES[number].objective and PROFILES[number].method and PROFILES[number].references for number in expected)


def test_immutable_snapshot_materializes_independent_copies():
    case = make_custom_qa_case()
    before = case_fingerprint(case)
    capture = ReportSnapshot.capture(case, CUSTOM_MODE)
    first, first_result = capture.materialize()
    first.tables["ingredientes"].loc[0, "kg_lote"] = 99
    first_result.metrics["masa_entrada_kg"] = 99
    second, second_result = capture.materialize()
    assert second.tables["ingredientes"].loc[0, "kg_lote"] == 4
    assert second_result.metrics["masa_entrada_kg"] != 99
    assert case_fingerprint(case) == before == capture.fingerprint


@pytest.mark.parametrize("mode", ("base", "custom"))
def test_sha_routes_and_distance_intensity_use_engine(mode):
    case = make_example_case() if mode == "base" else make_custom_qa_case()
    snap = compute_case(case)
    for key in ("TW base calculado", "TW propuesto calculado"):
        frame = snap.tables[key]
        assert (frame["tw_kg_m_dia"] - frame["intensidad_kg_dia"] * frame["distancia_m"]).abs().max() < 1e-8
    result = tables_for_section(12, case, snap)
    summary = next(table.frame for table in result if table.title == "Suma de trabajo de transporte")
    assert summary.loc[0, "T.W. total"] == pytest.approx(snap.tables["TW base calculado"]["tw_kg_m_dia"].sum())
    assert summary.loc[1, "T.W. total"] == pytest.approx(snap.tables["TW propuesto calculado"]["tw_kg_m_dia"].sum())
    assert any("Matriz desde-hacia" in name for name, *_ in figures_for_section(12, case, snap))
    assert any("Red topológica" in name for name, *_ in figures_for_section(13, case, snap))


def test_pareto_and_ishikawa_do_not_invent_causes():
    base = make_example_case()
    snap = compute_case(base)
    frame = snap.tables["Pareto calculado"]
    assert frame["min_dia"].is_monotonic_decreasing
    assert frame["acumulado_pct"].is_monotonic_increasing
    assert frame["acumulado_pct"].iloc[-1] == pytest.approx(100)
    assert figures_for_section(17, base, snap) == []
    assert figures_for_section(16, base, snap)[0][1].startswith(b"\x89PNG")
    custom = make_custom_qa_case()
    assert len(figures_for_section(17, custom, compute_case(custom))) == 1


def test_slp_relations_only_use_documented_flow():
    snap = compute_case(make_example_case())
    pairs = relation_pairs(snap)
    assert not pairs.empty
    assert set(pairs["grado"]) <= {"A", "E", "I", "O", "U"}
    assert "X" not in set(pairs["grado"])
    assert pairs.loc[pairs["intensidad_kg_dia"].eq(0), "motivo"].eq("Sin flujo registrado").all()
    assert any("SLP" in title for title, *_ in figures_for_section(33, make_example_case(), snap))


def test_financial_and_schedule_figures_require_complete_inputs():
    base = make_example_case()
    base_snap = compute_case(base)
    assert "LCC calculado" not in base_snap.tables
    assert figures_for_section(35, base, base_snap) == []
    custom = make_custom_qa_case()
    custom_snap = compute_case(custom)
    assert "LCC calculado" in custom_snap.tables
    assert "CPM calculado" in custom_snap.tables
    assert figures_for_section(35, custom, custom_snap)
    assert custom_snap.metrics["payback_b_vs_a_anios"] == pytest.approx(1.5)
    assert "vpn_b_vs_a_mxn" in custom_snap.metrics


@pytest.fixture(scope="module", params=(BASE_MODE, CUSTOM_MODE))
def report_text(request):
    mode = request.param
    case = select_case(mode, make_empty_case() if mode == BASE_MODE else make_custom_qa_case())
    data = build_report_pdf(case, mode)
    reader = PdfReader(BytesIO(data))
    pages = [page.extract_text() for page in reader.pages]
    return mode, pages, "\n".join(pages)


def test_pdf_text_and_sections_are_ordered(report_text):
    mode, pages, text = report_text
    assert len(pages) >= 40
    assert all(len(page.strip()) > 200 for page in pages)
    offsets = [text.index(f"{spec.number}. {spec.title}", text.index("Resumen ejecutivo")) for spec in SECTION_SPECS]
    assert offsets == sorted(offsets)
    assert "Índice de apartados" in text
    assert "ESQUEMA NO A ESCALA" in text
    assert "Matriz triangular de relaciones SLP" in text
    if mode == BASE_MODE:
        assert "8,057" in text
        assert "11.75" in text
        assert "Dosificación sin báscula calibrada" not in text
    else:
        assert "Datos personalizados" in text
        assert "12.05" in text
        assert "7,930" in text
        assert "Dosificación sin báscula calibrada" in text
        assert "Recuperación incremental B frente a A" in text
        assert "8,057" not in text


def test_pdf_transport_totals_match_shared_engine(report_text):
    mode, _, text = report_text
    case = make_example_case() if mode == BASE_MODE else make_custom_qa_case()
    snap = compute_case(case)
    for name in ("TW base calculado", "TW propuesto calculado"):
        total = snap.tables[name]["tw_kg_m_dia"].sum()
        printed = f"{total:,.4f}".rstrip("0").rstrip(".")
        assert printed in text


def test_empty_custom_preserves_missing_values():
    case = select_case(CUSTOM_MODE, make_empty_case())
    snap = compute_case(case)
    assert "equilibrio" not in snap.metrics
    assert pd.isna(case.params["precio_250_mxn"])
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(build_report_pdf(case, CUSTOM_MODE))).pages)
    assert "No calculable con los datos disponibles" in text or "no calculable con los datos disponibles" in text
    assert "8,057" not in text

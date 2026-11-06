"""Pruebas de cobertura y aislamiento del reporte técnico integral."""

import sqlite3
from io import BytesIO

import pytest
from pypdf import PdfReader

from pydi.reporting import ReportInfo, build_report_pdf, case_fingerprint, select_case
from pydi.reporting.sections import SECTION_SPECS
from pydi.reporting.validation import BASE_MODE, CUSTOM_MODE
from pydi.v2_model import make_empty_case, make_example_case
from pydi.v2_results import compute_case


def _pages(pdf: bytes) -> list[str]:
    assert pdf.startswith(b"%PDF-")
    reader = PdfReader(BytesIO(pdf))
    assert not reader.is_encrypted
    pages = [page.extract_text() for page in reader.pages]
    assert pages and all(len(text.strip()) > 20 for text in pages)
    return pages


@pytest.fixture(scope="module")
def base_report() -> tuple[bytes, list[str]]:
    pdf = build_report_pdf(select_case(BASE_MODE, make_empty_case()), BASE_MODE)
    return pdf, _pages(pdf)


def test_base_report_has_ordered_39_sections_and_real_toc(base_report):
    pdf, pages = base_report
    assert len(pages) >= 45
    assert "Modalidad: Datos base del proyecto PYDI" in pages[0]
    full_text = "\n".join(pages[3:])
    positions = [full_text.index(f"{spec.number}. {spec.title}") for spec in SECTION_SPECS]
    assert len(positions) == 39 and positions == sorted(positions)
    assert "Conclusiones" in full_text and "Anexos" in full_text
    assert "11.75" in full_text and "8,057" in full_text
    assert "5. Ishikawa" not in pages[0]
    assert "Descripción del producto" in pages[1]
    assert "5" in pages[1]  # Primera sección comienza en página 5.
    reader = PdfReader(BytesIO(pdf))
    image_pages = [page for page in reader.pages if page.images]
    assert len(image_pages) >= 10
    assert len(pdf) > 100_000


def test_custom_report_recalculates_and_preserves_session_case():
    current = make_example_case()
    current.tables["ingredientes"].loc[0, "kg_lote"] = 4.0
    current.tables["ingredientes"].loc[1, "kg_lote"] = 5.5
    current.tables["costos_fijos"].loc[0, "mxn_mes"] += 1000
    current.tables["rutas_base"].loc[0, "distancia_m"] += 2
    current.params["lotes_propuestos_dia"] = 8.0
    current.params["precio_250_mxn"] = 36.0
    current.params["cvu_250_mxn"] = 12.0
    before = case_fingerprint(current)
    selected = select_case(CUSTOM_MODE, current)
    snapshot = compute_case(selected)
    pdf = build_report_pdf(selected, CUSTOM_MODE, ReportInfo(project="Escenario de prueba"))
    full_text = "\n".join(_pages(pdf))
    assert "Modalidad: Datos personalizados" in full_text
    assert "Escenario de prueba" in full_text
    assert "191,300" in full_text
    assert f"{snapshot.metrics['equilibrio']['bolsas_enteras']:,.0f}" in full_text
    assert "8,057" not in full_text  # El equilibrio del escenario base no persiste.
    assert "1,144" in full_text and "832" in full_text  # P-Q usa la receta y ritmo editados.
    assert "8,876.96" in full_text  # T.W. responde a la distancia y ritmo editados.
    assert case_fingerprint(current) == before
    assert selected is not current
    assert select_case(BASE_MODE, current).params["precio_250_mxn"] == 35.0
    assert case_fingerprint(current) == before


def test_empty_custom_case_reports_missing_data_without_seed_values(monkeypatch):
    case = make_empty_case()
    case.params["precio_250_mxn"] = None
    before = case_fingerprint(case)
    def reject_database_access(*_args, **_kwargs):
        raise AssertionError("El generador no debe abrir SQLite")

    monkeypatch.setattr(sqlite3, "connect", reject_database_access)
    pdf = build_report_pdf(select_case(CUSTOM_MODE, case), CUSTOM_MODE)
    full_text = "\n".join(_pages(pdf))
    assert "Modalidad: Datos personalizados" in full_text
    assert "Pendiente: Parámetro precio_250_mxn" in full_text
    assert "Resultado P-Q calculado: no calculable" in full_text
    assert "190,300" not in full_text
    assert "8,057" not in full_text
    assert case_fingerprint(case) == before


def test_long_table_splits_and_repeats_header(base_report):
    _, pages = base_report
    # El catálogo de elementos ocupa varias páginas y conserva su encabezado.
    locations = [index for index, text in enumerate(pages) if "ASO-MP-001" in text]
    assert locations
    assert any("codigo" in pages[index].lower() for index in locations)
    assert any("ASO-MP-" in text for text in pages)
    assert "Relación numerada de tablas" in "\n".join(pages)

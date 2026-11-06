"""Reporte técnico integral del escenario industrial PYDI."""

from .pdf_builder import ReportInfo, build_report_pdf
from .validation import case_fingerprint, select_case

__all__ = ["ReportInfo", "build_report_pdf", "case_fingerprint", "select_case"]

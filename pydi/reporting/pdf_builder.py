"""Construcción en memoria del reporte técnico de 39 apartados."""

import re
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    Image,
    KeepTogether,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from pydi.calculations.methods import method_assessment
from pydi.calculations.storage_finance import dock_capacity
from pydi.calculations.transport_quality import occupancy
from pydi.reporting.charts import figures_for_section, render_figure_png
from pydi.reporting.report_snapshot import ReportSnapshot
from pydi.reporting.sections import SECTION_SPECS, SectionSpec
from pydi.reporting.technical import PROFILES, required_data, tables_for_section
from pydi.reporting.technical_figures import figures_for_section as technical_figures
from pydi.reporting.validation import BASE_MODE, CUSTOM_MODE
from pydi.v2_barcode import code128_preview_png
from pydi.v2_model import Case
from pydi.v2_reports import FORMULAS, PARAM_ORIGINS
from pydi.v2_results import Snapshot

INK = colors.HexColor("#17324D")
BLUE = colors.HexColor("#176B87")
LIGHT = colors.HexColor("#EFF5F7")
GRAY = colors.HexColor("#536579")
ORANGE = colors.HexColor("#A9611A")


@dataclass(frozen=True)
class ReportInfo:
    project: str = "Polvo de avena con soya"
    responsible: str = ""
    institution: str = ""
    observations: str = ""
    generated_at: datetime | None = None

    def cleaned(self) -> "ReportInfo":
        values = tuple(str(value or "") for value in (self.project, self.responsible, self.institution, self.observations))
        if any(len(value) > limit for value, limit in zip(values, (120, 120, 160, 800))):
            raise ValueError("Los datos de identificación exceden la longitud permitida.")
        return ReportInfo(*(value.strip() for value in values), generated_at=self.generated_at)


def _register_fonts() -> None:
    if "IndustrialSans" in pdfmetrics.getRegisteredFontNames():
        return
    from matplotlib import get_data_path

    directory = Path(get_data_path()) / "fonts" / "ttf"
    pdfmetrics.registerFont(TTFont("IndustrialSans", str(directory / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("IndustrialSans-Bold", str(directory / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("IndustrialSans", normal="IndustrialSans", bold="IndustrialSans-Bold")


def _styles():
    base = getSampleStyleSheet()
    font = "IndustrialSans"
    styles = {
        "cover_kicker": ParagraphStyle("CoverKicker", parent=base["Normal"], fontName="IndustrialSans-Bold", fontSize=11, textColor=BLUE, spaceAfter=16),
        "cover_title": ParagraphStyle("CoverTitle", parent=base["Title"], fontName="IndustrialSans-Bold", fontSize=24, leading=31, textColor=INK, alignment=TA_LEFT, spaceAfter=18),
        "cover_meta": ParagraphStyle("CoverMeta", parent=base["Normal"], fontName=font, fontSize=10, leading=16, textColor=INK, spaceAfter=7),
        "h1": ParagraphStyle("SectionHeading", parent=base["Heading1"], fontName="IndustrialSans-Bold", fontSize=15, leading=20, textColor=INK, spaceBefore=15, spaceAfter=9, keepWithNext=True),
        "h2": ParagraphStyle("Subheading", parent=base["Heading2"], fontName="IndustrialSans-Bold", fontSize=10, leading=14, textColor=BLUE, spaceBefore=10, spaceAfter=5, keepWithNext=True),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName=font, fontSize=8.5, leading=13, textColor=INK, spaceAfter=7),
        "small": ParagraphStyle("Small", parent=base["BodyText"], fontName=font, fontSize=7.3, leading=11, textColor=GRAY, spaceAfter=5),
        "warning": ParagraphStyle("Warning", parent=base["BodyText"], fontName=font, fontSize=8, leading=12, textColor=ORANGE, spaceAfter=6),
        "table_header": ParagraphStyle("TableHeader", parent=base["Normal"], fontName="IndustrialSans-Bold", fontSize=7, leading=9, textColor=colors.white),
        "table_cell": ParagraphStyle("TableCell", parent=base["Normal"], fontName=font, fontSize=6.8, leading=9.2, textColor=INK),
        "caption": ParagraphStyle("Caption", parent=base["Normal"], fontName=font, fontSize=7, leading=10, textColor=GRAY, alignment=TA_CENTER, spaceBefore=4, spaceAfter=10),
        "table_caption": ParagraphStyle("TableCaption", parent=base["Normal"], fontName="IndustrialSans-Bold", fontSize=7.5, leading=10.5, textColor=INK, spaceBefore=8, spaceAfter=4, keepWithNext=True),
    }
    return styles


def _text(value: object) -> str:
    if value is None:
        return "Pendiente"
    try:
        if pd.isna(value):
            return "Pendiente"
    except (TypeError, ValueError):
        pass
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    if isinstance(value, bool):
        return "Sí" if value else "No"
    result = str(value).strip()
    return result if result else "Pendiente"


def _para(value: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(_text(value)).replace("\n", "<br/>"), style)


def _unit(key: str) -> str:
    units = {
        "masa_entrada_kg": "kg/lote", "costo_ingredientes_mxn": "MXN/lote", "costo_total_lote_mxn": "MXN/lote",
        "costo_fijo_mxn_mes": "MXN/mes", "payback_b_vs_a_anios": "años", "vpn_b_vs_a_mxn": "MXN presentes",
        "disponible_s": "s/turno", "lotes_continuos": "lotes/turno", "lotes_completos": "lotes/turno",
        "lotes_mes": "lotes/mes", "bolsas_250_mes": "bolsas/mes", "bolsas_500_mes": "bolsas/mes",
        "kg_empacados_lote": "kg/lote", "bolsas_reales": "bolsas 250 g/mes", "bolsas_enteras": "bolsas 250 g/mes",
        "puntos": "puntos", "porcentaje": "%", "cajas_tarima": "cajas/tarima",
    }
    return units.get(key, "")


def _flat_metrics(spec: SectionSpec, snap: Snapshot) -> pd.DataFrame:
    rows = []
    for key in spec.metrics:
        value = snap.metrics.get(key)
        if isinstance(value, dict):
            rows.extend((f"{key}.{item}", result, _unit(item)) for item, result in value.items() if not isinstance(result, (dict, pd.DataFrame)))
        elif isinstance(value, (int, float, str, bool)):
            rows.append((key, value, _unit(key)))
    return pd.DataFrame(rows, columns=["indicador", "valor [C]", "unidad"])


def _missing(spec: SectionSpec, case: Case, snap: Snapshot) -> list[str]:
    missing = [f"Parámetro {key}" for key in spec.params if case.params.get(key) is None]
    for name in spec.inputs:
        table = case.tables[name]
        if table.empty:
            missing.append(f"Tabla {name}: sin filas capturadas")
            continue
        for column in table.columns:
            if column in ("origen", "origen_posicion"):
                continue
            absent = table[column].isna() | table[column].astype(str).str.strip().eq("")
            if absent.any() and (absent.sum() == len(table) or spec.results and any(result not in snap.tables for result in spec.results)):
                missing.append(f"{name}.{column}: {int(absent.sum())}/{len(table)} sin dato")
    for result in spec.results:
        if result not in snap.tables:
            missing.append(f"Resultado {result}: no calculable")
    return missing


def _alerts(number: int, snap: Snapshot) -> list[str]:
    return [f"{level}: {message}" for level, section, message in snap.alerts
            if re.match(rf"^{number}(?:\b|–|-)", section)]


def _formula_rows(number: int) -> pd.DataFrame:
    mask = FORMULAS["apartado"].astype(str).map(lambda value: number in [int(item) for item in re.findall(r"\d+", value)])
    return FORMULAS.loc[mask].copy()


def _interactive_results(number: int, case: Case) -> dict[str, pd.DataFrame]:
    """Resultados que la interfaz calcula directamente con las funciones compartidas."""
    if number == 21:
        rows = []
        for row in case.tables["dedicado"].itertuples():
            try:
                rows.append((row.ubicacion, occupancy(row.posiciones_totales, row.posiciones_ocupadas)))
            except (TypeError, ValueError):
                continue
        return {"Ocupación dedicada [M/C]": pd.DataFrame(rows, columns=["ubicacion", "ocupacion_pct"])} if rows else {}
    if number == 27:
        rows = []
        for row in case.tables["muelles"].itertuples():
            try:
                result = dock_capacity(row.posiciones, row.tiempo_operativo_s, row.tiempo_vehiculo_s, row.demanda_vehiculos)
                rows.append((row.muelle, result["vehiculos_turno"], result["margen_vehiculos"]))
            except (TypeError, ValueError):
                continue
        return {"Capacidad de muelles [M/C]": pd.DataFrame(rows, columns=["muelle", "vehiculos_turno", "margen_vehiculos"])} if rows else {}
    if number == 32:
        rows = []
        for row in case.tables["metodos"].itertuples():
            rows.append((row.ruta, row.equipo_candidato,
                         method_assessment(row.capacidad_kg, row.higiene_verificada, row.ergonomia_verificada)))
        return {"Evaluación de métodos [M]": pd.DataFrame(rows, columns=["ruta", "equipo", "evaluacion"])} if rows else {}
    return {}


class _ReportDoc(BaseDocTemplate):
    def __init__(self, stream: BytesIO, modality: str):
        super().__init__(stream, pagesize=A4, leftMargin=17 * mm, rightMargin=17 * mm,
                         topMargin=21 * mm, bottomMargin=18 * mm, title="Reporte técnico integral PYDI")
        self.modality = "BASE" if modality == BASE_MODE else "PERSONALIZADO"
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, leftPadding=0,
                      rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="A4", frames=[frame], onPage=self._page))

    def _page(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LIGHT)
        canvas.line(self.leftMargin, A4[1] - 15 * mm, A4[0] - self.rightMargin, A4[1] - 15 * mm)
        canvas.setFont("IndustrialSans", 7)
        canvas.setFillColor(GRAY)
        if doc.page > 1:
            canvas.drawString(self.leftMargin, A4[1] - 13 * mm, f"Industrial App V4 · PYDI SHA / SLP · {self.modality}")
            canvas.drawRightString(A4[0] - self.rightMargin, 11 * mm, f"Página {doc.page}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "SectionHeading" and hasattr(flowable, "bookmarkName"):
            key = flowable.bookmarkName
            self.canv.bookmarkPage(key)
            self.notify("TOCEntry", (0, flowable.getPlainText(), self.page, key))


def _data_table(frame: pd.DataFrame, title: str, doc: _ReportDoc, styles: dict, number: int,
                register: list[str], source: str = "Escenario y motor de Industrial App", note: str = "") -> list:
    if frame.empty:
        return [_para(f"{title}: no calculable con los datos disponibles; capture las entradas indicadas.", styles["warning"])]
    columns = list(frame.columns)
    groups = [columns] if len(columns) <= 4 else [[columns[0], *columns[index:index + 3]]
                                                  for index in range(1, len(columns), 3)]
    output = []
    for index, group in enumerate(groups, 1):
        local_number = sum(item.startswith(f"Tabla {number}.") for item in register) + 1
        label = f"Tabla {number}.{local_number}. {title}"
        if len(groups) > 1:
            label += f" · columnas {index}/{len(groups)} (clave repetida)"
        register.append(label)
        output.append(_para(label, styles["table_caption"]))
        widths = [doc.width / len(group)] * len(group)
        header = [_para(col.replace("_", " "), styles["table_header"]) for col in group]
        rows = [[_para(value, styles["table_cell"]) for value in record]
                for record in frame[group].itertuples(index=False, name=None)]
        table = LongTable([header, *rows], colWidths=widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D7E2E8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        output.extend((table, _para(f"Fuente: {source}." + (f" {note}" if note else ""), styles["small"]), Spacer(1, 6)))
    return output


def _executive(case: Case, snap: Snapshot, styles: dict) -> list:
    rows = []
    cap, prod = snap.metrics.get("capacidad"), snap.metrics.get("produccion")
    rows.append(f"Producción: {prod['lotes_mes']:,.2f} lotes/mes; {prod['bolsas_250_mes']:,.0f} bolsas de 250 g y {prod['bolsas_500_mes']:,.0f} de 500 g." if prod else "Producción: pendiente de tiempos, ritmo y empaques completos.")
    rows.append(f"Capacidad base: {cap['lotes_continuos']:,.3f} lotes/turno continuos; {cap['lotes_completos']:,.0f} lotes completos." if cap else "Capacidad base: pendiente de tiempo disponible y ciclo.")
    fixed, equilibrium = snap.metrics.get("costo_fijo_mxn_mes"), snap.metrics.get("equilibrio")
    rows.append(f"Costo fijo: ${fixed:,.2f} MXN/mes; equilibrio: {equilibrium['bolsas_reales']:,.4f} bolsas de 250 g/mes ({equilibrium['bolsas_enteras']:,.0f} enteras)." if fixed is not None and equilibrium else "Costo y equilibrio: pendientes de costos fijos, precio y costo variable completos.")
    ingredients = snap.tables.get("Ingredientes calculados")
    rows.append("Materiales principales: " + ", ".join(str(value) for value in ingredients["nombre"].head(5)) + "." if ingredients is not None and not ingredients.empty else "Materiales principales: receta no calculable.")
    comparison = snap.tables.get("Comparación transporte")
    if comparison is not None and not comparison.empty:
        work = comparison.loc[comparison["indicador"] == "Trabajo de transporte"].iloc[0]
        rows.append(f"Trabajo de transporte: {work['base']:,.2f} a {work['propuesto']:,.2f} kg·m/día; variación {work['reduccion_pct']:,.2f} %.")
    else:
        rows.append("Transporte y mejora: pendientes de rutas y parámetros completos.")
    lcc = snap.tables.get("LCC calculado")
    rows.append("Economía: " + "; ".join(f"{row.alternativa}: ${row.lcc_nominal_mxn:,.2f} MXN nominal" for row in lcc.itertuples()) if lcc is not None and not lcc.empty else "Economía: LCC, VPN y recuperación sin verificación hasta capturar flujos y cotizaciones.")
    if "Evaluación calculada" in snap.tables and lcc is not None:
        scores = snap.tables["Evaluación calculada"].set_index("alternativa")["puntuacion"]
        costs = lcc.set_index("alternativa")["lcc_nominal_mxn"]
        rows.append(f"Sistema recomendado por puntaje y costo nominal: {scores.idxmax()} [M/C]; verificar restricciones." if scores.idxmax() == costs.idxmin() else "Sistema recomendado: decisión multicriterio pendiente; costo mínimo y mejor puntaje difieren.")
    else:
        rows.append("Sistema recomendado: B es referencia documental [D]; la recomendación calculada está pendiente.")
    output = [_para("Resumen ejecutivo", styles["h1"])]
    output.extend(_para("• " + item, styles["body"]) for item in rows)
    output.append(_para(f"Advertencias del escenario: {len(snap.alerts)}. [D] documental; [S] supuesto; [C] calculado; [M] complemento; [U] edición del usuario.", styles["small"]))
    return output


def _conclusions(snap: Snapshot, styles: dict) -> list:
    lines = []
    if "masa_entrada_kg" in snap.metrics:
        mass = snap.metrics["masa_entrada_kg"]
        lines.append(f"La receta registrada suma {mass:,.2f} kg/lote, según los ingredientes del escenario.")
    if "equilibrio" in snap.metrics:
        lines.append(f"Con los costos y precio capturados, el equilibrio de 250 g es {snap.metrics['equilibrio']['bolsas_enteras']:,.0f} bolsas enteras por mes; no se extrapola a 500 g.")
    comparison = snap.tables.get("Comparación transporte")
    if comparison is not None and not comparison.empty:
        row = comparison.loc[comparison["indicador"] == "Trabajo de transporte"].iloc[0]
        lines.append(f"El escenario de rutas arroja una variación de {row['reduccion_pct']:,.2f} % en T.W. frente a la base, sujeta a validar las intensidades y distancias capturadas.")
    if "LCC calculado" not in snap.tables:
        lines.append("La evaluación económica no permite comprobar las cifras documentales sin inversión y flujos completos.")
    if "Auditoría evaluada" in snap.tables:
        measured = snap.tables["Auditoría evaluada"]["estado"].ne("Sin medición").sum()
        lines.append(f"La auditoría dispone de {measured} indicadores medidos; las metas restantes no deben interpretarse como resultados observados.")
    if not lines:
        lines.append("No hay resultados calculables suficientes para una conclusión cuantitativa; capture las entradas indicadas en cada apartado.")
    return [_para("Conclusiones", styles["h1"]), *(_para("• " + line, styles["body"]) for line in lines)]


def _figure(image_bytes: bytes, title: str, source: str, doc: _ReportDoc, styles: dict,
            number: int, register: list[str]) -> list:
    with PILImage.open(BytesIO(image_bytes)) as bitmap:
        width, height = bitmap.size
    display_width = doc.width
    display_height = min(display_width * height / width, 88 * mm)
    if display_height < display_width * height / width:
        display_width = display_height * width / height
    local = sum(item.startswith(f"Figura {number}.") for item in register) + 1
    label = f"Figura {number}.{local}. {title}"
    register.append(label)
    return [KeepTogether([Image(BytesIO(image_bytes), width=display_width, height=display_height),
                          _para(f"{label}. Fuente: {source}.", styles["caption"])])]


def build_report_pdf(case: Case, modality: str, info: ReportInfo | None = None) -> bytes:
    """Devuelve un PDF completo sin escribir en SQLite ni mutar el escenario recibido."""
    if modality not in (BASE_MODE, CUSTOM_MODE):
        raise ValueError("Modalidad de reporte desconocida.")
    _register_fonts()
    details = (info or ReportInfo()).cleaned()
    capture = ReportSnapshot.capture(case, modality)
    scenario, snap = capture.materialize()
    styles = _styles()
    output = BytesIO()
    doc = _ReportDoc(output, modality)
    story = []
    when = details.generated_at or datetime.now().astimezone()
    story.extend([
        Spacer(1, 57 * mm),
        _para("INDUSTRIAL APP V4 · PYDI SHA / SLP", styles["cover_kicker"]),
        _para("Reporte técnico integral de Planeación y Diseño de Instalaciones", styles["cover_title"]),
        _para(f"Proyecto o producto: {details.project or 'Sin nombre proporcionado'}", styles["cover_meta"]),
        _para("Modalidad: Datos base del proyecto PYDI" if modality == BASE_MODE else "Modalidad: Datos personalizados", styles["cover_meta"]),
        _para(f"Versión del caso: {capture.case_version} · Huella SHA-256: {capture.fingerprint[:16]}…", styles["cover_meta"]),
        _para(f"Generado: {when.strftime('%d/%m/%Y %H:%M %Z')}", styles["cover_meta"]),
    ])
    for label, value in (("Responsable", details.responsible), ("Institución", details.institution), ("Observaciones", details.observations)):
        if value:
            story.append(_para(f"{label}: {value}", styles["cover_meta"]))
    story.extend((Spacer(1, 38 * mm), _para("Fuente del proyecto: Proyecto PYDI (1).docx. Los datos [M] son complementarios o ilustrativos.", styles["small"]), PageBreak()))

    story.append(_para("Índice de apartados", styles["h1"]))
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("TOC", parent=styles["body"], leftIndent=0, firstLineIndent=0, rightIndent=0,
                                      fontName="IndustrialSans", fontSize=8, leading=13, spaceAfter=1)]
    story.extend((toc, PageBreak()))
    story.extend(_executive(scenario, snap, styles))
    story.append(PageBreak())

    table_register, figure_register = [], []
    for spec in SECTION_SPECS:
        story.append(CondPageBreak(150))
        heading = _para(f"{spec.number}. {spec.title}", styles["h1"])
        heading.bookmarkName = f"section-{spec.number}"
        story.append(heading)
        profile = PROFILES[spec.number]
        story.append(_para(f"Objetivo: {profile.objective}", styles["body"]))
        story.append(_para(f"Método: {profile.method} Marco: {profile.references}.", styles["small"]))
        story.append(_para(spec.interpretation, styles["body"]))
        formulas = _formula_rows(spec.number)
        if not formulas.empty:
            story.append(_para("Fórmulas y procedencia", styles["h2"]))
            story.extend(_data_table(formulas, "Fórmulas aplicables", doc, styles, spec.number, table_register))
        if spec.params:
            params = pd.DataFrame([(key, scenario.params.get(key),
                                    "[U] editado; " + PARAM_ORIGINS.get(key, "[M]") if key in scenario.modified_params else PARAM_ORIGINS.get(key, "[M]"))
                                   for key in spec.params], columns=["parámetro", "valor", "procedencia"])
            story.append(_para("Parámetros del escenario", styles["h2"]))
            story.extend(_data_table(params, "Parámetros", doc, styles, spec.number, table_register))
        technical_tables = tables_for_section(spec.number, scenario, snap)
        if technical_tables:
            story.append(_para("Artefactos técnicos del apartado", styles["h2"]))
            for artifact in technical_tables:
                story.extend(_data_table(artifact.frame, artifact.title, doc, styles, spec.number,
                                         table_register, artifact.source, artifact.note))
        metric_frame = _flat_metrics(spec, snap)
        if not metric_frame.empty:
            story.append(_para("Indicadores calculados", styles["h2"]))
            story.extend(_data_table(metric_frame, "Indicadores", doc, styles, spec.number, table_register))
        for name, frame in _interactive_results(spec.number, scenario).items():
            story.append(_para("Resultados derivados", styles["h2"]))
            story.extend(_data_table(frame, name, doc, styles, spec.number, table_register))
        if spec.number == 25:
            identifiers = scenario.tables["identificaciones"]
            if not identifiers.empty and identifiers["codigo"].notna().any():
                sample = identifiers.loc[identifiers["codigo"].notna()].iloc[0]
                value = f"{sample['codigo']}|{sample['lote']}|{sample['ubicacion']}"
                image_bytes = code128_preview_png(value)
                story.extend(_figure(image_bytes, "Código 128 demostrativo del primer identificador [M]",
                                     "Escenario documental; no es inventario V3", doc, styles, spec.number, figure_register))
        for caption, figure in figures_for_section(spec.number, scenario, snap):
            image_bytes = render_figure_png(figure)
            story.extend(_figure(image_bytes, caption, "Motor del escenario [C/M]", doc, styles,
                                 spec.number, figure_register))
        for caption, image_bytes, source in technical_figures(spec.number, scenario, snap):
            story.extend(_figure(image_bytes, caption, source, doc, styles, spec.number, figure_register))
        limitation = required_data(spec.number, scenario, snap)
        if limitation:
            story.append(_para(limitation, styles["warning"]))
        missing = _missing(spec, scenario, snap)
        alerts = _alerts(spec.number, snap)
        if missing or alerts:
            story.append(_para("Estado de datos y advertencias", styles["h2"]))
            for message in missing[:8]:
                story.append(_para("Pendiente: " + message, styles["warning"]))
            if len(missing) > 8:
                story.append(_para(f"Otros {len(missing) - 8} campos incompletos constan en las tablas anteriores.", styles["warning"]))
            story.extend(_para(message, styles["warning"]) for message in alerts)

    story.append(CondPageBreak(200))
    story.extend(_conclusions(snap, styles))
    story.append(CondPageBreak(200))
    story.append(_para("Anexos", styles["h1"]))
    story.append(_para("A. Fórmulas y procedencia", styles["h2"]))
    story.append(_para("Las ecuaciones, unidades y referencias se presentan junto al apartado que las utiliza. Los valores de los anexos no sustituyen el motor de cálculo.", styles["body"]))
    story.append(_para("B. Incidencias de calidad de datos", styles["h2"]))
    story.append(_para(f"El motor emitió {len(snap.alerts)} advertencias, reproducidas junto a los apartados afectados. Las celdas pendientes permanecen visibles en sus tablas.", styles["body"]))
    story.append(_para("C. Procedencia y supuestos", styles["h2"]))
    story.append(_para("Fuente principal: Word canónico Proyecto PYDI (1).docx. [D] declarado; [S] supuesto del documento; [C] calculado con el motor de Industrial App; [M] complemento metodológico o ejemplo ilustrativo; [U] editado por el usuario. Los resultados del Word que carecen de flujos verificables permanecen como referencia.", styles["body"]))
    story.append(_para("D. Glosario y bibliografía metodológica", styles["h2"]))
    story.append(_para("SHA: Systematic Handling Analysis; SLP: Systematic Layout Planning; P-Q-R-S-T: producto, cantidad, ruta, servicios y tiempo; T.W.: trabajo de transporte; LCC: costo del ciclo de vida; VPN: valor presente neto; CPM: método de ruta crítica. Los grados A/E/I/O/U/X expresan cercanía desde absolutamente necesaria hasta indeseable; X solo procede de incompatibilidad documentada.", styles["body"]))
    bibliography = (
        "R1. Muther y Haganas, Systematic Handling Analysis (SHA).",
        "R2. Muther y Hales, Systematic Layout Planning, 4.ª ed.",
        "R3. Muther, Planificación y proyección de la empresa industrial.",
        "R4. Heragu, Facilities Design, 4.ª ed.",
        "R5. Tompkins et al., Facilities Planning, 4.ª ed.",
        "R6. García-Díaz y Smith, Facilities Planning and Design.",
        "R7. Niebel y Freivalds, Ingeniería industrial: métodos, estándares y diseño del trabajo, 12.ª ed.",
        "R8. Sapag Chain y Sapag Chain, Preparación y evaluación de proyectos, 5.ª ed.",
    )
    story.extend(_para(item, styles["small"]) for item in bibliography)
    doc.multiBuild(story)
    return output.getvalue()

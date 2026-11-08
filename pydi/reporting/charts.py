"""Figuras estáticas derivadas de las mismas figuras Plotly de la interfaz."""

import html
import os
import re
import tempfile
from io import BytesIO
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "industrialapp-matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from matplotlib import patches

from pydi.v2_charts import (
    di_chart,
    equilibrium_chart,
    five_s_chart,
    gantt_chart,
    pallet_chart,
    pq_chart,
    production_chart,
    simple_bars,
    tw_chart,
)
from pydi.v2_model import Case
from pydi.v2_results import Snapshot


def figures_for_section(number: int, case: Case, snap: Snapshot) -> list[tuple[str, object]]:
    """Construye las figuras existentes con las entradas y resultados del escenario."""
    t, m, p = snap.tables, snap.metrics, case.params
    figures = []
    if number == 2 and "produccion" in m:
        figures.append(("Producción mensual propuesta", production_chart(m["produccion"], m.get("capacidad"))))
    elif number == 3 and "localizacion" in m:
        values = pd.DataFrame(m["localizacion"].items(), columns=["municipio", "puntuacion"])
        figures.append(("Ponderación de municipios", simple_bars(values, "municipio", "puntuacion", "Ponderación de municipios [C]")))
    elif number == 4 and "equilibrio" in m:
        figures.append(("Punto de equilibrio de 250 g", equilibrium_chart(m["costo_fijo_mxn_mes"], p["cvu_250_mxn"], p["precio_250_mxn"], m["equilibrio"]["bolsas_reales"])))
    elif number == 6 and "siete_r" in m:
        values = pd.DataFrame(m["siete_r"].items(), columns=["estado", "cantidad"])
        figures.append(("Estado de las 7 R", simple_bars(values, "estado", "cantidad", "7 R · estado actual [D/U]")))
    elif number == 7 and "P-Q calculado" in t:
        figures.append(("Análisis producto-cantidad", pq_chart(t["P-Q calculado"])))
    elif number == 11 and m.get("estiba", {}).get("cabe_geometria"):
        figures.append(("Patrón geométrico de estiba", pallet_chart(p, int(m["estiba"]["cajas_capa_max_rejilla"]))))
    elif number == 12 and {"TW base calculado", "TW propuesto calculado"} <= t.keys():
        figures.append(("Trabajo de transporte por ruta", tw_chart(t["TW base calculado"], t["TW propuesto calculado"])))
    elif number == 13 and {"TW base calculado", "TW propuesto calculado"} <= t.keys():
        figures.append(("Distancia-intensidad", di_chart(t["TW base calculado"], t["TW propuesto calculado"])))
    elif number == 18 and "cinco_s" in m and case.tables["cinco_s"]["puntaje"].notna().all():
        figures.append(("Auditoría 5S", five_s_chart(case.tables["cinco_s"])))
    elif number == 34:
        if "LCC calculado" in t:
            figures.append(("Costo nominal de ciclo de vida", simple_bars(t["LCC calculado"], "alternativa", "lcc_nominal_mxn", "Costo de ciclo de vida nominal [M/C]")))
        if "Sensibilidad LCC" in t:
            fig = px.line(t["Sensibilidad LCC"], x="tasa", y="lcc_descontado_mxn", color="alternativa", markers=True, title="Sensibilidad del LCC descontado [M/C]")
            fig.update_xaxes(tickformat=".0%", title="Tasa anual")
            fig.update_yaxes(title="MXN presentes")
            figures.append(("Sensibilidad del LCC descontado", fig))
    elif number == 36 and "Evaluación calculada" in t:
        figures.append(("Evaluación cualitativa", simple_bars(t["Evaluación calculada"], "alternativa", "puntuacion", "Evaluación cualitativa [M/C]")))
    elif number == 38:
        if "CPM calculado" in t:
            figures.append(("Cronograma CPM", gantt_chart(t["CPM calculado"], computed=True)))
    elif number == 39 and "Auditoría evaluada" in t:
        measured = t["Auditoría evaluada"].dropna(subset=["valor_evaluado"])
        if not measured.empty:
            figures.append(("Mediciones de auditoría", simple_bars(measured, "indicador", "valor_evaluado", "Mediciones capturadas [U]")))
    return figures


def _plain(value: object) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "\n", str(value or ""))).replace("\n\n", "\n")


def render_figure_png(figure: object) -> bytes:
    """Dibuja trazos, barras, formas y anotaciones Plotly sin Chrome/Kaleido."""
    fig, ax = plt.subplots(figsize=(8.2, 4.3), dpi=300)
    fig.patch.set_facecolor("white")
    axes = {"y": ax, "y2": None}
    for trace in figure.data:
        kind = getattr(trace, "type", "")
        axis_name = getattr(trace, "yaxis", None) or "y"
        if axis_name == "y2" and axes["y2"] is None:
            axes["y2"] = ax.twinx()
        target = axes[axis_name] or ax
        label = str(getattr(trace, "name", "") or "")
        color = getattr(getattr(trace, "marker", None), "color", None)
        if not isinstance(color, str):
            color = getattr(getattr(trace, "line", None), "color", None)
        if not isinstance(color, str):
            color = None
        raw_x, raw_y = getattr(trace, "x", None), getattr(trace, "y", None)
        xs = list(raw_x) if raw_x is not None else []
        ys = list(raw_y) if raw_y is not None else []
        if kind == "bar":
            if getattr(trace, "orientation", None) == "h":
                target.barh(ys, xs, left=list(trace.base) if trace.base is not None else 0, color=color, alpha=0.82, label=label)
            else:
                target.bar(xs, ys, color=color, alpha=0.82, label=label)
        elif kind == "scatter" and xs and ys:
            mode = getattr(trace, "mode", None) or "lines"
            linestyle = "-" if "lines" in mode else "None"
            marker = "o" if "markers" in mode else None
            target.plot(xs, ys, linestyle=linestyle, marker=marker, markersize=4, linewidth=1.7, color=color, label=label)
            if "text" in mode and getattr(trace, "text", None) is not None:
                for x, y, value in zip(xs, ys, trace.text):
                    if value is not None:
                        target.annotate(str(value), (x, y), xytext=(0, 5), textcoords="offset points", fontsize=6.5, ha="center")
    for shape in figure.layout.shapes or []:
        if shape.type == "rect":
            ax.add_patch(patches.Rectangle((shape.x0, shape.y0), shape.x1 - shape.x0, shape.y1 - shape.y0,
                                            facecolor=shape.fillcolor or "none", edgecolor=shape.line.color or "#176B87", linewidth=0.8))
        elif shape.type == "line":
            ax.plot([shape.x0, shape.x1], [shape.y0, shape.y1], color=shape.line.color or "#D9822B", linestyle="--", linewidth=1)
    for note in figure.layout.annotations or []:
        if note.xref == "paper" or note.yref == "paper":
            continue
        if isinstance(note.x, (int, float)) and isinstance(note.y, (int, float)):
            ax.annotate(_plain(note.text), (note.x, note.y), fontsize=6.5, ha="center", va="center")
    title = _plain(getattr(figure.layout.title, "text", ""))
    if title:
        ax.set_title(title, fontsize=10, fontweight="bold", pad=14)
    for key, label in (("xaxis", "x"), ("yaxis", "y")):
        title_obj = getattr(getattr(figure.layout, key), "title", None)
        value = _plain(getattr(title_obj, "text", ""))
        if value:
            (ax.set_xlabel if label == "x" else ax.set_ylabel)(value, fontsize=8)
    if axes["y2"] is not None:
        title_obj = getattr(figure.layout.yaxis2, "title", None)
        axes["y2"].set_ylabel(_plain(getattr(title_obj, "text", "")), fontsize=8)
    for axis_name, target in (("xaxis", ax.set_xlim), ("yaxis", ax.set_ylim)):
        bounds = getattr(getattr(figure.layout, axis_name), "range", None)
        if bounds is not None and all(isinstance(v, (int, float)) for v in bounds):
            target(bounds)
    if axes["y2"] is not None:
        bounds = getattr(figure.layout.yaxis2, "range", None)
        if bounds is not None:
            axes["y2"].set_ylim(bounds)
    for target in (ax, axes["y2"]):
        if target is not None:
            target.grid(axis="y", alpha=0.18)
            target.tick_params(labelsize=7)
    labels = [line.get_label() for line in ax.get_lines()] + [bar.get_label() for bar in ax.containers]
    if sum(bool(label and not label.startswith("_")) for label in labels) > 1:
        ax.legend(fontsize=7, loc="best", frameon=False)
    fig.autofmt_xdate(rotation=25, ha="right")
    fig.tight_layout(pad=1.4)
    output = BytesIO()
    fig.savefig(output, format="png", dpi=300, facecolor="white")
    plt.close(fig)
    return output.getvalue()

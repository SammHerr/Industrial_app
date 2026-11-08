"""Diagramas originales SHA, SLP y de métodos para el PDF V4.

Se dibujan a 300 ppp desde el escenario calculado. No reproducen páginas de
libros ni suponen coordenadas físicas cuando solo hay posiciones ilustrativas.
"""

import math
from io import BytesIO

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, Rectangle

from pydi.reporting.technical import relation_pairs
from pydi.v2_model import Case
from pydi.v2_results import Snapshot

INK = "#17324d"
BLUE = "#176b87"
GREEN = "#327f70"
ORANGE = "#a9611a"
LIGHT = "#e9f1f4"


def _save(fig) -> bytes:
    output = BytesIO()
    fig.savefig(output, format="png", dpi=300, facecolor="white", bbox_inches="tight", pad_inches=.12)
    plt.close(fig)
    return output.getvalue()


def process_sequence(case: Case) -> bytes | None:
    stages = case.tables["proceso"]
    if stages.empty:
        return None
    fig, ax = plt.subplots(figsize=(7.3, 2.4))
    ax.set_xlim(0, len(stages) + .2)
    ax.set_ylim(0, 1)
    ax.axis("off")
    for i, row in enumerate(stages.itertuples(index=False), 1):
        x = i - .55
        ax.add_patch(Rectangle((x, .39), .9, .35, facecolor=LIGHT, edgecolor=BLUE, linewidth=1.1))
        name = str(row.etapa)
        if len(name) > 17:
            name = name[:16] + "…"
        ax.text(x + .45, .57, name, ha="center", va="center", fontsize=7, color=INK)
        duration = "tiempo pendiente" if pd.isna(row.duracion_s) else f"{float(row.duracion_s):,.0f} s"
        ax.text(x + .45, .32, duration, ha="center", va="top", fontsize=6.5, color=INK)
        if i < len(stages):
            ax.annotate("", xy=(x + 1.04, .56), xytext=(x + .91, .56),
                        arrowprops={"arrowstyle": "->", "color": INK, "lw": 1})
    ax.text(.05, .9, "Secuencia documentada (tipo de actividad por validar)", fontsize=8, color=INK)
    return _save(fig)


def from_to_matrix(snap: Snapshot) -> bytes | None:
    routes = snap.tables.get("TW base calculado")
    if routes is None or routes.empty:
        return None
    table = routes.pivot_table(index="origen_area", columns="destino_area", values="intensidad_kg_dia", aggfunc="sum", fill_value=0)
    if table.empty:
        return None
    fig, ax = plt.subplots(figsize=(7.3, max(2.7, .42 * len(table) + 1.3)))
    values = table.to_numpy(dtype=float)
    ax.imshow(values, cmap="Blues", aspect="auto", vmin=0)
    ax.set_xticks(range(len(table.columns)), [str(value)[:20] for value in table.columns], rotation=35, ha="right", fontsize=6.7)
    ax.set_yticks(range(len(table.index)), [str(value)[:22] for value in table.index], fontsize=6.7)
    ax.set_xlabel("HACIA", fontsize=8)
    ax.set_ylabel("DESDE", fontsize=8)
    for y in range(values.shape[0]):
        for x in range(values.shape[1]):
            if values[y, x] > 0:
                ax.text(x, y, f"{values[y, x]:,.0f}", ha="center", va="center", fontsize=6.5,
                        color="white" if values[y, x] > values.max() * .55 else INK)
    ax.set_title("Matriz desde-hacia · intensidad base (kg/día)", fontsize=9, color=INK)
    fig.tight_layout()
    return _save(fig)


def route_topology(snap: Snapshot) -> bytes | None:
    routes = snap.tables.get("TW propuesto calculado")
    if routes is None or routes.empty:
        return None
    nodes = sorted(set(routes["origen_area"].astype(str)) | set(routes["destino_area"].astype(str)))
    if len(nodes) < 2:
        return None
    angles = np.linspace(0, 2 * math.pi, len(nodes), endpoint=False)
    positions = {name: (math.cos(angle), math.sin(angle)) for name, angle in zip(nodes, angles)}
    fig, ax = plt.subplots(figsize=(7.3, 4.1))
    ax.axis("off")
    maximum = max(float(routes["intensidad_kg_dia"].max()), 1)
    for row in routes.itertuples():
        start, end = positions[str(row.origen_area)], positions[str(row.destino_area)]
        width = .6 + 2.5 * float(row.intensidad_kg_dia) / maximum
        arrow = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=9, linewidth=width,
                                color=BLUE, alpha=.62, shrinkA=23, shrinkB=23,
                                connectionstyle="arc3,rad=.08")
        ax.add_patch(arrow)
    for index, name in enumerate(nodes, 1):
        x, y = positions[name]
        ax.scatter([x], [y], s=520, facecolor=LIGHT, edgecolor=INK, zorder=5)
        ax.text(x, y, str(index), ha="center", va="center", fontsize=8, weight="bold", color=INK, zorder=6)
    legend = "   ".join(f"{i} {name}" for i, name in enumerate(nodes, 1))
    ax.text(.5, -.04, legend, transform=ax.transAxes, ha="center", va="top", fontsize=5.6, wrap=True, color=INK)
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.2)
    ax.set_title("ESQUEMA NO A ESCALA · flechas = dirección; grosor = kg/día", fontsize=9, color=INK)
    fig.tight_layout()
    return _save(fig)


def pareto(snap: Snapshot) -> bytes | None:
    frame = snap.tables.get("Pareto calculado")
    if frame is None or frame.empty:
        return None
    frame = frame.sort_values("min_dia", ascending=False, kind="stable")
    fig, ax = plt.subplots(figsize=(7.3, 3.3))
    xs = np.arange(len(frame))
    values = frame["min_dia"].to_numpy(dtype=float)
    ax.bar(xs, values, color=BLUE, edgecolor=INK, width=.68, label="min/día")
    ax.set_ylabel("Tiempo perdido (min/día)", fontsize=8)
    ax.set_xticks(xs, [str(value) if pd.notna(value) and str(value).strip() else f"C{i+1}"
                         for i, value in enumerate(frame["rutas"])], fontsize=7)
    ax.grid(axis="y", alpha=.2)
    total = values.sum()
    if total > 0:
        cumulative = np.cumsum(values) / total * 100
        right = ax.twinx()
        right.plot(xs, cumulative, "o-", color=ORANGE, linewidth=1.8, label="Acumulado")
        right.axhline(80, color=INK, linestyle="--", linewidth=1, label="Umbral 80 %")
        right.set_ylim(0, 105)
        right.set_ylabel("Acumulado (%)", fontsize=8)
        right.tick_params(labelsize=7)
        right.legend(loc="lower right", fontsize=6.5, frameon=False)
    ax.tick_params(labelsize=7)
    ax.set_title("Pareto de causas registradas · orden descendente", fontsize=9, color=INK)
    fig.tight_layout()
    return _save(fig)


def fishbone(case: Case) -> bytes | None:
    causes = case.tables["ishikawa"]
    causes = causes.loc[causes["causa"].fillna("").astype(str).str.strip().ne("")]
    if causes.empty:
        return None
    groups = list(causes.groupby("categoria", sort=False))
    fig, ax = plt.subplots(figsize=(7.3, 3.2))
    ax.axis("off")
    ax.plot([.08, .87], [.5, .5], color=INK, linewidth=2)
    ax.annotate("Efecto\nregistrado", xy=(.88, .5), xytext=(.98, .5), ha="center", va="center",
                fontsize=7, arrowprops={"arrowstyle": "-|>", "color": INK})
    for i, (category, rows) in enumerate(groups):
        x = .16 + i * (.66 / max(1, len(groups) - 1))
        sign = 1 if i % 2 == 0 else -1
        ax.plot([x, x - .08], [.5, .5 + sign * .22], color=BLUE, linewidth=1.4)
        label = "; ".join(rows["causa"].astype(str))
        ax.text(x - .08, .5 + sign * .25, f"{category}: {label[:80]}", fontsize=6.5,
                ha="center", va="bottom" if sign > 0 else "top", wrap=True, color=INK)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(.05, .95)
    ax.set_title("Ishikawa · hipótesis capturadas, causalidad no verificada", fontsize=9, color=INK)
    return _save(fig)


def slp_matrix(snap: Snapshot) -> bytes | None:
    pairs = relation_pairs(snap)
    if pairs.empty:
        return None
    nodes = list(dict.fromkeys([*pairs["desde"], *pairs["hacia"]]))
    fig, ax = plt.subplots(figsize=(7.3, 4.0))
    ax.set_xlim(0, len(nodes))
    ax.set_ylim(len(nodes), 0)
    ax.set_xticks(np.arange(len(nodes)) + .5, [str(i + 1) for i in range(len(nodes))], fontsize=8)
    ax.set_yticks(np.arange(len(nodes)) + .5, [str(i + 1) for i in range(len(nodes))], fontsize=8)
    ax.xaxis.tick_top()
    by_pair = {(row.desde, row.hacia): row.grado for row in pairs.itertuples()}
    gray = {"A": "#abc7d4", "E": "#c5d9e1", "I": "#dce8ec", "O": "#edf2f3", "U": "#f8fafb"}
    for i, left in enumerate(nodes):
        ax.add_patch(Rectangle((i, i), 1, 1, facecolor=INK, edgecolor=INK, linewidth=.5))
        ax.text(i + .5, i + .5, str(i + 1), ha="center", va="center", fontsize=8, color="white")
        for j, right in enumerate(nodes):
            if j <= i:
                continue
            grade = by_pair.get((left, right), by_pair.get((right, left), "U"))
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=gray[grade], edgecolor=INK, linewidth=.5))
            ax.text(j + .5, i + .5, grade, ha="center", va="center", fontsize=8, color=INK)
    ax.text(.5, -.1, "   ".join(f"{i+1} {name}" for i, name in enumerate(nodes)), transform=ax.transAxes,
            ha="center", va="top", fontsize=5.7, wrap=True)
    ax.text(.5, -.22, "A/E/I/O/U: cercanía sugerida por intensidad; X: incompatibilidad no capturada", transform=ax.transAxes,
            ha="center", va="top", fontsize=6.5)
    ax.set_title("Matriz triangular SLP derivada del flujo propuesto", fontsize=9, color=INK, pad=18)
    ax.axis("off")
    return _save(fig)


def information_flow() -> bytes:
    steps = ["Alta física", "ID único", "QR / Code 128", "SQLite", "Consulta", "Venta / evento"]
    fig, ax = plt.subplots(figsize=(7.3, 2.0))
    ax.set_xlim(0, len(steps))
    ax.set_ylim(0, 1)
    ax.axis("off")
    for i, label in enumerate(steps):
        x = i + .08
        ax.add_patch(Rectangle((x, .38), .8, .32, facecolor=LIGHT, edgecolor=BLUE, linewidth=1))
        ax.text(x + .4, .54, label, ha="center", va="center", fontsize=7, color=INK)
        if i < len(steps) - 1:
            ax.annotate("", xy=(x + .98, .54), xytext=(x + .82, .54), arrowprops={"arrowstyle": "->", "color": INK})
    ax.text(.5, .15, "Flujo lógico del software; no representa traslados físicos ni ventas del escenario.",
            transform=ax.transAxes, ha="center", fontsize=7, color=INK)
    return _save(fig)


def cashflow(case: Case, snap: Snapshot) -> bytes | None:
    if "payback_b_vs_a_anios" not in snap.metrics:
        return None
    data = case.tables["alternativas"].set_index("alternativa")
    if not {"A", "B"} <= set(data.index):
        return None
    investment = float(data.loc["B", "inversion_mxn"]) - float(data.loc["A", "inversion_mxn"])
    annual = float(data.loc["B", "ahorro_neto_anual_mxn"])
    years = int(case.params["horizonte_anios"])
    if years < 1 or years > 50:
        return None
    periods = np.arange(years + 1)
    cumulative = -investment + annual * periods
    fig, ax = plt.subplots(figsize=(7.3, 3.0))
    ax.bar(periods[1:], [annual] * years, color=BLUE, alpha=.6, label="Flujo neto anual")
    ax.plot(periods, cumulative, "o-", color=ORANGE, label="Acumulado")
    ax.axhline(0, color=INK, linewidth=.8)
    ax.set_xlabel("Año", fontsize=8)
    ax.set_ylabel("MXN", fontsize=8)
    ax.set_title("Recuperación incremental B frente a A", fontsize=9, color=INK)
    ax.grid(axis="y", alpha=.2)
    ax.legend(fontsize=7, frameon=False)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    return _save(fig)


def figures_for_section(number: int, case: Case, snap: Snapshot) -> list[tuple[str, bytes, str]]:
    builders = {
        2: ("Secuencia productiva documentada", lambda: process_sequence(case), "Etapas del escenario [D/U]"),
        12: ("Matriz desde-hacia de intensidad", lambda: from_to_matrix(snap), "Rutas calculadas [C]"),
        13: ("Red topológica del flujo propuesto", lambda: route_topology(snap), "Rutas calculadas [C]; sin escala física"),
        16: ("Pareto con umbral de 80 %", lambda: pareto(snap), "Tiempos calculados [C]"),
        17: ("Ishikawa de causas capturadas", lambda: fishbone(case), "Causas del escenario [U]"),
        25: ("Flujo lógico de identificación V3", information_flow, "Arquitectura de Industrial App V3"),
        33: ("Matriz triangular de relaciones SLP", lambda: slp_matrix(snap), "Intensidad de rutas [C/M]"),
        35: ("Flujo neto y acumulado", lambda: cashflow(case, snap), "Parámetros y alternativas del escenario [C]"),
    }
    if number not in builders:
        return []
    title, builder, source = builders[number]
    data = builder()
    return [(title, data, source)] if data else []

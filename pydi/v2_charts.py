"""Gráficas V2; reciben solamente datos del snapshot actual."""

import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BLUE = "#176B87"
GREEN = "#2A9D78"
ORANGE = "#D9822B"


def pq_chart(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=df["material"], y=df["kg_mes_calculado"], marker_color=BLUE, name="kg/mes [C]")
    fig.add_scatter(x=df["material"], y=df["acumulado_pct"], mode="lines+markers", line_color=GREEN, name="Acumulado % [C]", secondary_y=True)
    fig.update_yaxes(title_text="kg/mes", secondary_y=False)
    fig.update_yaxes(title_text="Acumulado %", range=[0, 105], secondary_y=True)
    fig.update_layout(title="P-Q calculado desde lotes y masa por lote", xaxis_tickangle=-30)
    return fig


def production_chart(production: dict, capacity: dict | None) -> go.Figure:
    names = ["250 g", "500 g"]
    values = [production["bolsas_250_mes"], production["bolsas_500_mes"]]
    fig = px.bar(x=names, y=values, text=values, labels={"x": "Presentación", "y": "Bolsas/mes"}, color_discrete_sequence=[BLUE])
    fig.update_layout(title="Producción mensual propuesta [C]")
    if capacity:
        fig.add_annotation(text=f"Capacidad base secuencial: {capacity['lotes_continuos']:.3f} lotes/turno [C]", xref="paper", yref="paper", x=0, y=1.15, showarrow=False)
    return fig


def equilibrium_chart(fixed: float, variable: float, price: float, exact: float) -> go.Figure:
    x_max = max(10000, math.ceil(exact * 1.5 / 1000) * 1000)
    x = [x_max * i / 60 for i in range(61)]
    fig = go.Figure()
    fig.add_scatter(x=x, y=[price * q for q in x], name="Ingresos [C]", line_color=GREEN)
    fig.add_scatter(x=x, y=[fixed + variable * q for q in x], name="Costo total [C]", line_color=ORANGE)
    fig.add_vline(x=exact, line_dash="dash", line_color=BLUE, annotation_text=f"Qe {exact:,.1f}")
    fig.update_layout(title="Punto de equilibrio · solo bolsa 250 g", xaxis_title="Bolsas 250 g/mes", yaxis_title="MXN/mes")
    return fig


def pareto_chart(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=df["causa"], y=df["min_dia"], marker_color=BLUE, name="min/día [D/U]")
    fig.add_scatter(x=df["causa"], y=df["acumulado_pct"], mode="lines+markers", line_color=GREEN, name="Acumulado % [C]", secondary_y=True)
    fig.update_yaxes(title_text="min/día", secondary_y=False)
    fig.update_yaxes(title_text="Acumulado %", range=[0, 105], secondary_y=True)
    fig.update_layout(title="Pareto de tiempos", xaxis_tickangle=-35)
    return fig


def tw_chart(base: pd.DataFrame, proposed: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=base["id"], y=base["tw_kg_m_dia"], name="Base", marker_color=BLUE)
    fig.add_bar(x=proposed["id"], y=proposed["tw_kg_m_dia"], name="Propuesto", marker_color=GREEN)
    fig.update_layout(title="Trabajo de transporte por ruta [C]", xaxis_title="Ruta", yaxis_title="kg·m/día", barmode="group")
    return fig


def di_chart(base: pd.DataFrame, proposed: pd.DataFrame) -> go.Figure:
    combined = pd.concat([base.assign(metodo="Base"), proposed.assign(metodo="Propuesto")], ignore_index=True)
    fig = px.scatter(combined, x="distancia_m", y="intensidad_kg_dia", text="id", color="metodo", hover_data=["origen_area", "destino_area", "viajes_dia"], color_discrete_map={"Base": BLUE, "Propuesto": GREEN})
    fig.update_traces(textposition="top center", marker_size=10)
    fig.add_vline(x=15, line_dash="dash", line_color=ORANGE, annotation_text="15 m [D]")
    fig.add_hline(y=1000, line_dash="dash", line_color=ORANGE, annotation_text="1,000 kg/día [D]")
    fig.update_layout(title="Distancia–intensidad y criterio documental §31", xaxis_title="Distancia (m)", yaxis_title="Intensidad (kg/día)")
    return fig


def layout_chart(areas: pd.DataFrame, routes: pd.DataFrame | None = None) -> go.Figure:
    data = areas.dropna(subset=["x_m", "y_m"])
    fig = px.scatter(data, x="x_m", y="y_m", text="clave", size="superficie_m2", hover_name="area", size_max=35, color_discrete_sequence=[BLUE])
    fig.update_traces(textposition="top center")
    coords = {str(row.clave): (row.x_m, row.y_m) for row in data.itertuples()}
    def zone(label: str) -> str | None:
        label = label.casefold()
        for keyword, code in (
            ("kit diario", "EMP"), ("insumos", "AIE"), ("almacén mp", "AMP"),
            ("almacén pt", "APT"), ("descarga", "REC"), ("recepción", "REC"),
            ("preparación", "PRE"), ("tostado", "TOS"), ("molino", "MOL"),
            ("empaque", "EMP"), ("embarque", "EMB"),
        ):
            if keyword in label:
                return code
        return None
    if routes is not None:
        for row in routes.itertuples():
            origin = zone(str(row.origen_area))
            destination = zone(str(row.destino_area))
            if origin in coords and destination in coords:
                x0, y0 = coords[origin]
                x1, y1 = coords[destination]
                fig.add_scatter(x=[x0, x1], y=[y0, y1], mode="lines", line={"color": GREEN, "width": 1}, name=str(row.id), showlegend=False, hoverinfo="skip")
    fig.update_xaxes(range=[0, 30], title="x conceptual (m)")
    fig.update_yaxes(range=[0, 20], title="y conceptual (m)", scaleanchor="x", scaleratio=1)
    fig.update_layout(title="Plano conceptual 30 × 20 m · posiciones ilustrativas [M]")
    return fig


def pallet_chart(params: dict, max_boxes: int) -> go.Figure:
    pl, pw = params["tarima_largo_cm"], params["tarima_ancho_cm"]
    bl, bw = params["caja_largo_cm"], params["caja_ancho_cm"]
    count = int(params["cajas_capa"])
    nx, ny = math.floor(pl / bl), math.floor(pw / bw)
    if nx * ny < count:
        bl, bw = bw, bl
        nx, ny = math.floor(pl / bl), math.floor(pw / bw)
    fig = go.Figure()
    for i in range(min(count, max_boxes)):
        col, row = i % nx, i // nx
        fig.add_shape(type="rect", x0=col * bl, x1=(col + 1) * bl, y0=row * bw, y1=(row + 1) * bw, line_color="white", fillcolor=BLUE)
        fig.add_annotation(x=(col + 0.5) * bl, y=(row + 0.5) * bw, text=str(i + 1), showarrow=False, font_color="white")
    fig.update_xaxes(range=[0, pl], title="Tarima, cm")
    fig.update_yaxes(range=[0, pw], scaleanchor="x", scaleratio=1, title="Tarima, cm")
    fig.update_layout(title="Estiba geométrica 2D [C] · no certifica carga ni estabilidad")
    return fig


def ishikawa_chart(df: pd.DataFrame) -> go.Figure:
    categories = ("Método", "Maquinaria/equipo", "Mano de obra", "Materiales", "Medición", "Medio ambiente")
    fig = go.Figure()
    fig.add_scatter(x=[0, 10], y=[0, 0], mode="lines", line={"color": BLUE, "width": 4}, showlegend=False)
    for i, category in enumerate(categories):
        x = 1.3 + i * 1.4
        sign = 1 if i % 2 == 0 else -1
        fig.add_scatter(x=[x, x - 0.8], y=[0, sign * 1.2], mode="lines", line_color=BLUE, showlegend=False)
        subset = df.loc[df["categoria"] == category, "causa"] if not df.empty else pd.Series(dtype=str)
        causes = "; ".join(str(c) for c in subset.dropna() if str(c).strip())
        fig.add_annotation(x=x - 0.8, y=sign * 1.3, text=f"{category}<br>{causes or 'Sin causa evaluada'}", showarrow=False, yanchor="bottom" if sign > 0 else "top")
    fig.add_annotation(x=10, y=0, text="Manejo lento / merma", showarrow=True, ax=75, ay=0)
    fig.update_xaxes(visible=False, range=[-0.3, 11.5])
    fig.update_yaxes(visible=False, range=[-2.5, 2.5])
    fig.update_layout(title="Ishikawa 6M · hipótesis editables, causalidad no probada", showlegend=False)
    return fig


def five_s_chart(df: pd.DataFrame) -> go.Figure:
    grouped = df.groupby("s", as_index=False)["puntaje"].sum()
    fig = px.bar(grouped, x="s", y="puntaje", text_auto=True, color_discrete_sequence=[GREEN])
    fig.update_yaxes(range=[0, 8], title="Puntos de 8")
    fig.update_layout(title="Auditoría 5S [U]")
    return fig


def gantt_chart(df: pd.DataFrame, *, computed: bool = False) -> go.Figure:
    x0 = "ES" if computed else "inicio_referencia"
    x1 = "EF" if computed else "fin_referencia"
    fig = go.Figure()
    for row in df.itertuples():
        start, end = getattr(row, x0), getattr(row, x1)
        if pd.notna(start) and pd.notna(end):
            fig.add_bar(y=[row.actividad], x=[end - start + (0 if computed else 1)], base=[start], orientation="h", name=row.id, showlegend=False, marker_color=ORANGE if computed and row.critica else BLUE)
    fig.update_xaxes(title="Semana", range=[0, max(13, float(df[x1].dropna().max()) + 1) if df[x1].notna().any() else 13])
    fig.update_layout(title="Gantt calculado [M]" if computed else "Ventanas ilustrativas dentro de 12 semanas [M]")
    return fig


def simple_bars(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    fig = px.bar(df, x=x, y=y, text_auto=".2f", color_discrete_sequence=[BLUE])
    fig.update_layout(title=title)
    return fig

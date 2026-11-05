"""Gráficas Plotly construidas únicamente con tablas calculadas actuales."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

AZUL = "#176B87"
VERDE = "#3A9B7A"


def pq_masa(datos: pd.DataFrame) -> go.Figure:
    figura = make_subplots(specs=[[{"secondary_y": True}]])
    figura.add_bar(x=datos["material"], y=datos["kg_mes"], name="Masa (kg/mes)", marker_color=AZUL)
    figura.add_scatter(
        x=datos["material"], y=datos["acumulado_pct"], name="Acumulado (%)",
        mode="lines+markers", line_color=VERDE, secondary_y=True,
    )
    figura.update_yaxes(title_text="kg/mes", secondary_y=False)
    figura.update_yaxes(title_text="Acumulado (%)", range=[0, 105], secondary_y=True)
    figura.update_layout(title="Análisis P-Q por material", xaxis_tickangle=-25, legend_orientation="h")
    return figura


def produccion(datos: pd.DataFrame) -> go.Figure:
    figura = px.bar(datos, x="presentacion", y="bolsas_mes", text_auto=",.0f", color_discrete_sequence=[AZUL])
    figura.update_layout(title="Producción mensual por presentación", xaxis_title="Presentación", yaxis_title="Bolsas/mes")
    return figura


def pareto(datos: pd.DataFrame) -> go.Figure:
    figura = make_subplots(specs=[[{"secondary_y": True}]])
    figura.add_bar(x=datos["causa"], y=datos["min_dia"], name="min/día", marker_color=AZUL)
    figura.add_scatter(
        x=datos["causa"], y=datos["acumulado_pct"], name="Acumulado (%)",
        mode="lines+markers", line_color=VERDE, secondary_y=True,
    )
    figura.update_yaxes(title_text="min/día", secondary_y=False)
    figura.update_yaxes(title_text="Acumulado (%)", range=[0, 105], secondary_y=True)
    figura.update_layout(title="Pareto de tiempos de manejo", xaxis_tickangle=-35, legend_orientation="h")
    return figura


def distancia_intensidad(base: pd.DataFrame, propuesto: pd.DataFrame) -> go.Figure:
    ambos = pd.concat(
        [base.assign(metodo="Base"), propuesto.assign(metodo="Propuesto")], ignore_index=True
    )
    figura = px.scatter(
        ambos, x="distancia_m", y="intensidad_kg_dia", color="metodo", text="id",
        hover_data=["origen", "destino", "viajes_dia", "tw_kg_m_dia"],
        color_discrete_map={"Base": AZUL, "Propuesto": VERDE},
    )
    figura.update_traces(textposition="top center", marker_size=11)
    figura.update_layout(
        title="Distancia e intensidad por ruta", xaxis_title="Distancia (m)",
        yaxis_title="Intensidad (kg/día)", legend_title="Método",
    )
    return figura


def comparacion(datos: pd.DataFrame) -> go.Figure:
    largo = datos.melt(id_vars="indicador", value_vars=["Base", "Propuesto"], var_name="método", value_name="valor")
    figura = px.bar(
        largo, x="indicador", y="valor", color="método", barmode="group", facet_col="indicador",
        facet_col_wrap=3, color_discrete_map={"Base": AZUL, "Propuesto": VERDE},
    )
    figura.update_xaxes(matches=None, showticklabels=False)
    figura.update_yaxes(matches=None)
    figura.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    figura.update_layout(title="Indicadores de manejo: base vs propuesto", legend_title="Método")
    return figura

"""
Componentes gráficos do Dashboard de Vulnerabilidade Educacional.

Este módulo é responsável apenas pela renderização dos gráficos.
A preparação, validação e sumarização dos dados ficam em chart_data.py.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .chart_data import (
    CATEGORY_ORDER,
    build_overview_payload,
    prepare_correlation_data,
    prepare_distribution_data,
    prepare_scatter_data,
)
from .chart_insights import (
    generate_overview_insight,
    render_ai_analysis,
)

CATEGORY_COLORS = {
    "Muito baixa": "#2F75B5",
    "Baixa": "#9ECAE1",
    "Média": "#FED976",
    "Alta": "#FD8D3C",
    "Muito alta": "#BD0026",
    "N/D": "#BDBDBD",
}


def format_decimal_br(
    value: object,
    decimal_places: int = 3,
) -> str:
    """
    Formata números decimais no padrão brasileiro.
    """
    if pd.isna(value):
        return "N/D"

    return (
        f"{float(value):.{decimal_places}f}"
        .replace(".", ",")
    )


def format_integer_br(
    value: object,
) -> str:
    """
    Formata números inteiros no padrão brasileiro.
    """
    if pd.isna(value):
        return "N/D"

    return (
    f"{round(float(value)):,}"
    .replace(",", ".")
    )


def apply_default_layout(
    figure: go.Figure,
    title: str,
    xaxis_title: str,
    yaxis_title: str,
) -> go.Figure:
    """
    Aplica o layout visual padrão aos gráficos.
    """
    figure.update_layout(
        title={
            "text": title,
            "x": 0.02,
            "xanchor": "left",
        },
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        margin={
            "l": 60,
            "r": 30,
            "t": 80,
            "b": 60,
        },
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Arial",
            "color": "#1F2937",
        },
        hoverlabel={
            "font": {
                "family": "Arial",
            }
        },
    )

    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#DCE3EA",
    )

    figure.update_yaxes(
        showgrid=True,
        gridcolor="#DCE3EA",
        zeroline=False,
        linecolor="#DCE3EA",
    )

    return figure


def render_ive_distribution(
    df: pd.DataFrame,
) -> None:
    """
    Renderiza a distribuição dos municípios por categoria do IVE.
    """
    try:
        distribution_df = prepare_distribution_data(
            df
        )

    except ValueError as error:
        st.info(str(error))
        return

    distribution_df = distribution_df.copy()

    distribution_df["_MUNICIPIOS_TOOLTIP"] = (
        distribution_df["Municípios"]
        .apply(format_integer_br)
    )

    distribution_df["_PERCENTUAL_TOOLTIP"] = (
        distribution_df["Percentual"]
        .apply(
            lambda value: (
                f"{float(value):.1f}%"
                .replace(".", ",")
            )
        )
    )

    category_order = (
        distribution_df["Categoria IVE"]
        .tolist()
    )

    figure = px.bar(
        distribution_df,
        x="Categoria IVE",
        y="Municípios",
        color="Categoria IVE",
        category_orders={
            "Categoria IVE": category_order,
        },
        color_discrete_map=CATEGORY_COLORS,
        custom_data=[
            "_MUNICIPIOS_TOOLTIP",
            "_PERCENTUAL_TOOLTIP",
        ],
    )

    figure.update_traces(
        text=None,
        texttemplate=None,
        textposition="none",
        marker_line_width=0,
        hovertemplate=(
            "<b>%{x}</b><br><br>"
            "Municípios: %{customdata[0]}<br>"
            "Percentual: %{customdata[1]}"
            "<extra></extra>"
        ),
    )

    figure = apply_default_layout(
        figure=figure,
        title=(
            "Distribuição dos municípios "
            "por categoria do IVE"
        ),
        xaxis_title="Categoria do IVE",
        yaxis_title="Quantidade de municípios",
    )

    figure.update_layout(
        showlegend=False
    )

    figure.update_xaxes(
        categoryorder="array",
        categoryarray=category_order,
    )

    figure.update_yaxes(
        rangemode="tozero",
        tickformat=",.0f",
    )

    st.plotly_chart(
        figure,
        width="stretch",
        config={
            "displayModeBar": False,
        },
    )


def render_infrastructure_scatter(
    df: pd.DataFrame,
) -> None:
    """
    Renderiza a relação entre infraestrutura escolar e IVE.
    """
    try:
        (
            scatter_df,
            infrastructure_column,
            category_column,
        ) = prepare_scatter_data(df)

    except ValueError as error:
        st.info(str(error))
        return

    scatter_df = scatter_df.copy()

    scatter_df["_IVE_TOOLTIP"] = (
        scatter_df["IVE"]
        .apply(format_decimal_br)
    )

    scatter_df["_CATEGORIA_TOOLTIP"] = (
        scatter_df[category_column]
        .fillna("N/D")
        .astype(str)
    )

    scatter_df["_INFRA_TOOLTIP"] = (
        scatter_df[infrastructure_column]
        .apply(format_decimal_br)
    )

    scatter_df["_MATRICULAS_TOOLTIP"] = (
        scatter_df["NUM_MATRICULAS"]
        .apply(format_integer_br)
    )

    figure = px.scatter(
        scatter_df,
        x=infrastructure_column,
        y="IVE",
        color=category_column,
        category_orders={
            category_column: (
                CATEGORY_ORDER + ["N/D"]
            )
        },
        color_discrete_map=CATEGORY_COLORS,
        hover_name="NO_MUNICIPIO",
        custom_data=[
            "_IVE_TOOLTIP",
            "_CATEGORIA_TOOLTIP",
            "_INFRA_TOOLTIP",
            "_MATRICULAS_TOOLTIP",
        ],
    )

    figure.update_traces(
        marker={
            "size": 9,
            "opacity": 0.75,
            "line": {
                "width": 0.5,
                "color": "#FFFFFF",
            },
        },
        selector={
            "mode": "markers",
        },
    )

    figure.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br><br>"
            "IVE: %{customdata[0]}<br>"
            "Categoria IVE: %{customdata[1]}<br>"
            "Infra média: %{customdata[2]}<br>"
            "Matrículas: %{customdata[3]}"
            "<extra></extra>"
        ),
        selector={
            "mode": "markers",
        },
    )

    figure = apply_default_layout(
        figure=figure,
        title=(
            "Relação entre infraestrutura escolar e IVE"
        ),
        xaxis_title="Infraestrutura média",
        yaxis_title="IVE",
    )

    x_min = float(
        scatter_df[infrastructure_column].min()
    )
    x_max = float(
        scatter_df[infrastructure_column].max()
    )
    y_min = float(
        scatter_df["IVE"].min()
    )
    y_max = float(
        scatter_df["IVE"].max()
    )

    x_tick_values = [
        x_min
        + (x_max - x_min) * index / 5
        for index in range(6)
    ]

    y_tick_values = [
        y_min
        + (y_max - y_min) * index / 5
        for index in range(6)
    ]

    figure.update_xaxes(
        tickmode="array",
        tickvals=x_tick_values,
        ticktext=[
            format_decimal_br(
                value,
                decimal_places=2,
            )
            for value in x_tick_values
        ],
    )

    figure.update_yaxes(
        tickmode="array",
        tickvals=y_tick_values,
        ticktext=[
            format_decimal_br(
                value,
                decimal_places=2,
            )
            for value in y_tick_values
        ],
    )

    figure.update_layout(
        legend_title_text="Categoria IVE"
    )

    st.plotly_chart(
        figure,
        width="stretch",
        config={
            "displayModeBar": False,
        },
    )


def render_correlation_heatmap(
    df: pd.DataFrame,
) -> None:
    """
    Renderiza o heatmap de correlação entre os indicadores educacionais.
    """
    try:
        (
            correlation_matrix,
            display_labels,
        ) = prepare_correlation_data(df)

    except ValueError as error:
        st.info(str(error))
        return

    formatted_values = correlation_matrix.map(
        lambda value: format_decimal_br(
            value,
            decimal_places=2,
        )
    )

    figure = go.Figure(
        data=go.Heatmap(
            z=correlation_matrix.to_numpy(),
            x=display_labels,
            y=display_labels,
            zmin=-1,
            zmax=1,
            zmid=0,
            colorscale="RdBu_r",
            colorbar={
                "title": {
                    "text": "Correlação",
                    "side": "right",
                },
                "tickvals": [
                    -1,
                    -0.5,
                    0,
                    0.5,
                    1,
                ],
                "ticktext": [
                    "-1,00",
                    "-0,50",
                    "0,00",
                    "0,50",
                    "1,00",
                ],
                "thickness": 16,
            },
            text=formatted_values.to_numpy(),
            texttemplate="%{text}",
            textfont={
                "size": 12,
            },
            customdata=formatted_values.to_numpy(),
            hovertemplate=(
                "<b>%{y} × %{x}</b><br><br>"
                "Correlação de Pearson: %{customdata}"
                "<extra></extra>"
            ),
            xgap=1,
            ygap=1,
        )
    )

    figure.update_layout(
        title={
            "text": (
                "Correlação entre os indicadores educacionais"
            ),
            "x": 0.02,
            "xanchor": "left",
        },
        margin={
            "l": 140,
            "r": 40,
            "t": 80,
            "b": 120,
        },
        height=620,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Arial",
            "color": "#1F2937",
        },
        hoverlabel={
            "font": {
                "family": "Arial",
            }
        },
    )

    figure.update_xaxes(
        title=None,
        side="bottom",
        tickangle=-35,
        showgrid=False,
        zeroline=False,
    )

    figure.update_yaxes(
        title=None,
        autorange="reversed",
        showgrid=False,
        zeroline=False,
    )

    st.plotly_chart(
        figure,
        width="stretch",
        config={
            "displayModeBar": False,
        },
    )


def render_overview_ai(
    df: pd.DataFrame,
) -> None:
    """
    Renderiza a análise integrada da aba Visão Geral.
    """
    try:
        payload = build_overview_payload(df)

    except ValueError as error:
        st.info(
            "A análise integrada não está disponível: "
            f"{error}"
        )
        return

    render_ai_analysis(
        title="Visão Geral",
        payload=payload,
        session_prefix="overview",
        generator_function=lambda summaries: (
            generate_overview_insight(
                summaries[0],
                summaries[1],
                summaries[2],
            )
        ),
    )
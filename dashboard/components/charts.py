"""
Componentes gráficos do Dashboard de Vulnerabilidade Educacional.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


CATEGORY_ORDER = [
    "Muito baixa",
    "Baixa",
    "Média",
    "Alta",
    "Muito alta",
]

CATEGORY_COLORS = {
    "Muito baixa": "#2F75B5",
    "Baixa": "#9ECAE1",
    "Média": "#FED976",
    "Alta": "#FD8D3C",
    "Muito alta": "#BD0026",
    "N/D": "#BDBDBD",
}


def format_decimal_br(value: object, decimal_places: int = 3) -> str:
    """Formata números decimais no padrão brasileiro."""
    if pd.isna(value):
        return "N/D"
    return f"{float(value):.{decimal_places}f}".replace(".", ",")


def format_integer_br(value: object) -> str:
    """Formata números inteiros no padrão brasileiro."""
    if pd.isna(value):
        return "N/D"
    return f"{int(round(float(value))):,}".replace(",", ".")


def identify_category_column(df: pd.DataFrame) -> str | None:
    """Identifica a coluna de categoria do IVE disponível."""
    if "IVE_CATEGORIA" in df.columns:
        return "IVE_CATEGORIA"
    if "IVE_CATEGORIA_RELATIVA" in df.columns:
        return "IVE_CATEGORIA_RELATIVA"
    return None


def identify_region_column(df: pd.DataFrame) -> str | None:
    """Identifica a melhor coluna territorial disponível."""
    for column in ["NM_RGI", "NM_RGINT", "NM_REGIA", "NM_REGIAO", "REGIAO"]:
        if column in df.columns:
            return column
    return None


def identify_infrastructure_column(df: pd.DataFrame) -> str | None:
    """Identifica a coluna de infraestrutura disponível."""
    for column in ["INFRA_MEDIA", "INFRAESTRUTURA_MEDIA", "INDICE_INFRAESTRUTURA"]:
        if column in df.columns:
            return column
    return None


def apply_default_layout(
    figure: go.Figure,
    title: str,
    xaxis_title: str,
    yaxis_title: str,
) -> go.Figure:
    """Aplica o layout visual padrão aos gráficos."""
    figure.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        margin={"l": 60, "r": 30, "t": 80, "b": 60},
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial", "color": "#1F2937"},
        hoverlabel={"font": {"family": "Arial"}},
    )
    figure.update_xaxes(showgrid=False, zeroline=False, linecolor="#DCE3EA")
    figure.update_yaxes(showgrid=True, gridcolor="#DCE3EA", zeroline=False, linecolor="#DCE3EA")
    return figure


def render_ive_distribution(df: pd.DataFrame) -> None:
    """Renderiza a distribuição dos municípios por categoria do IVE."""
    category_column = identify_category_column(df)

    if category_column is None:
        st.info(
            "O gráfico de distribuição não está disponível porque "
            "a base não possui uma coluna de categoria do IVE."
        )
        return

    distribution_df = (
        df[category_column]
        .dropna()
        .astype(str)
        .value_counts()
        .reindex(CATEGORY_ORDER, fill_value=0)
        .rename_axis("Categoria IVE")
        .reset_index(name="Municípios")
    )

    total = int(distribution_df["Municípios"].sum())
    if total == 0:
        st.info("Não existem dados suficientes para o gráfico de distribuição do IVE.")
        return

    distribution_df["Percentual"] = distribution_df["Municípios"] / total * 100
    distribution_df["_MUNICIPIOS_TOOLTIP"] = distribution_df["Municípios"].apply(format_integer_br)
    distribution_df["_PERCENTUAL_TOOLTIP"] = distribution_df["Percentual"].apply(
        lambda value: f"{value:.1f}%".replace(".", ",")
    )
    distribution_df["_ROTULO"] = (
        distribution_df["_MUNICIPIOS_TOOLTIP"]
        + "<br>"
        + distribution_df["_PERCENTUAL_TOOLTIP"]
    )

    figure = px.bar(
        distribution_df,
        x="Categoria IVE",
        y="Municípios",
        color="Categoria IVE",
        category_orders={"Categoria IVE": CATEGORY_ORDER},
        color_discrete_map=CATEGORY_COLORS,
        text="_ROTULO",
        custom_data=["_MUNICIPIOS_TOOLTIP", "_PERCENTUAL_TOOLTIP"],
    )

    figure.update_traces(
        textposition="outside",
        cliponaxis=False,
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
        title="Distribuição dos municípios por categoria do IVE",
        xaxis_title="Categoria do IVE",
        yaxis_title="Quantidade de municípios",
    )
    figure.update_layout(showlegend=False, uniformtext_minsize=10, uniformtext_mode="hide")
    figure.update_xaxes(categoryorder="array", categoryarray=CATEGORY_ORDER)
    figure.update_yaxes(rangemode="tozero", tickformat=",.0f")

    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def render_ive_by_region(df: pd.DataFrame) -> None:
    """Renderiza o IVE médio por região geográfica."""
    region_column = identify_region_column(df)

    if region_column is None:
        st.info(
            "O gráfico regional não está disponível porque "
            "a base não possui uma coluna territorial compatível."
        )
        return

    region_df = df.dropna(subset=[region_column, "IVE"]).copy()
    if region_df.empty:
        st.info("Não existem dados suficientes para a análise regional.")
        return

    region_summary = (
        region_df.groupby(region_column, as_index=False, observed=True)
        .agg(IVE_MEDIO=("IVE", "mean"), MUNICIPIOS=("IVE", "size"))
        .sort_values("IVE_MEDIO", ascending=True)
    )
    region_summary["_IVE_TOOLTIP"] = region_summary["IVE_MEDIO"].apply(format_decimal_br)
    region_summary["_MUNICIPIOS_TOOLTIP"] = region_summary["MUNICIPIOS"].apply(format_integer_br)

    figure = px.bar(
        region_summary,
        x="IVE_MEDIO",
        y=region_column,
        orientation="h",
        custom_data=["_IVE_TOOLTIP", "_MUNICIPIOS_TOOLTIP"],
    )
    figure.update_traces(
        marker_color="#2F75B5",
        marker_line_width=0,
        hovertemplate=(
            "<b>%{y}</b><br><br>"
            "IVE médio: %{customdata[0]}<br>"
            "Municípios: %{customdata[1]}"
            "<extra></extra>"
        ),
    )
    figure = apply_default_layout(
        figure=figure,
        title="IVE médio por região",
        xaxis_title="IVE médio",
        yaxis_title="Região",
    )
    figure.update_xaxes(tickformat=".3f")
    figure.update_layout(showlegend=False)

    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def render_infrastructure_scatter(df: pd.DataFrame) -> None:
    """Renderiza a relação entre infraestrutura escolar e IVE."""
    infrastructure_column = identify_infrastructure_column(df)

    if infrastructure_column is None:
        st.info(
            "O gráfico de infraestrutura não está disponível porque "
            "a base não possui uma coluna compatível."
        )
        return

    required_columns = [infrastructure_column, "IVE", "NO_MUNICIPIO"]
    scatter_df = df.dropna(subset=required_columns).copy()

    if scatter_df.empty:
        st.info("Não existem dados suficientes para o gráfico de infraestrutura.")
        return

    category_column = identify_category_column(scatter_df)
    if category_column is None:
        scatter_df["_CATEGORIA_IVE"] = "N/D"
        category_column = "_CATEGORIA_IVE"

    scatter_df[category_column] = (
        scatter_df[category_column]
        .astype("object")
        .where(scatter_df[category_column].notna(), "N/D")
        .astype(str)
    )

    if "NUM_MATRICULAS" not in scatter_df.columns:
        scatter_df["NUM_MATRICULAS"] = pd.NA

    scatter_df["_IVE_TOOLTIP"] = scatter_df["IVE"].apply(format_decimal_br)
    scatter_df["_CATEGORIA_TOOLTIP"] = scatter_df[category_column].fillna("N/D").astype(str)
    scatter_df["_INFRA_TOOLTIP"] = scatter_df[infrastructure_column].apply(format_decimal_br)
    scatter_df["_MATRICULAS_TOOLTIP"] = scatter_df["NUM_MATRICULAS"].apply(format_integer_br)

    figure = px.scatter(
        scatter_df,
        x=infrastructure_column,
        y="IVE",
        color=category_column,
        category_orders={category_column: CATEGORY_ORDER + ["N/D"]},
        color_discrete_map=CATEGORY_COLORS,
        hover_name="NO_MUNICIPIO",
        custom_data=[
            "_IVE_TOOLTIP",
            "_CATEGORIA_TOOLTIP",
            "_INFRA_TOOLTIP",
            "_MATRICULAS_TOOLTIP",
        ],
        trendline="ols",
    )

    figure.update_traces(
        marker={
            "size": 9,
            "opacity": 0.75,
            "line": {"width": 0.5, "color": "#FFFFFF"},
        },
        selector={"mode": "markers"},
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
        selector={"mode": "markers"},
    )
    figure.update_traces(
        line={"color": "#667085", "width": 2, "dash": "dash"},
        hoverinfo="skip",
        selector={"mode": "lines"},
    )

    figure = apply_default_layout(
        figure=figure,
        title="Relação entre infraestrutura escolar e IVE",
        xaxis_title="Infraestrutura média",
        yaxis_title="IVE",
    )
    figure.update_xaxes(tickformat=".3f")
    figure.update_yaxes(tickformat=".3f")
    figure.update_layout(legend_title_text="Categoria IVE")

    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
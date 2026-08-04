"""
Componentes gráficos do Dashboard de Vulnerabilidade Educacional.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.chart_insights import (
    render_ai_analysis,
    generate_overview_insight,
)


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

    distribution_df = (
        distribution_df.loc[distribution_df["Municípios"] > 0]
        .sort_values("Municípios", ascending=False)
        .reset_index(drop=True)
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

    category_order = distribution_df["Categoria IVE"].tolist()

    figure = px.bar(
        distribution_df,
        x="Categoria IVE",
        y="Municípios",
        color="Categoria IVE",
        category_orders={"Categoria IVE": category_order},
        color_discrete_map=CATEGORY_COLORS,
        custom_data=["_MUNICIPIOS_TOOLTIP", "_PERCENTUAL_TOOLTIP"],
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
        title="Distribuição dos municípios por categoria do IVE",
        xaxis_title="Categoria do IVE",
        yaxis_title="Quantidade de municípios",
    )
    figure.update_layout(showlegend=False)
    figure.update_xaxes(
        categoryorder="array",
        categoryarray=category_order,
    )
    figure.update_yaxes(rangemode="tozero", tickformat=",.0f")

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

    figure = apply_default_layout(
        figure=figure,
        title="Relação entre infraestrutura escolar e IVE",
        xaxis_title="Infraestrutura média",
        yaxis_title="IVE",
    )
    x_min = float(scatter_df[infrastructure_column].min())
    x_max = float(scatter_df[infrastructure_column].max())
    y_min = float(scatter_df["IVE"].min())
    y_max = float(scatter_df["IVE"].max())

    x_tick_values = [
        x_min + (x_max - x_min) * index / 5
        for index in range(6)
    ]
    y_tick_values = [
        y_min + (y_max - y_min) * index / 5
        for index in range(6)
    ]

    figure.update_xaxes(
        tickmode="array",
        tickvals=x_tick_values,
        ticktext=[format_decimal_br(value, decimal_places=2) for value in x_tick_values],
    )
    figure.update_yaxes(
        tickmode="array",
        tickvals=y_tick_values,
        ticktext=[format_decimal_br(value, decimal_places=2) for value in y_tick_values],
    )
    figure.update_layout(legend_title_text="Categoria IVE")

    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})



def render_correlation_heatmap(df: pd.DataFrame) -> None:
    """Renderiza o heatmap de correlação entre os indicadores educacionais."""
    indicator_labels = {
        "IVE": "IVE",
        "INFRA_MEDIA": "Infraestrutura",
        "MEDIA_INSE": "INSE",
        "ABANDONO_EM": "Abandono",
        "REPROVACAO_EM": "Reprovação",
        "DISTORCAO_EM": "Distorção idade-série",
        "MEDIA_MATRICULAS_ESCOLA": "Matrículas por escola",
    }

    available_columns = [
        column
        for column in indicator_labels
        if column in df.columns
    ]

    if len(available_columns) < 2:
        st.info(
            "O heatmap de correlação não está disponível porque "
            "a base possui menos de dois indicadores compatíveis."
        )
        return

    correlation_df = (
        df[available_columns]
        .apply(pd.to_numeric, errors="coerce")
        .dropna(axis=1, how="all")
    )

    valid_columns = [
        column
        for column in correlation_df.columns
        if correlation_df[column].nunique(dropna=True) > 1
    ]
    correlation_df = correlation_df[valid_columns]

    if correlation_df.shape[1] < 2:
        st.info(
            "Não existem indicadores numéricos com variação suficiente "
            "para calcular a matriz de correlação."
        )
        return

    correlation_matrix = correlation_df.corr(
        method="pearson",
        min_periods=3,
    )

    display_labels = [
        indicator_labels[column]
        for column in correlation_matrix.columns
    ]

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
                "tickvals": [-1, -0.5, 0, 0.5, 1],
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
            textfont={"size": 12},
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
            "text": "Correlação entre os indicadores educacionais",
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
        config={"displayModeBar": False},
    )


def render_overview_ai(
    df: pd.DataFrame,
) -> None:
    """
    Renderiza a análise integrada da aba Visão Geral.
    """

    # ============================
    # Distribuição do IVE
    # ============================

    category_column = identify_category_column(df)

    distribution_df = (
        df[category_column]
        .dropna()
        .astype(str)
        .value_counts()
        .rename_axis("Categoria")
        .reset_index(name="Municípios")
    )

    total = distribution_df["Municípios"].sum()

    distribution_df["Percentual"] = (
        distribution_df["Municípios"] / total * 100
    )

    distribution_summary = distribution_df.to_string(
        index=False
    )

    # ============================
    # Scatter
    # ============================

    infrastructure_column = identify_infrastructure_column(df)

    scatter_df = df.dropna(
        subset=[
            infrastructure_column,
            "IVE",
        ]
    )

    scatter_summary = {
        "correlation": round(
            scatter_df[infrastructure_column].corr(
                scatter_df["IVE"]
            ),
            3,
        ),
        "ive_min": round(
            scatter_df["IVE"].min(),
            3,
        ),
        "ive_max": round(
            scatter_df["IVE"].max(),
            3,
        ),
        "infra_min": round(
            scatter_df[infrastructure_column].min(),
            3,
        ),
        "infra_max": round(
            scatter_df[infrastructure_column].max(),
            3,
        ),
        "municipalities": len(scatter_df),
    }

    scatter_summary = "\n".join(
        [
            f"{key}: {value}"
            for key, value in scatter_summary.items()
        ]
    )

    # ============================
    # Correlação
    # ============================

    correlation_columns = [
        "IVE",
        "INFRA_MEDIA",
        "MEDIA_INSE",
        "ABANDONO_EM",
        "REPROVACAO_EM",
        "DISTORCAO_EM",
    ]

    available = [
        column
        for column in correlation_columns
        if column in df.columns
    ]

    correlation_matrix = (
        df[available]
        .corr(numeric_only=True)
    )

    ive_corr = (
        correlation_matrix["IVE"]
        .drop("IVE")
        .sort_values(
            key=lambda x: x.abs(),
            ascending=False,
        )
    )

    correlation_summary = "\n".join(
        [
            f"{index}: {value:.3f}"
            for index, value in ive_corr.items()
        ]
    )

    # ============================
    # IA
    # ============================

    render_ai_analysis(
        title="Visão Geral",
        payload=(
            distribution_summary,
            scatter_summary,
            correlation_summary,
        ),
        session_prefix="overview",
        generator_function=lambda payload: (
            generate_overview_insight(
                payload[0],
                payload[1],
                payload[2],
            )
        ),
    )
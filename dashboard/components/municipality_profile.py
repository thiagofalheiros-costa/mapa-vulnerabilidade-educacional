"""
Componente de diagnóstico municipal do dashboard.
"""

from __future__ import annotations

from typing import Final

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


PRIMARY_COLOR: Final[str] = "#17365D"
SECONDARY_COLOR: Final[str] = "#2F75B5"
STATE_COLOR: Final[str] = "#AAB7C4"

CATEGORY_COLUMNS: Final[tuple[str, ...]] = (
    "IVE_CATEGORIA_RELATIVA",
    "IVE_CATEGORIA",
)

PROFILE_INDICATORS: Final[tuple[dict[str, str], ...]] = (
    {
        "raw": "ABANDONO_EM",
        "component": "ABANDONO_EM_COMPONENTE",
        "label": "Abandono",
        "format": "percent",
        "direction": "higher_worse",
    },
    {
        "raw": "REPROVACAO_EM",
        "component": "REPROVACAO_EM_COMPONENTE",
        "label": "Reprovação",
        "format": "percent",
        "direction": "higher_worse",
    },
    {
        "raw": "DISTORCAO_EM",
        "component": "DISTORCAO_EM_COMPONENTE",
        "label": "Distorção idade-série",
        "format": "percent",
        "direction": "higher_worse",
    },
    {
        "raw": "MEDIA_INSE",
        "component": "MEDIA_INSE_COMPONENTE",
        "label": "Baixo INSE",
        "format": "decimal",
        "direction": "lower_worse",
    },
    {
        "raw": "INFRA_MEDIA",
        "component": "INFRA_MEDIA_COMPONENTE",
        "label": "Baixa infraestrutura",
        "format": "decimal",
        "direction": "lower_worse",
    },
    {
        "raw": "MEDIA_MATRICULAS_ESCOLA",
        "component": "MEDIA_MATRICULAS_ESCOLA_COMPONENTE",
        "label": "Pressão de matrículas",
        "format": "integer",
        "direction": "higher_worse",
    },
)


def format_decimal(value: float, decimal_places: int = 3) -> str:
    """Formata um número decimal no padrão brasileiro."""
    if pd.isna(value):
        return "N/D"

    return f"{float(value):.{decimal_places}f}".replace(".", ",")


def format_integer(value: float) -> str:
    """Formata um número inteiro no padrão brasileiro."""
    if pd.isna(value):
        return "N/D"

    return f"{int(round(float(value))):,}".replace(",", ".")


def format_percent(value: float) -> str:
    """Formata uma taxa percentual."""
    if pd.isna(value):
        return "N/D"

    return f"{float(value):.1f}%".replace(".", ",")


def format_ordinal(value: float) -> str:
    """Formata uma posição ordinal."""
    if pd.isna(value):
        return "N/D"

    return f"{int(value)}º"


def identify_category_column(dataframe: pd.DataFrame) -> str | None:
    """Identifica a coluna de categoria disponível."""
    for column in CATEGORY_COLUMNS:
        if column in dataframe.columns:
            return column

    return None


def render_profile_card(
    label: str,
    value: str,
    detail: str,
) -> None:
    """Renderiza um card compacto do diagnóstico municipal."""
    card_html = (
        '<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-detail">{detail}</div>'
        "</div>"
    )

    st.markdown(card_html, unsafe_allow_html=True)


def select_municipality(filtered_df: pd.DataFrame) -> pd.Series:
    """Exibe o seletor e devolve a linha do município escolhido."""
    municipality_options = (
        filtered_df[["CO_MUNICIPIO", "NO_MUNICIPIO"]]
        .drop_duplicates()
        .sort_values("NO_MUNICIPIO")
        .reset_index(drop=True)
    )

    labels = municipality_options["NO_MUNICIPIO"].tolist()

    selected_name = st.selectbox(
        "Selecione um município para o diagnóstico",
        options=labels,
        key="municipality_profile_selector",
    )

    selected_code = municipality_options.loc[
        municipality_options["NO_MUNICIPIO"].eq(selected_name),
        "CO_MUNICIPIO",
    ].iloc[0]

    return filtered_df.loc[
        filtered_df["CO_MUNICIPIO"].eq(selected_code)
    ].iloc[0]


def build_comparison_table(
    municipality: pd.Series,
    complete_df: pd.DataFrame,
) -> pd.DataFrame:
    """Monta a comparação entre o município e a média estadual."""
    rows: list[dict[str, str]] = []

    base_metrics = [
        ("IVE", "IVE", "decimal"),
        ("Abandono", "ABANDONO_EM", "percent"),
        ("Reprovação", "REPROVACAO_EM", "percent"),
        ("Distorção idade-série", "DISTORCAO_EM", "percent"),
        ("INSE médio", "MEDIA_INSE", "decimal"),
        ("Infraestrutura média", "INFRA_MEDIA", "decimal"),
        (
            "Matrículas por escola",
            "MEDIA_MATRICULAS_ESCOLA",
            "integer",
        ),
    ]

    formatters = {
        "decimal": format_decimal,
        "percent": format_percent,
        "integer": format_integer,
    }

    for label, column, format_type in base_metrics:
        if column not in complete_df.columns:
            continue

        municipality_value = pd.to_numeric(
            pd.Series([municipality.get(column)]),
            errors="coerce",
        ).iloc[0]
        state_value = pd.to_numeric(
            complete_df[column],
            errors="coerce",
        ).mean()

        formatter = formatters[format_type]

        rows.append(
            {
                "Indicador": label,
                "Município": formatter(municipality_value),
                "Média estadual": formatter(state_value),
            }
        )

    return pd.DataFrame(rows)


def get_radar_indicators(
    dataframe: pd.DataFrame,
) -> list[dict[str, str]]:
    """Seleciona dimensões disponíveis para o radar."""
    return [
        indicator
        for indicator in PROFILE_INDICATORS
        if indicator["component"] in dataframe.columns
    ]


def create_radar_chart(
    municipality: pd.Series,
    complete_df: pd.DataFrame,
) -> go.Figure | None:
    """Cria radar das contribuições normalizadas para o IVE."""
    indicators = get_radar_indicators(complete_df)

    if len(indicators) < 3:
        return None

    labels = [indicator["label"] for indicator in indicators]
    municipality_values = [
        float(municipality[indicator["component"]])
        if pd.notna(municipality[indicator["component"]])
        else 0.0
        for indicator in indicators
    ]
    state_values = [
        float(
            pd.to_numeric(
                complete_df[indicator["component"]],
                errors="coerce",
            ).mean()
        )
        for indicator in indicators
    ]

    max_value = max(municipality_values + state_values)
    radial_max = max(max_value * 1.15, 0.01)

    figure = go.Figure()

    figure.add_trace(
        go.Scatterpolar(
            r=municipality_values,
            theta=labels,
            fill="toself",
            name=str(municipality["NO_MUNICIPIO"]),
            line={"color": SECONDARY_COLOR, "width": 3},
            fillcolor="rgba(47, 117, 181, 0.22)",
            hovertemplate=(
                "%{theta}<br>Contribuição: %{r:.3f}"
                "<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Scatterpolar(
            r=state_values,
            theta=labels,
            fill="toself",
            name="Média estadual",
            line={"color": STATE_COLOR, "width": 2, "dash": "dot"},
            fillcolor="rgba(170, 183, 196, 0.12)",
            hovertemplate=(
                "%{theta}<br>Média estadual: %{r:.3f}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title={
            "text": "Contribuição das dimensões para o IVE",
            "x": 0.02,
            "xanchor": "left",
        },
        polar={
            "radialaxis": {
                "visible": True,
                "range": [0, radial_max],
                "tickformat": ".2f",
            },
            "angularaxis": {
                "direction": "clockwise",
            },
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.18,
            "xanchor": "center",
            "x": 0.5,
        },
        margin={"l": 45, "r": 45, "t": 70, "b": 70},
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial", "color": "#1F2937"},
    )

    return figure


def compare_indicator(
    municipality_value: float,
    state_value: float,
    direction: str,
    tolerance: float = 0.03,
) -> str:
    """Classifica a posição do município em relação à média estadual."""
    if pd.isna(municipality_value) or pd.isna(state_value):
        return "indisponível"

    scale = abs(state_value) if state_value != 0 else 1.0
    relative_difference = (municipality_value - state_value) / scale

    if abs(relative_difference) <= tolerance:
        return "similar"

    if direction == "higher_worse":
        return "worse" if municipality_value > state_value else "better"

    return "worse" if municipality_value < state_value else "better"


def generate_interpretation(
    municipality: pd.Series,
    complete_df: pd.DataFrame,
) -> str:
    """Gera uma síntese automática baseada em regras transparentes."""
    municipality_ive = pd.to_numeric(
        pd.Series([municipality.get("IVE")]),
        errors="coerce",
    ).iloc[0]
    state_ive = pd.to_numeric(
        complete_df["IVE"],
        errors="coerce",
    ).mean()

    if municipality_ive > state_ive * 1.03:
        opening = "apresenta IVE superior à média estadual"
    elif municipality_ive < state_ive * 0.97:
        opening = "apresenta IVE inferior à média estadual"
    else:
        opening = "apresenta IVE próximo à média estadual"

    worse_labels: list[str] = []
    better_labels: list[str] = []

    for indicator in PROFILE_INDICATORS:
        column = indicator["raw"]

        if column not in complete_df.columns:
            continue

        municipality_value = pd.to_numeric(
            pd.Series([municipality.get(column)]),
            errors="coerce",
        ).iloc[0]
        state_value = pd.to_numeric(
            complete_df[column],
            errors="coerce",
        ).mean()

        comparison = compare_indicator(
            municipality_value=municipality_value,
            state_value=state_value,
            direction=indicator["direction"],
        )

        if comparison == "worse":
            worse_labels.append(indicator["label"].lower())
        elif comparison == "better":
            better_labels.append(indicator["label"].lower())

    sentences = [
        f"{municipality['NO_MUNICIPIO']} {opening}."
    ]

    if worse_labels:
        highlighted = ", ".join(worse_labels[:3])
        sentences.append(
            "As dimensões que mais exigem atenção, em comparação "
            f"com o padrão estadual, são: {highlighted}."
        )

    if better_labels:
        highlighted = ", ".join(better_labels[:2])
        sentences.append(
            "Como aspectos relativamente favoráveis, destacam-se: "
            f"{highlighted}."
        )

    if not worse_labels and not better_labels:
        sentences.append(
            "Os indicadores disponíveis permanecem próximos das "
            "médias observadas no estado."
        )

    return " ".join(sentences)

def identify_main_dimension(
    municipality: pd.Series,
) -> str:
    """
    Identifica a dimensão com maior contribuição para o IVE.
    """
    available_indicators = [
        indicator
        for indicator in PROFILE_INDICATORS
        if indicator["component"] in municipality.index
        and pd.notna(municipality.get(indicator["component"]))
    ]

    if not available_indicators:
        return "N/D"

    main_indicator = max(
        available_indicators,
        key=lambda indicator: float(
            municipality[indicator["component"]]
        ),
    )

    return main_indicator["label"]

def render_municipality_profile(
    filtered_df: pd.DataFrame,
    complete_df: pd.DataFrame,
) -> None:
    """Renderiza o diagnóstico municipal completo."""
    st.subheader("Diagnóstico municipal")
    st.caption(
        "Selecione um município presente nos filtros atuais para comparar "
        "seus resultados com a média dos 497 municípios do estado."
    )

    municipality = select_municipality(filtered_df)
    category_column = identify_category_column(complete_df)

    category = (
        str(municipality[category_column])
        if category_column is not None
        and pd.notna(municipality[category_column])
        else "N/D"
    )

    card_columns = st.columns(5)

    with card_columns[0]:
        render_profile_card(
            label="Município",
            value=str(municipality["NO_MUNICIPIO"]),
            detail=str(municipality.get("SG_UF", "RS")),
        )

    with card_columns[1]:
        render_profile_card(
            label="IVE",
            value=format_decimal(municipality.get("IVE")),
            detail=(
                "média estadual: "
                f"{format_decimal(complete_df['IVE'].mean())}"
            ),
        )

    with card_columns[2]:
        render_profile_card(
            label="Ranking estadual",
            value=format_ordinal(municipality.get("IVE_RANK")),
            detail=f"entre {format_integer(complete_df['CO_MUNICIPIO'].nunique())}",
        )

    with card_columns[3]:
        render_profile_card(
            label="Categoria",
            value=category,
            detail="classificação do IVE",
        )

    with card_columns[4]:
        render_profile_card(
            label="Dimensão principal",
            value=identify_main_dimension(municipality),
            detail="maior contribuição normalizada para o IVE",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    left_column, right_column = st.columns(
        [1.15, 0.85],
        gap="large",
    )

    with left_column:
        radar_chart = create_radar_chart(
            municipality=municipality,
            complete_df=complete_df,
        )

        if radar_chart is None:
            st.info(
                "O radar exige ao menos três colunas de componentes "
                "normalizados do IVE."
            )
        else:
            st.plotly_chart(
                radar_chart,
                width="stretch",
                key="municipality_profile_radar",
            )

    with right_column:
        st.markdown("#### Município × média estadual")

        comparison_table = build_comparison_table(
            municipality=municipality,
            complete_df=complete_df,
        )

        st.dataframe(
            comparison_table,
            width="stretch",
            hide_index=True,
            column_config={
                "Indicador": st.column_config.TextColumn("Indicador"),
                "Município": st.column_config.TextColumn("Município"),
                "Média estadual": st.column_config.TextColumn(
                    "Média estadual"
                ),
            },
        )

        st.markdown("#### Principais percepções")
        st.info(
            generate_interpretation(
                municipality=municipality,
                complete_df=complete_df,
            )
        )
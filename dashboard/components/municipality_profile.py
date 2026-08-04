"""
Componente de diagnóstico municipal do dashboard.
"""

from __future__ import annotations

import logging
from html import escape
from typing import Final

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components.municipality_insights import (
    generate_municipality_insight,
)

PRIMARY_COLOR: Final[str] = "#17365D"
SECONDARY_COLOR: Final[str] = "#2F75B5"
STATE_COLOR: Final[str] = "#AAB7C4"

logger = logging.getLogger(__name__)

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

    return f"{round(float(value)):,}".replace(",", ".")


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

INDICATOR_TOOLTIPS: Final[dict[str, str]] = {
    "INSE médio": (
        "Indicador de Nível Socioeconômico médio dos estudantes. "
        "Valores mais elevados representam, em geral, contextos "
        "socioeconômicos mais favoráveis."
    ),
    "Infraestrutura média": (
        "Média municipal dos indicadores de infraestrutura das escolas, "
        "considerando recursos como biblioteca, laboratório de informática, "
        "quadra, internet e banda larga. Valores maiores indicam melhor "
        "disponibilidade média de infraestrutura."
    ),
}


def render_comparison_table(comparison_table: pd.DataFrame) -> None:
    """Renderiza a comparação municipal com tooltips por indicador."""
    rows_html: list[str] = []

    for _, row in comparison_table.iterrows():
        indicator = str(row["Indicador"])
        municipality_value = str(row["Município"])
        state_value = str(row["Média estadual"])

        tooltip = INDICATOR_TOOLTIPS.get(indicator)

        if tooltip:
            indicator_html = (
                f'<span class="indicator-tooltip" title="{escape(tooltip)}">'
                f"{escape(indicator)} ⓘ"
                "</span>"
            )
        else:
            indicator_html = escape(indicator)

        rows_html.append(
            "<tr>"
            f"<td>{indicator_html}</td>"
            f"<td>{escape(municipality_value)}</td>"
            f"<td>{escape(state_value)}</td>"
            "</tr>"
        )

    table_html = (
        """
        <style>
            .comparison-table {
                width: 100%;
                border-collapse: collapse;
                background-color: #FFFFFF;
                border: 1px solid #DCE3EA;
                border-radius: 12px;
                overflow: hidden;
                font-family: Arial, sans-serif;
                color: #1F2937;
                font-size: 0.88rem;
            }

            .comparison-table th {
                background-color: #F5F7FA;
                color: #17365D;
                font-weight: 600;
                text-align: center;
                padding: 0.7rem 0.6rem;
                border-bottom: 1px solid #DCE3EA;
            }

            .comparison-table td {
                padding: 0.65rem 0.6rem;
                border-bottom: 1px solid #E8EDF2;
                text-align: center;
            }

            .comparison-table td:first-child {
                text-align: left;
                font-weight: 500;
            }

            .comparison-table tr:last-child td {
                border-bottom: none;
            }

            .indicator-tooltip {
                cursor: help;
                text-decoration: none;
            }
        </style>

        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Indicador</th>
                    <th>Município</th>
                    <th>Média estadual</th>
                </tr>
            </thead>
            <tbody>
        """
        + "".join(rows_html)
        + """
            </tbody>
        </table>
        """
    )

    st.markdown(table_html, unsafe_allow_html=True)

def build_municipality_insight_payload(
    municipality: pd.Series,
    category_column: str | None,
) -> dict[str, object]:
    """
    Prepara os indicadores do município para a análise com IA.
    """
    category_value = (
        municipality.get(category_column)
        if category_column is not None
        else "Não disponível"
    )

    return {
        "NO_MUNICIPIO": municipality.get("NO_MUNICIPIO"),
        "IVE": municipality.get("IVE"),
        "IVE_CATEGORIA": category_value,
        "RANK_VULNERABILIDADE": municipality.get("IVE_RANK"),
        "INFRA_MEDIA": municipality.get("INFRA_MEDIA"),
        "MEDIA_INSE": municipality.get("MEDIA_INSE"),
        "ABANDONO_EM": municipality.get("ABANDONO_EM"),
        "REPROVACAO_EM": municipality.get("REPROVACAO_EM"),
        "APROVACAO_EM": municipality.get("APROVACAO_EM"),
        "DISTORCAO_EM": municipality.get("DISTORCAO_EM"),
        "NUM_ESCOLAS": municipality.get("NUM_ESCOLAS"),
        "NUM_MATRICULAS": municipality.get("NUM_MATRICULAS"),
    }



def render_ai_insight(
    municipality: pd.Series,
    category_column: str | None,
) -> None:
    """
    Renderiza a análise inteligente do município selecionado.
    """
    municipality_name = str(
        municipality.get(
            "NO_MUNICIPIO",
            "Município não identificado",
        )
    )
    municipality_code = str(
        municipality.get(
            "CO_MUNICIPIO",
            "Código não disponível",
        )
    )

    state_key = "municipality_ai_insight"
    municipality_key = "municipality_ai_code"

    if state_key not in st.session_state:
        st.session_state[state_key] = None

    if municipality_key not in st.session_state:
        st.session_state[municipality_key] = None

    if st.session_state[municipality_key] != municipality_code:
        st.session_state[state_key] = None
        st.session_state[municipality_key] = municipality_code

    st.markdown("#### ✨ Análise Inteligente")

    st.caption(
        "🤖 Conteúdo gerado automaticamente por IA "
        "com base nos indicadores do município selecionado."
    )

    generate_button = st.button(
        "✨ Gerar análise com IA",
        type="primary",
        key=f"generate_ai_insight_{municipality_code}",
        width="stretch",
    )

    if generate_button:
        payload = build_municipality_insight_payload(
            municipality=municipality,
            category_column=category_column,
        )

        logger.info(
            "Iniciando análise municipal com IA. "
            "municipio=%s codigo=%s",
            municipality_name,
            municipality_code,
        )

        try:
            with st.spinner(
                f"Analisando os indicadores de {municipality_name}..."
            ):
                generated_insight = (
                    generate_municipality_insight(payload)
                )

                st.session_state[state_key] = generated_insight

            logger.info(
                "Análise municipal gerada com sucesso. "
                "municipio=%s codigo=%s tamanho_resposta=%s",
                municipality_name,
                municipality_code,
                len(generated_insight),
            )

        except ValueError as error:
            logger.warning(
                "Falha de validação na análise municipal. "
                "municipio=%s codigo=%s erro=%s",
                municipality_name,
                municipality_code,
                error,
            )

            st.error(str(error))

        except TimeoutError:
            logger.warning(
                "Tempo limite excedido na análise municipal. "
                "municipio=%s codigo=%s",
                municipality_name,
                municipality_code,
            )

            st.warning(
                "A geração da análise demorou mais que o esperado. "
                "Tente novamente em alguns instantes."
            )

        except ConnectionError:
            logger.warning(
                "Falha de conexão na análise municipal. "
                "municipio=%s codigo=%s",
                municipality_name,
                municipality_code,
            )

            st.warning(
                "Não foi possível conectar ao serviço de IA. "
                "Verifique sua conexão e tente novamente."
            )

        except Exception:
            logger.exception(
                "Erro inesperado na análise municipal. "
                "municipio=%s codigo=%s",
                municipality_name,
                municipality_code,
            )

            st.warning(
                "Não foi possível gerar a análise automática "
                "neste momento."
            )

    if st.session_state[state_key]:
        with st.expander(
            "📄 Mostrar análise",
            expanded=True,
        ):
            st.markdown(
                st.session_state[state_key]
            )

    else:
        st.info(
            "Clique no botão acima para gerar uma leitura automática "
            "dos indicadores do município selecionado."
        )


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

        render_comparison_table(comparison_table)

        render_ai_insight(
            municipality=municipality,
            category_column=category_column,
        )
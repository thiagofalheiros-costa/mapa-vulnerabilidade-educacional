"""
Página principal do Dashboard de Vulnerabilidade Educacional.
"""
from textwrap import dedent
import pandas as pd
import streamlit as st

from components.charts import (
    render_infrastructure_scatter,
    render_correlation_heatmap,
    render_ive_distribution,
    render_overview_ai,
)

from components.data_loader import load_dashboard_data
from components.filters import apply_dashboard_filters
from components.map import render_ive_map
from components.municipality_profile import render_municipality_profile


st.set_page_config(
    page_title="Mapa da Vulnerabilidade Educacional",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_custom_style() -> None:
    """
    Aplica a identidade visual do dashboard.
    """
    css = dedent(
        """
        <style>
            :root {
                --primary-color: #17365D;
                --secondary-color: #2F75B5;
                --background-color: #F5F7FA;
                --card-background: #FFFFFF;
                --border-color: #DCE3EA;
                --text-color: #1F2937;
                --muted-text: #667085;
            }

            .stApp {
                background-color: var(--background-color);
            }

            [data-testid="stHeader"] {
                background-color: rgba(0, 0, 0, 0);
            }

            [data-testid="stSidebar"] {
                background-color: #FFFFFF;
                border-right: 1px solid var(--border-color);
            }

            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3 {
                color: var(--primary-color);
            }

            h1,
            h2,
            h3 {
                color: var(--primary-color);
            }

            .dashboard-title {
                color: var(--primary-color);
                font-size: 2.75rem;
                font-weight: 700;
                line-height: 1.2;
                margin: 0 0 1rem 0;
            }

            .dashboard-subtitle {
                color: var(--muted-text);
                font-size: 1.05rem;
                line-height: 1.6;
                max-width: 1100px;
                margin-bottom: 1.2rem;
            }

            .metric-card {
                background-color: var(--card-background);
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 1.15rem 1.25rem;
                min-height: 145px;
                box-shadow: 0 3px 12px rgba(23, 54, 93, 0.06);
            }

            .metric-icon {
                font-size: 1.45rem;
                margin-bottom: 0.5rem;
            }

            .metric-label {
                color: var(--muted-text);
                font-size: 0.9rem;
                font-weight: 500;
                margin-bottom: 0.3rem;
            }

            .metric-value {
                color: var(--primary-color);
                font-size: 2rem;
                font-weight: 700;
                line-height: 1.15;
            }

            .metric-detail {
                color: var(--muted-text);
                font-size: 0.8rem;
                margin-top: 0.4rem;
            }

            .filter-summary {
                background-color: #EAF2F8;
                border-left: 4px solid var(--secondary-color);
                border-radius: 6px;
                color: var(--text-color);
                padding: 0.75rem 1rem;
                margin: 0.6rem 0 1.2rem 0;
            }

            div[data-testid="stDataFrame"] {
                background-color: #FFFFFF;
                border: 1px solid var(--border-color);
                border-radius: 12px;
                overflow: hidden;
            }

            div[data-testid="stCustomComponentV1"] {
                background-color: #FFFFFF;
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 0.35rem;
                overflow: hidden;
                box-shadow: 0 3px 12px rgba(23, 54, 93, 0.05);
            }

            div[data-testid="stDataFrame"] [role="columnheader"] {
                justify-content: center !important;
                text-align: center !important;
            }

            div[data-testid="stPlotlyChart"] {
                background-color: #FFFFFF;
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 0.5rem;
                box-shadow: 0 3px 12px rgba(23, 54, 93, 0.05);
            }

            div[data-testid="stDataFrame"]
            [role="columnheader"] > div {
                justify-content: center !important;
                text-align: center !important;
                width: 100% !important;
            }

            div[data-testid="stDataFrame"]
            [role="columnheader"] span {
                display: block !important;
                text-align: center !important;
                width: 100% !important;
            }

            .sidebar-project-title {
                color: var(--primary-color);
                font-size: 1.25rem;
                font-weight: 700;
                line-height: 1.35;
                margin-bottom: 0.35rem;
            }

            .sidebar-project-description {
                color: var(--muted-text);
                font-size: 0.85rem;
                line-height: 1.45;
            }

            .sidebar-footer {
                color: var(--muted-text);
                font-size: 0.78rem;
                line-height: 1.5;
            }

            @media (max-width: 900px) {
                .dashboard-title {
                    font-size: 2rem;
                }

                .metric-card {
                    min-height: 125px;
                }

                .metric-value {
                    font-size: 1.6rem;
                }
            }
        </style>
        """
    )

    st.markdown(
        css,
        unsafe_allow_html=True,
    )


def format_integer(value: int | float) -> str:
    """
    Formata números inteiros com ponto como separador de milhar.
    """
    if pd.isna(value):
        return ""

    return f"{int(value):,}".replace(",", ".")


def format_decimal(
    value: float,
    decimal_places: int = 3,
) -> str:
    """
    Formata números decimais com vírgula como separador.
    """
    if pd.isna(value):
        return ""

    return (
        f"{float(value):.{decimal_places}f}"
        .replace(".", ",")
    )


def format_ordinal(value: int | float) -> str:
    """
    Formata uma posição utilizando o indicador ordinal masculino.
    """
    if pd.isna(value):
        return ""

    return f"{int(value)}º"


def render_sidebar_header() -> None:
    """
    Renderiza o cabeçalho institucional da barra lateral.
    """
    sidebar_html = (
        '<div class="sidebar-project-title">'
        "🗺️ Mapa da Vulnerabilidade Educacional"
        "</div>"
        '<div class="sidebar-project-description">'
        "Painel municipal para exploração do Índice de "
        "Vulnerabilidade Educacional no Rio Grande do Sul."
        "</div>"
    )

    st.sidebar.markdown(
        sidebar_html,
        unsafe_allow_html=True,
    )

    st.sidebar.divider()


def render_sidebar_footer() -> None:
    """
    Renderiza as informações institucionais da barra lateral.
    """
    st.sidebar.divider()

    footer_html = (
        '<div class="sidebar-footer">'
        "<strong>Sobre o projeto</strong><br>"
        "Versão 1.0<br>"
        "Fontes: INEP e IBGE<br>"
        "Unidade de análise: município"
        "</div>"
    )

    st.sidebar.markdown(
        footer_html,
        unsafe_allow_html=True,
    )


def render_dashboard_header() -> None:
    """
    Renderiza o título e a descrição principal do dashboard.
    """
    title_html = (
        '<div class="dashboard-title">'
        "Mapa da Vulnerabilidade Educacional"
        "</div>"
    )

    subtitle_html = (
        '<div class="dashboard-subtitle">'
        "O painel apresenta o <strong>Índice de Vulnerabilidade "
        "Educacional — IVE</strong> dos municípios do Rio Grande do Sul, "
        "combinando indicadores de rendimento, distorção idade-série, "
        "nível socioeconômico e infraestrutura escolar."
        "</div>"
    )

    st.markdown(
        title_html,
        unsafe_allow_html=True,
    )

    st.markdown(
        subtitle_html,
        unsafe_allow_html=True,
    )


def render_metric_card(
    icon: str,
    label: str,
    value: str,
    detail: str,
) -> None:
    """
    Renderiza um card personalizado de indicador.

    Parameters
    ----------
    icon : str
        Emoji exibido no card.
    label : str
        Nome do indicador.
    value : str
        Valor principal.
    detail : str
        Informação complementar.
    """
    card_html = (
        '<div class="metric-card">'
        f'<div class="metric-icon">{icon}</div>'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-detail">{detail}</div>'
        "</div>"
    )

    st.markdown(
        card_html,
        unsafe_allow_html=True,
    )


def render_filter_summary(
    filtered_municipalities: int,
    total_municipalities: int,
) -> None:
    """
    Renderiza o resumo da quantidade de municípios exibidos.
    """
    summary_html = (
        '<div class="filter-summary">'
        "Exibindo "
        f"<strong>{format_integer(filtered_municipalities)}</strong> "
        "de "
        f"<strong>{format_integer(total_municipalities)}</strong> "
        "municípios."
        "</div>"
    )

    st.markdown(
        summary_html,
        unsafe_allow_html=True,
    )


def calculate_filtered_rank(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recalcula a posição dentro do conjunto filtrado.

    O ranking geral original é preservado na coluna IVE_RANK.

    Parameters
    ----------
    df : pd.DataFrame
        Base filtrada.

    Returns
    -------
    pd.DataFrame
        Base com a coluna POSICAO_FILTRO.
    """
    ranked_df = df.copy()

    ranked_df["POSICAO_FILTRO"] = (
        ranked_df["IVE"]
        .rank(
            method="min",
            ascending=False,
        )
        .astype(int)
    )

    return (
        ranked_df
        .sort_values(
            ["POSICAO_FILTRO", "NO_MUNICIPIO"]
        )
        .reset_index(drop=True)
    )


def identify_category_column(
    df: pd.DataFrame,
) -> str | None:
    """
    Identifica a coluna de categoria do IVE disponível na base.
    """
    if "IVE_CATEGORIA" in df.columns:
        return "IVE_CATEGORIA"

    if "IVE_CATEGORIA_RELATIVA" in df.columns:
        return "IVE_CATEGORIA_RELATIVA"

    return None


def build_ranking_table(
    filtered_df: pd.DataFrame,
    category_column: str | None,
) -> pd.DataFrame:
    """
    Prepara e formata a tabela de ranking.
    """
    ranking_columns = [
        "POSICAO_FILTRO",
        "IVE_RANK",
        "NO_MUNICIPIO",
        "SG_UF",
        "IVE",
    ]

    if category_column is not None:
        ranking_columns.append(category_column)

    ranking_columns.extend(
        [
            column
            for column in [
                "NUM_ESCOLAS",
                "NUM_MATRICULAS",
            ]
            if column in filtered_df.columns
        ]
    )

    ranking = (
        filtered_df[ranking_columns]
        .sort_values(
            ["POSICAO_FILTRO", "NO_MUNICIPIO"]
        )
        .head(20)
        .copy()
    )

    ranking["POSICAO_FILTRO"] = (
        ranking["POSICAO_FILTRO"]
        .apply(format_ordinal)
    )

    ranking["IVE_RANK"] = (
        ranking["IVE_RANK"]
        .apply(format_ordinal)
    )

    ranking["IVE"] = (
        ranking["IVE"]
        .apply(format_decimal)
    )

    if "NUM_ESCOLAS" in ranking.columns:
        ranking["NUM_ESCOLAS"] = (
            ranking["NUM_ESCOLAS"]
            .apply(format_integer)
        )

    if "NUM_MATRICULAS" in ranking.columns:
        ranking["NUM_MATRICULAS"] = (
            ranking["NUM_MATRICULAS"]
            .apply(format_integer)
        )

    return ranking


def build_ranking_column_config(
    category_column: str | None,
) -> dict:
    """
    Cria a configuração visual das colunas do ranking.
    """
    column_config = {
        "POSICAO_FILTRO": st.column_config.TextColumn(
            "Posição no filtro",
            help=(
                "Posição considerando apenas os "
                "municípios filtrados."
            ),
        ),
        "IVE_RANK": st.column_config.TextColumn(
            "Ranking geral",
            help=(
                "Posição do município no ranking "
                "completo do estado."
            ),
        ),
        "NO_MUNICIPIO": st.column_config.TextColumn(
            "Município"
        ),
        "SG_UF": st.column_config.TextColumn(
            "UF"
        ),
        "IVE": st.column_config.TextColumn(
            "IVE"
        ),
        "NUM_ESCOLAS": st.column_config.TextColumn(
            "Escolas"
        ),
        "NUM_MATRICULAS": st.column_config.TextColumn(
            "Matrículas"
        ),
    }

    if category_column is not None:
        column_config[category_column] = (
            st.column_config.TextColumn("Categoria")
        )

    return column_config



def main() -> None:
    """
    Executa a página inicial do dashboard.
    """
    apply_custom_style()
    render_sidebar_header()

    try:
        complete_df = load_dashboard_data()
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()

    filtered_df = apply_dashboard_filters(complete_df)

    render_sidebar_footer()
    render_dashboard_header()

    if filtered_df.empty:
        st.warning(
            "Nenhum município corresponde aos filtros selecionados. "
            "Ajuste os filtros na barra lateral."
        )
        st.stop()

    filtered_df = calculate_filtered_rank(filtered_df)

    filtered_municipalities = (
        filtered_df["CO_MUNICIPIO"].nunique()
    )

    total_municipalities = (
        complete_df["CO_MUNICIPIO"].nunique()
    )

    total_schools = (
        filtered_df["NUM_ESCOLAS"].sum()
        if "NUM_ESCOLAS" in filtered_df.columns
        else None
    )

    total_enrollments = (
        filtered_df["NUM_MATRICULAS"].sum()
        if "NUM_MATRICULAS" in filtered_df.columns
        else None
    )

    mean_ive = filtered_df["IVE"].mean()

    most_vulnerable = filtered_df.loc[
        filtered_df["IVE"].idxmax(),
        "NO_MUNICIPIO",
    ]

    render_filter_summary(
        filtered_municipalities=filtered_municipalities,
        total_municipalities=total_municipalities,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            icon="📍",
            label="Municípios analisados",
            value=format_integer(filtered_municipalities),
            detail=(
                f"de {format_integer(total_municipalities)} municípios"
            ),
        )

    with col2:
        render_metric_card(
            icon="🏫",
            label="Escolas",
            value=(
                format_integer(total_schools)
                if total_schools is not None
                else "N/D"
            ),
            detail="escolas nos municípios filtrados",
        )

    with col3:
        render_metric_card(
            icon="🎓",
            label="Matrículas",
            value=(
                format_integer(total_enrollments)
                if total_enrollments is not None
                else "N/D"
            ),
            detail="matrículas da educação básica",
        )

    with col4:
        render_metric_card(
            icon="📊",
            label="IVE médio",
            value=format_decimal(mean_ive),
            detail=f"maior IVE: {most_vulnerable}",
        )

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    render_municipality_profile(
        filtered_df=filtered_df,
        complete_df=complete_df,
    )

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    st.subheader("Distribuição territorial da vulnerabilidade")

    st.caption(
        "Passe o cursor sobre um município para consultar seus "
        "indicadores. O mapa responde automaticamente aos filtros "
        "selecionados na barra lateral."
    )

    render_ive_map(filtered_df)

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    st.subheader("Municípios com maior vulnerabilidade")

    category_column = identify_category_column(filtered_df)

    ranking = build_ranking_table(
        filtered_df=filtered_df,
        category_column=category_column,
    )

    column_config = build_ranking_column_config(
        category_column=category_column,
    )

    st.dataframe(
        ranking,
        width="stretch",
        hide_index=True,
        column_config=column_config,
    )

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    st.subheader("Visão Geral - indicadores")
  
    
   
    chart_col1, chart_col2 = st.columns(
        [1, 1],
        gap="large",
    )

    with chart_col1:
        render_ive_distribution(filtered_df)

    with chart_col2:
        render_correlation_heatmap(filtered_df)

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    render_infrastructure_scatter(filtered_df)

    st.markdown(
    "<br>",
    unsafe_allow_html=True,
)

    render_overview_ai(filtered_df)

if __name__ == "__main__":
    main()
"""
Componentes de filtragem utilizados no dashboard.
"""

from typing import Optional

import pandas as pd
import streamlit as st
import math


REGION_COLUMN_CANDIDATES = [
    "NM_RGINT",
    "NM_RGI",
    "NM_REGIA",
    "REGIAO",
]


def find_region_column(df: pd.DataFrame) -> Optional[str]:
    """
    Identifica a coluna territorial disponível na base.

    Parameters
    ----------
    df : pd.DataFrame
        Base municipal utilizada pelo dashboard.

    Returns
    -------
    Optional[str]
        Nome da coluna territorial encontrada ou None.
    """
    for column in REGION_COLUMN_CANDIDATES:
        if column in df.columns:
            return column

    return None


def identify_category_column(df: pd.DataFrame) -> Optional[str]:
    """
    Identifica a coluna de categoria do IVE disponível na base.

    Parameters
    ----------
    df : pd.DataFrame
        Base municipal utilizada pelo dashboard.

    Returns
    -------
    Optional[str]
        Nome da coluna de categoria encontrada ou None.
    """
    if "IVE_CATEGORIA" in df.columns:
        return "IVE_CATEGORIA"

    if "IVE_CATEGORIA_RELATIVA" in df.columns:
        return "IVE_CATEGORIA_RELATIVA"

    return None


def create_ive_options(
    minimum_value: float,
    maximum_value: float,
) -> list[float]:
    """
    Cria as opções do seletor de faixa do IVE.

    O limite inferior é arredondado para baixo e o limite superior
    é arredondado para cima, garantindo que todos os municípios
    permaneçam incluídos no intervalo padrão.
    """
    
    minimum_integer = math.floor(minimum_value * 1_000)
    maximum_integer = math.ceil(maximum_value * 1_000)

    return [
        value / 1_000
        for value in range(
            minimum_integer,
            maximum_integer + 1,
        )
    ]


def format_ive_filter_value(value: float) -> str:
    """
    Formata o IVE com vírgula como separador decimal.
    """
    return f"{value:.3f}".replace(".", ",")


def apply_dashboard_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renderiza os filtros da barra lateral e retorna a base filtrada.

    Parameters
    ----------
    df : pd.DataFrame
        Base completa do dashboard.

    Returns
    -------
    pd.DataFrame
        Base após a aplicação dos filtros selecionados.
    """
    filtered_df = df.copy()

    st.sidebar.markdown("## Filtros")

    region_column = find_region_column(filtered_df)

    if region_column is not None:
        region_options = sorted(
            filtered_df[region_column]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_regions = st.sidebar.multiselect(
            label="Região",
            options=region_options,
            default=region_options,
            help="Selecione uma ou mais regiões para analisar.",
        )

        if selected_regions:
            filtered_df = filtered_df[
                filtered_df[region_column]
                .astype(str)
                .isin(selected_regions)
            ]
        else:
            filtered_df = filtered_df.iloc[0:0]

    category_column = identify_category_column(filtered_df)

    if category_column is not None:
        category_options = sorted(
            filtered_df[category_column]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_categories = st.sidebar.multiselect(
            label="Categoria do IVE",
            options=category_options,
            default=category_options,
            help=(
                "Filtre os municípios pela categoria "
                "de vulnerabilidade."
            ),
        )

        if selected_categories:
            filtered_df = filtered_df[
                filtered_df[category_column]
                .astype(str)
                .isin(selected_categories)
            ]
        else:
            filtered_df = filtered_df.iloc[0:0]

    municipality_options = sorted(
        filtered_df["NO_MUNICIPIO"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_municipalities = st.sidebar.multiselect(
        label="Município",
        options=municipality_options,
        placeholder="Todos os municípios",
        help=(
            "Deixe o campo vazio para manter todos os municípios "
            "ou selecione municípios específicos."
        ),
    )

    if selected_municipalities:
        filtered_df = filtered_df[
            filtered_df["NO_MUNICIPIO"]
            .astype(str)
            .isin(selected_municipalities)
        ]

    ive_values = df["IVE"].dropna().astype(float)

    if not ive_values.empty:
        ive_minimum = float(ive_values.min())
        ive_maximum = float(ive_values.max())

        ive_options = create_ive_options(
            minimum_value=ive_minimum,
            maximum_value=ive_maximum,
        )

        selected_ive_range = st.sidebar.select_slider(
            label="Faixa do IVE",
            options=ive_options,
            value=(
                ive_options[0],
                ive_options[-1],
            ),
            format_func=format_ive_filter_value,
            help=(
                "Defina o intervalo do Índice de "
                "Vulnerabilidade Educacional."
            ),
        )

        filtered_df = filtered_df[
            filtered_df["IVE"].between(
                selected_ive_range[0],
                selected_ive_range[1],
                inclusive="both",
            )
        ]

    return filtered_df.reset_index(drop=True)
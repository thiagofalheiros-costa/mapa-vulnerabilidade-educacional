"""
Preparação de dados para os gráficos do dashboard.

Este módulo concentra transformações, validações e resumos estatísticos.
A renderização com Plotly permanece em charts.py.
"""

from __future__ import annotations

import pandas as pd

CATEGORY_ORDER = [
    "Muito baixa",
    "Baixa",
    "Média",
    "Alta",
    "Muito alta",
]

INDICATOR_LABELS = {
    "IVE": "IVE",
    "INFRA_MEDIA": "Infraestrutura",
    "MEDIA_INSE": "INSE",
    "ABANDONO_EM": "Abandono",
    "REPROVACAO_EM": "Reprovação",
    "DISTORCAO_EM": "Distorção idade-série",
    "MEDIA_MATRICULAS_ESCOLA": "Matrículas por escola",
}


def identify_category_column(
    dataframe: pd.DataFrame,
) -> str | None:
    """
    Identifica a coluna de categoria do IVE disponível.
    """
    if "IVE_CATEGORIA" in dataframe.columns:
        return "IVE_CATEGORIA"

    if "IVE_CATEGORIA_RELATIVA" in dataframe.columns:
        return "IVE_CATEGORIA_RELATIVA"

    return None


def identify_infrastructure_column(
    dataframe: pd.DataFrame,
) -> str | None:
    """
    Identifica a coluna de infraestrutura disponível.
    """
    candidates = [
        "INFRA_MEDIA",
        "INFRAESTRUTURA_MEDIA",
        "INDICE_INFRAESTRUTURA",
    ]

    for column in candidates:
        if column in dataframe.columns:
            return column

    return None


def prepare_distribution_data(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepara a distribuição dos municípios por categoria do IVE.

    Raises
    ------
    ValueError
        Quando a categoria não existe ou não há dados válidos.
    """
    category_column = identify_category_column(
        dataframe
    )

    if category_column is None:
        raise ValueError(
            "A base não possui uma coluna de categoria do IVE."
        )

    distribution = (
        dataframe[category_column]
        .dropna()
        .astype(str)
        .value_counts()
        .reindex(CATEGORY_ORDER, fill_value=0)
        .rename_axis("Categoria IVE")
        .reset_index(name="Municípios")
    )

    distribution = (
        distribution.loc[
            distribution["Municípios"] > 0
        ]
        .sort_values(
            "Municípios",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    total = int(
        distribution["Municípios"].sum()
    )

    if total == 0:
        raise ValueError(
            "Não existem dados suficientes para a distribuição do IVE."
        )

    distribution["Percentual"] = (
        distribution["Municípios"]
        / total
        * 100
    )

    return distribution


def prepare_scatter_data(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, str, str]:
    """
    Prepara os dados do scatter de infraestrutura e IVE.

    Returns
    -------
    tuple
        DataFrame preparado, coluna de infraestrutura e coluna de categoria.

    Raises
    ------
    ValueError
        Quando faltam colunas ou observações válidas.
    """
    infrastructure_column = (
        identify_infrastructure_column(
            dataframe
        )
    )

    if infrastructure_column is None:
        raise ValueError(
            "A base não possui uma coluna compatível de infraestrutura."
        )

    required_columns = [
        infrastructure_column,
        "IVE",
        "NO_MUNICIPIO",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "A base não possui as colunas obrigatórias: "
            + ", ".join(missing_columns)
        )

    scatter = dataframe.dropna(
        subset=required_columns
    ).copy()

    if scatter.empty:
        raise ValueError(
            "Não existem dados suficientes para o gráfico de infraestrutura."
        )

    category_column = identify_category_column(
        scatter
    )

    if category_column is None:
        category_column = "_CATEGORIA_IVE"
        scatter[category_column] = "N/D"
    else:
        scatter[category_column] = (
            scatter[category_column]
            .astype("object")
            .where(
                scatter[category_column].notna(),
                "N/D",
            )
            .astype(str)
        )

    if "NUM_MATRICULAS" not in scatter.columns:
        scatter["NUM_MATRICULAS"] = pd.NA

    return (
        scatter,
        infrastructure_column,
        category_column,
    )


def prepare_correlation_data(
    dataframe: pd.DataFrame,
    *,
    min_periods: int = 3,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Prepara a matriz de correlação dos indicadores disponíveis.

    Raises
    ------
    ValueError
        Quando não há ao menos dois indicadores com variação.
    """
    available_columns = [
        column
        for column in INDICATOR_LABELS
        if column in dataframe.columns
    ]

    if len(available_columns) < 2:
        raise ValueError(
            "A base possui menos de dois indicadores compatíveis."
        )

    correlation_data = (
        dataframe[available_columns]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
        .dropna(
            axis=1,
            how="all",
        )
    )

    valid_columns = [
        column
        for column in correlation_data.columns
        if correlation_data[column].nunique(
            dropna=True
        ) > 1
    ]

    correlation_data = correlation_data[
        valid_columns
    ]

    if correlation_data.shape[1] < 2:
        raise ValueError(
            "Não existem indicadores numéricos com variação "
            "suficiente para calcular a correlação."
        )

    correlation_matrix = correlation_data.corr(
        method="pearson",
        min_periods=min_periods,
    )

    labels = [
        INDICATOR_LABELS[column]
        for column in correlation_matrix.columns
    ]

    return correlation_matrix, labels


def build_distribution_summary(
    dataframe: pd.DataFrame,
) -> str:
    """
    Constrói o resumo textual da distribuição do IVE.
    """
    distribution = prepare_distribution_data(
        dataframe
    )

    lines = [
        (
            f"{row['Categoria IVE']}: "
            f"{int(row['Municípios'])} municípios "
            f"({float(row['Percentual']):.1f}%)"
        )
        for _, row in distribution.iterrows()
    ]

    return "\n".join(lines)


def build_scatter_summary(
    dataframe: pd.DataFrame,
) -> str:
    """
    Constrói o resumo estatístico do scatter.
    """
    (
        scatter,
        infrastructure_column,
        _,
    ) = prepare_scatter_data(
        dataframe
    )

    correlation = scatter[
        infrastructure_column
    ].corr(
        scatter["IVE"]
    )

    values = {
        "Correlação entre infraestrutura e IVE": correlation,
        "IVE mínimo": scatter["IVE"].min(),
        "IVE máximo": scatter["IVE"].max(),
        "Infraestrutura mínima": scatter[
            infrastructure_column
        ].min(),
        "Infraestrutura máxima": scatter[
            infrastructure_column
        ].max(),
        "Municípios analisados": len(scatter),
    }

    lines = []

    for label, value in values.items():
        if label == "Municípios analisados":
            lines.append(
                f"{label}: {int(value)}"
            )
        elif pd.isna(value):
            lines.append(
                f"{label}: N/D"
            )
        else:
            lines.append(
                f"{label}: {float(value):.3f}"
            )

    return "\n".join(lines)


def build_correlation_summary(
    dataframe: pd.DataFrame,
) -> str:
    """
    Constrói o resumo das correlações entre o IVE e os indicadores.
    """
    correlation_matrix, _ = (
        prepare_correlation_data(
            dataframe
        )
    )

    if "IVE" not in correlation_matrix.columns:
        raise ValueError(
            "A matriz de correlação não possui o indicador IVE."
        )

    ive_correlations = (
        correlation_matrix["IVE"]
        .drop(
            labels=["IVE"],
            errors="ignore",
        )
        .dropna()
        .sort_values(
            key=lambda series: series.abs(),
            ascending=False,
        )
    )

    if ive_correlations.empty:
        raise ValueError(
            "Não foi possível calcular correlações válidas com o IVE."
        )

    lines = [
        (
            f"IVE × {INDICATOR_LABELS.get(column, column)} "
            f"= {float(value):.3f}"
        )
        for column, value in ive_correlations.items()
    ]

    return "\n".join(lines)


def build_overview_payload(
    dataframe: pd.DataFrame,
) -> tuple[str, str, str]:
    """
    Constrói os três resumos enviados à análise integrada com IA.
    """
    return (
        build_distribution_summary(dataframe),
        build_scatter_summary(dataframe),
        build_correlation_summary(dataframe),
    )
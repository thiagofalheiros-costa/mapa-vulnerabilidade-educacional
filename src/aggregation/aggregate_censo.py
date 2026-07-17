"""
Agregação municipal do Censo Escolar.

Este módulo agrega informações no nível da escola para o nível
municipal, produzindo indicadores de infraestrutura, localização,
dependência administrativa e matrículas.
"""

import pandas as pd


REQUIRED_COLUMNS = [
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "SG_UF",
    "CO_ENTIDADE",
    "QT_MAT_BAS",
    "INFRA_SCORE",
    "IS_RURAL",
    "IS_ESTADUAL",
    "IS_MUNICIPAL",
    "IS_PUBLICA",
    "IN_BIBLIOTECA",
    "IN_LABORATORIO_INFORMATICA",
    "IN_QUADRA_ESPORTES",
    "IN_INTERNET",
    "IN_BANDA_LARGA",
]


def validate_columns(
    dataframe: pd.DataFrame,
) -> None:
    """
    Verifica se a base possui as colunas necessárias.

    Parameters
    ----------
    dataframe:
        Base escolar preparada para agregação.

    Raises
    ------
    ValueError
        Caso alguma coluna obrigatória não esteja disponível.
    """
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "A base do Censo não possui as colunas necessárias: "
            f"{missing_columns}"
        )


def aggregate_by_municipality(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Agrega os dados escolares no nível municipal.

    Os percentuais representam a proporção de escolas do município
    que possuem determinada característica.

    Parameters
    ----------
    dataframe:
        Base do Censo Escolar com uma linha por escola e variáveis
        derivadas criadas.

    Returns
    -------
    pandas.DataFrame
        Base agregada com uma linha por município.
    """
    validate_columns(dataframe)

    municipality_df = (
        dataframe
        .groupby(
            [
                "CO_MUNICIPIO",
                "NO_MUNICIPIO",
                "SG_UF",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            NUM_ESCOLAS=(
                "CO_ENTIDADE",
                "nunique",
            ),
            NUM_MATRICULAS=(
                "QT_MAT_BAS",
                lambda series: series.sum(min_count=1),
            ),
            INFRA_MEDIA=(
                "INFRA_SCORE",
                "mean",
            ),
            PERC_RURAL=(
                "IS_RURAL",
                "mean",
            ),
            PERC_PUBLICA=(
                "IS_PUBLICA",
                "mean",
            ),
            PERC_ESTADUAL=(
                "IS_ESTADUAL",
                "mean",
            ),
            PERC_MUNICIPAL=(
                "IS_MUNICIPAL",
                "mean",
            ),
            PERC_BIBLIOTECA=(
                "IN_BIBLIOTECA",
                "mean",
            ),
            PERC_LAB_INFO=(
                "IN_LABORATORIO_INFORMATICA",
                "mean",
            ),
            PERC_QUADRA=(
                "IN_QUADRA_ESPORTES",
                "mean",
            ),
            PERC_INTERNET=(
                "IN_INTERNET",
                "mean",
            ),
            PERC_BANDA_LARGA=(
                "IN_BANDA_LARGA",
                "mean",
            ),
        )
    )

    municipality_df["MEDIA_MATRICULAS_ESCOLA"] = (
        municipality_df["NUM_MATRICULAS"]
        / municipality_df["NUM_ESCOLAS"]
    )

    percentage_columns = [
        "PERC_RURAL",
        "PERC_PUBLICA",
        "PERC_ESTADUAL",
        "PERC_MUNICIPAL",
        "PERC_BIBLIOTECA",
        "PERC_LAB_INFO",
        "PERC_QUADRA",
        "PERC_INTERNET",
        "PERC_BANDA_LARGA",
    ]

    municipality_df["INFRA_MEDIA"] = (
        municipality_df["INFRA_MEDIA"]
        .round(3)
    )

    municipality_df[percentage_columns] = (
        municipality_df[percentage_columns]
        .round(4)
    )

    municipality_df["MEDIA_MATRICULAS_ESCOLA"] = (
        municipality_df["MEDIA_MATRICULAS_ESCOLA"]
        .round(2)
    )

    municipality_df["CO_MUNICIPIO"] = (
        pd.to_numeric(
            municipality_df["CO_MUNICIPIO"],
            errors="raise",
        )
        .astype("int64")
    )

    municipality_df = (
        municipality_df
        .sort_values("CO_MUNICIPIO")
        .reset_index(drop=True)
    )

    return municipality_df
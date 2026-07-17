"""
Agregação municipal do Censo Escolar.
"""

import pandas as pd


MUNICIPALITY_KEYS = [
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "SG_UF",
]


def aggregate_by_municipality(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Agrega a base escolar no nível municipal.

    Cada linha do resultado representa um município.

    São calculados indicadores de:

    - quantidade de escolas;
    - quantidade de matrículas;
    - média de matrículas por escola;
    - infraestrutura escolar;
    - localização;
    - dependência administrativa;
    - disponibilidade de equipamentos e serviços.
    """
    municipality_df = (
        df
        .groupby(
            MUNICIPALITY_KEYS,
            as_index=False,
        )
        .agg(
            NUM_ESCOLAS=(
                "CO_ENTIDADE",
                "nunique",
            ),
            NUM_MATRICULAS=(
                "QT_MAT_BAS",
                lambda series: series.sum(
                    min_count=1
                ),
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

    decimal_columns = [
        "INFRA_MEDIA",
        "PERC_RURAL",
        "PERC_PUBLICA",
        "PERC_ESTADUAL",
        "PERC_MUNICIPAL",
        "PERC_BIBLIOTECA",
        "PERC_LAB_INFO",
        "PERC_QUADRA",
        "PERC_INTERNET",
        "PERC_BANDA_LARGA",
        "MEDIA_MATRICULAS_ESCOLA",
    ]

    municipality_df[decimal_columns] = (
        municipality_df[decimal_columns]
        .round(3)
    )

    municipality_df = municipality_df.sort_values(
        by=[
            "SG_UF",
            "NO_MUNICIPIO",
        ],
        ignore_index=True,
    )

    return municipality_df
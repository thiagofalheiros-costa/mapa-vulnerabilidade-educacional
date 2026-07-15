"""
Agregação municipal do Censo Escolar.
"""

import pandas as pd


def aggregate_by_municipality(
    df: pd.DataFrame,
) -> pd.DataFrame:

    municipality_df = (

        df

        .groupby(

            [

                "CO_MUNICIPIO",

                "NO_MUNICIPIO",

                "SG_UF",

            ],

            as_index=False,

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

    municipality_df["INFRA_MEDIA"] = (

        municipality_df["INFRA_MEDIA"]

        .round(3)

    )

    return municipality_df
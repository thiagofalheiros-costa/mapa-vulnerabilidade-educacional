"""
Testes da agregação municipal do Censo Escolar.
"""

import pandas as pd

from src.aggregation.aggregate_censo import (
    aggregate_by_municipality,
)


def create_school_dataframe() -> pd.DataFrame:
    """
    Cria uma base escolar pequena com dois municípios.
    """
    return pd.DataFrame(
        {
            "CO_MUNICIPIO": [
                4300001,
                4300001,
                4300002,
            ],
            "NO_MUNICIPIO": [
                "Município A",
                "Município A",
                "Município B",
            ],
            "SG_UF": [
                "RS",
                "RS",
                "RS",
            ],
            "CO_ENTIDADE": [
                1001,
                1002,
                2001,
            ],
            "QT_MAT_BAS": [
                100,
                200,
                50,
            ],
            "INFRA_SCORE": [
                0.75,
                1.00,
                0.50,
            ],
            "IS_RURAL": [
                0,
                1,
                0,
            ],
            "IS_ESTADUAL": [
                1,
                0,
                1,
            ],
            "IS_MUNICIPAL": [
                0,
                1,
                0,
            ],
            "IN_BIBLIOTECA": [
                1,
                1,
                0,
            ],
            "IN_LABORATORIO_INFORMATICA": [
                0,
                1,
                0,
            ],
            "IN_INTERNET": [
                1,
                1,
                1,
            ],
            "IN_BANDA_LARGA": [
                1,
                0,
                1,
            ],
        }
    )


def test_aggregate_returns_one_row_per_municipality() -> None:
    df = create_school_dataframe()

    result = aggregate_by_municipality(df)

    assert len(result) == 2
    assert result["CO_MUNICIPIO"].nunique() == 2


def test_aggregate_municipality_a() -> None:
    df = create_school_dataframe()

    result = aggregate_by_municipality(df)

    municipality_a = result.loc[
        result["CO_MUNICIPIO"] == 4300001
    ].iloc[0]

    assert municipality_a["NUM_ESCOLAS"] == 2
    assert municipality_a["NUM_MATRICULAS"] == 300
    assert municipality_a["INFRA_MEDIA"] == 0.875
    assert municipality_a["PERC_RURAL"] == 0.5
    assert municipality_a["PERC_ESTADUAL"] == 0.5
    assert municipality_a["PERC_MUNICIPAL"] == 0.5
    assert municipality_a["PERC_BIBLIOTECA"] == 1.0
    assert municipality_a["PERC_LAB_INFO"] == 0.5
    assert municipality_a["PERC_INTERNET"] == 1.0
    assert municipality_a["PERC_BANDA_LARGA"] == 0.5


def test_total_enrollment_is_preserved() -> None:
    df = create_school_dataframe()

    result = aggregate_by_municipality(df)

    assert result["NUM_MATRICULAS"].sum() == df["QT_MAT_BAS"].sum()
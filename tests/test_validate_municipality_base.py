"""
Testes das validações da base municipal consolidada.
"""

import pandas as pd
import pytest

from src.validate_municipality_base import (
    validate_expected_columns,
    validate_municipality_key,
    validate_ranges,
    validate_school_flow_consistency,
)


def create_valid_dataframe() -> pd.DataFrame:
    """
    Cria uma base mínima válida para os testes.
    """
    return pd.DataFrame(
        {
            "CO_MUNICIPIO": [4300001, 4300002],
            "NO_MUNICIPIO": ["Município A", "Município B"],
            "SG_UF": ["RS", "RS"],
            "NUM_ESCOLAS": [5, 10],
            "NUM_MATRICULAS": [500, 1000],
            "INFRA_MEDIA": [0.7, 0.8],
            "PERC_RURAL": [0.2, 0.3],
            "PERC_ESTADUAL": [0.4, 0.5],
            "PERC_MUNICIPAL": [0.6, 0.5],
            "PERC_BIBLIOTECA": [0.8, 0.9],
            "PERC_LAB_INFO": [0.4, 0.5],
            "PERC_QUADRA": [0.7, 0.8],
            "PERC_INTERNET": [1.0, 1.0],
            "PERC_BANDA_LARGA": [0.8, 0.9],
            "PERC_PUBLICA": [1.0, 1.0],
            "MEDIA_MATRICULAS_ESCOLA": [100.0, 100.0],
            "APROVACAO_EF": [90.0, 91.0],
            "APROVACAO_EM": [85.0, 86.0],
            "REPROVACAO_EF": [8.0, 7.0],
            "REPROVACAO_EM": [10.0, 9.0],
            "ABANDONO_EF": [2.0, 2.0],
            "ABANDONO_EM": [5.0, 5.0],
            "QTD_ALUNOS_INSE": [100.0, 200.0],
            "MEDIA_INSE": [5.2, 5.5],
            "DISTORCAO_EF": [10.0, 11.0],
            "DISTORCAO_EM": [15.0, 16.0],
        }
    )


def test_required_columns_are_valid() -> None:
    """
    Confirma que uma base completa passa pela validação.
    """
    dataframe = create_valid_dataframe()

    validate_expected_columns(dataframe)


def test_missing_column_raises_error() -> None:
    """
    Confirma que uma coluna ausente gera erro.
    """
    dataframe = (
        create_valid_dataframe()
        .drop(columns="MEDIA_INSE")
    )

    with pytest.raises(
        ValueError,
        match="Colunas ausentes",
    ):
        validate_expected_columns(dataframe)


def test_duplicated_municipality_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Confirma que códigos municipais duplicados geram erro.
    """
    dataframe = create_valid_dataframe()

    dataframe.loc[1, "CO_MUNICIPIO"] = (
        dataframe.loc[0, "CO_MUNICIPIO"]
    )

    monkeypatch.setattr(
        "src.validate_municipality_base."
        "EXPECTED_MUNICIPALITIES",
        2,
    )

    with pytest.raises(
        ValueError,
        match="municípios duplicados",
    ):
        validate_municipality_key(dataframe)


def test_proportion_above_one_raises_error() -> None:
    """
    Confirma que proporções acima de um geram erro.
    """
    dataframe = create_valid_dataframe()

    dataframe.loc[0, "PERC_RURAL"] = 1.2

    with pytest.raises(
        ValueError,
        match="PERC_RURAL",
    ):
        validate_ranges(dataframe)


def test_rate_above_one_hundred_raises_error() -> None:
    """
    Confirma que taxas acima de cem geram erro.
    """
    dataframe = create_valid_dataframe()

    dataframe.loc[0, "DISTORCAO_EF"] = 105.0

    with pytest.raises(
        ValueError,
        match="DISTORCAO_EF",
    ):
        validate_ranges(dataframe)


def test_school_flow_sum_is_valid() -> None:
    """
    Confirma que taxas que totalizam cem são aceitas.
    """
    dataframe = create_valid_dataframe()

    validate_school_flow_consistency(dataframe)


def test_invalid_school_flow_sum_raises_error() -> None:
    """
    Confirma que taxas inconsistentes geram erro.
    """
    dataframe = create_valid_dataframe()

    dataframe.loc[0, "APROVACAO_EF"] = 80.0

    with pytest.raises(
        ValueError,
        match="não somam",
    ):
        validate_school_flow_consistency(dataframe)
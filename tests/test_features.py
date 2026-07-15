"""
Testes das features do Censo Escolar.
"""

import pandas as pd

from src.features.censo_features import (
    create_features,
    create_infrastructure_score,
    create_public_network_flags,
)


def create_test_dataframe() -> pd.DataFrame:
    """
    Cria uma base escolar pequena para os testes.
    """
    return pd.DataFrame(
        {
            "TP_DEPENDENCIA": [1, 2, 3],
            "TP_LOCALIZACAO": [1, 2, 1],
            "IN_AGUA_POTAVEL": [1, 1, 0],
            "IN_ENERGIA_REDE_PUBLICA": [1, 1, 1],
            "IN_ESGOTO_REDE_PUBLICA": [1, 0, 0],
            "IN_BIBLIOTECA": [1, 1, 0],
            "IN_LABORATORIO_INFORMATICA": [1, 0, 0],
            "IN_QUADRA_ESPORTES": [1, 1, 1],
            "IN_INTERNET": [1, 1, 1],
            "IN_BANDA_LARGA": [1, 0, 1],
        }
    )


def test_create_infrastructure_score() -> None:
    df = create_test_dataframe()

    result = create_infrastructure_score(df)

    assert "INFRA_SCORE" in result.columns
    assert result.loc[0, "INFRA_SCORE"] == 1.0
    assert result.loc[1, "INFRA_SCORE"] == 0.625
    assert result.loc[2, "INFRA_SCORE"] == 0.5


def test_create_public_network_flags() -> None:
    df = create_test_dataframe()

    result = create_public_network_flags(df)

    assert result["IS_FEDERAL"].tolist() == [1, 0, 0]
    assert result["IS_ESTADUAL"].tolist() == [0, 1, 0]
    assert result["IS_MUNICIPAL"].tolist() == [0, 0, 1]
    assert result["IS_RURAL"].tolist() == [0, 1, 0]


def test_create_features_preserves_number_of_rows() -> None:
    df = create_test_dataframe()

    result = create_features(df)

    assert len(result) == len(df)
    assert "INFRA_SCORE" in result.columns
    assert "IS_RURAL" in result.columns
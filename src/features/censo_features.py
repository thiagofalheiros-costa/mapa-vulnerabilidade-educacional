"""
Feature engineering do Censo Escolar.
"""

import pandas as pd

from src.logger import setup_logger


logger = setup_logger()


INFRA_COLUMNS = [
    "IN_AGUA_POTAVEL",
    "IN_ENERGIA_REDE_PUBLICA",
    "IN_ESGOTO_REDE_PUBLICA",
    "IN_BIBLIOTECA",
    "IN_LABORATORIO_INFORMATICA",
    "IN_QUADRA_ESPORTES",
    "IN_INTERNET",
    "IN_BANDA_LARGA",
]


def create_infrastructure_score(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cria o score de infraestrutura escolar.
    """

    feature_df = df.copy()

    feature_df["INFRA_SCORE"] = (
        feature_df[INFRA_COLUMNS]
        .mean(axis=1)
        .round(3)
    )

    logger.info(
        "Infraestrutura calculada."
    )

    return feature_df


def create_public_network_flags(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cria indicadores de rede.
    """

    feature_df = df.copy()

    feature_df["IS_ESTADUAL"] = (
        feature_df["TP_DEPENDENCIA"] == 2
    ).astype(int)

    feature_df["IS_MUNICIPAL"] = (
        feature_df["TP_DEPENDENCIA"] == 3
    ).astype(int)

    feature_df["IS_FEDERAL"] = (
        feature_df["TP_DEPENDENCIA"] == 1
    ).astype(int)

    feature_df["IS_RURAL"] = (
        feature_df["TP_LOCALIZACAO"] == 2
    ).astype(int)

    return feature_df


def create_features(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = create_infrastructure_score(df)

    df = create_public_network_flags(df)

    return df
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

    O score corresponde à média dos indicadores binários
    de infraestrutura disponíveis para cada escola.

    O resultado varia entre zero e um:

    - zero: nenhum item de infraestrutura disponível;
    - um: todos os itens de infraestrutura disponíveis.
    """
    feature_df = df.copy()

    feature_df["INFRA_SCORE"] = (
        feature_df[INFRA_COLUMNS]
        .mean(axis=1)
        .round(3)
    )

    logger.info(
        "Score de infraestrutura calculado."
    )

    return feature_df


def create_public_network_flags(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cria indicadores binários de rede e localização.

    Dependências administrativas:

    - 1: federal;
    - 2: estadual;
    - 3: municipal;
    - 4: privada.

    Uma escola é considerada pública quando pertence às
    redes federal, estadual ou municipal.
    """
    feature_df = df.copy()

    feature_df["IS_FEDERAL"] = (
        feature_df["TP_DEPENDENCIA"] == 1
    ).astype(int)

    feature_df["IS_ESTADUAL"] = (
        feature_df["TP_DEPENDENCIA"] == 2
    ).astype(int)

    feature_df["IS_MUNICIPAL"] = (
        feature_df["TP_DEPENDENCIA"] == 3
    ).astype(int)

    feature_df["IS_PUBLICA"] = (
        feature_df["TP_DEPENDENCIA"]
        .isin([1, 2, 3])
        .astype(int)
    )

    feature_df["IS_RURAL"] = (
        feature_df["TP_LOCALIZACAO"] == 2
    ).astype(int)

    logger.info(
        "Indicadores de rede e localização criados."
    )

    return feature_df


def create_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Executa todas as etapas de feature engineering do Censo.

    Parameters
    ----------
    df:
        Base escolar tratada.

    Returns
    -------
    pd.DataFrame
        Base escolar com as novas features.
    """
    feature_df = create_infrastructure_score(df)

    feature_df = create_public_network_flags(
        feature_df
    )

    return feature_df
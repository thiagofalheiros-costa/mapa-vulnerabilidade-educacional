"""
Feature engineering do Censo Escolar.

Este módulo cria indicadores binários de infraestrutura,
localização e dependência administrativa no nível da escola.
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


BASE_COLUMNS = [
    "TP_DEPENDENCIA",
    "TP_LOCALIZACAO",
    *INFRA_COLUMNS,
]


def validate_feature_columns(
    dataframe: pd.DataFrame,
) -> None:
    """
    Verifica as colunas necessárias para criar as features.

    Parameters
    ----------
    dataframe:
        Base do Censo Escolar.

    Raises
    ------
    ValueError
        Caso alguma coluna obrigatória esteja ausente.
    """
    missing_columns = [
        column
        for column in BASE_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Não foi possível criar as features do Censo. "
            f"Colunas ausentes: {missing_columns}"
        )


def create_infrastructure_score(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cria o score médio de infraestrutura por escola.

    Parameters
    ----------
    dataframe:
        Base escolar contendo indicadores binários de infraestrutura.

    Returns
    -------
    pandas.DataFrame
        Base com a coluna INFRA_SCORE.
    """
    feature_df = dataframe.copy()

    for column in INFRA_COLUMNS:
        feature_df[column] = pd.to_numeric(
            feature_df[column],
            errors="coerce",
        )

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
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cria indicadores de rede pública e localização.

    Parameters
    ----------
    dataframe:
        Base do Censo Escolar.

    Returns
    -------
    pandas.DataFrame
        Base com indicadores binários derivados.
    """
    feature_df = dataframe.copy()

    feature_df["IS_FEDERAL"] = (
        feature_df["TP_DEPENDENCIA"] == 1
    ).astype("int8")

    feature_df["IS_ESTADUAL"] = (
        feature_df["TP_DEPENDENCIA"] == 2
    ).astype("int8")

    feature_df["IS_MUNICIPAL"] = (
        feature_df["TP_DEPENDENCIA"] == 3
    ).astype("int8")

    feature_df["IS_PUBLICA"] = (
        feature_df["TP_DEPENDENCIA"].isin(
            [1, 2, 3]
        )
    ).astype("int8")

    feature_df["IS_RURAL"] = (
        feature_df["TP_LOCALIZACAO"] == 2
    ).astype("int8")

    return feature_df

def create_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Executa todas as etapas de feature engineering do Censo.

    Parameters
    ----------
    dataframe:
        Base escolar do Censo.

    Returns
    -------
    pandas.DataFrame
        Base escolar com as features criadas.
    """
    validate_feature_columns(dataframe)

    feature_df = create_infrastructure_score(
        dataframe
    )

    feature_df = create_public_network_flags(
        feature_df
    )

    logger.info(
        "Features escolares criadas: %s linhas.",
        len(feature_df),
    )

    return feature_df
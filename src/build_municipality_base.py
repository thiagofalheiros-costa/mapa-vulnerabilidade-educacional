"""
Construção da base municipal consolidada.

Este módulo integra as características municipais derivadas
do Censo Escolar com os indicadores educacionais do INEP.
"""

from pathlib import Path

import pandas as pd

from src.config import (
    MUNICIPALITY_BASE_PATH,
    MUNICIPALITY_FEATURES_PATH,
    MUNICIPALITY_INDICATORS_PATH,
)
from src.logger import setup_logger


logger = setup_logger()


def validate_input_file(
    file_path: Path,
) -> None:
    """
    Verifica se um arquivo de entrada existe.

    Parameters
    ----------
    file_path:
        Caminho do arquivo que será validado.

    Raises
    ------
    FileNotFoundError
        Caso o arquivo não seja encontrado.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {file_path}"
        )


def validate_unique_municipalities(
    dataframe: pd.DataFrame,
    dataset_name: str,
) -> None:
    """
    Verifica se existe uma única linha por município.

    Parameters
    ----------
    dataframe:
        Base municipal que será validada.

    dataset_name:
        Nome da base utilizado nas mensagens de erro.

    Raises
    ------
    ValueError
        Caso existam códigos municipais duplicados.
    """
    duplicated = dataframe[
        "CO_MUNICIPIO"
    ].duplicated(
        keep=False,
    )

    if duplicated.any():
        duplicated_codes = (
            dataframe.loc[
                duplicated,
                "CO_MUNICIPIO",
            ]
            .drop_duplicates()
            .astype(str)
            .tolist()
        )

        raise ValueError(
            f"A base {dataset_name} possui municípios duplicados: "
            f"{duplicated_codes[:10]}"
        )


def validate_municipality_coverage(
    features: pd.DataFrame,
    indicators: pd.DataFrame,
) -> list[int]:
    """
    Compara a cobertura municipal das bases de entrada.

    A base de características define o universo analítico:
    municípios com oferta pública de Ensino Médio propedêutico.

    Municípios presentes apenas na base de indicadores são aceitos,
    pois não possuem escolas no recorte definido e serão excluídos
    da base consolidada.

    Parameters
    ----------
    features:
        Base de características municipais.

    indicators:
        Base de indicadores educacionais.

    Returns
    -------
    list[int]
        Códigos presentes apenas na base de indicadores.

    Raises
    ------
    ValueError
        Caso algum município da base de características não esteja
        disponível na base de indicadores.
    """
    feature_codes = set(
        features["CO_MUNICIPIO"]
    )

    indicator_codes = set(
        indicators["CO_MUNICIPIO"]
    )

    missing_in_indicators = sorted(
        feature_codes - indicator_codes
    )

    excluded_from_features = sorted(
        indicator_codes - feature_codes
    )

    if missing_in_indicators:
        raise ValueError(
            "Existem municípios com oferta de Ensino Médio "
            "propedêutico sem indicadores educacionais. "
            f"Códigos: {missing_in_indicators[:10]}."
        )

    if excluded_from_features:
        logger.warning(
            "%s município(s) da base de indicadores não possuem "
            "oferta pública de Ensino Médio propedêutico e serão "
            "excluídos da base consolidada. Códigos: %s",
            len(excluded_from_features),
            excluded_from_features[:10],
        )

    return excluded_from_features


def validate_merged_indicators(
    municipality_base: pd.DataFrame,
    indicator_columns: list[str],
) -> None:
    """
    Verifica se algum município ficou sem todos os indicadores
    após a integração.

    Parameters
    ----------
    municipality_base:
        Base municipal consolidada.

    indicator_columns:
        Colunas oriundas da base de indicadores.
    """
    indicator_value_columns = [
        column
        for column in indicator_columns
        if column != "CO_MUNICIPIO"
    ]

    if not indicator_value_columns:
        raise ValueError(
            "Nenhuma coluna de indicador foi encontrada "
            "para a integração."
        )

    municipalities_without_indicators = (
        municipality_base[
            indicator_value_columns
        ]
        .isna()
        .all(axis=1)
    )

    if municipalities_without_indicators.any():
        missing_codes = (
            municipality_base.loc[
                municipalities_without_indicators,
                "CO_MUNICIPIO",
            ]
            .astype(str)
            .tolist()
        )

        raise ValueError(
            "Foram encontrados municípios sem nenhum indicador "
            f"após a integração: {missing_codes[:10]}."
        )


def build_municipality_base(
    features_path: Path = MUNICIPALITY_FEATURES_PATH,
    indicators_path: Path = MUNICIPALITY_INDICATORS_PATH,
) -> pd.DataFrame:
    """
    Integra características e indicadores municipais.

    A base de características municipais é utilizada como base
    principal. Os indicadores são incorporados por meio do código
    do município.

    Parameters
    ----------
    features_path:
        Caminho da base de características municipais.

    indicators_path:
        Caminho da base de indicadores educacionais.

    Returns
    -------
    pandas.DataFrame
        Base municipal consolidada.
    """
    validate_input_file(
        features_path
    )
    validate_input_file(
        indicators_path
    )

    logger.info(
        "Carregando características municipais: %s",
        features_path,
    )

    features = pd.read_parquet(
        features_path
    )

    logger.info(
        "Carregando indicadores municipais: %s",
        indicators_path,
    )

    indicators = pd.read_parquet(
        indicators_path
    )

    validate_unique_municipalities(
        features,
        "municipality_features",
    )

    validate_unique_municipalities(
        indicators,
        "municipality_indicators",
    )

    excluded_codes = validate_municipality_coverage(
        features,
        indicators,
    )

    indicator_columns = [
        column
        for column in indicators.columns
        if column not in {
            "NO_MUNICIPIO",
            "SG_UF",
        }
    ]

    municipality_base = features.merge(
        indicators[
            indicator_columns
        ],
        on="CO_MUNICIPIO",
        how="left",
        validate="one_to_one",
    )

    if len(municipality_base) != len(features):
        raise ValueError(
            "A integração alterou a quantidade de municípios: "
            f"{len(features)} antes e "
            f"{len(municipality_base)} depois."
        )

    validate_merged_indicators(
        municipality_base=municipality_base,
        indicator_columns=indicator_columns,
    )

    municipality_base = (
        municipality_base
        .sort_values(
            "CO_MUNICIPIO"
        )
        .reset_index(
            drop=True
        )
    )

    logger.info(
        "Base municipal construída: %s linhas e %s colunas.",
        municipality_base.shape[0],
        municipality_base.shape[1],
    )

    logger.info(
        "Universo analítico consolidado: %s municípios com oferta "
        "pública de Ensino Médio propedêutico.",
        municipality_base[
            "CO_MUNICIPIO"
        ].nunique(),
    )

    if excluded_codes:
        logger.info(
            "Municípios excluídos por ausência de oferta "
            "no recorte: %s",
            excluded_codes,
        )

    return municipality_base


def save_municipality_base(
    dataframe: pd.DataFrame,
    output_path: Path = MUNICIPALITY_BASE_PATH,
) -> Path:
    """
    Salva a base municipal consolidada em formato Parquet.

    Parameters
    ----------
    dataframe:
        Base municipal consolidada.

    output_path:
        Caminho do arquivo de saída.

    Returns
    -------
    pathlib.Path
        Caminho do arquivo gerado.
    """
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_parquet(
        output_path,
        index=False,
    )

    logger.info(
        "Base municipal salva em: %s",
        output_path,
    )

    return output_path


def main() -> None:
    """
    Constrói e salva a base municipal consolidada.
    """
    municipality_base = build_municipality_base()

    output_path = save_municipality_base(
        municipality_base
    )

    print("\nDimensão da base municipal:")
    print(
        municipality_base.shape
    )

    print("\nQuantidade de municípios:")
    print(
        municipality_base[
            "CO_MUNICIPIO"
        ].nunique()
    )

    print("\nValores ausentes:")
    print(
        municipality_base
        .isna()
        .sum()
        .sort_values(
            ascending=False
        )
        .to_string()
    )

    print("\nPrimeiras linhas:")
    print(
        municipality_base
        .head()
        .to_string(
            index=False
        )
    )

    print("\nArquivo gerado em:")
    print(
        output_path
    )


if __name__ == "__main__":
    main()
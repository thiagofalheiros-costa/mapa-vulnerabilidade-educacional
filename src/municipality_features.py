"""
Construção das características municipais do Censo Escolar.

Este módulo carrega o Parquet tratado do Censo Escolar, cria
features no nível da escola, agrega os resultados por município
e salva a base municipal em formato Parquet.
"""

from pathlib import Path

import pandas as pd

from src.aggregation.aggregate_censo import aggregate_by_municipality
from src.features.censo_features import create_features
from src.config import (
    CENSO_PROCESSED_PATH,
    MUNICIPALITY_FEATURES_PATH,
)
from src.logger import setup_logger


logger = setup_logger()


EXPECTED_COLUMNS = [
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "SG_UF",
    "NUM_ESCOLAS",
    "NUM_MATRICULAS",
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


def validate_input_file(
    file_path: Path,
) -> None:
    """
    Verifica se o arquivo de entrada existe.

    Parameters
    ----------
    file_path:
        Caminho do Parquet do Censo Escolar.

    Raises
    ------
    FileNotFoundError
        Caso o arquivo não seja encontrado.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Arquivo do Censo não encontrado: {file_path}"
        )


def validate_municipality_features(
    dataframe: pd.DataFrame,
    expected_municipalities: int = 497,
) -> None:
    """
    Valida a base municipal criada.

    Parameters
    ----------
    dataframe:
        Base municipal agregada.

    expected_municipalities:
        Quantidade esperada de municípios.

    Raises
    ------
    ValueError
        Caso a base possua problemas estruturais.
    """
    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "A base municipal não possui todas as colunas esperadas: "
            f"{missing_columns}"
        )

    if dataframe["CO_MUNICIPIO"].duplicated().any():
        raise ValueError(
            "A base municipal possui códigos de município duplicados."
        )

    if len(dataframe) != expected_municipalities:
        raise ValueError(
            "Quantidade inesperada de municípios. "
            f"Esperado: {expected_municipalities}. "
            f"Encontrado: {len(dataframe)}."
        )

    if dataframe["CO_MUNICIPIO"].nunique() != expected_municipalities:
        raise ValueError(
            "A quantidade de códigos municipais únicos é diferente "
            "da quantidade esperada."
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

    invalid_percentages = (
        (dataframe[percentage_columns] < 0)
        | (dataframe[percentage_columns] > 1)
    )

    if invalid_percentages.any().any():
        invalid_columns = (
            invalid_percentages
            .any()
            .loc[lambda series: series]
            .index
            .tolist()
        )

        raise ValueError(
            "Foram encontrados percentuais fora do intervalo "
            f"entre 0 e 1: {invalid_columns}"
        )

    if (dataframe["NUM_ESCOLAS"] <= 0).any():
        raise ValueError(
            "Foram encontrados municípios sem escolas."
        )

    logger.info(
        "Validação concluída: %s municípios e %s colunas.",
        dataframe.shape[0],
        dataframe.shape[1],
    )


def build_municipality_features(
    input_path: Path = CENSO_PROCESSED_PATH,
) -> pd.DataFrame:
    """
    Constrói as características municipais.

    Parameters
    ----------
    input_path:
        Caminho do Parquet tratado do Censo Escolar.

    Returns
    -------
    pandas.DataFrame
        Base municipal agregada.
    """
    validate_input_file(input_path)

    logger.info(
        "Carregando Parquet do Censo: %s",
        input_path,
    )

    censo = pd.read_parquet(input_path)

    logger.info(
        "Censo carregado: %s linhas e %s colunas.",
        censo.shape[0],
        censo.shape[1],
    )

    school_features = create_features(censo)

    municipality_features = aggregate_by_municipality(
        school_features
    )

    validate_municipality_features(
        municipality_features
    )

    return municipality_features


def save_municipality_features(
    dataframe: pd.DataFrame,
    output_path: Path = MUNICIPALITY_FEATURES_PATH,
) -> Path:
    """
    Salva as características municipais em formato Parquet.

    Parameters
    ----------
    dataframe:
        Base de características municipais.

    output_path:
        Caminho de saída.

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
        "Características municipais salvas em: %s",
        output_path,
    )

    return output_path


def main() -> None:
    """
    Executa a construção da base de características municipais.
    """
    municipality_features = build_municipality_features()

    output_path = save_municipality_features(
        municipality_features
    )

    print("\nDimensão:")
    print(municipality_features.shape)

    print("\nQuantidade de municípios:")
    print(
        municipality_features[
            "CO_MUNICIPIO"
        ].nunique()
    )

    print("\nColunas:")
    print(municipality_features.columns.tolist())

    print("\nValores ausentes:")
    print(
        municipality_features
        .isna()
        .sum()
        .sort_values(ascending=False)
        .to_string()
    )

    print("\nPrimeiras linhas:")
    print(
        municipality_features
        .head()
        .to_string(index=False)
    )

    print("\nArquivo gerado em:")
    print(output_path)


if __name__ == "__main__":
    main()
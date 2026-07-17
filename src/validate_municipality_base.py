"""
Validação da base municipal consolidada.

Este módulo executa verificações estruturais, de integridade
e de consistência sobre a base final de municípios.
"""

from pathlib import Path

import pandas as pd

from src.config import MUNICIPALITY_BASE_PATH
from src.logger import setup_logger


logger = setup_logger()


EXPECTED_MUNICIPALITIES = 497

IDENTIFICATION_COLUMNS = [
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "SG_UF",
]

COUNT_COLUMNS = [
    "NUM_ESCOLAS",
    "NUM_MATRICULAS",
    "MEDIA_MATRICULAS_ESCOLA",
    "QTD_ALUNOS_INSE",
]

PROPORTION_COLUMNS = [
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
]

RATE_COLUMNS = [
    "APROVACAO_EF",
    "APROVACAO_EM",
    "REPROVACAO_EF",
    "REPROVACAO_EM",
    "ABANDONO_EF",
    "ABANDONO_EM",
    "DISTORCAO_EF",
    "DISTORCAO_EM",
]

EXPECTED_COLUMNS = [
    *IDENTIFICATION_COLUMNS,
    "NUM_ESCOLAS",
    "NUM_MATRICULAS",
    "INFRA_MEDIA",
    "PERC_RURAL",
    "PERC_ESTADUAL",
    "PERC_MUNICIPAL",
    "PERC_BIBLIOTECA",
    "PERC_LAB_INFO",
    "PERC_QUADRA",
    "PERC_INTERNET",
    "PERC_BANDA_LARGA",
    "PERC_PUBLICA",
    "MEDIA_MATRICULAS_ESCOLA",
    "APROVACAO_EF",
    "APROVACAO_EM",
    "REPROVACAO_EF",
    "REPROVACAO_EM",
    "ABANDONO_EF",
    "ABANDONO_EM",
    "QTD_ALUNOS_INSE",
    "MEDIA_INSE",
    "DISTORCAO_EF",
    "DISTORCAO_EM",
]


def validate_file_exists(
    file_path: Path,
) -> None:
    """
    Verifica se o arquivo da base municipal existe.

    Parameters
    ----------
    file_path:
        Caminho do arquivo Parquet.

    Raises
    ------
    FileNotFoundError
        Caso o arquivo não seja encontrado.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Base municipal não encontrada: {file_path}"
        )


def validate_expected_columns(
    dataframe: pd.DataFrame,
) -> None:
    """
    Verifica se todas as colunas esperadas estão presentes.

    Parameters
    ----------
    dataframe:
        Base municipal consolidada.

    Raises
    ------
    ValueError
        Caso existam colunas obrigatórias ausentes.
    """
    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "A base municipal não possui todas as colunas esperadas. "
            f"Colunas ausentes: {missing_columns}"
        )


def validate_municipality_key(
    dataframe: pd.DataFrame,
) -> None:
    """
    Valida a chave municipal da base.

    Parameters
    ----------
    dataframe:
        Base municipal consolidada.

    Raises
    ------
    ValueError
        Caso existam códigos ausentes, duplicados ou quantidade
        inesperada de municípios.
    """
    if dataframe["CO_MUNICIPIO"].isna().any():
        raise ValueError(
            "Existem códigos de município ausentes."
        )

    duplicated = dataframe["CO_MUNICIPIO"].duplicated(
        keep=False
    )

    if duplicated.any():
        duplicated_codes = (
            dataframe.loc[
                duplicated,
                "CO_MUNICIPIO",
            ]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            "Foram encontrados municípios duplicados: "
            f"{duplicated_codes[:10]}"
        )

    municipality_count = (
        dataframe["CO_MUNICIPIO"].nunique()
    )

    if municipality_count != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de municípios. "
            f"Esperado: {EXPECTED_MUNICIPALITIES}. "
            f"Encontrado: {municipality_count}."
        )

    if len(dataframe) != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de linhas. "
            f"Esperado: {EXPECTED_MUNICIPALITIES}. "
            f"Encontrado: {len(dataframe)}."
        )


def validate_identification_columns(
    dataframe: pd.DataFrame,
) -> None:
    """
    Valida nome e UF dos municípios.

    Parameters
    ----------
    dataframe:
        Base municipal consolidada.

    Raises
    ------
    ValueError
        Caso existam identificadores ausentes ou inválidos.
    """
    for column in IDENTIFICATION_COLUMNS:
        if dataframe[column].isna().any():
            raise ValueError(
                f"A coluna {column} possui valores ausentes."
            )

    if dataframe["NO_MUNICIPIO"].astype(str).str.strip().eq("").any():
        raise ValueError(
            "Existem municípios com nome vazio."
        )

    invalid_uf = (
        dataframe["SG_UF"]
        .astype(str)
        .str.strip()
        .ne("RS")
    )

    if invalid_uf.any():
        invalid_values = (
            dataframe.loc[
                invalid_uf,
                "SG_UF",
            ]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            "Foram encontradas UFs diferentes de RS: "
            f"{invalid_values}"
        )


def validate_numeric_columns(
    dataframe: pd.DataFrame,
) -> None:
    """
    Verifica se as colunas analíticas são numéricas.

    Parameters
    ----------
    dataframe:
        Base municipal consolidada.

    Raises
    ------
    ValueError
        Caso alguma coluna analítica não seja numérica.
    """
    numeric_columns = [
        *COUNT_COLUMNS,
        *PROPORTION_COLUMNS,
        *RATE_COLUMNS,
        "MEDIA_INSE",
    ]

    invalid_columns = [
        column
        for column in numeric_columns
        if not pd.api.types.is_numeric_dtype(
            dataframe[column]
        )
    ]

    if invalid_columns:
        raise ValueError(
            "As seguintes colunas deveriam ser numéricas: "
            f"{invalid_columns}"
        )


def validate_positive_values(
    dataframe: pd.DataFrame,
) -> None:
    """
    Verifica valores que devem ser positivos.

    Parameters
    ----------
    dataframe:
        Base municipal consolidada.

    Raises
    ------
    ValueError
        Caso existam municípios sem escolas, matrículas ou média
        válida de matrículas.
    """
    strictly_positive_columns = [
        "NUM_ESCOLAS",
        "NUM_MATRICULAS",
        "MEDIA_MATRICULAS_ESCOLA",
    ]

    for column in strictly_positive_columns:
        invalid = dataframe[column] <= 0

        if invalid.any():
            municipalities = (
                dataframe.loc[
                    invalid,
                    [
                        "CO_MUNICIPIO",
                        "NO_MUNICIPIO",
                        column,
                    ],
                ]
                .head(10)
                .to_dict("records")
            )

            raise ValueError(
                f"A coluna {column} possui valores menores "
                f"ou iguais a zero: {municipalities}"
            )

    invalid_inse_count = (
        dataframe["QTD_ALUNOS_INSE"].notna()
        & (dataframe["QTD_ALUNOS_INSE"] <= 0)
    )

    if invalid_inse_count.any():
        raise ValueError(
            "QTD_ALUNOS_INSE possui valores menores ou iguais "
            "a zero entre os registros preenchidos."
        )


def validate_ranges(
    dataframe: pd.DataFrame,
) -> None:
    """
    Valida os intervalos das variáveis analíticas.

    Parameters
    ----------
    dataframe:
        Base municipal consolidada.

    Raises
    ------
    ValueError
        Caso existam proporções ou taxas fora dos limites válidos.
    """
    for column in PROPORTION_COLUMNS:
        invalid = (
            dataframe[column].notna()
            & ~dataframe[column].between(
                0,
                1,
                inclusive="both",
            )
        )

        if invalid.any():
            invalid_values = (
                dataframe.loc[
                    invalid,
                    [
                        "CO_MUNICIPIO",
                        "NO_MUNICIPIO",
                        column,
                    ],
                ]
                .head(10)
                .to_dict("records")
            )

            raise ValueError(
                f"A coluna {column} possui valores fora "
                f"do intervalo entre 0 e 1: {invalid_values}"
            )

    for column in RATE_COLUMNS:
        invalid = (
            dataframe[column].notna()
            & ~dataframe[column].between(
                0,
                100,
                inclusive="both",
            )
        )

        if invalid.any():
            invalid_values = (
                dataframe.loc[
                    invalid,
                    [
                        "CO_MUNICIPIO",
                        "NO_MUNICIPIO",
                        column,
                    ],
                ]
                .head(10)
                .to_dict("records")
            )

            raise ValueError(
                f"A coluna {column} possui valores fora "
                f"do intervalo entre 0 e 100: {invalid_values}"
            )


def validate_public_network_percentage(
    dataframe: pd.DataFrame,
    tolerance: float = 0.0002,
) -> None:
    """
    Verifica a consistência do percentual de escolas públicas.

    O percentual público deve ser igual à soma das proporções
    estadual e municipal, considerando que a base atual não possui
    escolas federais ou que sua participação já foi incorporada
    antes da remoção da coluna correspondente.

    Parameters
    ----------
    dataframe:
        Base municipal consolidada.

    tolerance:
        Tolerância aceita para diferenças decorrentes de
        arredondamento.

    Raises
    ------
    ValueError
        Caso o percentual público seja menor do que a soma das
        proporções estadual e municipal.
    """
    known_public_percentage = (
        dataframe["PERC_ESTADUAL"]
        + dataframe["PERC_MUNICIPAL"]
    )

    invalid = (
        dataframe["PERC_PUBLICA"]
        + tolerance
        < known_public_percentage
    )

    if invalid.any():
        invalid_values = (
            dataframe.loc[
                invalid,
                [
                    "CO_MUNICIPIO",
                    "NO_MUNICIPIO",
                    "PERC_PUBLICA",
                    "PERC_ESTADUAL",
                    "PERC_MUNICIPAL",
                ],
            ]
            .head(10)
            .to_dict("records")
        )

        raise ValueError(
            "PERC_PUBLICA é inferior à soma das proporções "
            f"estadual e municipal: {invalid_values}"
        )


def validate_school_flow_consistency(
    dataframe: pd.DataFrame,
    tolerance: float = 0.2,
) -> None:
    """
    Verifica a soma das taxas de rendimento escolar.

    Aprovação, reprovação e abandono devem totalizar
    aproximadamente 100%.

    Parameters
    ----------
    dataframe:
        Base municipal consolidada.

    tolerance:
        Diferença máxima aceita em relação a 100 pontos percentuais.

    Raises
    ------
    ValueError
        Caso alguma soma preenchida esteja fora da tolerância.
    """
    stages = {
        "EF": [
            "APROVACAO_EF",
            "REPROVACAO_EF",
            "ABANDONO_EF",
        ],
        "EM": [
            "APROVACAO_EM",
            "REPROVACAO_EM",
            "ABANDONO_EM",
        ],
    }

    for stage, columns in stages.items():
        complete_rows = dataframe[columns].notna().all(
            axis=1
        )

        rate_sum = dataframe[columns].sum(
            axis=1,
            min_count=len(columns),
        )

        invalid = (
            complete_rows
            & ((rate_sum - 100).abs() > tolerance)
        )

        if invalid.any():
            invalid_data = (
                dataframe.loc[
                    invalid,
                    [
                        "CO_MUNICIPIO",
                        "NO_MUNICIPIO",
                        *columns,
                    ],
                ]
                .assign(SOMA=rate_sum.loc[invalid])
                .head(10)
                .to_dict("records")
            )

            raise ValueError(
                f"As taxas de rendimento do {stage} não somam "
                f"aproximadamente 100: {invalid_data}"
            )


def validate_missing_values(
    dataframe: pd.DataFrame,
) -> pd.Series:
    """
    Produz o relatório de valores ausentes.

    As ausências não causam erro porque parte delas decorre
    da indisponibilidade dos dados na fonte original.

    Parameters
    ----------
    dataframe:
        Base municipal consolidada.

    Returns
    -------
    pandas.Series
        Quantidade de ausências por coluna.
    """
    missing_values = (
        dataframe
        .isna()
        .sum()
        .sort_values(ascending=False)
    )

    unexpected_missing_columns = [
        column
        for column in dataframe.columns
        if missing_values[column] > 0
        and column not in {
            "QTD_ALUNOS_INSE",
            "MEDIA_INSE",
            "APROVACAO_EM",
            "REPROVACAO_EM",
            "ABANDONO_EM",
            "DISTORCAO_EM",
        }
    ]

    if unexpected_missing_columns:
        logger.warning(
            "Foram encontradas ausências em colunas não previstas: %s",
            unexpected_missing_columns,
        )

    return missing_values


def validate_municipality_base(
    file_path: Path = MUNICIPALITY_BASE_PATH,
) -> pd.DataFrame:
    """
    Executa todas as validações da base municipal.

    Parameters
    ----------
    file_path:
        Caminho da base municipal consolidada.

    Returns
    -------
    pandas.DataFrame
        Base validada.
    """
    validate_file_exists(file_path)

    logger.info(
        "Carregando base municipal: %s",
        file_path,
    )

    dataframe = pd.read_parquet(file_path)

    logger.info(
        "Base carregada: %s linhas e %s colunas.",
        dataframe.shape[0],
        dataframe.shape[1],
    )

    validate_expected_columns(dataframe)
    validate_municipality_key(dataframe)
    validate_identification_columns(dataframe)
    validate_numeric_columns(dataframe)
    validate_positive_values(dataframe)
    validate_ranges(dataframe)
    validate_public_network_percentage(dataframe)
    validate_school_flow_consistency(dataframe)

    logger.info(
        "Todas as validações críticas foram aprovadas."
    )

    return dataframe


def main() -> None:
    """
    Executa a validação e imprime o relatório final.
    """
    dataframe = validate_municipality_base()

    missing_values = validate_missing_values(
        dataframe
    )

    print("\n" + "=" * 60)
    print("RELATÓRIO DE VALIDAÇÃO DA BASE MUNICIPAL")
    print("=" * 60)

    print("\nDimensão:")
    print(dataframe.shape)

    print("\nMunicípios únicos:")
    print(dataframe["CO_MUNICIPIO"].nunique())

    print("\nMunicípios duplicados:")
    print(
        dataframe["CO_MUNICIPIO"]
        .duplicated()
        .sum()
    )

    print("\nDistribuição por UF:")
    print(
        dataframe["SG_UF"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\nValores ausentes:")
    print(
        missing_values
        .loc[lambda series: series > 0]
        .to_string()
    )

    print("\nResumo numérico:")
    print(
        dataframe
        .describe()
        .transpose()
        .to_string()
    )

    print("\n" + "=" * 60)
    print("BASE MUNICIPAL APROVADA")
    print("=" * 60)


if __name__ == "__main__":
    main()
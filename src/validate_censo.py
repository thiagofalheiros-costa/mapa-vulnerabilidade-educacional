"""
Validações de qualidade do Censo Escolar.
"""

import pandas as pd

from src.logger import setup_logger
from src.metadata.censo import INFRA_COLUMNS


logger = setup_logger()


def validate_unique_school_code(
    df: pd.DataFrame,
) -> None:
    """
    Verifica se cada código de escola aparece apenas uma vez.
    """
    duplicated_codes = (
        df.loc[
            df["CO_ENTIDADE"].duplicated(keep=False),
            "CO_ENTIDADE",
        ]
        .dropna()
        .unique()
    )

    if len(duplicated_codes) > 0:
        raise ValueError(
            "Foram encontrados códigos de escola duplicados: "
            f"{duplicated_codes[:10].tolist()}"
        )

    logger.info(
        "Validação concluída: CO_ENTIDADE é único."
    )


def validate_binary_columns(
    df: pd.DataFrame,
    columns: list[str] | None = None,
) -> None:
    """
    Verifica se variáveis binárias contêm somente 0, 1 ou nulos.
    """
    columns = columns or INFRA_COLUMNS

    invalid_values = {}

    for column in columns:
        values = set(
            df[column]
            .dropna()
            .unique()
            .tolist()
        )

        invalid = values - {0, 1}

        if invalid:
            invalid_values[column] = sorted(invalid)

    if invalid_values:
        raise ValueError(
            "Foram encontrados valores inválidos em colunas "
            f"binárias: {invalid_values}"
        )

    logger.info(
        "Validação concluída: variáveis binárias contêm "
        "somente 0, 1 ou nulos."
    )


def validate_school_ids(
    df: pd.DataFrame,
) -> None:
    """
    Verifica preenchimento dos identificadores principais.
    """
    required_ids = [
        "CO_ENTIDADE",
        "CO_MUNICIPIO",
        "SG_UF",
        "NO_ENTIDADE",
        "NO_MUNICIPIO",
    ]

    missing = {
        column: int(df[column].isna().sum())
        for column in required_ids
        if df[column].isna().any()
    }

    if missing:
        raise ValueError(
            "Existem identificadores obrigatórios ausentes: "
            f"{missing}"
        )

    logger.info(
        "Validação concluída: identificadores obrigatórios "
        "estão preenchidos."
    )


def validate_enrollment(
    df: pd.DataFrame,
) -> None:
    """
    Verifica se a quantidade de matrículas possui valores negativos.
    """
    negative_count = int(
        (df["QT_MAT_BAS"].dropna() < 0).sum()
    )

    if negative_count > 0:
        raise ValueError(
            "Foram encontrados "
            f"{negative_count} registros com matrícula negativa."
        )

    logger.info(
        "Validação concluída: não há matrículas negativas."
    )


def build_quality_report(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Gera relatório resumido de qualidade por coluna.
    """
    total_rows = len(df)

    records = []

    for column in df.columns:
        missing_count = int(df[column].isna().sum())

        records.append(
            {
                "coluna": column,
                "tipo": str(df[column].dtype),
                "valores_ausentes": missing_count,
                "percentual_ausente": round(
                    missing_count / total_rows * 100,
                    2,
                ) if total_rows else 0.0,
                "valores_unicos": int(
                    df[column].nunique(dropna=True)
                ),
            }
        )

    return (
        pd.DataFrame(records)
        .sort_values(
            ["percentual_ausente", "coluna"],
            ascending=[False, True],
        )
        .reset_index(drop=True)
    )


def validate_censo(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Executa todas as validações do Censo Escolar.
    """
    logger.info(
        "Iniciando validações do Censo Escolar."
    )

    validate_school_ids(df)
    validate_unique_school_code(df)
    validate_binary_columns(df)
    validate_enrollment(df)

    logger.info(
        "Todas as validações do Censo Escolar foram concluídas."
    )

    return build_quality_report(df)
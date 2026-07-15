"""
Pré-processamento do Censo Escolar.
"""

from pathlib import Path

import pandas as pd

from src.load_data import read_data
from src.metadata.selectors import get_censo_columns


DEPENDENCIAS_PUBLICAS = [1, 2, 3]


def load_censo(
    file_path: Path,
    nrows: int | None = None,
) -> pd.DataFrame:
    """
    Carrega somente as colunas utilizadas pelo projeto.
    """
    return read_data(
        file_path=file_path,
        usecols=get_censo_columns(),
        nrows=nrows,
    )


def filter_censo(
    df: pd.DataFrame,
    uf: str = "RS",
    active_school_code: int = 1,
) -> pd.DataFrame:
    """
    Filtra escolas do recorte inicial do projeto.

    Mantém:
    - a UF selecionada;
    - escolas em funcionamento;
    - dependências federal, estadual e municipal.
    """
    filtered_df = df.loc[
        (df["SG_UF"] == uf)
        & (
            df["TP_SITUACAO_FUNCIONAMENTO"]
            == active_school_code
        )
        & (
            df["TP_DEPENDENCIA"]
            .isin(DEPENDENCIAS_PUBLICAS)
        )
    ].copy()

    return filtered_df


def convert_censo_types(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Converte colunas do Censo para tipos mais adequados.
    """
    converted_df = df.copy()

    integer_columns = [
        "NU_ANO_CENSO",
        "CO_MUNICIPIO",
        "CO_ENTIDADE",
        "TP_DEPENDENCIA",
        "TP_LOCALIZACAO",
        "TP_SITUACAO_FUNCIONAMENTO",
        "QT_MAT_BAS",
    ]

    binary_columns = [
        "IN_AGUA_POTAVEL",
        "IN_ENERGIA_REDE_PUBLICA",
        "IN_ESGOTO_REDE_PUBLICA",
        "IN_BIBLIOTECA",
        "IN_LABORATORIO_INFORMATICA",
        "IN_QUADRA_ESPORTES",
        "IN_INTERNET",
        "IN_BANDA_LARGA",
    ]

    for column in integer_columns:
        converted_df[column] = pd.to_numeric(
            converted_df[column],
            errors="coerce",
        ).astype("Int64")

    for column in binary_columns:
        converted_df[column] = pd.to_numeric(
            converted_df[column],
            errors="coerce",
        ).astype("Int8")

    return converted_df


def preprocess_censo(
    file_path: Path,
    uf: str = "RS",
    nrows: int | None = None,
) -> pd.DataFrame:
    """
    Executa o pré-processamento inicial do Censo Escolar.
    """
    df = load_censo(
        file_path=file_path,
        nrows=nrows,
    )

    df = filter_censo(
        df=df,
        uf=uf,
    )

    df = convert_censo_types(df)

    return df
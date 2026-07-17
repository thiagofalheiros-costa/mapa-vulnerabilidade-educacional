"""
Leitura e padronização dos indicadores educacionais do INEP.

Este módulo trata as bases municipais de:

- Taxas de rendimento escolar;
- Indicador de Nível Socioeconômico (INSE);
- Taxa de Distorção Idade-Série (TDI).

As funções retornam bases com uma única linha por município,
considerando o total da localização e da dependência administrativa.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import INSE_PATH, RENDIMENTO_PATH, TDI_PATH
from src.logger import setup_logger


logger = setup_logger()


def validate_file(file_path: Path) -> None:
    """
    Verifica se um arquivo existe.

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


def convert_numeric_columns(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Converte colunas para formato numérico.

    Valores representados por '--' são convertidos para ausentes.

    Parameters
    ----------
    dataframe:
        DataFrame que contém as colunas.

    columns:
        Colunas que serão convertidas.

    Returns
    -------
    pandas.DataFrame
        DataFrame com as colunas convertidas.
    """
    dataframe = dataframe.copy()

    for column in columns:
        if column not in dataframe.columns:
            continue

        dataframe[column] = (
            dataframe[column]
            .replace("--", np.nan)
            .astype(str)
            .str.replace(",", ".", regex=False)
        )

        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    return dataframe


def load_rendimento(
    file_path: Path = RENDIMENTO_PATH,
    uf: str = "RS",
) -> pd.DataFrame:
    """
    Carrega e trata as taxas municipais de rendimento escolar.

    São mantidas apenas as linhas correspondentes ao total da
    localização e ao total da dependência administrativa.

    Parameters
    ----------
    file_path:
        Caminho do arquivo de rendimento escolar.

    uf:
        Sigla da Unidade da Federação utilizada no filtro.

    Returns
    -------
    pandas.DataFrame
        Base municipal com taxas de aprovação, reprovação
        e abandono no Ensino Fundamental e no Ensino Médio.
    """
    validate_file(file_path)

    logger.info(
        "Carregando taxas de rendimento: %s",
        file_path.name,
    )

    dataframe = pd.read_excel(
        file_path,
        sheet_name="MUNICIPIOS ",
        header=8,
    )

    dataframe = dataframe.loc[
        (dataframe["SG_UF"] == uf)
        & (dataframe["NO_CATEGORIA"] == "Total")
        & (dataframe["NO_DEPENDENCIA"] == "Total")
    ].copy()

    selected_columns = {
        "CO_MUNICIPIO": "CO_MUNICIPIO",
        "NO_MUNICIPIO": "NO_MUNICIPIO",
        "SG_UF": "SG_UF",
        "1_CAT_FUN": "APROVACAO_EF",
        "1_CAT_MED": "APROVACAO_EM",
        "2_CAT_FUN": "REPROVACAO_EF",
        "2_CAT_MED": "REPROVACAO_EM",
        "3_CAT_FUN": "ABANDONO_EF",
        "3_CAT_MED": "ABANDONO_EM",
    }

    dataframe = dataframe[
        list(selected_columns)
    ].rename(columns=selected_columns)

    numeric_columns = [
        "APROVACAO_EF",
        "APROVACAO_EM",
        "REPROVACAO_EF",
        "REPROVACAO_EM",
        "ABANDONO_EF",
        "ABANDONO_EM",
    ]

    dataframe = convert_numeric_columns(
        dataframe=dataframe,
        columns=numeric_columns,
    )

    dataframe["CO_MUNICIPIO"] = (
        pd.to_numeric(
            dataframe["CO_MUNICIPIO"],
            errors="raise",
        )
        .astype("int64")
    )

    dataframe = (
        dataframe
        .drop_duplicates(subset=["CO_MUNICIPIO"])
        .sort_values("CO_MUNICIPIO")
        .reset_index(drop=True)
    )

    logger.info(
        "Rendimento carregado: %s municípios.",
        len(dataframe),
    )

    return dataframe


def load_inse(
    file_path: Path = INSE_PATH,
    uf: str = "RS",
) -> pd.DataFrame:
    """
    Carrega e trata o INSE municipal.

    Para obter uma única observação por município, são mantidas
    as linhas com total das redes e total das localizações:

    - TP_TIPO_REDE igual a 6;
    - TP_LOCALIZACAO igual a 0.

    Parameters
    ----------
    file_path:
        Caminho do arquivo de INSE.

    uf:
        Sigla da Unidade da Federação utilizada no filtro.

    Returns
    -------
    pandas.DataFrame
        Base municipal com média do INSE e quantidade de alunos.
    """
    validate_file(file_path)

    logger.info(
        "Carregando INSE: %s",
        file_path.name,
    )

    dataframe = pd.read_excel(
        file_path,
        sheet_name="INSE_MUN_2023",
    )

    dataframe = dataframe.loc[
        (dataframe["SG_UF"] == uf)
        & (dataframe["TP_TIPO_REDE"] == 6)
        & (dataframe["TP_LOCALIZACAO"] == 0)
    ].copy()

    selected_columns = {
        "CO_MUNICIPIO": "CO_MUNICIPIO",
        "NO_MUNICIPIO": "NO_MUNICIPIO",
        "SG_UF": "SG_UF",
        "QTD_ALUNOS_INSE": "QTD_ALUNOS_INSE",
        "MEDIA_INSE": "MEDIA_INSE",
    }

    dataframe = dataframe[
        list(selected_columns)
    ].rename(columns=selected_columns)

    dataframe = convert_numeric_columns(
        dataframe=dataframe,
        columns=[
            "QTD_ALUNOS_INSE",
            "MEDIA_INSE",
        ],
    )

    dataframe["CO_MUNICIPIO"] = (
        pd.to_numeric(
            dataframe["CO_MUNICIPIO"],
            errors="raise",
        )
        .astype("int64")
    )

    dataframe = (
        dataframe
        .drop_duplicates(subset=["CO_MUNICIPIO"])
        .sort_values("CO_MUNICIPIO")
        .reset_index(drop=True)
    )

    logger.info(
        "INSE carregado: %s municípios.",
        len(dataframe),
    )

    return dataframe


def load_tdi(
    file_path: Path = TDI_PATH,
    uf: str = "RS",
) -> pd.DataFrame:
    """
    Carrega e trata a taxa municipal de distorção idade-série.

    São mantidas apenas as linhas correspondentes ao total da
    localização e ao total da dependência administrativa.

    Parameters
    ----------
    file_path:
        Caminho do arquivo de distorção idade-série.

    uf:
        Sigla da Unidade da Federação utilizada no filtro.

    Returns
    -------
    pandas.DataFrame
        Base municipal com taxas de distorção do Ensino
        Fundamental e do Ensino Médio.
    """
    validate_file(file_path)

    logger.info(
        "Carregando taxa de distorção: %s",
        file_path.name,
    )

    dataframe = pd.read_excel(
        file_path,
        sheet_name="MUNICIPIO",
        header=8,
    )

    dataframe = dataframe.loc[
        (dataframe["SG_UF"] == uf)
        & (dataframe["NO_CATEGORIA"] == "Total")
        & (dataframe["NO_DEPENDENCIA"] == "Total")
    ].copy()

    selected_columns = {
        "CO_MUNICIPIO": "CO_MUNICIPIO",
        "NO_MUNICIPIO": "NO_MUNICIPIO",
        "SG_UF": "SG_UF",
        "FUN_CAT_0": "DISTORCAO_EF",
        "MED_CAT_0": "DISTORCAO_EM",
    }

    dataframe = dataframe[
        list(selected_columns)
    ].rename(columns=selected_columns)

    dataframe = convert_numeric_columns(
        dataframe=dataframe,
        columns=[
            "DISTORCAO_EF",
            "DISTORCAO_EM",
        ],
    )

    dataframe["CO_MUNICIPIO"] = (
        pd.to_numeric(
            dataframe["CO_MUNICIPIO"],
            errors="raise",
        )
        .astype("int64")
    )

    dataframe = (
        dataframe
        .drop_duplicates(subset=["CO_MUNICIPIO"])
        .sort_values("CO_MUNICIPIO")
        .reset_index(drop=True)
    )

    logger.info(
        "Distorção carregada: %s municípios.",
        len(dataframe),
    )

    return dataframe
from pathlib import Path
from typing import Dict

import pandas as pd

from src.config import RAW_DIR
from src.utils import limpar_colunas, logger


# ============================================================
# 1. Função genérica para carregar arquivos CSV
# ============================================================

def carregar_csv(
    caminho: Path,
    sep: str = ";",
    encoding: str = "latin1"
) -> pd.DataFrame:
    """
    Carrega um arquivo CSV e padroniza os nomes das colunas.

    Parâmetros
    ----------
    caminho:
        Caminho completo do arquivo.

    sep:
        Separador utilizado no arquivo.

    encoding:
        Codificação de caracteres do arquivo.

    Retorno
    -------
    pd.DataFrame
        DataFrame carregado e com colunas padronizadas.
    """

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}"
        )

    logger.info(
        "Iniciando leitura do arquivo: %s",
        caminho.name
    )

    try:
        df = pd.read_csv(
            caminho,
            sep=sep,
            encoding=encoding,
            low_memory=False
        )

    except UnicodeDecodeError:
        logger.warning(
            "Falha com encoding %s. Tentando UTF-8.",
            encoding
        )

        df = pd.read_csv(
            caminho,
            sep=sep,
            encoding="utf-8",
            low_memory=False
        )

    df = limpar_colunas(df)

    logger.info(
        "Arquivo %s carregado: %s linhas e %s colunas",
        caminho.name,
        df.shape[0],
        df.shape[1]
    )

    return df


# ============================================================
# 2. Função para carregar todas as bases do projeto
# ============================================================

def carregar_bases() -> Dict[str, pd.DataFrame]:
    """
    Carrega as bases iniciais do projeto.

    Retorna um dicionário no formato:

    {
        "censo": DataFrame,
        "rendimento": DataFrame,
        "distorcao": DataFrame,
        "inse": DataFrame
    }
    """

    arquivos = {
        "censo": {
            "caminho": RAW_DIR / "censo_escolar.csv",
            "sep": ";",
            "encoding": "latin1"
        },
        "rendimento": {
            "caminho": RAW_DIR / "indicadores_rendimento.csv",
            "sep": ";",
            "encoding": "latin1"
        },
        "distorcao": {
            "caminho": RAW_DIR / "distorcao_idade_serie.csv",
            "sep": ";",
            "encoding": "latin1"
        },
        "inse": {
            "caminho": RAW_DIR / "inse.csv",
            "sep": ";",
            "encoding": "latin1"
        }
    }

    bases = {}

    for nome_base, configuracao in arquivos.items():

        logger.info(
            "Carregando base: %s",
            nome_base
        )

        bases[nome_base] = carregar_csv(
            caminho=configuracao["caminho"],
            sep=configuracao["sep"],
            encoding=configuracao["encoding"]
        )

    return bases
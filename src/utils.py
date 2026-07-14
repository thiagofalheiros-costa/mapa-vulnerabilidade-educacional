import logging
import re
import unicodedata

import pandas as pd


# ============================================================
# 1. Configuração do sistema de logs
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


# ============================================================
# 2. Função para limpar nomes de colunas
# ============================================================

def limpar_nome_coluna(nome: str) -> str:
    """
    Padroniza o nome de uma coluna.

    Exemplo:
        "Taxa de Aprovação (%)"
        torna-se
        "taxa_de_aprovacao"
    """

    nome = nome.strip().lower()

    nome = unicodedata.normalize(
        "NFKD",
        nome
    )

    nome = nome.encode(
        "ascii",
        errors="ignore"
    ).decode("utf-8")

    nome = re.sub(
        r"[^a-z0-9]+",
        "_",
        nome
    )

    nome = nome.strip("_")

    return nome


def limpar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna uma cópia do DataFrame com os nomes
    das colunas padronizados.
    """

    df = df.copy()

    df.columns = [
        limpar_nome_coluna(coluna)
        for coluna in df.columns
    ]

    return df
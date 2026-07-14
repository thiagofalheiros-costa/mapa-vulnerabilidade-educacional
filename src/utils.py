"""
Funções utilitárias do projeto.
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd


def create_directory(path: Path) -> None:
    """
    Cria uma pasta e seus diretórios superiores caso não existam.
    """
    path.mkdir(
        parents=True,
        exist_ok=True,
    )


def list_files(
    path: Path,
    recursive: bool = False,
) -> list[Path]:
    """
    Lista os arquivos existentes em uma pasta.

    Parameters
    ----------
    path:
        Pasta que será inspecionada.

    recursive:
        Se verdadeiro, procura também nas subpastas.

    Returns
    -------
    list[Path]
        Lista ordenada de caminhos.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"A pasta informada não existe: {path}"
        )

    pattern = "**/*" if recursive else "*"

    return sorted(
        file
        for file in path.glob(pattern)
        if file.is_file()
    )


def normalize_column_name(column: object) -> str:
    """
    Padroniza o nome de uma coluna.

    Exemplo
    -------
    'Código do Município' se torna 'CODIGO_DO_MUNICIPIO'.
    """
    column = str(column).strip()

    column = unicodedata.normalize(
        "NFKD",
        column,
    )

    column = "".join(
        character
        for character in column
        if not unicodedata.combining(character)
    )

    column = column.upper()

    column = re.sub(
        r"[^A-Z0-9]+",
        "_",
        column,
    )

    column = re.sub(
        r"_+",
        "_",
        column,
    )

    return column.strip("_")


def normalize_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Padroniza os nomes de todas as colunas do DataFrame.

    O DataFrame original não é alterado.
    """
    normalized_df = df.copy()

    normalized_df.columns = [
        normalize_column_name(column)
        for column in normalized_df.columns
    ]

    return normalized_df

def validate_required_columns(
    df: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str = "base",
) -> None:
    """
    Verifica se o DataFrame possui todas as colunas obrigatórias.

    Parameters
    ----------
    df:
        DataFrame que será validado.

    required_columns:
        Nomes das colunas esperadas.

    dataset_name:
        Nome usado na mensagem de erro.

    Raises
    ------
    ValueError
        Quando uma ou mais colunas obrigatórias não existem.
    """
    normalized_required_columns = {
        normalize_column_name(column)
        for column in required_columns
    }

    available_columns = set(df.columns)

    missing_columns = (
        normalized_required_columns
        - available_columns
    )

    if missing_columns:
        raise ValueError(
            f"A base '{dataset_name}' não possui as colunas "
            f"obrigatórias: {sorted(missing_columns)}"
        )
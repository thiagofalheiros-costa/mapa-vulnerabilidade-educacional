"""
Funções responsáveis pela leitura dos arquivos do projeto.

Projeto: Mapa de Vulnerabilidade Educacional
Autor: Thiago Falheiros
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from src.logger import setup_logger
from src.utils import normalize_columns


logger = setup_logger()


# Extensões aceitas pelo pipeline
SUPPORTED_EXTENSIONS = {
    ".csv",
    ".txt",
    ".xlsx",
    ".xls",
    ".parquet",
    ".feather",
}


def validate_file(file_path: Path) -> None:
    """
    Valida se o arquivo existe e se sua extensão é suportada.

    Parameters
    ----------
    file_path:
        Caminho do arquivo que será validado.

    Raises
    ------
    FileNotFoundError
        Quando o arquivo não existe.

    ValueError
        Quando o formato do arquivo não é suportado.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"O caminho informado não corresponde a um arquivo: {file_path}"
        )

    extension = file_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Formato não suportado: {extension}. "
            f"Formatos aceitos: {sorted(SUPPORTED_EXTENSIONS)}"
        )


def detect_csv_separator(
    file_path: Path,
    encoding: str,
) -> str:
    """
    Detecta se o separador principal de um arquivo é vírgula,
    ponto e vírgula, tabulação ou barra vertical.

    Parameters
    ----------
    file_path:
        Caminho do arquivo.

    encoding:
        Codificação usada para abrir o arquivo.

    Returns
    -------
    str
        Separador identificado.
    """
    separators = [";", ",", "\t", "|"]

    with file_path.open(
        mode="r",
        encoding=encoding,
        errors="replace",
    ) as file:
        first_line = file.readline()

    occurrences = {
        separator: first_line.count(separator)
        for separator in separators
    }

    detected_separator = max(
        occurrences,
        key=occurrences.get,
    )

    if occurrences[detected_separator] == 0:
        logger.warning(
            "Nenhum separador comum foi identificado em %s. "
            "Será utilizado ponto e vírgula.",
            file_path.name,
        )
        return ";"

    logger.info(
        "Separador detectado em %s: %r",
        file_path.name,
        detected_separator,
    )

    return detected_separator


def detect_encoding(file_path: Path) -> str:
    """
    Testa codificações comuns em arquivos públicos brasileiros.

    Parameters
    ----------
    file_path:
        Caminho do arquivo.

    Returns
    -------
    str
        Primeira codificação compatível encontrada.

    Raises
    ------
    UnicodeError
        Quando nenhuma codificação testada permite abrir o arquivo.
    """
    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp1252",
        "latin1",
    ]

    for encoding in encodings:
        try:
            with file_path.open(
                mode="r",
                encoding=encoding,
            ) as file:
                file.read(100_000)

            logger.info(
                "Encoding detectado em %s: %s",
                file_path.name,
                encoding,
            )

            return encoding

        except UnicodeDecodeError:
            continue

    raise UnicodeError(
        f"Não foi possível identificar a codificação de {file_path}."
    )


def read_csv_file(
    file_path: Path,
    usecols: Optional[list[str]] = None,
    nrows: Optional[int] = None,
    low_memory: bool = False,
) -> pd.DataFrame:
    """
    Carrega arquivos CSV ou TXT detectando codificação e separador.

    Parameters
    ----------
    file_path:
        Caminho do arquivo.

    usecols:
        Lista opcional de colunas que deverão ser carregadas.

    nrows:
        Número opcional de linhas a serem lidas.

    low_memory:
        Controla o processamento interno de tipos do pandas.

    Returns
    -------
    pandas.DataFrame
        Dados carregados.
    """
    encoding = detect_encoding(file_path)

    separator = detect_csv_separator(
        file_path=file_path,
        encoding=encoding,
    )

    logger.info(
        "Iniciando leitura do arquivo: %s",
        file_path.name,
    )

    df = pd.read_csv(
        file_path,
        sep=separator,
        encoding=encoding,
        usecols=usecols,
        nrows=nrows,
        low_memory=low_memory,
    )

    return df


def read_excel_file(
    file_path: Path,
    sheet_name: str | int = 0,
    usecols: Optional[list[str]] = None,
    nrows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Carrega arquivos Excel.

    Parameters
    ----------
    file_path:
        Caminho do arquivo.

    sheet_name:
        Nome ou posição da planilha.

    usecols:
        Lista opcional de colunas.

    nrows:
        Número opcional de linhas.

    Returns
    -------
    pandas.DataFrame
        Dados carregados.
    """
    logger.info(
        "Iniciando leitura da planilha: %s",
        file_path.name,
    )

    return pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        usecols=usecols,
        nrows=nrows,
    )


def read_data(
    file_path: str | Path,
    usecols: Optional[list[str]] = None,
    nrows: Optional[int] = None,
    sheet_name: str | int = 0,
    normalize: bool = True,
) -> pd.DataFrame:
    """
    Carrega um arquivo de acordo com sua extensão.

    Formatos suportados:
    - CSV;
    - TXT;
    - XLSX;
    - XLS;
    - Parquet;
    - Feather.

    Parameters
    ----------
    file_path:
        Caminho do arquivo.

    usecols:
        Lista opcional de colunas que deverão ser carregadas.

    nrows:
        Número opcional de linhas.

    sheet_name:
        Planilha que será lida em arquivos Excel.

    normalize:
        Indica se os nomes das colunas devem ser padronizados.

    Returns
    -------
    pandas.DataFrame
        DataFrame carregado.

    Raises
    ------
    ValueError
        Quando o tipo de arquivo não é suportado.
    """
    path = Path(file_path)

    validate_file(path)

    extension = path.suffix.lower()

    if extension in {".csv", ".txt"}:
        df = read_csv_file(
            file_path=path,
            usecols=usecols,
            nrows=nrows,
        )

    elif extension in {".xlsx", ".xls"}:
        df = read_excel_file(
            file_path=path,
            sheet_name=sheet_name,
            usecols=usecols,
            nrows=nrows,
        )

    elif extension == ".parquet":
        logger.info(
            "Iniciando leitura do arquivo Parquet: %s",
            path.name,
        )

        df = pd.read_parquet(
            path,
            columns=usecols,
        )

        if nrows is not None:
            df = df.head(nrows)

    elif extension == ".feather":
        logger.info(
            "Iniciando leitura do arquivo Feather: %s",
            path.name,
        )

        df = pd.read_feather(
            path,
            columns=usecols,
        )

        if nrows is not None:
            df = df.head(nrows)

    else:
        raise ValueError(
            f"Não existe leitor configurado para: {extension}"
        )

    if normalize:
        df = normalize_columns(df)

    logger.info(
        "Arquivo carregado com sucesso: %s linhas e %s colunas.",
        len(df),
        len(df.columns),
    )

    return df
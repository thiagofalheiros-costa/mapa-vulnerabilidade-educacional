"""
Inspeção inicial das bases de dados.

Este módulo localiza arquivos de dados, carrega uma amostra e gera
relatórios com nomes das colunas, tipos, valores ausentes, cardinalidade
e consumo de memória.

Projeto: Mapa de Vulnerabilidade Educacional
Autor: Thiago Falheiros
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from src.load_data import read_data
from src.logger import setup_logger
from src.utils import create_directory, list_files


logger = setup_logger()


DATA_EXTENSIONS = {
    ".csv",
    ".txt",
    ".xlsx",
    ".xls",
    ".parquet",
    ".feather",
}


def find_data_files(directory: Path) -> list[Path]:
    """
    Localiza recursivamente arquivos de dados em uma pasta.

    Parameters
    ----------
    directory:
        Diretório que será pesquisado.

    Returns
    -------
    list[Path]
        Arquivos de dados encontrados, ordenados por tamanho decrescente.
    """
    files = list_files(
        path=directory,
        recursive=True,
    )

    data_files = [
        file
        for file in files
        if file.suffix.lower() in DATA_EXTENSIONS
        and not file.name.startswith("~$")
    ]

    data_files = sorted(
        data_files,
        key=lambda file: file.stat().st_size,
        reverse=True,
    )

    logger.info(
        "%s arquivo(s) de dados encontrado(s) em %s.",
        len(data_files),
        directory,
    )

    return data_files


def create_file_inventory(
    files: list[Path],
    base_directory: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Cria um inventário dos arquivos encontrados.

    Parameters
    ----------
    files:
        Lista dos arquivos que serão inventariados.

    base_directory:
        Diretório usado para gerar caminhos relativos.

    Returns
    -------
    pandas.DataFrame
        Inventário dos arquivos.
    """
    records = []

    for file in files:
        if base_directory is not None:
            try:
                displayed_path = file.relative_to(base_directory)
            except ValueError:
                displayed_path = file
        else:
            displayed_path = file

        records.append(
            {
                "arquivo": file.name,
                "extensao": file.suffix.lower(),
                "caminho": str(displayed_path),
                "tamanho_mb": round(
                    file.stat().st_size / (1024**2),
                    2,
                ),
            }
        )

    return pd.DataFrame(records)


def select_main_data_file(
    files: list[Path],
    filename_terms: Optional[list[str]] = None,
) -> Path:
    """
    Seleciona o arquivo principal mais provável.

    A função prioriza arquivos cujos nomes contenham termos informados.
    Quando nenhum termo é encontrado, seleciona o maior arquivo.

    Parameters
    ----------
    files:
        Arquivos candidatos.

    filename_terms:
        Termos usados para priorizar o arquivo principal.

    Returns
    -------
    pathlib.Path
        Caminho do arquivo selecionado.

    Raises
    ------
    FileNotFoundError
        Quando nenhum arquivo de dados é encontrado.
    """
    if not files:
        raise FileNotFoundError(
            "Nenhum arquivo de dados foi encontrado."
        )

    terms = filename_terms or [
        "microdados",
        "educacao_basica",
        "ed_basica",
        "censo_escolar",
        "escola",
    ]

    normalized_terms = [
        term.lower()
        for term in terms
    ]

    matching_files = [
        file
        for file in files
        if any(
            term in file.name.lower()
            for term in normalized_terms
        )
    ]

    candidates = matching_files or files

    selected_file = max(
        candidates,
        key=lambda file: file.stat().st_size,
    )

    logger.info(
        "Arquivo principal selecionado: %s",
        selected_file,
    )

    return selected_file


def build_column_profile(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produz um perfil das colunas de um DataFrame.

    O relatório contém tipo, quantidade de valores preenchidos,
    valores ausentes, percentual de ausência, cardinalidade,
    exemplo de valor e uso de memória.

    Parameters
    ----------
    df:
        DataFrame que será analisado.

    Returns
    -------
    pandas.DataFrame
        Perfil técnico das colunas.
    """
    total_rows = len(df)

    records = []

    for column in df.columns:
        series = df[column]

        missing_count = int(series.isna().sum())
        non_missing_count = int(series.notna().sum())

        if total_rows == 0:
            missing_percentage = 0.0
        else:
            missing_percentage = round(
                missing_count / total_rows * 100,
                2,
            )

        non_null_values = series.dropna()

        example_value = (
            str(non_null_values.iloc[0])
            if not non_null_values.empty
            else None
        )

        records.append(
            {
                "coluna": column,
                "tipo_amostra": str(series.dtype),
                "linhas_preenchidas": non_missing_count,
                "valores_ausentes": missing_count,
                "percentual_ausente": missing_percentage,
                "valores_unicos_amostra": int(
                    series.nunique(dropna=True)
                ),
                "exemplo_valor": example_value,
                "memoria_kb": round(
                    series.memory_usage(deep=True) / 1024,
                    2,
                ),
            }
        )

    profile = pd.DataFrame(records)

    return profile.sort_values(
        by=[
            "percentual_ausente",
            "coluna",
        ],
        ascending=[
            False,
            True,
        ],
    ).reset_index(drop=True)


def build_dataset_summary(
    df: pd.DataFrame,
    file_path: Path,
    sample_size: int,
) -> pd.DataFrame:
    """
    Cria um resumo geral da base inspecionada.

    Parameters
    ----------
    df:
        Amostra carregada.

    file_path:
        Arquivo de origem.

    sample_size:
        Quantidade máxima de linhas solicitadas.

    Returns
    -------
    pandas.DataFrame
        Resumo geral da inspeção.
    """
    duplicated_rows = int(
        df.duplicated().sum()
    )

    total_cells = df.shape[0] * df.shape[1]

    missing_cells = int(
        df.isna().sum().sum()
    )

    if total_cells == 0:
        missing_percentage = 0.0
    else:
        missing_percentage = round(
            missing_cells / total_cells * 100,
            2,
        )

    summary = {
        "arquivo": file_path.name,
        "caminho": str(file_path),
        "extensao": file_path.suffix.lower(),
        "tamanho_arquivo_mb": round(
            file_path.stat().st_size / (1024**2),
            2,
        ),
        "linhas_solicitadas": sample_size,
        "linhas_carregadas": df.shape[0],
        "quantidade_colunas": df.shape[1],
        "celulas_ausentes_amostra": missing_cells,
        "percentual_ausente_amostra": missing_percentage,
        "linhas_duplicadas_amostra": duplicated_rows,
        "memoria_dataframe_mb": round(
            df.memory_usage(deep=True).sum() / (1024**2),
            2,
        ),
    }

    return pd.DataFrame([summary])


def inspect_data_file(
    file_path: Path,
    output_directory: Path,
    sample_size: int = 5_000,
    report_prefix: str = "inspecao_dados",
    sheet_name: str | int = 0,
) -> dict[str, pd.DataFrame]:
    """
    Inspeciona um arquivo e exporta relatórios técnicos.

    Parameters
    ----------
    file_path:
        Arquivo que será inspecionado.

    output_directory:
        Pasta onde os relatórios serão salvos.

    sample_size:
        Quantidade máxima de linhas da amostra.

    report_prefix:
        Prefixo dos arquivos gerados.

    sheet_name:
        Nome ou posição da aba, caso o arquivo seja Excel.

    Returns
    -------
    dict[str, pandas.DataFrame]
        Resumo, perfil das colunas e amostra.
    """
    create_directory(output_directory)

    logger.info(
        "Iniciando inspeção de %s.",
        file_path.name,
    )

    df = read_data(
        file_path=file_path,
        nrows=sample_size,
        sheet_name=sheet_name,
        normalize=True,
    )

    summary = build_dataset_summary(
        df=df,
        file_path=file_path,
        sample_size=sample_size,
    )

    column_profile = build_column_profile(df)

    sample = df.head(20).copy()

    summary_path = (
        output_directory
        / f"{report_prefix}_resumo.csv"
    )

    columns_path = (
        output_directory
        / f"{report_prefix}_colunas.csv"
    )

    sample_path = (
        output_directory
        / f"{report_prefix}_amostra.csv"
    )

    summary.to_csv(
        summary_path,
        index=False,
        encoding="utf-8-sig",
    )

    column_profile.to_csv(
        columns_path,
        index=False,
        encoding="utf-8-sig",
    )

    sample.to_csv(
        sample_path,
        index=False,
        encoding="utf-8-sig",
    )

    logger.info(
        "Resumo salvo em: %s",
        summary_path,
    )

    logger.info(
        "Perfil das colunas salvo em: %s",
        columns_path,
    )

    logger.info(
        "Amostra salva em: %s",
        sample_path,
    )

    return {
        "resumo": summary,
        "colunas": column_profile,
        "amostra": sample,
    }


def inspect_directory(
    input_directory: Path,
    output_directory: Path,
    sample_size: int = 5_000,
    report_prefix: str = "inspecao_dados",
    filename_terms: Optional[list[str]] = None,
) -> dict[str, pd.DataFrame]:
    """
    Localiza e inspeciona o principal arquivo de uma pasta.

    Parameters
    ----------
    input_directory:
        Pasta que contém os arquivos brutos.

    output_directory:
        Pasta de saída dos relatórios.

    sample_size:
        Quantidade máxima de linhas carregadas.

    report_prefix:
        Prefixo dos relatórios.

    filename_terms:
        Termos usados para selecionar o arquivo principal.

    Returns
    -------
    dict[str, pandas.DataFrame]
        Inventário e relatórios da inspeção.
    """
    create_directory(output_directory)

    files = find_data_files(input_directory)

    inventory = create_file_inventory(
        files=files,
        base_directory=input_directory,
    )

    inventory_path = (
        output_directory
        / f"{report_prefix}_inventario.csv"
    )

    inventory.to_csv(
        inventory_path,
        index=False,
        encoding="utf-8-sig",
    )

    logger.info(
        "Inventário salvo em: %s",
        inventory_path,
    )

    main_file = select_main_data_file(
        files=files,
        filename_terms=filename_terms,
    )

    inspection = inspect_data_file(
        file_path=main_file,
        output_directory=output_directory,
        sample_size=sample_size,
        report_prefix=report_prefix,
    )

    inspection["inventario"] = inventory

    return inspection
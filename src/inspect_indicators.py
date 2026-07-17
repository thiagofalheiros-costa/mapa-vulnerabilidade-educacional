"""
Inspeção inicial dos arquivos de indicadores educacionais do INEP.

Este módulo identifica as abas existentes e exibe as primeiras
linhas de cada planilha sem assumir previamente onde está o cabeçalho.
"""

from pathlib import Path

import pandas as pd

from src.config import INSE_PATH, RENDIMENTO_PATH, TDI_PATH
from src.logger import setup_logger


logger = setup_logger()


def inspect_excel_file(
    file_path: Path,
    sample_rows: int = 15,
) -> None:
    """
    Inspeciona as abas e as primeiras linhas de um arquivo Excel.

    A planilha é lida inicialmente sem cabeçalho para que seja
    possível identificar em qual linha começam os nomes reais
    das colunas.

    Parameters
    ----------
    file_path:
        Caminho completo do arquivo Excel.

    sample_rows:
        Quantidade de linhas exibidas por aba.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {file_path}"
        )

    logger.info("Inspecionando arquivo: %s", file_path.name)

    excel_file = pd.ExcelFile(file_path)

    print("\n" + "=" * 100)
    print(f"ARQUIVO: {file_path.name}")
    print(f"CAMINHO: {file_path}")
    print(f"ABAS: {excel_file.sheet_names}")
    print("=" * 100)

    for sheet_name in excel_file.sheet_names:
        print(f"\nABA: {sheet_name}")
        print("-" * 100)

        sample = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=None,
            nrows=sample_rows,
        )

        print(
            sample.to_string(
                index=True,
                header=False,
            )
        )


def main() -> None:
    """
    Inspeciona os arquivos de rendimento, INSE e distorção.
    """
    indicator_files = [
        RENDIMENTO_PATH,
        INSE_PATH,
        TDI_PATH,
    ]

    for file_path in indicator_files:
        try:
            inspect_excel_file(file_path)
        except FileNotFoundError as error:
            logger.error("%s", error)
        except Exception:
            logger.exception(
                "Erro ao inspecionar o arquivo %s.",
                file_path,
            )


if __name__ == "__main__":
    main()
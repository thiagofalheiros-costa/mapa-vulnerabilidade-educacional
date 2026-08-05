"""
Pré-processamento do Censo Escolar.

Este módulo:

- carrega somente as colunas utilizadas pelo projeto;
- mantém escolas públicas ativas do Rio Grande do Sul;
- restringe a base às escolas com matrículas no Ensino Médio propedêutico;
- converte os tipos das variáveis;
- salva a base processada em formato Parquet.

Execução
--------
Na raiz do projeto:

python -m src.preprocess_censo

Caso exista mais de um arquivo no diretório do Censo:

python -m src.preprocess_censo --input "caminho/do/microdado.csv"
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from src.censo_selectors import get_censo_columns
from src.config import CENSO_DIR, CENSO_PROCESSED_PATH
from src.load_data import read_data
from src.metadata.common import (
    CODIGO_ESCOLA_ATIVA,
    DEPENDENCIAS_PUBLICAS,
)


logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".csv",
    ".txt",
    ".parquet",
    ".xlsx",
    ".xls",
}

PREFERRED_FILENAME_TERMS = (
    "microdados_ed_basica_2024",
    "microdados",
    "censo_escolar",
)


def configure_logging() -> None:
    """
    Configura os logs exibidos durante a execução.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def find_censo_file(
    input_directory: Path,
) -> Path:
    """
    Localiza automaticamente o arquivo original do Censo Escolar.

    Parameters
    ----------
    input_directory
        Diretório que contém os microdados.

    Returns
    -------
    Path
        Caminho do arquivo identificado.

    Raises
    ------
    FileNotFoundError
        Quando o diretório ou os arquivos não são encontrados.
    ValueError
        Quando mais de um arquivo candidato é identificado.
    """
    if not input_directory.exists():
        raise FileNotFoundError(
            "O diretório dos microdados do Censo não foi encontrado: "
            f"{input_directory}"
        )

    candidates = [
        path
        for path in input_directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not candidates:
        raise FileNotFoundError(
            "Nenhum arquivo compatível foi encontrado em: "
            f"{input_directory}"
        )

    preferred_candidates = [
        path
        for path in candidates
        if any(
            term in path.stem.lower()
            for term in PREFERRED_FILENAME_TERMS
        )
    ]

    selected_candidates = (
        preferred_candidates
        if preferred_candidates
        else candidates
    )

    if len(selected_candidates) > 1:
        candidate_list = "\n".join(
            f"- {path}"
            for path in sorted(selected_candidates)
        )

        raise ValueError(
            "Mais de um arquivo candidato foi encontrado. "
            "Informe o arquivo correto com --input:\n"
            f"{candidate_list}"
        )

    return selected_candidates[0]


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
    active_school_code: int = CODIGO_ESCOLA_ATIVA,
) -> pd.DataFrame:
    """
    Filtra o Censo Escolar para o recorte do projeto.

    Mantém:

    - escolas do Rio Grande do Sul;
    - escolas em atividade;
    - escolas das redes públicas;
    - escolas com matrículas no Ensino Médio propedêutico.
    """
    required_columns = {
        "SG_UF",
        "TP_SITUACAO_FUNCIONAMENTO",
        "TP_DEPENDENCIA",
        "QT_MAT_MED_PROP",
    }

    missing_columns = required_columns.difference(
        df.columns
    )

    if missing_columns:
        raise ValueError(
            "A base do Censo não possui as colunas necessárias "
            "para o filtro: "
            + ", ".join(sorted(missing_columns))
        )

    high_school_enrollment = pd.to_numeric(
        df["QT_MAT_MED_PROP"],
        errors="coerce",
    ).fillna(0)

    filtered_df = df.loc[
        df["SG_UF"].eq(uf)
        & df[
            "TP_SITUACAO_FUNCIONAMENTO"
        ].eq(active_school_code)
        & df["TP_DEPENDENCIA"].isin(
            DEPENDENCIAS_PUBLICAS
        )
        & high_school_enrollment.gt(0)
    ].copy()

    return filtered_df


def convert_censo_types(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Converte colunas do Censo para tipos adequados.
    """
    converted_df = df.copy()

    integer_columns = [
        "NU_ANO_CENSO",
        "CO_MUNICIPIO",
        "CO_ENTIDADE",
        "TP_DEPENDENCIA",
        "TP_LOCALIZACAO",
        "TP_SITUACAO_FUNCIONAMENTO",
        "QT_MAT_MED_PROP",
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
        if column not in converted_df.columns:
            continue

        converted_df[column] = pd.to_numeric(
            converted_df[column],
            errors="coerce",
        ).astype("Int64")

    for column in binary_columns:
        if column not in converted_df.columns:
            continue

        converted_df[column] = pd.to_numeric(
            converted_df[column],
            errors="coerce",
        ).astype("Int8")

    return converted_df


def validate_censo(
    df: pd.DataFrame,
) -> None:
    """
    Valida a base após o pré-processamento.
    """
    required_columns = {
        "CO_ENTIDADE",
        "CO_MUNICIPIO",
        "TP_DEPENDENCIA",
        "QT_MAT_MED_PROP",
    }

    missing_columns = required_columns.difference(
        df.columns
    )

    if missing_columns:
        raise ValueError(
            "A base processada não possui as colunas obrigatórias: "
            + ", ".join(sorted(missing_columns))
        )

    if df.empty:
        raise ValueError(
            "Nenhuma escola permaneceu após os filtros."
        )

    invalid_enrollment = pd.to_numeric(
        df["QT_MAT_MED_PROP"],
        errors="coerce",
    ).fillna(0).le(0)

    if invalid_enrollment.any():
        raise ValueError(
            "A base processada contém escolas sem matrícula "
            "no Ensino Médio propedêutico."
        )

    duplicated_schools = df[
        "CO_ENTIDADE"
    ].duplicated()

    if duplicated_schools.any():
        raise ValueError(
            "A base processada contém "
            f"{int(duplicated_schools.sum())} escolas duplicadas."
        )


def preprocess_censo(
    file_path: Path,
    uf: str = "RS",
    nrows: int | None = None,
) -> pd.DataFrame:
    """
    Executa o pré-processamento completo do Censo Escolar.
    """
    df = load_censo(
        file_path=file_path,
        nrows=nrows,
    )

    df = filter_censo(
        df=df,
        uf=uf,
    )

    df = convert_censo_types(
        df
    )

    validate_censo(
        df
    )

    return df


def build_dependency_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Resume escolas, municípios e matrículas por rede.
    """
    dependency_labels = {
        1: "Federal",
        2: "Estadual",
        3: "Municipal",
        4: "Privada",
    }

    return (
        df.assign(
            REDE_ENSINO=(
                df["TP_DEPENDENCIA"]
                .map(dependency_labels)
                .fillna("Não identificada")
            )
        )
        .groupby(
            [
                "TP_DEPENDENCIA",
                "REDE_ENSINO",
            ],
            as_index=False,
        )
        .agg(
            ESCOLAS=(
                "CO_ENTIDADE",
                "nunique",
            ),
            MUNICIPIOS=(
                "CO_MUNICIPIO",
                "nunique",
            ),
            MATRICULAS_EM_PROP=(
                "QT_MAT_MED_PROP",
                "sum",
            ),
        )
        .sort_values(
            "TP_DEPENDENCIA"
        )
        .reset_index(drop=True)
    )


def parse_args() -> argparse.Namespace:
    """
    Lê os argumentos da linha de comando.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Pré-processa os microdados do Censo Escolar "
            "para o Ensino Médio propedêutico."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help=(
            "Arquivo original dos microdados. "
            "Quando omitido, o script procura em CENSO_DIR."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=CENSO_PROCESSED_PATH,
        help=(
            "Caminho do arquivo Parquet processado."
        ),
    )

    parser.add_argument(
        "--uf",
        type=str,
        default="RS",
        help="Unidade da federação utilizada no filtro.",
    )

    parser.add_argument(
        "--nrows",
        type=int,
        default=None,
        help=(
            "Número opcional de linhas para teste. "
            "Não utilize na geração definitiva."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """
    Executa o pré-processamento e salva o arquivo Parquet.
    """
    configure_logging()

    args = parse_args()

    input_path = (
        args.input
        if args.input is not None
        else find_censo_file(CENSO_DIR)
    )

    logger.info(
        "Iniciando pré-processamento do Censo Escolar."
    )
    logger.info(
        "Arquivo de entrada: %s",
        input_path,
    )

    processed_df = preprocess_censo(
        file_path=input_path,
        uf=args.uf,
        nrows=args.nrows,
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    processed_df.to_parquet(
        args.output,
        index=False,
    )

    summary = build_dependency_summary(
        processed_df
    )

    logger.info(
        "Pré-processamento concluído."
    )
    logger.info(
        "Escolas processadas: %s",
        processed_df["CO_ENTIDADE"].nunique(),
    )
    logger.info(
        "Municípios com oferta: %s",
        processed_df["CO_MUNICIPIO"].nunique(),
    )
    logger.info(
        "Matrículas no Ensino Médio propedêutico: %s",
        int(
            processed_df[
                "QT_MAT_MED_PROP"
            ].sum()
        ),
    )
    logger.info(
        "Arquivo salvo em: %s",
        args.output,
    )

    print("\nResumo por rede de ensino:\n")
    print(
        summary.to_string(
            index=False,
        )
    )

    print("\nDimensão da base processada:")
    print(processed_df.shape)

    print("\nArquivo gerado:")
    print(args.output)


if __name__ == "__main__":
    main()
"""
Inspeção de colunas relacionadas ao Ensino Médio no Censo Escolar.

Este script identifica e resume colunas potencialmente úteis para
filtrar escolas que ofertam Ensino Médio, incluindo variáveis ligadas a:

- Ensino Médio;
- matrículas;
- dependência administrativa;
- etapa/modalidade de ensino;
- situação de funcionamento.

Uso
---
python -m src.inspect_high_school_columns

Ou, informando explicitamente o arquivo:

python -m src.inspect_high_school_columns ^
  --input data/processed/censo_escolar_rs_2024.parquet
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd


LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "censo_escolar_rs_2024.parquet"
)

SEARCH_GROUPS: dict[str, tuple[str, ...]] = {
    "ensino_medio": (
        "MED",
        "MEDIO",
        "ENSINO_MEDIO",
        "EM_",
        "_EM",
    ),
    "matriculas": (
        "MAT",
        "MATRIC",
        "QT_",
        "NUM_",
    ),
    "dependencia": (
        "DEPEND",
        "TP_DEP",
        "REDE",
    ),
    "etapa_modalidade": (
        "ETAPA",
        "MODAL",
        "CURSO",
        "ENSINO",
        "IN_",
    ),
    "situacao_funcionamento": (
        "SITUACAO",
        "FUNCION",
        "ATIVA",
    ),
}

EXACT_PRIORITY_COLUMNS = (
    "CO_ENTIDADE",
    "NO_ENTIDADE",
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "TP_DEPENDENCIA",
    "TP_SITUACAO_FUNCIONAMENTO",
    "IN_MED",
    "IN_MEDIO",
    "IN_ENSINO_MEDIO",
    "QT_MAT_MED",
    "QT_MAT_MED_PROP",
    "QT_MAT_MED_INT",
    "QT_MAT_MED_NM",
    "QT_MAT_MED_CT",
    "QT_MAT_MED_TEC",
)


def configure_logging() -> None:
    """Configura logs simples para execução no terminal."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def load_data(input_path: Path) -> pd.DataFrame:
    """Carrega a base Parquet."""
    if not input_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {input_path}"
        )

    LOGGER.info(
        "Lendo base: %s",
        input_path,
    )

    dataframe = pd.read_parquet(input_path)

    LOGGER.info(
        "Base carregada: %s linhas e %s colunas.",
        len(dataframe),
        len(dataframe.columns),
    )

    return dataframe


def find_matching_columns(
    dataframe: pd.DataFrame,
    terms: tuple[str, ...],
) -> list[str]:
    """
    Localiza colunas contendo pelo menos um dos termos informados.
    """
    matches = []

    for column in dataframe.columns:
        upper_column = str(column).upper()

        if any(
            term.upper() in upper_column
            for term in terms
        ):
            matches.append(str(column))

    return sorted(set(matches))


def summarize_column(
    dataframe: pd.DataFrame,
    column: str,
    *,
    sample_size: int = 10,
) -> dict[str, object]:
    """
    Resume tipo, valores ausentes, cardinalidade e amostra de valores.
    """
    series = dataframe[column]

    non_null = series.dropna()

    unique_values = (
        non_null.astype("string")
        .value_counts(dropna=False)
        .head(sample_size)
    )

    sample = [
        {
            "valor": str(index),
            "frequencia": int(value),
        }
        for index, value in unique_values.items()
    ]

    numeric_series = pd.to_numeric(
        series,
        errors="coerce",
    )

    numeric_non_null = numeric_series.dropna()

    return {
        "coluna": column,
        "dtype": str(series.dtype),
        "na": int(series.isna().sum()),
        "na_percentual": round(
            float(series.isna().mean() * 100),
            2,
        ),
        "valores_unicos": int(
            non_null.nunique(dropna=True)
        ),
        "minimo": (
            float(numeric_non_null.min())
            if not numeric_non_null.empty
            else None
        ),
        "maximo": (
            float(numeric_non_null.max())
            if not numeric_non_null.empty
            else None
        ),
        "amostra_valores": sample,
    }


def print_column_summary(
    summary: dict[str, object],
) -> None:
    """Imprime o resumo de uma coluna."""
    print(
        f"\nColuna: {summary['coluna']}"
    )
    print(
        f"Tipo: {summary['dtype']}"
    )
    print(
        "Ausentes: "
        f"{summary['na']} "
        f"({summary['na_percentual']}%)"
    )
    print(
        f"Valores únicos: {summary['valores_unicos']}"
    )

    if summary["minimo"] is not None:
        print(
            f"Mínimo: {summary['minimo']}"
        )
        print(
            f"Máximo: {summary['maximo']}"
        )

    print("Valores mais frequentes:")

    for item in summary["amostra_valores"]:
        print(
            f"  - {item['valor']}: "
            f"{item['frequencia']}"
        )


def inspect_priority_columns(
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Retorna colunas prioritárias encontradas na base.
    """
    return [
        column
        for column in EXACT_PRIORITY_COLUMNS
        if column in dataframe.columns
    ]


def print_group_results(
    dataframe: pd.DataFrame,
    group_name: str,
    columns: list[str],
) -> None:
    """
    Imprime todas as colunas encontradas para um grupo.
    """
    print("\n" + "=" * 80)
    print(
        f"GRUPO: {group_name.upper()}"
    )
    print("=" * 80)

    if not columns:
        print(
            "Nenhuma coluna encontrada."
        )
        return

    print(
        f"Quantidade de colunas: {len(columns)}"
    )

    for column in columns:
        print(
            f"- {column}"
        )

    for column in columns:
        summary = summarize_column(
            dataframe,
            column,
        )
        print_column_summary(summary)


def inspect_high_school_columns(
    dataframe: pd.DataFrame,
) -> None:
    """
    Executa a inspeção completa das colunas relevantes.
    """
    print("\n" + "=" * 80)
    print("INSPEÇÃO DE COLUNAS DO CENSO ESCOLAR")
    print("=" * 80)

    print(
        f"\nLinhas: {len(dataframe)}"
    )
    print(
        f"Colunas: {len(dataframe.columns)}"
    )

    priority_columns = inspect_priority_columns(
        dataframe
    )

    print("\n" + "=" * 80)
    print("COLUNAS PRIORITÁRIAS ENCONTRADAS")
    print("=" * 80)

    if priority_columns:
        for column in priority_columns:
            print(
                f"- {column}"
            )
    else:
        print(
            "Nenhuma coluna prioritária foi encontrada."
        )

    for group_name, terms in SEARCH_GROUPS.items():
        columns = find_matching_columns(
            dataframe,
            terms,
        )

        print_group_results(
            dataframe=dataframe,
            group_name=group_name,
            columns=columns,
        )

    print("\n" + "=" * 80)
    print("RECOMENDAÇÃO PARA O PRÓXIMO PASSO")
    print("=" * 80)

    high_school_flags = [
        column
        for column in (
            "IN_MED",
            "IN_MEDIO",
            "IN_ENSINO_MEDIO",
        )
        if column in dataframe.columns
    ]

    high_school_enrollment_columns = [
        column
        for column in dataframe.columns
        if (
            "MAT_MED" in str(column).upper()
            or "MATRICUL" in str(column).upper()
            and "MED" in str(column).upper()
        )
    ]

    if high_school_flags:
        print(
            "Foi encontrada ao menos uma variável binária de oferta "
            "de Ensino Médio:"
        )

        for column in high_school_flags:
            print(
                f"- {column}"
            )

        print(
            "\nNa auditoria por rede, a filtragem deve priorizar "
            "uma dessas colunas com valor igual a 1."
        )

    elif high_school_enrollment_columns:
        print(
            "Não foi encontrada variável binária clara, mas foram "
            "encontradas colunas de matrícula do Ensino Médio:"
        )

        for column in high_school_enrollment_columns:
            print(
                f"- {column}"
            )

        print(
            "\nNa auditoria por rede, a filtragem deve considerar "
            "somente escolas cuja soma dessas matrículas seja maior que zero."
        )

    else:
        print(
            "Não foi encontrada uma variável clara de oferta ou matrícula "
            "do Ensino Médio. Será necessário revisar manualmente os nomes "
            "das colunas ou a etapa de pré-processamento."
        )


def parse_args() -> argparse.Namespace:
    """Lê argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description=(
            "Inspeciona colunas relacionadas ao Ensino Médio "
            "na base do Censo Escolar."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help=(
            "Caminho do arquivo Parquet no nível de escola."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Ponto de entrada do script."""
    configure_logging()
    args = parse_args()

    dataframe = load_data(
        args.input
    )

    inspect_high_school_columns(
        dataframe
    )


if __name__ == "__main__":
    main()
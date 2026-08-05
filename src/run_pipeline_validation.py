"""
Validação integrada dos principais artefatos do pipeline.

Este módulo verifica a consistência entre:

- municipality_features.parquet;
- municipality_base.parquet;
- municipality_vulnerability.parquet.

Execução
--------
Na raiz do projeto:

python -m src.run_pipeline_validation
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.config import (
    MUNICIPALITY_BASE_PATH,
    MUNICIPALITY_FEATURES_PATH,
    MUNICIPALITY_FINAL_INDEX_PATH,
)
from src.logger import setup_logger
from src.vulnerability_index import CATEGORY_LABELS


logger = setup_logger()


REQUIRED_FEATURE_COLUMNS = {
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "SG_UF",
    "NUM_ESCOLAS",
    "NUM_MATRICULAS",
    "INFRA_MEDIA",
    "PERC_RURAL",
    "PERC_PUBLICA",
    "PERC_ESTADUAL",
    "PERC_MUNICIPAL",
    "MEDIA_MATRICULAS_ESCOLA",
}

REQUIRED_BASE_COLUMNS = {
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "NUM_ESCOLAS",
    "NUM_MATRICULAS",
    "INFRA_MEDIA",
    "MEDIA_INSE",
    "ABANDONO_EM",
    "REPROVACAO_EM",
    "APROVACAO_EM",
    "DISTORCAO_EM",
    "MEDIA_MATRICULAS_ESCOLA",
}

REQUIRED_VULNERABILITY_COLUMNS = {
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "IVE",
    "IVE_CATEGORIA",
    "RANK_VULNERABILIDADE",
}

IVE_COMPONENT_COLUMNS = {
    "ABANDONO_EM",
    "REPROVACAO_EM",
    "DISTORCAO_EM",
    "MEDIA_INSE",
    "INFRA_MEDIA",
    "MEDIA_MATRICULAS_ESCOLA",
}

PERCENTAGE_COLUMNS = {
    "PERC_RURAL",
    "PERC_PUBLICA",
    "PERC_ESTADUAL",
    "PERC_MUNICIPAL",
    "PERC_BIBLIOTECA",
    "PERC_LAB_INFO",
    "PERC_QUADRA",
    "PERC_INTERNET",
    "PERC_BANDA_LARGA",
}


def validate_file_exists(
    file_path: Path,
    dataset_name: str,
) -> None:
    """
    Verifica se um artefato do pipeline existe.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"O arquivo de {dataset_name} não foi encontrado: "
            f"{file_path}"
        )


def load_parquet(
    file_path: Path,
    dataset_name: str,
) -> pd.DataFrame:
    """
    Carrega um arquivo Parquet após validar sua existência.
    """
    validate_file_exists(
        file_path=file_path,
        dataset_name=dataset_name,
    )

    logger.info(
        "Carregando %s: %s",
        dataset_name,
        file_path,
    )

    dataframe = pd.read_parquet(
        file_path
    )

    if dataframe.empty:
        raise ValueError(
            f"A base {dataset_name} está vazia."
        )

    return dataframe


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: set[str],
    dataset_name: str,
) -> None:
    """
    Verifica se todas as colunas obrigatórias estão presentes.
    """
    missing_columns = sorted(
        required_columns.difference(
            dataframe.columns
        )
    )

    if missing_columns:
        raise ValueError(
            f"A base {dataset_name} não possui as colunas "
            f"obrigatórias: {missing_columns}."
        )


def validate_municipality_structure(
    dataframe: pd.DataFrame,
    dataset_name: str,
    expected_municipalities: int,
) -> None:
    """
    Valida quantidade, unicidade e preenchimento dos municípios.
    """
    if "CO_MUNICIPIO" not in dataframe.columns:
        raise ValueError(
            f"A base {dataset_name} não possui CO_MUNICIPIO."
        )

    missing_codes = dataframe[
        "CO_MUNICIPIO"
    ].isna()

    if missing_codes.any():
        raise ValueError(
            f"A base {dataset_name} possui "
            f"{int(missing_codes.sum())} códigos municipais ausentes."
        )

    duplicated_codes = dataframe[
        "CO_MUNICIPIO"
    ].duplicated(
        keep=False
    )

    if duplicated_codes.any():
        duplicated = (
            dataframe.loc[
                duplicated_codes,
                "CO_MUNICIPIO",
            ]
            .drop_duplicates()
            .astype(str)
            .tolist()
        )

        raise ValueError(
            f"A base {dataset_name} possui municípios duplicados: "
            f"{duplicated[:10]}."
        )

    row_count = len(dataframe)
    unique_count = dataframe[
        "CO_MUNICIPIO"
    ].nunique()

    if row_count != expected_municipalities:
        raise ValueError(
            f"A base {dataset_name} possui {row_count} linhas, "
            f"mas eram esperadas {expected_municipalities}."
        )

    if unique_count != expected_municipalities:
        raise ValueError(
            f"A base {dataset_name} possui {unique_count} códigos "
            f"municipais únicos, mas eram esperados "
            f"{expected_municipalities}."
        )


def validate_same_municipalities(
    first_dataframe: pd.DataFrame,
    second_dataframe: pd.DataFrame,
    first_name: str,
    second_name: str,
) -> None:
    """
    Verifica se duas bases possuem o mesmo conjunto de municípios.
    """
    first_codes = set(
        first_dataframe["CO_MUNICIPIO"]
    )

    second_codes = set(
        second_dataframe["CO_MUNICIPIO"]
    )

    only_in_first = sorted(
        first_codes - second_codes
    )

    only_in_second = sorted(
        second_codes - first_codes
    )

    if only_in_first or only_in_second:
        raise ValueError(
            f"As bases {first_name} e {second_name} possuem "
            "coberturas municipais diferentes. "
            f"Somente em {first_name}: {only_in_first[:10]}. "
            f"Somente em {second_name}: {only_in_second[:10]}."
        )


def validate_feature_values(
    dataframe: pd.DataFrame,
) -> None:
    """
    Valida os principais valores da base de características.
    """
    if dataframe["NUM_ESCOLAS"].le(0).any():
        raise ValueError(
            "A base de características possui municípios "
            "sem escolas."
        )

    if dataframe["NUM_MATRICULAS"].le(0).any():
        raise ValueError(
            "A base de características possui municípios "
            "sem matrículas no Ensino Médio propedêutico."
        )

    available_percentage_columns = sorted(
        PERCENTAGE_COLUMNS.intersection(
            dataframe.columns
        )
    )

    if available_percentage_columns:
        invalid_percentages = (
            dataframe[
                available_percentage_columns
            ].lt(0)
            | dataframe[
                available_percentage_columns
            ].gt(1)
        )

        if invalid_percentages.any().any():
            invalid_columns = (
                invalid_percentages
                .any()
                .loc[
                    lambda series: series
                ]
                .index
                .tolist()
            )

            raise ValueError(
                "Foram encontrados percentuais fora do intervalo "
                f"entre 0 e 1: {invalid_columns}."
            )


def validate_base_indicators(
    dataframe: pd.DataFrame,
) -> None:
    """
    Verifica se os componentes do IVE possuem dados válidos.
    """
    missing_component_columns = sorted(
        IVE_COMPONENT_COLUMNS.difference(
            dataframe.columns
        )
    )

    if missing_component_columns:
        raise ValueError(
            "A base municipal não possui todos os componentes "
            f"do IVE: {missing_component_columns}."
        )

    components = dataframe[
        sorted(IVE_COMPONENT_COLUMNS)
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    completely_missing_columns = (
        components.isna()
        .all()
        .loc[
            lambda series: series
        ]
        .index
        .tolist()
    )

    if completely_missing_columns:
        raise ValueError(
            "Os seguintes componentes do IVE não possuem "
            f"nenhum valor válido: {completely_missing_columns}."
        )

    municipalities_without_components = (
        components
        .isna()
        .all(axis=1)
    )

    if municipalities_without_components.any():
        missing_codes = (
            dataframe.loc[
                municipalities_without_components,
                "CO_MUNICIPIO",
            ]
            .astype(str)
            .tolist()
        )

        raise ValueError(
            "Foram encontrados municípios sem nenhum componente "
            f"válido do IVE: {missing_codes[:10]}."
        )


def validate_ive(
    dataframe: pd.DataFrame,
    expected_municipalities: int,
) -> None:
    """
    Valida o índice, as categorias e o ranking.
    """
    ive = pd.to_numeric(
        dataframe["IVE"],
        errors="coerce",
    )

    if ive.isna().any():
        raise ValueError(
            "O IVE possui valores ausentes ou não numéricos."
        )

    if not ive.between(
        0,
        1,
        inclusive="both",
    ).all():
        raise ValueError(
            "Foram encontrados valores do IVE fora do "
            "intervalo entre 0 e 1."
        )

    valid_categories = set(
        CATEGORY_LABELS
    )

    observed_categories = set(
        dataframe["IVE_CATEGORIA"]
        .dropna()
        .astype(str)
        .unique()
    )

    invalid_categories = sorted(
        observed_categories - valid_categories
    )

    if invalid_categories:
        raise ValueError(
            "Foram encontradas categorias de IVE inválidas: "
            f"{invalid_categories}."
        )

    if dataframe["IVE_CATEGORIA"].isna().any():
        raise ValueError(
            "A categoria do IVE possui valores ausentes."
        )

    ranking = pd.to_numeric(
        dataframe["RANK_VULNERABILIDADE"],
        errors="coerce",
    )

    if ranking.isna().any():
        raise ValueError(
            "O ranking possui valores ausentes ou não numéricos."
        )

    if ranking.duplicated().any():
        raise ValueError(
            "O ranking possui posições duplicadas."
        )

    expected_ranking = set(
        range(
            1,
            expected_municipalities + 1,
        )
    )

    observed_ranking = set(
        ranking.astype(int)
    )

    if observed_ranking != expected_ranking:
        missing_positions = sorted(
            expected_ranking - observed_ranking
        )

        unexpected_positions = sorted(
            observed_ranking - expected_ranking
        )

        raise ValueError(
            "O ranking não forma uma sequência completa. "
            f"Posições ausentes: {missing_positions[:10]}. "
            f"Posições inesperadas: {unexpected_positions[:10]}."
        )

    expected_order = (
        dataframe["IVE"]
        .rank(
            method="first",
            ascending=False,
        )
        .astype(int)
    )

    if not expected_order.equals(
        dataframe[
            "RANK_VULNERABILIDADE"
        ].astype(int)
    ):
        raise ValueError(
            "O ranking não está consistente com a ordenação "
            "decrescente do IVE."
        )


def run_pipeline_validation(
    *,
    features_path: Path,
    base_path: Path,
    vulnerability_path: Path,
    expected_municipalities: int,
) -> None:
    """
    Executa todas as validações integradas do pipeline.
    """
    features = load_parquet(
        file_path=features_path,
        dataset_name="municipality_features",
    )

    municipality_base = load_parquet(
        file_path=base_path,
        dataset_name="municipality_base",
    )

    vulnerability = load_parquet(
        file_path=vulnerability_path,
        dataset_name="municipality_vulnerability",
    )

    validate_required_columns(
        dataframe=features,
        required_columns=REQUIRED_FEATURE_COLUMNS,
        dataset_name="municipality_features",
    )

    validate_required_columns(
        dataframe=municipality_base,
        required_columns=REQUIRED_BASE_COLUMNS,
        dataset_name="municipality_base",
    )

    validate_required_columns(
        dataframe=vulnerability,
        required_columns=REQUIRED_VULNERABILITY_COLUMNS,
        dataset_name="municipality_vulnerability",
    )

    validate_municipality_structure(
        dataframe=features,
        dataset_name="municipality_features",
        expected_municipalities=expected_municipalities,
    )

    validate_municipality_structure(
        dataframe=municipality_base,
        dataset_name="municipality_base",
        expected_municipalities=expected_municipalities,
    )

    validate_municipality_structure(
        dataframe=vulnerability,
        dataset_name="municipality_vulnerability",
        expected_municipalities=expected_municipalities,
    )

    validate_same_municipalities(
        first_dataframe=features,
        second_dataframe=municipality_base,
        first_name="municipality_features",
        second_name="municipality_base",
    )

    validate_same_municipalities(
        first_dataframe=municipality_base,
        second_dataframe=vulnerability,
        first_name="municipality_base",
        second_name="municipality_vulnerability",
    )

    validate_feature_values(
        features
    )

    validate_base_indicators(
        municipality_base
    )

    validate_ive(
        dataframe=vulnerability,
        expected_municipalities=expected_municipalities,
    )

    print("\nValidação integrada concluída com sucesso.\n")

    print(
        "✓ municipality_features.parquet: "
        f"{features.shape[0]} linhas e "
        f"{features.shape[1]} colunas"
    )

    print(
        "✓ municipality_base.parquet: "
        f"{municipality_base.shape[0]} linhas e "
        f"{municipality_base.shape[1]} colunas"
    )

    print(
        "✓ municipality_vulnerability.parquet: "
        f"{vulnerability.shape[0]} linhas e "
        f"{vulnerability.shape[1]} colunas"
    )

    print(
        "✓ Municípios únicos: "
        f"{expected_municipalities}"
    )

    print(
        "✓ Ranking completo: "
        f"1–{expected_municipalities}"
    )

    print(
        "✓ IVE dentro do intervalo entre 0 e 1"
    )

    print(
        "✓ Categorias válidas e sem valores ausentes"
    )

    print(
        "✓ Cobertura municipal consistente entre os arquivos"
    )


def parse_args() -> argparse.Namespace:
    """
    Lê os argumentos da linha de comando.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Valida os principais artefatos do pipeline "
            "do Mapa da Vulnerabilidade Educacional."
        )
    )

    parser.add_argument(
        "--features",
        type=Path,
        default=MUNICIPALITY_FEATURES_PATH,
        help=(
            "Caminho de municipality_features.parquet."
        ),
    )

    parser.add_argument(
        "--base",
        type=Path,
        default=MUNICIPALITY_BASE_PATH,
        help=(
            "Caminho de municipality_base.parquet."
        ),
    )

    parser.add_argument(
        "--vulnerability",
        type=Path,
        default=MUNICIPALITY_FINAL_INDEX_PATH,
        help=(
            "Caminho de municipality_vulnerability.parquet."
        ),
    )

    parser.add_argument(
        "--expected-municipalities",
        type=int,
        default=496,
        help=(
            "Quantidade esperada de municípios no universo analítico."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """
    Executa a validação integrada.
    """
    args = parse_args()

    run_pipeline_validation(
        features_path=args.features,
        base_path=args.base,
        vulnerability_path=args.vulnerability,
        expected_municipalities=args.expected_municipalities,
    )


if __name__ == "__main__":
    main()
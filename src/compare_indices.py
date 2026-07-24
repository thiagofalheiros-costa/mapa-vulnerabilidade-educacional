"""Comparação entre o IVE manual, PCA e análise fatorial."""

from itertools import combinations
from pathlib import Path
from typing import Final, Sequence

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.logger import setup_logger

logger = setup_logger()

ID_COLUMNS: Final[tuple[str, ...]] = (
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "SG_UF",
)

INDEX_COLUMNS: Final[tuple[str, ...]] = (
    "IVE",
    "IVE_PCA",
    "IVE_FACTOR",
)

TOP_CUTOFFS: Final[tuple[int, ...]] = (10, 20, 50, 100)


def _validate_columns(
    dataframe: pd.DataFrame,
    required_columns: Sequence[str],
    dataframe_name: str,
) -> None:
    """Valida a presença das colunas obrigatórias."""
    missing_columns = sorted(set(required_columns) - set(dataframe.columns))
    if missing_columns:
        raise ValueError(
            f"A base '{dataframe_name}' não contém todas as colunas necessárias. "
            f"Colunas ausentes: {missing_columns}."
        )


def _prepare_merge_columns(
    dataframe: pd.DataFrame,
    index_column: str,
) -> pd.DataFrame:
    """Seleciona identificadores disponíveis e a coluna de índice."""
    available_id_columns = [
        column for column in ID_COLUMNS if column in dataframe.columns
    ]
    return dataframe.loc[:, [*available_id_columns, index_column]].copy()


def merge_validation_indices(
    manual: pd.DataFrame,
    pca: pd.DataFrame,
    factor: pd.DataFrame,
) -> pd.DataFrame:
    """Combina os três índices em uma única base municipal."""
    _validate_columns(manual, ["CO_MUNICIPIO", "IVE"], "manual")
    _validate_columns(pca, ["CO_MUNICIPIO", "IVE_PCA"], "PCA")
    _validate_columns(factor, ["CO_MUNICIPIO", "IVE_FACTOR"], "fatorial")

    manual_selected = _prepare_merge_columns(manual, "IVE")
    pca_selected = pca.loc[:, ["CO_MUNICIPIO", "IVE_PCA"]].copy()
    factor_selected = factor.loc[:, ["CO_MUNICIPIO", "IVE_FACTOR"]].copy()

    comparison = (
        manual_selected
        .merge(
            pca_selected,
            on="CO_MUNICIPIO",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            factor_selected,
            on="CO_MUNICIPIO",
            how="inner",
            validate="one_to_one",
        )
    )

    for column in INDEX_COLUMNS:
        comparison[column] = pd.to_numeric(comparison[column], errors="coerce")

    if comparison[list(INDEX_COLUMNS)].isna().any().any():
        raise ValueError(
            "Os índices de validação contêm valores ausentes ou inválidos."
        )

    comparison["RANK_IVE"] = (
        comparison["IVE"].rank(method="min", ascending=False).astype("Int64")
    )
    comparison["RANK_IVE_PCA"] = (
        comparison["IVE_PCA"].rank(method="min", ascending=False).astype("Int64")
    )
    comparison["RANK_IVE_FACTOR"] = (
        comparison["IVE_FACTOR"]
        .rank(method="min", ascending=False)
        .astype("Int64")
    )

    comparison["DIF_RANK_IVE_PCA"] = (
        comparison["RANK_IVE"] - comparison["RANK_IVE_PCA"]
    ).abs()
    comparison["DIF_RANK_IVE_FACTOR"] = (
        comparison["RANK_IVE"] - comparison["RANK_IVE_FACTOR"]
    ).abs()
    comparison["DIF_RANK_PCA_FACTOR"] = (
        comparison["RANK_IVE_PCA"] - comparison["RANK_IVE_FACTOR"]
    ).abs()

    return comparison


def calculate_index_correlations(comparison: pd.DataFrame) -> pd.DataFrame:
    """Calcula correlações de Pearson e Spearman entre os índices."""
    _validate_columns(comparison, list(INDEX_COLUMNS), "comparação")
    rows: list[dict[str, float | int | str]] = []

    for index_1, index_2 in combinations(INDEX_COLUMNS, 2):
        pair = comparison[[index_1, index_2]].dropna()
        pearson = pair[index_1].corr(pair[index_2], method="pearson")
        spearman, p_value = spearmanr(
            pair[index_1], pair[index_2], nan_policy="omit"
        )

        rows.append(
            {
                "INDICE_1": index_1,
                "INDICE_2": index_2,
                "CORRELACAO_PEARSON": float(pearson),
                "CORRELACAO_SPEARMAN": float(spearman),
                "P_VALOR_SPEARMAN": float(p_value),
                "NUM_OBSERVACOES": int(len(pair)),
            }
        )

    return pd.DataFrame(rows)


def calculate_ranking_stability(
    comparison: pd.DataFrame,
    top_cutoffs: Sequence[int] = TOP_CUTOFFS,
) -> pd.DataFrame:
    """Avalia sobreposição e diferença de posições nos Top N."""
    _validate_columns(
        comparison,
        ["CO_MUNICIPIO", *INDEX_COLUMNS],
        "comparação",
    )

    rows: list[dict[str, float | int | str]] = []

    for index_1, index_2 in combinations(INDEX_COLUMNS, 2):
        rank_column_1 = f"RANK_{index_1}"
        rank_column_2 = f"RANK_{index_2}"

        for top in top_cutoffs:
            effective_top = min(int(top), len(comparison))
            top_1 = comparison.nlargest(effective_top, index_1)
            top_2 = comparison.nlargest(effective_top, index_2)

            municipalities_1 = set(top_1["CO_MUNICIPIO"])
            municipalities_2 = set(top_2["CO_MUNICIPIO"])
            common_municipalities = municipalities_1 & municipalities_2
            union_municipalities = municipalities_1 | municipalities_2
            overlap = len(common_municipalities)

            common_rows = comparison[
                comparison["CO_MUNICIPIO"].isin(common_municipalities)
            ].copy()
            rank_difference = (
                common_rows[rank_column_1] - common_rows[rank_column_2]
            ).abs()

            rows.append(
                {
                    "INDICE_1": index_1,
                    "INDICE_2": index_2,
                    "TOP": effective_top,
                    "MUNICIPIOS_EM_COMUM": overlap,
                    "PERCENTUAL_CONCORDANCIA": overlap / effective_top,
                    "INDICE_JACCARD": (
                        overlap / len(union_municipalities)
                        if union_municipalities
                        else np.nan
                    ),
                    "DIFERENCA_MEDIA_RANK": (
                        float(rank_difference.mean())
                        if not rank_difference.empty
                        else np.nan
                    ),
                    "DIFERENCA_MEDIANA_RANK": (
                        float(rank_difference.median())
                        if not rank_difference.empty
                        else np.nan
                    ),
                }
            )

    return pd.DataFrame(rows)


def create_priority_consensus(
    comparison: pd.DataFrame,
    top_n: int = 50,
) -> pd.DataFrame:
    """Cria ranking de consenso pela posição média nos três métodos."""
    _validate_columns(
        comparison,
        [
            "CO_MUNICIPIO",
            "RANK_IVE",
            "RANK_IVE_PCA",
            "RANK_IVE_FACTOR",
        ],
        "comparação",
    )

    consensus = comparison.copy()
    rank_columns = ["RANK_IVE", "RANK_IVE_PCA", "RANK_IVE_FACTOR"]

    consensus["RANK_MEDIO_CONSENSO"] = (
        consensus[rank_columns].astype(float).mean(axis=1)
    )
    consensus["DESVIO_RANK_CONSENSO"] = (
        consensus[rank_columns].astype(float).std(axis=1)
    )

    for cutoff in (10, 20, 50):
        consensus[f"PRESENTE_TOP_{cutoff}_TRES_INDICES"] = (
            (consensus["RANK_IVE"] <= cutoff)
            & (consensus["RANK_IVE_PCA"] <= cutoff)
            & (consensus["RANK_IVE_FACTOR"] <= cutoff)
        )

    consensus = consensus.sort_values(
        ["RANK_MEDIO_CONSENSO", "DESVIO_RANK_CONSENSO"],
        ascending=True,
    ).head(top_n)

    consensus.insert(0, "POSICAO_CONSENSO", range(1, len(consensus) + 1))
    return consensus.reset_index(drop=True)


def run_index_comparison(
    manual: pd.DataFrame,
    pca: pd.DataFrame,
    factor: pd.DataFrame,
    consensus_top_n: int = 50,
) -> dict[str, pd.DataFrame]:
    """Executa a comparação completa entre os três índices."""
    municipality_validation = merge_validation_indices(
        manual=manual,
        pca=pca,
        factor=factor,
    )
    index_correlations = calculate_index_correlations(municipality_validation)
    ranking_stability = calculate_ranking_stability(municipality_validation)
    priority_consensus = create_priority_consensus(
        municipality_validation,
        top_n=consensus_top_n,
    )

    logger.info(
        "Comparação concluída para %s municípios.",
        len(municipality_validation),
    )

    return {
        "municipality_validation": municipality_validation,
        "index_comparison": municipality_validation,
        "index_correlations": index_correlations,
        "ranking_stability": ranking_stability,
        "priority_consensus": priority_consensus,
    }



def compare_indices(
    manual: pd.DataFrame,
    pca: pd.DataFrame,
    factor: pd.DataFrame,
    consensus_top_n: int = 50,
) -> dict[str, pd.DataFrame]:
    """
    Mantém compatibilidade com a interface usada nas versões anteriores.

    Esta função é um alias público de ``run_index_comparison``.
    """
    return run_index_comparison(
        manual=manual,
        pca=pca,
        factor=factor,
        consensus_top_n=consensus_top_n,
    )


def execute_comparison_pipeline(
    manual_path: Path,
    pca_path: Path,
    factor_path: Path,
    processed_output_path: Path,
    tables_directory: Path,
) -> dict[str, pd.DataFrame]:
    """Lê as bases, compara os índices e salva as saídas."""
    manual_path = Path(manual_path)
    pca_path = Path(pca_path)
    factor_path = Path(factor_path)
    processed_output_path = Path(processed_output_path)
    tables_directory = Path(tables_directory)

    for path in (manual_path, pca_path, factor_path):
        if not path.exists():
            raise FileNotFoundError(f"Base não encontrada: {path}")

    manual = pd.read_parquet(manual_path)
    pca = pd.read_parquet(pca_path)
    factor = pd.read_parquet(factor_path)

    results = run_index_comparison(
        manual=manual,
        pca=pca,
        factor=factor,
    )

    processed_output_path.parent.mkdir(parents=True, exist_ok=True)
    tables_directory.mkdir(parents=True, exist_ok=True)

    results["municipality_validation"].to_parquet(
        processed_output_path,
        index=False,
    )

    output_files = {
        "index_correlations": "index_correlations.csv",
        "ranking_stability": "ranking_stability.csv",
        "priority_consensus": "priority_consensus.csv",
    }

    for result_name, filename in output_files.items():
        results[result_name].to_csv(
            tables_directory / filename,
            index=False,
            encoding="utf-8-sig",
        )

    logger.info("Comparações salvas com sucesso.")
    return results

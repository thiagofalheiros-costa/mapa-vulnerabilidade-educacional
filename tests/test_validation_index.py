"""Testes básicos da validação estatística."""

import numpy as np
import pandas as pd

from src.compare_indices import compare_indices
from src.validate_factor import run_factor_validation
from src.validate_pca import FEATURES, run_pca_validation


def _sample_dataframe(rows: int = 100) -> pd.DataFrame:
    """Cria uma base sintética reprodutível."""
    rng = np.random.default_rng(42)

    dataframe = pd.DataFrame(
        {
            "CO_MUNICIPIO": np.arange(rows),
            "NO_MUNICIPIO": [f"Município {i}" for i in range(rows)],
            "SG_UF": ["RS"] * rows,
        }
    )

    latent = rng.normal(size=rows)

    for index, column in enumerate(FEATURES):
        values = latent + rng.normal(scale=0.4, size=rows)
        values = (values - values.min()) / (
            values.max() - values.min()
        )

        if column in {
            "MEDIA_INSE_NORM",
            "INFRA_MEDIA_NORM",
            "MEDIA_MATRICULAS_ESCOLA_NORM",
        }:
            values = 1 - values

        dataframe[column] = values

    dataframe["IVE"] = (
        dataframe["ABANDONO_EM_NORM"]
        + dataframe["REPROVACAO_EM_NORM"]
        + dataframe["DISTORCAO_EM_NORM"]
        + (1 - dataframe["MEDIA_INSE_NORM"])
        + (1 - dataframe["INFRA_MEDIA_NORM"])
        + (1 - dataframe["MEDIA_MATRICULAS_ESCOLA_NORM"])
    ) / 6

    dataframe["RANK_VULNERABILIDADE"] = (
        dataframe["IVE"]
        .rank(method="min", ascending=False)
        .astype("Int64")
    )

    return dataframe


def test_pca_generates_normalized_index() -> None:
    dataframe = _sample_dataframe()
    results = run_pca_validation(dataframe)

    index = results["municipality_pca"]["IVE_PCA"]

    assert len(index) == len(dataframe)
    assert index.between(0, 1).all()


def test_factor_generates_normalized_index() -> None:
    dataframe = _sample_dataframe()
    results = run_factor_validation(dataframe)

    index = results["municipality_factor"]["IVE_FACTOR"]

    assert len(index) == len(dataframe)
    assert index.between(0, 1).all()


def test_comparison_preserves_municipalities() -> None:
    dataframe = _sample_dataframe()
    pca = run_pca_validation(dataframe)["municipality_pca"]
    factor = run_factor_validation(dataframe)["municipality_factor"]

    results = compare_indices(dataframe, pca, factor)

    assert len(results["index_comparison"]) == len(dataframe)
    assert len(results["index_correlations"]) == 3

"""Testes adicionais da estabilidade dos rankings."""

import numpy as np
import pandas as pd

from src.compare_indices import (
    calculate_ranking_stability,
    run_index_comparison,
)


def _comparison_dataframe(size: int = 120) -> pd.DataFrame:
    municipalities = np.arange(1, size + 1)
    ive = np.linspace(1, 0, size)

    return pd.DataFrame(
        {
            "CO_MUNICIPIO": municipalities,
            "IVE": ive,
            "IVE_PCA": ive,
            "IVE_FACTOR": ive[::-1],
            "RANK_IVE": np.arange(1, size + 1),
            "RANK_IVE_PCA": np.arange(1, size + 1),
            "RANK_IVE_FACTOR": np.arange(size, 0, -1),
        }
    )


def test_identical_rankings_have_full_overlap() -> None:
    comparison = _comparison_dataframe()
    stability = calculate_ranking_stability(
        comparison,
        top_cutoffs=[10, 20, 50],
    )

    identical = stability[
        (stability["INDICE_1"] == "IVE")
        & (stability["INDICE_2"] == "IVE_PCA")
    ]

    assert (identical["PERCENTUAL_CONCORDANCIA"] == 1.0).all()
    assert (identical["DIFERENCA_MEDIA_RANK"] == 0.0).all()


def test_opposite_rankings_have_no_top_10_overlap() -> None:
    comparison = _comparison_dataframe()
    stability = calculate_ranking_stability(
        comparison,
        top_cutoffs=[10],
    )

    opposite = stability[
        (stability["INDICE_1"] == "IVE")
        & (stability["INDICE_2"] == "IVE_FACTOR")
    ].iloc[0]

    assert opposite["MUNICIPIOS_EM_COMUM"] == 0
    assert opposite["PERCENTUAL_CONCORDANCIA"] == 0.0


def test_comparison_returns_ranking_stability() -> None:
    size = 120
    manual = pd.DataFrame(
        {
            "CO_MUNICIPIO": np.arange(1, size + 1),
            "NO_MUNICIPIO": [
                f"Município {number}" for number in range(1, size + 1)
            ],
            "SG_UF": "RS",
            "IVE": np.linspace(1, 0, size),
        }
    )

    pca = manual[["CO_MUNICIPIO"]].copy()
    pca["IVE_PCA"] = manual["IVE"]

    factor = manual[["CO_MUNICIPIO"]].copy()
    factor["IVE_FACTOR"] = manual["IVE"]

    results = run_index_comparison(
        manual=manual,
        pca=pca,
        factor=factor,
    )

    assert "ranking_stability" in results
    assert not results["ranking_stability"].empty

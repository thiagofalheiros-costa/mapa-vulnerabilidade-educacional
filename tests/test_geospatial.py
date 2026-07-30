"""
Testes unitários para o módulo geoespacial.
"""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from src.geospatial import (
    create_priority_flag,
    merge_municipality_geodata,
    repair_geometries,
    standardize_municipality_code,
    validate_geodata,
)


@pytest.fixture
def sample_boundaries() -> gpd.GeoDataFrame:
    """
    Cria uma pequena malha municipal simulada.
    """
    geometries = [
        Polygon(
            [
                (0, 0),
                (1, 0),
                (1, 1),
                (0, 1),
                (0, 0),
            ]
        ),
        Polygon(
            [
                (1, 0),
                (2, 0),
                (2, 1),
                (1, 1),
                (1, 0),
            ]
        ),
        Polygon(
            [
                (2, 0),
                (3, 0),
                (3, 1),
                (2, 1),
                (2, 0),
            ]
        ),
    ]

    return gpd.GeoDataFrame(
        {
            "CO_MUNICIPIO": [
                "4300001",
                "4300002",
                "4300003",
            ],
            "NM_MUN": [
                "Município A",
                "Município B",
                "Município C",
            ],
        },
        geometry=geometries,
        crs="EPSG:4674",
    )


@pytest.fixture
def sample_index() -> pd.DataFrame:
    """
    Cria uma base simulada do IVE.
    """
    return pd.DataFrame(
        {
            "CO_MUNICIPIO": [
                4300001,
                4300002,
                4300003,
            ],
            "NO_MUNICIPIO": [
                "Município A",
                "Município B",
                "Município C",
            ],
            "IVE": [
                0.20,
                0.35,
                0.50,
            ],
            "IVE_CATEGORIA_RELATIVA": [
                "Muito baixa",
                "Média",
                "Muito alta",
            ],
            "IVE_RANK": [
                3,
                2,
                1,
            ],
        }
    )


def test_standardize_municipality_code() -> None:
    """
    Deve converter diferentes formatos em códigos de 7 dígitos.
    """
    series = pd.Series(
        [
            4300001,
            "4300002",
            "4300003.0",
        ]
    )

    result = standardize_municipality_code(series)

    assert result.tolist() == [
        "4300001",
        "4300002",
        "4300003",
    ]


def test_repair_geometries(
    sample_boundaries: gpd.GeoDataFrame,
) -> None:
    """
    Todas as geometrias devem permanecer válidas.
    """
    result = repair_geometries(
        sample_boundaries
    )

    assert isinstance(
        result,
        gpd.GeoDataFrame,
    )
    assert result.geometry.is_valid.all()
    assert not result.geometry.isna().any()


def test_merge_municipality_geodata(
    sample_boundaries: gpd.GeoDataFrame,
    sample_index: pd.DataFrame,
) -> None:
    """
    O merge deve preservar todos os municípios.
    """
    result = merge_municipality_geodata(
        boundaries=sample_boundaries,
        municipality_index=sample_index,
        expected_municipalities=3,
    )

    assert isinstance(
        result,
        gpd.GeoDataFrame,
    )
    assert len(result) == 3
    assert result["IVE"].notna().all()
    assert result["CO_MUNICIPIO"].nunique() == 3


def test_merge_raises_error_for_unmatched_municipality(
    sample_boundaries: gpd.GeoDataFrame,
    sample_index: pd.DataFrame,
) -> None:
    """
    Deve falhar quando um município da malha não estiver no IVE.
    """
    incomplete_index = sample_index.iloc[:2].copy()

    with pytest.raises(
        ValueError,
        match="municípios da malha não foram encontrados",
    ):
        merge_municipality_geodata(
            boundaries=sample_boundaries,
            municipality_index=incomplete_index,
            expected_municipalities=3,
        )


def test_create_priority_flag(
    sample_boundaries: gpd.GeoDataFrame,
    sample_index: pd.DataFrame,
) -> None:
    """
    Deve identificar corretamente os municípios prioritários.
    """
    geodata = merge_municipality_geodata(
        boundaries=sample_boundaries,
        municipality_index=sample_index,
        expected_municipalities=3,
    )

    result = create_priority_flag(
        geodata=geodata,
        top_n=2,
    )

    priority_counts = (
        result["PRIORIDADE"]
        .value_counts()
        .to_dict()
    )

    assert priority_counts["Top 2"] == 2
    assert priority_counts["Demais municípios"] == 1


def test_validate_geodata(
    sample_boundaries: gpd.GeoDataFrame,
    sample_index: pd.DataFrame,
) -> None:
    """
    A base simulada deve ser considerada válida.
    """
    geodata = merge_municipality_geodata(
        boundaries=sample_boundaries,
        municipality_index=sample_index,
        expected_municipalities=3,
    )

    summary = validate_geodata(
        geodata=geodata,
        expected_municipalities=3,
    )

    assert summary["municipios_total"] == 3
    assert summary["municipios_unicos"] == 3
    assert summary["codigos_duplicados"] == 0
    assert summary["indicadores_nulos"] == 0
    assert summary["geometrias_invalidas"] == 0
    assert summary["base_valida"] is True
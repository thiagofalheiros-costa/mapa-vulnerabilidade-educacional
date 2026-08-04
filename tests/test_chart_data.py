"""
Testes unitários da preparação de dados dos gráficos.

Este módulo valida as transformações, os resumos estatísticos
e os tratamentos de exceções definidos em chart_data.py.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dashboard.components import chart_data


@pytest.fixture
def complete_dataframe() -> pd.DataFrame:
    """
    Retorna uma base simulada com os indicadores utilizados
    pelos gráficos e pela análise integrada.
    """
    return pd.DataFrame(
        {
            "NO_MUNICIPIO": [
                "Município A",
                "Município B",
                "Município C",
                "Município D",
                "Município E",
            ],
            "IVE": [
                0.10,
                0.20,
                0.30,
                0.40,
                0.50,
            ],
            "IVE_CATEGORIA": [
                "Muito baixa",
                "Baixa",
                "Baixa",
                "Média",
                "Alta",
            ],
            "INFRA_MEDIA": [
                0.90,
                0.80,
                0.70,
                0.60,
                0.50,
            ],
            "MEDIA_INSE": [
                5.0,
                4.8,
                4.5,
                4.2,
                4.0,
            ],
            "ABANDONO_EM": [
                1.0,
                2.0,
                3.0,
                4.0,
                5.0,
            ],
            "REPROVACAO_EM": [
                2.0,
                4.0,
                6.0,
                8.0,
                10.0,
            ],
            "DISTORCAO_EM": [
                5.0,
                8.0,
                11.0,
                14.0,
                17.0,
            ],
            "MEDIA_MATRICULAS_ESCOLA": [
                200,
                250,
                300,
                350,
                400,
            ],
            "NUM_MATRICULAS": [
                1000,
                2000,
                3000,
                4000,
                5000,
            ],
        }
    )


# =============================================================================
# IDENTIFICAÇÃO DE COLUNAS
# =============================================================================


def test_identify_category_column_prefers_absolute_category() -> None:
    """
    Deve priorizar IVE_CATEGORIA quando as duas colunas existem.
    """
    dataframe = pd.DataFrame(
        {
            "IVE_CATEGORIA": ["Baixa"],
            "IVE_CATEGORIA_RELATIVA": ["Média"],
        }
    )

    result = chart_data.identify_category_column(
        dataframe
    )

    assert result == "IVE_CATEGORIA"


def test_identify_category_column_uses_relative_category() -> None:
    """
    Deve usar a categoria relativa quando a absoluta não existe.
    """
    dataframe = pd.DataFrame(
        {
            "IVE_CATEGORIA_RELATIVA": [
                "Média"
            ],
        }
    )

    result = chart_data.identify_category_column(
        dataframe
    )

    assert result == "IVE_CATEGORIA_RELATIVA"


def test_identify_category_column_returns_none() -> None:
    """
    Deve retornar None quando nenhuma categoria está disponível.
    """
    dataframe = pd.DataFrame(
        {
            "IVE": [0.25],
        }
    )

    result = chart_data.identify_category_column(
        dataframe
    )

    assert result is None


@pytest.mark.parametrize(
    (
        "column_name",
        "expected",
    ),
    [
        (
            "INFRA_MEDIA",
            "INFRA_MEDIA",
        ),
        (
            "INFRAESTRUTURA_MEDIA",
            "INFRAESTRUTURA_MEDIA",
        ),
        (
            "INDICE_INFRAESTRUTURA",
            "INDICE_INFRAESTRUTURA",
        ),
    ],
)
def test_identify_infrastructure_column(
    column_name: str,
    expected: str,
) -> None:
    """
    Deve reconhecer os nomes aceitos para infraestrutura.
    """
    dataframe = pd.DataFrame(
        {
            column_name: [0.75],
        }
    )

    result = (
        chart_data.identify_infrastructure_column(
            dataframe
        )
    )

    assert result == expected


def test_identify_infrastructure_column_returns_none() -> None:
    """
    Deve retornar None quando não existe coluna compatível.
    """
    dataframe = pd.DataFrame(
        {
            "IVE": [0.25],
        }
    )

    result = (
        chart_data.identify_infrastructure_column(
            dataframe
        )
    )

    assert result is None


# =============================================================================
# DISTRIBUIÇÃO DO IVE
# =============================================================================


def test_prepare_distribution_data_returns_expected_counts(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    Deve calcular corretamente a quantidade por categoria.
    """
    result = chart_data.prepare_distribution_data(
        complete_dataframe
    )

    counts = result.set_index(
        "Categoria IVE"
    )["Municípios"]

    assert counts["Baixa"] == 2
    assert counts["Muito baixa"] == 1
    assert counts["Média"] == 1
    assert counts["Alta"] == 1


def test_prepare_distribution_data_removes_empty_categories(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    Não deve manter categorias com quantidade igual a zero.
    """
    result = chart_data.prepare_distribution_data(
        complete_dataframe
    )

    assert (
        "Muito alta"
        not in result["Categoria IVE"].tolist()
    )


def test_prepare_distribution_data_calculates_percentages(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    Os percentuais devem somar aproximadamente 100%.
    """
    result = chart_data.prepare_distribution_data(
        complete_dataframe
    )

    assert result["Percentual"].sum() == pytest.approx(
        100.0
    )

    low_percentage = result.loc[
        result["Categoria IVE"].eq("Baixa"),
        "Percentual",
    ].iloc[0]

    assert low_percentage == pytest.approx(
        40.0
    )


def test_prepare_distribution_data_sorts_descending(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    Deve ordenar as categorias pela quantidade de municípios.
    """
    result = chart_data.prepare_distribution_data(
        complete_dataframe
    )

    quantities = result["Municípios"].tolist()

    assert quantities == sorted(
        quantities,
        reverse=True,
    )


def test_prepare_distribution_data_raises_without_category() -> None:
    """
    Deve falhar quando não existe coluna de categoria.
    """
    dataframe = pd.DataFrame(
        {
            "IVE": [
                0.20,
                0.30,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="não possui uma coluna de categoria",
    ):
        chart_data.prepare_distribution_data(
            dataframe
        )


def test_prepare_distribution_data_raises_without_valid_values() -> None:
    """
    Deve falhar quando todos os valores de categoria são ausentes.
    """
    dataframe = pd.DataFrame(
        {
            "IVE_CATEGORIA": [
                None,
                None,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="Não existem dados suficientes",
    ):
        chart_data.prepare_distribution_data(
            dataframe
        )


# =============================================================================
# SCATTER
# =============================================================================


def test_prepare_scatter_data_returns_expected_structure(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    Deve devolver o DataFrame e os nomes das colunas utilizadas.
    """
    (
        scatter,
        infrastructure_column,
        category_column,
    ) = chart_data.prepare_scatter_data(
        complete_dataframe
    )

    assert len(scatter) == 5
    assert infrastructure_column == "INFRA_MEDIA"
    assert category_column == "IVE_CATEGORIA"


def test_prepare_scatter_data_removes_missing_required_values() -> None:
    """
    Deve remover linhas sem município, infraestrutura ou IVE.
    """
    dataframe = pd.DataFrame(
        {
            "NO_MUNICIPIO": [
                "Município A",
                "Município B",
                "Município C",
            ],
            "IVE": [
                0.20,
                None,
                0.40,
            ],
            "INFRA_MEDIA": [
                0.80,
                0.70,
                None,
            ],
            "IVE_CATEGORIA": [
                "Baixa",
                "Média",
                "Alta",
            ],
        }
    )

    scatter, _, _ = (
        chart_data.prepare_scatter_data(
            dataframe
        )
    )

    assert len(scatter) == 1
    assert (
        scatter["NO_MUNICIPIO"].iloc[0]
        == "Município A"
    )


def test_prepare_scatter_data_creates_default_category() -> None:
    """
    Deve criar categoria N/D quando não há coluna categórica.
    """
    dataframe = pd.DataFrame(
        {
            "NO_MUNICIPIO": [
                "Município A",
                "Município B",
            ],
            "IVE": [
                0.20,
                0.30,
            ],
            "INFRA_MEDIA": [
                0.80,
                0.70,
            ],
        }
    )

    (
        scatter,
        _,
        category_column,
    ) = chart_data.prepare_scatter_data(
        dataframe
    )

    assert category_column == "_CATEGORIA_IVE"
    assert (
        scatter[category_column]
        .eq("N/D")
        .all()
    )


def test_prepare_scatter_data_creates_enrollment_column() -> None:
    """
    Deve criar NUM_MATRICULAS quando a coluna não existe.
    """
    dataframe = pd.DataFrame(
        {
            "NO_MUNICIPIO": [
                "Município A",
                "Município B",
            ],
            "IVE": [
                0.20,
                0.30,
            ],
            "INFRA_MEDIA": [
                0.80,
                0.70,
            ],
        }
    )

    scatter, _, _ = (
        chart_data.prepare_scatter_data(
            dataframe
        )
    )

    assert "NUM_MATRICULAS" in scatter.columns
    assert scatter["NUM_MATRICULAS"].isna().all()


def test_prepare_scatter_data_raises_without_infrastructure() -> None:
    """
    Deve falhar quando não existe coluna de infraestrutura.
    """
    dataframe = pd.DataFrame(
        {
            "NO_MUNICIPIO": ["Município A"],
            "IVE": [0.20],
        }
    )

    with pytest.raises(
        ValueError,
        match="coluna compatível de infraestrutura",
    ):
        chart_data.prepare_scatter_data(
            dataframe
        )


def test_prepare_scatter_data_raises_without_required_column() -> None:
    """
    Deve informar quando falta uma coluna obrigatória.
    """
    dataframe = pd.DataFrame(
        {
            "IVE": [
                0.20,
                0.30,
            ],
            "INFRA_MEDIA": [
                0.80,
                0.70,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="NO_MUNICIPIO",
    ):
        chart_data.prepare_scatter_data(
            dataframe
        )


def test_prepare_scatter_data_raises_when_empty_after_dropna() -> None:
    """
    Deve falhar quando nenhuma linha válida permanece.
    """
    dataframe = pd.DataFrame(
        {
            "NO_MUNICIPIO": [
                "Município A",
                "Município B",
            ],
            "IVE": [
                None,
                None,
            ],
            "INFRA_MEDIA": [
                None,
                None,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="Não existem dados suficientes",
    ):
        chart_data.prepare_scatter_data(
            dataframe
        )


# =============================================================================
# CORRELAÇÃO
# =============================================================================


def test_prepare_correlation_data_returns_square_matrix(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    Deve devolver uma matriz quadrada e rótulos correspondentes.
    """
    matrix, labels = (
        chart_data.prepare_correlation_data(
            complete_dataframe
        )
    )

    assert matrix.shape[0] == matrix.shape[1]
    assert matrix.shape[0] == len(labels)
    assert "IVE" in matrix.columns
    assert "Infraestrutura" in labels


def test_prepare_correlation_data_has_unit_diagonal(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    A diagonal principal da matriz deve ser igual a 1.
    """
    matrix, _ = (
        chart_data.prepare_correlation_data(
            complete_dataframe
        )
    )

    for column in matrix.columns:
        assert matrix.loc[
            column,
            column,
        ] == pytest.approx(1.0)


def test_prepare_correlation_data_removes_constant_columns() -> None:
    """
    Deve remover indicadores sem variação.
    """
    dataframe = pd.DataFrame(
        {
            "IVE": [
                0.10,
                0.20,
                0.30,
                0.40,
            ],
            "INFRA_MEDIA": [
                0.90,
                0.80,
                0.70,
                0.60,
            ],
            "MEDIA_INSE": [
                4.0,
                4.0,
                4.0,
                4.0,
            ],
        }
    )

    matrix, labels = (
        chart_data.prepare_correlation_data(
            dataframe
        )
    )

    assert "MEDIA_INSE" not in matrix.columns
    assert "INSE" not in labels


def test_prepare_correlation_data_raises_with_one_indicator() -> None:
    """
    Deve falhar quando há menos de dois indicadores compatíveis.
    """
    dataframe = pd.DataFrame(
        {
            "IVE": [
                0.10,
                0.20,
                0.30,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="menos de dois indicadores",
    ):
        chart_data.prepare_correlation_data(
            dataframe
        )


def test_prepare_correlation_data_raises_without_variation() -> None:
    """
    Deve falhar quando os indicadores não apresentam variação.
    """
    dataframe = pd.DataFrame(
        {
            "IVE": [
                0.20,
                0.20,
                0.20,
            ],
            "INFRA_MEDIA": [
                0.70,
                0.70,
                0.70,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="variação suficiente",
    ):
        chart_data.prepare_correlation_data(
            dataframe
        )


# =============================================================================
# RESUMOS PARA IA
# =============================================================================


def test_build_distribution_summary_contains_categories(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    Deve gerar um resumo textual com categorias e quantidades.
    """
    result = chart_data.build_distribution_summary(
        complete_dataframe
    )

    assert "Baixa: 2 municípios" in result
    assert "Muito baixa: 1 municípios" in result
    assert "40.0%" in result


def test_build_scatter_summary_contains_statistics(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    Deve incluir correlação, extremos e quantidade de municípios.
    """
    result = chart_data.build_scatter_summary(
        complete_dataframe
    )

    assert (
        "Correlação entre infraestrutura e IVE"
        in result
    )
    assert "IVE mínimo: 0.100" in result
    assert "IVE máximo: 0.500" in result
    assert "Infraestrutura mínima: 0.500" in result
    assert "Infraestrutura máxima: 0.900" in result
    assert "Municípios analisados: 5" in result


def test_build_scatter_summary_calculates_negative_correlation(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    A base simulada deve produzir correlação negativa perfeita.
    """
    result = chart_data.build_scatter_summary(
        complete_dataframe
    )

    assert (
        "Correlação entre infraestrutura e IVE: -1.000"
        in result
    )


def test_build_correlation_summary_contains_ive_relations(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    Deve listar as correlações entre o IVE e os indicadores.
    """
    result = chart_data.build_correlation_summary(
        complete_dataframe
    )

    assert "IVE × Infraestrutura" in result
    assert "IVE × INSE" in result
    assert "IVE × Abandono" in result


def test_build_correlation_summary_raises_without_ive() -> None:
    """
    Deve falhar quando a matriz não contém o IVE.
    """
    dataframe = pd.DataFrame(
        {
            "INFRA_MEDIA": [
                0.90,
                0.80,
                0.70,
                0.60,
            ],
            "MEDIA_INSE": [
                5.0,
                4.8,
                4.5,
                4.2,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="não possui o indicador IVE",
    ):
        chart_data.build_correlation_summary(
            dataframe
        )


def test_build_overview_payload_returns_three_summaries(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    Deve devolver os três resumos utilizados pela análise integrada.
    """
    payload = chart_data.build_overview_payload(
        complete_dataframe
    )

    assert isinstance(payload, tuple)
    assert len(payload) == 3

    distribution_summary = payload[0]
    scatter_summary = payload[1]
    correlation_summary = payload[2]

    assert "Baixa: 2 municípios" in distribution_summary
    assert "IVE mínimo" in scatter_summary
    assert "IVE × Infraestrutura" in correlation_summary


def test_build_overview_payload_returns_strings(
    complete_dataframe: pd.DataFrame,
) -> None:
    """
    Todos os elementos do payload devem ser strings não vazias.
    """
    payload = chart_data.build_overview_payload(
        complete_dataframe
    )

    assert all(
        isinstance(summary, str)
        for summary in payload
    )

    assert all(
        summary.strip()
        for summary in payload
    )
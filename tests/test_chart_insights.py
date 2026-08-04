"""
Testes unitários das análises inteligentes da Visão Geral.

Os testes refletem a arquitetura definida na Sprint 10:
uma única análise integrada para os três gráficos do dashboard.
"""

from __future__ import annotations

from unittest.mock import Mock

import pandas as pd
import pytest

from dashboard.components import chart_insights


@pytest.fixture
def distribution_summary() -> str:
    """
    Retorna um resumo simulado da distribuição do IVE.
    """
    return (
        "Muito baixa: 80 municípios (16,10%)\n"
        "Baixa: 300 municípios (60,36%)\n"
        "Média: 100 municípios (20,12%)\n"
        "Alta: 17 municípios (3,42%)"
    )


@pytest.fixture
def scatter_summary() -> str:
    """
    Retorna um resumo simulado do gráfico de dispersão.
    """
    return (
        "Correlação entre infraestrutura e IVE: -0,612\n"
        "IVE mínimo: 0,057\n"
        "IVE máximo: 0,648\n"
        "Infraestrutura mínima: 0,310\n"
        "Infraestrutura máxima: 0,920\n"
        "Municípios analisados: 497"
    )


@pytest.fixture
def correlation_summary() -> str:
    """
    Retorna um resumo simulado das correlações com o IVE.
    """
    return (
        "IVE × INSE = -0,720\n"
        "IVE × Infraestrutura = -0,610\n"
        "IVE × Abandono = 0,580\n"
        "IVE × Reprovação = 0,440"
    )


def test_format_number_returns_not_available_for_nan() -> None:
    """
    Deve retornar N/D para valores ausentes.
    """
    result = chart_insights.format_number(
        float("nan")
    )

    assert result == "N/D"


def test_format_number_uses_brazilian_format() -> None:
    """
    Deve formatar números com ponto de milhar e vírgula decimal.
    """
    result = chart_insights.format_number(
        1234.567,
        decimals=2,
    )

    assert result == "1.234,57"


def test_format_number_respects_decimal_places() -> None:
    """
    Deve respeitar a quantidade de casas decimais informada.
    """
    result = chart_insights.format_number(
        0.48125,
        decimals=3,
    )

    assert result == "0,481"


def test_build_overview_prompt_contains_distribution_summary(
    distribution_summary: str,
    scatter_summary: str,
    correlation_summary: str,
) -> None:
    """
    Deve incluir o resumo da distribuição no prompt integrado.
    """
    prompt = chart_insights.build_overview_prompt(
        distribution_summary=distribution_summary,
        scatter_summary=scatter_summary,
        correlation_summary=correlation_summary,
    )

    assert distribution_summary in prompt


def test_build_overview_prompt_contains_scatter_summary(
    distribution_summary: str,
    scatter_summary: str,
    correlation_summary: str,
) -> None:
    """
    Deve incluir o resumo do scatter no prompt integrado.
    """
    prompt = chart_insights.build_overview_prompt(
        distribution_summary=distribution_summary,
        scatter_summary=scatter_summary,
        correlation_summary=correlation_summary,
    )

    assert scatter_summary in prompt


def test_build_overview_prompt_contains_correlation_summary(
    distribution_summary: str,
    scatter_summary: str,
    correlation_summary: str,
) -> None:
    """
    Deve incluir o resumo das correlações no prompt integrado.
    """
    prompt = chart_insights.build_overview_prompt(
        distribution_summary=distribution_summary,
        scatter_summary=scatter_summary,
        correlation_summary=correlation_summary,
    )

    assert correlation_summary in prompt


def test_build_overview_prompt_contains_required_sections(
    distribution_summary: str,
    scatter_summary: str,
    correlation_summary: str,
) -> None:
    """
    Deve incluir todas as seções definidas para a resposta da IA.
    """
    prompt = chart_insights.build_overview_prompt(
        distribution_summary=distribution_summary,
        scatter_summary=scatter_summary,
        correlation_summary=correlation_summary,
    )

    assert "### Panorama geral" in prompt
    assert "### Evidências observadas" in prompt
    assert "### Aspectos que merecem atenção" in prompt


def test_build_overview_prompt_contains_safety_instructions(
    distribution_summary: str,
    scatter_summary: str,
    correlation_summary: str,
) -> None:
    """
    Deve orientar a IA a evitar causalidade e linguagem alarmista.
    """
    prompt = chart_insights.build_overview_prompt(
        distribution_summary=distribution_summary,
        scatter_summary=scatter_summary,
        correlation_summary=correlation_summary,
    )

    assert "Não estabeleça relações de causa e efeito" in prompt
    assert "Não utilize linguagem alarmista" in prompt
    assert "Utilize somente os dados apresentados" in prompt


def test_generate_overview_insight_calls_gemini_once(
    monkeypatch: pytest.MonkeyPatch,
    distribution_summary: str,
    scatter_summary: str,
    correlation_summary: str,
) -> None:
    """
    Deve enviar o prompt integrado uma única vez ao serviço Gemini.
    """
    gemini_mock = Mock(
        return_value="Análise integrada gerada"
    )

    monkeypatch.setattr(
        chart_insights,
        "generate_gemini_response",
        gemini_mock,
    )

    result = chart_insights.generate_overview_insight(
        distribution_summary=distribution_summary,
        scatter_summary=scatter_summary,
        correlation_summary=correlation_summary,
    )

    expected_prompt = chart_insights.build_overview_prompt(
        distribution_summary=distribution_summary,
        scatter_summary=scatter_summary,
        correlation_summary=correlation_summary,
    )

    assert result == "Análise integrada gerada"
    gemini_mock.assert_called_once_with(
        expected_prompt
    )


def test_generate_overview_insight_returns_gemini_response(
    monkeypatch: pytest.MonkeyPatch,
    distribution_summary: str,
    scatter_summary: str,
    correlation_summary: str,
) -> None:
    """
    Deve devolver a resposta da Gemini sem alterações.
    """
    expected_response = (
        "### Panorama geral\n\n"
        "Os dados indicam um cenário de atenção."
    )

    monkeypatch.setattr(
        chart_insights,
        "generate_gemini_response",
        lambda prompt: expected_response,
    )

    result = chart_insights.generate_overview_insight(
        distribution_summary=distribution_summary,
        scatter_summary=scatter_summary,
        correlation_summary=correlation_summary,
    )

    assert result == expected_response


def test_build_payload_hash_is_equal_for_identical_dataframes() -> None:
    """
    DataFrames com o mesmo conteúdo devem produzir o mesmo hash.
    """
    first_df = pd.DataFrame(
        {
            "categoria": [
                "Baixa",
                "Média",
            ],
            "quantidade": [
                10,
                5,
            ],
        }
    )

    second_df = first_df.copy()

    first_hash = chart_insights.build_payload_hash(
        first_df
    )
    second_hash = chart_insights.build_payload_hash(
        second_df
    )

    assert first_hash == second_hash


def test_build_payload_hash_changes_when_dataframe_changes() -> None:
    """
    Alterações nos dados devem produzir um hash diferente.
    """
    first_df = pd.DataFrame(
        {
            "categoria": [
                "Baixa",
                "Média",
            ],
            "quantidade": [
                10,
                5,
            ],
        }
    )

    second_df = pd.DataFrame(
        {
            "categoria": [
                "Baixa",
                "Média",
            ],
            "quantidade": [
                11,
                5,
            ],
        }
    )

    first_hash = chart_insights.build_payload_hash(
        first_df
    )
    second_hash = chart_insights.build_payload_hash(
        second_df
    )

    assert first_hash != second_hash


def test_build_payload_hash_is_equal_for_identical_payloads() -> None:
    """
    Payloads integrados idênticos devem gerar o mesmo hash.
    """
    payload = (
        "Resumo da distribuição",
        "Resumo do scatter",
        "Resumo das correlações",
    )

    first_hash = chart_insights.build_payload_hash(
        payload
    )
    second_hash = chart_insights.build_payload_hash(
        payload
    )

    assert first_hash == second_hash


def test_build_payload_hash_changes_when_filter_results_change() -> None:
    """
    Mudanças nos resumos decorrentes dos filtros devem alterar o hash.
    """
    first_payload = (
        "Baixa: 300 municípios",
        "Correlação: -0,612",
        "IVE × INSE = -0,720",
    )

    second_payload = (
        "Baixa: 200 municípios",
        "Correlação: -0,450",
        "IVE × INSE = -0,600",
    )

    first_hash = chart_insights.build_payload_hash(
        first_payload
    )
    second_hash = chart_insights.build_payload_hash(
        second_payload
    )

    assert first_hash != second_hash


def test_build_payload_hash_returns_string() -> None:
    """
    O hash deve ser retornado como uma string não vazia.
    """
    payload = (
        "Distribuição",
        "Scatter",
        "Correlação",
    )

    result = chart_insights.build_payload_hash(
        payload
    )

    assert isinstance(result, str)
    assert result
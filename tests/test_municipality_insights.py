"""
Testes unitários das análises inteligentes do diagnóstico municipal.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from dashboard.components import municipality_insights


@pytest.fixture
def complete_municipality() -> dict[str, object]:
    """
    Retorna um município com todos os indicadores preenchidos.
    """
    return {
        "NO_MUNICIPIO": "Município de teste",
        "IVE": 0.481,
        "IVE_CATEGORIA": "Alta",
        "RANK_VULNERABILIDADE": 5,
        "INFRA_MEDIA": 0.412,
        "MEDIA_INSE": 4.02,
        "ABANDONO_EM": 7.8,
        "REPROVACAO_EM": 12.3,
        "APROVACAO_EM": 79.9,
        "DISTORCAO_EM": 18.6,
        "NUM_ESCOLAS": 25,
        "NUM_MATRICULAS": 8500,
    }


def test_format_number_returns_not_available_for_none() -> None:
    """
    Deve retornar 'Não disponível' para valores nulos.
    """
    result = municipality_insights.format_number(None)

    assert result == "Não disponível"


def test_format_number_returns_not_available_for_nan() -> None:
    """
    Deve retornar 'Não disponível' para valores NaN.
    """
    result = municipality_insights.format_number(float("nan"))

    assert result == "Não disponível"


def test_format_number_returns_not_available_for_invalid_value() -> None:
    """
    Deve retornar 'Não disponível' para valores não numéricos.
    """
    result = municipality_insights.format_number("valor inválido")

    assert result == "Não disponível"


def test_format_number_uses_brazilian_decimal_format() -> None:
    """
    Deve formatar números com vírgula decimal e ponto de milhar.
    """
    result = municipality_insights.format_number(
        1234.567,
        decimals=2,
    )

    assert result == "1.234,57"


def test_format_number_adds_suffix() -> None:
    """
    Deve acrescentar corretamente o sufixo informado.
    """
    result = municipality_insights.format_number(
        7.8,
        decimals=2,
        suffix="%",
    )

    assert result == "7,80%"


def test_build_municipality_prompt_contains_name(
    complete_municipality: dict[str, object],
) -> None:
    """
    Deve incluir o nome do município no prompt.
    """
    prompt = municipality_insights.build_municipality_prompt(
        complete_municipality
    )

    assert "Município de teste" in prompt


def test_build_municipality_prompt_contains_indicators(
    complete_municipality: dict[str, object],
) -> None:
    """
    Deve incluir os principais indicadores formatados no prompt.
    """
    prompt = municipality_insights.build_municipality_prompt(
        complete_municipality
    )

    assert "0,481" in prompt
    assert "Alta" in prompt
    assert "0,412" in prompt
    assert "4,02" in prompt
    assert "7,80%" in prompt
    assert "12,30%" in prompt
    assert "79,90%" in prompt
    assert "18,60%" in prompt
    assert "25" in prompt
    assert "8.500" in prompt


def test_build_municipality_prompt_contains_required_sections(
    complete_municipality: dict[str, object],
) -> None:
    """
    Deve incluir todas as seções obrigatórias da resposta.
    """
    prompt = municipality_insights.build_municipality_prompt(
        complete_municipality
    )

    assert "### Diagnóstico" in prompt
    assert "### Evidências observadas" in prompt
    assert "### Prioridades para a gestão" in prompt


def test_build_municipality_prompt_handles_missing_values() -> None:
    """
    Deve representar indicadores ausentes como 'Não disponível'.
    """
    municipality = {
        "NO_MUNICIPIO": "Município incompleto",
        "IVE": None,
        "IVE_CATEGORIA": None,
        "RANK_VULNERABILIDADE": None,
    }

    prompt = municipality_insights.build_municipality_prompt(
        municipality
    )

    assert "Município incompleto" in prompt
    assert "Não disponível" in prompt


def test_build_municipality_prompt_uses_default_name() -> None:
    """
    Deve usar um nome padrão quando o município não for informado.
    """
    prompt = municipality_insights.build_municipality_prompt({})

    assert "Município não identificado" in prompt


def test_generate_municipality_insight_calls_gemini(
    monkeypatch: pytest.MonkeyPatch,
    complete_municipality: dict[str, object],
) -> None:
    """
    Deve enviar o prompt construído exatamente uma vez ao serviço Gemini.
    """
    gemini_mock = Mock(
        return_value="Análise gerada"
    )

    monkeypatch.setattr(
        municipality_insights,
        "generate_gemini_response",
        gemini_mock,
    )

    result = municipality_insights.generate_municipality_insight(
        complete_municipality
    )

    expected_prompt = municipality_insights.build_municipality_prompt(
        complete_municipality
    )

    assert result == "Análise gerada"
    gemini_mock.assert_called_once_with(expected_prompt)


def test_generate_municipality_insight_returns_gemini_response(
    monkeypatch: pytest.MonkeyPatch,
    complete_municipality: dict[str, object],
) -> None:
    """
    Deve devolver sem alterações a resposta retornada pelo serviço Gemini.
    """
    expected_response = (
        "### Diagnóstico\n\n"
        "Os dados indicam um cenário de atenção."
    )

    monkeypatch.setattr(
        municipality_insights,
        "generate_gemini_response",
        lambda prompt: expected_response,
    )

    result = municipality_insights.generate_municipality_insight(
        complete_municipality
    )

    assert result == expected_response
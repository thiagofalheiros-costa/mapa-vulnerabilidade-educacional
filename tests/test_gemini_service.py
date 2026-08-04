"""
Testes unitários do serviço de integração com a Gemini API.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from dashboard.components import gemini_service


@pytest.fixture(autouse=True)
def clear_gemini_cache() -> None:
    """
    Limpa o cache antes e depois de cada teste.

    Isso garante independência entre os casos de teste.
    """
    gemini_service.generate_gemini_response.clear()

    yield

    gemini_service.generate_gemini_response.clear()


def test_get_gemini_client_raises_error_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Deve informar claramente quando a chave da API não está configurada.
    """
    monkeypatch.delenv(
        "GEMINI_API_KEY",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="GEMINI_API_KEY",
    ):
        gemini_service.get_gemini_client()


def test_get_gemini_client_uses_environment_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Deve criar o cliente utilizando a chave definida no ambiente.
    """
    fake_client = object()
    client_constructor = Mock(
        return_value=fake_client
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-api-key",
    )
    monkeypatch.setattr(
        gemini_service.genai,
        "Client",
        client_constructor,
    )

    result = gemini_service.get_gemini_client()

    assert result is fake_client
    client_constructor.assert_called_once_with(
        api_key="test-api-key"
    )


@pytest.mark.parametrize(
    "prompt",
    [
        "",
        "   ",
        "\n\t",
    ],
)
def test_generate_gemini_response_rejects_empty_prompt(
    prompt: str,
) -> None:
    """
    Deve rejeitar prompts vazios ou formados apenas por espaços.
    """
    with pytest.raises(
    ValueError,
    match="prompt enviado para o Gemini está vazio",
    ):
        gemini_service.generate_gemini_response(
            prompt
        )


def test_generate_gemini_response_returns_stripped_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Deve devolver o texto da API sem espaços nas extremidades.
    """
    create_mock = Mock(
        return_value=SimpleNamespace(
            output_text="  integração funcionando.  "
        )
    )
    fake_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=create_mock
        )
    )

    monkeypatch.setattr(
        gemini_service,
        "get_gemini_client",
        lambda: fake_client,
    )

    result = gemini_service.generate_gemini_response(
        "Responda com uma frase.",
    )

    assert result == "integração funcionando."
    create_mock.assert_called_once_with(
        model=gemini_service.GEMINI_MODEL,
        input="Responda com uma frase.",
    )


def test_generate_gemini_response_accepts_custom_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Deve encaminhar o modelo informado para a API.
    """
    create_mock = Mock(
        return_value=SimpleNamespace(
            output_text="Resposta"
        )
    )
    fake_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=create_mock
        )
    )

    monkeypatch.setattr(
        gemini_service,
        "get_gemini_client",
        lambda: fake_client,
    )

    result = gemini_service.generate_gemini_response(
        "Prompt de teste",
        model="modelo-de-teste",
    )

    assert result == "Resposta"
    create_mock.assert_called_once_with(
        model="modelo-de-teste",
        input="Prompt de teste",
    )


@pytest.mark.parametrize(
    "output_text",
    [
        None,
        "",
    ],
)
def test_generate_gemini_response_raises_error_without_text(
    monkeypatch: pytest.MonkeyPatch,
    output_text: str | None,
) -> None:
    """
    Deve falhar quando a API não retorna conteúdo textual.
    """
    fake_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=Mock(
                return_value=SimpleNamespace(
                    output_text=output_text
                )
            )
        )
    )

    monkeypatch.setattr(
        gemini_service,
        "get_gemini_client",
        lambda: fake_client,
    )

    with pytest.raises(
        RuntimeError,
        match="não retornou conteúdo textual",
    ):
        gemini_service.generate_gemini_response(
            "Prompt válido"
        )


def test_generate_gemini_response_propagates_api_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Deve preservar a exceção original quando a API falha.
    """
    api_error = ConnectionError(
        "Falha de conexão simulada"
    )

    fake_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=Mock(
                side_effect=api_error
            )
        )
    )

    monkeypatch.setattr(
        gemini_service,
        "get_gemini_client",
        lambda: fake_client,
    )

    with pytest.raises(
        ConnectionError,
        match="Falha de conexão simulada",
    ):
        gemini_service.generate_gemini_response(
            "Prompt válido"
        )


def test_generate_gemini_response_uses_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Deve evitar uma segunda chamada à API para o mesmo prompt e modelo.
    """
    create_mock = Mock(
        return_value=SimpleNamespace(
            output_text="Resposta em cache"
        )
    )
    fake_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=create_mock
        )
    )

    monkeypatch.setattr(
        gemini_service,
        "get_gemini_client",
        lambda: fake_client,
    )

    first_result = (
        gemini_service.generate_gemini_response(
            "Mesmo prompt"
        )
    )
    second_result = (
        gemini_service.generate_gemini_response(
            "Mesmo prompt"
        )
    )

    assert first_result == "Resposta em cache"
    assert second_result == "Resposta em cache"
    assert create_mock.call_count == 1


def test_cache_distinguishes_different_prompts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Deve realizar novas chamadas quando o conteúdo do prompt muda.
    """
    create_mock = Mock(
        side_effect=[
            SimpleNamespace(output_text="Resposta A"),
            SimpleNamespace(output_text="Resposta B"),
        ]
    )
    fake_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=create_mock
        )
    )

    monkeypatch.setattr(
        gemini_service,
        "get_gemini_client",
        lambda: fake_client,
    )

    first_result = (
        gemini_service.generate_gemini_response(
            "Prompt A"
        )
    )
    second_result = (
        gemini_service.generate_gemini_response(
            "Prompt B"
        )
    )

    assert first_result == "Resposta A"
    assert second_result == "Resposta B"
    assert create_mock.call_count == 2
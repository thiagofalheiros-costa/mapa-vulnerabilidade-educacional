"""
Serviços de integração com a Gemini API.

Este módulo é responsável apenas pela comunicação com a API.
A construção dos prompts fica a cargo dos módulos especializados
(ex.: municipality_insights.py e chart_insights.py).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from time import perf_counter

import streamlit as st
from dotenv import load_dotenv
from google import genai

# =============================================================================
# Configuração
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)

GEMINI_MODEL = "gemini-3.6-flash"

logger = logging.getLogger(__name__)


# =============================================================================
# Cliente
# =============================================================================

def get_gemini_client() -> genai.Client:
    """
    Cria e retorna o cliente da Gemini API.

    Raises
    ------
    ValueError
        Caso a variável GEMINI_API_KEY não esteja configurada.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.error(
            "Falha ao criar cliente Gemini: variável "
            "GEMINI_API_KEY ausente."
        )

        raise ValueError(
            "A variável GEMINI_API_KEY não foi encontrada. "
            f"Verifique o arquivo: {ENV_PATH}"
        )

    logger.debug(
        "Criando cliente Gemini."
    )

    return genai.Client(
        api_key=api_key
    )


# =============================================================================
# Geração de respostas
# =============================================================================

@st.cache_data(
    show_spinner=False,
    ttl=3600,
)
def generate_gemini_response(
    prompt: str,
    *,
    model: str = GEMINI_MODEL,
) -> str:
    """
    Envia um prompt para a Gemini API.

    As respostas são armazenadas em cache durante uma hora.
    Caso o mesmo prompt seja enviado novamente, a resposta é
    recuperada do cache, evitando uma nova chamada à API.

    Parameters
    ----------
    prompt
        Prompt completo.
    model
        Modelo da Gemini utilizado.

    Returns
    -------
    str
        Texto retornado pela API.
    """
    if not prompt.strip():
        logger.warning(
            "Tentativa de chamada à Gemini com prompt vazio."
        )

        raise ValueError(
            "O prompt enviado para o Gemini está vazio."
        )

    start_time = perf_counter()

    logger.info(
        "Iniciando chamada à Gemini. "
        "modelo=%s tamanho_prompt=%s",
        model,
        len(prompt),
    )

    try:
        client = get_gemini_client()

        interaction = client.interactions.create(
            model=model,
            input=prompt,
        )

        response_text = interaction.output_text

        if not response_text:
            raise RuntimeError(
                "A Gemini API não retornou conteúdo textual."
            )

        cleaned_response = response_text.strip()
        elapsed_time = perf_counter() - start_time

        logger.info(
            "Chamada à Gemini concluída. "
            "modelo=%s tempo_segundos=%.3f "
            "tamanho_resposta=%s",
            model,
            elapsed_time,
            len(cleaned_response),
        )

        return cleaned_response

    except Exception:
        elapsed_time = perf_counter() - start_time

        logger.exception(
            "Falha na chamada à Gemini. "
            "modelo=%s tempo_segundos=%.3f "
            "tamanho_prompt=%s",
            model,
            elapsed_time,
            len(prompt),
        )

        raise
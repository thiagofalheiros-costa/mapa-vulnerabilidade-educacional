"""
Serviços de integração com a Gemini API.

Este módulo é responsável apenas pela comunicação com a API.
A construção dos prompts fica a cargo dos módulos especializados
(ex.: municipality_insights.py e chart_insights.py).
"""

from __future__ import annotations

import os
from pathlib import Path

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
        raise ValueError(
            "A variável GEMINI_API_KEY não foi encontrada. "
            f"Verifique o arquivo: {ENV_PATH}"
        )

    return genai.Client(api_key=api_key)


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
        raise ValueError(
            "O prompt enviado para o Gemini está vazio."
        )

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

    return response_text.strip()
"""
Análises inteligentes dos gráficos do dashboard.

Responsável pela construção dos prompts enviados ao Gemini
e pela interface reutilizável de geração das análises.
"""


from __future__ import annotations

import hashlib
import logging

import pandas as pd
import streamlit as st

from .gemini_service import generate_gemini_response

logger = logging.getLogger(__name__)

def format_number(
    value: object,
    decimals: int = 2,
) -> str:
    """Formata números no padrão brasileiro."""
    if pd.isna(value):
        return "N/D"

    return (
        f"{float(value):,.{decimals}f}"
        .replace(",", "TEMP")
        .replace(".", ",")
        .replace("TEMP", ".")
    )



# =============================================================================
# VISÃO GERAL
# =============================================================================


def build_overview_prompt(
    distribution_summary: str,
    scatter_summary: str,
    correlation_summary: str,
) -> str:
    """
    Constrói o prompt da análise integrada da Visão Geral.
    """

    return f"""
Você atua como especialista em políticas públicas educacionais.

Sua tarefa é produzir uma interpretação integrada da situação dos
municípios do Rio Grande do Sul a partir do painel Visão Geral do
Mapa da Vulnerabilidade Educacional.

IMPORTANTE

- Utilize somente os dados apresentados.
- Não explique como os gráficos funcionam.
- Não repita números desnecessariamente.
- Não estabeleça relações de causa e efeito.
- Não utilize linguagem alarmista.
- Escreva como um analista experiente orientando gestores públicos.

DISTRIBUIÇÃO DO IVE

{distribution_summary}

------------------------------------------------------------

RELAÇÃO ENTRE INFRAESTRUTURA E IVE

{scatter_summary}

------------------------------------------------------------

CORRELAÇÕES ENTRE OS INDICADORES

{correlation_summary}

------------------------------------------------------------

Estruture a resposta exatamente assim:

### Panorama geral

Escreva um parágrafo resumindo o cenário observado.

### Evidências observadas

Explique quais padrões aparecem de forma consistente entre os três
gráficos.

### Aspectos que merecem atenção

Apresente três aspectos que podem representar prioridades de
investigação para a gestão educacional.

A resposta deve possuir entre 220 e 320 palavras.
""".strip()


def generate_overview_insight(
    distribution_summary: str,
    scatter_summary: str,
    correlation_summary: str,
) -> str:
    """
    Gera uma interpretação integrada da aba Visão Geral.
    """

    prompt = build_overview_prompt(
        distribution_summary=distribution_summary,
        scatter_summary=scatter_summary,
        correlation_summary=correlation_summary,
    )

    return generate_gemini_response(prompt)

# =============================================================================
# INTERFACE STREAMLIT
# =============================================================================


def build_payload_hash(
    payload: object,
) -> str:
    """
    Gera um hash para identificar mudanças decorrentes
    da aplicação de filtros.
    """

    if isinstance(payload, pd.DataFrame):
        content = payload.to_csv(index=False)

    else:
        content = str(payload)

    return hashlib.md5(
        content.encode("utf-8")
    ).hexdigest()


def render_ai_analysis(
    *,
    title: str,
    payload: object,
    session_prefix: str,
    generator_function,
) -> None:
    """
    Renderiza uma interface padrão para geração de análises
    inteligentes dos gráficos.
    """

    insight_key = f"{session_prefix}_insight"
    hash_key = f"{session_prefix}_hash"

    current_hash = build_payload_hash(payload)

    if hash_key not in st.session_state:
        st.session_state[hash_key] = current_hash

    if insight_key not in st.session_state:
        st.session_state[insight_key] = None

    if st.session_state[hash_key] != current_hash:
        st.session_state[hash_key] = current_hash
        st.session_state[insight_key] = None

    st.markdown("#### ✨ Análise Inteligente")

    st.caption(
        "🤖 Conteúdo gerado automaticamente por IA "
        "a partir dos dados dos gráficos acima."
    )

    if st.button(
        "✨ Gerar análise com IA",
        key=f"{session_prefix}_button",
        type="primary",
        width="stretch",
    ):
        try:
            with st.spinner(
                "Gerando análise..."
            ):
                st.session_state[insight_key] = (
                    generator_function(payload)
                )

        except ValueError as error:
            st.error(str(error))

        except TimeoutError:
            st.warning(
                "A geração da análise demorou mais que o esperado. "
                "Tente novamente em alguns instantes."
            )

        except ConnectionError:
            st.warning(
                "Não foi possível conectar ao serviço de IA. "
                "Verifique sua conexão e tente novamente."
            )

        except Exception:
            logger.exception(
                "Erro ao gerar análise inteligente: %s.",
                title,
            )

            st.warning(
                "Não foi possível gerar a análise automática "
                "neste momento."
            )

    if st.session_state[insight_key]:

        with st.expander(
            "📄 Mostrar análise",
            expanded=True,
        ):

            st.markdown(
                st.session_state[insight_key]
            )

    else:

        st.info(
            "Clique no botão acima para gerar uma análise integrada "
            "dos indicadores apresentados nos gráficos."
        )
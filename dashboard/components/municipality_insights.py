"""
Análises inteligentes para o diagnóstico municipal.

Este módulo é responsável por:

- formatação dos indicadores;
- construção do prompt;
- geração da análise educacional.

Toda a comunicação com a Gemini API é realizada pelo
gemini_service.py.
"""

from __future__ import annotations

from components.gemini_service import generate_gemini_response


def format_number(
    value: object,
    decimals: int = 2,
    suffix: str = "",
) -> str:
    """
    Formata números para o padrão brasileiro.
    """
    if value is None:
        return "Não disponível"

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "Não disponível"

    if numeric_value != numeric_value:
        return "Não disponível"

    formatted = f"{numeric_value:,.{decimals}f}"

    formatted = (
        formatted
        .replace(",", "TEMP")
        .replace(".", ",")
        .replace("TEMP", ".")
    )

    return f"{formatted}{suffix}"


def build_municipality_prompt(
    municipality: dict[str, object],
) -> str:
    """
    Constrói o prompt utilizado pela Gemini.
    """
    municipality_name = str(
        municipality.get(
            "NO_MUNICIPIO",
            "Município não identificado",
        )
    )

    municipality_category = municipality.get(
        "IVE_CATEGORIA",
        "Não disponível",
    )

    return f"""
Você atua como analista de políticas públicas educacionais.

Sua tarefa é interpretar os indicadores de um município do Rio Grande do Sul
a partir do Índice de Vulnerabilidade Educacional (IVE).

Escreva em português brasileiro,
com linguagem técnica acessível,
humana,
pedagógica
e adequada a gestores públicos.

REGRAS

1. Utilize apenas os dados apresentados.
2. Não invente informações.
3. Não estabeleça relações de causa e efeito.
4. Não compare com a média estadual,
exceto quando explicitamente informada.
5. Utilize linguagem prudente.

DADOS

Município:
{municipality_name}

IVE:
{format_number(municipality.get("IVE"),3)}

Categoria:
{municipality_category}

Ranking:
{format_number(
municipality.get("RANK_VULNERABILIDADE"),
0
)}

Infraestrutura:
{format_number(
municipality.get("INFRA_MEDIA"),
3
)}

INSE:
{format_number(
municipality.get("MEDIA_INSE"),
2
)}

Abandono:
{format_number(
municipality.get("ABANDONO_EM"),
suffix="%"
)}

Reprovação:
{format_number(
municipality.get("REPROVACAO_EM"),
suffix="%"
)}

Aprovação:
{format_number(
municipality.get("APROVACAO_EM"),
suffix="%"
)}

Distorção:
{format_number(
municipality.get("DISTORCAO_EM"),
suffix="%"
)}

Escolas:
{format_number(
municipality.get("NUM_ESCOLAS"),
0
)}

Matrículas:
{format_number(
municipality.get("NUM_MATRICULAS"),
0
)}

ESTRUTURA

### Diagnóstico

### Evidências observadas

### Prioridades para a gestão

Entre 180 e 300 palavras.
""".strip()


def generate_municipality_insight(
    municipality: dict[str, object],
) -> str:
    """
    Gera a análise textual do município.
    """
    prompt = build_municipality_prompt(
        municipality
    )

    return generate_gemini_response(
        prompt
    )
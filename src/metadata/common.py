"""
Metadados e constantes compartilhados entre as bases do projeto.

Projeto: Mapa de Vulnerabilidade Educacional
Autor: Thiago Falheiros
"""

# ==========================================================
# Colunas comuns de identificação
# ==========================================================

COL_ANO = "NU_ANO_CENSO"

COL_UF = "SG_UF"

COL_CODIGO_UF = "CO_UF"

COL_MUNICIPIO = "CO_MUNICIPIO"

COL_NOME_MUNICIPIO = "NO_MUNICIPIO"

COL_ESCOLA = "CO_ENTIDADE"

COL_NOME_ESCOLA = "NO_ENTIDADE"


# ==========================================================
# Dependência administrativa
# ==========================================================

DEPENDENCIA_ADMINISTRATIVA = {
    1: "Federal",
    2: "Estadual",
    3: "Municipal",
    4: "Privada",
}

DEPENDENCIAS_PUBLICAS = [1, 2, 3]


# ==========================================================
# Localização
# ==========================================================

LOCALIZACAO = {
    1: "Urbana",
    2: "Rural",
}


# ==========================================================
# Situação de funcionamento
# ==========================================================

SITUACAO_FUNCIONAMENTO = {
    1: "Em atividade",
    2: "Paralisada",
    3: "Extinta no ano do Censo",
    4: "Extinta em anos anteriores",
}

CODIGO_ESCOLA_ATIVA = 1


# ==========================================================
# Configurações territoriais
# ==========================================================

CODIGO_UF_RS = 43

SIGLA_UF_RS = "RS"
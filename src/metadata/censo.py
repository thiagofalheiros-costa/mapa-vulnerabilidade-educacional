"""
Metadados do Censo Escolar.
"""

# ==========================================================
# Identificação
# ==========================================================

IDENTIFICATION_COLUMNS = [
    "NU_ANO_CENSO",
    "CO_ENTIDADE",
    "NO_ENTIDADE",
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "SG_UF",
]

# ==========================================================
# Dependência
# ==========================================================

ADMIN_COLUMNS = [
    "TP_DEPENDENCIA",
    "TP_LOCALIZACAO",
    "TP_SITUACAO_FUNCIONAMENTO",
]

# ==========================================================
# Infraestrutura
# ==========================================================

INFRA_COLUMNS = [
    "IN_AGUA_POTAVEL",
    "IN_ENERGIA_REDE_PUBLICA",
    "IN_ESGOTO_REDE_PUBLICA",
    "IN_BIBLIOTECA",
    "IN_LABORATORIO_INFORMATICA",
    "IN_INTERNET",
    "IN_BANDA_LARGA",
    "IN_QUADRA_ESPORTES",
]

# ==========================================================
# Matrículas do Ensino Médio
# ==========================================================

ENROLLMENT_COLUMNS = [
    "QT_MAT_MED_PROP",
]

# ==========================================================
# Todas as colunas utilizadas
# ==========================================================

CENSO_COLUMNS = (
    IDENTIFICATION_COLUMNS
    + ADMIN_COLUMNS
    + INFRA_COLUMNS
    + ENROLLMENT_COLUMNS
)
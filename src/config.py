"""
Configurações globais do projeto.

Autor: Thiago Falheiros
Projeto: Mapa de Vulnerabilidade Educacional
"""

from pathlib import Path

# ==========================================================
# Diretórios do projeto
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"

REPORTS_DIR = PROJECT_ROOT / "reports"

FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
MAPS_DIR = REPORTS_DIR / "maps"

MODELS_DIR = PROJECT_ROOT / "models"

DOCS_DIR = PROJECT_ROOT / "docs"

# ==========================================================
# Bases de dados
# ==========================================================

CENSO_DIR = RAW_DIR / "censo_escolar"
RENDIMENTO_DIR = RAW_DIR / "rendimento"
DISTORCAO_DIR = RAW_DIR / "distorcao"
INSE_DIR = RAW_DIR / "inse"
IBGE_DIR = RAW_DIR / "ibge"
MALHA_DIR = RAW_DIR / "malha_municipal"

# ==========================================================
# Configurações do projeto
# ==========================================================

ANO_BASE = 2024

UF = "RS"

RANDOM_STATE = 43

ENCODING = "latin1"

CSV_SEPARATOR = ";"

# ==========================================================
# Colunas de identificação
# ==========================================================

COL_ENTIDADE = "CO_ENTIDADE"

COL_MUNICIPIO = "CO_MUNICIPIO"

COL_UF = "SG_UF"

COL_NOME_MUNICIPIO = "NO_MUNICIPIO"

COL_NOME_ESCOLA = "NO_ENTIDADE"

"""
Configurações e caminhos utilizados no projeto.
"""

from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

CENSO_DIR = RAW_DIR / "censo_escolar"

REPORTS_DIR = PROJECT_DIR / "reports"
TABLES_DIR = REPORTS_DIR / "tables"

# Arquivo produzido na sprint anterior.
CENSO_SCHOOLS_PARQUET = INTERIM_DIR / "censo_escolar_2024_escolas.parquet"

# Base analítica municipal produzida na Sprint 4.
MUNICIPALITY_FEATURES_PARQUET = (
    PROCESSED_DIR / "municipios_features.parquet"
)
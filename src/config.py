"""
Configurações globais e caminhos utilizados no projeto.

Autor: Thiago Falheiros
Projeto: Mapa da Vulnerabilidade Educacional
"""

from pathlib import Path

# ==========================================================
# Identificação do projeto
# ==========================================================

ANO_BASE = 2024
UF = "RS"
RANDOM_STATE = 43
ENCODING = "latin1"
CSV_SEPARATOR = ";"

# ==========================================================
# Diretórios principais
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = PROJECT_ROOT

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
# Diretórios das fontes brutas
# Padrão: data/raw/<fonte>/2024
# ==========================================================

CENSO_DIR = RAW_DIR / "censo_escolar" / str(ANO_BASE)
RENDIMENTO_DIR = RAW_DIR / "rendimento" / str(ANO_BASE)
DISTORCAO_DIR = RAW_DIR / "distorcao" / str(ANO_BASE)
INSE_DIR = RAW_DIR / "inse" / str(ANO_BASE)
IBGE_DIR = RAW_DIR / "ibge" / str(ANO_BASE)
MALHA_DIR = RAW_DIR / "malha_municipal" / str(ANO_BASE)

# ==========================================================
# Arquivos brutos utilizados
# ==========================================================

TDI_PATH = DISTORCAO_DIR / "TDI_MUNICIPIOS_2024.xlsx"
RENDIMENTO_PATH = (
    RENDIMENTO_DIR / "tx_rend_municipios_2024.xlsx"
)
INSE_PATH = INSE_DIR / "INSE_2023_municipios.xlsx"
MUNICIPALITY_SHAPEFILE_PATH = (
    MALHA_DIR / "RS_Municipios_2024.shp"
)

# ==========================================================
# Arquivos processados
# ==========================================================

CENSO_PROCESSED_PATH = (
    PROCESSED_DIR / "censo_escolar_rs_2024.parquet"
)
MUNICIPALITY_FEATURES_PATH = (
    PROCESSED_DIR / "municipios_features.parquet"
)
MUNICIPALITY_INDICATORS_PATH = (
    PROCESSED_DIR / "municipality_indicators.parquet"
)
MUNICIPALITY_BASE_PATH = (
    PROCESSED_DIR / "municipality_base.parquet"
)
MUNICIPALITY_FINAL_INDEX_PATH = (
    PROCESSED_DIR / "municipality_vulnerability.parquet"
)
MUNICIPALITY_GEODATA_PATH = (
    PROCESSED_DIR / "municipality_geodata.parquet"
)

# ==========================================================
# Arquivos de saída geoespaciais
# ==========================================================

IVE_CONTINUOUS_MAP_PATH = (
    MAPS_DIR / "ive_municipios_rs_continuo.png"
)
IVE_CATEGORY_MAP_PATH = (
    MAPS_DIR / "ive_municipios_rs_categorias.png"
)
IVE_PRIORITY_MAP_PATH = (
    MAPS_DIR / "ive_municipios_rs_prioritarios.png"
)
IVE_INTERACTIVE_MAP_PATH = (
    MAPS_DIR / "ive_municipios_rs_interativo.html"
)

# ==========================================================
# Colunas de identificação
# ==========================================================

COL_ENTIDADE = "CO_ENTIDADE"
COL_MUNICIPIO = "CO_MUNICIPIO"
COL_UF = "SG_UF"
COL_NOME_MUNICIPIO = "NO_MUNICIPIO"
COL_NOME_ESCOLA = "NO_ENTIDADE"

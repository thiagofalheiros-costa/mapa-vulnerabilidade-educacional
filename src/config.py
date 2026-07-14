
from pathlib import Path

# ============================================================
# Estrutura de diretórios
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"

RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"

MODELS_DIR = ROOT_DIR / "models"

REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
MAPS_DIR = REPORTS_DIR / "maps"
TABLES_DIR = REPORTS_DIR / "tables"

OUTPUT_DIR = ROOT_DIR / "outputs"

# ============================================================
# Criação automática das pastas
# ============================================================

DIRECTORIES = [
    RAW_DIR,
    INTERIM_DIR,
    PROCESSED_DIR,
    EXTERNAL_DIR,
    MODELS_DIR,
    REPORTS_DIR,
    FIGURES_DIR,
    MAPS_DIR,
    TABLES_DIR,
    OUTPUT_DIR
]

for folder in DIRECTORIES:
    folder.mkdir(parents=True, exist_ok=True)
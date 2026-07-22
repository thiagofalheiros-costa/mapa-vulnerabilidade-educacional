from src.config import PROCESSED_DIR
from src.vulnerability_index import save_vulnerability_base

import pandas as pd

municipality_base = pd.read_parquet(
    PROCESSED_DIR / "municipality_base.parquet"
)

result = save_vulnerability_base(
    municipality_base,
    PROCESSED_DIR / "municipality_vulnerability.parquet"
)

print(result[[
    "NO_MUNICIPIO",
    "IVE",
    "IVE_CATEGORIA",
    "RANK_VULNERABILIDADE"
]].head())


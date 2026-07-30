"""
Funções responsáveis pelo carregamento dos dados do dashboard.
"""

from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DATA_CANDIDATES = [
    PROCESSED_DIR / "municipality_vulnerability.parquet",
    PROCESSED_DIR / "municipality_base.parquet",
]


def find_dashboard_data() -> Path:
    """
    Localiza a base municipal utilizada pelo dashboard.

    Returns
    -------
    Path
        Caminho do primeiro arquivo existente entre os candidatos.

    Raises
    ------
    FileNotFoundError
        Caso nenhuma base candidata seja localizada.
    """
    for file_path in DATA_CANDIDATES:
        if file_path.exists():
            return file_path

    expected_files = "\n".join(
        f"- {file_path}" for file_path in DATA_CANDIDATES
    )

    raise FileNotFoundError(
        "Nenhuma base municipal foi localizada.\n"
        "Arquivos procurados:\n"
        f"{expected_files}"
    )


@st.cache_data(show_spinner="Carregando os dados...")
def load_dashboard_data() -> pd.DataFrame:
    """
    Carrega e prepara a base municipal para o dashboard.

    Returns
    -------
    pd.DataFrame
        Base municipal ordenada pelo ranking do IVE.
    """
    file_path = find_dashboard_data()

    df = pd.read_parquet(file_path)

    required_columns = {
        "CO_MUNICIPIO",
        "NO_MUNICIPIO",
        "SG_UF",
        "IVE",
    }

    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))

        raise ValueError(
            "A base não contém todas as colunas obrigatórias. "
            f"Colunas ausentes: {missing_text}"
        )

    df = df.copy()

    df["CO_MUNICIPIO"] = (
        df["CO_MUNICIPIO"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )

    if "IVE_RANK" in df.columns:
        df = df.sort_values("IVE_RANK")
    else:
        df = df.sort_values("IVE", ascending=False)

        df["IVE_RANK"] = (
            df["IVE"]
            .rank(
                method="min",
                ascending=False,
            )
            .astype(int)
        )

    return df.reset_index(drop=True)
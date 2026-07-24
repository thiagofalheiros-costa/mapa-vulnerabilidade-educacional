"""Validação do IVE por Análise de Componentes Principais."""

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from src.logger import setup_logger


logger = setup_logger()

FEATURES = [
    "ABANDONO_EM_NORM",
    "REPROVACAO_EM_NORM",
    "DISTORCAO_EM_NORM",
    "MEDIA_INSE_NORM",
    "INFRA_MEDIA_NORM",
    "MEDIA_MATRICULAS_ESCOLA_NORM",
]

# Todas as colunas entram orientadas para que valores maiores
# representem maior vulnerabilidade.
DIRECTIONS = {
    "ABANDONO_EM_NORM": 1,
    "REPROVACAO_EM_NORM": 1,
    "DISTORCAO_EM_NORM": 1,
    "MEDIA_INSE_NORM": -1,
    "INFRA_MEDIA_NORM": -1,
    "MEDIA_MATRICULAS_ESCOLA_NORM": -1,
}

ID_COLUMNS = ["CO_MUNICIPIO", "NO_MUNICIPIO", "SG_UF"]


def _validate_columns(
    dataframe: pd.DataFrame,
    columns: Sequence[str],
) -> None:
    """Valida a presença e a variabilidade das colunas."""
    missing = [column for column in columns if column not in dataframe.columns]
    if missing:
        raise ValueError(f"Colunas ausentes para PCA: {missing}")

    numeric = dataframe.loc[:, columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    all_missing = numeric.columns[numeric.isna().all()].tolist()
    if all_missing:
        raise ValueError(f"Colunas totalmente nulas: {all_missing}")

    constant = [
        column
        for column in columns
        if numeric[column].nunique(dropna=True) <= 1
    ]
    if constant:
        raise ValueError(f"Colunas sem variância: {constant}")


def _orient_features(
    dataframe: pd.DataFrame,
    columns: Sequence[str],
) -> pd.DataFrame:
    """Orienta as variáveis para a direção da vulnerabilidade."""
    oriented = dataframe.loc[:, columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    for column in columns:
        if DIRECTIONS[column] == -1:
            oriented[column] = 1 - oriented[column]

    return oriented


def _normalize(values: np.ndarray) -> np.ndarray:
    """Normaliza um vetor no intervalo entre zero e um."""
    values = np.asarray(values, dtype=float)
    minimum = np.nanmin(values)
    maximum = np.nanmax(values)

    if np.isclose(minimum, maximum):
        raise ValueError("Não é possível normalizar um vetor constante.")

    return (values - minimum) / (maximum - minimum)


def run_pca_validation(
    dataframe: pd.DataFrame,
    feature_columns: Sequence[str] = FEATURES,
    manual_index_column: str = "IVE",
) -> dict[str, pd.DataFrame]:
    """Executa a PCA e gera um índice municipal alternativo."""
    feature_columns = list(feature_columns)
    _validate_columns(dataframe, feature_columns)

    oriented = _orient_features(dataframe, feature_columns)

    imputer = SimpleImputer(strategy="median")
    imputed = imputer.fit_transform(oriented)

    scaler = StandardScaler()
    standardized = scaler.fit_transform(imputed)

    model = PCA()
    scores = model.fit_transform(standardized)
    first_component = scores[:, 0]

    correlation = np.nan
    if manual_index_column in dataframe.columns:
        manual_index = pd.to_numeric(
            dataframe[manual_index_column],
            errors="coerce",
        )
        valid = manual_index.notna().to_numpy()

        if valid.sum() >= 2:
            correlation = float(
                np.corrcoef(
                    first_component[valid],
                    manual_index.to_numpy()[valid],
                )[0, 1]
            )
            if correlation < 0:
                first_component *= -1
                model.components_[0] *= -1

    ive_pca = _normalize(first_component)

    output_columns = [
        column for column in ID_COLUMNS if column in dataframe.columns
    ]
    if manual_index_column in dataframe.columns:
        output_columns.append(manual_index_column)

    municipality = dataframe.loc[:, output_columns].copy()
    municipality["PCA_SCORE"] = first_component
    municipality["IVE_PCA"] = ive_pca
    municipality["RANK_IVE_PCA"] = (
        municipality["IVE_PCA"]
        .rank(method="min", ascending=False)
        .astype("Int64")
    )

    component_names = [
        f"CP_{number}"
        for number in range(1, len(feature_columns) + 1)
    ]

    loadings = pd.DataFrame(
        model.components_.T,
        columns=component_names,
    )
    loadings.insert(0, "VARIAVEL", feature_columns)

    variance = pd.DataFrame(
        {
            "COMPONENTE": component_names,
            "AUTOVALOR": model.explained_variance_,
            "VARIANCIA_EXPLICADA": model.explained_variance_ratio_,
            "VARIANCIA_EXPLICADA_PERCENTUAL": (
                model.explained_variance_ratio_ * 100
            ),
            "VARIANCIA_ACUMULADA_PERCENTUAL": (
                np.cumsum(model.explained_variance_ratio_) * 100
            ),
        }
    )

    diagnostics = pd.DataFrame(
        {
            "METRICA": [
                "NUM_OBSERVACOES",
                "NUM_VARIAVEIS",
                "CORRELACAO_ORIGINAL_CP1_IVE",
            ],
            "VALOR": [
                len(dataframe),
                len(feature_columns),
                correlation,
            ],
        }
    )

    logger.info(
        "PCA concluída. CP1 explica %.2f%% da variância.",
        variance.loc[0, "VARIANCIA_EXPLICADA_PERCENTUAL"],
    )

    return {
        "municipality_pca": municipality,
        "pca_loadings": loadings,
        "pca_variance": variance,
        "pca_diagnostics": diagnostics,
    }


def execute_pca_pipeline(
    input_path: Path,
    processed_output_path: Path,
    tables_directory: Path,
) -> dict[str, pd.DataFrame]:
    """Lê a base, executa a PCA e salva as saídas."""
    input_path = Path(input_path)
    processed_output_path = Path(processed_output_path)
    tables_directory = Path(tables_directory)

    if not input_path.exists():
        raise FileNotFoundError(f"Base não encontrada: {input_path}")

    dataframe = pd.read_parquet(input_path)
    results = run_pca_validation(dataframe)

    processed_output_path.parent.mkdir(parents=True, exist_ok=True)
    tables_directory.mkdir(parents=True, exist_ok=True)

    results["municipality_pca"].to_parquet(
        processed_output_path,
        index=False,
    )
    results["pca_loadings"].to_csv(
        tables_directory / "pca_loadings.csv",
        index=False,
        encoding="utf-8-sig",
    )
    results["pca_variance"].to_csv(
        tables_directory / "pca_variance.csv",
        index=False,
        encoding="utf-8-sig",
    )
    results["pca_diagnostics"].to_csv(
        tables_directory / "pca_diagnostics.csv",
        index=False,
        encoding="utf-8-sig",
    )

    logger.info("Resultados da PCA salvos com sucesso.")
    return results


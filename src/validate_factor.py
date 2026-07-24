"""
Validação do IVE por análise fatorial exploratória.

Este módulo utiliza apenas NumPy, pandas, SciPy e scikit-learn,
evitando dependência do pacote factor-analyzer.
"""

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.stats import chi2
from sklearn.decomposition import FactorAnalysis
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from src.logger import setup_logger
from src.validate_pca import (
    FEATURES,
    ID_COLUMNS,
    _normalize,
    _orient_features,
    _validate_columns,
)


logger = setup_logger()


def calculate_kmo(
    standardized_features: np.ndarray,
) -> tuple[np.ndarray, float]:
    """
    Calcula o KMO individual e geral.

    O KMO compara as correlações observadas com as correlações
    parciais entre as variáveis.
    """
    correlation_matrix = np.corrcoef(
        standardized_features,
        rowvar=False,
    )

    inverse_correlation = np.linalg.pinv(
        correlation_matrix
    )

    diagonal = np.sqrt(
        np.outer(
            np.diag(inverse_correlation),
            np.diag(inverse_correlation),
        )
    )

    partial_correlation = (
        -inverse_correlation / diagonal
    )

    np.fill_diagonal(
        partial_correlation,
        0.0,
    )

    correlation_squared = (
        correlation_matrix**2
    )

    partial_squared = (
        partial_correlation**2
    )

    np.fill_diagonal(
        correlation_squared,
        0.0,
    )

    numerator_per_variable = (
        correlation_squared.sum(axis=0)
    )

    denominator_per_variable = (
        numerator_per_variable
        + partial_squared.sum(axis=0)
    )

    kmo_per_variable = np.divide(
        numerator_per_variable,
        denominator_per_variable,
        out=np.full_like(
            numerator_per_variable,
            np.nan,
            dtype=float,
        ),
        where=denominator_per_variable != 0,
    )

    total_numerator = (
        correlation_squared.sum()
    )

    total_denominator = (
        total_numerator
        + partial_squared.sum()
    )

    kmo_total = (
        total_numerator / total_denominator
    )

    return kmo_per_variable, float(kmo_total)


def calculate_bartlett_sphericity(
    standardized_features: np.ndarray,
) -> tuple[float, int, float]:
    """
    Executa o teste de esfericidade de Bartlett.

    O teste verifica se a matriz de correlações é diferente
    de uma matriz identidade.
    """
    number_of_observations = (
        standardized_features.shape[0]
    )

    number_of_variables = (
        standardized_features.shape[1]
    )

    correlation_matrix = np.corrcoef(
        standardized_features,
        rowvar=False,
    )

    determinant = np.linalg.det(
        correlation_matrix
    )

    if determinant <= 0:
        determinant = np.finfo(float).eps

    chi_square_value = -(
        number_of_observations
        - 1
        - ((2 * number_of_variables + 5) / 6)
    ) * np.log(determinant)

    degrees_of_freedom = int(
        number_of_variables
        * (number_of_variables - 1)
        / 2
    )

    p_value = chi2.sf(
        chi_square_value,
        degrees_of_freedom,
    )

    return (
        float(chi_square_value),
        degrees_of_freedom,
        float(p_value),
    )


def select_number_of_factors(
    standardized_features: np.ndarray,
) -> tuple[int, np.ndarray]:
    """
    Seleciona fatores pelo critério de Kaiser.

    São retidos os fatores cujos autovalores da matriz de
    correlação são superiores a 1.
    """
    correlation_matrix = np.corrcoef(
        standardized_features,
        rowvar=False,
    )

    eigenvalues = np.linalg.eigvalsh(
        correlation_matrix
    )

    eigenvalues = np.sort(
        eigenvalues
    )[::-1]

    number_of_factors = max(
        1,
        int(np.sum(eigenvalues > 1.0)),
    )

    return number_of_factors, eigenvalues


def calculate_factor_loadings(
    model: FactorAnalysis,
) -> np.ndarray:
    """
    Obtém a matriz de cargas fatoriais.

    No scikit-learn, components_ possui formato:

        fatores × variáveis

    Por isso, a matriz é transposta.
    """
    return model.components_.T.copy()


def calculate_communalities(
    loadings: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calcula comunalidades e unicidades.

    A comunalidade corresponde à soma das cargas quadráticas.
    """
    communalities = np.sum(
        loadings**2,
        axis=1,
    )

    uniquenesses = 1 - communalities

    return communalities, uniquenesses


def orient_factor_solution(
    scores: np.ndarray,
    loadings: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Orienta os fatores para que valores maiores representem
    maior vulnerabilidade.
    """
    orientation = np.where(
        loadings.sum(axis=0) < 0,
        -1,
        1,
    )

    oriented_scores = (
        scores
        * orientation.reshape(1, -1)
    )

    oriented_loadings = (
        loadings
        * orientation.reshape(1, -1)
    )

    return (
        oriented_scores,
        oriented_loadings,
        orientation,
    )


def calculate_factor_variance(
    loadings: np.ndarray,
    number_of_variables: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula a variância explicada pelos fatores.
    """
    sum_squared_loadings = np.sum(
        loadings**2,
        axis=0,
    )

    variance_ratio = (
        sum_squared_loadings
        / number_of_variables
    )

    cumulative_variance = np.cumsum(
        variance_ratio
    )

    return (
        sum_squared_loadings,
        variance_ratio,
        cumulative_variance,
    )


def run_factor_validation(
    dataframe: pd.DataFrame,
    feature_columns: Sequence[str] = FEATURES,
    manual_index_column: str = "IVE",
) -> dict[str, pd.DataFrame]:
    """
    Executa a análise fatorial e gera o IVE fatorial.
    """
    feature_columns = list(
        feature_columns
    )

    _validate_columns(
        dataframe,
        feature_columns,
    )

    oriented_features = _orient_features(
        dataframe,
        feature_columns,
    )

    imputer = SimpleImputer(
        strategy="median"
    )

    imputed_features = imputer.fit_transform(
        oriented_features
    )

    scaler = StandardScaler()

    standardized_features = scaler.fit_transform(
        imputed_features
    )

    (
        kmo_per_variable,
        kmo_total,
    ) = calculate_kmo(
        standardized_features
    )

    (
        bartlett_chi_square,
        bartlett_degrees_of_freedom,
        bartlett_p_value,
    ) = calculate_bartlett_sphericity(
        standardized_features
    )

    (
        number_of_factors,
        eigenvalues,
    ) = select_number_of_factors(
        standardized_features
    )

    model = FactorAnalysis(
        n_components=number_of_factors,
        random_state=42,
    )

    factor_scores = model.fit_transform(
        standardized_features
    )

    factor_loadings = calculate_factor_loadings(
        model
    )

    (
        oriented_scores,
        oriented_loadings,
        factor_orientation,
    ) = orient_factor_solution(
        scores=factor_scores,
        loadings=factor_loadings,
    )

    (
        sum_squared_loadings,
        variance_ratio,
        cumulative_variance,
    ) = calculate_factor_variance(
        loadings=oriented_loadings,
        number_of_variables=len(
            feature_columns
        ),
    )

    weight_sum = variance_ratio.sum()

    if np.isclose(weight_sum, 0.0):
        factor_weights = np.repeat(
            1 / number_of_factors,
            number_of_factors,
        )
    else:
        factor_weights = (
            variance_ratio / weight_sum
        )

    composite_score = (
        oriented_scores
        @ factor_weights
    )

    correlation = np.nan

    if manual_index_column in dataframe.columns:
        manual_index = pd.to_numeric(
            dataframe[manual_index_column],
            errors="coerce",
        )

        valid_mask = (
            manual_index.notna().to_numpy()
            & np.isfinite(composite_score)
        )

        if valid_mask.sum() >= 2:
            correlation = float(
                np.corrcoef(
                    composite_score[valid_mask],
                    manual_index.to_numpy()[
                        valid_mask
                    ],
                )[0, 1]
            )

            if correlation < 0:
                composite_score *= -1

    ive_factor = _normalize(
        composite_score
    )

    output_columns = [
        column
        for column in ID_COLUMNS
        if column in dataframe.columns
    ]

    if manual_index_column in dataframe.columns:
        output_columns.append(
            manual_index_column
        )

    municipality_factor = dataframe.loc[
        :,
        output_columns,
    ].copy()

    for factor_index in range(
        number_of_factors
    ):
        municipality_factor[
            f"FATOR_{factor_index + 1}_SCORE"
        ] = oriented_scores[
            :,
            factor_index,
        ]

    municipality_factor[
        "FACTOR_SCORE"
    ] = composite_score

    municipality_factor[
        "IVE_FACTOR"
    ] = ive_factor

    municipality_factor[
        "RANK_IVE_FACTOR"
    ] = (
        municipality_factor["IVE_FACTOR"]
        .rank(
            method="min",
            ascending=False,
        )
        .astype("Int64")
    )

    factor_names = [
        f"FATOR_{number}"
        for number in range(
            1,
            number_of_factors + 1,
        )
    ]

    loadings_table = pd.DataFrame(
        oriented_loadings,
        columns=factor_names,
    )

    loadings_table.insert(
        0,
        "VARIAVEL",
        feature_columns,
    )

    communalities, uniquenesses = (
        calculate_communalities(
            oriented_loadings
        )
    )

    communalities_table = pd.DataFrame(
        {
            "VARIAVEL": feature_columns,
            "COMUNALIDADE": communalities,
            "UNICIDADE": uniquenesses,
            "KMO_INDIVIDUAL": (
                kmo_per_variable
            ),
        }
    )

    variance_table = pd.DataFrame(
        {
            "FATOR": factor_names,
            "SOMA_CARGAS_QUADRADAS": (
                sum_squared_loadings
            ),
            "VARIANCIA_EXPLICADA": (
                variance_ratio
            ),
            "VARIANCIA_EXPLICADA_PERCENTUAL": (
                variance_ratio * 100
            ),
            "VARIANCIA_ACUMULADA_PERCENTUAL": (
                cumulative_variance * 100
            ),
            "PESO_INDICE": factor_weights,
            "ORIENTACAO": factor_orientation,
        }
    )

    eigenvalues_table = pd.DataFrame(
        {
            "ORDEM": np.arange(
                1,
                len(eigenvalues) + 1,
            ),
            "AUTOVALOR": eigenvalues,
            "RETIDO_KAISER": (
                np.arange(
                    1,
                    len(eigenvalues) + 1,
                )
                <= number_of_factors
            ),
        }
    )

    diagnostics_table = pd.DataFrame(
        {
            "METRICA": [
                "KMO_GERAL",
                "BARTLETT_QUI_QUADRADO",
                "BARTLETT_GRAUS_LIBERDADE",
                "BARTLETT_P_VALOR",
                "NUM_FATORES",
                "CORRELACAO_ORIGINAL_FACTOR_IVE",
            ],
            "VALOR": [
                kmo_total,
                bartlett_chi_square,
                bartlett_degrees_of_freedom,
                bartlett_p_value,
                number_of_factors,
                correlation,
            ],
        }
    )

    logger.info(
        "Análise fatorial concluída: "
        "KMO %.3f; Bartlett p=%.6g; "
        "%s fator(es).",
        kmo_total,
        bartlett_p_value,
        number_of_factors,
    )

    return {
        "municipality_factor": (
            municipality_factor
        ),
        "factor_loadings": (
            loadings_table
        ),
        "factor_communalities": (
            communalities_table
        ),
        "factor_variance": (
            variance_table
        ),
        "factor_eigenvalues": (
            eigenvalues_table
        ),
        "factor_diagnostics": (
            diagnostics_table
        ),
    }


def execute_factor_pipeline(
    input_path: Path,
    processed_output_path: Path,
    tables_directory: Path,
) -> dict[str, pd.DataFrame]:
    """
    Lê a base, executa a análise fatorial e salva as saídas.
    """
    input_path = Path(
        input_path
    )

    processed_output_path = Path(
        processed_output_path
    )

    tables_directory = Path(
        tables_directory
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Base não encontrada: {input_path}"
        )

    dataframe = pd.read_parquet(
        input_path
    )

    if dataframe.empty:
        raise ValueError(
            "A base informada está vazia."
        )

    results = run_factor_validation(
        dataframe
    )

    processed_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    tables_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    results[
        "municipality_factor"
    ].to_parquet(
        processed_output_path,
        index=False,
    )

    output_files = {
        "factor_loadings": (
            "factor_loadings.csv"
        ),
        "factor_communalities": (
            "factor_communalities.csv"
        ),
        "factor_variance": (
            "factor_variance.csv"
        ),
        "factor_eigenvalues": (
            "factor_eigenvalues.csv"
        ),
        "factor_diagnostics": (
            "factor_diagnostics.csv"
        ),
    }

    for result_name, filename in (
        output_files.items()
    ):
        results[result_name].to_csv(
            tables_directory / filename,
            index=False,
            encoding="utf-8-sig",
        )

    logger.info(
        "Resultados da análise fatorial "
        "salvos com sucesso."
    )

    return results
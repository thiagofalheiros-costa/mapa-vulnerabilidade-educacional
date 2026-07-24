"""
Validação do Índice de Vulnerabilidade Educacional por análise fatorial.

Este módulo aplica análise fatorial exploratória às mesmas variáveis
normalizadas utilizadas na validação por PCA.

As principais etapas são:

- orientação das variáveis para vulnerabilidade;
- tratamento de valores ausentes;
- padronização das variáveis;
- cálculo do KMO;
- execução do teste de esfericidade de Bartlett;
- definição do número de fatores;
- estimação das cargas fatoriais;
- cálculo das comunalidades e unicidades;
- geração de um índice fatorial municipal;
- normalização do índice entre zero e um.

A execução deste módulo deve ser controlada pelo main.py.
"""

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import (
    calculate_bartlett_sphericity,
    calculate_kmo,
)
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from src.logger import setup_logger
from src.validate_pca import (
    DEFAULT_PCA_FEATURES,
    IDENTIFICATION_COLUMNS,
    PCA_FEATURE_DIRECTIONS,
    normalize_zero_one,
    orient_features_to_vulnerability,
    validate_numeric_features,
    validate_required_columns,
)


logger = setup_logger()


# A análise fatorial utiliza exatamente as mesmas variáveis da PCA.
DEFAULT_FACTOR_FEATURES = DEFAULT_PCA_FEATURES


def prepare_factor_features(
    dataframe: pd.DataFrame,
    feature_columns: Sequence[str],
    feature_directions: dict[str, int] = PCA_FEATURE_DIRECTIONS,
) -> tuple[
    np.ndarray,
    pd.DataFrame,
    SimpleImputer,
    StandardScaler,
]:
    """
    Prepara as variáveis para a análise fatorial.

    O processamento inclui:

    1. conversão para valores numéricos;
    2. orientação das variáveis para vulnerabilidade;
    3. imputação dos valores ausentes pela mediana;
    4. padronização com média zero e desvio-padrão um.

    Parameters
    ----------
    dataframe:
        Base municipal produzida na Sprint 6.

    feature_columns:
        Variáveis utilizadas na análise fatorial.

    feature_directions:
        Direção conceitual de cada variável em relação à
        vulnerabilidade.

        - 1: valores maiores representam maior vulnerabilidade;
        - -1: valores maiores representam menor vulnerabilidade.

    Returns
    -------
    tuple
        Matriz padronizada, DataFrame com as variáveis orientadas,
        imputador ajustado e padronizador ajustado.
    """
    oriented_features = orient_features_to_vulnerability(
        dataframe=dataframe,
        feature_columns=feature_columns,
        feature_directions=feature_directions,
    )

    imputer = SimpleImputer(strategy="median")

    imputed_features = imputer.fit_transform(
        oriented_features
    )

    scaler = StandardScaler()

    standardized_features = scaler.fit_transform(
        imputed_features
    )

    return (
        standardized_features,
        oriented_features,
        imputer,
        scaler,
    )


def calculate_factorability_statistics(
    standardized_features: np.ndarray,
    feature_columns: Sequence[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calcula o KMO e o teste de esfericidade de Bartlett.

    O KMO avalia se as correlações entre as variáveis são adequadas
    para a aplicação de análise fatorial. Em geral:

    - KMO abaixo de 0,50: inadequado;
    - KMO entre 0,50 e 0,59: fraco;
    - KMO entre 0,60 e 0,69: aceitável;
    - KMO entre 0,70 e 0,79: bom;
    - KMO entre 0,80 e 0,89: muito bom;
    - KMO a partir de 0,90: excelente.

    O teste de Bartlett verifica se a matriz de correlações é
    significativamente diferente de uma matriz identidade. Um valor
    de p inferior a 0,05 favorece a análise fatorial.

    Parameters
    ----------
    standardized_features:
        Matriz de variáveis padronizadas.

    feature_columns:
        Nomes das variáveis utilizadas na análise.

    Returns
    -------
    tuple
        Tabela de estatísticas gerais e tabela com o KMO individual
        de cada variável.
    """
    kmo_per_variable, kmo_total = calculate_kmo(
        standardized_features
    )

    bartlett_chi_square, bartlett_p_value = (
        calculate_bartlett_sphericity(
            standardized_features
        )
    )

    general_statistics = pd.DataFrame(
        {
            "METRICA": [
                "KMO_GERAL",
                "BARTLETT_QUI_QUADRADO",
                "BARTLETT_P_VALOR",
                "NUM_OBSERVACOES",
                "NUM_VARIAVEIS",
            ],
            "VALOR": [
                float(kmo_total),
                float(bartlett_chi_square),
                float(bartlett_p_value),
                int(standardized_features.shape[0]),
                int(standardized_features.shape[1]),
            ],
        }
    )

    variable_kmo = pd.DataFrame(
        {
            "VARIAVEL": list(feature_columns),
            "KMO_INDIVIDUAL": kmo_per_variable,
        }
    )

    return general_statistics, variable_kmo


def determine_number_of_factors(
    standardized_features: np.ndarray,
    maximum_factors: int | None = None,
) -> tuple[int, pd.DataFrame]:
    """
    Determina o número inicial de fatores pelo critério de Kaiser.

    Pelo critério de Kaiser, são retidos os fatores com autovalor
    superior a 1.

    Caso nenhum autovalor seja superior a 1, é mantido pelo menos um
    fator. O número também pode ser limitado por ``maximum_factors``.

    Parameters
    ----------
    standardized_features:
        Matriz padronizada.

    maximum_factors:
        Número máximo de fatores permitido. Quando não informado, o
        limite é igual à quantidade de variáveis.

    Returns
    -------
    tuple
        Número de fatores selecionados e tabela com os autovalores.
    """
    number_of_variables = standardized_features.shape[1]

    initial_analyzer = FactorAnalyzer(
        n_factors=number_of_variables,
        rotation=None,
        method="minres",
    )

    initial_analyzer.fit(standardized_features)

    eigenvalues, common_factor_eigenvalues = (
        initial_analyzer.get_eigenvalues()
    )

    selected_factors = int(
        np.sum(eigenvalues > 1.0)
    )

    selected_factors = max(
        1,
        selected_factors,
    )

    if maximum_factors is not None:
        if maximum_factors < 1:
            raise ValueError(
                "O número máximo de fatores deve ser maior "
                "ou igual a 1."
            )

        selected_factors = min(
            selected_factors,
            maximum_factors,
        )

    selected_factors = min(
        selected_factors,
        number_of_variables,
    )

    eigenvalues_table = pd.DataFrame(
        {
            "FATOR": [
                f"FATOR_{factor_number}"
                for factor_number in range(
                    1,
                    number_of_variables + 1,
                )
            ],
            "AUTOVALOR": eigenvalues,
            "AUTOVALOR_FATOR_COMUM": (
                common_factor_eigenvalues
            ),
            "AUTOVALOR_MAIOR_QUE_UM": (
                eigenvalues > 1.0
            ),
            "FATOR_RETIDO": [
                factor_number <= selected_factors
                for factor_number in range(
                    1,
                    number_of_variables + 1,
                )
            ],
        }
    )

    return selected_factors, eigenvalues_table


def fit_factor_model(
    standardized_features: np.ndarray,
    number_of_factors: int,
) -> tuple[FactorAnalyzer, np.ndarray, str | None]:
    """
    Ajusta o modelo de análise fatorial.

    A rotação Varimax é utilizada quando dois ou mais fatores são
    retidos. Quando apenas um fator é selecionado, nenhuma rotação é
    aplicada.

    Parameters
    ----------
    standardized_features:
        Matriz padronizada.

    number_of_factors:
        Quantidade de fatores que serão estimados.

    Returns
    -------
    tuple
        Modelo ajustado, escores fatoriais e rotação utilizada.
    """
    rotation = (
        "varimax"
        if number_of_factors > 1
        else None
    )

    factor_model = FactorAnalyzer(
        n_factors=number_of_factors,
        rotation=rotation,
        method="minres",
    )

    factor_model.fit(standardized_features)

    factor_scores = factor_model.transform(
        standardized_features
    )

    return factor_model, factor_scores, rotation


def build_factor_loadings_table(
    factor_model: FactorAnalyzer,
    feature_columns: Sequence[str],
    factor_orientation: np.ndarray | None = None,
) -> pd.DataFrame:
    """
    Constrói a tabela de cargas fatoriais.

    Parameters
    ----------
    factor_model:
        Modelo de análise fatorial ajustado.

    feature_columns:
        Variáveis utilizadas na análise.

    factor_orientation:
        Multiplicadores aplicados aos fatores para orientar os
        escores em direção à vulnerabilidade.

    Returns
    -------
    pandas.DataFrame
        Cargas fatoriais por variável e fator.
    """
    loadings = factor_model.loadings_.copy()

    if factor_orientation is not None:
        loadings = (
            loadings
            * factor_orientation.reshape(1, -1)
        )

    factor_names = [
        f"FATOR_{factor_number}"
        for factor_number in range(
            1,
            factor_model.n_factors + 1,
        )
    ]

    loadings_table = pd.DataFrame(
        loadings,
        index=feature_columns,
        columns=factor_names,
    )

    loadings_table = (
        loadings_table
        .reset_index()
        .rename(columns={"index": "VARIAVEL"})
    )

    return loadings_table


def build_communality_table(
    factor_model: FactorAnalyzer,
    feature_columns: Sequence[str],
) -> pd.DataFrame:
    """
    Constrói a tabela de comunalidades e unicidades.

    A comunalidade representa a parcela da variância de cada variável
    explicada pelos fatores retidos. A unicidade representa a parcela
    não explicada pelo modelo.

    Parameters
    ----------
    factor_model:
        Modelo de análise fatorial ajustado.

    feature_columns:
        Variáveis utilizadas na análise.

    Returns
    -------
    pandas.DataFrame
        Comunalidades e unicidades por variável.
    """
    communalities = factor_model.get_communalities()
    uniquenesses = factor_model.get_uniquenesses()

    return pd.DataFrame(
        {
            "VARIAVEL": list(feature_columns),
            "COMUNALIDADE": communalities,
            "UNICIDADE": uniquenesses,
        }
    )


def build_factor_variance_table(
    factor_model: FactorAnalyzer,
) -> pd.DataFrame:
    """
    Constrói a tabela de variância explicada pelos fatores.

    Parameters
    ----------
    factor_model:
        Modelo de análise fatorial ajustado.

    Returns
    -------
    pandas.DataFrame
        Soma das cargas quadráticas, proporção da variância e
        proporção acumulada.
    """
    (
        sum_squared_loadings,
        proportional_variance,
        cumulative_variance,
    ) = factor_model.get_factor_variance()

    return pd.DataFrame(
        {
            "FATOR": [
                f"FATOR_{factor_number}"
                for factor_number in range(
                    1,
                    factor_model.n_factors + 1,
                )
            ],
            "SOMA_CARGAS_QUADRATICAS": (
                sum_squared_loadings
            ),
            "PROPORCAO_VARIANCIA": (
                proportional_variance
            ),
            "PROPORCAO_VARIANCIA_PERCENTUAL": (
                proportional_variance * 100
            ),
            "VARIANCIA_ACUMULADA": (
                cumulative_variance
            ),
            "VARIANCIA_ACUMULADA_PERCENTUAL": (
                cumulative_variance * 100
            ),
        }
    )


def orient_factor_scores(
    factor_scores: np.ndarray,
    factor_model: FactorAnalyzer,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Orienta os fatores para representar vulnerabilidade.

    Como todas as variáveis de entrada já foram orientadas para que
    valores maiores representem maior vulnerabilidade, cada fator é
    orientado a partir da soma de suas cargas.

    Quando a soma das cargas de um fator é negativa, o sinal de seu
    score é invertido.

    Parameters
    ----------
    factor_scores:
        Escores fatoriais de todos os municípios.

    factor_model:
        Modelo fatorial ajustado.

    Returns
    -------
    tuple
        Escores orientados e vetor com os multiplicadores aplicados.
    """
    oriented_scores = np.asarray(
        factor_scores,
        dtype=float,
    ).copy()

    loading_sums = factor_model.loadings_.sum(
        axis=0
    )

    factor_orientation = np.where(
        loading_sums < 0,
        -1,
        1,
    )

    oriented_scores = (
        oriented_scores
        * factor_orientation.reshape(1, -1)
    )

    return oriented_scores, factor_orientation


def build_composite_factor_score(
    oriented_factor_scores: np.ndarray,
    factor_variance_table: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Combina os fatores retidos em um único score municipal.

    Quando mais de um fator é retido, os escores são combinados
    utilizando como peso a proporção da variância explicada por cada
    fator.

    Os pesos são normalizados para que sua soma seja igual a 1.

    Parameters
    ----------
    oriented_factor_scores:
        Escores fatoriais orientados para vulnerabilidade.

    factor_variance_table:
        Tabela com a proporção da variância explicada.

    Returns
    -------
    tuple
        Score fatorial composto e pesos utilizados.
    """
    factor_weights = (
        factor_variance_table[
            "PROPORCAO_VARIANCIA"
        ]
        .to_numpy(dtype=float)
    )

    weight_sum = factor_weights.sum()

    if (
        not np.isfinite(weight_sum)
        or np.isclose(weight_sum, 0.0)
    ):
        logger.warning(
            "Não foi possível utilizar a variância explicada como "
            "peso. Todos os fatores receberão o mesmo peso."
        )

        factor_weights = np.repeat(
            1 / oriented_factor_scores.shape[1],
            oriented_factor_scores.shape[1],
        )

    else:
        factor_weights = (
            factor_weights / weight_sum
        )

    composite_score = (
        oriented_factor_scores
        @ factor_weights
    )

    return composite_score, factor_weights


def orient_composite_score(
    composite_score: np.ndarray,
    reference_index: pd.Series | None = None,
) -> tuple[np.ndarray, int, float | None]:
    """
    Orienta o score composto pela correlação com o IVE manual.

    O sinal das soluções fatoriais é arbitrário. Por isso, quando o
    IVE manual está disponível, o score final é orientado para manter
    correlação positiva com ele.

    Parameters
    ----------
    composite_score:
        Score fatorial municipal.

    reference_index:
        IVE manual produzido na Sprint 6.

    Returns
    -------
    tuple
        Score orientado, multiplicador aplicado e correlação antes da
        eventual inversão.
    """
    oriented_score = np.asarray(
        composite_score,
        dtype=float,
    ).copy()

    if reference_index is None:
        return oriented_score, 1, None

    reference_values = pd.to_numeric(
        reference_index,
        errors="coerce",
    )

    valid_mask = (
        np.isfinite(oriented_score)
        & reference_values.notna().to_numpy()
    )

    if valid_mask.sum() < 2:
        logger.warning(
            "Não há observações válidas suficientes para orientar "
            "o índice fatorial pela correlação com o IVE manual."
        )

        return oriented_score, 1, None

    correlation = np.corrcoef(
        oriented_score[valid_mask],
        reference_values.to_numpy()[valid_mask],
    )[0, 1]

    if np.isnan(correlation):
        logger.warning(
            "A correlação entre o score fatorial e o IVE manual "
            "não pôde ser calculada."
        )

        return oriented_score, 1, None

    if correlation < 0:
        oriented_score *= -1

        return (
            oriented_score,
            -1,
            float(correlation),
        )

    return oriented_score, 1, float(correlation)


def build_factor_weight_table(
    factor_weights: np.ndarray,
    factor_orientation: np.ndarray,
) -> pd.DataFrame:
    """
    Constrói a tabela dos pesos utilizados no índice fatorial.

    Parameters
    ----------
    factor_weights:
        Pesos baseados na variância explicada.

    factor_orientation:
        Multiplicadores usados para orientar os fatores.

    Returns
    -------
    pandas.DataFrame
        Fatores, pesos e orientação.
    """
    return pd.DataFrame(
        {
            "FATOR": [
                f"FATOR_{factor_number}"
                for factor_number in range(
                    1,
                    len(factor_weights) + 1,
                )
            ],
            "PESO_INDICE_FATORIAL": factor_weights,
            "ORIENTACAO": factor_orientation,
        }
    )


def run_factor_validation(
    dataframe: pd.DataFrame,
    feature_columns: Sequence[str] = DEFAULT_FACTOR_FEATURES,
    manual_index_column: str = "IVE",
    minimum_kmo: float = 0.60,
    significance_level: float = 0.05,
    maximum_factors: int | None = None,
) -> dict[str, object]:
    """
    Executa a validação do IVE por análise fatorial.

    Parameters
    ----------
    dataframe:
        Base municipal gerada na Sprint 6.

    feature_columns:
        Variáveis utilizadas na análise fatorial.

    manual_index_column:
        Coluna que contém o IVE manual. Ela é utilizada apenas para
        orientar o sinal do índice fatorial.

    minimum_kmo:
        Valor mínimo de referência para o KMO geral.

    significance_level:
        Nível de significância adotado para o teste de Bartlett.

    maximum_factors:
        Limite opcional para o número de fatores.

    Returns
    -------
    dict
        Resultados completos da análise fatorial.
    """
    feature_columns = list(feature_columns)

    logger.info(
        "Iniciando validação do IVE por análise fatorial."
    )

    validate_required_columns(
        dataframe=dataframe,
        required_columns=feature_columns,
    )

    validate_numeric_features(
        dataframe=dataframe,
        feature_columns=feature_columns,
    )

    (
        standardized_features,
        oriented_features,
        imputer,
        scaler,
    ) = prepare_factor_features(
        dataframe=dataframe,
        feature_columns=feature_columns,
        feature_directions=PCA_FEATURE_DIRECTIONS,
    )

    (
        factor_statistics,
        variable_kmo,
    ) = calculate_factorability_statistics(
        standardized_features=standardized_features,
        feature_columns=feature_columns,
    )

    kmo_total = float(
        factor_statistics.loc[
            factor_statistics["METRICA"] == "KMO_GERAL",
            "VALOR",
        ].iloc[0]
    )

    bartlett_p_value = float(
        factor_statistics.loc[
            factor_statistics["METRICA"]
            == "BARTLETT_P_VALOR",
            "VALOR",
        ].iloc[0]
    )

    logger.info(
        "KMO geral: %.4f.",
        kmo_total,
    )

    logger.info(
        "Teste de Bartlett: p-valor = %.6g.",
        bartlett_p_value,
    )

    if kmo_total < minimum_kmo:
        logger.warning(
            "O KMO geral foi inferior ao valor de referência "
            "de %.2f. A solução fatorial deve ser interpretada "
            "com cautela.",
            minimum_kmo,
        )

    if bartlett_p_value >= significance_level:
        logger.warning(
            "O teste de Bartlett não foi significativo ao nível "
            "de %.2f. A matriz de correlações pode não ser adequada "
            "para análise fatorial.",
            significance_level,
        )

    (
        number_of_factors,
        factor_eigenvalues,
    ) = determine_number_of_factors(
        standardized_features=standardized_features,
        maximum_factors=maximum_factors,
    )

    logger.info(
        "Número de fatores selecionados pelo critério de Kaiser: %s.",
        number_of_factors,
    )

    (
        factor_model,
        factor_scores,
        rotation,
    ) = fit_factor_model(
        standardized_features=standardized_features,
        number_of_factors=number_of_factors,
    )

    (
        oriented_factor_scores,
        factor_orientation,
    ) = orient_factor_scores(
        factor_scores=factor_scores,
        factor_model=factor_model,
    )

    factor_variance = build_factor_variance_table(
        factor_model=factor_model,
    )

    (
        composite_factor_score,
        factor_weights,
    ) = build_composite_factor_score(
        oriented_factor_scores=oriented_factor_scores,
        factor_variance_table=factor_variance,
    )

    reference_index = (
        dataframe[manual_index_column]
        if manual_index_column in dataframe.columns
        else None
    )

    if reference_index is None:
        logger.warning(
            "A coluna %s não foi encontrada. O índice fatorial "
            "será mantido na orientação definida pelas cargas.",
            manual_index_column,
        )

    (
        oriented_composite_score,
        composite_orientation,
        orientation_correlation,
    ) = orient_composite_score(
        composite_score=composite_factor_score,
        reference_index=reference_index,
    )

    ive_factor = normalize_zero_one(
        oriented_composite_score
    )

    identification_columns = [
        column
        for column in IDENTIFICATION_COLUMNS
        if column in dataframe.columns
    ]

    output_columns = identification_columns.copy()

    if manual_index_column in dataframe.columns:
        output_columns.append(
            manual_index_column
        )

    municipality_factor = dataframe.loc[
        :,
        output_columns,
    ].copy()

    for factor_index in range(
        oriented_factor_scores.shape[1]
    ):
        factor_number = factor_index + 1

        municipality_factor[
            f"FATOR_{factor_number}_SCORE"
        ] = oriented_factor_scores[:, factor_index]

    municipality_factor[
        "FACTOR_SCORE_BRUTO"
    ] = oriented_composite_score

    municipality_factor["IVE_FACTOR"] = ive_factor

    municipality_factor["RANKING_IVE_FACTOR"] = (
        municipality_factor["IVE_FACTOR"]
        .rank(
            method="min",
            ascending=False,
        )
        .astype("Int64")
    )

    factor_loadings = build_factor_loadings_table(
        factor_model=factor_model,
        feature_columns=feature_columns,
        factor_orientation=factor_orientation,
    )

    factor_communalities = build_communality_table(
        factor_model=factor_model,
        feature_columns=feature_columns,
    )

    factor_weights_table = build_factor_weight_table(
        factor_weights=factor_weights,
        factor_orientation=factor_orientation,
    )

    factor_statistics = pd.concat(
        [
            factor_statistics,
            pd.DataFrame(
                {
                    "METRICA": [
                        "NUM_FATORES_RETIDOS",
                        "ROTACAO_VARIMAX",
                        "KMO_MINIMO_REFERENCIA",
                        "NIVEL_SIGNIFICANCIA_BARTLETT",
                        "ORIENTACAO_SCORE_COMPOSTO",
                        "CORRELACAO_ORIGINAL_COM_IVE",
                    ],
                    "VALOR": [
                        number_of_factors,
                        int(rotation == "varimax"),
                        minimum_kmo,
                        significance_level,
                        composite_orientation,
                        (
                            orientation_correlation
                            if orientation_correlation is not None
                            else np.nan
                        ),
                    ],
                }
            ),
        ],
        ignore_index=True,
    )

    logger.info(
        "Análise fatorial concluída com sucesso."
    )

    logger.info(
        "Variância acumulada explicada pelos fatores retidos: "
        "%.2f%%.",
        factor_variance[
            "VARIANCIA_ACUMULADA_PERCENTUAL"
        ].iloc[-1],
    )

    if orientation_correlation is not None:
        logger.info(
            "Correlação original entre o score fatorial e %s: %.4f.",
            manual_index_column,
            orientation_correlation,
        )

    if composite_orientation == -1:
        logger.info(
            "O sinal do score fatorial composto foi invertido para "
            "que valores maiores representem maior vulnerabilidade."
        )

    return {
        "municipality_factor": municipality_factor,
        "factor_loadings": factor_loadings,
        "factor_communalities": factor_communalities,
        "factor_statistics": factor_statistics,
        "factor_variable_kmo": variable_kmo,
        "factor_eigenvalues": factor_eigenvalues,
        "factor_variance": factor_variance,
        "factor_weights": factor_weights_table,
        "factor_model": factor_model,
        "imputer": imputer,
        "scaler": scaler,
        "feature_columns": feature_columns,
        "feature_directions": PCA_FEATURE_DIRECTIONS,
        "oriented_features": oriented_features,
        "number_of_factors": number_of_factors,
        "rotation": rotation,
        "factor_orientation": factor_orientation,
        "composite_orientation": composite_orientation,
        "orientation_correlation": orientation_correlation,
    }


def save_factor_results(
    results: dict[str, object],
    processed_output_path: Path,
    loadings_output_path: Path,
    communalities_output_path: Path,
    statistics_output_path: Path,
    kmo_output_path: Path,
    eigenvalues_output_path: Path,
    variance_output_path: Path,
    weights_output_path: Path,
) -> None:
    """
    Salva os resultados produzidos pela análise fatorial.

    Parameters
    ----------
    results:
        Dicionário retornado por ``run_factor_validation``.

    processed_output_path:
        Arquivo Parquet com o IVE fatorial municipal.

    loadings_output_path:
        CSV com as cargas fatoriais.

    communalities_output_path:
        CSV com as comunalidades e unicidades.

    statistics_output_path:
        CSV com o KMO geral, Bartlett e demais estatísticas.

    kmo_output_path:
        CSV com o KMO individual por variável.

    eigenvalues_output_path:
        CSV com os autovalores utilizados na seleção dos fatores.

    variance_output_path:
        CSV com a variância explicada pelos fatores.

    weights_output_path:
        CSV com os pesos usados na composição do índice fatorial.
    """
    output_paths = [
        Path(processed_output_path),
        Path(loadings_output_path),
        Path(communalities_output_path),
        Path(statistics_output_path),
        Path(kmo_output_path),
        Path(eigenvalues_output_path),
        Path(variance_output_path),
        Path(weights_output_path),
    ]

    for output_path in output_paths:
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    dataframe_results = {
        "municipality_factor": (
            processed_output_path,
            "parquet",
        ),
        "factor_loadings": (
            loadings_output_path,
            "csv",
        ),
        "factor_communalities": (
            communalities_output_path,
            "csv",
        ),
        "factor_statistics": (
            statistics_output_path,
            "csv",
        ),
        "factor_variable_kmo": (
            kmo_output_path,
            "csv",
        ),
        "factor_eigenvalues": (
            eigenvalues_output_path,
            "csv",
        ),
        "factor_variance": (
            variance_output_path,
            "csv",
        ),
        "factor_weights": (
            weights_output_path,
            "csv",
        ),
    }

    for result_name, (
        output_path,
        output_format,
    ) in dataframe_results.items():
        result_dataframe = results[result_name]

        if not isinstance(
            result_dataframe,
            pd.DataFrame,
        ):
            raise TypeError(
                f"O resultado {result_name} deve ser um DataFrame."
            )

        output_path = Path(output_path)

        if output_format == "parquet":
            result_dataframe.to_parquet(
                output_path,
                index=False,
            )

        else:
            result_dataframe.to_csv(
                output_path,
                index=False,
                encoding="utf-8-sig",
            )

        logger.info(
            "Resultado %s salvo em: %s",
            result_name,
            output_path,
        )


def execute_factor_pipeline(
    input_path: Path,
    processed_output_path: Path,
    loadings_output_path: Path,
    communalities_output_path: Path,
    statistics_output_path: Path,
    kmo_output_path: Path,
    eigenvalues_output_path: Path,
    variance_output_path: Path,
    weights_output_path: Path,
    feature_columns: Sequence[str] = DEFAULT_FACTOR_FEATURES,
    manual_index_column: str = "IVE",
    minimum_kmo: float = 0.60,
    significance_level: float = 0.05,
    maximum_factors: int | None = None,
) -> dict[str, object]:
    """
    Lê a base da Sprint 6, executa a análise fatorial e salva as saídas.

    Esta é a função que deverá ser chamada pelo main.py.

    Parameters
    ----------
    input_path:
        Base municipal produzida na Sprint 6.

    processed_output_path:
        Parquet com o IVE fatorial municipal.

    loadings_output_path:
        CSV com as cargas fatoriais.

    communalities_output_path:
        CSV com comunalidades e unicidades.

    statistics_output_path:
        CSV com KMO geral e teste de Bartlett.

    kmo_output_path:
        CSV com KMO individual das variáveis.

    eigenvalues_output_path:
        CSV com os autovalores.

    variance_output_path:
        CSV com a variância explicada.

    weights_output_path:
        CSV com os pesos do índice fatorial.

    feature_columns:
        Variáveis utilizadas no modelo.

    manual_index_column:
        Nome do IVE manual.

    minimum_kmo:
        Valor mínimo de referência para o KMO.

    significance_level:
        Nível de significância de Bartlett.

    maximum_factors:
        Quantidade máxima opcional de fatores.

    Returns
    -------
    dict
        Resultados completos da análise fatorial.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(
            "A base da Sprint 6 não foi encontrada: "
            f"{input_path}"
        )

    logger.info(
        "Lendo base municipal para análise fatorial: %s",
        input_path,
    )

    dataframe = pd.read_parquet(input_path)

    if dataframe.empty:
        raise ValueError(
            "A base informada para análise fatorial está vazia."
        )

    logger.info(
        "Base carregada para análise fatorial: %s linhas e "
        "%s colunas.",
        dataframe.shape[0],
        dataframe.shape[1],
    )

    results = run_factor_validation(
        dataframe=dataframe,
        feature_columns=feature_columns,
        manual_index_column=manual_index_column,
        minimum_kmo=minimum_kmo,
        significance_level=significance_level,
        maximum_factors=maximum_factors,
    )

    save_factor_results(
        results=results,
        processed_output_path=processed_output_path,
        loadings_output_path=loadings_output_path,
        communalities_output_path=communalities_output_path,
        statistics_output_path=statistics_output_path,
        kmo_output_path=kmo_output_path,
        eigenvalues_output_path=eigenvalues_output_path,
        variance_output_path=variance_output_path,
        weights_output_path=weights_output_path,
    )

    logger.info(
        "Pipeline de validação por análise fatorial concluído "
        "com sucesso."
    )

    return results
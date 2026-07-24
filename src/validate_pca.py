"""
Validação do Índice de Vulnerabilidade Educacional por PCA.

Este módulo aplica Análise de Componentes Principais às variáveis
utilizadas na construção do IVE manual.

As principais saídas são:

- índice municipal baseado no primeiro componente principal;
- cargas dos componentes principais;
- variância explicada por componente;
- base municipal com o IVE_PCA.

A execução deste módulo deve ser controlada pelo main.py.
"""

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from src.logger import setup_logger


logger = setup_logger()


# Variáveis utilizadas na construção do índice.
#
DEFAULT_PCA_FEATURES = [
    "ABANDONO_EM_NORM",
    "REPROVACAO_EM_NORM",
    "DISTORCAO_EM_NORM",
    "MEDIA_INSE_NORM",
    "INFRA_MEDIA_NORM",
    "MEDIA_MATRICULAS_ESCOLA_NORM",
]


# Define a direção das variáveis em relação à vulnerabilidade.
#
#  1: valores maiores indicam maior vulnerabilidade.
# -1: valores maiores indicam menor vulnerabilidade e precisam
#     ser invertidos antes da análise.
PCA_FEATURE_DIRECTIONS = {
    "ABANDONO_EM_NORM": 1,
    "REPROVACAO_EM_NORM": 1,
    "DISTORCAO_EM_NORM": 1,
    "MEDIA_INSE_NORM": -1,
    "INFRA_MEDIA_NORM": -1,
    "MEDIA_MATRICULAS_ESCOLA_NORM": -1,
}

IDENTIFICATION_COLUMNS = [
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "SG_UF",
]


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: Sequence[str],
) -> None:
    """
    Valida se todas as colunas obrigatórias estão presentes.

    Parameters
    ----------
    dataframe:
        DataFrame que será validado.

    required_columns:
        Relação de colunas que devem existir na base.

    Raises
    ------
    ValueError
        Quando uma ou mais colunas obrigatórias não forem encontradas.
    """
    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        available_columns = ", ".join(dataframe.columns.astype(str))

        raise ValueError(
            "As seguintes colunas necessárias para a PCA não foram "
            f"encontradas: {missing_columns}. "
            f"Colunas disponíveis: {available_columns}"
        )


def validate_numeric_features(
    dataframe: pd.DataFrame,
    feature_columns: Sequence[str],
) -> None:
    """
    Verifica se as variáveis selecionadas podem ser usadas na PCA.

    Parameters
    ----------
    dataframe:
        Base que contém as variáveis da análise.

    feature_columns:
        Variáveis selecionadas para a PCA.

    Raises
    ------
    ValueError
        Quando uma variável não possui nenhum valor numérico válido
        ou apresenta variância igual a zero.
    """
    invalid_columns: list[str] = []
    constant_columns: list[str] = []

    for column in feature_columns:
        numeric_series = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        if numeric_series.notna().sum() == 0:
            invalid_columns.append(column)
            continue

        if numeric_series.nunique(dropna=True) <= 1:
            constant_columns.append(column)

    if invalid_columns:
        raise ValueError(
            "As seguintes variáveis não possuem valores numéricos "
            f"válidos: {invalid_columns}"
        )

    if constant_columns:
        raise ValueError(
            "As seguintes variáveis apresentam variância igual a zero "
            f"e não podem ser utilizadas na PCA: {constant_columns}"
        )

def orient_features_to_vulnerability(
    dataframe: pd.DataFrame,
    feature_columns: Sequence[str],
    feature_directions: dict[str, int],
) -> pd.DataFrame:
    """
    Orienta todas as variáveis para a mesma direção conceitual.

    Após a transformação, valores maiores devem representar maior
    vulnerabilidade educacional.

    Variáveis com direção igual a -1 são invertidas. Como as colunas
    normalizadas estão no intervalo entre zero e um, a inversão é
    realizada por meio de:

        valor_invertido = 1 - valor_original

    Parameters
    ----------
    dataframe:
        Base municipal com as variáveis normalizadas.

    feature_columns:
        Variáveis utilizadas na PCA.

    feature_directions:
        Dicionário que informa a direção de cada variável:

        - 1: valores maiores representam maior vulnerabilidade;
        - -1: valores maiores representam menor vulnerabilidade.

    Returns
    -------
    pandas.DataFrame
        Variáveis numéricas orientadas para vulnerabilidade.

    Raises
    ------
    ValueError
        Quando uma direção diferente de 1 ou -1 é informada.
    """
    oriented_features = dataframe.loc[:, feature_columns].copy()

    for column in feature_columns:
        oriented_features[column] = pd.to_numeric(
            oriented_features[column],
            errors="coerce",
        )

        direction = feature_directions.get(column, 1)

        if direction not in {-1, 1}:
            raise ValueError(
                f"A direção da variável {column} deve ser 1 ou -1. "
                f"Valor recebido: {direction}"
            )

        if direction == -1:
            oriented_features[column] = (
                1 - oriented_features[column]
            )

    return oriented_features

def prepare_pca_features(
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
    Prepara as variáveis para a Análise de Componentes Principais.

    O processamento inclui:

    1. conversão para valores numéricos;
    2. orientação das variáveis para vulnerabilidade;
    3. imputação dos ausentes pela mediana;
    4. padronização com média zero e desvio-padrão um.

    Parameters
    ----------
    dataframe:
        Base municipal da Sprint 6.

    feature_columns:
        Colunas utilizadas na PCA.

    feature_directions:
        Direção conceitual de cada variável.

    Returns
    -------
    tuple
        Matriz padronizada, variáveis orientadas, imputador ajustado
        e padronizador ajustado.
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

def normalize_zero_one(values: np.ndarray) -> np.ndarray:
    """
    Normaliza uma sequência numérica para o intervalo entre zero e um.

    Parameters
    ----------
    values:
        Valores que serão normalizados.

    Returns
    -------
    numpy.ndarray
        Valores no intervalo [0, 1].

    Raises
    ------
    ValueError
        Quando todos os valores são iguais.
    """
    values = np.asarray(values, dtype=float)

    minimum = np.nanmin(values)
    maximum = np.nanmax(values)

    value_range = maximum - minimum

    if np.isclose(value_range, 0.0):
        raise ValueError(
            "Não foi possível normalizar o score da PCA porque todos "
            "os municípios receberam o mesmo valor."
        )

    return (values - minimum) / value_range


def orient_first_component(
    component_scores: np.ndarray,
    reference_index: pd.Series | None = None,
) -> tuple[np.ndarray, int, float | None]:
    """
    Orienta o primeiro componente para representar vulnerabilidade.

    O sinal dos componentes de uma PCA é arbitrário. Por isso, quando
    o IVE manual é fornecido, o primeiro componente é orientado para
    apresentar correlação positiva com esse índice.

    Caso o índice de referência não seja informado, o componente é
    mantido na orientação original do algoritmo.

    Parameters
    ----------
    component_scores:
        Escores municipais do primeiro componente principal.

    reference_index:
        Índice manual criado na Sprint 6.

    Returns
    -------
    tuple
        Escores orientados, multiplicador aplicado e correlação antes
        da eventual inversão.
    """
    oriented_scores = np.asarray(
        component_scores,
        dtype=float,
    ).copy()

    if reference_index is None:
        return oriented_scores, 1, None

    reference_values = pd.to_numeric(
        reference_index,
        errors="coerce",
    )

    valid_mask = (
        np.isfinite(oriented_scores)
        & reference_values.notna().to_numpy()
    )

    if valid_mask.sum() < 2:
        logger.warning(
            "Não há observações válidas suficientes para orientar "
            "o primeiro componente pela correlação com o IVE manual."
        )

        return oriented_scores, 1, None

    correlation = np.corrcoef(
        oriented_scores[valid_mask],
        reference_values.to_numpy()[valid_mask],
    )[0, 1]

    if np.isnan(correlation):
        logger.warning(
            "A correlação entre o primeiro componente e o IVE manual "
            "não pôde ser calculada."
        )

        return oriented_scores, 1, None

    if correlation < 0:
        oriented_scores *= -1

        return oriented_scores, -1, float(correlation)

    return oriented_scores, 1, float(correlation)


def build_pca_loadings_table(
    pca: PCA,
    feature_columns: Sequence[str],
    orientation_multiplier: int,
) -> pd.DataFrame:
    """
    Constrói a tabela de cargas dos componentes principais.

    As cargas representam a relação entre as variáveis originais
    padronizadas e cada componente principal.

    Parameters
    ----------
    pca:
        Modelo PCA ajustado.

    feature_columns:
        Variáveis utilizadas na análise.

    orientation_multiplier:
        Multiplicador aplicado ao primeiro componente para garantir
        que valores maiores representem maior vulnerabilidade.

    Returns
    -------
    pandas.DataFrame
        Tabela de cargas por variável e componente.
    """
    component_names = [
        f"PC{component_number}"
        for component_number in range(
            1,
            pca.n_components_ + 1,
        )
    ]

    loadings = (
        pca.components_.T
        * np.sqrt(pca.explained_variance_)
    )

    loadings_table = pd.DataFrame(
        loadings,
        index=feature_columns,
        columns=component_names,
    )

    if orientation_multiplier == -1:
        loadings_table["PC1"] *= -1

    loadings_table = (
        loadings_table
        .reset_index()
        .rename(columns={"index": "VARIAVEL"})
    )

    return loadings_table


def build_pca_variance_table(pca: PCA) -> pd.DataFrame:
    """
    Constrói a tabela de variância explicada pela PCA.

    Parameters
    ----------
    pca:
        Modelo PCA ajustado.

    Returns
    -------
    pandas.DataFrame
        Variância individual e acumulada de cada componente.
    """
    explained_variance_ratio = pca.explained_variance_ratio_

    variance_table = pd.DataFrame(
        {
            "COMPONENTE": [
                f"PC{component_number}"
                for component_number in range(
                    1,
                    pca.n_components_ + 1,
                )
            ],
            "AUTOVALOR": pca.explained_variance_,
            "VARIANCIA_EXPLICADA": explained_variance_ratio,
            "VARIANCIA_EXPLICADA_PERCENTUAL": (
                explained_variance_ratio * 100
            ),
            "VARIANCIA_ACUMULADA": np.cumsum(
                explained_variance_ratio
            ),
            "VARIANCIA_ACUMULADA_PERCENTUAL": (
                np.cumsum(explained_variance_ratio) * 100
            ),
        }
    )

    return variance_table


def run_pca_validation(
    dataframe: pd.DataFrame,
    feature_columns: Sequence[str] = DEFAULT_PCA_FEATURES,
    manual_index_column: str = "IVE",
) -> dict[str, object]:
    """
    Executa a validação do IVE por PCA.

    Parameters
    ----------
    dataframe:
        Base municipal gerada na Sprint 6.

    feature_columns:
        Variáveis utilizadas para estimar os componentes principais.

    manual_index_column:
        Nome da coluna que contém o IVE manual. A coluna é usada
        apenas para orientar o sinal do primeiro componente.

    Returns
    -------
    dict
        Resultados da PCA:

        - base municipal com o IVE_PCA;
        - tabela de cargas;
        - tabela de variância;
        - modelo PCA;
        - imputador;
        - padronizador;
        - variáveis utilizadas;
        - correlação de orientação;
        - multiplicador de orientação.
    """
    feature_columns = list(feature_columns)

    logger.info(
        "Iniciando validação do IVE por Análise de Componentes "
        "Principais."
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
) = prepare_pca_features(
    dataframe=dataframe,
    feature_columns=feature_columns,
    feature_directions=PCA_FEATURE_DIRECTIONS,
)

    number_of_components = min(
        standardized_features.shape[0],
        standardized_features.shape[1],
    )

    pca = PCA(
        n_components=number_of_components,
        random_state=42,
    )

    component_matrix = pca.fit_transform(
        standardized_features
    )

    first_component = component_matrix[:, 0]

    reference_index = (
        dataframe[manual_index_column]
        if manual_index_column in dataframe.columns
        else None
    )

    if reference_index is None:
        logger.warning(
            "A coluna %s não foi encontrada. O sinal do primeiro "
            "componente será mantido na orientação original.",
            manual_index_column,
        )

    (
        oriented_first_component,
        orientation_multiplier,
        orientation_correlation,
    ) = orient_first_component(
        component_scores=first_component,
        reference_index=reference_index,
    )

    component_matrix[:, 0] = oriented_first_component

    pca_index = normalize_zero_one(
        oriented_first_component
    )

    identification_columns = [
        column
        for column in IDENTIFICATION_COLUMNS
        if column in dataframe.columns
    ]

    output_columns = identification_columns.copy()

    if manual_index_column in dataframe.columns:
        output_columns.append(manual_index_column)

    pca_base = dataframe.loc[:, output_columns].copy()

    pca_base["PCA_SCORE_BRUTO"] = oriented_first_component
    pca_base["IVE_PCA"] = pca_index
    pca_base["RANKING_IVE_PCA"] = (
        pca_base["IVE_PCA"]
        .rank(
            method="min",
            ascending=False,
        )
        .astype("Int64")
    )

    loadings_table = build_pca_loadings_table(
        pca=pca,
        feature_columns=feature_columns,
        orientation_multiplier=orientation_multiplier,
    )

    variance_table = build_pca_variance_table(pca)

    logger.info(
        "PCA concluída. O primeiro componente explicou %.2f%% "
        "da variância.",
        variance_table.loc[
            variance_table["COMPONENTE"] == "PC1",
            "VARIANCIA_EXPLICADA_PERCENTUAL",
        ].iloc[0],
    )

    if orientation_correlation is not None:
        logger.info(
            "Correlação original entre PC1 e %s: %.4f.",
            manual_index_column,
            orientation_correlation,
        )

    if orientation_multiplier == -1:
        logger.info(
            "O sinal do primeiro componente foi invertido para que "
            "valores maiores representem maior vulnerabilidade."
        )

    return {
        "municipality_pca": pca_base,
        "pca_loadings": loadings_table,
        "pca_variance": variance_table,
        "pca_model": pca,
        "imputer": imputer,
        "scaler": scaler,
        "feature_columns": feature_columns,
        "orientation_multiplier": orientation_multiplier,
        "orientation_correlation": orientation_correlation,
        "oriented_features": oriented_features,
        "feature_directions": PCA_FEATURE_DIRECTIONS,
    }


def save_pca_results(
    results: dict[str, object],
    processed_output_path: Path,
    loadings_output_path: Path,
    variance_output_path: Path,
) -> None:
    """
    Salva os resultados produzidos pela PCA.

    Parameters
    ----------
    results:
        Dicionário retornado por ``run_pca_validation``.

    processed_output_path:
        Caminho do arquivo Parquet com o IVE_PCA.

    loadings_output_path:
        Caminho do CSV com as cargas da PCA.

    variance_output_path:
        Caminho do CSV com a variância explicada.
    """
    processed_output_path = Path(processed_output_path)
    loadings_output_path = Path(loadings_output_path)
    variance_output_path = Path(variance_output_path)

    processed_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    loadings_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    variance_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    municipality_pca = results["municipality_pca"]
    pca_loadings = results["pca_loadings"]
    pca_variance = results["pca_variance"]

    if not isinstance(municipality_pca, pd.DataFrame):
        raise TypeError(
            "O resultado municipality_pca deve ser um DataFrame."
        )

    if not isinstance(pca_loadings, pd.DataFrame):
        raise TypeError(
            "O resultado pca_loadings deve ser um DataFrame."
        )

    if not isinstance(pca_variance, pd.DataFrame):
        raise TypeError(
            "O resultado pca_variance deve ser um DataFrame."
        )

    municipality_pca.to_parquet(
        processed_output_path,
        index=False,
    )

    pca_loadings.to_csv(
        loadings_output_path,
        index=False,
        encoding="utf-8-sig",
    )

    pca_variance.to_csv(
        variance_output_path,
        index=False,
        encoding="utf-8-sig",
    )

    logger.info(
        "Base municipal com PCA salva em: %s",
        processed_output_path,
    )

    logger.info(
        "Cargas da PCA salvas em: %s",
        loadings_output_path,
    )

    logger.info(
        "Variância explicada salva em: %s",
        variance_output_path,
    )


def execute_pca_pipeline(
    input_path: Path,
    processed_output_path: Path,
    loadings_output_path: Path,
    variance_output_path: Path,
    feature_columns: Sequence[str] = DEFAULT_PCA_FEATURES,
    manual_index_column: str = "IVE",
) -> dict[str, object]:
    """
    Lê a base da Sprint 6, executa a PCA e salva os resultados.

    Esta é a função que deverá ser chamada pelo main.py.

    Parameters
    ----------
    input_path:
        Caminho da base produzida na Sprint 6.

    processed_output_path:
        Caminho do Parquet com o resultado municipal da PCA.

    loadings_output_path:
        Caminho do CSV com as cargas dos componentes.

    variance_output_path:
        Caminho do CSV com as variâncias explicadas.

    feature_columns:
        Variáveis utilizadas na PCA.

    manual_index_column:
        Nome da coluna do IVE manual.

    Returns
    -------
    dict
        Resultados completos da PCA.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"A base da Sprint 6 não foi encontrada: {input_path}"
        )

    logger.info(
        "Lendo base municipal para execução da PCA: %s",
        input_path,
    )

    dataframe = pd.read_parquet(input_path)

    if dataframe.empty:
        raise ValueError(
            "A base informada para a PCA está vazia."
        )

    logger.info(
        "Base carregada para a PCA: %s linhas e %s colunas.",
        dataframe.shape[0],
        dataframe.shape[1],
    )

    results = run_pca_validation(
        dataframe=dataframe,
        feature_columns=feature_columns,
        manual_index_column=manual_index_column,
    )

    save_pca_results(
        results=results,
        processed_output_path=processed_output_path,
        loadings_output_path=loadings_output_path,
        variance_output_path=variance_output_path,
    )

    logger.info(
        "Pipeline de validação por PCA concluído com sucesso."
    )

    return results
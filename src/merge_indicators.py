"""
Consolidação dos indicadores educacionais em nível municipal.

Este módulo integra as bases tratadas de rendimento escolar,
INSE e distorção idade-série, preservando os municípios presentes
na base de rendimento.
"""

from pathlib import Path

import pandas as pd

from src.config import MUNICIPALITY_INDICATORS_PATH
from src.load_indicators import load_inse, load_rendimento, load_tdi
from src.logger import setup_logger


logger = setup_logger()


def validate_unique_municipalities(
    dataframe: pd.DataFrame,
    dataset_name: str,
) -> None:
    """
    Verifica se existe apenas uma linha por município.

    Parameters
    ----------
    dataframe:
        Base municipal que será validada.

    dataset_name:
        Nome utilizado na mensagem de erro.

    Raises
    ------
    ValueError
        Caso existam códigos municipais duplicados.
    """
    duplicated = dataframe["CO_MUNICIPIO"].duplicated()

    if duplicated.any():
        duplicated_codes = (
            dataframe.loc[duplicated, "CO_MUNICIPIO"]
            .astype(str)
            .tolist()
        )

        raise ValueError(
            f"A base {dataset_name} possui municípios duplicados: "
            f"{duplicated_codes[:10]}"
        )


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str,
) -> None:
    """
    Verifica a presença das colunas obrigatórias.

    Parameters
    ----------
    dataframe:
        DataFrame que será validado.

    required_columns:
        Lista de colunas obrigatórias.

    dataset_name:
        Nome da base exibido na mensagem de erro.

    Raises
    ------
    ValueError
        Caso alguma coluna obrigatória esteja ausente.
    """
    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"A base {dataset_name} não possui as colunas: "
            f"{missing_columns}"
        )


def build_indicator_dataset(
    uf: str = "RS",
) -> pd.DataFrame:
    """
    Constrói a base consolidada de indicadores municipais.

    A base de rendimento é utilizada como referência territorial,
    pois contém os 497 municípios do Rio Grande do Sul.

    O INSE é incorporado por junção à esquerda. Assim, municípios
    sem informação socioeconômica permanecem na base, com valores
    ausentes em QTD_ALUNOS_INSE e MEDIA_INSE.

    Parameters
    ----------
    uf:
        Sigla da Unidade da Federação.

    Returns
    -------
    pandas.DataFrame
        Base consolidada de indicadores municipais.
    """
    logger.info(
        "Iniciando consolidação dos indicadores municipais de %s.",
        uf,
    )

    rendimento = load_rendimento(uf=uf)
    inse = load_inse(uf=uf)
    tdi = load_tdi(uf=uf)

    validate_unique_municipalities(
        rendimento,
        "rendimento",
    )
    validate_unique_municipalities(
        inse,
        "INSE",
    )
    validate_unique_municipalities(
        tdi,
        "distorção idade-série",
    )

    validate_required_columns(
        rendimento,
        [
            "CO_MUNICIPIO",
            "NO_MUNICIPIO",
            "SG_UF",
            "APROVACAO_EF",
            "APROVACAO_EM",
            "REPROVACAO_EF",
            "REPROVACAO_EM",
            "ABANDONO_EF",
            "ABANDONO_EM",
        ],
        "rendimento",
    )

    validate_required_columns(
        inse,
        [
            "CO_MUNICIPIO",
            "QTD_ALUNOS_INSE",
            "MEDIA_INSE",
        ],
        "INSE",
    )

    validate_required_columns(
        tdi,
        [
            "CO_MUNICIPIO",
            "DISTORCAO_EF",
            "DISTORCAO_EM",
        ],
        "distorção idade-série",
    )

    inse_features = inse[
        [
            "CO_MUNICIPIO",
            "QTD_ALUNOS_INSE",
            "MEDIA_INSE",
        ]
    ].copy()

    tdi_features = tdi[
        [
            "CO_MUNICIPIO",
            "DISTORCAO_EF",
            "DISTORCAO_EM",
        ]
    ].copy()

    indicators = rendimento.merge(
        inse_features,
        on="CO_MUNICIPIO",
        how="left",
        validate="one_to_one",
    )

    indicators = indicators.merge(
        tdi_features,
        on="CO_MUNICIPIO",
        how="left",
        validate="one_to_one",
    )

    indicators = (
        indicators
        .sort_values("CO_MUNICIPIO")
        .reset_index(drop=True)
    )

    if len(indicators) != len(rendimento):
        raise ValueError(
            "A consolidação alterou a quantidade de municípios: "
            f"{len(rendimento)} antes e {len(indicators)} depois."
        )

    validate_unique_municipalities(
        indicators,
        "indicadores consolidados",
    )

    logger.info(
        "Indicadores consolidados: %s municípios e %s colunas.",
        indicators.shape[0],
        indicators.shape[1],
    )

    logger.info(
        "Municípios sem MEDIA_INSE: %s.",
        indicators["MEDIA_INSE"].isna().sum(),
    )

    return indicators


def save_indicator_dataset(
    dataframe: pd.DataFrame,
    output_path: Path = MUNICIPALITY_INDICATORS_PATH,
) -> Path:
    """
    Salva a base consolidada de indicadores em formato Parquet.

    Parameters
    ----------
    dataframe:
        Base consolidada de indicadores.

    output_path:
        Caminho do arquivo de saída.

    Returns
    -------
    pathlib.Path
        Caminho do arquivo salvo.
    """
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_parquet(
        output_path,
        index=False,
    )

    logger.info(
        "Base de indicadores salva em: %s",
        output_path,
    )

    return output_path


def main() -> None:
    """
    Executa a consolidação e salva a base de indicadores.
    """
    indicators = build_indicator_dataset()
    output_path = save_indicator_dataset(indicators)

    print("\nResumo da base de indicadores:\n")
    print(indicators.info())

    print("\nDimensão:")
    print(indicators.shape)

    print("\nValores ausentes:")
    print(
        indicators
        .isna()
        .sum()
        .sort_values(ascending=False)
        .to_string()
    )

    print("\nPrimeiras linhas:")
    print(indicators.head().to_string(index=False))

    print("\nArquivo gerado em:")
    print(output_path)


if __name__ == "__main__":
    main()
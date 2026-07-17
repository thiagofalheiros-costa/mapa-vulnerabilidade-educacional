"""
Pipeline principal do Mapa de Vulnerabilidade Educacional.
"""

from pathlib import Path

from src.aggregation.aggregate_censo import (
    aggregate_by_municipality,
)
from src.config import (
    CENSO_DIR,
    INTERIM_DIR,
    PROCESSED_DIR,
    TABLES_DIR,
    UF,
)
from src.features.censo_features import create_features
from src.inspect_data import (
    find_data_files,
    inspect_directory,
    select_main_data_file,
)
from src.load_data import read_data
from src.logger import setup_logger
from src.preprocess_censo import preprocess_censo
from src.utils import create_directory
from src.validate_censo import validate_censo


logger = setup_logger()


INTERIM_CENSO_PATH = (
    INTERIM_DIR
    / "censo_escolar_rs_2024.parquet"
)

PROCESSED_CENSO_PATH = (
    PROCESSED_DIR
    / "censo_municipio_rs_2024.parquet"
)

QUALITY_REPORT_PATH = (
    TABLES_DIR
    / "qualidade_censo_escolar_rs_2024.csv"
)


def run_inspection() -> None:
    """
    Gera os relatórios de inspeção do Censo Escolar.
    """
    logger.info(
        "Etapa 1: inspeção do Censo Escolar."
    )

    inspect_directory(
        input_directory=CENSO_DIR,
        output_directory=TABLES_DIR,
        sample_size=5_000,
        report_prefix="censo_escolar_2024",
        filename_terms=[
            "microdados_ed_basica_2024",
        ],
    )

    logger.info(
        "Etapa 1 concluída: relatórios de inspeção gerados."
    )


def find_main_census_file() -> Path:
    """
    Localiza o arquivo principal dos microdados do Censo Escolar.

    Returns
    -------
    Path
        Caminho do arquivo principal encontrado.
    """
    files = find_data_files(CENSO_DIR)

    main_file = select_main_data_file(
        files=files,
        filename_terms=[
            "microdados_ed_basica_2024",
        ],
    )

    logger.info(
        "Arquivo principal identificado: %s",
        main_file,
    )

    return main_file


def build_interim_censo() -> None:
    """
    Gera a base escolar intermediária e o relatório de qualidade.
    """
    logger.info(
        "Etapa 2: geração da base intermediária."
    )

    main_file = find_main_census_file()

    df_school = preprocess_censo(
        file_path=main_file,
        uf=UF,
    )

    quality_report = validate_censo(df_school)

    create_directory(INTERIM_DIR)
    create_directory(TABLES_DIR)

    df_school.to_parquet(
        INTERIM_CENSO_PATH,
        index=False,
    )

    quality_report.to_csv(
        QUALITY_REPORT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    logger.info(
        "Base intermediária salva em: %s",
        INTERIM_CENSO_PATH,
    )

    logger.info(
        "Relatório de qualidade salvo em: %s",
        QUALITY_REPORT_PATH,
    )

    logger.info(
        "Etapa 2 concluída: %s escolas processadas.",
        len(df_school),
    )


def build_processed_censo() -> None:
    """
    Cria as features e gera a base municipal processada.
    """
    logger.info(
        "Etapa 3: geração da base municipal."
    )

    if not INTERIM_CENSO_PATH.exists():
        raise FileNotFoundError(
            "A base intermediária não foi encontrada: "
            f"{INTERIM_CENSO_PATH}"
        )

    df_school = read_data(
        file_path=INTERIM_CENSO_PATH,
        normalize=False,
    )

    logger.info(
        "Base intermediária carregada com dimensão: %s",
        df_school.shape,
    )

    df_school = create_features(df_school)

    logger.info(
        "Features escolares criadas com sucesso."
    )

    df_municipality = aggregate_by_municipality(
        df_school
    )

    create_directory(PROCESSED_DIR)

    df_municipality.to_parquet(
        PROCESSED_CENSO_PATH,
        index=False,
    )

    municipality_count = (
        df_municipality["CO_MUNICIPIO"].nunique()
    )

    logger.info(
        "Base municipal salva em: %s",
        PROCESSED_CENSO_PATH,
    )

    logger.info(
        "Etapa 3 concluída: %s municípios processados.",
        municipality_count,
    )

    print("\nDimensão da base municipal:")
    print(df_municipality.shape)

    print("\nQuantidade de municípios:")
    print(municipality_count)

    print("\nPrimeiras linhas:")
    print(
    df_municipality[
        [
            "CO_MUNICIPIO",
            "NO_MUNICIPIO",
            "NUM_ESCOLAS",
            "NUM_MATRICULAS",
            "MEDIA_MATRICULAS_ESCOLA",
            "PERC_PUBLICA",
            "INFRA_MEDIA",
        ]
    ]
    .head()
    .to_string(index=False)
)


def main() -> None:
    """
    Executa o pipeline completo do Censo Escolar.
    """
    logger.info(
        "Iniciando pipeline do Mapa de Vulnerabilidade Educacional."
    )

    run_inspection()
    build_interim_censo()
    build_processed_censo()

    logger.info(
        "Pipeline concluído com sucesso."
    )


if __name__ == "__main__":
    main()
"""
Pipeline principal do Mapa de Vulnerabilidade Educacional.
"""

from src.aggregation.aggregate_censo import aggregate_by_municipality
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


def run_inspection() -> None:
    """
    Gera os relatórios de inspeção do Censo Escolar.
    """
    logger.info("Etapa 1: inspeção do Censo Escolar.")

    inspect_directory(
        input_directory=CENSO_DIR,
        output_directory=TABLES_DIR,
        sample_size=5_000,
        report_prefix="censo_escolar_2024",
        filename_terms=[
            "microdados_ed_basica_2024",
        ],
    )


def build_interim_censo() -> None:
    """
    Gera a base escolar intermediária e o relatório de qualidade.
    """
    logger.info("Etapa 2: geração da base intermediária.")

    files = find_data_files(CENSO_DIR)

    main_file = select_main_data_file(
        files=files,
        filename_terms=[
            "microdados_ed_basica_2024",
        ],
    )

    df_school = preprocess_censo(
        file_path=main_file,
        uf=UF,
    )

    quality_report = validate_censo(df_school)

    create_directory(INTERIM_DIR)
    create_directory(TABLES_DIR)

    interim_path = (
        INTERIM_DIR
        / "censo_escolar_rs_2024.parquet"
    )

    quality_path = (
        TABLES_DIR
        / "qualidade_censo_escolar_rs_2024.csv"
    )

    df_school.to_parquet(
        interim_path,
        index=False,
    )

    quality_report.to_csv(
        quality_path,
        index=False,
        encoding="utf-8-sig",
    )

    logger.info(
        "Base intermediária salva em: %s",
        interim_path,
    )

    logger.info(
        "Relatório de qualidade salvo em: %s",
        quality_path,
    )


def build_processed_censo() -> None:
    """
    Cria as features e gera a base municipal processada.
    """
    logger.info("Etapa 3: geração da base municipal.")

    interim_path = (
        INTERIM_DIR
        / "censo_escolar_rs_2024.parquet"
    )

    processed_path = (
        PROCESSED_DIR
        / "censo_municipio_rs_2024.parquet"
    )

    df_school = read_data(
        file_path=interim_path,
        normalize=False,
    )

    df_school = create_features(df_school)

    df_municipality = aggregate_by_municipality(
        df_school
    )

    create_directory(PROCESSED_DIR)

    df_municipality.to_parquet(
        processed_path,
        index=False,
    )

    logger.info(
        "Base municipal salva em: %s",
        processed_path,
    )

    print("\nDimensão da base municipal:")
    print(df_municipality.shape)

    print("\nQuantidade de municípios:")
    print(
        df_municipality[
            "CO_MUNICIPIO"
        ].nunique()
    )

    print("\nPrimeiras linhas:")
    print(
        df_municipality
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
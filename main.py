"""
Pré-processamento e validação do Censo Escolar.
"""

from src.config import (
    CENSO_DIR,
    INTERIM_DIR,
    TABLES_DIR,
    UF,
)
from src.inspect_data import (
    find_data_files,
    select_main_data_file,
)
from src.logger import setup_logger
from src.metadata.preprocess_censo import preprocess_censo
from src.utils import create_directory
from src.validate_censo import validate_censo


logger = setup_logger()


def main() -> None:
    logger.info(
        "Iniciando pipeline do Censo Escolar."
    )

    files = find_data_files(CENSO_DIR)

    main_file = select_main_data_file(
        files=files,
        filename_terms=[
            "microdados_ed_basica_2024",
        ],
    )

    df = preprocess_censo(
        file_path=main_file,
        uf=UF,
    )

    quality_report = validate_censo(df)

    create_directory(INTERIM_DIR)
    create_directory(TABLES_DIR)

    parquet_path = (
        INTERIM_DIR
        / "censo_escolar_rs_2024.parquet"
    )

    quality_path = (
        TABLES_DIR
        / "qualidade_censo_escolar_rs_2024.csv"
    )

    df.to_parquet(
        parquet_path,
        index=False,
    )

    quality_report.to_csv(
        quality_path,
        index=False,
        encoding="utf-8-sig",
    )

    logger.info(
        "Base intermediária salva em: %s",
        parquet_path,
    )

    logger.info(
        "Relatório de qualidade salvo em: %s",
        quality_path,
    )

    print("\nDimensão da base:")
    print(df.shape)

    print("\nRelatório de qualidade:")
    print(
        quality_report
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
"""Integração da Sprint 7 ao projeto."""

from src.compare_indices import execute_comparison_pipeline
from src.config import PROCESSED_DIR, TABLES_DIR
from src.logger import setup_logger
from src.validate_factor import execute_factor_pipeline
from src.validate_pca import execute_pca_pipeline
from src.validation_report import execute_validation_report


logger = setup_logger()


def run_sprint_7() -> None:
    """Executa toda a validação estatística do IVE."""
    manual_path = PROCESSED_DIR / "municipality_vulnerability.parquet"
    pca_path = PROCESSED_DIR / "municipality_pca.parquet"
    factor_path = PROCESSED_DIR / "municipality_factor.parquet"
    comparison_path = PROCESSED_DIR / "municipality_validation.parquet"

    logger.info("Iniciando Sprint 7: validação estatística do IVE.")

    execute_pca_pipeline(
        input_path=manual_path,
        processed_output_path=pca_path,
        tables_directory=TABLES_DIR,
    )

    execute_factor_pipeline(
        input_path=manual_path,
        processed_output_path=factor_path,
        tables_directory=TABLES_DIR,
    )

    execute_comparison_pipeline(
        manual_path=manual_path,
        pca_path=pca_path,
        factor_path=factor_path,
        processed_output_path=comparison_path,
        tables_directory=TABLES_DIR,
    )

    execute_validation_report(
        tables_directory=TABLES_DIR,
        output_path=TABLES_DIR.parent / "validation_report.md",
    )

    logger.info("Sprint 7 concluída com sucesso.")


if __name__ == "__main__":
    run_sprint_7()
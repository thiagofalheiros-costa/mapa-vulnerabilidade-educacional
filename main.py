"""
Geração dos relatórios de inspeção do Censo Escolar.
"""

from src.config import CENSO_DIR, TABLES_DIR
from src.inspect_data import inspect_directory
from src.logger import setup_logger


logger = setup_logger()


def main() -> None:
    logger.info("Iniciando inspeção do Censo Escolar 2024.")

    reports = inspect_directory(
        input_directory=CENSO_DIR,
        output_directory=TABLES_DIR,
        sample_size=5_000,
        report_prefix="censo_escolar_2024",
        filename_terms=[
            "microdados_ed_basica_2024",
        ],
    )

    print("\nResumo da base:\n")
    print(reports["resumo"].to_string(index=False))

    print("\nArquivos de inspeção recriados em:")
    print(TABLES_DIR)


if __name__ == "__main__":
    main()
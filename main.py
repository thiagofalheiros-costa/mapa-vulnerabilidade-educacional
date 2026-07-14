"""
Ponto de entrada do projeto.
"""

from src.config import CENSO_DIR, TABLES_DIR
from src.inspect_data import inspect_directory
from src.logger import setup_logger


logger = setup_logger()


def main() -> None:
    """
    Executa a inspeção inicial do Censo Escolar.
    """
    logger.info(
        "Iniciando inspeção do Censo Escolar."
    )

    reports = inspect_directory(
        input_directory=CENSO_DIR,
        output_directory=TABLES_DIR,
        sample_size=5_000,
        report_prefix="censo_escolar_2024",
        filename_terms=[
            "microdados",
            "educacao_basica",
            "ed_basica",
        ],
    )

    summary = reports["resumo"]
    columns = reports["colunas"]
    sample = reports["amostra"]

    print("\nResumo da base:\n")
    print(summary.to_string(index=False))

    print("\nPrimeiras 20 colunas do relatório:\n")
    print(columns.head(20).to_string(index=False))

    print("\nAmostra dos dados:\n")
    print(sample.head().to_string(index=False))


if __name__ == "__main__":
    main()
"""
Execução da análise exploratória do Índice de Vulnerabilidade Educacional.

Este script lê a base municipal com o IVE, gera a classificação relativa,
os rankings, as tabelas, os gráficos e a base analítica enriquecida.
"""

from pathlib import Path

import pandas as pd

from src.logger import setup_logger
from src.vulnerability_analysis import run_vulnerability_analysis


logger = setup_logger()

PROJECT_ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
TABLES_DIR = REPORTS_DIR / "tables"
FIGURES_DIR = REPORTS_DIR / "figures"

INPUT_PATH = PROCESSED_DIR / "municipality_vulnerability.parquet"
OUTPUT_PATH = PROCESSED_DIR / "municipality_vulnerability_analysis.parquet"


def main() -> None:
    """Executa a Sprint 7 do início ao fim."""
    logger.info("Iniciando análise exploratória do IVE.")

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "A base com o IVE não foi encontrada. "
            f"Caminho esperado: {INPUT_PATH}"
        )

    municipality_vulnerability = pd.read_parquet(INPUT_PATH)

    logger.info(
        "Base de vulnerabilidade carregada: %s linhas e %s colunas.",
        municipality_vulnerability.shape[0],
        municipality_vulnerability.shape[1],
    )

    outputs = run_vulnerability_analysis(
        dataframe=municipality_vulnerability,
        tables_dir=TABLES_DIR,
        figures_dir=FIGURES_DIR,
        processed_output_path=OUTPUT_PATH,
        top_n=20,
    )

    enriched_data = outputs["enriched_data"]
    summary = outputs["summary"]
    category_distribution = outputs["category_distribution"]
    relative_distribution = outputs["relative_category_distribution"]
    most_vulnerable = outputs["most_vulnerable"]
    correlations = outputs["correlations"]

    logger.info(
        "Base analítica salva em: %s",
        outputs["processed_output_path"],
    )
    logger.info("Tabelas salvas em: %s", TABLES_DIR)
    logger.info("Gráficos salvos em: %s", FIGURES_DIR)

    print("\nResumo da base analítica:")
    print(enriched_data.shape)

    print("\nResumo estatístico do IVE:")
    print(summary.to_string(index=False))

    print("\nDistribuição da categoria absoluta:")
    print(category_distribution.to_string(index=False))

    print("\nDistribuição da categoria relativa:")
    print(relative_distribution.to_string(index=False))

    print("\nTop 20 municípios mais vulneráveis:")
    print(
        most_vulnerable[
            [
                "NO_MUNICIPIO",
                "IVE",
                "IVE_CATEGORIA",
                "IVE_CATEGORIA_RELATIVA",
                "RANK_VULNERABILIDADE",
                "PRINCIPAL_DIMENSAO_VULNERABILIDADE",
            ]
        ].to_string(index=False)
    )

    print("\nCorrelação dos indicadores com o IVE:")
    print(
        correlations["IVE"]
        .drop(labels="IVE")
        .sort_values(ascending=False)
        .to_string()
    )

    print("\nArquivos gerados:")
    for key, value in outputs.items():
        if key.endswith("_path") or key.endswith("_figure"):
            if value is not None:
                print(f"- {value}")

    logger.info("Análise exploratória do IVE concluída com sucesso.")


if __name__ == "__main__":
    main()
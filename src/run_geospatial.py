
"""
Execução da Sprint 8 — Integração geoespacial do IVE.
"""

from src.config import (
    IVE_CATEGORY_MAP_PATH,
    IVE_CONTINUOUS_MAP_PATH,
    IVE_INTERACTIVE_MAP_PATH,
    IVE_PRIORITY_MAP_PATH,
    MAPS_DIR,
    MUNICIPALITY_GEODATA_PATH,
    MUNICIPALITY_FINAL_INDEX_PATH,
    MUNICIPALITY_SHAPEFILE_PATH,
)
from src.geospatial import (
    create_category_ive_map,
    create_continuous_ive_map,
    create_interactive_ive_map,
    create_priority_flag,
    create_priority_map,
    load_municipality_boundaries,
    load_municipality_index,
    merge_municipality_geodata,
    repair_geometries,
    save_geodata,
    save_validation_report,
    validate_geodata,
)
from src.logger import setup_logger


logger = setup_logger()


def main() -> None:
    """
    Executa o pipeline geoespacial completo da Sprint 8.
    """
    logger.info(
        "Iniciando integração geoespacial do IVE."
    )

    MAPS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger.info(
        "Carregando malha municipal: %s",
        MUNICIPALITY_SHAPEFILE_PATH,
    )

    boundaries = load_municipality_boundaries(
        filepath=MUNICIPALITY_SHAPEFILE_PATH,
        code_column="CD_MUN",
    )

    logger.info(
        "Quantidade de geometrias carregadas: %s",
        len(boundaries),
    )

    boundaries = repair_geometries(
        boundaries
    )

    logger.info(
        "Carregando base municipal do IVE: %s",
        MUNICIPALITY_FINAL_INDEX_PATH,
    )

    municipality_index = load_municipality_index(
        filepath=MUNICIPALITY_FINAL_INDEX_PATH,
        code_column="CO_MUNICIPIO",
    )

    logger.info(
        "Quantidade de municípios na base do IVE: %s",
        len(municipality_index),
    )

    geodata = merge_municipality_geodata(
        boundaries=boundaries,
        municipality_index=municipality_index,
        boundary_code_column="CO_MUNICIPIO",
        index_code_column="CO_MUNICIPIO",
        indicator_column="IVE",
        expected_municipalities=497,
    )

    logger.info(
        "Quantidade de municípios após o merge: %s",
        len(geodata),
    )

    geodata = create_priority_flag(
        geodata=geodata,
        rank_column="RANK_VULNERABILIDADE",
        top_n=50,
        output_column="PRIORIDADE",
    )

    validation_summary = validate_geodata(
        geodata=geodata,
        code_column="CO_MUNICIPIO",
        indicator_column="IVE",
        expected_municipalities=497,
    )

    validation_report_path = (
        MAPS_DIR
        / "geospatial_validation.json"
    )

    save_validation_report(
        summary=validation_summary,
        filepath=validation_report_path,
    )

    logger.info(
        "Relatório de validação salvo em: %s",
        validation_report_path,
    )

    save_geodata(
        geodata=geodata,
        filepath=MUNICIPALITY_GEODATA_PATH,
    )

    logger.info(
        "Base geoespacial salva em: %s",
        MUNICIPALITY_GEODATA_PATH,
    )

    create_continuous_ive_map(
        geodata=geodata,
        output_path=IVE_CONTINUOUS_MAP_PATH,
        indicator_column="IVE",
    )

    logger.info(
        "Mapa contínuo do IVE salvo em: %s",
        IVE_CONTINUOUS_MAP_PATH,
    )

    create_category_ive_map(
        geodata=geodata,
        output_path=IVE_CATEGORY_MAP_PATH,
        category_column="IVE_CATEGORIA",
    )

    logger.info(
        "Mapa categórico do IVE salvo em: %s",
        IVE_CATEGORY_MAP_PATH,
    )

    create_priority_map(
        geodata=geodata,
        output_path=IVE_PRIORITY_MAP_PATH,
        priority_column="PRIORIDADE",
        priority_label="Top 50",
    )

    logger.info(
        "Mapa de municípios prioritários salvo em: %s",
        IVE_PRIORITY_MAP_PATH,
    )

    create_interactive_ive_map(
        geodata=geodata,
        output_path=IVE_INTERACTIVE_MAP_PATH,
        indicator_column="IVE",
        municipality_name_column="NO_MUNICIPIO",
        category_column="IVE_CATEGORIA",
        rank_column="RANK_VULNERABILIDADE",
    )

    logger.info(
        "Mapa interativo do IVE salvo em: %s",
        IVE_INTERACTIVE_MAP_PATH,
    )

    print("\nResumo da validação geoespacial:\n")

    for metric, value in validation_summary.items():
        print(f"{metric}: {value}")

    print("\nArquivos gerados:\n")
    print(MUNICIPALITY_GEODATA_PATH)
    print(IVE_CONTINUOUS_MAP_PATH)
    print(IVE_CATEGORY_MAP_PATH)
    print(IVE_PRIORITY_MAP_PATH)
    print(IVE_INTERACTIVE_MAP_PATH)
    print(validation_report_path)

    logger.info(
        "Pipeline geoespacial concluído com sucesso."
    )


if __name__ == "__main__":
    main()


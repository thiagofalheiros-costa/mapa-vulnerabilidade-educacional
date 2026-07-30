"""
Pipeline principal do Mapa de Vulnerabilidade Educacional.
"""

from src.run_geospatial import main as run_geospatial


def main() -> None:
    """
    Executa o pipeline geoespacial da Sprint 8.
    """
    run_geospatial()


if __name__ == "__main__":
    main()
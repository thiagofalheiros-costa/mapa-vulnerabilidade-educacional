"""
Ponto de entrada do projeto.
"""

from src.config import CENSO_DIR
from src.load_data import read_data
from src.logger import setup_logger
from src.utils import validate_required_columns


logger = setup_logger()


def main() -> None:
    """
    Executa o teste inicial do leitor de dados.
    """
    logger.info(
        "Iniciando o projeto Mapa de Vulnerabilidade Educacional."
    )

    file_path = CENSO_DIR / "teste_censo.csv"

    df = read_data(
        file_path=file_path,
    )

    validate_required_columns(
        df=df,
        required_columns=[
            "Código da Entidade",
            "Código do Município",
            "UF",
        ],
        dataset_name="Censo Escolar de teste",
    )

    logger.info(
        "Validação das colunas concluída com sucesso."
    )

    print("\nPrimeiras linhas:\n")
    print(df.head())

    print("\nColunas normalizadas:\n")
    print(df.columns.tolist())

    print("\nTipos das colunas:\n")
    print(df.dtypes)


if __name__ == "__main__":
    main()
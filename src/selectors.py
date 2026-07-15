"""
Selecionadores de variáveis.
"""

from src.metadata.censo import CENSO_COLUMNS


def get_censo_columns():

    """
    Retorna as colunas utilizadas pelo projeto.
    """

    return CENSO_COLUMNS.copy()
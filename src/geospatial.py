"""
Funções para integração, validação e visualização geoespacial
do Índice de Vulnerabilidade Educacional.

O módulo realiza:

1. carregamento da malha municipal;
2. padronização dos códigos municipais;
3. validação das geometrias;
4. integração da malha com a base do IVE;
5. geração de mapas estáticos;
6. inclusão de seta norte e barra de escala;
7. geração de mapa interativo;
8. exportação do GeoDataFrame processado.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from branca.colormap import LinearColormap
from matplotlib.patches import Patch
from matplotlib_scalebar.scalebar import ScaleBar


DEFAULT_TARGET_CRS = "EPSG:4674"

# SIRGAS 2000 / UTM zone 22S.
# Sistema projetado em metros, adequado para a maior parte do RS.
MAP_PROJECTED_CRS = "EPSG:31982"

CATEGORY_ORDER = [
    "Muito baixa",
    "Baixa",
    "Média",
    "Alta",
    "Muito alta",
]

CATEGORY_COLORS = {
    "Muito baixa": "#1a9850",
    "Baixa": "#91cf60",
    "Média": "#fee08b",
    "Alta": "#fc8d59",
    "Muito alta": "#d73027",
}


def standardize_municipality_code(
    series: pd.Series,
    digits: int = 7,
) -> pd.Series:
    """
    Padroniza códigos municipais como strings numéricas.

    Remove espaços, separadores e casas decimais adicionadas
    durante leituras de arquivos tabulares.

    Parameters
    ----------
    series:
        Série contendo os códigos municipais.
    digits:
        Quantidade esperada de dígitos do código.

    Returns
    -------
    pandas.Series
        Série de códigos padronizados.
    """
    standardized = (
        series.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
    )

    standardized = standardized.where(
        standardized.str.len().gt(0),
        pd.NA,
    )

    return standardized.str.zfill(digits)


def load_municipality_boundaries(
    filepath: str | Path,
    code_column: str = "CD_MUN",
    target_crs: str = DEFAULT_TARGET_CRS,
) -> gpd.GeoDataFrame:
    """
    Carrega e prepara a malha municipal.

    Parameters
    ----------
    filepath:
        Caminho do shapefile, GeoPackage ou GeoJSON.
    code_column:
        Coluna que identifica o código do município.
    target_crs:
        Sistema de referência utilizado na saída.

    Returns
    -------
    geopandas.GeoDataFrame
        Malha municipal preparada.
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(
            f"Arquivo geográfico não encontrado: {filepath}"
        )

    geodata = gpd.read_file(filepath)

    if geodata.empty:
        raise ValueError("A malha municipal está vazia.")

    if code_column not in geodata.columns:
        raise KeyError(
            f"A coluna geográfica '{code_column}' não foi encontrada. "
            f"Colunas disponíveis: {list(geodata.columns)}"
        )

    if "geometry" not in geodata.columns:
        raise KeyError(
            "A malha municipal não possui uma coluna de geometria."
        )

    if geodata.crs is None:
        raise ValueError(
            "A malha municipal não possui CRS definido."
        )

    geodata = geodata.copy()

    geodata["CO_MUNICIPIO"] = standardize_municipality_code(
        geodata[code_column]
    )

    if geodata["CO_MUNICIPIO"].isna().any():
        invalid_codes = int(
            geodata["CO_MUNICIPIO"].isna().sum()
        )

        raise ValueError(
            f"Foram encontrados {invalid_codes} códigos municipais inválidos."
        )

    if geodata["CO_MUNICIPIO"].duplicated().any():
        duplicated = (
            geodata.loc[
                geodata["CO_MUNICIPIO"].duplicated(keep=False),
                "CO_MUNICIPIO",
            ]
            .dropna()
            .unique()
            .tolist()
        )

        raise ValueError(
            "Foram encontrados códigos municipais duplicados na malha: "
            f"{duplicated[:10]}"
        )

    geodata = geodata.to_crs(target_crs)

    return geodata


def repair_geometries(
    geodata: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Repara geometrias inválidas utilizando make_valid quando disponível.

    Parameters
    ----------
    geodata:
        GeoDataFrame que será validado.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame com as geometrias reparadas.
    """
    if not isinstance(geodata, gpd.GeoDataFrame):
        raise TypeError(
            "O objeto informado deve ser um GeoDataFrame."
        )

    result = geodata.copy()

    null_geometry_count = int(
        result.geometry.isna().sum()
    )

    if null_geometry_count > 0:
        raise ValueError(
            f"Foram encontradas {null_geometry_count} geometrias nulas."
        )

    empty_geometry_count = int(
        result.geometry.is_empty.sum()
    )

    if empty_geometry_count > 0:
        raise ValueError(
            f"Foram encontradas {empty_geometry_count} geometrias vazias."
        )

    invalid_mask = ~result.geometry.is_valid

    if invalid_mask.any():
        try:
            result.loc[invalid_mask, "geometry"] = (
                result.loc[invalid_mask, "geometry"].make_valid()
            )
        except AttributeError:
            result.loc[invalid_mask, "geometry"] = (
                result.loc[invalid_mask, "geometry"].buffer(0)
            )

    remaining_invalid = int(
        (~result.geometry.is_valid).sum()
    )

    if remaining_invalid > 0:
        raise ValueError(
            f"Restaram {remaining_invalid} geometrias inválidas "
            "após a tentativa de reparo."
        )

    return result


def load_municipality_index(
    filepath: str | Path,
    code_column: str = "CO_MUNICIPIO",
) -> pd.DataFrame:
    """
    Carrega a base municipal contendo o IVE.

    O formato é identificado pela extensão do arquivo.

    Parameters
    ----------
    filepath:
        Caminho da base municipal.
    code_column:
        Coluna que identifica o código municipal.

    Returns
    -------
    pandas.DataFrame
        Base municipal preparada.
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(
            f"Base municipal não encontrada: {filepath}"
        )

    suffix = filepath.suffix.lower()

    if suffix == ".parquet":
        municipality_index = pd.read_parquet(filepath)
    elif suffix == ".csv":
        municipality_index = pd.read_csv(filepath)
    elif suffix in {".xlsx", ".xls"}:
        municipality_index = pd.read_excel(filepath)
    else:
        raise ValueError(
            "Formato não suportado. Utilize Parquet, CSV ou Excel."
        )

    if municipality_index.empty:
        raise ValueError(
            "A base municipal do IVE está vazia."
        )

    if code_column not in municipality_index.columns:
        raise KeyError(
            f"A coluna '{code_column}' não foi encontrada na base do IVE. "
            f"Colunas disponíveis: {list(municipality_index.columns)}"
        )

    municipality_index = municipality_index.copy()

    municipality_index[code_column] = (
        standardize_municipality_code(
            municipality_index[code_column]
        )
    )

    if municipality_index[code_column].isna().any():
        invalid_codes = int(
            municipality_index[code_column].isna().sum()
        )

        raise ValueError(
            f"Foram encontrados {invalid_codes} códigos inválidos "
            "na base do IVE."
        )

    if municipality_index[code_column].duplicated().any():
        duplicated = (
            municipality_index.loc[
                municipality_index[code_column].duplicated(
                    keep=False
                ),
                code_column,
            ]
            .dropna()
            .unique()
            .tolist()
        )

        raise ValueError(
            "Foram encontrados municípios duplicados na base do IVE: "
            f"{duplicated[:10]}"
        )

    return municipality_index


def merge_municipality_geodata(
    boundaries: gpd.GeoDataFrame,
    municipality_index: pd.DataFrame,
    boundary_code_column: str = "CO_MUNICIPIO",
    index_code_column: str = "CO_MUNICIPIO",
    indicator_column: str = "IVE",
    expected_municipalities: int | None = 497,
) -> gpd.GeoDataFrame:
    """
    Integra a malha municipal com a base do IVE.

    Registros existentes apenas na malha são removidos, desde que
    a quantidade final corresponda ao total esperado de municípios.

    Parameters
    ----------
    boundaries:
        Malha municipal.
    municipality_index:
        Base tabular contendo o IVE.
    boundary_code_column:
        Código municipal na malha.
    index_code_column:
        Código municipal na base do IVE.
    indicator_column:
        Coluna utilizada para verificar a correspondência.
    expected_municipalities:
        Quantidade esperada de municípios. Pode ser None.

    Returns
    -------
    geopandas.GeoDataFrame
        Base geoespacial integrada.
    """
    if boundary_code_column not in boundaries.columns:
        raise KeyError(
            f"A coluna '{boundary_code_column}' não existe na malha."
        )

    if index_code_column not in municipality_index.columns:
        raise KeyError(
            f"A coluna '{index_code_column}' não existe na base do IVE."
        )

    if indicator_column not in municipality_index.columns:
        raise KeyError(
            f"O indicador '{indicator_column}' não existe na base do IVE."
        )

    boundaries_copy = boundaries.copy()
    index_copy = municipality_index.copy()

    boundaries_copy[boundary_code_column] = (
        standardize_municipality_code(
            boundaries_copy[boundary_code_column]
        )
    )

    index_copy[index_code_column] = (
        standardize_municipality_code(
            index_copy[index_code_column]
        )
    )

    if index_code_column != boundary_code_column:
        index_copy = index_copy.rename(
            columns={
                index_code_column: boundary_code_column,
            }
        )

    merged = boundaries_copy.merge(
        index_copy,
        on=boundary_code_column,
        how="left",
        validate="one_to_one",
        indicator="_merge_status",
    )

    unmatched = merged.loc[
        merged["_merge_status"] == "left_only",
        boundary_code_column,
    ].tolist()

    if unmatched:
        print(
            f"Aviso: {len(unmatched)} registros da malha não foram "
            f"encontrados na base do IVE e serão removidos. "
            f"Códigos: {unmatched[:20]}"
        )

        merged = merged.loc[
            merged["_merge_status"] == "both"
        ].copy()

    merged = merged.drop(
        columns="_merge_status"
    )

    if merged[indicator_column].isna().any():
        missing_indicator = merged.loc[
            merged[indicator_column].isna(),
            boundary_code_column,
        ].tolist()

        raise ValueError(
            f"{len(missing_indicator)} municípios estão sem valor de "
            f"'{indicator_column}'. Códigos: {missing_indicator[:20]}"
        )

    if expected_municipalities is not None:
        if len(merged) != expected_municipalities:
            raise ValueError(
                f"A base integrada possui {len(merged)} municípios, "
                f"mas eram esperados {expected_municipalities}."
            )

    return gpd.GeoDataFrame(
        merged,
        geometry="geometry",
        crs=boundaries.crs,
    )


def create_priority_flag(
    geodata: gpd.GeoDataFrame,
    rank_column: str = "RANK_VULNERABILIDADE",
    top_n: int = 50,
    output_column: str = "PRIORIDADE",
) -> gpd.GeoDataFrame:
    """
    Cria uma classificação binária de prioridade.

    Parameters
    ----------
    geodata:
        Base geoespacial integrada.
    rank_column:
        Coluna do ranking do IVE.
    top_n:
        Quantidade de municípios prioritários.
    output_column:
        Nome da coluna criada.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame com a classificação de prioridade.
    """
    if rank_column not in geodata.columns:
        raise KeyError(
            f"A coluna de ranking '{rank_column}' não foi encontrada."
        )

    if top_n <= 0:
        raise ValueError(
            "O valor de top_n deve ser maior do que zero."
        )

    result = geodata.copy()

    numeric_rank = pd.to_numeric(
        result[rank_column],
        errors="coerce",
    )

    if numeric_rank.isna().any():
        raise ValueError(
            f"A coluna '{rank_column}' contém valores inválidos."
        )

    result[output_column] = numeric_rank.le(top_n).map(
        {
            True: f"Top {top_n}",
            False: "Demais municípios",
        }
    )

    return result


def validate_geodata(
    geodata: gpd.GeoDataFrame,
    code_column: str = "CO_MUNICIPIO",
    indicator_column: str = "IVE",
    expected_municipalities: int | None = 497,
) -> dict[str, Any]:
    """
    Gera um resumo da qualidade da base geoespacial.

    Parameters
    ----------
    geodata:
        Base geoespacial integrada.
    code_column:
        Código municipal.
    indicator_column:
        Indicador principal.
    expected_municipalities:
        Quantidade esperada de municípios.

    Returns
    -------
    dict
        Resumo das validações.
    """
    if not isinstance(geodata, gpd.GeoDataFrame):
        raise TypeError(
            "O objeto deve ser um GeoDataFrame."
        )

    required_columns = {
        code_column,
        indicator_column,
        "geometry",
    }

    missing_columns = required_columns.difference(
        geodata.columns
    )

    if missing_columns:
        raise KeyError(
            "Colunas obrigatórias ausentes: "
            f"{sorted(missing_columns)}"
        )

    summary = {
        "municipios_total": int(len(geodata)),
        "municipios_unicos": int(
            geodata[code_column].nunique()
        ),
        "codigos_nulos": int(
            geodata[code_column].isna().sum()
        ),
        "codigos_duplicados": int(
            geodata[code_column].duplicated().sum()
        ),
        "indicadores_nulos": int(
            geodata[indicator_column].isna().sum()
        ),
        "geometrias_nulas": int(
            geodata.geometry.isna().sum()
        ),
        "geometrias_vazias": int(
            geodata.geometry.is_empty.sum()
        ),
        "geometrias_invalidas": int(
            (~geodata.geometry.is_valid).sum()
        ),
        "crs": str(geodata.crs),
    }

    if expected_municipalities is not None:
        summary["quantidade_esperada"] = (
            expected_municipalities
        )

        summary["quantidade_valida"] = (
            len(geodata) == expected_municipalities
        )

    summary["base_valida"] = all(
        [
            summary["codigos_nulos"] == 0,
            summary["codigos_duplicados"] == 0,
            summary["indicadores_nulos"] == 0,
            summary["geometrias_nulas"] == 0,
            summary["geometrias_vazias"] == 0,
            summary["geometrias_invalidas"] == 0,
            summary.get("quantidade_valida", True),
        ]
    )

    return summary


def save_validation_report(
    summary: dict[str, Any],
    filepath: str | Path,
) -> Path:
    """
    Salva o resumo de validação em JSON.

    Parameters
    ----------
    summary:
        Dicionário gerado por validate_geodata.
    filepath:
        Caminho do arquivo JSON.

    Returns
    -------
    pathlib.Path
        Caminho do relatório salvo.
    """
    filepath = Path(filepath)

    filepath.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with filepath.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            ensure_ascii=False,
            indent=4,
        )

    return filepath


def save_geodata(
    geodata: gpd.GeoDataFrame,
    filepath: str | Path,
) -> Path:
    """
    Salva o GeoDataFrame em formato GeoParquet.

    Parameters
    ----------
    geodata:
        Base geoespacial integrada.
    filepath:
        Caminho do arquivo Parquet.

    Returns
    -------
    pathlib.Path
        Caminho salvo.
    """
    filepath = Path(filepath)

    filepath.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geodata.to_parquet(
        filepath,
        index=False,
    )

    return filepath


def prepare_map_geodata(
    geodata: gpd.GeoDataFrame,
    projected_crs: str = MAP_PROJECTED_CRS,
) -> gpd.GeoDataFrame:
    """
    Prepara uma cópia projetada da base para mapas estáticos.

    A projeção em metros permite a construção correta da barra
    de escala.

    Parameters
    ----------
    geodata:
        Base geoespacial original.
    projected_crs:
        CRS projetado utilizado na visualização.

    Returns
    -------
    geopandas.GeoDataFrame
        Cópia da base reprojetada.
    """
    if not isinstance(geodata, gpd.GeoDataFrame):
        raise TypeError(
            "O objeto informado deve ser um GeoDataFrame."
        )

    if geodata.crs is None:
        raise ValueError(
            "O GeoDataFrame não possui CRS definido."
        )

    result = geodata.copy()

    if result.crs.to_string() != projected_crs:
        result = result.to_crs(projected_crs)

    return result


def add_map_elements(
    axis: plt.Axes,
    north_x: float = 0.94,
    north_y: float = 0.92,
    scalebar_location: str = "lower right",
) -> None:
    """
    Adiciona seta norte e barra de escala ao mapa.

    A barra de escala pressupõe que os dados tenham sido
    projetados em um CRS cuja unidade seja metro.

    Parameters
    ----------
    axis:
        Eixo do Matplotlib.
    north_x:
        Posição horizontal da seta norte em coordenadas do eixo.
    north_y:
        Posição vertical superior da seta norte.
    scalebar_location:
        Localização da barra de escala.
    """
    axis.annotate(
        "N",
        xy=(north_x, north_y),
        xytext=(north_x, north_y - 0.11),
        xycoords=axis.transAxes,
        textcoords=axis.transAxes,
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        arrowprops={
            "facecolor": "black",
            "edgecolor": "black",
            "width": 3,
            "headwidth": 11,
            "headlength": 12,
        },
        zorder=10,
    )

    scalebar = ScaleBar(
        dx=1,
        units="m",
        dimension="si-length",
        location=scalebar_location,
        length_fraction=0.20,
        width_fraction=0.004,
        box_alpha=0.85,
        box_color="white",
        color="black",
        scale_loc="bottom",
        label_loc="top",
        font_properties={
            "size": 10,
        },
    )

    axis.add_artist(scalebar)


def create_continuous_ive_map(
    geodata: gpd.GeoDataFrame,
    output_path: str | Path,
    indicator_column: str = "IVE",
    title: str = (
        "Índice de Vulnerabilidade Educacional "
        "por município — Rio Grande do Sul"
    ),
) -> Path:
    """
    Cria um mapa coroplético contínuo do IVE.

    Parameters
    ----------
    geodata:
        Base geoespacial integrada.
    output_path:
        Caminho da imagem.
    indicator_column:
        Coluna numérica representada no mapa.
    title:
        Título da visualização.

    Returns
    -------
    pathlib.Path
        Caminho da imagem salva.
    """
    if indicator_column not in geodata.columns:
        raise KeyError(
            f"A coluna '{indicator_column}' não foi encontrada."
        )

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    map_data = prepare_map_geodata(
        geodata
    )

    figure, axis = plt.subplots(
        figsize=(11, 11)
    )

    map_data.plot(
        column=indicator_column,
        cmap="RdYlGn_r",
        linewidth=0.10,
        edgecolor="white",
        legend=True,
        legend_kwds={
            "label": "Índice de Vulnerabilidade Educacional",
            "shrink": 0.65,
        },
        missing_kwds={
            "color": "lightgrey",
            "label": "Sem informação",
        },
        ax=axis,
    )

    axis.set_title(
        title,
        fontsize=16,
        pad=18,
    )

    axis.set_axis_off()

    add_map_elements(
        axis=axis,
        north_x=0.93,
        north_y=0.92,
        scalebar_location="lower right",
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)

    return output_path


def create_category_ive_map(
    geodata: gpd.GeoDataFrame,
    output_path: str | Path,
    category_column: str = "IVE_CATEGORIA",
    title: str = (
        "Categorias de vulnerabilidade educacional "
        "— Rio Grande do Sul"
    ),
) -> Path:
    """
    Cria mapa categórico do IVE.

    Parameters
    ----------
    geodata:
        Base geoespacial integrada.
    output_path:
        Caminho da imagem.
    category_column:
        Coluna que contém as categorias.
    title:
        Título da visualização.

    Returns
    -------
    pathlib.Path
        Caminho salvo.
    """
    if category_column not in geodata.columns:
        raise KeyError(
            f"A coluna '{category_column}' não foi encontrada."
        )

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result = prepare_map_geodata(
        geodata
    )

    result[category_column] = pd.Categorical(
        result[category_column],
        categories=CATEGORY_ORDER,
        ordered=True,
    )

    figure, axis = plt.subplots(
        figsize=(11, 11)
    )

    for category in CATEGORY_ORDER:
        category_data = result.loc[
            result[category_column] == category
        ]

        if category_data.empty:
            continue

        category_data.plot(
            color=CATEGORY_COLORS[category],
            linewidth=0.10,
            edgecolor="white",
            ax=axis,
        )

    legend_items = [
        Patch(
            facecolor=CATEGORY_COLORS[category],
            edgecolor="none",
            label=category,
        )
        for category in CATEGORY_ORDER
    ]

    axis.legend(
        handles=legend_items,
        title="Categoria do IVE",
        loc="lower left",
        frameon=True,
    )

    axis.set_title(
        title,
        fontsize=16,
        pad=18,
    )

    axis.set_axis_off()

    add_map_elements(
        axis=axis,
        north_x=0.93,
        north_y=0.92,
        scalebar_location="lower right",
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)

    return output_path


def create_priority_map(
    geodata: gpd.GeoDataFrame,
    output_path: str | Path,
    priority_column: str = "PRIORIDADE",
    priority_label: str = "Top 50",
    title: str = (
        "Municípios prioritários segundo o IVE "
        "— Rio Grande do Sul"
    ),
) -> Path:
    """
    Cria mapa binário dos municípios prioritários.

    Parameters
    ----------
    geodata:
        Base geoespacial integrada.
    output_path:
        Caminho da imagem.
    priority_column:
        Coluna que identifica prioridade.
    priority_label:
        Valor que representa municípios prioritários.
    title:
        Título da visualização.

    Returns
    -------
    pathlib.Path
        Caminho salvo.
    """
    if priority_column not in geodata.columns:
        raise KeyError(
            f"A coluna '{priority_column}' não foi encontrada."
        )

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result = prepare_map_geodata(
        geodata
    )

    result["_MAP_COLOR"] = result[priority_column].map(
        {
            priority_label: "#d73027",
            "Demais municípios": "#d9d9d9",
        }
    ).fillna("#d9d9d9")

    figure, axis = plt.subplots(
        figsize=(11, 11)
    )

    result.plot(
        color=result["_MAP_COLOR"],
        linewidth=0.10,
        edgecolor="white",
        ax=axis,
    )

    legend_items = [
        Patch(
            facecolor="#d73027",
            edgecolor="none",
            label=priority_label,
        ),
        Patch(
            facecolor="#d9d9d9",
            edgecolor="none",
            label="Demais municípios",
        ),
    ]

    axis.legend(
        handles=legend_items,
        title="Priorização",
        loc="lower left",
        frameon=True,
    )

    axis.set_title(
        title,
        fontsize=16,
        pad=18,
    )

    axis.set_axis_off()

    add_map_elements(
        axis=axis,
        north_x=0.93,
        north_y=0.92,
        scalebar_location="lower right",
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)

    return output_path


def create_interactive_ive_map(
    geodata: gpd.GeoDataFrame,
    output_path: str | Path,
    indicator_column: str = "IVE",
    municipality_name_column: str = "NO_MUNICIPIO",
    category_column: str = "IVE_CATEGORIA",
    rank_column: str = "RANK_VULNERABILIDADE",
) -> Path:
    """
    Cria um mapa interativo em HTML.

    Parameters
    ----------
    geodata:
        Base geoespacial integrada.
    output_path:
        Caminho do arquivo HTML.
    indicator_column:
        Coluna numérica do IVE.
    municipality_name_column:
        Nome do município.
    category_column:
        Categoria do IVE.
    rank_column:
        Ranking municipal.

    Returns
    -------
    pathlib.Path
        Caminho do HTML salvo.
    """
    required_columns = {
        indicator_column,
        municipality_name_column,
        category_column,
        rank_column,
        "geometry",
    }

    missing_columns = required_columns.difference(
        geodata.columns
    )

    if missing_columns:
        raise KeyError(
            "Colunas necessárias ao mapa interativo ausentes: "
            f"{sorted(missing_columns)}"
        )

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    map_data = geodata.to_crs(
        "EPSG:4326"
    ).copy()

    try:
        center_geometry = map_data.geometry.union_all()
    except AttributeError:
        center_geometry = map_data.geometry.unary_union

    center = center_geometry.centroid

    minimum = float(
        map_data[indicator_column].min()
    )

    maximum = float(
        map_data[indicator_column].max()
    )  

    colormap = LinearColormap(
    colors=[
        "#1a9850",
        "#91cf60",
        "#d9ef8b",
        "#ffffbf",
        "#fee08b",
        "#fc8d59",
        "#d73027",
    ],
    index=[
        minimum,
        minimum + (maximum - minimum) * 0.15,
        minimum + (maximum - minimum) * 0.30,
        minimum + (maximum - minimum) * 0.50,
        minimum + (maximum - minimum) * 0.70,
        minimum + (maximum - minimum) * 0.85,
        maximum,
    ],
    vmin=minimum,
    vmax=maximum,
    caption="Índice de Vulnerabilidade Educacional",
)

    map_object = folium.Map(
        location=[
            center.y,
            center.x,
        ],
        zoom_start=6,
        tiles="CartoDB positron",
        control_scale=True,
    )

    def style_function(
        feature: dict[str, Any],
    ) -> dict[str, Any]:
        value = feature["properties"].get(
            indicator_column
        )

        if value is None:
            fill_color = "#d9d9d9"
        else:
            fill_color = colormap(float(value))

        return {
            "fillColor": fill_color,
            "color": "#666666",
            "weight": 0.5,
            "fillOpacity": 0.8,
        }

    def highlight_function(
        _: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "color": "#000000",
            "weight": 2,
            "fillOpacity": 0.95,
        }

    tooltip = folium.GeoJsonTooltip(
        fields=[
            municipality_name_column,
            indicator_column,
            category_column,
            rank_column,
        ],
        aliases=[
            "Município:",
            "IVE:",
            "Categoria:",
            "Posição no ranking:",
        ],
        localize=True,
        sticky=False,
        labels=True,
        style=(
            "background-color: white; "
            "color: #333333; "
            "font-family: Arial; "
            "font-size: 13px; "
            "padding: 10px;"
        ),
    )

    folium.GeoJson(
        data=map_data.to_json(),
        name="Índice de Vulnerabilidade Educacional",
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=tooltip,
    ).add_to(map_object)

    colormap.add_to(map_object)

    folium.LayerControl(
        collapsed=False
    ).add_to(map_object)

    map_object.save(
        output_path
    )

    return output_path
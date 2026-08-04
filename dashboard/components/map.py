"""
Componente de mapa interativo do dashboard.
"""

from pathlib import Path

import branca.colormap as cm
import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

REQUIRED_GEO_COLUMNS = {
    "CO_MUNICIPIO",
    "geometry",
}

# A simplificação é realizada em metros em uma projeção adequada ao RS.
# O valor reduz o tamanho do GeoJSON sem comprometer a leitura estadual.
SIMPLIFICATION_CRS = "EPSG:31982"
SIMPLIFICATION_TOLERANCE_METERS = 250


def normalize_municipality_code(
    series: pd.Series,
) -> pd.Series:
    """
    Padroniza o código municipal no formato de sete dígitos.

    Parameters
    ----------
    series : pd.Series
        Série contendo códigos municipais.

    Returns
    -------
    pd.Series
        Série padronizada como texto.
    """
    return (
        series
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .str.zfill(7)
    )


@st.cache_data(show_spinner=False)
def find_geospatial_file() -> Path:
    """
    Localiza automaticamente uma base geoespacial em data/processed.

    A função procura arquivos Parquet que contenham as colunas
    CO_MUNICIPIO e geometry.

    Returns
    -------
    Path
        Caminho da base geoespacial localizada.

    Raises
    ------
    FileNotFoundError
        Quando nenhuma base geoespacial é encontrada.
    """
    parquet_files = sorted(
        PROCESSED_DIR.glob("*.parquet")
    )

    for file_path in parquet_files:
        try:
            candidate = gpd.read_parquet(file_path)

            if REQUIRED_GEO_COLUMNS.issubset(candidate.columns):
                return file_path

        except (
            ValueError,
            TypeError,
            OSError,
        ):
            continue

    raise FileNotFoundError(
        "Nenhuma base geoespacial foi encontrada em "
        f"{PROCESSED_DIR}. O arquivo deve ser Parquet e conter "
        "as colunas 'CO_MUNICIPIO' e 'geometry'."
    )


def simplify_geometries(
    geodata: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Simplifica as geometrias municipais para acelerar o Folium.

    A simplificação ocorre em projeção métrica, preservando a
    topologia, e a malha retorna ao EPSG:4326.
    """
    projected = geodata.to_crs(
        SIMPLIFICATION_CRS
    ).copy()

    projected["geometry"] = (
        projected["geometry"]
        .simplify(
            tolerance=SIMPLIFICATION_TOLERANCE_METERS,
            preserve_topology=True,
        )
    )

    projected = projected[
        projected["geometry"].notna()
        & ~projected["geometry"].is_empty
    ].copy()

    return projected.to_crs(epsg=4326)


@st.cache_data(
    show_spinner="Carregando e otimizando a malha municipal..."
)
def load_geospatial_data() -> gpd.GeoDataFrame:
    """
    Carrega e prepara a base geoespacial municipal.

    Returns
    -------
    gpd.GeoDataFrame
        Malha municipal em coordenadas geográficas.
    """
    file_path = find_geospatial_file()

    geodata = gpd.read_parquet(file_path).copy()

    geodata["CO_MUNICIPIO"] = normalize_municipality_code(
        geodata["CO_MUNICIPIO"]
    )

    geodata = geodata[
        geodata["geometry"].notna()
    ].copy()

    if geodata.empty:
        raise ValueError(
            "A base geoespacial não possui geometrias válidas."
        )

    if geodata.crs is None:
        raise ValueError(
            "A base geoespacial não possui um sistema de "
            "referência de coordenadas definido."
        )

    geodata = simplify_geometries(
        geodata
    )

    if geodata.empty:
        raise ValueError(
            "A simplificação removeu todas as geometrias válidas."
        )

    return geodata[
        [
            "CO_MUNICIPIO",
            "geometry",
        ]
    ].copy()


def identify_category_column(
    dataframe: pd.DataFrame,
) -> str | None:
    """
    Identifica a coluna de categoria do IVE.
    """
    candidates = [
        "IVE_CATEGORIA",
        "IVE_CATEGORIA_RELATIVA",
    ]

    for column in candidates:
        if column in dataframe.columns:
            return column

    return None


def format_decimal_br(
    value: float,
    decimal_places: int = 3,
) -> str:
    """
    Formata um número decimal no padrão brasileiro.
    """
    if pd.isna(value):
        return "N/D"

    return (
        f"{float(value):.{decimal_places}f}"
        .replace(".", ",")
    )


def format_integer_br(
    value: float,
) -> str:
    """
    Formata um número inteiro com ponto como separador de milhar.
    """
    if pd.isna(value):
        return "N/D"

    return f"{int(value):,}".replace(",", ".")


def prepare_map_data(
    filtered_df: pd.DataFrame,
    geodata: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Integra os dados filtrados à malha municipal.

    Parameters
    ----------
    filtered_df : pd.DataFrame
        Base analítica filtrada no dashboard.
    geodata : gpd.GeoDataFrame
        Base geoespacial municipal.

    Returns
    -------
    gpd.GeoDataFrame
        Base pronta para renderização do mapa.
    """
    analytical_data = filtered_df.copy()

    analytical_data["CO_MUNICIPIO"] = (
        normalize_municipality_code(
            analytical_data["CO_MUNICIPIO"]
        )
    )

    selected_columns = [
        "CO_MUNICIPIO",
        "NO_MUNICIPIO",
        "SG_UF",
        "IVE",
        "IVE_RANK",
    ]

    optional_columns = [
        "IVE_CATEGORIA",
        "IVE_CATEGORIA_RELATIVA",
        "NUM_ESCOLAS",
        "NUM_MATRICULAS",
        "INFRA_MEDIA",
        "ABANDONO_EM",
        "REPROVACAO_EM",
        "DISTORCAO_EM",
        "MEDIA_INSE",
    ]

    selected_columns.extend(
        [
            column
            for column in optional_columns
            if column in analytical_data.columns
        ]
    )

    analytical_data = analytical_data[
        selected_columns
    ].drop_duplicates(
        subset="CO_MUNICIPIO"
    )

    geometry_columns = [
        "CO_MUNICIPIO",
        "geometry",
    ]

    map_data = geodata[
        geometry_columns
    ].merge(
        analytical_data,
        on="CO_MUNICIPIO",
        how="inner",
        validate="one_to_one",
    )

    if map_data.empty:
        raise ValueError(
            "Nenhum município da base filtrada foi localizado "
            "na malha geoespacial."
        )

    return gpd.GeoDataFrame(
        map_data,
        geometry="geometry",
        crs=geodata.crs,
    )


def add_formatted_map_columns(
    map_data: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Adiciona colunas textuais formatadas para o tooltip.
    """
    result = map_data.copy()

    result["IVE_FORMATADO"] = (
        result["IVE"]
        .apply(format_decimal_br)
    )

    result["RANKING_FORMATADO"] = (
        result["IVE_RANK"]
        .apply(
            lambda value: (
                f"{int(value)}º"
                if pd.notna(value)
                else "N/D"
            )
        )
    )

    if "NUM_ESCOLAS" in result.columns:
        result["ESCOLAS_FORMATADO"] = (
            result["NUM_ESCOLAS"]
            .apply(format_integer_br)
        )

    if "NUM_MATRICULAS" in result.columns:
        result["MATRICULAS_FORMATADO"] = (
            result["NUM_MATRICULAS"]
            .apply(format_integer_br)
        )

    if "INFRA_MEDIA" in result.columns:
        result["INFRA_FORMATADA"] = (
            result["INFRA_MEDIA"]
            .apply(format_decimal_br)
        )

    return result


def create_colormap(
    map_data: gpd.GeoDataFrame,
) -> cm.LinearColormap:
    """
    Cria a escala contínua de cores do IVE.
    """
    minimum_ive = float(map_data["IVE"].min())
    maximum_ive = float(map_data["IVE"].max())

    if minimum_ive == maximum_ive:
        minimum_ive -= 0.001
        maximum_ive += 0.001

    # Paleta ColorBrewer RdYlGn_r:
    # valores baixos do IVE em verde e valores altos em vermelho.
    colormap = cm.LinearColormap(
        colors=[
            "#006837",
            "#1A9850",
            "#66BD63",
            "#A6D96A",
            "#D9EF8B",
            "#FFFFBF",
            "#FEE08B",
            "#FDAE61",
            "#F46D43",
            "#D73027",
            "#A50026",
        ],
        vmin=minimum_ive,
        vmax=maximum_ive,
        caption="Índice de Vulnerabilidade Educacional — IVE",
    )

    return colormap


def create_tooltip(
    map_data: gpd.GeoDataFrame,
) -> folium.GeoJsonTooltip:
    """
    Cria o tooltip exibido sobre cada município.
    """
    fields = [
        "NO_MUNICIPIO",
        "IVE_FORMATADO",
        "RANKING_FORMATADO",
    ]

    aliases = [
        "Município:",
        "IVE:",
        "Ranking geral:",
    ]

    category_column = identify_category_column(
        map_data
    )

    if category_column is not None:
        fields.append(category_column)
        aliases.append("Categoria:")

    if "ESCOLAS_FORMATADO" in map_data.columns:
        fields.append("ESCOLAS_FORMATADO")
        aliases.append("Escolas:")

    if "MATRICULAS_FORMATADO" in map_data.columns:
        fields.append("MATRICULAS_FORMATADO")
        aliases.append("Matrículas:")

    if "INFRA_FORMATADA" in map_data.columns:
        fields.append("INFRA_FORMATADA")
        aliases.append("Infraestrutura média:")

    return folium.GeoJsonTooltip(
        fields=fields,
        aliases=aliases,
        localize=False,
        sticky=False,
        labels=True,
        style=(
            "background-color: white;"
            "color: #1F2937;"
            "font-family: Arial;"
            "font-size: 13px;"
            "padding: 10px;"
        ),
    )


def calculate_map_center(
    map_data: gpd.GeoDataFrame,
) -> list[float]:
    """
    Calcula o centro aproximado do conjunto de municípios.
    """
    bounds = map_data.total_bounds

    minimum_longitude = bounds[0]
    minimum_latitude = bounds[1]
    maximum_longitude = bounds[2]
    maximum_latitude = bounds[3]

    center_latitude = (
        minimum_latitude + maximum_latitude
    ) / 2

    center_longitude = (
        minimum_longitude + maximum_longitude
    ) / 2

    return [
        center_latitude,
        center_longitude,
    ]


def create_ive_map(
    map_data: gpd.GeoDataFrame,
) -> folium.Map:
    """
    Cria o mapa coroplético interativo do IVE.
    """
    formatted_data = add_formatted_map_columns(
        map_data
    )

    center = calculate_map_center(
        formatted_data
    )

    colormap = create_colormap(
        formatted_data
    )

    municipality_map = folium.Map(
        location=center,
        zoom_start=7,
        tiles="CartoDB positron",
        control_scale=True,
        prefer_canvas=True,
    )

    def style_function(feature: dict) -> dict:
        ive_value = feature["properties"].get("IVE")

        return {
            "fillColor": (
                colormap(ive_value)
                if ive_value is not None
                else "#D9D9D9"
            ),
            "color": "#FFFFFF",
            "weight": 0.7,
            "fillOpacity": 0.8,
        }

    def highlight_function(_: dict) -> dict:
        return {
            "color": "#17365D",
            "weight": 2.5,
            "fillOpacity": 0.95,
        }

    folium.GeoJson(
        data=formatted_data.__geo_interface__,
        name="IVE municipal",
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=create_tooltip(formatted_data),
        zoom_on_click=False,
        smooth_factor=2,
        show=True,
    ).add_to(municipality_map)

    # Camada adicional com os 50 municípios prioritários.
    priority_data = formatted_data.loc[
        pd.to_numeric(
            formatted_data["IVE_RANK"],
            errors="coerce",
        ).le(50)
    ].copy()

    if not priority_data.empty:
        priority_group = folium.FeatureGroup(
            name="Municípios prioritários — Top 50",
            overlay=True,
            control=True,
            show=False,
        )

        folium.GeoJson(
            data=priority_data.__geo_interface__,
            name="Top 50",
            style_function=lambda _: {
                "fillColor": "#E63228",
                "color": "#FFFFFF",
                "weight": 1.0,
                "fillOpacity": 0.9,
            },
            highlight_function=lambda _: {
                "fillColor": "#B71C1C",
                "color": "#17365D",
                "weight": 2.5,
                "fillOpacity": 1.0,
            },
            tooltip=create_tooltip(priority_data),
            zoom_on_click=False,
            smooth_factor=2,
        ).add_to(priority_group)

        priority_group.add_to(municipality_map)

    colormap.add_to(municipality_map)

    bounds = formatted_data.total_bounds

    municipality_map.fit_bounds(
        [
            [bounds[1], bounds[0]],
            [bounds[3], bounds[2]],
        ],
        padding=(20, 20),
    )

    folium.LayerControl(
        collapsed=False,
        position="topright",
    ).add_to(municipality_map)

    return municipality_map


def render_ive_map(
    filtered_df: pd.DataFrame,
) -> None:
    """
    Carrega, prepara e renderiza o mapa interativo.
    """
    try:
        geodata = load_geospatial_data()

        map_data = prepare_map_data(
            filtered_df=filtered_df,
            geodata=geodata,
        )

        municipality_map = create_ive_map(
            map_data
        )

    except (
        FileNotFoundError,
        ValueError,
        TypeError,
    ) as error:
        st.warning(
            "Não foi possível carregar o mapa interativo."
        )
        st.caption(str(error))
        return

    folium_static(
        municipality_map,
        width=1400,
        height=650,
    )
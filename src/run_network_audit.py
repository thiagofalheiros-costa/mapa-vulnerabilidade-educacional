"""
Auditoria da oferta de Ensino Médio por rede de ensino.

Este script analisa uma base do Censo Escolar no nível de escola e gera:

- resumo por rede de ensino;
- composição das redes por município;
- lista de municípios com oferta municipal;
- relatório metodológico em Markdown.

Uso
---
python -m src.run_network_audit

Ou, informando caminhos:

python -m src.run_network_audit \
    --input data/processed/censo_escolar_rs_2024.parquet \
    --output reports/network_audit
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd


LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "censo_escolar_rs_2024.parquet"
)

DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "network_audit"
)

DEPENDENCY_LABELS = {
    1: "Federal",
    2: "Estadual",
    3: "Municipal",
    4: "Privada",
}

SCHOOL_ID_CANDIDATES = (
    "CO_ENTIDADE",
    "CO_ESCOLA",
    "ID_ESCOLA",
)

MUNICIPALITY_CODE_CANDIDATES = (
    "CO_MUNICIPIO",
    "CO_MUNICIPIO_ESCOLA",
)

MUNICIPALITY_NAME_CANDIDATES = (
    "NO_MUNICIPIO",
    "NO_MUNICIPIO_ESCOLA",
)

DEPENDENCY_CANDIDATES = (
    "TP_DEPENDENCIA",
    "TP_DEPENDENCIA_ADMINISTRATIVA",
)

ENROLLMENT_CANDIDATES = (
    "QT_MAT_MED",
    "QT_MAT_MED_PROP",
    "QT_MAT_MED_INT",
    "NUM_MATRICULAS",
    "QT_MATRICULAS_EM",
)

HIGH_SCHOOL_FLAG_CANDIDATES = (
    "IN_MED",
    "IN_MEDIO",
    "IN_ENSINO_MEDIO",
)


def configure_logging() -> None:
    """Configura logs simples para execução via terminal."""
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | %(message)s"
        ),
    )


def find_column(
    dataframe: pd.DataFrame,
    candidates: tuple[str, ...],
    *,
    required: bool = True,
) -> str | None:
    """
    Localiza a primeira coluna disponível entre as candidatas.
    """
    for column in candidates:
        if column in dataframe.columns:
            return column

    if required:
        raise ValueError(
            "Nenhuma das colunas esperadas foi encontrada: "
            + ", ".join(candidates)
        )

    return None


def normalize_municipality_code(
    series: pd.Series,
) -> pd.Series:
    """Padroniza o código municipal no formato de sete dígitos."""
    return (
        series
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .str.zfill(7)
    )


def identify_enrollment_columns(
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Identifica colunas de matrícula de Ensino Médio.

    Quando mais de uma coluna detalhada estiver disponível, todas são
    somadas para compor o total da escola.
    """
    available = [
        column
        for column in ENROLLMENT_CANDIDATES
        if column in dataframe.columns
    ]

    if "QT_MAT_MED" in available:
        return ["QT_MAT_MED"]

    return available


def filter_high_school_schools(
    dataframe: pd.DataFrame,
    enrollment_columns: list[str],
) -> pd.DataFrame:
    """
    Mantém somente escolas com oferta de Ensino Médio.

    A prioridade é:
    1. indicador binário de oferta;
    2. total de matrículas de Ensino Médio maior que zero;
    3. base inteira, quando o arquivo já tiver sido previamente filtrado.
    """
    for flag_column in HIGH_SCHOOL_FLAG_CANDIDATES:
        if flag_column in dataframe.columns:
            flag = pd.to_numeric(
                dataframe[flag_column],
                errors="coerce",
            )

            return dataframe.loc[
                flag.eq(1)
            ].copy()

    if enrollment_columns:
        enrollment_total = (
            dataframe[enrollment_columns]
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0)
            .sum(axis=1)
        )

        return dataframe.loc[
            enrollment_total.gt(0)
        ].copy()

    LOGGER.warning(
        "Nenhuma coluna explícita de oferta ou matrícula do Ensino Médio "
        "foi encontrada. A auditoria considerará todas as linhas da base."
    )

    return dataframe.copy()


def prepare_school_base(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepara uma base padronizada com uma linha por escola.
    """
    school_id_column = find_column(
        dataframe,
        SCHOOL_ID_CANDIDATES,
    )
    municipality_code_column = find_column(
        dataframe,
        MUNICIPALITY_CODE_CANDIDATES,
    )
    municipality_name_column = find_column(
        dataframe,
        MUNICIPALITY_NAME_CANDIDATES,
    )
    dependency_column = find_column(
        dataframe,
        DEPENDENCY_CANDIDATES,
    )

    enrollment_columns = identify_enrollment_columns(
        dataframe
    )

    high_school_data = filter_high_school_schools(
        dataframe=dataframe,
        enrollment_columns=enrollment_columns,
    )

    prepared = pd.DataFrame(
        {
            "CO_ESCOLA": (
                high_school_data[school_id_column]
                .astype("string")
                .str.strip()
            ),
            "CO_MUNICIPIO": normalize_municipality_code(
                high_school_data[municipality_code_column]
            ),
            "NO_MUNICIPIO": (
                high_school_data[municipality_name_column]
                .astype("string")
                .str.strip()
            ),
            "TP_DEPENDENCIA": pd.to_numeric(
                high_school_data[dependency_column],
                errors="coerce",
            ),
        }
    )

    if enrollment_columns:
        prepared["MATRICULAS_EM"] = (
            high_school_data[enrollment_columns]
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0)
            .sum(axis=1)
        )
    else:
        prepared["MATRICULAS_EM"] = pd.NA

    prepared = prepared.dropna(
        subset=[
            "CO_ESCOLA",
            "CO_MUNICIPIO",
            "TP_DEPENDENCIA",
        ]
    ).copy()

    prepared["TP_DEPENDENCIA"] = (
        prepared["TP_DEPENDENCIA"]
        .astype(int)
    )

    prepared["REDE_ENSINO"] = (
        prepared["TP_DEPENDENCIA"]
        .map(DEPENDENCY_LABELS)
        .fillna(
            prepared["TP_DEPENDENCIA"]
            .map(lambda value: f"Código {value}")
        )
    )

    # Caso existam múltiplas linhas por escola, preserva uma única escola
    # e soma as matrículas disponíveis.
    prepared = (
        prepared.groupby(
            [
                "CO_ESCOLA",
                "CO_MUNICIPIO",
                "NO_MUNICIPIO",
                "TP_DEPENDENCIA",
                "REDE_ENSINO",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            MATRICULAS_EM=(
                "MATRICULAS_EM",
                lambda values: (
                    values.sum(min_count=1)
                ),
            )
        )
    )

    if prepared.empty:
        raise ValueError(
            "Nenhuma escola de Ensino Médio foi identificada na base."
        )

    return prepared


def build_network_summary(
    school_base: pd.DataFrame,
) -> pd.DataFrame:
    """
    Resume escolas, matrículas e municípios por rede.
    """
    summary = (
        school_base.groupby(
            [
                "TP_DEPENDENCIA",
                "REDE_ENSINO",
            ],
            as_index=False,
        )
        .agg(
            ESCOLAS=(
                "CO_ESCOLA",
                "nunique",
            ),
            MUNICIPIOS=(
                "CO_MUNICIPIO",
                "nunique",
            ),
            MATRICULAS_EM=(
                "MATRICULAS_EM",
                lambda values: (
                    values.sum(min_count=1)
                ),
            ),
        )
        .sort_values("TP_DEPENDENCIA")
        .reset_index(drop=True)
    )

    total_schools = summary["ESCOLAS"].sum()
    summary["PERCENTUAL_ESCOLAS"] = (
        summary["ESCOLAS"]
        / total_schools
        * 100
    )

    total_enrollments = summary["MATRICULAS_EM"].sum(
        min_count=1
    )

    if pd.notna(total_enrollments) and total_enrollments > 0:
        summary["PERCENTUAL_MATRICULAS"] = (
            summary["MATRICULAS_EM"]
            / total_enrollments
            * 100
        )
    else:
        summary["PERCENTUAL_MATRICULAS"] = pd.NA

    return summary


def build_municipality_network_table(
    school_base: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cria uma linha por município com a composição de redes.
    """
    municipality_network = (
        school_base.groupby(
            [
                "CO_MUNICIPIO",
                "NO_MUNICIPIO",
                "REDE_ENSINO",
            ],
            as_index=False,
        )
        .agg(
            ESCOLAS=(
                "CO_ESCOLA",
                "nunique",
            ),
            MATRICULAS_EM=(
                "MATRICULAS_EM",
                lambda values: (
                    values.sum(min_count=1)
                ),
            ),
        )
    )

    school_pivot = (
        municipality_network.pivot_table(
            index=[
                "CO_MUNICIPIO",
                "NO_MUNICIPIO",
            ],
            columns="REDE_ENSINO",
            values="ESCOLAS",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    enrollment_pivot = (
        municipality_network.pivot_table(
            index=[
                "CO_MUNICIPIO",
                "NO_MUNICIPIO",
            ],
            columns="REDE_ENSINO",
            values="MATRICULAS_EM",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    network_names = sorted(
        school_base["REDE_ENSINO"]
        .dropna()
        .unique()
        .tolist()
    )

    school_pivot = school_pivot.rename(
        columns={
            network: f"ESCOLAS_{network.upper()}"
            for network in network_names
        }
    )

    enrollment_pivot = enrollment_pivot.rename(
        columns={
            network: f"MATRICULAS_{network.upper()}"
            for network in network_names
        }
    )

    municipality_table = school_pivot.merge(
        enrollment_pivot,
        on=[
            "CO_MUNICIPIO",
            "NO_MUNICIPIO",
        ],
        how="outer",
        validate="one_to_one",
    )

    school_columns = [
        column
        for column in municipality_table.columns
        if column.startswith("ESCOLAS_")
    ]

    municipality_table["REDES_PRESENTES"] = (
        municipality_table.apply(
            lambda row: " + ".join(
                network
                for network in network_names
                if row.get(
                    f"ESCOLAS_{network.upper()}",
                    0,
                )
                > 0
            ),
            axis=1,
        )
    )

    municipality_table["TOTAL_ESCOLAS_EM"] = (
        municipality_table[school_columns]
        .sum(axis=1)
    )

    municipality_table["OFERTA_EXCLUSIVAMENTE_MUNICIPAL"] = (
        municipality_table["REDES_PRESENTES"]
        .eq("Municipal")
    )

    municipality_table["POSSUI_REDE_MUNICIPAL"] = (
        municipality_table["REDES_PRESENTES"]
        .str.contains(
            "Municipal",
            regex=False,
        )
    )

    return municipality_table.sort_values(
        "NO_MUNICIPIO"
    ).reset_index(drop=True)


def build_composition_summary(
    municipality_table: pd.DataFrame,
) -> pd.DataFrame:
    """
    Resume quantos municípios aparecem em cada combinação de redes.
    """
    return (
        municipality_table["REDES_PRESENTES"]
        .value_counts(dropna=False)
        .rename_axis("COMPOSICAO_REDES")
        .reset_index(name="MUNICIPIOS")
        .sort_values(
            "MUNICIPIOS",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def format_decimal_br(
    value: object,
    decimals: int = 2,
) -> str:
    """Formata decimal no padrão brasileiro."""
    if pd.isna(value):
        return "N/D"

    return (
        f"{float(value):,.{decimals}f}"
        .replace(",", "TEMP")
        .replace(".", ",")
        .replace("TEMP", ".")
    )


def format_integer_br(
    value: object,
) -> str:
    """Formata inteiro no padrão brasileiro."""
    if pd.isna(value):
        return "N/D"

    return f"{round(float(value)):,}".replace(",", ".")


def build_methodological_recommendation(
    network_summary: pd.DataFrame,
    municipality_table: pd.DataFrame,
) -> str:
    """
    Gera recomendação metodológica baseada na cobertura municipal.
    """
    municipal_row = network_summary.loc[
        network_summary["REDE_ENSINO"].eq("Municipal")
    ]

    if municipal_row.empty:
        return (
            "A base não identificou escolas municipais com oferta de "
            "Ensino Médio. Não se recomenda criar um IVE municipal separado."
        )

    municipal_schools = int(
        municipal_row["ESCOLAS"].iloc[0]
    )
    municipal_municipalities = int(
        municipality_table["POSSUI_REDE_MUNICIPAL"].sum()
    )
    total_municipalities = int(
        municipality_table["CO_MUNICIPIO"].nunique()
    )
    municipal_coverage = (
        municipal_municipalities
        / total_municipalities
        * 100
    )

    if municipal_coverage < 10:
        return (
            f"A oferta municipal de Ensino Médio aparece em apenas "
            f"{municipal_municipalities} dos {total_municipalities} "
            f"municípios analisados ({municipal_coverage:.1f}%), "
            f"somando {municipal_schools} escolas. Recomenda-se manter "
            "o IVE territorial como visão principal e apresentar a rede "
            "municipal em um painel descritivo específico, em vez de "
            "recalcular um índice municipal para todo o estado."
        )

    return (
        f"A rede municipal está presente em {municipal_municipalities} "
        f"dos {total_municipalities} municípios "
        f"({municipal_coverage:.1f}%), somando {municipal_schools} escolas. "
        "Há cobertura suficiente para considerar um recorte por rede, "
        "desde que rendimento, distorção e INSE também estejam disponíveis "
        "na mesma granularidade."
    )


def write_markdown_report(
    *,
    output_path: Path,
    school_base: pd.DataFrame,
    network_summary: pd.DataFrame,
    composition_summary: pd.DataFrame,
    municipality_table: pd.DataFrame,
) -> None:
    """
    Salva relatório sintético da auditoria em Markdown.
    """
    total_schools = school_base["CO_ESCOLA"].nunique()
    total_municipalities = (
        school_base["CO_MUNICIPIO"].nunique()
    )
    municipal_municipalities = int(
        municipality_table["POSSUI_REDE_MUNICIPAL"].sum()
    )
    exclusive_municipalities = int(
        municipality_table[
            "OFERTA_EXCLUSIVAMENTE_MUNICIPAL"
        ].sum()
    )

    lines = [
        "# Auditoria da oferta de Ensino Médio por rede",
        "",
        "## Escopo",
        "",
        (
            f"- Escolas de Ensino Médio identificadas: "
            f"**{format_integer_br(total_schools)}**."
        ),
        (
            f"- Municípios com oferta identificada: "
            f"**{format_integer_br(total_municipalities)}**."
        ),
        (
            f"- Municípios com alguma oferta municipal: "
            f"**{format_integer_br(municipal_municipalities)}**."
        ),
        (
            f"- Municípios com oferta exclusivamente municipal: "
            f"**{format_integer_br(exclusive_municipalities)}**."
        ),
        "",
        "## Resumo por rede",
        "",
        "| Rede | Escolas | % escolas | Municípios | Matrículas EM | % matrículas |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for _, row in network_summary.iterrows():
        lines.append(
            "| "
            f"{row['REDE_ENSINO']} | "
            f"{format_integer_br(row['ESCOLAS'])} | "
            f"{format_decimal_br(row['PERCENTUAL_ESCOLAS'])}% | "
            f"{format_integer_br(row['MUNICIPIOS'])} | "
            f"{format_integer_br(row['MATRICULAS_EM'])} | "
            f"{format_decimal_br(row['PERCENTUAL_MATRICULAS'])}% |"
        )

    lines.extend(
        [
            "",
            "## Composição das redes nos municípios",
            "",
            "| Composição | Municípios |",
            "|---|---:|",
        ]
    )

    for _, row in composition_summary.iterrows():
        lines.append(
            "| "
            f"{row['COMPOSICAO_REDES']} | "
            f"{format_integer_br(row['MUNICIPIOS'])} |"
        )

    municipal_names = (
        municipality_table.loc[
            municipality_table["POSSUI_REDE_MUNICIPAL"],
            "NO_MUNICIPIO",
        ]
        .dropna()
        .astype(str)
        .sort_values()
        .tolist()
    )

    lines.extend(
        [
            "",
            "## Municípios com oferta municipal de Ensino Médio",
            "",
        ]
    )

    if municipal_names:
        lines.extend(
            f"- {municipality}"
            for municipality in municipal_names
        )
    else:
        lines.append(
            "Nenhum município foi identificado."
        )

    recommendation = (
        build_methodological_recommendation(
            network_summary=network_summary,
            municipality_table=municipality_table,
        )
    )

    lines.extend(
        [
            "",
            "## Recomendação metodológica",
            "",
            recommendation,
            "",
            "## Observações",
            "",
            (
                "- A auditoria considera as redes identificadas pela coluna "
                "`TP_DEPENDENCIA`."
            ),
            (
                "- O filtro de Ensino Médio utiliza, quando disponível, "
                "um indicador de oferta ou o total de matrículas da etapa."
            ),
            (
                "- A criação de um IVE por rede só é metodologicamente "
                "consistente se todos os componentes do índice estiverem "
                "disponíveis no mesmo recorte administrativo."
            ),
        ]
    )

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def run_network_audit(
    input_path: Path,
    output_dir: Path,
) -> dict[str, Path]:
    """
    Executa a auditoria e salva os artefatos.
    """
    LOGGER.info(
        "Lendo base do Censo Escolar: %s",
        input_path,
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {input_path}"
        )

    dataframe = pd.read_parquet(
        input_path
    )

    LOGGER.info(
        "Base carregada: %s linhas e %s colunas.",
        len(dataframe),
        len(dataframe.columns),
    )

    school_base = prepare_school_base(
        dataframe
    )
    network_summary = build_network_summary(
        school_base
    )
    municipality_table = (
        build_municipality_network_table(
            school_base
        )
    )
    composition_summary = (
        build_composition_summary(
            municipality_table
        )
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    network_summary_path = (
        output_dir / "network_summary.csv"
    )
    municipality_table_path = (
        output_dir / "municipalities_by_network.csv"
    )
    composition_summary_path = (
        output_dir / "network_composition_summary.csv"
    )
    municipal_schools_path = (
        output_dir / "municipal_high_school_schools.csv"
    )
    report_path = (
        output_dir / "network_report.md"
    )

    network_summary.to_csv(
        network_summary_path,
        index=False,
        encoding="utf-8-sig",
    )
    municipality_table.to_csv(
        municipality_table_path,
        index=False,
        encoding="utf-8-sig",
    )
    composition_summary.to_csv(
        composition_summary_path,
        index=False,
        encoding="utf-8-sig",
    )
    school_base.loc[
        school_base["REDE_ENSINO"].eq("Municipal")
    ].sort_values(
        [
            "NO_MUNICIPIO",
            "CO_ESCOLA",
        ]
    ).to_csv(
        municipal_schools_path,
        index=False,
        encoding="utf-8-sig",
    )

    write_markdown_report(
        output_path=report_path,
        school_base=school_base,
        network_summary=network_summary,
        composition_summary=composition_summary,
        municipality_table=municipality_table,
    )

    LOGGER.info(
        "Auditoria concluída. Resultados salvos em: %s",
        output_dir,
    )

    return {
        "network_summary": network_summary_path,
        "municipalities_by_network": municipality_table_path,
        "network_composition_summary": composition_summary_path,
        "municipal_high_school_schools": municipal_schools_path,
        "network_report": report_path,
    }


def parse_args() -> argparse.Namespace:
    """Lê os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description=(
            "Audita a oferta de Ensino Médio por rede de ensino."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help=(
            "Caminho da base Parquet no nível de escola."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Diretório onde os resultados serão salvos."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Ponto de entrada do script."""
    configure_logging()
    args = parse_args()

    paths = run_network_audit(
        input_path=args.input,
        output_dir=args.output,
    )

    print("\nArquivos gerados:\n")

    for name, path in paths.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
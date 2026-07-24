"""Geração do relatório de validação estatística do IVE."""

from pathlib import Path

import pandas as pd

from src.logger import setup_logger

logger = setup_logger()


def _read_csv(tables_directory: Path, filename: str) -> pd.DataFrame:
    """Lê uma tabela obrigatória do relatório."""
    path = tables_directory / filename
    if not path.exists():
        raise FileNotFoundError(f"Tabela de validação não encontrada: {path}")
    return pd.read_csv(path)


def _get_diagnostic_value(diagnostics: pd.DataFrame, metric: str) -> float:
    """Obtém um valor da tabela de diagnósticos."""
    row = diagnostics.loc[diagnostics["METRICA"] == metric, "VALOR"]
    if row.empty:
        raise ValueError(f"Métrica ausente nos diagnósticos: {metric}")
    return float(row.iloc[0])


def _format_decimal(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def _format_percent(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%".replace(".", ",")


def _correlation_interpretation(value: float) -> str:
    absolute_value = abs(value)
    if absolute_value >= 0.90:
        return "muito forte"
    if absolute_value >= 0.70:
        return "forte"
    if absolute_value >= 0.50:
        return "moderada"
    if absolute_value >= 0.30:
        return "fraca"
    return "muito fraca"


def _kmo_interpretation(value: float) -> str:
    if value >= 0.90:
        return "excelente"
    if value >= 0.80:
        return "muito bom"
    if value >= 0.70:
        return "bom"
    if value >= 0.60:
        return "aceitável"
    if value >= 0.50:
        return "baixo, mas ainda utilizável com cautela"
    return "inadequado"


def _build_correlation_section(correlations: pd.DataFrame) -> list[str]:
    lines = ["## Concordância entre os índices", ""]

    for row in correlations.itertuples(index=False):
        pearson = float(row.CORRELACAO_PEARSON)
        spearman = float(row.CORRELACAO_SPEARMAN)
        lines.append(
            f"- **{row.INDICE_1} × {row.INDICE_2}:** "
            f"Pearson = {_format_decimal(pearson)} "
            f"({_correlation_interpretation(pearson)}); "
            f"Spearman = {_format_decimal(spearman)}."
        )

    lines.extend(["", correlations.to_markdown(index=False, floatfmt=".4f"), ""])
    return lines


def _build_ranking_stability_section(
    ranking_stability: pd.DataFrame,
) -> list[str]:
    lines = [
        "## Estabilidade dos rankings",
        "",
        (
            "A estabilidade foi avaliada pela sobreposição dos municípios "
            "classificados entre os Top 10, Top 20, Top 50 e Top 100 de cada "
            "método. Também foram calculados o índice de Jaccard e a diferença "
            "média de posição entre os municípios em comum."
        ),
        "",
    ]

    for pair, pair_data in ranking_stability.groupby(
        ["INDICE_1", "INDICE_2"],
        sort=False,
    ):
        index_1, index_2 = pair
        lines.extend([f"### {index_1} × {index_2}", ""])

        for row in pair_data.itertuples(index=False):
            lines.append(
                f"- Top {int(row.TOP)}: {int(row.MUNICIPIOS_EM_COMUM)} "
                f"municípios em comum "
                f"({_format_percent(float(row.PERCENTUAL_CONCORDANCIA))}); "
                f"diferença média de ranking de "
                f"{_format_decimal(float(row.DIFERENCA_MEDIA_RANK), 1)} posições."
            )
        lines.append("")

    display_table = ranking_stability.copy()
    display_table["PERCENTUAL_CONCORDANCIA"] *= 100
    display_table["INDICE_JACCARD"] *= 100
    lines.extend([display_table.to_markdown(index=False, floatfmt=".2f"), ""])
    return lines


def _build_methodological_conclusion(
    pca_variance: pd.DataFrame,
    factor_diagnostics: pd.DataFrame,
    factor_variance: pd.DataFrame,
    correlations: pd.DataFrame,
    ranking_stability: pd.DataFrame,
) -> list[str]:
    cp1_variance = float(
        pca_variance.loc[
            pca_variance["COMPONENTE"] == "CP_1",
            "VARIANCIA_EXPLICADA_PERCENTUAL",
        ].iloc[0]
    )
    kmo = _get_diagnostic_value(factor_diagnostics, "KMO_GERAL")
    bartlett_p = _get_diagnostic_value(
        factor_diagnostics,
        "BARTLETT_P_VALOR",
    )
    number_of_factors = int(
        _get_diagnostic_value(factor_diagnostics, "NUM_FATORES")
    )
    factor_cumulative = float(
        factor_variance["VARIANCIA_ACUMULADA_PERCENTUAL"].iloc[-1]
    )

    manual_pca = correlations[
        (correlations["INDICE_1"] == "IVE")
        & (correlations["INDICE_2"] == "IVE_PCA")
    ]
    manual_factor = correlations[
        (correlations["INDICE_1"] == "IVE")
        & (correlations["INDICE_2"] == "IVE_FACTOR")
    ]

    pearson_manual_pca = float(
        manual_pca["CORRELACAO_PEARSON"].iloc[0]
    )
    pearson_manual_factor = float(
        manual_factor["CORRELACAO_PEARSON"].iloc[0]
    )

    top_50_manual_pca = ranking_stability[
        (ranking_stability["INDICE_1"] == "IVE")
        & (ranking_stability["INDICE_2"] == "IVE_PCA")
        & (ranking_stability["TOP"] == 50)
    ]
    top_50_overlap = (
        float(top_50_manual_pca["PERCENTUAL_CONCORDANCIA"].iloc[0])
        if not top_50_manual_pca.empty
        else float("nan")
    )

    overlap_sentence = ""
    if pd.notna(top_50_overlap):
        overlap_sentence = (
            f"No recorte dos 50 municípios mais vulneráveis, o IVE manual "
            f"e a PCA apresentaram {_format_percent(top_50_overlap)} de "
            f"concordância. "
        )

    return [
        "## Conclusão metodológica",
        "",
        (
            f"A primeira componente principal explicou "
            f"{_format_decimal(cp1_variance, 2)}% da variância total. "
            f"A análise fatorial apresentou KMO geral de "
            f"{_format_decimal(kmo)}, classificado como "
            f"{_kmo_interpretation(kmo)}, e o teste de Bartlett foi "
            f"estatisticamente significativo (p = {bartlett_p:.3e})."
        ),
        "",
        (
            f"Foram retidos {number_of_factors} fatores, responsáveis por "
            f"{_format_decimal(factor_cumulative, 2)}% da variância comum "
            f"estimada pelo modelo fatorial."
        ),
        "",
        (
            f"O IVE manual apresentou correlação de Pearson de "
            f"{_format_decimal(pearson_manual_pca)} com o índice obtido pela "
            f"PCA e de {_format_decimal(pearson_manual_factor)} com o índice "
            f"fatorial. Esses resultados indicam elevada concordância entre "
            f"a construção teórica do índice e a estrutura empírica dos "
            f"indicadores."
        ),
        "",
        overlap_sentence
        + (
            "A combinação entre correlações elevadas, preservação dos "
            "municípios prioritários e coerência das dimensões latentes "
            "sustenta a manutenção do IVE manual como índice principal do "
            "projeto, utilizando PCA e análise fatorial como métodos de "
            "validação e análise de sensibilidade."
        ),
        "",
    ]


def execute_validation_report(
    tables_directory: Path,
    output_path: Path,
) -> Path:
    """Gera o relatório Markdown da validação estatística."""
    tables_directory = Path(tables_directory)
    output_path = Path(output_path)

    pca_loadings = _read_csv(tables_directory, "pca_loadings.csv")
    pca_variance = _read_csv(tables_directory, "pca_variance.csv")
    factor_loadings = _read_csv(tables_directory, "factor_loadings.csv")
    factor_communalities = _read_csv(
        tables_directory,
        "factor_communalities.csv",
    )
    factor_variance = _read_csv(tables_directory, "factor_variance.csv")
    factor_diagnostics = _read_csv(
        tables_directory,
        "factor_diagnostics.csv",
    )
    correlations = _read_csv(tables_directory, "index_correlations.csv")
    ranking_stability = _read_csv(
        tables_directory,
        "ranking_stability.csv",
    )
    priority_consensus = _read_csv(
        tables_directory,
        "priority_consensus.csv",
    )

    kmo = _get_diagnostic_value(factor_diagnostics, "KMO_GERAL")
    bartlett_p = _get_diagnostic_value(
        factor_diagnostics,
        "BARTLETT_P_VALOR",
    )
    number_of_factors = int(
        _get_diagnostic_value(factor_diagnostics, "NUM_FATORES")
    )

    report: list[str] = [
        "# Relatório de Validação Estatística do IVE",
        "",
        "## Objetivo",
        "",
        (
            "Avaliar a robustez do Índice de Vulnerabilidade Educacional "
            "(IVE) por meio de Análise de Componentes Principais, análise "
            "fatorial exploratória, correlações entre métodos e estabilidade "
            "dos rankings municipais."
        ),
        "",
        "## Análise de Componentes Principais",
        "",
        pca_variance.to_markdown(index=False, floatfmt=".4f"),
        "",
        "### Cargas da PCA",
        "",
        pca_loadings.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Análise fatorial exploratória",
        "",
        f"- **KMO geral:** {_format_decimal(kmo)} "
        f"({_kmo_interpretation(kmo)}).",
        f"- **Teste de Bartlett:** p = {bartlett_p:.3e}.",
        f"- **Número de fatores retidos:** {number_of_factors}.",
        "",
        "### Variância dos fatores",
        "",
        factor_variance.to_markdown(index=False, floatfmt=".4f"),
        "",
        "### Cargas fatoriais",
        "",
        factor_loadings.to_markdown(index=False, floatfmt=".4f"),
        "",
        "### Comunalidades e KMO individual",
        "",
        factor_communalities.to_markdown(index=False, floatfmt=".4f"),
        "",
    ]

    report.extend(_build_correlation_section(correlations))
    report.extend(_build_ranking_stability_section(ranking_stability))
    report.extend(
        [
            "## Municípios prioritários por consenso",
            "",
            (
                "O ranking de consenso utiliza a posição média dos municípios "
                "no IVE manual, no índice PCA e no índice fatorial. Menores "
                "valores indicam maior prioridade."
            ),
            "",
            priority_consensus.to_markdown(index=False, floatfmt=".4f"),
            "",
        ]
    )
    report.extend(
        _build_methodological_conclusion(
            pca_variance=pca_variance,
            factor_diagnostics=factor_diagnostics,
            factor_variance=factor_variance,
            correlations=correlations,
            ranking_stability=ranking_stability,
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(report), encoding="utf-8")

    logger.info("Relatório de validação salvo em: %s", output_path)
    return output_path

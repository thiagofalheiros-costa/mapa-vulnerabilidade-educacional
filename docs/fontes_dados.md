# Fontes de Dados

## 1. Visão geral

O **Mapa da Vulnerabilidade Educacional** utiliza bases públicas produzidas pelo Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (Inep) e pelo Instituto Brasileiro de Geografia e Estatística (IBGE). Essas fontes foram selecionadas por permitirem observar, de forma complementar, a estrutura da oferta educacional, o fluxo escolar, o contexto socioeconômico dos estudantes e a distribuição territorial dos municípios do Rio Grande do Sul.

O projeto trabalha principalmente com dados de 2024. A única exceção é o Indicador de Nível Socioeconômico (INSE), cuja versão utilizada corresponde ao ano de 2023. Essa diferença decorre do calendário de divulgação das bases oficiais e deve ser considerada na interpretação dos resultados.

## 2. Inventário das fontes

| Base | Instituição | Ano utilizado | Unidade original | Chave principal | Uso no projeto |
|---|---|---:|---|---|---|
| Censo Escolar | Inep | 2024 | Escola | `CO_ENTIDADE` e `CO_MUNICIPIO` | escolas, matrículas, localização, dependência administrativa e infraestrutura |
| Taxas de rendimento | Inep | 2024 | Município | `CO_MUNICIPIO` | aprovação, reprovação e abandono no Ensino Fundamental e no Ensino Médio |
| Distorção idade-série | Inep | 2024 | Município | `CO_MUNICIPIO` | percentual de estudantes em situação de defasagem escolar |
| Indicador de Nível Socioeconômico | Inep | 2023 | Município | `CO_MUNICIPIO` | contexto socioeconômico médio dos estudantes |
| Malha Municipal | IBGE | 2024 | Município | `CD_MUN` | geometrias utilizadas nos mapas |
| Códigos e nomes municipais | IBGE/Inep | 2024 | Município | código IBGE | padronização e integração territorial |

## 3. Censo Escolar

O Censo Escolar é a principal fonte utilizada para caracterizar a oferta educacional. A base original possui registros no nível da escola e reúne informações sobre matrículas, localização, dependência administrativa e condições de infraestrutura.

No projeto, foram selecionadas as escolas do Rio Grande do Sul e construídos indicadores municipais a partir da agregação dos registros escolares. Entre as informações utilizadas estão:

- quantidade de escolas;
- total de matrículas;
- média de matrículas por escola;
- localização urbana ou rural;
- dependência administrativa estadual ou municipal;
- existência de biblioteca;
- laboratório de informática;
- quadra esportiva;
- acesso à internet;
- disponibilidade de banda larga.

Como os municípios apresentam quantidades muito distintas de escolas, boa parte das variáveis de infraestrutura foi expressa em proporções. Dessa forma, o indicador não representa apenas o número absoluto de equipamentos existentes, mas o percentual de escolas municipais que dispõe de cada recurso.

### Arquivo processado

```text
data/processed/censo_escolar_rs_2024.parquet
```

### Principal produto derivado

```text
data/processed/municipios_features.parquet
```

## 4. Taxas de rendimento

As taxas de rendimento escolar são produzidas pelo Inep e permitem observar a situação final dos estudantes ao término do ano letivo. A base municipal utilizada no projeto contém indicadores para o Ensino Fundamental e para o Ensino Médio.

As variáveis incorporadas são:

- taxa de aprovação;
- taxa de reprovação;
- taxa de abandono.

Para a construção do IVE, foram utilizados os indicadores do Ensino Médio:

```text
APROVACAO_EM
REPROVACAO_EM
ABANDONO_EM
```

A reprovação e o abandono foram incluídos diretamente no índice por representarem situações de maior vulnerabilidade. A aprovação foi preservada na base analítica para fins de descrição e comparação, mas não integra diretamente o cálculo do IVE.

### Arquivo original utilizado

```text
data/raw/rendimento/2024/tx_rend_municipios_2024.xlsx
```

## 5. Distorção idade-série

A taxa de distorção idade-série representa o percentual de estudantes com idade superior à esperada para o ano ou série frequentada. Esse indicador permite observar trajetórias escolares marcadas por repetência, interrupções ou ingresso tardio.

A base utilizada possui informações para o Ensino Fundamental e para o Ensino Médio:

```text
DISTORCAO_EF
DISTORCAO_EM
```

No IVE, foi utilizada a variável `DISTORCAO_EM`. Valores mais elevados representam maior vulnerabilidade educacional.

### Arquivo original utilizado

```text
data/raw/distorcao/2024/TDI_MUNICIPIOS_2024.xlsx
```

## 6. Indicador de Nível Socioeconômico

O Indicador de Nível Socioeconômico (INSE) procura sintetizar características sociais e econômicas dos estudantes atendidos pelas redes e escolas. Sua inclusão no projeto busca reconhecer que os resultados educacionais não dependem apenas da estrutura das escolas, mas também das condições sociais em que os estudantes estão inseridos.

As variáveis utilizadas são:

```text
QTD_ALUNOS_INSE
MEDIA_INSE
```

`QTD_ALUNOS_INSE` informa a quantidade de estudantes considerada no cálculo do indicador. `MEDIA_INSE` representa o valor médio municipal.

Como valores mais altos de INSE indicam condições socioeconômicas mais favoráveis, a variável é invertida durante a construção do IVE. Dessa forma, municípios com menor INSE recebem maior contribuição no componente de vulnerabilidade.

A versão utilizada no projeto corresponde ao ano de 2023, pois era a publicação municipal disponível e compatível com o recorte da análise no momento da construção da base.

### Arquivo original utilizado

```text
data/raw/inse/2023/INSE_2023_municipios.xlsx
```

## 7. Malha Municipal do IBGE

A malha municipal do IBGE fornece as geometrias necessárias à representação espacial dos resultados. Ela é utilizada para construir o GeoDataFrame municipal, os mapas estáticos e o mapa interativo exibido no dashboard.

A integração ocorre por meio do código municipal. Na malha, a variável territorial original é `CD_MUN`, posteriormente padronizada para o mesmo formato adotado nas bases analíticas.

### Arquivo original utilizado

```text
data/raw/malha_municipal/2024/RS_Municipios_2024.shp
```

Como a fonte está em formato Shapefile, sua leitura depende também dos arquivos auxiliares associados, como `.dbf`, `.shx`, `.prj` e `.cpg`.

### Produto geográfico derivado

```text
data/processed/municipality_geodata.parquet
```

## 8. Integração das bases

A integração foi realizada no nível municipal, tendo `CO_MUNICIPIO` como chave principal. A base de taxas de rendimento foi adotada como referência territorial por conter os 497 municípios do Rio Grande do Sul.

O processo geral foi:

```text
Censo Escolar agregado
        │
        ├── Taxas de rendimento
        ├── Distorção idade-série
        └── INSE
                │
                ▼
      Base municipal consolidada
                │
                ▼
      Índice de Vulnerabilidade
                │
                ▼
        Integração com a malha
```

As junções foram realizadas com validação de cardinalidade `one-to-one`, garantindo que cada código municipal aparecesse apenas uma vez em cada base consolidada.

## 9. Bases processadas

Os principais produtos derivados das fontes originais são:

| Arquivo | Descrição |
|---|---|
| `censo_escolar_rs_2024.parquet` | recorte tratado do Censo Escolar para o Rio Grande do Sul |
| `municipios_features.parquet` | características agregadas das escolas no nível municipal |
| `municipality_indicators.parquet` | indicadores de rendimento, distorção e INSE consolidados |
| `municipality_base.parquet` | integração entre características escolares e indicadores educacionais |
| `municipality_vulnerability.parquet` | base final com componentes, IVE, categorias e ranking |
| `municipality_geodata.parquet` | base municipal integrada às geometrias do IBGE |

## 10. Qualidade e cobertura

A consolidação final alcançou os 497 municípios do Rio Grande do Sul. Entretanto, algumas bases apresentaram ausências pontuais:

- dois municípios sem `MEDIA_INSE` e `QTD_ALUNOS_INSE`;
- um município com ausência em indicadores de rendimento e distorção do Ensino Médio.

Essas ausências foram preservadas durante a integração. Para o cálculo do IVE, os valores ausentes dos componentes foram preenchidos pela mediana da respectiva variável, conforme descrito em `metodologia_ive.md`.

## 11. Limitações das fontes

A utilização conjunta dessas bases exige alguns cuidados.

Primeiro, os indicadores não possuem necessariamente o mesmo ano de referência. O INSE utilizado é de 2023, enquanto as demais bases centrais são de 2024. Essa diferença temporal é pequena, mas impede interpretar todos os componentes como uma fotografia estritamente simultânea.

Segundo, cada base possui metodologia própria. O fato de os dados serem integrados no nível municipal não significa que tenham sido produzidos sob os mesmos critérios de cobertura, coleta ou validação.

Terceiro, a agregação municipal pode ocultar desigualdades internas. Municípios com média semelhante podem apresentar escolas com condições muito diferentes entre si.

Por fim, os dados públicos estão sujeitos a revisões e mudanças de formato. Uma atualização futura do projeto deve verificar nomes de arquivos, colunas, níveis de agregação e cobertura antes de reutilizar o pipeline.

## 12. Uso responsável

As fontes utilizadas permitem identificar padrões territoriais e apoiar diagnósticos, mas não devem ser empregadas para responsabilizar isoladamente escolas, estudantes ou profissionais da educação.

Os indicadores retratam condições agregadas e devem ser interpretados em conjunto. O IVE funciona como instrumento de priorização e investigação, não como medida definitiva da qualidade da educação de um município.
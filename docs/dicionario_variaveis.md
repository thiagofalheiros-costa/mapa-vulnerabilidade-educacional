# Dicionário de Variáveis

## 1. Apresentação

Este documento descreve as principais variáveis utilizadas no **Mapa da Vulnerabilidade Educacional**, desde a base municipal consolidada até a construção do Índice de Vulnerabilidade Educacional (IVE).

A unidade de análise é o município. Dessa forma, cada linha da base final representa um dos 497 municípios do Rio Grande do Sul. As variáveis foram organizadas em cinco grupos: identificação territorial, estrutura da oferta educacional, infraestrutura escolar, indicadores educacionais e variáveis derivadas do IVE.

Os percentuais construídos a partir do Censo Escolar são armazenados, em geral, no intervalo entre 0 e 1. Assim, o valor `0,75`, por exemplo, corresponde a 75% das escolas do município.

---

## 2. Identificação territorial

| Variável | Descrição | Tipo | Unidade ou domínio | Fonte |
|---|---|---|---|---|
| `CO_MUNICIPIO` | Código oficial do município, utilizado como chave de integração entre as bases. | Inteiro ou texto numérico | Código IBGE | Inep/IBGE |
| `NO_MUNICIPIO` | Nome do município. | Texto | Nome oficial | Inep/IBGE |
| `SG_UF` | Sigla da Unidade da Federação. | Texto | `RS` | Inep/IBGE |

O código municipal é a principal chave de relacionamento do projeto. Sua utilização reduz problemas associados a diferenças de grafia, acentuação ou abreviação dos nomes dos municípios.

---

## 3. Estrutura da oferta educacional

| Variável | Descrição | Tipo | Unidade ou domínio | Fonte |
|---|---|---|---|---|
| `NUM_ESCOLAS` | Quantidade de escolas consideradas na agregação municipal. | Inteiro | Escolas | Censo Escolar 2024 |
| `NUM_MATRICULAS` | Soma das matrículas das escolas consideradas no município. | Numérico | Matrículas | Censo Escolar 2024 |
| `MEDIA_MATRICULAS_ESCOLA` | Média de matrículas por escola no município. | Numérico | Matrículas por escola | Variável derivada |
| `PERC_RURAL` | Proporção de escolas localizadas em área rural. | Numérico | Escala de 0 a 1 | Variável derivada do Censo Escolar |
| `PERC_PUBLICA` | Proporção de escolas públicas entre as unidades consideradas. | Numérico | Escala de 0 a 1 | Variável derivada do Censo Escolar |
| `PERC_ESTADUAL` | Proporção de escolas pertencentes à rede estadual. | Numérico | Escala de 0 a 1 | Variável derivada do Censo Escolar |
| `PERC_MUNICIPAL` | Proporção de escolas pertencentes à rede municipal. | Numérico | Escala de 0 a 1 | Variável derivada do Censo Escolar |

A média de matrículas por escola é calculada pela razão entre o total de matrículas e o número de escolas do município. No modelo atual, essa variável integra o IVE como uma medida complementar da organização da oferta educacional.

---

## 4. Infraestrutura escolar

| Variável | Descrição | Tipo | Unidade ou domínio | Fonte |
|---|---|---|---|---|
| `PERC_BIBLIOTECA` | Proporção de escolas que informaram possuir biblioteca. | Numérico | Escala de 0 a 1 | Variável derivada do Censo Escolar |
| `PERC_LAB_INFO` | Proporção de escolas que informaram possuir laboratório de informática. | Numérico | Escala de 0 a 1 | Variável derivada do Censo Escolar |
| `PERC_QUADRA` | Proporção de escolas que informaram possuir quadra esportiva. | Numérico | Escala de 0 a 1 | Variável derivada do Censo Escolar |
| `PERC_INTERNET` | Proporção de escolas com acesso à internet. | Numérico | Escala de 0 a 1 | Variável derivada do Censo Escolar |
| `PERC_BANDA_LARGA` | Proporção de escolas com conexão de banda larga. | Numérico | Escala de 0 a 1 | Variável derivada do Censo Escolar |
| `INFRA_MEDIA` | Indicador municipal sintético construído a partir das variáveis de infraestrutura escolar. | Numérico | Escala de 0 a 1 | Variável derivada |

Valores maiores em `INFRA_MEDIA` representam, em média, maior disponibilidade dos equipamentos e serviços considerados. O indicador não avalia a qualidade, o estado de conservação ou a frequência de uso desses recursos.

---

## 5. Indicadores de rendimento escolar

### 5.1. Ensino Fundamental

| Variável | Descrição | Tipo | Unidade ou domínio | Fonte |
|---|---|---|---|---|
| `APROVACAO_EF` | Taxa municipal de aprovação no Ensino Fundamental. | Numérico | Percentual | Indicadores Educacionais do Inep |
| `REPROVACAO_EF` | Taxa municipal de reprovação no Ensino Fundamental. | Numérico | Percentual | Indicadores Educacionais do Inep |
| `ABANDONO_EF` | Taxa municipal de abandono no Ensino Fundamental. | Numérico | Percentual | Indicadores Educacionais do Inep |
| `DISTORCAO_EF` | Taxa municipal de distorção idade-série no Ensino Fundamental. | Numérico | Percentual | Indicadores Educacionais do Inep |

### 5.2. Ensino Médio

| Variável | Descrição | Tipo | Unidade ou domínio | Fonte |
|---|---|---|---|---|
| `APROVACAO_EM` | Taxa municipal de aprovação no Ensino Médio. | Numérico | Percentual | Indicadores Educacionais do Inep |
| `REPROVACAO_EM` | Taxa municipal de reprovação no Ensino Médio. | Numérico | Percentual | Indicadores Educacionais do Inep |
| `ABANDONO_EM` | Taxa municipal de abandono no Ensino Médio. | Numérico | Percentual | Indicadores Educacionais do Inep |
| `DISTORCAO_EM` | Taxa municipal de distorção idade-série no Ensino Médio. | Numérico | Percentual | Indicadores Educacionais do Inep |

As taxas de rendimento descrevem a situação dos estudantes ao final do período letivo. A distorção idade-série, por sua vez, representa a proporção de estudantes com idade superior à considerada adequada para a etapa frequentada.

Na versão atual do IVE, são utilizados os indicadores do Ensino Médio de reprovação, abandono e distorção idade-série. As variáveis do Ensino Fundamental permanecem na base para fins de análise e comparação.

---

## 6. Contexto socioeconômico

| Variável | Descrição | Tipo | Unidade ou domínio | Fonte |
|---|---|---|---|---|
| `MEDIA_INSE` | Valor médio municipal do Indicador de Nível Socioeconômico dos Educandos. | Numérico | Escala própria do INSE | Inep |
| `QTD_ALUNOS_INSE` | Quantidade de estudantes considerada no cálculo do INSE municipal. | Numérico | Estudantes | Inep |

Valores maiores em `MEDIA_INSE` representam, em termos gerais, condições socioeconômicas mais favoráveis. Por esse motivo, a variável é tratada como protetiva e tem sua direção invertida durante a construção do IVE.

O INSE não deve ser interpretado como uma medida direta da renda de toda a população municipal. Ele sintetiza características socioeconômicas dos estudantes contemplados pelo indicador do Inep.

---

## 7. Componentes utilizados no IVE

O índice principal utiliza seis variáveis da base municipal consolidada.

| Variável original | Dimensão representada | Peso | Direção no índice |
|---|---|---:|---|
| `ABANDONO_EM` | Abandono escolar no Ensino Médio | 0,20 | Maior valor = maior vulnerabilidade |
| `REPROVACAO_EM` | Reprovação no Ensino Médio | 0,20 | Maior valor = maior vulnerabilidade |
| `DISTORCAO_EM` | Distorção idade-série no Ensino Médio | 0,20 | Maior valor = maior vulnerabilidade |
| `MEDIA_INSE` | Contexto socioeconômico | 0,20 | Variável protetiva; direção invertida |
| `INFRA_MEDIA` | Infraestrutura escolar | 0,10 | Variável protetiva; direção invertida |
| `MEDIA_MATRICULAS_ESCOLA` | Organização da oferta educacional | 0,10 | Maior valor = maior componente no modelo atual |

A soma dos pesos é igual a 1. A justificativa metodológica para a seleção, normalização e ponderação dessas variáveis está disponível em [`metodologia_ive.md`](metodologia_ive.md).

---

## 8. Variáveis normalizadas

Para combinar indicadores medidos em escalas diferentes, cada componente do IVE é normalizado para o intervalo entre 0 e 1. As variáveis normalizadas recebem o sufixo `_NORM`.

| Variável | Descrição |
|---|---|
| `ABANDONO_EM_NORM` | Taxa de abandono do Ensino Médio normalizada. |
| `REPROVACAO_EM_NORM` | Taxa de reprovação do Ensino Médio normalizada. |
| `DISTORCAO_EM_NORM` | Taxa de distorção idade-série do Ensino Médio normalizada. |
| `MEDIA_INSE_NORM` | INSE normalizado e invertido, de modo que valores maiores representem maior vulnerabilidade. |
| `INFRA_MEDIA_NORM` | Infraestrutura média normalizada e invertida. |
| `MEDIA_MATRICULAS_ESCOLA_NORM` | Média de matrículas por escola normalizada. |

A normalização utilizada é do tipo min-max. Após esse procedimento, o menor valor observado recebe zero e o maior recebe um, sendo os demais posicionados proporcionalmente entre esses extremos.

---

## 9. Contribuição ponderada dos componentes

Após a normalização, cada componente é multiplicado por seu respectivo peso. As variáveis resultantes recebem o sufixo `_COMPONENTE`.

| Variável | Descrição |
|---|---|
| `ABANDONO_EM_COMPONENTE` | Contribuição ponderada do abandono para o IVE. |
| `REPROVACAO_EM_COMPONENTE` | Contribuição ponderada da reprovação para o IVE. |
| `DISTORCAO_EM_COMPONENTE` | Contribuição ponderada da distorção idade-série para o IVE. |
| `MEDIA_INSE_COMPONENTE` | Contribuição ponderada da vulnerabilidade socioeconômica para o IVE. |
| `INFRA_MEDIA_COMPONENTE` | Contribuição ponderada da infraestrutura para o IVE. |
| `MEDIA_MATRICULAS_ESCOLA_COMPONENTE` | Contribuição ponderada da média de matrículas por escola para o IVE. |

Essas variáveis tornam o cálculo auditável, pois permitem identificar quanto cada dimensão acrescentou ao valor final de determinado município.

---

## 10. Variáveis finais do Índice de Vulnerabilidade Educacional

| Variável | Descrição | Tipo | Unidade ou domínio |
|---|---|---|---|
| `IVE` | Índice de Vulnerabilidade Educacional, calculado pela soma dos seis componentes ponderados. | Numérico | Escala de 0 a 1 |
| `IVE_CATEGORIA` | Categoria absoluta do IVE, definida por faixas fixas. | Categórico ordenado | Muito baixa, Baixa, Média, Alta ou Muito alta |
| `RANK_VULNERABILIDADE` | Posição do município no ranking estadual, ordenado do maior para o menor IVE. | Inteiro | 1 a 497 |

### Faixas da classificação absoluta

| Intervalo do IVE | Categoria |
|---|---|
| Até 0,20 | Muito baixa |
| Acima de 0,20 até 0,40 | Baixa |
| Acima de 0,40 até 0,60 | Média |
| Acima de 0,60 até 0,80 | Alta |
| Acima de 0,80 | Muito alta |

Valores maiores do IVE representam maior vulnerabilidade relativa às dimensões incluídas no modelo. O índice não deve ser interpretado como uma medida direta e completa da qualidade da educação municipal.

---

## 11. Resumo da base final

A base de características municipais possui 16 variáveis. A base consolidada de indicadores acrescenta dez variáveis não duplicadas, totalizando 26 colunas antes da construção do IVE.

O cálculo do índice acrescenta:

- seis variáveis normalizadas;
- seis contribuições ponderadas;
- o valor do IVE;
- a categoria absoluta;
- o ranking estadual.

Dessa forma, a base produzida diretamente pelo módulo de construção do IVE possui 41 colunas. Campos adicionais utilizados exclusivamente na apresentação do dashboard podem ser criados dinamicamente e, por esse motivo, não fazem parte do núcleo documentado neste dicionário.

---

## 12. Observações de uso

1. Percentuais derivados do Censo Escolar estão armazenados em escala de 0 a 1, enquanto os indicadores educacionais divulgados pelo Inep podem permanecer em escala percentual.
2. Valores ausentes nos componentes do IVE são preenchidos pela mediana da variável durante o cálculo do índice.
3. As variáveis normalizadas dependem dos valores mínimo e máximo observados na base utilizada. Em uma atualização futura, seus valores podem mudar mesmo para um município cujos dados originais permaneçam iguais.
4. A posição no ranking é relativa ao conjunto de municípios analisados.
5. Variáveis agregadas no nível municipal podem ocultar desigualdades existentes entre escolas do mesmo território.
6. As categorias e o ranking devem ser interpretados em conjunto com os indicadores individuais apresentados no dashboard.

# Metodologia do Índice de Vulnerabilidade Educacional

## 1. Introdução

O Índice de Vulnerabilidade Educacional (IVE) foi construído com o objetivo de sintetizar, em uma única medida, diferentes dimensões associadas às condições educacionais dos municípios do Rio Grande do Sul. A pergunta que orientou a sua construção foi relativamente simples: **quais municípios apresentam maior vulnerabilidade educacional, considerando simultaneamente indicadores de fluxo escolar, distorção idade-série, contexto socioeconômico, infraestrutura e organização da oferta?**

Apesar de simples em sua formulação, essa pergunta envolve um problema metodológico importante. A vulnerabilidade educacional não se manifesta por meio de uma única variável. Um município pode apresentar baixa taxa de abandono, mas conviver com elevada reprovação; pode possuir escolas com boa infraestrutura, mas atender uma população inserida em um contexto socioeconômico mais desfavorável; ou ainda apresentar resultados medianos em todas as dimensões, sem que nenhuma delas, isoladamente, revele a situação do território.

Nesse sentido, o IVE foi concebido como um **índice composto**, isto é, uma medida sintética produzida a partir da combinação de diferentes indicadores. Seu objetivo não é substituir a leitura individual das variáveis, tampouco estabelecer uma explicação causal para os resultados educacionais, mas oferecer uma forma padronizada de comparação entre os 497 municípios do estado.

## 2. Unidade de análise e recorte

A unidade de análise adotada é o município. A opção pelo nível municipal decorre de três motivos principais. Primeiro, porque os municípios são unidades relevantes para o planejamento e a execução de políticas públicas educacionais, especialmente no que se refere à oferta, manutenção das escolas e organização das redes. Segundo, porque a integração das diferentes fontes de dados se mostrou mais estável no nível municipal. Por fim, esse recorte permite articular os indicadores educacionais à dimensão territorial, possibilitando a construção de mapas e a identificação de padrões regionais.

O recorte territorial compreende os 497 municípios do Rio Grande do Sul, tendo como ano-base principal 2024. As fontes utilizadas foram produzidas pelo Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (Inep), com complementação da malha territorial do Instituto Brasileiro de Geografia e Estatística (IBGE).

## 3. Dimensões consideradas

A construção do índice buscou reunir dimensões que representassem aspectos distintos da vulnerabilidade educacional. Foram selecionados seis componentes:

| Variável | Dimensão | Interpretação |
|---|---|---|
| `ABANDONO_EM` | fluxo escolar | maior valor indica maior vulnerabilidade |
| `REPROVACAO_EM` | fluxo escolar | maior valor indica maior vulnerabilidade |
| `DISTORCAO_EM` | trajetória escolar | maior valor indica maior vulnerabilidade |
| `MEDIA_INSE` | contexto socioeconômico | maior valor indica menor vulnerabilidade |
| `INFRA_MEDIA` | condições de oferta | maior valor indica menor vulnerabilidade |
| `MEDIA_MATRICULAS_ESCOLA` | organização da oferta | maior valor aumenta o componente de vulnerabilidade |

A escolha dessas variáveis procurou equilibrar três perspectivas. A primeira diz respeito ao desempenho do fluxo escolar, representado por abandono, reprovação e distorção idade-série. A segunda trata das condições sociais e materiais nas quais o processo educacional ocorre, incorporando o nível socioeconômico e a infraestrutura. A terceira considera a forma como a oferta está organizada, utilizando a média de matrículas por escola como medida complementar.

Cabe destacar que nenhuma dessas dimensões, isoladamente, é suficiente para classificar um município como vulnerável. O abandono pode ser baixo em determinado território, por exemplo, mas coexistir com alta distorção idade-série e condições socioeconômicas mais desfavoráveis. É justamente a combinação dos componentes que permite produzir uma leitura mais abrangente.

## 4. Tratamento dos valores ausentes

Antes da normalização, as variáveis são convertidas para formato numérico. Quando há valores ausentes, o preenchimento é realizado pela mediana da própria variável.

A escolha da mediana decorre da sua menor sensibilidade a valores extremos. Em comparação à média, ela tende a produzir uma imputação mais conservadora quando a distribuição é assimétrica. Além disso, como as ausências observadas na base final eram pontuais, o procedimento permitiu preservar os municípios na análise sem alterar de forma expressiva a estrutura geral dos dados.

Este tratamento não significa que a ausência de informação deixou de ser uma limitação. O preenchimento foi adotado como solução operacional para a construção do índice, mas a cobertura das fontes deve continuar sendo observada durante futuras atualizações.

## 5. Normalização dos indicadores

Os componentes do IVE possuem escalas distintas. Enquanto abandono, reprovação e distorção são expressos em percentuais, o INSE utiliza uma escala própria, e a infraestrutura média é derivada de proporções de equipamentos e serviços escolares. Para que essas variáveis pudessem ser combinadas, todas foram normalizadas para o intervalo entre 0 e 1.

Foi utilizada a normalização min-max:

```math
x'_{ij} = \frac{x_{ij} - \min(x_j)}{\max(x_j) - \min(x_j)}
```

onde:

- `x_ij` corresponde ao valor do município `i` na variável `j`;
- `min(x_j)` é o menor valor observado na variável;
- `max(x_j)` é o maior valor observado;
- `x'_ij` é o valor normalizado.

Como resultado, o município com o menor valor observado em uma variável recebe zero, enquanto o município com o maior valor recebe um. Os demais são posicionados proporcionalmente entre esses extremos.

A opção pela normalização min-max foi tomada, principalmente, por facilitar a interpretação dos componentes. Como o índice final também permanece no intervalo entre 0 e 1, torna-se possível compreender a contribuição de cada variável de forma direta. Por outro lado, essa estratégia é sensível a valores extremos, motivo pelo qual a distribuição das variáveis foi inspecionada antes da construção do índice.

Caso uma variável apresente o mesmo valor para todos os municípios, seu componente normalizado recebe zero. Essa regra evita divisão por zero e, ao mesmo tempo, reconhece que uma variável sem variação não contribui para diferenciar os territórios.

## 6. Orientação das variáveis

Para que os componentes pudessem ser somados, todos precisavam seguir a mesma direção: valores maiores deveriam representar maior vulnerabilidade.

Abandono, reprovação, distorção idade-série e média de matrículas por escola já seguem essa orientação no modelo adotado. No caso do INSE e da infraestrutura média, a interpretação é inversa, pois valores maiores representam condições mais favoráveis. Por esse motivo, essas variáveis foram invertidas após a normalização:

```math
x''_{ij} = 1 - x'_{ij}
```

Assim, um município com alto INSE passa a receber um valor menor no componente de vulnerabilidade socioeconômica, enquanto um município com baixo INSE recebe um valor maior. A mesma lógica foi aplicada à infraestrutura.

Essa etapa é fundamental. Sem a inversão, municípios com melhores condições socioeconômicas ou materiais receberiam pontuações maiores no índice, produzindo uma interpretação contraditória.

## 7. Definição dos pesos

Os pesos utilizados no IVE são:

| Componente | Peso |
|---|---:|
| abandono | 0,20 |
| reprovação | 0,20 |
| distorção idade-série | 0,20 |
| nível socioeconômico | 0,20 |
| infraestrutura média | 0,10 |
| média de matrículas por escola | 0,10 |
| **Total** | **1,00** |

A definição dos pesos buscou equilibrar duas preocupações. De um lado, abandono, reprovação e distorção idade-série representam resultados diretamente relacionados à trajetória dos estudantes e, por esse motivo, receberam peso relevante. Do outro, a vulnerabilidade educacional não poderia ser interpretada apenas como um problema de fluxo, sendo necessário incorporar o contexto socioeconômico com peso equivalente.

A infraestrutura e a média de matrículas por escola foram mantidas como dimensões complementares, cada uma com peso de 10%. Essa decisão evita que condições materiais e organização da oferta dominem o índice, ao mesmo tempo em que reconhece que ambas influenciam o contexto em que as escolas operam.

Os pesos possuem, portanto, uma fundamentação substantiva. Eles não foram estimados diretamente por um algoritmo, mas definidos a partir da interpretação das dimensões e posteriormente submetidos a estratégias de validação estatística.

## 8. Fórmula do IVE

O índice é calculado pela soma ponderada dos componentes normalizados:

```math
IVE_i = \sum_{j=1}^{6} w_j z_{ij}
```

onde:

- `IVE_i` é o índice do município `i`;
- `w_j` é o peso do componente `j`;
- `z_ij` é o valor normalizado e orientado do município `i` no componente `j`.

De forma expandida:

```math
IVE_i =
0{,}20A_i +
0{,}20R_i +
0{,}20D_i +
0{,}20S_i +
0{,}10I_i +
0{,}10M_i
```

em que:

- `A` representa abandono normalizado;
- `R` representa reprovação normalizada;
- `D` representa distorção idade-série normalizada;
- `S` representa o INSE normalizado e invertido;
- `I` representa a infraestrutura normalizada e invertida;
- `M` representa a média de matrículas por escola normalizada.

O resultado é limitado ao intervalo entre 0 e 1. Valores mais próximos de zero indicam menor vulnerabilidade relativa às dimensões consideradas, enquanto valores mais próximos de um indicam maior vulnerabilidade.

## 9. Classificação absoluta

Após o cálculo, o IVE é classificado em cinco categorias fixas:

| Intervalo | Categoria |
|---|---|
| até 0,20 | Muito baixa |
| acima de 0,20 até 0,40 | Baixa |
| acima de 0,40 até 0,60 | Média |
| acima de 0,60 até 0,80 | Alta |
| acima de 0,80 | Muito alta |

A classificação absoluta utiliza os mesmos pontos de corte para todos os municípios. Seu principal ganho é a estabilidade interpretativa: um município com IVE 0,45 será classificado como vulnerabilidade média independentemente da distribuição dos demais.

Por outro lado, a classificação absoluta pode produzir grupos desequilibrados. Isso aconteceu na aplicação atual, em que a maioria dos municípios se concentrou nas categorias muito baixa e baixa, enquanto poucos alcançaram as faixas superiores. Esse resultado não deve ser interpretado como um erro, mas como consequência da própria distribuição do índice e dos pontos de corte fixos.

## 10. Ranking estadual

Além das categorias, foi construído um ranking em ordem decrescente. O município com o maior IVE ocupa a primeira posição, seguido pelos demais.

O ranking permite identificar prioridades relativas mesmo quando dois municípios pertencem à mesma categoria. Em outras palavras, ele preserva a informação contínua do índice e facilita a comparação entre territórios próximos.

Em casos de valores iguais, a ordenação utiliza a ordem de ocorrência na base para atribuir posições distintas. Na prática, empates exatos são pouco prováveis devido à combinação de seis componentes contínuos.

## 11. Resultados descritivos

Na versão atual da base, o índice foi calculado para os 497 municípios do Rio Grande do Sul. O resumo estatístico foi:

| Medida | Valor |
|---|---:|
| média | 0,281 |
| desvio-padrão | 0,087 |
| mínimo | 0,057 |
| primeiro quartil | 0,221 |
| mediana | 0,278 |
| terceiro quartil | 0,336 |
| máximo | 0,648 |

A distribuição absoluta das categorias foi:

| Categoria | Municípios | Percentual |
|---|---:|---:|
| Muito baixa | 87 | 17,51% |
| Baixa | 367 | 73,84% |
| Média | 41 | 8,25% |
| Alta | 2 | 0,40% |
| Muito alta | 0 | 0,00% |

Esses resultados demonstram uma distribuição concentrada abaixo de 0,40. Contudo, isso não significa ausência de desigualdade entre os municípios. Mesmo dentro da categoria baixa, há diferenças importantes na composição do índice e na posição do ranking.

## 12. Validação por métodos multivariados

A adoção de pesos substantivos exige verificar se o índice produzido guarda relação com estruturas identificadas nos próprios dados. Para isto, o IVE manual foi comparado a dois métodos multivariados: Análise de Componentes Principais (PCA) e Análise Fatorial.

### 12.1. Análise de Componentes Principais

A PCA busca resumir a variância compartilhada entre as variáveis por meio de combinações lineares. Na aplicação realizada, a primeira componente explicou aproximadamente 33,23% da variância total.

As maiores cargas positivas foram observadas em:

- distorção idade-série: aproximadamente 0,577;
- abandono: aproximadamente 0,475;
- reprovação: aproximadamente 0,473.

O INSE apresentou carga negativa, de aproximadamente -0,354, coerente com a expectativa de que melhores condições socioeconômicas estejam associadas a menor vulnerabilidade.

Esse resultado foi importante porque a estrutura extraída pela PCA se mostrou substantivamente próxima à lógica do IVE manual: os indicadores de fluxo e trajetória escolar apresentaram contribuição positiva, enquanto o contexto socioeconômico seguiu direção inversa.

### 12.2. Análise Fatorial

A adequação da base à análise fatorial foi examinada pelos testes de Kaiser-Meyer-Olkin (KMO) e esfericidade de Bartlett.

O KMO global foi de aproximadamente 0,605, valor considerado suficiente para uma análise exploratória, ainda que não indique uma estrutura fatorial particularmente forte. O teste de Bartlett apresentou significância estatística, com valor de `p` próximo a `5,10 × 10⁻⁷⁸`, rejeitando a hipótese de uma matriz de correlações identidade.

A solução adotada extraiu dois fatores. Embora a análise tenha contribuído para compreender agrupamentos entre as variáveis, sua correspondência com o ranking manual foi inferior à observada na PCA.

## 13. Estabilidade dos rankings

A validação não se limitou à comparação de correlações entre os valores dos índices. Também foi examinada a concordância entre os municípios localizados nas primeiras posições dos rankings.

Na comparação entre IVE manual e PCA, foram observados:

- 8 municípios em comum entre os 10 primeiros;
- 16 em comum entre os 20 primeiros;
- 41 em comum entre os 50 primeiros;
- 85 em comum entre os 100 primeiros.

A concordância foi, portanto, de 80% nos grupos de 10 e 20 municípios, 82% no grupo de 50 e 85% no grupo de 100.

A análise fatorial apresentou menor concordância com o IVE manual, especialmente entre os primeiros colocados. Esse resultado reforçou a decisão de manter a abordagem manual como medida principal, utilizando os métodos multivariados como validação complementar e não como substituição automática.

## 14. Justificativa para a manutenção do IVE manual

A escolha final pelo IVE manual não representa uma rejeição aos métodos estatísticos. Pelo contrário, PCA e Análise Fatorial foram fundamentais para testar a coerência da estrutura construída.

Entretanto, um índice voltado à comunicação e ao apoio a políticas públicas precisa ser não apenas estatisticamente defensável, mas também interpretável. No IVE manual, é possível identificar de forma transparente:

- quais variáveis foram utilizadas;
- por que foram selecionadas;
- qual a direção de cada componente;
- quanto cada variável contribui para o resultado;
- como o valor final foi calculado.

Na PCA e na Análise Fatorial, os pesos são derivados da estrutura de correlação observada. Isso pode ser adequado em determinados objetivos, mas também faz com que o significado do índice dependa fortemente da distribuição específica da amostra. Além disso, uma variável pode receber maior peso porque apresenta maior variância compartilhada, e não necessariamente porque possui maior relevância substantiva para a política educacional.

Diante disso, a forte concordância entre o IVE manual e a PCA, especialmente entre os municípios mais vulneráveis, foi interpretada como evidência favorável à robustez da medida originalmente construída.

## 15. Interpretação adequada do índice

O IVE deve ser interpretado como uma medida comparativa e multidimensional. Um valor elevado indica que o município acumula condições menos favoráveis em parte relevante dos componentes analisados.

Todavia, o índice não permite afirmar, isoladamente, por que determinado município apresenta maior vulnerabilidade. Dois territórios com valores semelhantes podem alcançar esse resultado por combinações distintas. Em um deles, abandono e reprovação podem ser os principais fatores; em outro, o baixo INSE e a infraestrutura podem exercer maior influência.

Por esse motivo, o dashboard apresenta o IVE em conjunto com o perfil municipal, os componentes individuais e a comparação com as médias estaduais. O índice deve funcionar como ponto de partida para a investigação, e não como conclusão definitiva.

## 16. Limitações metodológicas

A construção de um índice composto envolve decisões normativas. A seleção das variáveis, os pesos, o método de normalização e os pontos de corte afetam o resultado final. Ainda que essas escolhas tenham sido documentadas e validadas, outras combinações metodologicamente defensáveis poderiam produzir rankings diferentes.

Também devem ser consideradas as seguintes limitações:

- o recorte utiliza principalmente dados de 2024 e não capta tendências históricas;
- os indicadores são agregados no nível municipal e podem ocultar desigualdades entre escolas;
- a normalização min-max depende dos valores extremos observados;
- a imputação pela mediana reduz perdas, mas não substitui a informação original;
- a média de infraestrutura sintetiza equipamentos distintos e não mede sua qualidade de uso;
- o INSE representa o contexto dos estudantes cobertos pelo indicador, não toda a população municipal;
- o índice não estabelece relações causais;
- a classificação absoluta depende de pontos de corte definidos previamente.

Outro ponto importante diz respeito ao risco de estigmatização. Classificar um município como mais vulnerável não significa atribuir responsabilidade às escolas, profissionais ou estudantes daquele território. A medida busca justamente evidenciar condições que podem demandar maior atenção e suporte por parte das políticas públicas.

## 17. Possíveis evoluções

O IVE poderá ser aprimorado por meio de:

- inclusão de séries históricas;
- análise da estabilidade temporal dos pesos e rankings;
- cálculo no nível da escola;
- incorporação de indicadores de aprendizagem;
- inclusão de medidas demográficas e territoriais;
- testes de sensibilidade com diferentes pesos;
- construção de intervalos de incerteza;
- validação externa com resultados educacionais não utilizados no índice;
- participação de especialistas e gestores na revisão dos componentes.

Uma evolução particularmente relevante seria comparar o índice a resultados observados em anos posteriores, verificando se municípios com maior IVE apresentam maior persistência de abandono, reprovação ou distorção. Tal exercício ampliaria a validade preditiva da medida, sem alterar seu caráter principal de diagnóstico territorial.

## 18. Síntese

Em linhas gerais, o IVE foi construído como uma medida transparente, replicável e substantivamente orientada. Sua principal contribuição está em organizar diferentes informações em uma escala comum, possibilitando a comparação entre municípios e a identificação de territórios que podem demandar maior atenção.

A validação por PCA e Análise Fatorial mostrou que a estrutura definida manualmente não está dissociada dos padrões presentes nos dados. Ao mesmo tempo, a manutenção dos pesos substantivos preserva a interpretabilidade do índice e facilita o seu uso em contextos de gestão e comunicação pública.

Portanto, o IVE não deve ser lido como uma medida definitiva da qualidade da educação, mas como um instrumento de apoio ao diagnóstico. Seu valor está menos em produzir uma classificação isolada e mais em estimular perguntas: quais componentes explicam a posição de cada município? Quais territórios acumulam diferentes formas de desvantagem? E, sobretudo, quais ações podem ser planejadas a partir dessas informações?
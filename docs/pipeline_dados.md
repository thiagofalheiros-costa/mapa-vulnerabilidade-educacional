# Pipeline de Dados

## 1. Introdução

O pipeline do **Mapa da Vulnerabilidade Educacional** foi construído para transformar bases públicas, originalmente produzidas em diferentes formatos e níveis de agregação, em uma base municipal única, consistente e adequada à construção do Índice de Vulnerabilidade Educacional (IVE).

A opção por organizar o projeto em etapas sucessivas decorre de uma questão prática: os dados educacionais utilizados não foram concebidos para funcionar, de forma imediata, como uma única base analítica. Cada fonte possui estrutura própria, periodicidade específica, nomes de variáveis distintos e diferentes critérios de divulgação. Nesse sentido, o pipeline cumpre a função de aproximar essas bases, produzir chaves comuns e garantir que cada município seja representado por um único registro ao final do processo.

## 2. Visão geral

```mermaid
flowchart LR
    A[Arquivos brutos] --> B[Inspeção]
    B --> C[Padronização]
    C --> D[Filtragem do recorte]
    D --> E[Agregação municipal]
    E --> F[Engenharia de atributos]
    F --> G[Integração dos indicadores]
    G --> H[Validação da base]
    H --> I[Construção do IVE]
    I --> J[Validação estatística]
    J --> K[Integração geoespacial]
    K --> L[Dashboard]
```

## 3. Fontes de dados

O pipeline articula quatro conjuntos centrais de informações:

1. **Censo Escolar 2024**, utilizado para identificar escolas, matrículas, dependência administrativa, localização e condições de infraestrutura;
2. **Indicadores de rendimento do Inep**, utilizados para incorporar aprovação, reprovação e abandono;
3. **Indicadores de distorção idade-série e nível socioeconômico**, utilizados para representar defasagem escolar e contexto social;
4. **Malha Municipal do IBGE**, utilizada para integrar os resultados à dimensão territorial.

A chave de integração adotada é o código do município. Em termos operacionais, essa decisão foi fundamental, visto que nomes de municípios podem apresentar diferenças de grafia, acentuação ou abreviação entre as fontes.

## 4. Etapa de inspeção

A primeira etapa consiste em examinar a estrutura dos arquivos antes da transformação. O objetivo é identificar:

- quantidade de linhas e colunas;
- nomes e tipos das variáveis;
- codificação dos arquivos;
- separadores utilizados;
- valores ausentes;
- duplicidades aparentes;
- colunas necessárias ao recorte analítico.

Os relatórios produzidos nesta etapa reduzem o risco de que mudanças silenciosas nas bases públicas sejam incorporadas ao pipeline sem verificação.

## 5. Pré-processamento do Censo Escolar

O Censo Escolar é disponibilizado no nível da escola. Como a unidade de análise do projeto é o município, foi necessário realizar um conjunto de filtros e transformações.

O recorte considera:

- escolas localizadas no Rio Grande do Sul;
- ano-base de 2024;
- redes estadual e municipais;
- variáveis necessárias à caracterização municipal.

Após a seleção das colunas, os dados são padronizados e salvos em formato Parquet. A utilização desse formato permitiu reduzir o tempo de leitura, preservar os tipos das variáveis e evitar a repetição do processamento dos arquivos originais.

## 6. Agregação municipal

A agregação converte registros escolares em indicadores municipais. Entre os produtos construídos estão:

- número de escolas;
- número de matrículas;
- média de matrículas por escola;
- percentual de escolas rurais;
- percentual de escolas públicas;
- participação das redes estadual e municipal;
- percentuais de bibliotecas, laboratórios de informática, quadras, internet e banda larga;
- indicador médio de infraestrutura.

Em vez de simplesmente somar variáveis binárias, as estruturas escolares foram expressas, em grande parte, como proporções. Esse procedimento permite comparar municípios com quantidades muito diferentes de escolas.

## 7. Engenharia de atributos

A engenharia de atributos foi orientada pela necessidade de transformar variáveis escolares em medidas substantivamente interpretáveis no nível municipal.

A infraestrutura média, por exemplo, sintetiza a disponibilidade de diferentes equipamentos e serviços escolares. Da mesma forma, a média de matrículas por escola foi mantida como uma medida complementar da organização da oferta educacional.

Cabe destacar que essas variáveis não devem ser interpretadas isoladamente como medidas de qualidade da educação. Elas representam dimensões contextuais que, combinadas a indicadores de fluxo e nível socioeconômico, ajudam a descrever situações de maior ou menor vulnerabilidade.

## 8. Integração dos indicadores educacionais

A base de características municipais é integrada aos indicadores de rendimento, distorção idade-série e nível socioeconômico.

O processo inclui:

- padronização dos códigos municipais;
- verificação da unicidade das chaves;
- seleção das etapas de ensino compatíveis com o projeto;
- renomeação das variáveis;
- junção das bases;
- diagnóstico de valores ausentes após o merge.

A base consolidada resultante contém um registro por município e reúne informações de estrutura, oferta, fluxo escolar e contexto socioeconômico.

## 9. Tratamento de valores ausentes

A presença de valores ausentes foi tratada de forma conservadora. Nos componentes utilizados no IVE, a normalização preenche ausências pela mediana da própria variável.

A escolha da mediana busca reduzir a influência de valores extremos. Ao mesmo tempo, o procedimento evita a exclusão completa de municípios em função de poucas ausências pontuais.

Esse tratamento não elimina a necessidade de registrar as limitações da cobertura. Por esse motivo, as ausências são verificadas antes e depois da integração.

## 10. Validação da base municipal

Antes da construção do índice, a base é submetida a verificações de consistência:

- presença das colunas obrigatórias;
- quantidade esperada de municípios;
- unicidade do código municipal;
- tipos numéricos;
- valores fora de intervalos plausíveis;
- proporções fora da escala esperada;
- quantidade de ausências;
- duplicidades.

A base municipal final alcançou os 497 municípios do Rio Grande do Sul.

## 11. Construção da base de vulnerabilidade

Com a base consolidada, o pipeline executa:

1. seleção dos componentes do índice;
2. normalização min-max;
3. inversão das variáveis protetivas;
4. aplicação dos pesos;
5. soma dos componentes;
6. classificação por categoria;
7. construção do ranking estadual.

O resultado é salvo em `data/processed/municipality_vulnerability.parquet`.

## 12. Integração geoespacial

A base com o IVE é integrada à malha municipal do IBGE. Essa etapa exige especial atenção à padronização dos códigos, tendo em vista que a malha pode conter geometrias ou registros administrativos que não correspondem diretamente aos 497 municípios analisados.

O resultado é uma base geográfica em formato Parquet, utilizada na construção dos mapas estáticos e do mapa interativo do dashboard.

## 13. Produtos do pipeline

Os principais produtos são:

```text
data/processed/censo_escolar_rs_2024.parquet
data/processed/municipios_features.parquet
data/processed/municipality_indicators.parquet
data/processed/municipality_base.parquet
data/processed/municipality_vulnerability.parquet
data/processed/municipality_geodata.parquet
```

Cada arquivo representa uma etapa lógica do processamento. Essa separação permite inspecionar resultados intermediários e facilita a identificação de erros.

## 14. Reprodutibilidade

A reprodutibilidade é sustentada por quatro elementos:

- caminhos relativos centralizados em `src/config.py`;
- bases processadas em formato Parquet;
- dependências declaradas em arquivos próprios;
- testes automatizados.

O pipeline analítico não é executado a cada inicialização do dashboard. Em produção, a aplicação consome os produtos finais previamente construídos, reduzindo o tempo de carregamento.

## 15. Limitações

O pipeline atual depende do download manual de algumas bases e da manutenção dos formatos de divulgação adotados pelo Inep e pelo IBGE. Caso uma fonte altere nomes de colunas, planilhas ou níveis de agregação, parte do processamento poderá precisar de revisão.

Além disso, a integração municipal não elimina diferenças conceituais entre as fontes. O fato de todas as variáveis estarem no mesmo nível territorial não significa que tenham sido produzidas sob o mesmo desenho metodológico.

## 16. Síntese

Em linhas gerais, o pipeline cumpre a função de transformar dados dispersos em uma estrutura analítica coerente. Seu principal ganho não está apenas na geração do IVE, mas na construção de uma base municipal documentada, passível de atualização, validação e reutilização em outras análises educacionais.
# Changelog

Todas as alterações relevantes do **Mapa da Vulnerabilidade Educacional** são registradas neste arquivo.

O formato segue, de maneira adaptada, as recomendações do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e os princípios de [Versionamento Semântico](https://semver.org/lang/pt-BR/). As versões anteriores à `1.0.0` representam marcos de desenvolvimento do projeto e não necessariamente correspondem a releases publicadas no GitHub.

## [1.0.0] - 2026-08-06

### Adicionado

- documentação profissional da arquitetura do projeto;
- documentação do pipeline de dados;
- documentação metodológica completa do Índice de Vulnerabilidade Educacional;
- dicionário analítico das variáveis;
- documentação revisada das fontes de dados;
- README profissional em português;
- licença MIT;
- changelog consolidado do desenvolvimento do projeto.

### Alterado

- reorganização da documentação para a primeira versão estável;
- atualização da apresentação do projeto, refletindo o dashboard publicado, a validação estatística e a integração com IA generativa;
- reorganização do `src/config.py`, com caminhos e constantes agrupados por natureza;
- padronização dos diretórios de dados brutos;
- limpeza e reorganização das regras do `.gitignore`;
- inclusão explícita das três bases processadas necessárias ao dashboard no versionamento.

### Removido

- arquivos vazios e sem utilização:
  - `src/download_data.py`;
  - `src/feature_engineering.py`;
  - `dashboard/components/metrics.py`;
  - `docs/metodologia.md`.

## [0.13.0] - 2026-08-06

### Adicionado

- deploy do dashboard no Streamlit Community Cloud;
- configuração da chave `GEMINI_API_KEY` por meio dos Secrets do Streamlit;
- inclusão das bases Parquet necessárias à aplicação em produção;
- inclusão da malha municipal e do arquivo `municipality_geodata.parquet` no ambiente publicado;
- arquivo `.python-version` para definição da versão do Python;
- modelos de configuração `.env.example` e `.streamlit/secrets.toml.example`.

### Alterado

- revisão do `requirements.txt`, mantendo apenas as dependências necessárias ao dashboard;
- adequação dos caminhos para funcionamento em ambiente local e no Linux do Streamlit Cloud;
- configuração do ambiente para execução reproduzível.

### Corrigido

- erro de bases municipais não localizadas no ambiente de deploy;
- ausência do mapa Folium causada pela falta dos arquivos geoespaciais no repositório;
- configuração da API do Gemini em produção;
- dependência ausente do pacote `branca`.

## [0.12.0] - 2026-08-04

### Adicionado

- testes de regressão para os componentes do dashboard e da integração com o Gemini;
- testes para criação do cliente Gemini, validação de prompts, respostas vazias, erros da API e uso de cache;
- validações adicionais sobre a base e os componentes analíticos.

### Alterado

- refatoração dos serviços de IA e dos componentes do dashboard;
- melhoria da organização interna dos módulos;
- revisão do tratamento de erros e das mensagens apresentadas ao usuário.

### Corrigido

- inconsistência na mensagem de erro para prompts vazios;
- referência indevida ao valor `497` em buscas amplas no código;
- identificação correta da variável `QT_MAT_BAS`.

## [0.11.0] - 2026-08-04

### Alterado

- otimização do carregamento e da renderização do mapa Folium;
- reorganização dos componentes relacionados ao mapa e às análises gerais;
- redução de operações repetidas durante a navegação no dashboard.

### Corrigido

- exibição da camada de municípios prioritários;
- problemas de desempenho na atualização do mapa;
- integração entre filtros, mapa e base geográfica.

## [0.10.0] - 2026-08-03

### Adicionado

- integração com a API do Gemini;
- geração de análises municipais em linguagem natural;
- geração de interpretações para a distribuição do IVE, o gráfico de dispersão e a matriz de correlação;
- serviço centralizado de conexão com o Gemini;
- construção de prompts específicos para municípios e visualizações;
- cache das respostas geradas pela IA;
- controles para gerar, ocultar e reexibir as análises.

### Alterado

- substituição das percepções fixas por análises geradas dinamicamente;
- reorganização dos módulos `gemini_service.py`, `municipality_insights.py`, `chart_insights.py` e `municipality_profile.py`;
- apresentação do diagnóstico municipal antes do mapa.

### Corrigido

- carregamento da variável `GEMINI_API_KEY` a partir do arquivo `.env`;
- reconhecimento do município selecionado nos prompts;
- repetição desnecessária de chamadas à API.

## [0.9.0] - 2026-07-31

### Adicionado

- dashboard interativo em Streamlit;
- filtros por faixa e categoria do IVE;
- indicadores gerais da base;
- perfil detalhado dos municípios;
- ranking estadual;
- gráfico de distribuição das categorias do IVE;
- gráfico de dispersão entre infraestrutura e vulnerabilidade;
- matriz de correlação dos indicadores;
- comparação entre indicadores municipais e médias estaduais;
- mapa interativo integrado ao dashboard.

### Alterado

- padronização da formatação numérica em português;
- aprimoramento dos tooltips e títulos dos gráficos;
- reorganização da disposição dos componentes da interface;
- remoção de rótulos e linhas de tendência que prejudicavam a leitura.

### Corrigido

- duplicidade na renderização do mapa;
- ordenação e exibição das categorias do IVE;
- caracteres especiais em gráficos;
- inversão das cores do gráfico de dispersão;
- compatibilidade com mudanças da API do Streamlit.

## [0.8.0] - 2026-07-29

### Adicionado

- integração da base do IVE com a malha municipal do IBGE;
- GeoDataFrame dos municípios do Rio Grande do Sul;
- mapa contínuo do IVE;
- mapa por categorias de vulnerabilidade;
- mapa de municípios prioritários;
- mapa interativo em Folium;
- escala cartográfica e indicação do norte;
- exportação da base geoespacial em formato Parquet.

### Corrigido

- remoção dos registros territoriais `4300001` e `4300002`, que não correspondem aos 497 municípios analisados;
- padronização dos códigos municipais para a junção com a malha;
- aplicação correta da paleta cartográfica no mapa interativo.

## [0.7.0] - 2026-07-23

### Adicionado

- validação do IVE por Análise de Componentes Principais;
- validação por Análise Fatorial;
- teste de Kaiser-Meyer-Olkin;
- teste de esfericidade de Bartlett;
- comparação entre o IVE manual, o índice da PCA e o índice fatorial;
- análise de estabilidade dos rankings para os grupos Top 10, 20, 50 e 100;
- cálculo de concordância e índice de Jaccard;
- relatório de validação estatística.

### Decidido

- manutenção do IVE manual como medida principal, em razão da sua interpretabilidade e da elevada concordância com a PCA entre os municípios prioritários.

## [0.6.0] - 2026-07-21

### Adicionado

- construção do Índice de Vulnerabilidade Educacional;
- normalização dos componentes para a escala entre 0 e 1;
- inversão das variáveis protetivas;
- aplicação dos pesos substantivos;
- classificação absoluta e relativa dos municípios;
- ranking estadual de vulnerabilidade;
- relatórios descritivos da distribuição do índice.

### Resultado

- cálculo do IVE para os 497 municípios do Rio Grande do Sul;
- média estadual de aproximadamente `0,281`;
- valores entre aproximadamente `0,057` e `0,648`.

## [0.5.0] - 2026-07-17

### Adicionado

- integração das taxas de rendimento, do INSE e da distorção idade-série;
- base consolidada de indicadores municipais;
- construção da `municipality_base.parquet`;
- validação da unicidade dos municípios, das colunas obrigatórias e dos valores ausentes;
- relatórios de qualidade da base municipal.

### Resultado

- base final com 497 municípios e 26 variáveis antes da construção do IVE.

## [0.4.0] - 2026-07-17

### Adicionado

- engenharia de atributos no nível municipal;
- número de escolas e matrículas;
- média de matrículas por escola;
- proporções de localização e dependência administrativa;
- indicadores de biblioteca, laboratório de informática, quadra, internet e banda larga;
- indicador médio de infraestrutura.

### Resultado

- base municipal de características com 497 municípios e 16 variáveis.

## [0.3.0] - 2026-07-13

### Adicionado

- agregação dos registros escolares no nível municipal;
- criação de atributos derivados do Censo Escolar;
- testes automatizados para agregação e engenharia de variáveis;
- validações de intervalos, duplicidades e quantidade de municípios.

## [0.2.0] - 2026-07-13

### Adicionado

- leitura e inspeção dos microdados do Censo Escolar 2024;
- recorte das escolas do Rio Grande do Sul;
- seleção das variáveis necessárias ao MVP;
- geração de relatórios de estrutura, amostras e valores ausentes;
- exportação da base tratada em formato Parquet.

## [0.1.0] - 2026-07-09

### Adicionado

- definição do problema e do escopo inicial do projeto;
- estrutura de diretórios para dados, código, testes, relatórios, dashboard e documentação;
- módulos iniciais de configuração, carregamento de dados, utilidades e execução;
- definição do município como unidade de análise do MVP;
- adoção do Rio Grande do Sul como recorte territorial inicial.

[1.0.0]: https://github.com/thiagofalheiros-costa/mapa-vulnerabilidade-educacional/releases/tag/v1.0.0

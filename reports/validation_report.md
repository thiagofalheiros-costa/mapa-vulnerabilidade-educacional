# Relatório de Validação Estatística do IVE

## Objetivo

Avaliar a robustez do Índice de Vulnerabilidade Educacional (IVE) por meio de Análise de Componentes Principais, análise fatorial exploratória, correlações entre métodos e estabilidade dos rankings municipais.

## Análise de Componentes Principais

| COMPONENTE   |   AUTOVALOR |   VARIANCIA_EXPLICADA |   VARIANCIA_EXPLICADA_PERCENTUAL |   VARIANCIA_ACUMULADA_PERCENTUAL |
|:-------------|------------:|----------------------:|---------------------------------:|---------------------------------:|
| CP_1         |      1.9977 |                0.3323 |                          33.2282 |                          33.2282 |
| CP_2         |      1.4486 |                0.2410 |                          24.0952 |                          57.3234 |
| CP_3         |      0.7827 |                0.1302 |                          13.0194 |                          70.3429 |
| CP_4         |      0.7686 |                0.1278 |                          12.7836 |                          83.1265 |
| CP_5         |      0.5719 |                0.0951 |                           9.5129 |                          92.6393 |
| CP_6         |      0.4425 |                0.0736 |                           7.3607 |                         100.0000 |

### Cargas da PCA

| VARIAVEL                     |    CP_1 |    CP_2 |    CP_3 |    CP_4 |    CP_5 |    CP_6 |
|:-----------------------------|--------:|--------:|--------:|--------:|--------:|--------:|
| ABANDONO_EM_NORM             |  0.4747 |  0.0609 | -0.1975 |  0.7651 | -0.0955 | -0.3707 |
| REPROVACAO_EM_NORM           |  0.4734 |  0.1380 |  0.6750 | -0.3351 |  0.0403 | -0.4328 |
| DISTORCAO_EM_NORM            |  0.5771 | -0.1201 |  0.0446 |  0.0435 |  0.4465 |  0.6703 |
| MEDIA_INSE_NORM              | -0.3544 |  0.3932 |  0.6142 |  0.4961 | -0.0119 |  0.3104 |
| INFRA_MEDIA_NORM             | -0.0838 |  0.6799 | -0.2932 | -0.0959 |  0.6291 | -0.1994 |
| MEDIA_MATRICULAS_ESCOLA_NORM | -0.2914 | -0.5881 |  0.2005 |  0.2125 |  0.6277 | -0.2997 |

## Análise fatorial exploratória

- **KMO geral:** 0,605 (aceitável).
- **Teste de Bartlett:** p = 5.105e-78.
- **Número de fatores retidos:** 2.

### Variância dos fatores

| FATOR   |   SOMA_CARGAS_QUADRADAS |   VARIANCIA_EXPLICADA |   VARIANCIA_EXPLICADA_PERCENTUAL |   VARIANCIA_ACUMULADA_PERCENTUAL |   PESO_INDICE |   ORIENTACAO |
|:--------|------------------------:|----------------------:|---------------------------------:|---------------------------------:|--------------:|-------------:|
| FATOR_1 |                  1.4399 |                0.2400 |                          23.9984 |                          23.9984 |        0.6314 |            1 |
| FATOR_2 |                  0.8405 |                0.1401 |                          14.0085 |                          38.0069 |        0.3686 |            1 |

### Cargas fatoriais

| VARIAVEL                     |   FATOR_1 |   FATOR_2 |
|:-----------------------------|----------:|----------:|
| ABANDONO_EM_NORM             |    0.5133 |    0.0673 |
| REPROVACAO_EM_NORM           |    0.5172 |    0.1308 |
| DISTORCAO_EM_NORM            |    0.8104 |   -0.1264 |
| MEDIA_INSE_NORM              |   -0.3837 |    0.2552 |
| INFRA_MEDIA_NORM             |   -0.1003 |    0.5813 |
| MEDIA_MATRICULAS_ESCOLA_NORM |   -0.3080 |   -0.6324 |

### Comunalidades e KMO individual

| VARIAVEL                     |   COMUNALIDADE |   UNICIDADE |   KMO_INDIVIDUAL |
|:-----------------------------|---------------:|------------:|-----------------:|
| ABANDONO_EM_NORM             |         0.2680 |      0.7320 |           0.6745 |
| REPROVACAO_EM_NORM           |         0.2846 |      0.7154 |           0.6428 |
| DISTORCAO_EM_NORM            |         0.6728 |      0.3272 |           0.6156 |
| MEDIA_INSE_NORM              |         0.2124 |      0.7876 |           0.6327 |
| INFRA_MEDIA_NORM             |         0.3480 |      0.6520 |           0.5053 |
| MEDIA_MATRICULAS_ESCOLA_NORM |         0.4948 |      0.5052 |           0.5438 |

## Concordância entre os índices

- **IVE × IVE_PCA:** Pearson = 0,966 (muito forte); Spearman = 0,961.
- **IVE × IVE_FACTOR:** Pearson = 0,757 (forte); Spearman = 0,733.
- **IVE_PCA × IVE_FACTOR:** Pearson = 0,888 (forte); Spearman = 0,876.

| INDICE_1   | INDICE_2   |   CORRELACAO_PEARSON |   CORRELACAO_SPEARMAN |   P_VALOR_SPEARMAN |   NUM_OBSERVACOES |
|:-----------|:-----------|---------------------:|----------------------:|-------------------:|------------------:|
| IVE        | IVE_PCA    |               0.9658 |                0.9612 |             0.0000 |               497 |
| IVE        | IVE_FACTOR |               0.7566 |                0.7326 |             0.0000 |               497 |
| IVE_PCA    | IVE_FACTOR |               0.8882 |                0.8761 |             0.0000 |               497 |

## Estabilidade dos rankings

A estabilidade foi avaliada pela sobreposição dos municípios classificados entre os Top 10, Top 20, Top 50 e Top 100 de cada método. Também foram calculados o índice de Jaccard e a diferença média de posição entre os municípios em comum.

### IVE × IVE_PCA

- Top 10: 8 municípios em comum (80,0%); diferença média de ranking de 1,0 posições.
- Top 20: 16 municípios em comum (80,0%); diferença média de ranking de 2,4 posições.
- Top 50: 41 municípios em comum (82,0%); diferença média de ranking de 6,7 posições.
- Top 100: 85 municípios em comum (85,0%); diferença média de ranking de 13,4 posições.

### IVE × IVE_FACTOR

- Top 10: 4 municípios em comum (40,0%); diferença média de ranking de 1,5 posições.
- Top 20: 8 municípios em comum (40,0%); diferença média de ranking de 5,0 posições.
- Top 50: 25 municípios em comum (50,0%); diferença média de ranking de 12,0 posições.
- Top 100: 67 municípios em comum (67,0%); diferença média de ranking de 26,3 posições.

### IVE_PCA × IVE_FACTOR

- Top 10: 6 municípios em comum (60,0%); diferença média de ranking de 1,3 posições.
- Top 20: 10 municípios em comum (50,0%); diferença média de ranking de 2,8 posições.
- Top 50: 34 municípios em comum (68,0%); diferença média de ranking de 11,9 posições.
- Top 100: 80 municípios em comum (80,0%); diferença média de ranking de 20,4 posições.

| INDICE_1   | INDICE_2   |   TOP |   MUNICIPIOS_EM_COMUM |   PERCENTUAL_CONCORDANCIA |   INDICE_JACCARD |   DIFERENCA_MEDIA_RANK |   DIFERENCA_MEDIANA_RANK |
|:-----------|:-----------|------:|----------------------:|--------------------------:|-----------------:|-----------------------:|-------------------------:|
| IVE        | IVE_PCA    |    10 |                     8 |                     80.00 |            66.67 |                   1.00 |                     1.00 |
| IVE        | IVE_PCA    |    20 |                    16 |                     80.00 |            66.67 |                   2.44 |                     2.00 |
| IVE        | IVE_PCA    |    50 |                    41 |                     82.00 |            69.49 |                   6.66 |                     5.00 |
| IVE        | IVE_PCA    |   100 |                    85 |                     85.00 |            73.91 |                  13.39 |                     9.00 |
| IVE        | IVE_FACTOR |    10 |                     4 |                     40.00 |            25.00 |                   1.50 |                     1.00 |
| IVE        | IVE_FACTOR |    20 |                     8 |                     40.00 |            25.00 |                   5.00 |                     4.00 |
| IVE        | IVE_FACTOR |    50 |                    25 |                     50.00 |            33.33 |                  12.04 |                    11.00 |
| IVE        | IVE_FACTOR |   100 |                    67 |                     67.00 |            50.38 |                  26.33 |                    26.00 |
| IVE_PCA    | IVE_FACTOR |    10 |                     6 |                     60.00 |            42.86 |                   1.33 |                     1.50 |
| IVE_PCA    | IVE_FACTOR |    20 |                    10 |                     50.00 |            33.33 |                   2.80 |                     2.00 |
| IVE_PCA    | IVE_FACTOR |    50 |                    34 |                     68.00 |            51.52 |                  11.85 |                    12.00 |
| IVE_PCA    | IVE_FACTOR |   100 |                    80 |                     80.00 |            66.67 |                  20.43 |                    17.00 |

## Municípios prioritários por consenso

O ranking de consenso utiliza a posição média dos municípios no IVE manual, no índice PCA e no índice fatorial. Menores valores indicam maior prioridade.

|   POSICAO_CONSENSO |   CO_MUNICIPIO | NO_MUNICIPIO            | SG_UF   |    IVE |   IVE_PCA |   IVE_FACTOR |   RANK_IVE |   RANK_IVE_PCA |   RANK_IVE_FACTOR |   DIF_RANK_IVE_PCA |   DIF_RANK_IVE_FACTOR |   DIF_RANK_PCA_FACTOR |   RANK_MEDIO_CONSENSO |   DESVIO_RANK_CONSENSO | PRESENTE_TOP_10_TRES_INDICES   | PRESENTE_TOP_20_TRES_INDICES   | PRESENTE_TOP_50_TRES_INDICES   |
|-------------------:|---------------:|:------------------------|:--------|-------:|----------:|-------------:|-----------:|---------------:|------------------:|-------------------:|----------------------:|----------------------:|----------------------:|-----------------------:|:-------------------------------|:-------------------------------|:-------------------------------|
|                  1 |        4319737 | São Valério do Sul      | RS      | 0.6481 |    1.0000 |       1.0000 |          1 |              1 |                 1 |                  0 |                     0 |                     0 |                1.0000 |                 0.0000 | True                           | True                           | True                           |
|                  2 |        4306429 | Dois Irmãos das Missões | RS      | 0.5923 |    0.8724 |       0.8193 |          3 |              2 |                 4 |                  1 |                     1 |                     2 |                3.0000 |                 1.0000 | True                           | True                           | True                           |
|                  3 |        4318507 | São José do Norte       | RS      | 0.5843 |    0.8067 |       0.8218 |          4 |              3 |                 3 |                  1 |                     1 |                     0 |                3.3333 |                 0.5774 | True                           | True                           | True                           |
|                  4 |        4315404 | Redentora               | RS      | 0.6192 |    0.7963 |       0.7132 |          2 |              4 |                 6 |                  2 |                     4 |                     2 |                4.0000 |                 2.0000 | True                           | True                           | True                           |
|                  5 |        4300604 | Alvorada                | RS      | 0.4613 |    0.6669 |       0.9507 |         12 |              5 |                 2 |                  7 |                    10 |                     3 |                6.3333 |                 5.1316 | False                          | True                           | True                           |
|                  6 |        4321105 | Tapes                   | RS      | 0.4900 |    0.6478 |       0.6545 |          7 |              8 |                11 |                  1 |                     4 |                     3 |                8.6667 |                 2.0817 | False                          | True                           | True                           |
|                  7 |        4306379 | Dilermando de Aguiar    | RS      | 0.5203 |    0.6531 |       0.5973 |          5 |              7 |                20 |                  2 |                    15 |                    13 |               10.6667 |                 8.1445 | False                          | True                           | True                           |
|                  8 |        4304663 | Capão do Leão           | RS      | 0.4493 |    0.6110 |       0.6869 |         14 |             10 |                 9 |                  4 |                     5 |                     1 |               11.0000 |                 2.6458 | False                          | True                           | True                           |
|                  9 |        4310876 | Jacuizinho              | RS      | 0.4932 |    0.6536 |       0.5935 |          6 |              6 |                21 |                  0 |                    15 |                    15 |               11.0000 |                 8.6603 | False                          | False                          | True                           |
|                 10 |        4317301 | Santa Vitória do Palmar | RS      | 0.4839 |    0.6183 |       0.5673 |          8 |              9 |                26 |                  1 |                    18 |                    17 |               14.3333 |                10.1160 | False                          | False                          | True                           |
|                 11 |        4306767 | Eldorado do Sul         | RS      | 0.4319 |    0.5885 |       0.6269 |         24 |             12 |                14 |                 12 |                    10 |                     2 |               16.6667 |                 6.4291 | False                          | False                          | True                           |
|                 12 |        4311759 | Manoel Viana            | RS      | 0.4459 |    0.5763 |       0.5617 |         16 |             14 |                28 |                  2 |                    12 |                    14 |               19.3333 |                 7.5719 | False                          | False                          | True                           |
|                 13 |        4307104 | Herval                  | RS      | 0.4642 |    0.5785 |       0.5443 |         10 |             13 |                36 |                  3 |                    26 |                    23 |               19.6667 |                14.2244 | False                          | False                          | True                           |
|                 14 |        4323002 | Viamão                  | RS      | 0.4293 |    0.5531 |       0.6188 |         27 |             18 |                16 |                  9 |                    11 |                     2 |               20.3333 |                 5.8595 | False                          | False                          | True                           |
|                 15 |        4314472 | Pinhal Grande           | RS      | 0.4592 |    0.6089 |       0.5220 |         13 |             11 |                45 |                  2 |                    32 |                    34 |               23.0000 |                19.0788 | False                          | False                          | True                           |
|                 16 |        4301636 | Balneário Pinhal        | RS      | 0.4154 |    0.5443 |       0.5883 |         34 |             20 |                22 |                 14 |                    12 |                     2 |               25.3333 |                 7.5719 | False                          | False                          | True                           |
|                 17 |        4321436 | Terra de Areia          | RS      | 0.4174 |    0.5417 |       0.5504 |         31 |             21 |                32 |                 10 |                     1 |                    11 |               28.0000 |                 6.0828 | False                          | False                          | True                           |
|                 18 |        4304606 | Canoas                  | RS      | 0.3847 |    0.5349 |       0.6896 |         52 |             24 |                 8 |                 28 |                    44 |                    16 |               28.0000 |                22.2711 | False                          | False                          | False                          |
|                 19 |        4322202 | Tupanciretã             | RS      | 0.4639 |    0.5692 |       0.4998 |         11 |             15 |                60 |                  4 |                    49 |                    45 |               28.6667 |                27.2091 | False                          | False                          | False                          |
|                 20 |        4314407 | Pelotas                 | RS      | 0.3888 |    0.5266 |       0.6440 |         47 |             30 |                12 |                 17 |                    35 |                    18 |               29.6667 |                17.5024 | False                          | False                          | True                           |
|                 21 |        4318705 | São Leopoldo            | RS      | 0.3708 |    0.5362 |       0.7411 |         67 |             23 |                 5 |                 44 |                    62 |                    18 |               31.6667 |                31.8957 | False                          | False                          | False                          |
|                 22 |        4306056 | Cristal                 | RS      | 0.4111 |    0.5268 |       0.5537 |         38 |             29 |                30 |                  9 |                     8 |                     1 |               32.3333 |                 4.9329 | False                          | False                          | True                           |
|                 23 |        4318309 | São Gabriel             | RS      | 0.4203 |    0.5307 |       0.5328 |         30 |             26 |                41 |                  4 |                    11 |                    15 |               32.3333 |                 7.7675 | False                          | False                          | True                           |
|                 24 |        4304689 | Capela de Santana       | RS      | 0.4478 |    0.5546 |       0.4830 |         15 |             17 |                67 |                  2 |                    52 |                    50 |               33.0000 |                29.4618 | False                          | False                          | False                          |
|                 25 |        4312708 | Nonoai                  | RS      | 0.4311 |    0.5444 |       0.5000 |         25 |             19 |                59 |                  6 |                    34 |                    40 |               34.3333 |                21.5716 | False                          | False                          | False                          |
|                 26 |        4318408 | São Jerônimo            | RS      | 0.4749 |    0.5564 |       0.4644 |          9 |             16 |                78 |                  7 |                    69 |                    62 |               34.3333 |                37.9781 | False                          | False                          | False                          |
|                 27 |        4306502 | Dom Feliciano           | RS      | 0.4338 |    0.5251 |       0.5066 |         21 |             31 |                55 |                 10 |                    34 |                    24 |               35.6667 |                17.4738 | False                          | False                          | False                          |
|                 28 |        4301875 | Barra do Quaraí         | RS      | 0.4171 |    0.5098 |       0.5387 |         32 |             37 |                39 |                  5 |                     7 |                     2 |               36.0000 |                 3.6056 | False                          | False                          | True                           |
|                 29 |        4310330 | Imbé                    | RS      | 0.3860 |    0.5146 |       0.5628 |         50 |             33 |                27 |                 17 |                    23 |                     6 |               36.6667 |                11.9304 | False                          | False                          | True                           |
|                 30 |        4315602 | Rio Grande              | RS      | 0.3885 |    0.5071 |       0.5818 |         49 |             39 |                23 |                 10 |                    26 |                    16 |               37.0000 |                13.1149 | False                          | False                          | True                           |
|                 31 |        4314902 | Porto Alegre            | RS      | 0.3757 |    0.5058 |       0.6697 |         61 |             41 |                10 |                 20 |                    51 |                    31 |               37.3333 |                25.6970 | False                          | False                          | False                          |
|                 32 |        4302808 | Caçapava do Sul         | RS      | 0.4164 |    0.5287 |       0.5080 |         33 |             27 |                54 |                  6 |                    21 |                    27 |               38.0000 |                14.1774 | False                          | False                          | False                          |
|                 33 |        4321600 | Tramandaí               | RS      | 0.3824 |    0.5000 |       0.6066 |         54 |             46 |                17 |                  8 |                    37 |                    29 |               39.0000 |                19.4679 | False                          | False                          | False                          |
|                 34 |        4320008 | Sapucaia do Sul         | RS      | 0.3650 |    0.5077 |       0.7108 |         74 |             38 |                 7 |                 36 |                    67 |                    31 |               39.6667 |                33.5311 | False                          | False                          | False                          |
|                 35 |        4307401 | Esmeralda               | RS      | 0.4112 |    0.5317 |       0.4953 |         37 |             25 |                61 |                 12 |                    24 |                    36 |               41.0000 |                18.3303 | False                          | False                          | False                          |
|                 36 |        4319406 | São Pedro do Sul        | RS      | 0.4305 |    0.5285 |       0.4778 |         26 |             28 |                69 |                  2 |                    43 |                    41 |               41.0000 |                24.2693 | False                          | False                          | False                          |
|                 37 |        4307831 | Eugênio de Castro       | RS      | 0.4356 |    0.5416 |       0.4458 |         18 |             22 |                87 |                  4 |                    69 |                    65 |               42.3333 |                38.7341 | False                          | False                          | False                          |
|                 38 |        4313375 | Nova Santa Rita         | RS      | 0.3885 |    0.5008 |       0.5449 |         48 |             45 |                35 |                  3 |                    13 |                    10 |               42.6667 |                 6.8069 | False                          | False                          | True                           |
|                 39 |        4315909 | Rodeio Bonito           | RS      | 0.3797 |    0.5239 |       0.5209 |         55 |             32 |                47 |                 23 |                     8 |                    15 |               44.6667 |                11.6762 | False                          | False                          | False                          |
|                 40 |        4305454 | Cidreira                | RS      | 0.3761 |    0.4852 |       0.5691 |         59 |             50 |                25 |                  9 |                    34 |                    25 |               44.6667 |                17.6163 | False                          | False                          | False                          |
|                 41 |        4316972 | Santa Margarida do Sul  | RS      | 0.3938 |    0.4870 |       0.5211 |         45 |             48 |                46 |                  3 |                     1 |                     2 |               46.3333 |                 1.5275 | False                          | False                          | True                           |
|                 42 |        4300406 | Alegrete                | RS      | 0.3759 |    0.4839 |       0.5458 |         60 |             51 |                34 |                  9 |                    26 |                    17 |               48.3333 |                13.2035 | False                          | False                          | False                          |
|                 43 |        4301305 | Arroio Grande           | RS      | 0.4204 |    0.5036 |       0.4671 |         29 |             44 |                72 |                 15 |                    43 |                    28 |               48.3333 |                21.8251 | False                          | False                          | False                          |
|                 44 |        4309654 | Hulha Negra             | RS      | 0.4071 |    0.5102 |       0.4720 |         42 |             36 |                70 |                  6 |                    28 |                    34 |               49.3333 |                18.1475 | False                          | False                          | False                          |
|                 45 |        4301107 | Arroio dos Ratos        | RS      | 0.3852 |    0.4785 |       0.5291 |         51 |             56 |                42 |                  5 |                     9 |                    14 |               49.6667 |                 7.0946 | False                          | False                          | False                          |
|                 46 |        4323804 | Xangri-lá               | RS      | 0.3629 |    0.4986 |       0.5805 |         80 |             47 |                24 |                 33 |                    56 |                    23 |               50.3333 |                28.1484 | False                          | False                          | False                          |
|                 47 |        4320206 | Seberi                  | RS      | 0.4115 |    0.5052 |       0.4655 |         36 |             42 |                76 |                  6 |                    40 |                    34 |               51.3333 |                21.5716 | False                          | False                          | False                          |
|                 48 |        4316402 | Rosário do Sul          | RS      | 0.3769 |    0.4854 |       0.5181 |         58 |             49 |                48 |                  9 |                    10 |                     1 |               51.6667 |                 5.5076 | False                          | False                          | False                          |
|                 49 |        4322400 | Uruguaiana              | RS      | 0.3734 |    0.4717 |       0.5518 |         66 |             61 |                31 |                  5 |                    35 |                    30 |               52.6667 |                18.9297 | False                          | False                          | False                          |
|                 50 |        4300851 | Arambaré                | RS      | 0.3945 |    0.5049 |       0.4664 |         44 |             43 |                74 |                  1 |                    30 |                    31 |               53.6667 |                17.6163 | False                          | False                          | False                          |

## Conclusão metodológica

A primeira componente principal explicou 33,23% da variância total. A análise fatorial apresentou KMO geral de 0,605, classificado como aceitável, e o teste de Bartlett foi estatisticamente significativo (p = 5.105e-78).

Foram retidos 2 fatores, responsáveis por 38,01% da variância comum estimada pelo modelo fatorial.

O IVE manual apresentou correlação de Pearson de 0,966 com o índice obtido pela PCA e de 0,757 com o índice fatorial. Esses resultados indicam elevada concordância entre a construção teórica do índice e a estrutura empírica dos indicadores.

No recorte dos 50 municípios mais vulneráveis, o IVE manual e a PCA apresentaram 82,0% de concordância. A combinação entre correlações elevadas, preservação dos municípios prioritários e coerência das dimensões latentes sustenta a manutenção do IVE manual como índice principal do projeto, utilizando PCA e análise fatorial como métodos de validação e análise de sensibilidade.

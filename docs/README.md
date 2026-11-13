# Como os gráficos do painel UFCA são calculados

Este guia usa os títulos e identificadores do [catálogo de gráficos](../data/graficos.json). Um identificador com `{prefixo}` representa a mesma fórmula nas páginas em que ela se repete. Os prefixos são `ufca`, `matcomp`, `computacao`, `civil`, `materiais` e `software`, conforme a família. O painel web também acrescenta `group-{grupo}-` aos IDs dos gráficos gerais de grupo e o código da disciplina aos IDs da análise individual.

- [Base e medidas](#base-e-medidas)
- [Evolução, horários e comparações entre cursos](#evolução-horários-e-comparações-entre-cursos)
- [Distribuição e composição](#distribuição-e-composição)
- [Análises específicas dos cursos](#análises-específicas-dos-cursos)
- [Análise individual](#análise-individual)
- [Gráficos estatísticos](#gráficos-estatísticos)
- [Gráficos adicionais do catálogo](#gráficos-adicionais-do-catálogo)
- [Comparações entre semestres](#comparações-entre-semestres)

## Base e medidas

Cada observação representa um registro de oferta de turma no SIGAA. A preparação normaliza os campos, descarta registros inválidos e remove duplicatas com a mesma identidade e conteúdo. Os indicadores usam turmas presenciais, com capacidade positiva e situação consolidada ou aberta, após a exclusão dos [registros sinalizados](consistencia-turmas.md). A contagem de matrículas soma registros nas turmas. Um estudante matriculado em duas turmas contribui duas vezes.

**Todos os dados** usa todos os semestres elegíveis. **Mais recente × anterior** usa os dois últimos semestres com oferta elegível para o grupo, e **Escolher semestres** usa o par indicado. Os gráficos principais do comparativo recebem as turmas dos dois semestres, e os valores de referência e do semestre comparado são recalculados separadamente. Quando exibido, o asterisco indica a presença de oferta aberta na série ou turma marcada.

As páginas dos cursos selecionam códigos das matrizes cadastradas, incluindo componentes históricos reconhecidos. A natureza da matriz atual tem precedência na classificação geral. Um código compartilhado pode contribuir para vários cursos. O CCT é calculado diretamente sobre a base filtrada, contando cada registro uma vez. [Seleção de turmas](../backend/services/data/selection.py) · [Preparação da base](../backend/services/data/preprocessing.py) · [Matrizes e cursos](../backend/services/domain/courses.py)

Para uma amostra de turmas, use as seguintes medidas.

| Medida | Cálculo |
| --- | --- |
| Turmas `N` | Quantidade de registros elegíveis no recorte. |
| Vagas `C` e matrículas `M` | `C = Σ cᵢ` e `M = Σ mᵢ`, em que `cᵢ` e `mᵢ` são a capacidade e as matrículas da turma `i`. |
| Ocupação da turma `rᵢ` | `mᵢ / cᵢ`. Pode ultrapassar 100%. |
| Ocupação geral | `M / C`, equivalente à média das ocupações ponderada pela capacidade. Sem capacidade no agrupamento, a ocupação fica indefinida. |
| Média e mediana da ocupação | A média é `Σ rᵢ / N`. A mediana é o valor central das ocupações ordenadas, com média dos dois valores centrais quando `N` é par. Cada turma tem o mesmo peso. |
| Vagas não preenchidas | `Σ max(cᵢ − mᵢ, 0)`. |
| Matrículas excedentes | `Σ max(mᵢ − cᵢ, 0)`. Sobras e excedentes são calculados por turma antes da soma. |
| Baixa ocupação, lotação e excesso | Contagens de turmas com `rᵢ < 25%`, `rᵢ ≥ 100%` e `rᵢ > 100%`, respectivamente. Turmas sem matrículas têm `mᵢ = 0`. |
| Faixas de ocupação | `[0%, 25%)`, `[25%, 50%)`, `[50%, 100%)` e `[100%, ∞)`. Cada turma entra em uma faixa. |
| Resumo anual | Agrupa pelo ano do período acadêmico e soma turmas, vagas e matrículas dos semestres do recorte. A ocupação anual usa `M / C` do ano. |

Uma turma com 20 de 20 vagas preenchidas e outra com 10 de 40 dão ocupação geral de `30 / 60 = 50%`. A média e a mediana das duas ocupações são `(100% + 25%) / 2 = 62,5%`. Uma lacuna indica ausência de oferta ou medida indefinida, enquanto um zero exibido é um valor calculado. [Métricas](../backend/services/analytics/metrics.py) · [Resumo por período](../backend/services/dashboard/periods.py)

## Evolução, horários e comparações entre cursos

| Gráfico e ID | Cálculo |
| --- | --- |
| Vagas e matrículas por semestre · `ufca-capacidade-matriculas`, `{prefixo}-vagas` | Uma barra para `C` e outra para `M` em cada semestre com oferta. |
| Distribuição das turmas por faixa · `ufca-faixas`, `{prefixo}-faixas` | Em cada semestre, empilha as contagens das quatro faixas. A altura total é `N`. |
| Turmas e disciplinas ofertadas · `{prefixo}-indicador-turmas` | Barras com `N` e linha com a quantidade de códigos distintos em cada semestre. |
| Vagas não preenchidas e matrículas acima da capacidade · `{prefixo}-indicador-saldo` | Soma os dois saldos por turma e mostra um total de cada tipo por semestre. |
| Ocupação geral por semestre · `ufca-indicador-ocupacao` | `M / C` das turmas de cada semestre. |
| Percentual de turmas com baixa ocupação ou lotadas · `{prefixo}-indicador-extremos` | Divide por `N` a contagem abaixo de 25% e, separadamente, a contagem a partir de 100% em cada semestre. |
| Concentração da oferta ao longo da semana · `ufca-grade-horaria` | Conta as turmas com aula sobreposta a cada combinação de dia e hora, das 07h às 21h. O detalhe da célula mostra a contagem por semestre. |
| Ocupação por turno · `ufca-turnos` | `M / C` das turmas de cada turno. O rótulo mostra quantas turmas compõem a barra. |
| Ocupação segundo o tamanho da turma · `ufca-tamanho` | Escolhe até cinco capacidades exatas pelo número de turmas. Mostra `M / C` e `N` para cada capacidade escolhida. |
| Ocupação geral por curso · `entre-cursos-ocupacao` | `M / C` dos códigos de cada curso no mesmo recorte. |
| Vagas e matrículas por curso · `entre-cursos-volume` | `C` e `M` dos códigos de cada curso no mesmo recorte. |
| Turmas ofertadas por curso · `entre-cursos-turmas` | `N` dos códigos de cada curso no mesmo recorte. |

No mapa semanal, uma aula das 8h às 10h entra nas células de 08h e 09h. Se a turma tem esse horário em três dias, contribui para seis células. Cada turma conta uma vez por célula, mesmo quando o horário aparece repetido no registro. As células contam ofertas de turma no recorte, sem multiplicar pelo número de semanas de aula.

Os turnos são manhã antes das 12h, tarde das 12h às 18h e noite a partir das 18h. Qualquer sobreposição com uma faixa conta para a classificação. Uma turma com aulas em mais de um turno entra em **Misto**. Uma turma sem horário reconhecido entra em **Sem horário**. [Cálculos dos gráficos](../backend/services/analytics/metrics.py) · [Comparação entre cursos](../backend/services/dashboard/groups.py)

## Distribuição e composição

| Gráfico e sufixo de `{prefixo}-` | Cálculo |
| --- | --- |
| Ocupação mediana e ocupação geral · `linha-ocupacao` | Para cada semestre, compara a mediana de `rᵢ` com `M / C`. |
| Vagas e matrículas médias por turma · `linha-tamanho` | Para cada semestre, mostra `C / N` e `M / N`. |
| Roscas de faixas · `rosca-historico`, `rosca-abertas` | Conta as turmas de cada faixa na amostra da rosca. Cada fatia ocupa a proporção da contagem sobre `N`. O painel por recorte usa a rosca principal. A variante de abertas pertence ao cálculo original com amostras separadas. |
| Distribuição das turmas por turno · `rosca-turnos` | Conta as turmas por turno. A fração de cada fatia é a contagem do turno dividida por `N`. |
| Vagas e matrículas por turma · `dispersao` | Agrupa as turmas com a mesma combinação `(cᵢ, mᵢ)`. Os eixos mostram essa combinação, o tamanho do ponto cresce com a frequência e a diagonal `m = c` indica 100%. |
| Composição da oferta por capacidade · `pizza-capacidades` | Conta turmas por capacidade exata. Exibe as cinco capacidades mais frequentes e agrega o restante em **Outras capacidades**. |
| Perfil de ocupação por faixa · `radar-faixas` | Cada eixo mostra a contagem da faixa dividida pelo total de turmas da série correspondente. |
| Composição da ocupação ao longo dos semestres · `faixas-percentual` | Divide cada contagem de faixa por `N` do semestre. Cada coluna com oferta soma 100%. |
| Dimensão da oferta por disciplina · `bolhas-disciplinas` | Cada código vira uma bolha em `(C, M)`. A área é proporcional à quantidade de turmas do código. |
| Matrículas por natureza curricular · `area-natureza` | Soma `mᵢ` por semestre nas categorias obrigatórias, optativas e compartilhadas ou sem classificação. No panorama web do CCT, códigos com naturezas conflitantes entre cursos ou mudança conhecida ficam na terceira categoria. |

[Cálculos de distribuição](../backend/services/analytics/metrics.py) · [Classificação no panorama web](../backend/services/dashboard/groups.py)

## Análises específicas dos cursos

| Gráfico e sufixo de `{prefixo}-` | Cálculo |
| --- | --- |
| Ocupação do curso e do CCT · `comparacao` | Para cada semestre com oferta do curso, mostra `M / C` do curso e `M / C` de todo o CCT no mesmo semestre e recorte. |
| Ocupação de obrigatórias e optativas · `natureza` | Calcula `M / C` para cada natureza, por semestre, segundo a classificação de referência do curso. |
| Ocupação das obrigatórias por disciplina · `historico-obrigatorias` | Cada célula calcula `M / C` para um código e semestre acadêmico. A matriz selecionada determina os códigos, a ordem das linhas e os agrupamentos por semestre curricular. Códigos sem oferta ficam com células vazias. |
| Ocupação das optativas por disciplina · `historico-optativas` | Calcula `M / C` por código e semestre. Lista as optativas com oferta no recorte e deixa vazias as células dos semestres sem turma daquele código. |
| Disciplinas com mais matrículas · `matriculas-historico` | Ordena por `M` acumulado por código. |
| Mais semestres abaixo de 25% · `baixa-recorrente` | Calcula `M / C` por código e semestre. Ordena pela quantidade de semestres com oferta e ocupação inferior a 25%. |
| Maior e menor ocupação acumulada · `maior-ocupacao`, `menor-ocupacao` | Calcula `M / C` no recorte para cada código e ordena do maior para o menor ou do menor para o maior. |
| Disciplinas com mais vagas · `mais-vagas` | Ordena por `C` acumulado por código. |
| Disciplinas com mais turmas · `mais-turmas` | Ordena por `N` acumulado por código. |
| Disciplinas ofertadas em mais semestres · `mais-semestres` | Ordena pelo número de semestres distintos com oferta de cada código. |
| Disciplinas com mais vagas não preenchidas · `sobras` | Ordena pelo total positivo de vagas não preenchidas por código. |
| Disciplinas com mais turmas lotadas · `lotadas` | Ordena pela contagem positiva de turmas com `rᵢ ≥ 100%` por código. |
| Disciplinas com mais matrículas acima da capacidade · `acima-capacidade` | Ordena pela soma positiva de matrículas excedentes por código. |
| Obrigatórias e optativas com mais matrículas · `obrigatorias-matriculas`, `optativas-matriculas` | Restringe à natureza indicada e ordena por `M` acumulado por código. |

Os rankings específicos mostram até dez códigos. O rótulo resolve empates na ordenação e códigos com o mesmo valor recebem a mesma posição numérica. Os quatro rankings gerais seguem a mesma lógica de agregação por código e mostram até dez resultados, ordenados em ordem decrescente.

| Ranking geral | Medida |
| --- | --- |
| `geral-ranking-matriculas` | `M` por código. |
| `geral-ranking-vagas` | `C` por código. |
| `geral-ranking-ocupacao` | `M / C` por código. |
| `geral-ranking-disponiveis` | Soma das vagas não preenchidas por código. |

[Cálculos por curso](../backend/services/analytics/metrics.py) · [Ordem das matrizes](../backend/services/domain/ppcs.py) · [Rankings gerais](../backend/services/dashboard/groups.py)

## Análise individual

Todos os gráficos desta seção filtram pelo código da cadeira escolhida.

| Gráfico e ID no catálogo | Cálculo |
| --- | --- |
| Vagas e matrículas por semestre · `cadeira-oferta` | `C` e `M` por semestre. |
| Ocupação geral e mediana · `cadeira-ocupacao` | `M / C` e mediana de `rᵢ` por semestre. |
| Vagas não preenchidas e matrículas excedentes · `cadeira-saldo` | Soma os dois saldos por turma, separadamente, em cada semestre. |
| Quantidade de turmas por semestre · `cadeira-turmas` | `N` da disciplina por semestre. Nas quatro séries temporais, semestre do recorte sem oferta da cadeira aparece como lacuna. |
| Ocupação de cada turma · `cadeira-por-turma` | Uma barra de `rᵢ` por turma, identificada pelo semestre e pela turma. |
| Faixas de ocupação · `cadeira-faixas`, `cadeira-faixas-abertas` | Conta as turmas por faixa na amostra da rosca. A versão de abertas é calculada quando a função recebe a oferta aberta como segunda amostra. O painel web exibe a rosca do recorte selecionado. |
| Ocupação por turno · `cadeira-turnos` | `M / C` das turmas da disciplina em cada turno. |
| Oferta por dia e horário · `cadeira-horarios` | Usa a mesma contagem por célula do mapa semanal. O detalhe lista os semestres e as turmas que compõem o valor. |

[Cálculos da análise individual](../backend/services/analytics/disciplines.py)

## Gráficos estatísticos

Nas estatísticas de ocupação, cada turma fornece um valor `rᵢ`. Seja `μ` a média aritmética e `σ = √(Σ(rᵢ − μ)² / N)` o desvio-padrão populacional. Os quantis usam interpolação linear na posição `(N − 1)p` da série ordenada com índice começando em zero. Assim, `Q1`, mediana e `Q3` usam `p = 0,25`, `0,50` e `0,75`. O intervalo interquartil é `IQR = Q3 − Q1`. O desvio absoluto mediano é `MAD = mediana(|rᵢ − mediana(r)|)`.

Nas estatísticas de concentração, `D` é a quantidade de códigos com oferta. Some as matrículas de cada código para obter `mⱼ` e divida pelo total `M` para obter sua participação `sⱼ`. Os códigos com zero matrículas entram na contagem de códigos. Quando `M = 0`, as medidas dependentes das participações ficam indefinidas.

| Gráfico e sufixo de `{prefixo}-estat-` | Cálculo |
| --- | --- |
| Distribuição detalhada da ocupação · `histograma` | Divide por `N` a quantidade de turmas em cada intervalo delimitado por 0%, 25%, 50%, 75%, 100% e 125%. Cada intervalo inclui seu limite inferior. O último é aberto para cima. |
| Faixa central de ocupação por semestre · `quartis` | Mostra a faixa de `Q1` a `Q3` e a linha da mediana para cada semestre. |
| Dispersão relativa da ocupação · `dispersao` | Mostra `σ / μ` e `MAD / mediana(r)` por semestre. Cada medida fica indefinida quando seu denominador é zero. |
| Assimetria e caudas da ocupação · `momentos` | Por semestre, calcula a média de `((rᵢ − μ) / σ)³` para a assimetria e a média de `((rᵢ − μ) / σ)⁴` menos 3 para o excesso de curtose. Ambas ficam indefinidas se `σ = 0`. |
| Turmas sinalizadas pela regra de Tukey · `tukey` | Por semestre, conta os valores estritamente abaixo de `Q1 − 1,5 × IQR` e estritamente acima de `Q3 + 1,5 × IQR`. Essas turmas seguem nos indicadores. |
| Distribuição acumulada da ocupação · `acumulada` | Em cada limiar `t`, mostra `contagem(rᵢ ≤ t) / N`. A curva em degraus usa zero e os valores distintos de ocupação observados. |
| Concentração das matrículas entre disciplinas · `lorenz` | Ordena os códigos por `mⱼ` crescente. No ponto `k`, mostra `k / D` no eixo horizontal e `Σ dos k menores mⱼ / M` no vertical. A referência de igualdade é a diagonal. |
| Índices de concentração por semestre · `concentracao` | O Gini usa `Σ[(2j − D − 1) × mⱼ] / (D × M)`, com `j` iniciando em 1 e `mⱼ` em ordem crescente. O HHI é `Σ sⱼ²`. |
| Disciplinas ofertadas e diversidade efetiva · `diversidade` | Mostra `D` e `1 / HHI` por semestre. |
| Participação das dez maiores disciplinas · `participacao` | Ordena os códigos por `mⱼ` decrescente e exibe `sⱼ` dos dez primeiros, usando `M` de todos os códigos do recorte. |
| Relação entre capacidade e ocupação por semestre · `correlacoes` | Pearson é `Σ[(xᵢ − x̄)(yᵢ − ȳ)] / √[Σ(xᵢ − x̄)² × Σ(yᵢ − ȳ)²]`, com `xᵢ = cᵢ` e `yᵢ = rᵢ`. Spearman aplica Pearson aos postos, atribuindo o posto médio nos empates. Correlações ficam indefinidas com menos de duas turmas ou série constante. |
| Capacidade e ocupação com ajuste descritivo · `regressao` | Plota `(cᵢ, rᵢ)` e agrupa pares iguais para o desenho. A reta de mínimos quadrados usa todas as turmas, com inclinação `b = Σ[(xᵢ − x̄)(yᵢ − ȳ)] / Σ(xᵢ − x̄)²` e intercepto `ȳ − b × x̄`. A reta requer variação de capacidade. Quando definido, `R² = Pearson²`. |
| Ocupação acima de um limiar e limite de Markov · `markov` | Para `t` de 25%, 50%, 75%, 100%, 125%, 150% e 200%, compara `contagem(rᵢ ≥ t) / N` com o limite superior `min(1, μ / t)`. |
| Concentração em torno da média e limite de Chebyshev · `chebyshev` | Para `k` de 1,5, 2, 2,5, 3 e 4, compara a fração de turmas cujo desvio absoluto em relação a `μ` é menor que `kσ` com o limite inferior `1 − 1/k²`. Se `σ = 0`, o gráfico exibe 100% na série observada, pois todas as turmas têm a ocupação média. |

O resumo estatístico também mostra a entropia normalizada `−Σ(sⱼ × ln(sⱼ)) / ln(D)`, com contribuição zero para `sⱼ = 0` e resultado zero para um único código com matrículas. A participação das 20% maiores disciplinas soma as participações dos `⌈0,2 × D⌉` primeiros códigos. [Implementação das estatísticas](../backend/services/analytics/statistics.py)

## Gráficos adicionais do catálogo

O cálculo em lote inclui famílias além das seções carregadas sob demanda no painel web. A exportação HTML usa os gráficos gerais dos grupos, a comparação entre cursos e os painéis de curso do acumulado. Os gráficos do cálculo em lote seguem a amostra selecionada quando processados por recorte. As séries independentes de abertas aparecem nas funções que recebem uma segunda amostra.

| Gráfico e ID | Cálculo |
| --- | --- |
| Ocupação por prefixo de código · `ufca-prefixos` | `M / C` por semestre e prefixo de letras, nas linhas CAR, CC, ECI, EM, ES e MC. |
| Ocupação de oito disciplinas selecionadas · `ufca-codigos` | `M / C` por semestre para CC0015, ECI0079, CAR0011, ECI0002, EM0105, EM0030, EM0043 e EM0114. |
| Ocupação das disciplinas listadas como optativas · `ufca-opt-curso` | `M / C` dos códigos optativos de cada matriz atual de referência, calculado separadamente para cada série recebida. |
| Ocupação por semestre e natureza curricular · `ufca-opt-periodo` | `M / C` por semestre para optativas e obrigatórias das listas exclusivas de referência. Exclui códigos presentes nas duas naturezas e mudanças conhecidas entre CC001 e CC002. |
| Ocupação das disciplinas abertas · `{prefixo}-abertas-ocupacao` | `M / C` por código na amostra de abertas, em ordem decrescente. |
| Vagas ainda não preenchidas · `{prefixo}-abertas-vagas` | Soma as vagas não preenchidas por código na amostra de abertas, em ordem decrescente. |
| Mais matrículas nas turmas abertas · `{prefixo}-abertas-matriculas` | Até dez códigos com maior `M` na amostra de abertas. |
| Menor ocupação nas turmas abertas · `{prefixo}-abertas-menor-ocupacao` | Até dez códigos com menor `M / C` na amostra de abertas. |

Os IDs `ufca-ranking-{coorte}-{seção}-{posição}` repetem as medidas da tabela abaixo para as coortes `obrigatorias`, `optativas` e `geral`. A primeira usa os códigos exclusivamente obrigatórios nas listas de referência. A segunda usa os exclusivamente optativos e EM0057. A terceira reúne as duas. Os códigos com mudança conhecida entre CC001 e CC002 ficam fora das listas exclusivas. No gráfico por matriz de curso, o agrupamento interno usa os códigos de cada matriz atual e inclui EM0057 entre as optativas de Materiais.

| Seção e posição no ID | Ranking | Medida e limite |
| --- | --- | --- |
| `1-1` | Mais matrículas | `M` por código, até 5. |
| `1-2` | Mais vagas | `C` por código, até 5. |
| `1-3` | Maior ocupação | Maior `M / C` por código, até 5. |
| `1-4` | Menor ocupação | Menor `M / C` por código, até 5. |
| `1-5` | Mais matrículas acima da capacidade | Soma dos excedentes por código, até 5. |
| `1-6` | Mais vagas não preenchidas | Soma das sobras por código, até 5. |
| `1-7` | Mais semestres no limite ou acima | Contagem de semestres em que `M / C ≥ 100%` para o código, até 4. |
| `1-8` | Mais semestres abaixo de 25% | Contagem de semestres em que `M / C < 25%` para o código, até 4. |
| `1-9` | Mais semestres com oferta | Número de semestres distintos por código, até 5. |
| `1-10` | Mais turmas | `N` por código, até 5. |
| `2-1` | Semestres com maior ocupação | `M / C` por semestre, até 7. |
| `2-2` | Semestres com mais matrículas | `M` por semestre, até 7. |
| `2-3` | Semestres com mais turmas lotadas | Contagem de `rᵢ ≥ 100%` por semestre, até 7. |
| `2-4` | Semestres com mais turmas abaixo de 25% | Contagem de `rᵢ < 25%` por semestre, até 7. |
| `3-1` | Mais turmas por dia e faixa horária | Contagem por dia e faixa de uma hora, considerando as 24 horas, até 5. |
| `3-2` | Ocupação por turno | `M / C` por turno, até 4. |
| `3-3` | Ocupação por prefixo do código | `M / C` por prefixo, até 6. |
| `3-4` | Ocupação por matriz de curso | `M / C` por matriz, até 5. |
| `3-5` | Ocupação nas capacidades de referência | `M / C` por capacidade exata entre 20, 25, 30, 40 e 50 vagas, até 5. |
| `4-1` | Mais matrículas em turmas abertas | `M` por código, até 5. |
| `4-2` | Maior ocupação em turmas abertas | Maior `M / C` por código, até 5. |
| `4-3` | Mais vagas não preenchidas em turmas abertas | Soma das sobras por código, até 5. |
| `4-4` | Menor ocupação em turmas abertas | Menor `M / C` por código, até 5. |

As barras desses rankings usam `100 × valor / teto` para a largura. O teto é comum às três coortes de cada ranking e vale pelo menos 1. Em ocupação, esse mínimo corresponde a 100%. O rótulo apresenta a medida original. [Cálculo em lote](../backend/services/analytics/metrics.py) · [Exportação HTML](../backend/services/presentation/export.py)

## Comparações entre semestres

O comparativo usa a mesma fórmula em cada semestre e cruza medidas com categorias compatíveis. A diferença é `valor comparado − valor de referência`. Em porcentagens, a diferença é expressa em pontos percentuais. Por exemplo, de 40% para 50% são `+10 p.p.` e a variação relativa é `+25%`. A variação relativa divide a diferença pela referência quando ela é positiva e a métrica admite esse cálculo. Índices e coeficientes tratados como decimais têm diferença na escala original.

Em rankings com lista completa disponível, o cruzamento usa a medida por código mesmo quando ele fica fora das barras visíveis. Uma categoria sem valor em um dos semestres fica sem diferença calculada. Curvas com eixo numérico são comparadas nos limiares coincidentes. Mapas de horário cruzam dia e hora, e mapas de ocupação por disciplina cruzam o código dentro da mesma versão de matriz. Dispersões, bolhas e a ocupação de cada turma têm gráficos de referência e ficam sem pareamento ponto a ponto. A categoria agregada **Outras capacidades** fica fora da diferença porque a composição pode variar entre semestres. [Cálculos da comparação](../backend/services/analytics/comparison.py) · [Recortes do painel web](../backend/services/dashboard/interactive.py)

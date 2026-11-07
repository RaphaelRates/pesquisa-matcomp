# Painel de oferta de disciplinas do CCT da UFCA

Aplicação web para explorar vagas, matrículas, ocupação e distribuição das turmas presenciais do Centro de Ciências e Tecnologia da Universidade Federal do Cariri, com uma área dedicada ao curso de Matemática Computacional.

O painel lê o arquivo JSON de turmas, calcula os indicadores no servidor e envia os resultados ao navegador. O navegador monta os gráficos com Chart.js e apresenta mapas de calor em tabelas interativas.

O painel apresenta primeiro os **resultados gerais do CCT** e depois **Matemática Computacional**. As abas globais **Histórico consolidado** e **Oferta de 2026.2** recalculam os gráficos, cartões e análises individuais para o recorte escolhido. A quantidade de visualizações depende do recorte; gráficos redundantes da oferta aberta são omitidos.

## Executar o site

Use Python 3.12 ou superior e um navegador com JavaScript habilitado. O projeto foi verificado com Python 3.14.

Na pasta do projeto, execute

```sh
python app.py
```

Abra [o painel local](http://127.0.0.1:8000/).

O servidor utiliza a biblioteca padrão do Python. O Chart.js 4.6.1 está incluído em `vendor/` e é servido pelo próprio aplicativo.

Para usar outra porta, execute

```sh
python app.py --porta 8080
```

Para utilizar outro arquivo de turmas, execute

```sh
python app.py --dados "caminho/para/turmas.json"
```

Encerre o serviço com `Ctrl+C`.

## Separar os recortes e comparar os resultados

- **Histórico consolidado:** somente turmas `CONSOLIDADA` anteriores a 2026.2, de 2023.1 a 2026.1 na base incluída.
- **Oferta de 2026.2:** somente turmas `ABERTA` de 2026.2. Essa aba recalcula também rankings, horários, distribuição, concentração e associações estatísticas; não reutiliza totais acumulados do histórico.

As abas valem para todo o painel, incluindo CCT, Matemática Computacional e as cadeiras selecionadas. Cada gráfico informa seu recorte.

As comparações usam **2026.2 versus o último semestre consolidado disponível**, 2026.1 na base incluída. O histórico acumulado continua disponível em sua própria aba, mas seus totais de vários semestres não são usados como base para calcular aumento ou redução de um único semestre.

| Medida | Leitura da diferença |
| --- | --- |
| Contagens, vagas e matrículas | Diferença absoluta `2026.2 − referência` e variação relativa `(2026.2 − referência) / referência`. |
| Ocupação e outras proporções | Diferença em **pontos percentuais (p.p.)**. Uma passagem de 40% para 50% corresponde a +10 p.p. |
| Índices e coeficientes | Diferença na escala original do indicador. |

Uma referência igual a zero não produz variação percentual definida. Ausência de uma categoria em um ranking limitado não significa valor zero ou queda de 100%; o painel identifica os casos sem par comparável. Turmas de semestres diferentes também não são emparelhadas apenas pelo número da turma. Curvas com grades distintas e gráficos de dispersão exigem leitura da comparação disponível, sem inventar correspondências entre pontos.

2026.2 ainda está aberto. As diferenças descrevem os registros presentes no arquivo, sem estabelecer causas, aprovação, evasão ou demanda reprimida. A alternância de disciplinas entre semestres e a situação aberta podem afetar a comparação com 2026.1.

## Análise individual das cadeiras

Use **Análise por cadeira** na navegação de cada área. Busque por código ou nome e escolha uma disciplina. O CCT usa todas as disciplinas elegíveis; MC usa a matriz curricular de referência, inclusive códigos compartilhados. Os cartões, o resumo e os gráficos acompanham a aba selecionada.

As famílias de gráficos incluem vagas e matrículas por semestre, ocupação geral e mediana, vagas não preenchidas e matrículas excedentes, quantidade de turmas, ocupação de cada turma, faixas de ocupação, ocupação por turno e distribuição por dia e horário. O catálogo mantém modelos de faixas para consolidadas e abertas, mas o recorte isolado omite a visualização redundante.

Semestres ou cadeiras sem oferta aparecem sem registro, não com ocupação zero. Cada registro recebe um índice no gráfico por turma para distinguir rótulos repetidos. Os gráficos individuais são montados no navegador para a seleção atual. A exportação HTML legada contém os gráficos gerais do histórico consolidado; as novas abas, comparações e o explorador individual estão disponíveis no painel web.

## Catálogo editável dos gráficos

O arquivo **`data/graficos.json`** organiza os gráficos gerais e os modelos compartilhados pelas cadeiras. As entradas do catálogo não representam uma contagem fixa de gráficos visíveis: o recorte seleciona as famílias aplicáveis. Ele é lido pelo servidor a cada reprocessamento, e controla o que o painel exibe. Também pode ser baixado pelo link na área de análise individual ou em `/api/graficos`.

Cada chave identifica um gráfico. Edite estes campos:

| Campo | Finalidade |
| --- | --- |
| `nome` | Título exibido no cartão. |
| `descricao` | Explicação exibida abaixo do título. |
| `tipo` | Formato da visualização, como `bar`, `line`, `donut` ou `heatmap`. |
| `tipos_permitidos` | Referência dos formatos compatíveis com os dados desse gráfico. |

Por exemplo, a entrada `cadeira-oferta` aceita `bar`, `line`, `stackedBar` e `area`. As chaves `cadeira-*` personalizam todas as disciplinas; as demais chaves identificam gráficos gerais específicos. Os tipos são validados no servidor para impedir formatos incompatíveis. Os cálculos permanecem nos serviços Python. Os textos derivados do catálogo são ajustados ao recorte selecionado, e a indicação de escopo acompanha o cartão.

Salve o JSON mantendo sua sintaxe válida e clique em **Recalcular dados** no painel (ou recarregue a página). Não é necessário reiniciar o servidor. Para acrescentar uma nova análise ou alterar seu cálculo, edite o serviço correspondente e inclua uma entrada no catálogo. Preserve nas descrições as distinções entre histórico e oferta aberta.

## Base de dados e recorte da análise

O arquivo padrão é `data/ufca-cct-ofertas-2023-2026.json`. Cada registro representa uma turma de uma disciplina em um semestre.

Entram nos cálculos as turmas com modalidade `Presencial` e capacidade maior que zero. A análise reúne dois recortes.

| Recorte | Registros utilizados |
| --- | --- |
| Histórico consolidado | Turmas com situação `CONSOLIDADA` anteriores a 2026.2. Na base incluída, abrangem 2023.1 a 2026.1. |
| Oferta aberta | Turmas de 2026.2 com situação `ABERTA`. |

O asterisco em **2026.2*** identifica a oferta aberta quando aparece nos rótulos. O escopo informado no gráfico e a aba selecionada identificam quais registros entram nos cálculos.

As listas de códigos das matrizes curriculares estão em `services/calc_metrics.py`. Elas definem as disciplinas obrigatórias e optativas de referência dos cursos de Engenharia Civil, Engenharia de Materiais, Ciência da Computação, Matemática Computacional e Engenharia de Software. O código também considera mudanças conhecidas entre as matrizes CC001 e CC002 de Ciência da Computação.

O recorte de Matemática Computacional seleciona os códigos presentes na matriz de referência do curso. As matrículas dessas turmas podem incluir estudantes de outros cursos.

### Totais da base incluída

Os quatro indicadores apresentados no início de cada área são o número de turmas do recorte selecionado, a capacidade total, as matrículas e a ocupação geral. Os quadros de comparação usam o semestre consolidado de referência, separadamente do histórico acumulado abaixo.

| Área | Recorte | Turmas | Vagas | Matrículas | Ocupação geral |
| --- | --- | ---: | ---: | ---: | ---: |
| CCT | Consolidadas | 1.208 | 48.726 | 26.094 | 53,6% |
| CCT | Abertas em 2026.2 | 172 | 6.995 | 4.032 | 57,6% |
| Matemática Computacional | Consolidadas | 120 | 5.538 | 2.513 | 45,4% |
| Matemática Computacional | Abertas em 2026.2 | 17 | 810 | 408 | 50,4% |

Esses valores descrevem o JSON incluído nesta versão. O site recalcula os resultados ao consultar a base.

## Resultados gerais do CCT

A área reúne oferta e matrículas, mapas de calor, horários, natureza curricular, rankings e análises estatísticas, sempre recalculados para a aba selecionada.

### Oferta e matrículas por semestre

- Vagas e matrículas por semestre.
- Distribuição das turmas por faixa de ocupação.
- Turmas e disciplinas ofertadas, com barras e linha.
- Vagas não preenchidas e matrículas acima da capacidade.
- Ocupação geral por semestre.
- Percentual de turmas com baixa ocupação ou lotadas.

Os gráficos permitem acompanhar simultaneamente o volume de oferta, as matrículas e a proporção de vagas ocupadas.

### Ocupação por prefixo e por disciplina

- **Ocupação por prefixo de código** cruza os prefixos CAR, CC, ECI, EM, ES e MC com os semestres do recorte selecionado.
- **Ocupação de oito disciplinas selecionadas** acompanha CC0015, ECI0079, CAR0011, ECI0002, EM0105, EM0030, EM0043 e EM0114, conforme a aba selecionada.

Os prefixos agrupam disciplinas pelas letras iniciais do código. A comparação por matriz de curso utiliza as listas de códigos curriculares.

### Horários, turnos e tamanho das turmas

| Gráfico | O que mostra |
| --- | --- |
| Concentração da oferta ao longo da semana | Mapa das turmas do recorte por dia e faixa horária, das 7h às 21h59. |
| Ocupação por turno | Razão entre matrículas e vagas das turmas de manhã, tarde, noite e turno misto. |
| Ocupação segundo o tamanho da turma | Ocupação nas cinco capacidades cadastradas mais frequentes no histórico. |

Uma turma que ocupa mais de uma faixa horária aparece nas respectivas células. A soma do mapa de horários representa ocorrências de horário.

### Optativas por curso e por semestre

- **Ocupação das disciplinas listadas como optativas** apresenta a ocupação das optativas por matriz de curso no recorte selecionado.
- **Ocupação por semestre e natureza curricular** compara obrigatórias e optativas nos semestres do recorte selecionado.

A classificação usa as matrizes de referência registradas no código. O gráfico por semestre utiliza códigos com classificação exclusiva, excluindo mudanças conhecidas de natureza. A base incluída não contém registros correspondentes às optativas de Engenharia de Software selecionadas por esse gráfico.

### Explorações visuais

Apresenta os mesmos onze tipos de análise disponíveis na área de MC, calculados para o conjunto de turmas do CCT.

### Rankings de obrigatórias, optativas e geral

Cada grupo apresenta rankings de disciplinas, semestres e características da oferta. Os rankings específicos da oferta aberta que repetem essas análises são omitidos nos recortes isolados.

| Conjunto | Quantidade | Comparações apresentadas |
| --- | ---: | --- |
| Disciplinas do recorte | 10 | Matrículas, vagas ofertadas, maior e menor ocupação acumulada, matrículas excedentes, vagas não preenchidas, recorrência de lotação e baixa ocupação, semestres com oferta e total de turmas. |
| Semestres do recorte | 4 | Ocupação, matrículas, turmas no limite ou acima e turmas abaixo de 25% de ocupação. |
| Oferta, turno e tamanho | 5 | Turmas por dia e faixa horária, ocupação por turno, prefixo, matriz de curso e capacidades de referência. |

Os rankings de disciplinas normalmente selecionam cinco posições dentro do recorte. Os de recorrência selecionam quatro. Os de semestres incluem até sete períodos. Os limites de cada gráfico são definidos em `chart_groups`, em `services/calc_metrics.py`.

Os grupos **Obrigatórias** e **Optativas** usam os códigos classificados para cada natureza no conjunto das matrizes. O grupo **Geral** reúne esses códigos. A disciplina EM0057 integra o conjunto optativo por uma regra de compatibilidade com a base histórica.

Os totais de referência do CCT usam todas as turmas elegíveis. Os rankings gerais usam a união dos conjuntos classificados. Nos rankings por matriz, códigos compartilhados podem contribuir para mais de um curso.

Os rankings de capacidade comparam os tamanhos fixos de **20, 25, 30, 40 e 50 vagas**. O gráfico de tamanhos mais frequentes calcula suas categorias a partir da base.

## Matemática Computacional

A área reúne evolução, mapas de calor, rankings, explorações visuais, análises estatísticas e o explorador de cadeiras.

### Evolução por semestre

| Gráfico | O que mostra |
| --- | --- |
| Vagas e matrículas por semestre | Compara a capacidade ofertada com as matrículas registradas nas disciplinas do curso. |
| Ocupação do curso e do CCT | Compara a razão entre matrículas e vagas de MC com a do centro. O total do CCT inclui MC. |
| Ocupação de obrigatórias e optativas | Compara as duas naturezas curriculares da matriz de MC. |
| Turmas por faixa de ocupação | Conta as turmas em quatro faixas, de abaixo de 25% a 100% ou mais. |
| Turmas e disciplinas ofertadas | Combina barras para turmas e uma linha para códigos distintos de disciplinas. |
| Vagas não preenchidas e matrículas acima da capacidade | Mostra os dois totais, calculados separadamente por turma. |
| Percentual de turmas com baixa ocupação ou lotadas | Compara a parcela de turmas abaixo de 25% com a parcela no limite ou acima da capacidade. |

### Histórico por disciplina

- **Ocupação das obrigatórias por disciplina** acompanha os códigos obrigatórios ao longo dos semestres.
- **Ocupação das optativas por disciplina** apresenta o mesmo acompanhamento para os códigos optativos.

Cada célula mostra a ocupação agregada de um código em um semestre. O traço indica ausência de registro naquele recorte. As tabelas incluem as disciplinas com oferta encontrada na base.

### Rankings das turmas do recorte

Os rankings permitem identificar as disciplinas com

- Mais matrículas.
- Mais semestres abaixo de 25% de ocupação.
- Maior ocupação acumulada.
- Menor ocupação acumulada.
- Mais vagas ofertadas.
- Mais turmas.
- Oferta em mais semestres.
- Mais vagas não preenchidas.
- Mais turmas lotadas.
- Mais matrículas acima da capacidade.
- Mais matrículas entre as obrigatórias.
- Mais matrículas entre as optativas.

Esses gráficos apresentam até dez disciplinas. Os rankings de vagas não preenchidas, turmas lotadas e matrículas excedentes selecionam valores positivos. Empates recebem a mesma posição.

### Explorações visuais

Esta seção reúne linhas, roscas, pizza, radar, dispersão, bolhas, colunas proporcionais e áreas empilhadas. O catálogo de formatos e a leitura de cada gráfico estão descritos mais adiante.

## Catálogo das explorações visuais

Os gráficos abaixo aparecem uma vez em MC e uma vez no CCT, sempre com os dados da respectiva área.

| Gráfico | Formato | Como interpretar |
| --- | --- | --- |
| Ocupação mediana e ocupação geral | Linhas | Compara a turma central da distribuição com a razão entre todas as matrículas e todas as vagas. |
| Vagas e matrículas médias por turma | Linhas | Mostra a média de vagas e de matrículas por turma em cada semestre. |
| Faixas de ocupação nas turmas do recorte | Rosca | Cada fatia representa a proporção de turmas em uma faixa de ocupação, conforme a aba selecionada. |
| Distribuição das turmas do recorte por turno | Rosca | Apresenta a participação de cada turno no total de turmas do recorte. |
| Vagas e matrículas por turma | Dispersão | Cruza capacidade e matrículas. O tamanho do ponto indica quantas turmas compartilham a combinação. A diagonal marca 100% de ocupação. |
| Composição da oferta por capacidade | Pizza | Mostra as cinco capacidades mais frequentes e agrupa as restantes em Outras. |
| Perfil de ocupação por faixa | Radar | Cada eixo corresponde a uma faixa. Mostra a proporção de turmas do recorte nessa faixa. |
| Composição da ocupação ao longo dos semestres | Colunas empilhadas de 100% | Cada coluna reúne todas as turmas de um semestre, divididas proporcionalmente pelas faixas de ocupação. |
| Dimensão da oferta por disciplina | Bolhas | Cada bolha representa um código do recorte. Os eixos somam vagas e matrículas e a área da bolha é proporcional ao número de turmas. |
| Matrículas por natureza curricular | Áreas empilhadas | Soma matrículas por semestre em obrigatórias, optativas e compartilhadas ou sem classificação. |

## Análises estatísticas em cada área

As áreas de MC e CCT apresentam indicadores de distribuição, concentração, associação e limites matemáticos. Os cartões-resumo mostram a mediana, o desvio-padrão em pontos percentuais, o Gini das matrículas por disciplina e a correlação de Pearson entre capacidade e ocupação.

A opção **Explorar os indicadores estatísticos** apresenta média aritmética, quartis, IQR, MAD, coeficiente de variação, assimetria, excesso de curtose, sinalizadores de Tukey, HHI, número efetivo de disciplinas, entropia normalizada, parcela das maiores disciplinas, Spearman e R².

| Conjunto | Gráfico | Aplicação |
| --- | --- | --- |
| Distribuição e robustez | Distribuição detalhada da ocupação | Histograma com seis classes e proporções das turmas do recorte selecionado. |
| Distribuição e robustez | Faixa central de ocupação por semestre | Faixa entre Q1 e Q3 e linha da mediana. Quartis por interpolação linear inclusiva, posição (n − 1)p. |
| Distribuição e robustez | Dispersão relativa da ocupação | Compara desvio-padrão / média e MAD / mediana. |
| Distribuição e robustez | Assimetria e caudas da ocupação | Momentos populacionais de ordem 3 e 4, com excesso de curtose em relação a 3. |
| Distribuição e robustez | Turmas sinalizadas pela regra de Tukey | Conta ocupações fora das cercas Q1 − 1,5 IQR e Q3 + 1,5 IQR de cada semestre. As turmas sinalizadas permanecem nos cálculos. |
| Distribuição e robustez | Distribuição acumulada da ocupação | Mostra a parcela de turmas com ocupação menor ou igual a um limiar. |
| Concentração e diversidade | Concentração das matrículas entre disciplinas | Curva de Lorenz dos totais por código e diagonal de igualdade. |
| Concentração e diversidade | Índices de concentração por semestre | Evolução de Gini e HHI. |
| Concentração e diversidade | Disciplinas ofertadas e diversidade efetiva | Compara códigos ofertados com o número efetivo de disciplinas, 1 / HHI. |
| Concentração e diversidade | Participação das dez maiores disciplinas nas matrículas | Participações individuais dos códigos com mais matrículas no total do recorte. |
| Associações e ajuste | Relação entre capacidade e ocupação por semestre | Coeficientes de Pearson e Spearman. Spearman usa postos médios nos empates. |
| Associações e ajuste | Capacidade e ocupação com ajuste descritivo | Dispersão com reta de mínimos quadrados e R². |
| Limites matemáticos | Ocupação acima de um limiar e limite de Markov | Compara a parcela observada de turmas com ocupação ≥ t com o limite superior média / t. |
| Limites matemáticos | Concentração em torno da média e limite de Chebyshev | Compara a parcela observada dentro de k desvios-padrão com o limite inferior 1 − 1/k². |

As estatísticas usam somente as turmas da aba selecionada, com peso igual por turma. Histograma e distribuição acumulada também são recalculados para esse recorte. Variância e desvio-padrão são populacionais, com divisor n. Índices com denominador zero são apresentados como indefinidos.

As desigualdades de Markov e Chebyshev são aplicadas à distribuição empírica obtida ao escolher uma turma uniformemente entre os registros do recorte selecionado. Markov exige ocupação não negativa e limiar positivo. Chebyshev usa a média aritmética e a variância dessa distribuição. Para variância zero, o painel identifica o caso em que todas as ocupações coincidem. As garantias se referem ao recorte observado.

Os coeficientes de associação e o ajuste linear descrevem a base. A capacidade integra o denominador da ocupação, e as observações incluem disciplinas repetidas em diferentes semestres. Esses aspectos devem acompanhar a interpretação das relações observadas.

Os indicadores de concentração usam matrículas somadas por código. HHI é a soma dos quadrados das participações, na escala de 0 a 1. O número efetivo 1 / HHI corresponde à quantidade de disciplinas com participações iguais que produziria o mesmo HHI. A entropia de Shannon é dividida pelo logaritmo do número de códigos. A parcela das 20% maiores disciplinas utiliza o número de códigos arredondado para cima.

Cada novo gráfico oferece **Método e interpretação**, com sua definição e orientações de leitura.

As definições de quartis e cercas de inspeção seguem a análise exploratória de dados. As cercas de Tukey servem para localizar observações que merecem revisão. [NIST — boxplot](https://www.itl.nist.gov/div898/handbook/eda/section3/boxplot.htm)

Pearson e Spearman são usados como medidas descritivas de associação. [NIST — Pearson](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/correlat.htm), [NIST — correlação por postos](https://www.itl.nist.gov/div898/software/dataplot/refman2/ch2/rankcorr.pdf)

As aplicações de Markov e Chebyshev utilizam suas condições para variáveis aleatórias e momentos. [University of British Columbia — desigualdades de concentração](https://www.cs.ubc.ca/~dsuth/532D/26w1/notes/html/chap_concentration.html)

Lorenz, Gini e HHI são adaptados aos totais de matrículas por disciplina. [Banco Mundial — índice de Gini](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.GINI), [DOJ — definição do HHI](https://www.justice.gov/atr/herfindahl-hirschman-index)

## Como os indicadores são calculados

| Indicador | Cálculo |
| --- | --- |
| Turmas | Quantidade de registros incluídos no recorte. |
| Disciplinas ofertadas | Quantidade de códigos distintos no recorte. |
| Vagas ofertadas | Soma de `capacidade`. |
| Matrículas | Soma de `matriculas`. |
| Ocupação da turma | `matriculas / capacidade`. |
| Ocupação geral ou acumulada | `soma(matriculas) / soma(capacidade)`. |
| Ocupação mediana | Mediana dos percentuais de ocupação das turmas. |
| Vagas não preenchidas | Soma de `max(capacidade - matriculas, 0)` para cada turma. |
| Matrículas acima da capacidade | Soma de `max(matriculas - capacidade, 0)` para cada turma. |
| Turmas lotadas | Contagem das turmas com ocupação maior ou igual a 100%. |
| Turmas de baixa ocupação | Contagem das turmas com ocupação abaixo de 25%. |
| Semestres com oferta | Quantidade de semestres distintos com registros do código. |

As faixas de ocupação são **abaixo de 25%**, **25% a menos de 50%**, **50% a menos de 100%** e **100% ou mais**.

A ocupação geral pondera os resultados pela capacidade das turmas. Por exemplo, turmas com 10 matrículas em 20 vagas e 40 matrículas em 100 vagas produzem uma ocupação geral de **50 / 120 = 41,7%** e uma ocupação mediana de **45%**.

Nos rankings de recorrência, matrículas e vagas são primeiro agregadas por código e semestre. Depois são contados os semestres no limite ou acima da capacidade, ou abaixo de 25%.

Os turnos são classificados pelos horários cadastrados. Manhã abrange horários antes das 12h, tarde vai das 12h às 18h e noite começa às 18h. Aulas que atravessam turnos entram em **Misto**. A ausência de horário reconhecido produz a categoria **Sem horário** nas análises que a incluem.

### Leitura dos resultados

Matrículas representam inscrições em turmas. Uma pessoa matriculada em várias disciplinas contribui para vários registros.

Uma ocupação acima de 100% indica matrículas superiores à capacidade cadastrada. Vagas não preenchidas e matrículas excedentes são apuradas turma a turma, preservando os dois totais mesmo quando ocorrem no mesmo curso.

Os resultados de 2026.2 refletem o estado das turmas abertas no arquivo. Comparações com o histórico consolidado devem considerar essa diferença de situação.

Um traço nos mapas indica ausência de registro no cruzamento analisado. A presença de turma com zero matrículas corresponde a ocupação de 0%.

## Navegação e interação

- A navegação fixa leva primeiro ao CCT e depois a MC.
- As abas globais alternam histórico consolidado e oferta de 2026.2.
- As comparações identificam a referência consolidada e apresentam aumentos, reduções ou ausência de par comparável.
- Cada área possui um índice de seções e indicadores-resumo.
- Cada cartão apresenta o formato, o título, a descrição e um link direto para o gráfico.
- Passar o mouse ou tocar nos gráficos permite consultar detalhes como valores, porcentagens e totais relacionados.
- Clicar nas legendas dos gráficos Chart.js permite ocultar ou reexibir séries ou categorias.
- Com o teclado, use `Tab` para focar um gráfico e as setas para percorrer os pontos. `Home` e `End` levam ao primeiro e ao último ponto. `Escape` fecha o destaque.
- A opção **Consultar dados** abre a tabela do gráfico.
- Os gráficos são carregados conforme se aproximam da área visível da página.
- O layout utiliza até três colunas em telas amplas e uma coluna em telas menores. Tabelas extensas possuem rolagem horizontal.

## Atualizar os dados

Edite ou substitua o JSON e use **Recalcular dados** ou atualize a página do navegador. A consulta a `/api/painel` relê o arquivo, prepara os registros e recalcula os resultados dos dois recortes e da referência.

O painel calcula uma assinatura **SHA-256** do arquivo fonte e informa se ele mudou desde a última consulta nesta aba do navegador. A primeira consulta estabelece a referência local. A data e a hora de reprocessamento indicam quando o cálculo foi executado; sozinhas, não comprovam que a base mudou. A assinatura detecta mudança no arquivo, inclusive de formatação, e não apenas alteração de matrículas.

Antes dos indicadores, o pré-processamento valida e normaliza textos, códigos, semestres, horários e contagens. Números ausentes, negativos ou fracionários são descartados com o registro correspondente e aparecem no relatório. Contagens numéricas em texto são convertidas quando representam inteiros válidos.

A deduplicação exige identidade de turma preenchida e conteúdo coincidente após a normalização, desconsiderando apenas os campos de proveniência `origem` e `linha`. Versões conflitantes de uma mesma turma permanecem na base tratada e são sinalizadas. O arquivo de origem é preservado.

A seção **Qualidade e preparação da base** informa quantos registros foram lidos, normalizados, descartados, deduplicados e incluídos no recorte. Também apresenta exclusões por modalidade, capacidade, situação ou semestre e avisos de horário. O processamento é realizado novamente em cada consulta.

A estrutura esperada é uma lista de objetos. Os campos utilizados nos cálculos são

| Campo | Conteúdo |
| --- | --- |
| `periodo` | Semestre, como `2026.2`. |
| `codigo` | Código da disciplina. |
| `disciplina` | Nome da disciplina. |
| `modalidade` | Modalidade da turma. O recorte usa `Presencial`. |
| `situacao` | Situação da turma, como `CONSOLIDADA` ou `ABERTA`. |
| `horario` | Texto com dias e intervalos, como `SEG 08:00-10:00`. |
| `matriculas` | Quantidade numérica de matrículas. |
| `capacidade` | Quantidade numérica de vagas cadastradas. |

A base também armazena `turma`, `docentes`, `tipo`, `local`, `origem` e `linha`. Esses campos preservam informações do registro de origem.

O período aberto de referência e as listas de códigos curriculares estão definidos em `services/calc_metrics.py`. A ampliação para outro semestre aberto ou outra matriz envolve atualizar essas referências e os textos correspondentes do painel.

Se o arquivo não puder ser lido ou processado, a API responde com HTTP 503 e a página apresenta uma mensagem de falha no carregamento. Após corrigir o arquivo, atualize a página.

## Organização do projeto

| Caminho | Responsabilidade |
| --- | --- |
| `app.py` | Servidor HTTP, página inicial, arquivos locais e rota de indicadores. |
| `services/calc_metrics.py` | Recortes, matrizes curriculares, indicadores e definição dos gráficos. |
| `services/preprocessing.py` | Validação, normalização, deduplicação conservadora e relatório de qualidade. |
| `services/statistics_metrics.py` | Estatísticas descritivas, concentração, associações e aplicações de Markov e Chebyshev. |
| `services/period_views.py` | Recortes independentes do histórico, da oferta aberta e do semestre consolidado de referência. |
| `services/period_comparison.py` | Pareamento das métricas e cálculo das diferenças entre 2026.2 e a referência. |
| `services/chart_catalog.py` | Aplicação e validação do catálogo editável dos gráficos. |
| `services/discipline_metrics.py` | Indicadores e gráficos individuais por cadeira. |
| `services/graph.py` | Leitura do JSON, montagem da resposta de dados e recursos de apresentação compartilhados. Inclui exportação estática. |
| `painel.js` | Montagem dos cartões, gráficos Chart.js, mapas de calor e interações no navegador. |
| `painel.css` | Layout, tipografia, cores e adaptação a diferentes telas. |
| `data/ufca-cct-ofertas-2023-2026.json` | Registros de turmas usados pela aplicação. |
| `vendor/chart.umd.min.js` | Distribuição local do Chart.js. |
| `vendor/Chart.js-LICENSE.md` | Licença da biblioteca incluída. |

O aplicativo funciona como um monólito. Um processo Python serve a interface e a API. Ao abrir a página, o navegador solicita os indicadores em `GET /api/painel` e desenha as visualizações com a resposta.

O serviço escuta em `127.0.0.1`, na porta 8000 por padrão. A página inicial está em `/`, e os arquivos de apresentação são servidos em `/painel.js`, `/painel.css` e `/vendor/chart.umd.min.js`.

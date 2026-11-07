# Painel de oferta de disciplinas do CCT da UFCA

Aplicação web para explorar vagas, matrículas, ocupação e distribuição das turmas presenciais do Centro de Ciências e Tecnologia da Universidade Federal do Cariri, com uma área dedicada ao curso de Matemática Computacional.

O painel lê o arquivo JSON de turmas, calcula os indicadores no servidor e envia os resultados ao navegador. O navegador monta os gráficos com Chart.js e apresenta mapas de calor em tabelas interativas.

Com a base incluída no projeto, o site apresenta **129 visualizações**, sendo **36 de Matemática Computacional** e **93 dos resultados gerais do CCT**.

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

## Base de dados e recorte da análise

O arquivo padrão é `data/ufca-cct-ofertas-2023-2026.json`. Cada registro representa uma turma de uma disciplina em um semestre.

Entram nos cálculos as turmas com modalidade `Presencial` e capacidade maior que zero. A análise reúne dois recortes.

| Recorte | Registros utilizados |
| --- | --- |
| Histórico consolidado | Turmas com situação `CONSOLIDADA`. Na base incluída, abrangem 2023.1 a 2026.1. |
| Oferta aberta | Turmas de 2026.2 com situação `ABERTA`. |

O asterisco em **2026.2*** identifica a oferta aberta. Nos gráficos de linha, o trecho que chega a esse semestre é tracejado.

As listas de códigos das matrizes curriculares estão em `services/calc_metrics.py`. Elas definem as disciplinas obrigatórias e optativas de referência dos cursos de Engenharia Civil, Engenharia de Materiais, Ciência da Computação, Matemática Computacional e Engenharia de Software. O código também considera mudanças conhecidas entre as matrizes CC001 e CC002 de Ciência da Computação.

O recorte de Matemática Computacional seleciona os códigos presentes na matriz de referência do curso. As matrículas dessas turmas podem incluir estudantes de outros cursos.

### Totais da base incluída

Os quatro indicadores apresentados no início de cada área são o número de turmas consolidadas, a capacidade total, as matrículas e a ocupação geral. A oferta aberta de 2026.2 é informada separadamente.

| Área | Recorte | Turmas | Vagas | Matrículas | Ocupação geral |
| --- | --- | ---: | ---: | ---: | ---: |
| Matemática Computacional | Consolidadas | 120 | 5.538 | 2.513 | 45,4% |
| Matemática Computacional | Abertas em 2026.2 | 17 | 810 | 408 | 50,4% |
| CCT | Consolidadas | 1.208 | 48.726 | 26.094 | 53,6% |
| CCT | Abertas em 2026.2 | 172 | 6.995 | 4.032 | 57,6% |

Esses valores descrevem o JSON incluído nesta versão. O site recalcula os resultados ao consultar a base.

## Matemática Computacional

Esta área contém cinco seções.

### Evolução por semestre — 7 gráficos

| Gráfico | O que mostra |
| --- | --- |
| Vagas e matrículas por semestre | Compara a capacidade ofertada com as matrículas registradas nas disciplinas do curso. |
| Ocupação do curso e do CCT | Compara a razão entre matrículas e vagas de MC com a do centro. O total do CCT inclui MC. |
| Ocupação de obrigatórias e optativas | Compara as duas naturezas curriculares da matriz de MC. |
| Turmas por faixa de ocupação | Conta as turmas em quatro faixas, de abaixo de 25% a 100% ou mais. |
| Turmas e disciplinas ofertadas | Combina barras para turmas e uma linha para códigos distintos de disciplinas. |
| Vagas não preenchidas e matrículas acima da capacidade | Mostra os dois totais, calculados separadamente por turma. |
| Percentual de turmas com baixa ocupação ou lotadas | Compara a parcela de turmas abaixo de 25% com a parcela no limite ou acima da capacidade. |

### Histórico por disciplina — 2 mapas de calor

- **Ocupação das obrigatórias por disciplina** acompanha os códigos obrigatórios ao longo dos semestres.
- **Ocupação das optativas por disciplina** apresenta o mesmo acompanhamento para os códigos optativos.

Cada célula mostra a ocupação agregada de um código em um semestre. O traço indica ausência de registro naquele recorte. As tabelas incluem as disciplinas com oferta encontrada na base.

### Rankings das turmas consolidadas — 12 gráficos

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

### Rankings das turmas abertas em 2026.2 — 4 gráficos

- **Ocupação das disciplinas abertas** ordena todas as disciplinas com oferta aberta pela ocupação.
- **Vagas ainda não preenchidas** ordena todas essas disciplinas pelas vagas disponíveis.
- **Mais matrículas nas turmas abertas** apresenta até dez disciplinas com os maiores totais.
- **Menor ocupação nas turmas abertas** apresenta até dez disciplinas com os menores percentuais.

### Explorações visuais — 11 gráficos

Esta seção reúne linhas, roscas, pizza, radar, dispersão, bolhas, colunas proporcionais e áreas empilhadas. O catálogo de formatos e a leitura de cada gráfico estão descritos mais adiante.

## Resultados gerais do CCT

Esta área contém 93 visualizações, organizadas em oito painéis.

### Oferta e matrículas por semestre — 6 gráficos

- Vagas e matrículas por semestre.
- Distribuição das turmas por faixa de ocupação.
- Turmas e disciplinas ofertadas, com barras e linha.
- Vagas não preenchidas e matrículas acima da capacidade.
- Ocupação geral por semestre.
- Percentual de turmas com baixa ocupação ou lotadas.

Os gráficos permitem acompanhar simultaneamente o volume de oferta, as matrículas e a proporção de vagas ocupadas.

### Ocupação por prefixo e por disciplina — 2 mapas de calor

- **Ocupação por prefixo de código** cruza os prefixos CAR, CC, ECI, EM, ES e MC com os semestres consolidados.
- **Ocupação de oito disciplinas selecionadas** acompanha CC0015, ECI0079, CAR0011, ECI0002, EM0105, EM0030, EM0043 e EM0114, incluindo a oferta aberta quando existente.

Os prefixos agrupam disciplinas pelas letras iniciais do código. A comparação por matriz de curso utiliza as listas de códigos curriculares.

### Horários, turnos e tamanho das turmas — 3 gráficos

| Gráfico | O que mostra |
| --- | --- |
| Concentração da oferta ao longo da semana | Mapa das turmas consolidadas por dia e faixa horária, das 7h às 21h59. |
| Ocupação por turno | Razão entre matrículas e vagas das turmas de manhã, tarde, noite e turno misto. |
| Ocupação segundo o tamanho da turma | Ocupação nas cinco capacidades cadastradas mais frequentes no histórico. |

Uma turma que ocupa mais de uma faixa horária aparece nas respectivas células. A soma do mapa de horários representa ocorrências de horário.

### Optativas por curso e por semestre — 2 gráficos

- **Ocupação das disciplinas listadas como optativas** compara os recortes consolidado e aberto por matriz de curso.
- **Ocupação por semestre e natureza curricular** compara obrigatórias e optativas no histórico consolidado.

A classificação usa as matrizes de referência registradas no código. O gráfico por semestre utiliza códigos com classificação exclusiva, excluindo mudanças conhecidas de natureza. A base incluída não contém registros correspondentes às optativas de Engenharia de Software selecionadas por esse gráfico.

### Explorações visuais — 11 gráficos

Apresenta os mesmos onze tipos de análise disponíveis na área de MC, calculados para o conjunto de turmas do CCT.

### Rankings de obrigatórias, optativas e geral — 69 gráficos

Cada grupo contém 23 gráficos, distribuídos em quatro conjuntos.

| Conjunto | Quantidade | Comparações apresentadas |
| --- | ---: | --- |
| Disciplinas consolidadas | 10 | Matrículas, vagas ofertadas, maior e menor ocupação acumulada, matrículas excedentes, vagas não preenchidas, recorrência de lotação e baixa ocupação, semestres com oferta e total de turmas. |
| Semestres consolidados | 4 | Ocupação, matrículas, turmas no limite ou acima e turmas abaixo de 25% de ocupação. |
| Oferta, turno e tamanho | 5 | Turmas por dia e faixa horária, ocupação por turno, prefixo, matriz de curso e capacidades de referência. |
| Turmas abertas de 2026.2 | 4 | Matrículas, maior ocupação, vagas não preenchidas e menor ocupação por disciplina. |

Os rankings de disciplinas normalmente selecionam cinco posições. Os de recorrência selecionam quatro. Os de semestres incluem até sete períodos. Os limites de cada gráfico são definidos em `chart_groups`, em `services/calc_metrics.py`.

Os grupos **Obrigatórias** e **Optativas** usam os códigos classificados para cada natureza no conjunto das matrizes. O grupo **Geral** reúne esses códigos. A disciplina EM0057 integra o conjunto optativo por uma regra de compatibilidade com a base histórica.

Os totais de referência do CCT usam todas as turmas elegíveis. Os rankings gerais usam a união dos conjuntos classificados. Nos rankings por matriz, códigos compartilhados podem contribuir para mais de um curso.

Os rankings de capacidade comparam os tamanhos fixos de **20, 25, 30, 40 e 50 vagas**. O gráfico de tamanhos mais frequentes calcula suas categorias a partir da base.

## Catálogo das explorações visuais

Os gráficos abaixo aparecem uma vez em MC e uma vez no CCT, sempre com os dados da respectiva área.

| Gráfico | Formato | Como interpretar |
| --- | --- | --- |
| Ocupação mediana e ocupação geral | Linhas | Compara a turma central da distribuição com a razão entre todas as matrículas e todas as vagas. |
| Vagas e matrículas médias por turma | Linhas | Mostra a média de vagas e de matrículas por turma em cada semestre. |
| Faixas de ocupação nas turmas consolidadas | Rosca | Cada fatia representa a proporção de turmas consolidadas em uma faixa. |
| Faixas de ocupação nas turmas abertas de 2026.2 | Rosca | Mostra a composição das turmas abertas pelas mesmas faixas. |
| Distribuição das turmas consolidadas por turno | Rosca | Apresenta a participação de cada turno no total de turmas. |
| Vagas e matrículas por turma consolidada | Dispersão | Cruza capacidade e matrículas. O tamanho do ponto indica quantas turmas compartilham a combinação. A diagonal marca 100% de ocupação. |
| Composição da oferta por capacidade | Pizza | Mostra as cinco capacidades mais frequentes e agrupa as restantes em Outras. |
| Perfil de ocupação por faixa | Radar | Cada eixo corresponde a uma faixa. Compara a proporção de turmas consolidadas e abertas nessa faixa. |
| Composição da ocupação ao longo dos semestres | Colunas empilhadas de 100% | Cada coluna reúne todas as turmas de um semestre, divididas proporcionalmente pelas faixas de ocupação. |
| Dimensão da oferta por disciplina | Bolhas | Cada bolha representa um código. Os eixos somam vagas e matrículas e a área da bolha é proporcional ao número de turmas. |
| Matrículas por natureza curricular | Áreas empilhadas | Soma matrículas por semestre em obrigatórias, optativas e compartilhadas ou sem classificação. |

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

- A navegação fixa leva às áreas de MC e do CCT.
- Cada área possui um índice de seções e indicadores-resumo.
- Cada cartão apresenta o formato, o título, a descrição e um link direto para o gráfico.
- Passar o mouse ou tocar nos gráficos permite consultar detalhes como valores, porcentagens e totais relacionados.
- Clicar nas legendas dos gráficos Chart.js permite ocultar ou reexibir séries ou categorias.
- Com o teclado, use `Tab` para focar um gráfico e as setas para percorrer os pontos. `Home` e `End` levam ao primeiro e ao último ponto. `Escape` fecha o destaque.
- A opção **Consultar dados** abre a tabela do gráfico.
- Os gráficos são carregados conforme se aproximam da área visível da página.
- O layout utiliza até três colunas em telas amplas e uma coluna em telas menores. Tabelas extensas possuem rolagem horizontal.

## Atualizar os dados

Edite ou substitua o JSON e atualize a página do navegador. A consulta a `/api/painel` relê o arquivo e recalcula os resultados.

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
| `services/graph.py` | Leitura do JSON, montagem da resposta de dados e recursos de apresentação compartilhados. Inclui exportação estática. |
| `painel.js` | Montagem dos cartões, gráficos Chart.js, mapas de calor e interações no navegador. |
| `painel.css` | Layout, tipografia, cores e adaptação a diferentes telas. |
| `data/ufca-cct-ofertas-2023-2026.json` | Registros de turmas usados pela aplicação. |
| `vendor/chart.umd.min.js` | Distribuição local do Chart.js. |
| `vendor/Chart.js-LICENSE.md` | Licença da biblioteca incluída. |

O aplicativo funciona como um monólito. Um processo Python serve a interface e a API. Ao abrir a página, o navegador solicita os indicadores em `GET /api/painel` e desenha as visualizações com a resposta.

O serviço escuta em `127.0.0.1`, na porta 8000 por padrão. A página inicial está em `/`, e os arquivos de apresentação são servidos em `/painel.js`, `/painel.css` e `/vendor/chart.umd.min.js`.

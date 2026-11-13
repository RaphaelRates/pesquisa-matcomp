# Painel de oferta de disciplinas do CCT da UFCA

Aplicação local para explorar vagas, matrículas, ocupação e distribuição das turmas do CCT. Python calcula os indicadores a partir dos arquivos por semestre. O frontend usa Svelte 5 e a cópia local do Chart.js.

A base incluída cobre **16 semestres, de 2019.1 a 2026.2**, com 2.643 registros. No panorama do CCT e nas páginas dos cinco cursos, é possível consultar o resumo anual, comparar semestres e explorar a oferta por disciplina.

## Executar

Requer Python 3.12 ou superior e Node.js 20.19+ na série 20 ou 22.12+. Na raiz do projeto:

```sh
npm --prefix frontend ci
npm --prefix frontend run build
python backend/app.py
```

O Vite compila o frontend em `frontend/dist/`. O processo Python serve a interface e a API em portas separadas. Durante alterações no frontend, mantenha `npm --prefix frontend run dev` em outro terminal para recompilar ao salvar.

Abra [o frontend](http://localhost:8000/) ou consulte [a API](http://localhost:8001/api/v1/painel/cct). Para escolher outras portas no PowerShell:

```powershell
$env:FRONTEND_PORT = '8080'
$env:API_PORT = '8081'
python backend/app.py
```

A opção `--dados` aceita uma pasta com arquivos por semestre ou um JSON externo contendo uma lista de turmas:

```sh
python backend/app.py --dados data/ufca
python backend/app.py --dados caminho/para/turmas.json
```

O servidor usa a biblioteca padrão do Python e escuta em `localhost` por padrão. Encerre com `Ctrl+C`.

## Executar com Docker

Inicie o Docker Desktop ou o Docker Engine com Compose. Na raiz do projeto, execute:

```sh
docker compose up --build -d --wait
docker compose ps
```

Abra [o frontend](http://localhost:8000/) ou consulte [a API do CCT](http://localhost:8001/api/v1/painel/cct). A imagem compila o Svelte em uma etapa com Node.js e executa o servidor Python em outra. O Compose publica as duas portas apenas na interface local e verifica se a API e o frontend compilado respondem.

O Compose monta `data/` em modo somente leitura. Ao mudar os dados ou o catálogo no computador, use **Atualizar dados** no painel. Após alterações no código, execute novamente `docker compose up --build -d --wait`.

Para mudar as portas ou a base, ajuste as [variáveis de ambiente](#variáveis-de-ambiente) e execute novamente `docker compose up -d --wait`.

```sh
docker compose logs -f painel
docker compose down
```

## Variáveis de ambiente

Com Docker Compose, copie [`.env.example`](.env.example) para `.env` na raiz e edite os valores. Ao executar o Python diretamente, defina as variáveis no terminal, como no exemplo da seção **Executar**. O Python lê o ambiente do processo.

| Variável | Padrão | Uso |
| --- | --- | --- |
| `FRONTEND_PORT` | `8000` | Porta do painel Svelte. |
| `API_PORT` | `8001` | Porta da API. O navegador recebe esse valor ao abrir o painel. |
| `HOST` | `localhost` | Endereço de escuta na execução direta do Python. No Docker, o Compose publica as duas portas apenas na interface local. |
| `DATA_PATH` | `data/ufca` | Diretório de semestres ou arquivo JSON. No Docker, indique um caminho dentro de `data/`, como `data/ufca/2022.1.json`. |
| `LOG_LEVEL` | `INFO` | Verbosidade do servidor. Aceita `DEBUG`, `INFO`, `WARNING`, `ERROR` e `CRITICAL`. Use `WARNING` para ocultar o log de cada requisição. |

Use portas diferentes para o frontend e a API. Na execução direta, `--porta`, `--porta-api`, `--host`, `--dados` e `--log-level` têm prioridade sobre as variáveis correspondentes.

## Usar o painel

### Navegação por curso

O cabeçalho reúne o panorama do CCT e as páginas dos cinco cursos. Em telas de até 900 px, o botão de hambúrguer abre um menu lateral deslizante. Feche pelo botão do menu, pela área externa ou pela tecla Esc.

Ao trocar de curso, o Svelte atualiza o conteúdo e a URL no mesmo documento, mantendo o cabeçalho. Os botões Voltar e Avançar do navegador e os links diretos para cursos continuam funcionando.

| Página | Recorte |
| --- | --- |
| `/` | Panorama do Centro de Ciências e Tecnologia |
| `/cursos/mc` | Matemática Computacional |
| `/cursos/cc` | Ciência da Computação |
| `/cursos/em` | Engenharia de Materiais |
| `/cursos/eci` | Engenharia Civil |
| `/cursos/es` | Engenharia de Software |

Cada página oferece os mesmos **37 gráficos gerais**, com séries por semestre, horários, capacidade, distribuição, rankings e estatísticas. O panorama tem **3 gráficos de comparação entre cursos**. Cada curso tem **16 gráficos específicos** de ocupação em relação ao CCT, natureza curricular, histórico e rankings por disciplina. Todas as páginas oferecem busca por código ou nome, com **8 gráficos** para a cadeira selecionada.

Os indicadores da página aparecem primeiro. Ao chegar a cerca de 240 px da área visível, cada seção faz sua própria requisição assíncrona. A primeira seção com gráficos carrega o módulo de visualização. Com os dados calculados, o Svelte monta cada gráfico próximo da tela. O primeiro gráfico em canvas carrega o Chart.js. Os links das seções e dos gráficos abrem diretamente o conteúdo correspondente.

Os cursos usam os códigos das matrizes de referência, incluindo os códigos CAR compartilhados que nelas aparecem. Uma disciplina CAR pode contribuir para mais de um curso. Cada turma contribui uma vez para o total do CCT, calculado diretamente sobre a base filtrada.

### Recortes temporais

- **Todos os dados** reúne turmas consolidadas e abertas de todos os semestres disponíveis.
- **Mais recente × anterior** compara os dois últimos semestres com oferta do curso.
- **Escolher semestres** permite selecionar o semestre de referência e o semestre comparado. Clique em **Aplicar à página** para atualizar os indicadores, o resumo anual, os gráficos e a análise por cadeira.

Cada curso usa os semestres em que há pelo menos uma turma elegível de sua matriz no recorte selecionado. Na base incluída, Engenharia de Software tem oferta em 2025.1, 2025.2, 2026.1 e 2026.2. Na análise de uma cadeira, uma lacuna indica que a cadeira ficou sem oferta naquele semestre do curso.

O **Resumo anual** mostra os semestres com oferta no recorte e seus totais de turmas, vagas e matrículas. A ocupação do ano divide o total de matrículas pelo total de vagas.

O modo é preservado ao navegar entre cursos. Cada curso abre sua própria seleção de semestres. Um par pode ser compartilhado em uma URL como `/cursos/mc?recorte=compare&referencia=2025.2&semestre=2026.2`. Para compartilhar uma seleção de cadeira, use `disciplina`. O asterisco identifica séries que incluem turmas abertas.

Nos modos de comparação, os detalhes dos gráficos usam os mesmos semestres escolhidos no topo. Contagens apresentam diferenças absolutas e relativas. Ocupação apresenta também a diferença em pontos percentuais. A variação relativa é definida para bases positivas.

### Matrizes curriculares

Em **Análises específicas do curso**, abra **Ocupação das obrigatórias por disciplina**. As linhas seguem o semestre curricular e a ordem das disciplinas dentro dele. Cada coluna representa um semestre de oferta. Um traço indica ausência de oferta elegível para a disciplina naquele semestre.

O painel oferece dez matrizes. A versão padrão de cada curso segue a aba **Matriz Curricular** no portal da UFCA. Quando há versões anteriores, escolha a grade no seletor **Matriz curricular**. O link **Matriz da UFCA** no gráfico abre a fonte da versão selecionada. Uma turma pode aparecer em duas matrizes quando seu código consta em ambas.

| Curso | Matriz padrão | Matrizes anteriores |
| --- | --- | --- |
| Matemática Computacional | MC002 · 2023.1 | MC001 · 2019.1 |
| Ciência da Computação | CC002 · 2023 | CC001 · 2019 |
| Engenharia de Materiais | EM01 · 2023.1 | 2010.1 · PPC 2009 |
| Engenharia Civil | ECI01 · 2023.1 | 2018.1 · PPC 2018.2 e 2006.2 |
| Engenharia de Software | ES01 · 2025.1 | — |

## Dados por semestre

A fonte padrão é a pasta `data/ufca/`:

```text
data/
├── graficos.json
└── ufca/
    ├── README.md
    ├── 2019.1.json
    ├── 2019.2.json
    ├── 2020.1.json
    ├── 2020.2.json
    ├── 2021.1.json
    ├── 2021.2.json
    ├── 2022.1.json
    ├── 2022.2.json
    ├── 2023.1.json
    ├── 2023.2.json
    ├── 2024.1.json
    ├── 2024.2.json
    ├── 2025.1.json
    ├── 2025.2.json
    ├── 2026.1.json
    └── 2026.2.json
```

Os 2.643 registros de 2019.1 a 2026.2 vêm das listagens do SIGAA fornecidas em anexos. A oferta aberta mais recente da base é de 2026.2.

Para acrescentar um semestre, coloque um arquivo `AAAA.1.json` ou `AAAA.2.json` em `data/ufca/` e use **Atualizar dados**. A API relê a pasta, valida o JSON e recalcula os recortes sem alterações no código ou reinício. Use uma lista de objetos em UTF-8 e informe em cada objeto o mesmo `periodo` do nome do arquivo. Nomes de semestre inválidos, períodos conflitantes e JSON malformado geram erro de leitura.

Cada registro contém `periodo`, `codigo`, `disciplina`, `turma`, `docentes`, `tipo`, `modalidade`, `situacao`, `horario`, `local`, `matriculas` e `capacidade`; os campos de proveniência `origem` e `linha` também são preservados.

Textos, códigos, números e horários são normalizados antes dos cálculos. Duplicatas exatas com identidade confirmada são removidas em memória; conflitos são preservados e informados. Entram nos gráficos as turmas presenciais com capacidade positiva e situação compatível com o recorte. EAD e registros de outras situações permanecem nos arquivos, mas ficam fora desses indicadores.

Na base incluída, o acumulado do CCT contém **2.501 turmas, 103.795 vagas e 55.516 matrículas**, com **53,5% de ocupação**. Os números somam 16 semestres, com as matrículas contadas por registro de turma e as vagas por oferta.

No mapa de horários, uma turma com aula das 8h às 10h entra nas faixas de 08h e 09h do dia correspondente. Selecione uma célula para ver a contagem por semestre no mapa do grupo, ou a lista de turmas no mapa da disciplina.

O botão **Atualizar dados**, na seção de qualidade, relê a base e o catálogo. A identificação SHA-256 da fonte considera os nomes e conteúdos dos arquivos. A preparação e os cálculos ocorrem em memória.

## Possíveis ofertas conjuntas e choques de horário

A preparação sinaliza códigos distintos com docentes, horários completos, datas e locais coincidentes, além de sobreposições de horário de um mesmo docente. Também sinaliza turmas presenciais distintas com o mesmo código de sala e sobreposição de horário em datas compatíveis, inclusive quando os docentes são diferentes. O aviso amarelo do CCT mostra todos os casos da base. Nas páginas de curso, aparece somente se houver casos que envolvam alguma turma da matriz. Os detalhes mantêm as demais turmas envolvidas para explicar o conflito. A seção **Qualidade e preparação da base** tem um atalho quando há casos a mostrar. O relatório da base atual está em [docs/consistencia-turmas.md](docs/consistencia-turmas.md).

São indícios, não duplicatas confirmadas: a capacidade pode representar uma cota por código. Todos os registros envolvidos nos casos sinalizados ficam fora dos indicadores até revisão, incluindo equivalências de local inferidas e sobreposições de docente. Os arquivos originais permanecem intactos; capacidades não são substituídas por estimativas. Equivalências de rótulos de local, como Sala/Bloco, são identificadas como inferidas. Confirmar vínculos e cotas no sistema acadêmico é necessário antes de deduplicar ou criar um identificador de turma conjunta. Os totais representam ofertas por código e não garantem contagem de turmas físicas únicas.

## Configuração e cálculos

Edite `data/graficos.json` para alterar `nome`, `descricao` e `tipo`. O campo `tipos_permitidos` documenta os formatos compatíveis, validados no servidor. Os gráficos gerais de grupo compartilham as entradas originais por `catalogKey`; os quatro rankings gerais e as três comparações entre cursos têm entradas próprias. As chaves `cadeira-*` personalizam as análises individuais. Salve e use Atualizar dados; não é necessário reiniciar o servidor para alterações nos dados ou catálogo.

O cadastro dos cursos fica em `backend/services/domain/courses.py`. As classificações de referência ficam em `backend/services/domain/curricula.py`, e a ordem de obrigatórias de cada PPC em `backend/services/domain/ppcs.py`. O recorte inclui os códigos identificados em matrizes anteriores, inclusive optativas. A classificação da matriz atual tem precedência nas análises gerais.

| Indicador | Cálculo |
| --- | --- |
| Turmas | Quantidade de registros elegíveis. |
| Vagas | Soma de `capacidade`. |
| Matrículas | Soma de `matriculas`. |
| Ocupação geral | Soma de matrículas dividida pela soma de vagas. |
| Vagas não preenchidas | Soma de `max(capacidade - matriculas, 0)` por turma. |
| Matrículas excedentes | Soma de `max(matriculas - capacidade, 0)` por turma. |

A ocupação geral pondera pela capacidade; mediana e outras estatísticas de ocupação atribuem o mesmo peso a cada turma. Variância e desvio-padrão são populacionais, quartis usam interpolação inclusiva e medidas indefinidas permanecem sem valor. Gini, HHI e diversidade usam matrículas por código. Pearson, Spearman e o ajuste linear descrevem associações; capacidade também integra o denominador da ocupação. Markov e Chebyshev são aplicados à distribuição empírica observada. Esses resultados não medem aprovação, evasão nem procura reprimida.

## Estrutura do projeto

```text
frontend/
├── src/
│   ├── pages/                  Composição das páginas por curso.
│   ├── features/dashboard/     Recortes, disciplinas, indicadores e qualidade.
│   ├── components/
│   │   ├── charts/              Cartão, figura, tabelas e comparação reutilizáveis.
│   │   ├── feedback/            Estados de erro.
│   │   └── layout/              Cabeçalho e navegação.
│   └── lib/                    Cliente HTTP, formatação e observação de rolagem.
├── vendor/                     Chart.js local e licença.
├── painel.css                  Estilos do painel.
└── vite.config.js              Compilação para frontend/dist/.
backend/
├── app.py                      Servidor HTTP, páginas de curso e API.
├── services/
│   ├── data/                   Leitura, normalização e consistência.
│   ├── domain/                 Cursos e matrizes curriculares.
│   ├── analytics/              Métricas, gráficos e comparações.
│   ├── dashboard/              Recortes e respostas da API.
│   └── presentation/           Exportação HTML estática.
└── tests/                      Testes de dados, unitários e de integração.
data/                           Catálogo de gráficos e arquivos por semestre.
docs/                           Relatórios e documentação complementar.
Dockerfile / compose.yaml       Imagem e execução do painel em Docker.
```

## API HTTP

A API versionada usa `/api/v1` na porta definida por `API_PORT`, com padrão 8001. A API permite requisições do navegador originadas em `http://localhost` na porta definida por `FRONTEND_PORT`. Todos os recursos abaixo aceitam `GET` e `HEAD`. As respostas usam JSON em UTF-8, com suporte a gzip e `Cache-Control: no-store`. Em `HEAD` são enviados os cabeçalhos da resposta, sem o corpo.

### Rotas e parâmetros

| Rota | Parâmetros de consulta | Campos principais em `data` |
| --- | --- | --- |
| `/api/v1/painel/{grupo}` | `recorte`, `referencia` e `semestre` no modo `compare` | `group`, `scope`, `scopes`, `summary`, `periodBreakdown`, `availableSemesters`, `sections`, `disciplines`, `source`, `quality`, `generatedAt`, `currentPeriod`, `baselinePeriod`, `comparedPeriod` |
| `/api/v1/painel/{grupo}/secoes/{secao}` | Mesmo recorte e par da página, com `revisao` obrigatória | `sections`, `statisticalSummary` quando aplicável, `description` quando disponível |
| `/api/v1/painel/{grupo}/disciplinas/{codigo}` | Mesmo recorte e par da página, com `revisao` obrigatória | `code`, `name`, `summary`, `offeredSemesters`, `sections` |
| `/api/v1/graficos` | Nenhum | Catálogo de `data/graficos.json` |

- `grupo` aceita `cct`, `mc`, `cc`, `em`, `eci` e `es`.
- `recorte` aceita `accumulated` (padrão), `latest` e `compare`. `historical` e `current` continuam disponíveis na API. Em `compare`, envie `referencia` e `semestre` juntos e use dois períodos distintos com oferta no grupo. Ao omitir ambos, a API seleciona os dois últimos semestres disponíveis.
- `secao` aceita `evolucao`, `horarios`, `distribuicao`, `rankings` e `estatisticas`. A seção `comparacao` pertence ao CCT e `curso` às páginas de curso. Use os IDs em `data.sections` da página.
- `codigo` é um código em maiúsculas presente na lista `data.disciplines` da página, como `MC0002`.
- `revisao` recebe `meta.revision` devolvida pela consulta da página. O servidor prepara e mantém em memória a revisão mais recente, calculada sobre a base e o catálogo. Ao receber HTTP 409, consulte a página novamente para obter a revisão atual.

### Respostas e erros

O envelope é `{"data": {...}, "meta": {"version": 1, "revision": "..."}, "error": null}`. A rota de catálogo retorna `revision: null`. Em erros, `data` e `revision` são nulos e `error` contém `code` e `message`.

| HTTP | `error.code` | Significado |
| --- | --- | --- |
| 200 | — | Consulta concluída, inclusive recortes válidos sem turmas |
| 400 | `invalid_query` | Parâmetro inválido ou repetido, par de semestres inválido ou revisão ausente na consulta de gráficos |
| 400 | `invalid_host`, `invalid_target`, `unexpected_body` | Endereço local incorreto, alvo inválido ou corpo em uma consulta |
| 403 | `origin_not_allowed` | Origem de navegador diferente do painel local |
| 404 | `not_found` | Rota, grupo, seção ou disciplina inexistente no grupo |
| 405 | `method_not_allowed` | Método diferente de GET ou HEAD |
| 409 | `revision_changed` | A revisão solicitada não é a revisão em memória |
| 503 | `data_unavailable` | Falha ao ler ou processar a base ou o catálogo |
| 503 | `server_busy` | Limite de consultas simultâneas. A resposta inclui `Retry-After`. |

Na resposta de página, `summary.selected` tem `n` (turmas), `c` (vagas), `m` (matrículas), `rate` (fração ocupada), `free` (vagas não preenchidas) e `extra` (matrículas excedentes), além de contagens por faixa. `source` identifica os arquivos e `quality.consistency` detalha todas as turmas sinalizadas na base. Nas páginas de curso, `data.consistency` traz os casos da matriz do curso. Cada registro da matriz é contado uma vez, mesmo que apareça em vários casos.

Nas páginas de curso, `scope.periods` lista os semestres selecionados. `periodBreakdown` traz os totais por ano e por semestre do recorte. Nos modos de comparação, `availableSemesters` lista as opções do grupo e `baselinePeriod` e `comparedPeriod` identificam o par ativo.

Nas respostas de gráficos, cada item em `sections[].plots` tem `id`, `title`, `description`, `columns`, `rows` e `spec` (tipo e eixos). Os valores em `rows` seguem a ordem de `columns`. As comparações contêm `baselinePeriod`, `currentPeriod`, `rows` e, quando disponível, `baselinePlot`. Uma proporção como `0.54` representa 54%. Medidas indefinidas são `null`.

No gráfico de obrigatórias, `curriculumOptions` lista os PPCs e suas fontes. `curriculumAlternatives` contém os gráficos das versões anteriores, indexados pelo ID do PPC. Em cada versão, `spec.yOrder` define a ordem das disciplinas e `spec.yGroups` indica o semestre curricular de cada linha.

### Segurança do acesso local

O servidor valida o cabeçalho `Host` e autoriza no navegador apenas a origem exata do frontend em `localhost`. Clientes HTTP diretos podem consultar a API sem enviar `Origin`. Os limites de endereço, parâmetros e conexões são aplicados antes dos cálculos. A interface usa uma política de segurança de conteúdo (CSP) e renderiza os dados recebidos como texto nos componentes Svelte. O servidor HTTP da biblioteca padrão é usado para execução local. [Documentação do servidor HTTP do Python](https://docs.python.org/3/library/http.server.html)

### Fluxo assíncrono

1. O Svelte consulta a rota de página ao abrir um curso ou alterar o recorte. A resposta traz os indicadores, a revisão, os IDs das seções e a lista de disciplinas.
2. Ao se aproximar da área visível, cada seção solicita seus gráficos com o mesmo recorte e par de semestres da página, além da `revisao`. Cada resposta é renderizada de forma independente.
3. A busca de cadeiras usa a lista da página. A consulta de gráficos é feita para o código selecionado quando a área de cadeiras se torna visível ou recebe foco.
4. Ao trocar de recorte ou de disciplina, o cliente cancela as requisições que ficaram obsoletas. Falhas são exibidas junto ao conteúdo afetado, com opção de repetir a consulta. Uma revisão vencida oferece atualizar os dados.

### Exemplo

Exemplo em PowerShell para consultar a página, a evolução e uma disciplina:

```powershell
$port = if ($env:API_PORT) { $env:API_PORT } else { '8001' }
$base = "http://localhost:${port}/api/v1/painel/mc"
$query = 'recorte=compare&referencia=2025.2&semestre=2026.2'
$page = Invoke-RestMethod "${base}?$query"
$revision = $page.meta.revision
Invoke-RestMethod "${base}/secoes/evolucao?${query}&revisao=$revision"
Invoke-RestMethod "${base}/disciplinas/MC0005?${query}&revisao=$revision"
```

### Rotas anteriores

`GET /api/painel` entrega a resposta completa dos grupos nos recortes acumulado, histórico e oferta aberta. Use a API v1 para escolher um par de semestres. `GET /api/graficos` devolve o catálogo diretamente. Essas rotas mantêm o formato anterior, incluindo o campo `erro` na resposta 503 de `/api/painel`.

## Testes e exportação

Execute a suíte completa:

```sh
python -m unittest discover -s backend/tests -t backend -v
```

Os testes verificam a integridade dos registros migrados, os totais por recorte e grupo, a classificação curricular, o tratamento de duplicatas, as fórmulas estatísticas e as comparações. Há regressões para ocupações constantes, bases iguais a zero, limiares próximos e categorias ausentes.

Para gerar o HTML estático do acumulado:

```sh
cd backend
python -m services.presentation.export --sem-abrir
```

A exportação mantém gráficos gerais e áreas de curso. A navegação por curso, a seleção de recorte e a busca por cadeira estão disponíveis no painel web. A saída padrão é `ufca-cct-painel.html`.

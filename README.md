# Painel de oferta de disciplinas do CCT da UFCA

Aplicação local para explorar vagas, matrículas, ocupação e distribuição das turmas do CCT. Python calcula os indicadores a partir dos arquivos por semestre. O frontend usa Svelte 5 e a cópia local do Chart.js.

## Executar

Requer Python 3.12 ou superior e Node.js 20.19+ na série 20 ou 22.12+. Na raiz do projeto:

```sh
npm --prefix frontend ci
npm --prefix frontend run build
python backend/app.py
```

O Vite compila o frontend em `frontend/dist/`. O servidor Python entrega a interface e a API no mesmo endereço. Durante alterações no frontend, mantenha `npm --prefix frontend run dev` em outro terminal para recompilar ao salvar.

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

- **Acumulado · 2022.1 a 2026.2** é a opção inicial. Inclui consolidadas de 2022.1 até 2026.1 e abertas de 2026.2. A base não tem registros de 2022.2.
- **Histórico consolidado** reúne as turmas consolidadas anteriores a 2026.2.
- **2026.2 · oferta aberta** apresenta somente as turmas abertas desse semestre.

Cada curso usa os semestres em que há pelo menos uma turma elegível de sua matriz no recorte selecionado. Na base incluída, Engenharia de Software tem oferta em 2025.1, 2025.2, 2026.1 e 2026.2. Na análise de uma cadeira, uma lacuna indica que a cadeira ficou sem oferta naquele semestre do curso.

O recorte é preservado ao navegar entre cursos e pode ser compartilhado na URL, como em `/cursos/mc?recorte=historical`. Para compartilhar uma seleção de cadeira, use `disciplina`, por exemplo `/cursos/mc?disciplina=MC0002#cadeiras-individual`. O asterisco identifica 2026.2 aberto nas séries que o usam. As matrículas e ocupações desse semestre ainda podem mudar.

As tabelas de diferença comparam **2026.2 com o último semestre consolidado disponível**, 2026.1 na base incluída. Contagens apresentam diferenças absolutas e relativas. Proporções apresentam também pontos percentuais. Bases iguais a zero deixam a variação relativa indefinida. Ausência de categoria não vira valor zero. Turmas e pontos de dispersão de semestres distintos não são pareados artificialmente. Grupos de composição variável como Outras capacidades ficam fora das diferenças.

## Dados por semestre

A fonte padrão é a pasta `data/ufca/`:

```text
data/
├── graficos.json
└── ufca/
    ├── README.md
    ├── 2022.1.json
    ├── 2023.1.json
    ├── 2023.2.json
    ├── 2024.1.json
    ├── 2024.2.json
    ├── 2025.1.json
    ├── 2025.2.json
    ├── 2026.1.json
    └── 2026.2.json
```

A coleção contém **1.555 registros**. Os 165 registros de 2022.1 vêm da listagem do SIGAA fornecida no anexo. Desse semestre, 162 turmas entram nos indicadores, duas foram sinalizadas por possível oferta conjunta e uma está interrompida. Os 1.390 registros dos outros semestres preservam os campos e a ordem originais. 2026.2 contém a oferta aberta.

O carregador lê os arquivos em ordem de semestre e exige que o campo `periodo` de cada registro coincida com o nome do arquivo. Nomes de semestre inválidos, períodos conflitantes, fontes vazias ou JSON malformado produzem uma mensagem de erro. Documentos como o README são ignorados.

Cada registro contém `periodo`, `codigo`, `disciplina`, `turma`, `docentes`, `tipo`, `modalidade`, `situacao`, `horario`, `local`, `matriculas` e `capacidade`; os campos de proveniência `origem` e `linha` também são preservados.

Textos, códigos, números e horários são normalizados antes dos cálculos. Duplicatas exatas com identidade confirmada são removidas em memória; conflitos são preservados e informados. Entram nos gráficos as turmas presenciais com capacidade positiva e situação compatível com o recorte. EAD e registros de outras situações permanecem nos arquivos, mas ficam fora desses indicadores.

Na base incluída, o acumulado do CCT contém **1.512 turmas, 60.855 vagas e 33.045 matrículas**, com **54,3% de ocupação**. Os números somam nove semestres, com as matrículas contadas por registro de turma e as vagas por oferta.

O botão **Atualizar dados**, na seção de qualidade, relê a base e o catálogo. A identificação SHA-256 da fonte considera os nomes e conteúdos dos arquivos. A preparação e os cálculos ocorrem em memória.

## Possíveis ofertas conjuntas e choques de horário

A preparação sinaliza códigos distintos com docentes, horários completos, datas e locais coincidentes, além de sobreposições de horário de um mesmo docente. Esses casos aparecem em **Qualidade e preparação da base** e em `quality.consistency` na API. O relatório da base atual está em [docs/consistencia-turmas.md](docs/consistencia-turmas.md).

São indícios, não duplicatas confirmadas: a capacidade pode representar uma cota por código. Todos os registros envolvidos nos casos sinalizados ficam fora dos indicadores até revisão, incluindo equivalências de local inferidas e sobreposições de docente. Os arquivos originais permanecem intactos; capacidades não são substituídas por estimativas. Equivalências de rótulos de local, como Sala/Bloco, são identificadas como inferidas. Confirmar vínculos e cotas no sistema acadêmico é necessário antes de deduplicar ou criar um identificador de turma conjunta. Os totais representam ofertas por código e não garantem contagem de turmas físicas únicas.

## Configuração e cálculos

Edite `data/graficos.json` para alterar `nome`, `descricao` e `tipo`. O campo `tipos_permitidos` documenta os formatos compatíveis, validados no servidor. Os gráficos gerais de grupo compartilham as entradas originais por `catalogKey`; os quatro rankings gerais e as três comparações entre cursos têm entradas próprias. As chaves `cadeira-*` personalizam as análises individuais. Salve e use Atualizar dados; não é necessário reiniciar o servidor para alterações nos dados ou catálogo.

As matrizes ficam em `backend/services/domain/curricula.py`, e o cadastro dos cursos em `backend/services/domain/courses.py`. Ciência da Computação usa CC002 como referência atual, acrescentando os códigos exclusivos de CC001. O recorte curricular pode diferir da seleção de todos os códigos com um prefixo; os demais códigos continuam acessíveis no grupo CCT.

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
| `/api/v1/painel/{grupo}` | `recorte` | `group`, `scope`, `scopes`, `summary`, `sections`, `disciplines`, `source`, `quality`, `generatedAt`, `currentPeriod`, `baselinePeriod` |
| `/api/v1/painel/{grupo}/secoes/{secao}` | `recorte`, `revisao` obrigatória | `sections`, `statisticalSummary` quando aplicável, `description` quando disponível |
| `/api/v1/painel/{grupo}/disciplinas/{codigo}` | `recorte`, `revisao` obrigatória | `code`, `name`, `summary`, `offeredSemesters`, `sections` |
| `/api/v1/graficos` | Nenhum | Catálogo de `data/graficos.json` |

- `grupo` aceita `cct`, `mc`, `cc`, `em`, `eci` e `es`.
- `recorte` aceita `accumulated` (padrão), `historical` e `current`. Envie o mesmo recorte da página nas consultas dependentes.
- `secao` aceita `evolucao`, `horarios`, `distribuicao`, `rankings` e `estatisticas`. A seção `comparacao` pertence ao CCT e `curso` às páginas de curso. Use os IDs em `data.sections` da página.
- `codigo` é um código em maiúsculas presente na lista `data.disciplines` da página, como `MC0002`.
- `revisao` recebe `meta.revision` devolvida pela consulta da página. O servidor prepara e mantém em memória a revisão mais recente, calculada sobre a base e o catálogo. Ao receber HTTP 409, consulte a página novamente para obter a revisão atual.

### Respostas e erros

O envelope é `{"data": {...}, "meta": {"version": 1, "revision": "..."}, "error": null}`. A rota de catálogo retorna `revision: null`. Em erros, `data` e `revision` são nulos e `error` contém `code` e `message`.

| HTTP | `error.code` | Significado |
| --- | --- | --- |
| 200 | — | Consulta concluída, inclusive recortes válidos sem turmas |
| 400 | `invalid_query` | Parâmetro inválido, repetido ou revisão ausente na consulta de gráficos |
| 400 | `invalid_host`, `invalid_target`, `unexpected_body` | Endereço local incorreto, alvo inválido ou corpo em uma consulta |
| 403 | `origin_not_allowed` | Origem de navegador diferente do painel local |
| 404 | `not_found` | Rota, grupo, seção ou disciplina inexistente no grupo |
| 405 | `method_not_allowed` | Método diferente de GET ou HEAD |
| 409 | `revision_changed` | A revisão solicitada não é a revisão em memória |
| 503 | `data_unavailable` | Falha ao ler ou processar a base ou o catálogo |
| 503 | `server_busy` | Limite de consultas simultâneas. A resposta inclui `Retry-After`. |

Na resposta de página, `summary.selected` tem `n` (turmas), `c` (vagas), `m` (matrículas), `rate` (fração ocupada), `free` (vagas não preenchidas) e `extra` (matrículas excedentes), além de contagens por faixa. `source` identifica os arquivos e `quality.consistency` detalha as turmas sinalizadas.

Nas páginas de curso, `scope.periods` e `scopes[].periods` listam os semestres com turmas elegíveis da matriz no respectivo recorte. Uma lista vazia indica ausência de oferta.

Nas respostas de gráficos, cada item em `sections[].plots` tem `id`, `title`, `description`, `columns`, `rows` e `spec` (tipo e eixos). Os valores em `rows` seguem a ordem de `columns`. As comparações contêm `baselinePeriod`, `currentPeriod`, `rows` e, quando disponível, `baselinePlot`. Uma proporção como `0.54` representa 54%. Medidas indefinidas são `null`.

### Segurança do acesso local

O servidor valida o cabeçalho `Host` e autoriza no navegador apenas a origem exata do frontend em `localhost`. Clientes HTTP diretos podem consultar a API sem enviar `Origin`. Os limites de endereço, parâmetros e conexões são aplicados antes dos cálculos. A interface usa uma política de segurança de conteúdo (CSP) e renderiza os dados recebidos como texto nos componentes Svelte. O servidor HTTP da biblioteca padrão é usado para execução local. [Documentação do servidor HTTP do Python](https://docs.python.org/3/library/http.server.html)

### Fluxo assíncrono

1. O Svelte consulta a rota de página ao abrir um curso ou alterar o recorte. A resposta traz os indicadores, a revisão, os IDs das seções e a lista de disciplinas.
2. Ao se aproximar da área visível, cada seção solicita seus gráficos com o mesmo `recorte` e `revisao`. Cada resposta é renderizada de forma independente.
3. A busca de cadeiras usa a lista da página. A consulta de gráficos é feita para o código selecionado quando a área de cadeiras se torna visível ou recebe foco.
4. Ao trocar de recorte ou de disciplina, o cliente cancela as requisições que ficaram obsoletas. Falhas são exibidas junto ao conteúdo afetado, com opção de repetir a consulta. Uma revisão vencida oferece atualizar os dados.

### Exemplo

Exemplo em PowerShell para consultar a página, a evolução e uma disciplina:

```powershell
$port = if ($env:API_PORT) { $env:API_PORT } else { '8001' }
$base = "http://localhost:${port}/api/v1/painel/mc"
$page = Invoke-RestMethod "${base}?recorte=accumulated"
$revision = $page.meta.revision
Invoke-RestMethod "${base}/secoes/evolucao?recorte=accumulated&revisao=$revision"
Invoke-RestMethod "${base}/disciplinas/MC0002?recorte=accumulated&revisao=$revision"
```

### Rotas anteriores

`GET /api/painel` entrega a resposta completa com todos os recortes e grupos. `GET /api/graficos` devolve o catálogo diretamente. Essas rotas mantêm o formato anterior, incluindo o campo `erro` na resposta 503 de `/api/painel`.

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

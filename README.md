# Painel de oferta de disciplinas do CCT da UFCA

Aplicação local para explorar vagas, matrículas, ocupação e distribuição das turmas do CCT. Os dados são carregados de arquivos separados por semestre. Python calcula os indicadores e o navegador apresenta os gráficos com o Chart.js incluído em `vendor/`.

## Executar

Requer Python 3.12 ou superior. Na raiz do projeto:

```sh
python app.py
```

Abra [o painel](http://127.0.0.1:8000/). Para escolher outra porta:

```sh
python app.py --porta 8001
```

A opção `--dados` aceita uma pasta com arquivos por semestre ou um JSON externo contendo uma lista de turmas:

```sh
python app.py --dados data/ufca
python app.py --dados caminho/para/turmas.json
```

O servidor usa somente a biblioteca padrão do Python e atende em `127.0.0.1`. Encerre com `Ctrl+C`.

## Usar o painel

### Gráficos gerais por grupo

O seletor **Grupo dos gráficos gerais** oferece:

| Grupo | Recorte |
| --- | --- |
| CCT | Todas as turmas elegíveis do centro, contadas diretamente. |
| MC | Matemática Computacional. |
| CC | Ciência da Computação. |
| EM | Engenharia de Materiais. |
| ECI | Engenharia Civil. |
| ES | Engenharia de Software. |

Cada grupo oferece os mesmos **37 gráficos gerais**: evolução por semestre, ocupação, distribuição de turmas, vagas disponíveis, horários e turnos, capacidades, rankings, concentração, associações e estatísticas descritivas. Trocar o grupo atualiza todos esses resultados e a busca por cadeira nessa área.

Os grupos de curso usam os códigos das matrizes de referência, incluindo os códigos compartilhados que nelas aparecem. CAR não é um curso nem uma opção própria no seletor. Uma disciplina CAR pode contribuir para mais de um curso; cada turma contribui apenas uma vez para o total do CCT. Os totais dos cursos, portanto, não devem ser somados para reconstruir o centro.

### Comparação entre cursos

Uma área permanente reúne três gráficos: ocupação, vagas e matrículas, e quantidade de turmas por curso. Eles usam o mesmo recorte temporal, independentemente do grupo selecionado na área geral.

### Análises específicas por curso

Os cinco cursos mantêm suas áreas próprias com **16 gráficos específicos**: comparação da ocupação do curso com o CCT, obrigatórias e optativas, mapas históricos por disciplina e rankings por código e natureza curricular. Cada área também preserva a busca individual por cadeira, com oito gráficos por seleção.

Os gráficos gerais comuns ficam no seletor, evitando repetir todas as distribuições e estatísticas em cada curso. Os títulos, descrições e formatos permanecem configuráveis no catálogo.

### Recortes temporais

- **Acumulado · 2023.1 a 2026.2** é a opção inicial: inclui consolidadas desde 2023.1 até 2026.1 e abertas de 2026.2.
- **Histórico consolidado** reúne as turmas consolidadas anteriores a 2026.2.
- **2026.2 · oferta aberta** apresenta somente as turmas abertas desse semestre.

A troca de recorte atualiza os grupos, as comparações e as áreas de curso. O asterisco identifica 2026.2 aberto nas séries que o usam. As matrículas e ocupações desse semestre ainda podem mudar.

As tabelas de diferença comparam **2026.2 com o último semestre consolidado disponível**, 2026.1 na base incluída. Não comparam um único semestre com o total de oito semestres. Contagens apresentam diferenças absolutas e relativas; proporções apresentam também pontos percentuais. Bases iguais a zero deixam a variação relativa indefinida. Ausência de categoria não vira valor zero. Turmas e pontos de dispersão de semestres distintos não são pareados artificialmente; grupos de composição variável como Outras capacidades ficam fora das diferenças.

## Dados por semestre

A fonte padrão é a pasta `data/ufca/`:

```text
data/
├── graficos.json
└── ufca/
    ├── README.md
    ├── 2023.1.json
    ├── 2023.2.json
    ├── 2024.1.json
    ├── 2024.2.json
    ├── 2025.1.json
    ├── 2025.2.json
    ├── 2026.1.json
    └── 2026.2.json
```

Os sete arquivos de 2023.1 a 2026.1 organizam o histórico solicitado. O arquivo de 2026.2 preserva a oferta aberta usada no acumulado e nas comparações. Os **1.390 registros originais**, seus campos e sua ordem por semestre foram mantidos na divisão; não há cópia monolítica da base.

O carregador lê os arquivos em ordem de semestre e exige que o campo `periodo` de cada registro coincida com o nome do arquivo. Nomes de semestre inválidos, períodos conflitantes, fontes vazias ou JSON malformado produzem uma mensagem de erro. Documentos como o README são ignorados.

Cada registro contém `periodo`, `codigo`, `disciplina`, `turma`, `docentes`, `tipo`, `modalidade`, `situacao`, `horario`, `local`, `matriculas` e `capacidade`; os campos de proveniência `origem` e `linha` também são preservados.

Textos, códigos, números e horários são normalizados antes dos cálculos. Duplicatas exatas com identidade confirmada são removidas em memória; conflitos são preservados e informados. Entram nos gráficos as turmas presenciais com capacidade positiva e situação compatível com o recorte. EAD e registros de outras situações permanecem nos arquivos, mas ficam fora desses indicadores.

Na base incluída, o acumulado do CCT contém **1.350 turmas, 54.478 vagas e 29.421 matrículas**, com **54,0% de ocupação**. Os números somam oito semestres; não representam estudantes únicos nem vagas simultâneas.

O botão **Atualizar dados** relê os arquivos e recalcula a resposta em memória. A identificação SHA-256 considera os nomes e conteúdos dos arquivos, permitindo indicar se a fonte mudou desde a última consulta na página. Não são gerados arquivos de resultados durante esse processamento.

## Possíveis ofertas conjuntas e choques de horário

A preparação sinaliza códigos distintos com docentes, horários completos, datas e locais coincidentes, além de sobreposições de horário de um mesmo docente. Esses casos aparecem em **Qualidade e preparação da base** e em `quality.consistency` na API. O relatório da base atual está em [docs/consistencia-turmas.md](docs/consistencia-turmas.md).

São indícios, não duplicatas confirmadas: a capacidade pode representar uma cota por código. Todos os registros envolvidos nos casos sinalizados ficam fora dos indicadores até revisão, incluindo equivalências de local inferidas e sobreposições de docente. Os arquivos originais permanecem intactos; capacidades não são substituídas por estimativas. Equivalências de rótulos de local, como Sala/Bloco, são identificadas como inferidas. Confirmar vínculos e cotas no sistema acadêmico é necessário antes de deduplicar ou criar um identificador de turma conjunta. Os totais representam ofertas por código e não garantem contagem de turmas físicas únicas.

## Configuração e cálculos

Edite `data/graficos.json` para alterar `nome`, `descricao` e `tipo`. O campo `tipos_permitidos` documenta os formatos compatíveis, validados no servidor. Os gráficos gerais de grupo compartilham as entradas originais por `catalogKey`; os quatro rankings gerais e as três comparações entre cursos têm entradas próprias. As chaves `cadeira-*` personalizam as análises individuais. Salve e use Atualizar dados; não é necessário reiniciar o servidor para alterações nos dados ou catálogo.

As matrizes ficam em `services/domain/curricula.py`, e o cadastro dos cursos em `services/domain/courses.py`. Ciência da Computação usa CC002 como referência atual, acrescentando os códigos exclusivos de CC001. O recorte curricular pode diferir da seleção de todos os códigos com um prefixo; os demais códigos continuam acessíveis no grupo CCT.

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
app.py                          Servidor HTTP e página inicial.
painel.js / painel.css          Interface, seletores e renderização.
services/
├── config.py                   Caminhos e configurações compartilhadas.
├── data/
│   ├── loader.py               Leitura dos semestres e identificação da fonte.
│   └── preprocessing.py        Validação, normalização e preparação.
├── domain/
│   ├── courses.py              Cadastro dos cursos e composição de matrizes.
│   └── curricula.py            Códigos e naturezas curriculares.
├── analytics/
│   ├── metrics.py              Agregações, rankings e especificações de gráficos.
│   ├── statistics.py           Estatísticas descritivas e associações.
│   ├── disciplines.py          Indicadores individuais por código.
│   └── comparison.py           Pareamento e diferenças entre semestres.
├── dashboard/
│   ├── catalog.py              Aplicação do catálogo editável.
│   ├── scopes.py               Textos e séries conforme o recorte temporal.
│   ├── periods.py              Montagem dos recortes e áreas de curso.
│   ├── groups.py               Grupos agregados e comparações entre cursos.
│   └── payload.py              Resposta final da aplicação.
└── presentation/
    └── export.py               Exportação HTML estática e recursos visuais.
tests/
├── data/                       Carregamento, integridade e divisão por semestre.
├── unit/                       Fórmulas, normalização, disciplinas e comparações.
└── integration/                Recortes, cursos, grupos e resposta do painel.
```

`GET /api/painel` entrega os dados calculados; `GET /api/graficos` disponibiliza o catálogo. Erros de leitura ou processamento retornam HTTP 503. Recursos temporários de conferência não fazem parte da aplicação.

## Testes e exportação

Execute a suíte completa:

```sh
python -m unittest discover -s tests -v
```

Os testes verificam a integridade dos registros migrados, os totais por recorte e grupo, a classificação curricular, o tratamento de duplicatas, as fórmulas estatísticas e as comparações. Há regressões para ocupações constantes, bases iguais a zero, limiares próximos e categorias ausentes.

Para gerar o HTML estático do acumulado:

```sh
python -m services.presentation.export --sem-abrir
```

A exportação mantém gráficos gerais e áreas de curso. A seleção interativa de grupos e cadeiras está disponível no painel web. A saída padrão é `ufca-cct-painel.html`.

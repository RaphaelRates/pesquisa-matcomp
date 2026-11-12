# Possíveis turmas conjuntas e inconsistências de horário

Verificação da base em 12/11/2026. Esta é uma lista de indícios para revisão cadastral, não uma confirmação de duplicidade.

Fonte: `data/ufca/` · 1555 registros · SHA-256 da coleção: `f8cf50dae9492c48c4e4ca1cd9669b2d28e87c56776b7b197210f8a1cda76a72`.

## Resultado

- 9 grupos com códigos diferentes, conjunto de docentes e faixas completas de horário coincidentes: seis com local normalizado igual e três com equivalência Sala/Bloco inferida.
- 8 pares adicionais com docente em comum e sobreposição parcial ou total de horário, sem coincidência completa de todos os metadados.
- Entre os nove grupos, apenas CC0017/MC0016 tem também o mesmo nome de disciplina. Os outros oito exigem distinguir oferta conjunta de possível erro de horário, local ou associação de docente.
- Política atual: os 33 registros envolvidos ficam fora dos indicadores até revisão, incluindo dois de 2022.1. Os arquivos originais e seus valores permanecem intactos.

## Critérios e limites

A comparação exige o mesmo semestre e modalidade presencial. As faixas consideram dia, início e fim da aula — coincidir apenas nos dias da semana não basta. Datas disjuntas não geram sobreposição. Docentes são normalizados por nome, sem confundir carga horária com identidade. Rótulos Sala/Bloco só produzem equivalência inferida, destacada separadamente. Metadados ausentes não são usados como uma identidade confiável; a ausência de datas é indicada no caso quando há coincidência dos demais campos.

As informações não revelam se a capacidade é uma cota por código, uma capacidade compartilhada, nem se os estudantes se repetem. Não há base para fundir registros ou substituir a ocupação de MC pela ocupação agregada de outro código. Por solicitação do responsável, os registros sinalizados são excluídos integralmente dos cálculos enquanto aguardam revisão. O CCT soma ofertas por código; essa contagem pode exceder a de turmas físicas.

## Casos para revisão

### 2022.1 — ECI0115 / EM0028

Coincidência entre disciplinas diferentes. Mesmo conjunto de docentes e mesmas faixas completas de horário; mesmas datas cadastradas; mesmo local normalizado.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha no anexo |
| --- | --- | ---: | --- | ---: |
| ECI0115 — INSTALAÇÕES ELÉTRICAS | Turma 01 | 18/50 | Sala: E03 | 328 |
| EM0028 — ELETROTÉCNICA | Turma 01 | 10/30 | Sala: E03 | 193 |

Arquivo [data/ufca/2022.1.json](../data/ufca/2022.1.json).

- **ECI0115** — GABRIELA LINHARES LANDIM (32h). Horário SEG 08:00-10:00, QUA 08:00-10:00, (15/08/2022 - 17/12/2022).
- **EM0028** — GABRIELA LINHARES LANDIM (32h). Horário SEG 08:00-10:00, QUA 08:00-10:00, (15/08/2022 - 17/12/2022).

Confirmar no SIGAA se há turma conjunta, cotas separadas ou erro de cadastro. Não deduplicar automaticamente.

### 1. 2023.1 — ECI0115 / EM0028

coincidência entre disciplinas diferentes

Mesmo conjunto de docentes e mesmas faixas completas de horário; mesmas datas cadastradas; mesmo local normalizado.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0115 — INSTALAÇÕES ELÉTRICAS | Turma 01 | 35/50 | Sala:E04 | 325 |
| EM0028 — ELETROTÉCNICA | Turma 01 | 23/40 | Sala:E04 | 189 |

Arquivo: [data/ufca/2023.1.json](../data/ufca/2023.1.json).

- **ECI0115** — GABRIELA LINHARES LANDIM (32h); horário: SEG 08:00-10:00; QUA 08:00-10:00; (17/07/2023 - 04/11/2023).
- **EM0028** — GABRIELA LINHARES LANDIM (32h); horário: SEG 08:00-10:00; QUA 08:00-10:00; (17/07/2023 - 04/11/2023).

Confirmar no SIGAA se há turma conjunta, cotas separadas ou erro de cadastro. Não deduplicar automaticamente.

### 2. 2023.2 — CC0017 / MC0016

possível turma conjunta (mesmo nome)

Mesmo conjunto de docentes e mesmas faixas completas de horário; mesmas datas cadastradas; mesmo local normalizado.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| CC0017 — ALGORITMOS EM GRAFOS | Turma 01 | 36/60 | Sala:A24-s | 43 |
| MC0016 — ALGORITMOS EM GRAFOS | Turma 01 | 3/50 | Sala:A24-s | 47 |

Arquivo: [data/ufca/2023.2.json](../data/ufca/2023.2.json).

- **CC0017** — CARLOS VINICIUS GOMES COSTA LIMA (32h); horário: TER 10:00-12:00; QUI 10:00-12:00; (27/11/2023 - 13/04/2024).
- **MC0016** — CARLOS VINICIUS GOMES COSTA LIMA (32h); horário: TER 10:00-12:00; QUI 10:00-12:00; (27/11/2023 - 13/04/2024).

Confirmar no SIGAA se há turma conjunta, cotas separadas ou erro de cadastro. Não deduplicar automaticamente.

### 3. 2023.2 — ECI0037 / ECI0094

sobreposição de horário de docente

Docente em comum, datas sobrepostas e ao menos uma faixa de aula simultânea.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0037 — MECANICA DOS SOLOS II | Turma 01 | 38/50 | sala:M04 | 436 |
| ECI0094 — ENSAIOS DE SOLOS E INSTRUMENTAÇÃO | Turma 01 | 17/50 | Laboratorio de solo - Bloc:M | 215 |

Arquivo: [data/ufca/2023.2.json](../data/ufca/2023.2.json).

- **ECI0037** — ANA PATRICIA NUNES BANDEIRA (64h); horário: TER 14:00-16:00; QUI 14:00-16:00; (27/11/2023 - 13/04/2024).
- **ECI0094** — ANA PATRICIA NUNES BANDEIRA (32h) e JOAO BARBOSA DE SOUZA NETO (32h); horário: QUI 14:00-18:00; (27/11/2023 - 13/04/2024).

Revisar horário, alternância de aulas e eventual oferta conjunta; coincidência não prova duplicata.

### 4. 2023.2 — ECI0044 / ECI0126

sobreposição de horário de docente

Docente em comum, datas sobrepostas e ao menos uma faixa de aula simultânea.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0044 — HIDROLOGIA | Turma 01 | 29/50 | Sala:K03 | 325 |
| ECI0126 — GERENCIAMENTO DE RESÍDUOS SÓLIDOS URBANOS | Turma 01 | 24/40 | Sala: Laboratório de Hidráulica- Bloco:D | 314 |

Arquivo: [data/ufca/2023.2.json](../data/ufca/2023.2.json).

- **ECI0044** — AMANDA BEZERRA DE SOUSA PINO (64h); horário: SEG 08:00-10:00; QUA 08:00-10:00; (27/11/2023 - 13/04/2024).
- **ECI0126** — AMANDA BEZERRA DE SOUSA PINO (32h) e MARIA GORETHE DE SOUSA LIMA BRITO (32h); horário: QUA 08:00-10:00; QUI 08:00-10:00; (27/11/2023 - 13/04/2024).

Revisar horário, alternância de aulas e eventual oferta conjunta; coincidência não prova duplicata.

### 5. 2023.2 — ECI0105 / ECI0115

sobreposição de horário de docente

Docente em comum, datas sobrepostas e ao menos uma faixa de aula simultânea.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0105 — MATERIAIS DE CONSTRUÇÃO CIVIL II | Turma 01A | 19/50 | Sala:E20-s | 410 |
| ECI0115 — INSTALAÇÕES ELÉTRICAS | Turma 01 | 45/50 | sala:M03 | 336 |

Arquivo: [data/ufca/2023.2.json](../data/ufca/2023.2.json).

- **ECI0105** — AERSON MOREIRA BARRETO (32h) e SOFIA LEAO CARVALHO (32h); horário: SEG 08:00-12:00; (27/11/2023 - 13/04/2024).
- **ECI0115** — SOFIA LEAO CARVALHO (64h); horário: SEG 08:00-10:00; QUA 08:00-10:00; (27/11/2023 - 13/04/2024).

Revisar horário, alternância de aulas e eventual oferta conjunta; coincidência não prova duplicata.

### 6. 2025.1 — ECI0028 / EM0089

coincidência entre disciplinas diferentes

Mesmo conjunto de docentes e mesmas faixas completas de horário; mesmas datas cadastradas; mesmo local normalizado.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0028 — RESISTENCIA DOS MATERIAIS I | Turma 01 | 14/50 | SALA E19s | 594 |
| EM0089 — RESISTÊNCIA DOS MATERIAIS | Turma 01 | 9/25 | Sala E19s | 590 |

Arquivo: [data/ufca/2025.1.json](../data/ufca/2025.1.json).

- **ECI0028** — FRANCISCO ALEX CORREIA MONTEIRO (32h); horário: QUA 10:00-12:00; SEX 10:00-12:00; (09/06/2025 - 18/10/2025).
- **EM0089** — FRANCISCO ALEX CORREIA MONTEIRO (32h); horário: QUA 10:00-12:00; SEX 10:00-12:00; (09/06/2025 - 18/10/2025).

Confirmar no SIGAA se há turma conjunta, cotas separadas ou erro de cadastro. Não deduplicar automaticamente.

### 7. 2025.1 — ECI0115 / EM0028

coincidência entre disciplinas diferentes

Mesmo conjunto de docentes e mesmas faixas completas de horário; mesmas datas cadastradas; mesmo local normalizado.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0115 — INSTALAÇÕES ELÉTRICAS | Turma 01 | 9/25 | SALA i103 | 340 |
| EM0028 — ELETROTÉCNICA | Turma 01 | 11/30 | SALA i103 | 181 |

Arquivo: [data/ufca/2025.1.json](../data/ufca/2025.1.json).

- **ECI0115** — SOFIA LEAO CARVALHO (32h); horário: SEG 08:00-10:00; QUA 08:00-10:00; (09/06/2025 - 18/10/2025).
- **EM0028** — SOFIA LEAO CARVALHO (32h); horário: SEG 08:00-10:00; QUA 08:00-10:00; (09/06/2025 - 18/10/2025).

Confirmar no SIGAA se há turma conjunta, cotas separadas ou erro de cadastro. Não deduplicar automaticamente.

### 8. 2025.2 — ECI0028 / EM0089

coincidência entre disciplinas diferentes · **local inferido**

Mesmo conjunto de docentes e mesmas faixas completas de horário; mesmas datas cadastradas; equivalência de rótulos de local inferida (Sala/Bloco).

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0028 — RESISTENCIA DOS MATERIAIS I | Turma 01 | 18/30 | SALA K102 | 576 |
| EM0089 — RESISTÊNCIA DOS MATERIAIS | Turma 01 | 6/25 | K102 | 572 |

Arquivo: [data/ufca/2025.2.json](../data/ufca/2025.2.json).

- **ECI0028** — FRANCISCO ALEX CORREIA MONTEIRO (32h); horário: QUA 10:00-12:00; SEX 10:00-12:00; (03/11/2025 - 31/03/2026).
- **EM0089** — FRANCISCO ALEX CORREIA MONTEIRO (32h); horário: QUA 10:00-12:00; SEX 10:00-12:00; (03/11/2025 - 31/03/2026).

Confirmar no SIGAA se há turma conjunta, cotas separadas ou erro de cadastro. Não deduplicar automaticamente.

### 9. 2025.2 — ECI0115 / EM0028

coincidência entre disciplinas diferentes · **local inferido**

Mesmo conjunto de docentes e mesmas faixas completas de horário; mesmas datas cadastradas; equivalência de rótulos de local inferida (Sala/Bloco).

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0115 — INSTALAÇÕES ELÉTRICAS | Turma 01 | 27/50 | SALA K 101 | 345 |
| EM0028 — ELETROTÉCNICA | Turma 01 | 6/30 | Bloco K 101 | 204 |

Arquivo: [data/ufca/2025.2.json](../data/ufca/2025.2.json).

- **ECI0115** — SOFIA LEAO CARVALHO (32h); horário: SEG 08:00-10:00; QUA 08:00-10:00; (03/11/2025 - 31/03/2026).
- **EM0028** — SOFIA LEAO CARVALHO (32h); horário: SEG 08:00-10:00; QUA 08:00-10:00; (03/11/2025 - 31/03/2026).

Confirmar no SIGAA se há turma conjunta, cotas separadas ou erro de cadastro. Não deduplicar automaticamente.

### 10. 2026.1 — ECI0103 / EM0089

coincidência entre disciplinas diferentes · **local inferido**

Mesmo conjunto de docentes e mesmas faixas completas de horário; mesmas datas cadastradas; equivalência de rótulos de local inferida (Sala/Bloco).

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0103 — MECÂNICA DAS ESTRUTURAS | Turma 02 | 43/50 | SALA A24s | 446 |
| EM0089 — RESISTÊNCIA DOS MATERIAIS | Turma 01 | 6/25 | A24S | 576 |

Arquivo: [data/ufca/2026.1.json](../data/ufca/2026.1.json).

- **ECI0103** — FRANCISCO ALEX CORREIA MONTEIRO (32h); horário: TER 16:00-18:00; QUI 16:00-18:00; (22/04/2026 - 31/08/2026).
- **EM0089** — FRANCISCO ALEX CORREIA MONTEIRO (32h); horário: TER 16:00-18:00; QUI 16:00-18:00; (22/04/2026 - 31/08/2026).

Confirmar no SIGAA se há turma conjunta, cotas separadas ou erro de cadastro. Não deduplicar automaticamente.

### 11. 2026.1 — ECI0079 / ECI0126

sobreposição de horário de docente

Docente em comum, datas sobrepostas e ao menos uma faixa de aula simultânea.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0079 — INTRODUÇÃO À ENGENHARIA CIVIL | Turma 01 | 56/60 | SALA A23-S | 356 |
| ECI0126 — GERENCIAMENTO DE RESÍDUOS SÓLIDOS URBANOS | Turma 01 | 0/30 | SALA K102 | 313 |

Arquivo: [data/ufca/2026.1.json](../data/ufca/2026.1.json).

- **ECI0079** — AMANDA BEZERRA DE SOUSA PINO (32h); horário: QUA 10:00-12:00; (22/04/2026 - 31/08/2026).
- **ECI0126** — AMANDA BEZERRA DE SOUSA PINO (32h) e MARIA GORETHE DE SOUSA LIMA BRITO (32h); horário: SEG 10:00-12:00; QUA 10:00-12:00; (20/04/2026 - 29/08/2026).

Revisar horário, alternância de aulas e eventual oferta conjunta; coincidência não prova duplicata.

### 12. 2026.1 — ECI0100 / ECI0106

sobreposição de horário de docente

Docente em comum, datas sobrepostas e ao menos uma faixa de aula simultânea.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0100 — TOPOGRAFIA | Turma 01A | 24/25 | SEG. SALA I105- TER LAB. A02 | 631 |
| ECI0106 — ANÁLISE E PLANEJAMENTO DE SISTEMA DE TRANSPORTES | Turma 01 | 31/50 | SALA K05 | 52 |

Arquivo: [data/ufca/2026.1.json](../data/ufca/2026.1.json).

- **ECI0100** — MARCOS JOSE TIMBO LIMA GOMES (16h) e ARY FERREIRA DA SILVA (32h); horário: SEG 08:00-10:00; TER 08:00-10:00; (22/04/2026 - 31/08/2026).
- **ECI0106** — ARY FERREIRA DA SILVA (64h); horário: SEG 08:00-10:00; QUA 08:00-10:00; (20/04/2026 - 29/08/2026).

Revisar horário, alternância de aulas e eventual oferta conjunta; coincidência não prova duplicata.

### 13. 2026.1 — ECI0100 / ECI0106

sobreposição de horário de docente

Docente em comum, datas sobrepostas e ao menos uma faixa de aula simultânea.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0100 — TOPOGRAFIA | Turma 03A | 18/25 | SEG. SALA I105- QUIN LAB. A02 | 634 |
| ECI0106 — ANÁLISE E PLANEJAMENTO DE SISTEMA DE TRANSPORTES | Turma 01 | 31/50 | SALA K05 | 52 |

Arquivo: [data/ufca/2026.1.json](../data/ufca/2026.1.json).

- **ECI0100** — MARCOS JOSE TIMBO LIMA GOMES (16h) e ARY FERREIRA DA SILVA (32h); horário: SEG 08:00-10:00; QUI 08:00-10:00; (22/04/2026 - 31/08/2026).
- **ECI0106** — ARY FERREIRA DA SILVA (64h); horário: SEG 08:00-10:00; QUA 08:00-10:00; (20/04/2026 - 29/08/2026).

Revisar horário, alternância de aulas e eventual oferta conjunta; coincidência não prova duplicata.

### 14. 2026.1 — MC0001 / MC0019

sobreposição de horário de docente

Docente em comum, datas sobrepostas e ao menos uma faixa de aula simultânea.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| MC0001 — CÁLCULO I | Turma 02 | 52/53 | SALA E04 | 93 |
| MC0019 — ANÁLISE I | Turma 01 | 22/50 | E01 | 56 |

Arquivo: [data/ufca/2026.1.json](../data/ufca/2026.1.json).

- **MC0001** — FRANCISCO CALVI DA CRUZ JUNIOR (32h) e FRANCISCA DAMIANA VIEIRA (64h); horário: SEG 08:00-10:00; QUA 08:00-10:00; SEX 08:00-10:00; (22/04/2026 - 31/08/2026).
- **MC0019** — FRANCISCO PEREIRA CHAVES (64h) e FRANCISCO CALVI DA CRUZ JUNIOR (32h); horário: SEG 08:00-10:00; QUA 08:00-10:00; SEX 08:00-10:00; (22/04/2026 - 31/08/2026).

Revisar horário, alternância de aulas e eventual oferta conjunta; coincidência não prova duplicata.

### 15. 2026.2 — ECI0103 / EM0089

coincidência entre disciplinas diferentes

Mesmo conjunto de docentes e mesmas faixas completas de horário; mesmas datas cadastradas; mesmo local normalizado.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0103 — MECÂNICA DAS ESTRUTURAS | Turma 01 | 44/50 | SALA A23 S | 415 |
| EM0089 — RESISTÊNCIA DOS MATERIAIS | Turma 01 | 8/25 | SALA A23S | 563 |

Arquivo: [data/ufca/2026.2.json](../data/ufca/2026.2.json).

- **ECI0103** — FRANCISCO ALEX CORREIA MONTEIRO (32h); horário: TER 16:00-18:00; QUI 16:00-18:00; (14/09/2026 - 20/02/2027).
- **EM0089** — FRANCISCO ALEX CORREIA MONTEIRO (32h); horário: TER 16:00-18:00; QUI 16:00-18:00; (14/09/2026 - 20/02/2027).

Confirmar no SIGAA se há turma conjunta, cotas separadas ou erro de cadastro. Não deduplicar automaticamente.

### 16. 2026.2 — ECI0050 / ECI0100

sobreposição de horário de docente

Docente em comum, datas sobrepostas e ao menos uma faixa de aula simultânea.

| Código e disciplina | Turma | Matrículas/vagas | Local | Linha na fonte original |
| --- | --- | ---: | --- | ---: |
| ECI0050 — OPERACAO DE SISTEMAS DE TRANSPORTES | Turma 02 | 19/50 | SALA E03 | 449 |
| ECI0100 — TOPOGRAFIA | Turma 02A | 13/25 | SEX SALA A23-S QUIN-LAB A02 | 635 |

Arquivo: [data/ufca/2026.2.json](../data/ufca/2026.2.json).

- **ECI0050** — ARY FERREIRA DA SILVA (48h); horário: QUI 08:00-11:00; (14/09/2026 - 20/02/2027).
- **ECI0100** — MARCOS JOSE TIMBO LIMA GOMES (32h) e ARY FERREIRA DA SILVA (16h); horário: QUI 08:00-10:00; SEX 08:00-10:00; (14/09/2026 - 20/02/2027).

Revisar horário, alternância de aulas e eventual oferta conjunta; coincidência não prova duplicata.

## Confirmação necessária

Consultar no sistema acadêmico ou com a coordenação: identificador da turma física/conjunta, vínculo entre códigos, capacidade total versus cotas por código e política de contagem das matrículas. Um futuro campo de turma conjunta deve ser preenchido somente com essa evidência, e não inferido automaticamente por nome, docente ou sala.

O painel recebe a lista atualizada em `quality.consistency` a cada carregamento e a mostra em Qualidade e preparação da base. A regra de deduplicação exata continua separada desse alerta.

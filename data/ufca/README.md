# Turmas da UFCA por semestre

Cada arquivo `AAAA.S.json` contém os registros originais daquele semestre, preservando todos os campos e a ordem. Os arquivos não contêm indicadores calculados.

| Semestre | Registros |
| --- | ---: |
| 2019.1 | 159 |
| 2019.2 | 154 |
| 2020.1 | 154 |
| 2020.2 | 144 |
| 2021.1 | 149 |
| 2021.2 | 161 |
| 2022.1 | 165 |
| 2022.2 | 167 |
| 2023.1 | 172 |
| 2023.2 | 176 |
| 2024.1 | 173 |
| 2024.2 | 179 |
| 2025.1 | 175 |
| 2025.2 | 170 |
| 2026.1 | 172 |
| 2026.2 | 173 |
| Total | 2.643 |

A aplicação preserva modalidades, situações e demais campos da fonte e aplica seus filtros em memória. O acumulado reúne os semestres com turmas elegíveis da base e calcula o intervalo de cada curso a partir da sua matriz.

O campo `origem` guarda o identificador do anexo do SIGAA e `linha` aponta para o início da turma no texto colado. A conferência dos 16 anexos encontrou correspondência em todos os registros de turma e seus campos, após desconsiderar diferenças de espaçamento.

Dos 2.643 registros, 2.501 entram no acumulado. A seleção exclui cinco registros a distância, seis turmas com outras situações e [131 ofertas sinalizadas](../../docs/consistencia-turmas.md) para revisão. As contagens por curso também dependem dos códigos comprovados nas matrizes.

| Grupo | Turmas | Vagas | Matrículas | Ocupação |
| --- | ---: | ---: | ---: | ---: |
| CCT | 2.501 | 103.795 | 55.516 | 53,5% |
| Matemática Computacional | 222 | 10.320 | 4.285 | 41,5% |
| Ciência da Computação | 323 | 14.239 | 8.728 | 61,3% |
| Engenharia de Materiais | 931 | 35.384 | 15.114 | 42,7% |
| Engenharia Civil | 1.082 | 46.867 | 28.907 | 61,7% |
| Engenharia de Software | 31 | 1.502 | 1.306 | 87,0% |

Ofertas de códigos sem vínculo curricular confirmado nesta revisão entram no panorama do CCT. Entre elas estão quatro ofertas de MC0030 e MC0040 e treze ofertas de ECI0072, ECI0126 e ECI0130. Códigos compartilhados podem contribuir para mais de uma página de curso.

Em Cálculo I (MC0001), há 18 registros na fonte e 17 turmas no acumulado. Das 17, 14 têm aula das 8h às 10h às segundas, quartas e sextas. Outras duas têm aula das 10h às 12h, e uma, das 14h às 16h, nos mesmos dias. A Turma 02 de 2026.1 fica fora por sobreposição de horário de docente com MC0019. O mapa conta cada turma em cada dia e faixa de uma hora em que aparece.

Ao adicionar um semestre, salve um arquivo `AAAA.1.json` ou `AAAA.2.json` nesta pasta. Use uma lista JSON em UTF-8 com o campo `periodo` de cada turma igual ao semestre no nome do arquivo. Clique em **Atualizar dados** para reler a pasta e recalcular o painel.

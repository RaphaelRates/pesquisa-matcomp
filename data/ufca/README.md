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

Os registros de 2019.1 a 2022.2 seguem a ordem das listagens do SIGAA nos anexos. O campo `origem` guarda o identificador do anexo e `linha` aponta para o início da turma no texto colado.

Ao adicionar um semestre, salve um arquivo `AAAA.1.json` ou `AAAA.2.json` nesta pasta. Use uma lista JSON em UTF-8 com o campo `periodo` de cada turma igual ao semestre no nome do arquivo. Clique em **Atualizar dados** para reler a pasta e recalcular o painel.

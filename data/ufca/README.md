# Turmas da UFCA por semestre

Cada arquivo `AAAA.S.json` contém os registros originais daquele semestre, preservando todos os campos e a ordem. Os arquivos não contêm indicadores calculados.

| Semestre | Registros |
| --- | ---: |
| 2022.1 | 165 |
| 2023.1 | 172 |
| 2023.2 | 176 |
| 2024.1 | 173 |
| 2024.2 | 179 |
| 2025.1 | 175 |
| 2025.2 | 170 |
| 2026.1 | 172 |
| 2026.2 | 173 |
| Total | 1.555 |

2026.2 é mantido em arquivo próprio para a oferta aberta e para o acumulado de 2022.1 a 2026.2. Modalidades, situações e demais campos da fonte são preservados; a aplicação aplica seus filtros em memória.

Os registros de 2022.1 seguem a ordem do anexo. O campo `origem` guarda o identificador do anexo e `linha` aponta para o início da turma no texto colado.

Ao editar ou adicionar um arquivo, mantenha uma lista JSON e o campo `periodo` igual ao semestre do nome. O carregador processa os arquivos em ordem cronológica. A integridade da migração é verificada em [backend/tests/data/test_loader.py](../../backend/tests/data/test_loader.py).

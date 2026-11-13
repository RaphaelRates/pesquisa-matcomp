"""Lê um arquivo de turmas ou uma coleção ordenada de semestres."""

import hashlib
import json
from collections import Counter
from pathlib import Path
import re


SEMESTER = re.compile(r'[1-9][0-9]{3}\.[12]')
SEMESTER_FILE = re.compile(rf'({SEMESTER.pattern})\.json', re.IGNORECASE)
SEMESTER_LIKE_FILE = re.compile(r'^\d{4}[._-].*\.json$', re.IGNORECASE)


def _reject_constant(value):
    raise ValueError(f'{value} não é um valor JSON válido')


def _read_list(path):
    content = path.read_bytes()
    try:
        rows = json.loads(content.decode('utf-8-sig'), parse_constant=_reject_constant)
    except ValueError as error:
        raise ValueError(f'O arquivo {path.name} não contém um JSON UTF-8 válido: {error}') from error
    if not isinstance(rows, list):
        raise ValueError(f'O arquivo {path.name} deve conter uma lista de turmas.')
    return rows, content


def _source(path, rows, files, digest):
    counts = Counter(row['periodo'] for row in rows if isinstance(row, dict)
                     and isinstance(row.get('periodo'), str) and SEMESTER.fullmatch(row['periodo']))
    latest = max(counts, default=None)
    return dict(name=path.name, sha256=digest, files=files, currentPeriod=latest, currentRows=counts[latest])


def load_offers(path):
    """Retorna ``(registros, origem)`` sem normalizar nem descartar registros.

    Diretórios contêm um JSON por semestre, com nomes ``2023.1.json``.
    Os arquivos são lidos em ordem de semestre e os registros de cada arquivo
    conservam sua ordem original. Outros documentos, como README.md e notas,
    são ignorados; nomes que parecem semestres mas são inválidos são rejeitados.
    Um arquivo JSON individual continua aceito para bases externas.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f'A fonte de turmas não foi encontrada: {path}')
    if path.is_file():
        rows, content = _read_list(path)
        digest = hashlib.sha256(content).hexdigest()
        files = [dict(name=path.name, period=None, rows=len(rows), sha256=digest)]
        return rows, _source(path, rows, files, digest)
    if not path.is_dir():
        raise ValueError(f'A fonte deve ser um arquivo JSON ou diretório de semestres: {path}')

    semesters = {}
    for file in path.iterdir():
        if not file.is_file():
            continue
        match = SEMESTER_FILE.fullmatch(file.name)
        if not match:
            if SEMESTER_LIKE_FILE.match(file.name):
                raise ValueError(f'Nome de semestre inválido: {file.name}. Use AAAA.1.json ou AAAA.2.json.')
            continue
        period = match[1]
        if period in semesters:
            raise ValueError(f'Há mais de um arquivo para o semestre {period}.')
        semesters[period] = file
    if not semesters:
        raise ValueError(f'Nenhum arquivo de semestre foi encontrado em {path}.')

    result = []
    files = []
    digest = hashlib.sha256()
    for period, file in sorted(semesters.items()):
        rows, content = _read_list(file)
        for index, row in enumerate(rows, 1):
            if not isinstance(row, dict) or row.get('periodo') != period:
                raise ValueError(f'{file.name}: o registro {index} deve informar o período {period}.')
        # Nomes relativos e conteúdo, sem caminhos absolutos nem datas do sistema.
        digest.update(file.name.encode('utf-8'))
        digest.update(b'\0')
        digest.update(content)
        digest.update(b'\0')
        files.append(dict(name=file.name, period=period, rows=len(rows), sha256=hashlib.sha256(content).hexdigest()))
        result.extend(rows)
    return result, _source(path, result, files, digest.hexdigest())

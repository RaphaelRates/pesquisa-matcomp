"""Sinaliza possíveis turmas conjuntas e choques; nunca funde registros."""

from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
import re
import unicodedata


SLOTS = re.compile(r'\b(SEG|TER|QUA|QUI|SEX|SAB|DOM) (\d{2}):(\d{2})-(\d{2}):(\d{2})')
DATES = re.compile(r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})')


def text(value):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', value or '')
                           if not unicodedata.combining(c)).upper().split())


def teachers(value):
    if not isinstance(value, str) or text(value) in {'', 'A DEFINIR', 'A DEFINIR DOCENTE', 'NAO INFORMADO', 'SEM DOCENTE'}:
        return ()
    names = re.findall(r'([^()]+?)\(\s*\d+(?:[.,]\d+)?\s*H\s*\)', text(value))
    return tuple(sorted({re.sub(r'^\s*(?:E |[,;])\s*', '', name).strip() for name in names})) if names else (text(value),) if value else ()


def location(value, alias=False):
    if not isinstance(value, str):
        return ''
    value = text(value)
    if value in {'', 'A DEFINIR', 'NAO INFORMADO', 'A CADASTRAR', 'SEM LOCAL'}:
        return ''
    if alias:
        value = re.sub(r'^(?:SALA|BLOCO)\s*[:.-]?\s*', '', value)
    return re.sub(r'[^A-Z0-9]', '', value)


def describe(row):
    return {key: row.get(key) for key in ('periodo', 'codigo', 'disciplina', 'turma', 'docentes',
            'horario', 'local', 'situacao', 'matriculas', 'capacidade', 'origem', 'linha')} | {'arquivo': f"{row['periodo']}.json"}


def find_consistency_issues(rows):
    """Evidência cadastral não determina cota, equivalência ou capacidade física."""
    indexed = []
    for i, row in enumerate(rows):
        if row['modalidade'] != 'Presencial':
            continue
        slots = tuple(sorted(set((d, int(sh)*60+int(sm), int(eh)*60+int(em))
                                 for d, sh, sm, eh, em in SLOTS.findall(text(row['horario']))
                                 if int(sh) < 24 and int(eh) <= 24 and int(sm) < 60 and int(em) < 60
                                 and int(sh)*60+int(sm) < int(eh)*60+int(em))))
        dates = []
        for start, end in DATES.findall(row['horario']):
            try:
                start, end = datetime.strptime(start, '%d/%m/%Y').date(), datetime.strptime(end, '%d/%m/%Y').date()
                if start <= end:
                    dates.append((start, end))
            except ValueError:
                pass
        staff = teachers(row.get('docentes', ''))
        # Metadados ausentes não formam uma identidade confiável.
        if not slots or not staff or staff == ('A DEFINIR',):
            continue
        indexed.append(dict(index=i, row=row, slots=slots, dates=tuple(sorted(dates)), teachers=staff,
                            room=location(row.get('local')), alias=location(row.get('local'), True)))
    findings, covered, involved = [], set(), set()
    for inferred in (False, True):
        groups = defaultdict(list)
        for entry in indexed:
            room = entry['alias' if inferred else 'room']
            if room:
                groups[(entry['row']['periodo'], entry['slots'], entry['dates'], entry['teachers'], room)].append(entry)
        for entries in groups.values():
            if len({e['row']['codigo'] for e in entries}) < 2:
                continue
            pairs = {tuple(sorted((a['index'], b['index']))) for a,b in combinations(entries,2)}
            if pairs <= covered:
                continue
            same_name = len({text(e['row']['disciplina']) for e in entries}) == 1
            finding = dict(kind='possible_joint_class' if same_name else 'simultaneous_different_subjects',
                           period=entries[0]['row']['periodo'], locationAlias=inferred,
                           evidence='Mesmo conjunto de docentes e mesmas faixas completas de horário; '
                                    + ('mesmas datas cadastradas; ' if entries[0]['dates'] else 'datas não informadas; ')
                                    + ('equivalência de rótulos de local inferida (Sala/Bloco).' if inferred else 'mesmo local normalizado.'),
                           records=[describe(e['row']) for e in entries],
                           recordedSeats=sum(e['row']['capacidade'] for e in entries),
                           recordedEnrollments=sum(e['row']['matriculas'] for e in entries),
                           action='Confirmar no SIGAA se há turma conjunta, cotas separadas ou erro de cadastro. Não deduplicar automaticamente.')
            involved.update(e['index'] for e in entries)
            findings.append(finding)
            covered |= pairs
    by_period = defaultdict(list)
    for entry in indexed:
        by_period[entry['row']['periodo']].append(entry)
    for entries in by_period.values():
        for a,b in combinations(entries,2):
            if tuple(sorted((a['index'], b['index']))) in covered:
                continue
            shared = set(a['teachers']) & set(b['teachers'])
            if not shared or a['row']['codigo'] == b['row']['codigo']:
                continue
            if not a['dates'] or not b['dates'] or not any(max(sa,sb) <= min(ea,eb) for sa,ea in a['dates'] for sb,eb in b['dates']):
                continue
            overlap = [(d, max(sa,sb), min(ea,eb)) for d,sa,ea in a['slots'] for db,sb,eb in b['slots']
                       if d == db and max(sa,sb) < min(ea,eb)]
            if overlap:
                involved.update((a['index'], b['index']))
                findings.append(dict(kind='teacher_schedule_overlap', period=a['row']['periodo'],
                                     locationAlias=False, evidence='Docente em comum, datas sobrepostas e ao menos uma faixa de aula simultânea.',
                                     sharedTeachers=sorted(shared), overlappingSlots=overlap,
                                     records=[describe(a['row']),describe(b['row'])],
                                     action='Revisar horário, alternância de aulas e eventual oferta conjunta; coincidência não prova duplicata.'))
    findings.sort(key=lambda f:(f['period'],f['kind'],tuple(r['codigo'] for r in f['records'])))
    return dict(candidateGroups=sum(f['kind'] != 'teacher_schedule_overlap' for f in findings),
                overlappingPairs=sum(f['kind'] == 'teacher_schedule_overlap' for f in findings),
                recordIndices=sorted(involved), excludedRecords=len(involved), countsByKind=dict(Counter(f['kind'] for f in findings)), findings=findings,
                policy='Registros sinalizados são excluídos dos indicadores até revisão; os arquivos originais são preservados. '
                       'os totais do painel representam ofertas por código, não turmas físicas únicas.')

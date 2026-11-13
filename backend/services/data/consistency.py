"""Sinaliza possíveis turmas conjuntas e choques; nunca funde registros."""

from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
import re
import unicodedata


SLOTS = re.compile(r'\b(SEG|TER|QUA|QUI|SEX|SAB|DOM) (\d{2}):(\d{2})-(\d{2}):(\d{2})')
DATES = re.compile(r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})')
ROOM_CODE = re.compile(r'[A-Z]\s*\d{1,3}(?:\s*-?\s*S)?')
WEEKDAYS = {day: index for index, day in enumerate(('SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM'))}


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


def classroom(value):
    """Reconhece um código de sala específico, inclusive com rótulo de laboratório."""
    if not isinstance(value, str):
        return ''
    label = re.sub(r'^(?:(?:LAB\.?\s*(?:DE\s+)?INFORMATICA\s+)?SALA\b|LAB\b\.?)\s*[:.-]?\s*', '', text(value))
    if ROOM_CODE.fullmatch(label):
        return re.sub(r'[^A-Z0-9]', '', label)
    return ''


def shared_slots(first, second):
    return [(day, max(start, other_start), min(end, other_end))
            for day, start, end in first['slots'] for other_day, other_start, other_end in second['slots']
            if day == other_day and max(start, other_start) < min(end, other_end)]


def describe(row):
    return {key: row.get(key) for key in ('periodo', 'codigo', 'disciplina', 'turma', 'docentes',
            'horario', 'local', 'situacao', 'matriculas', 'capacidade', 'origem', 'linha')} | {'arquivo': f"{row['periodo']}.json"}


def summarize_findings(findings, excluded_records):
    counts = Counter(finding['kind'] for finding in findings)
    return dict(candidateGroups=counts['possible_joint_class'] + counts['simultaneous_different_subjects'],
                overlappingPairs=counts['teacher_schedule_overlap'], roomOverlappingPairs=counts['room_schedule_overlap'],
                excludedRecords=excluded_records, countsByKind=dict(counts), findings=findings)


def course_consistency(report, codes):
    findings = [finding for finding in report['findings']
                if any(row['codigo'] in codes for row in finding['records'])]
    excluded = sum(count for code, count in report['excludedRecordsByCode'].items() if code in codes)
    return summarize_findings(findings, excluded)


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
        if not slots:
            continue
        indexed.append(dict(index=i, row=row, slots=slots, dates=tuple(sorted(dates)), teachers=staff,
                            room=location(row.get('local')), alias=location(row.get('local'), True),
                            classroom=classroom(row.get('local'))))
    findings, covered, involved = [], set(), set()
    for inferred in (False, True):
        groups = defaultdict(list)
        for entry in indexed:
            room = entry['alias' if inferred else 'room']
            if room and entry['teachers']:
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
            overlap = shared_slots(a, b)
            if overlap:
                covered.add((a['index'], b['index']))
                involved.update((a['index'], b['index']))
                findings.append(dict(kind='teacher_schedule_overlap', period=a['row']['periodo'],
                                     locationAlias=False, evidence='Docente em comum, datas sobrepostas e ao menos uma faixa de aula simultânea.',
                                     sharedTeachers=sorted(shared), overlappingSlots=overlap,
                                     records=[describe(a['row']),describe(b['row'])],
                                     action='Revisar horário, alternância de aulas e eventual oferta conjunta; coincidência não prova duplicata.'))

    by_classroom = defaultdict(list)
    for entry in indexed:
        row = entry['row']
        if entry['classroom'] and entry['dates'] and row['situacao'] in {'CONSOLIDADA', 'ABERTA'} and row['capacidade'] > 0:
            by_classroom[row['periodo'], entry['classroom']].append(entry)
    for (period, room), entries in by_classroom.items():
        for a, b in combinations(entries, 2):
            indices = a['index'], b['index']
            first, second = a['row'], b['row']
            if indices in covered or (first['codigo'], text(first['turma'])) == (second['codigo'], text(second['turma'])):
                continue
            dates = [(max(start, other_start), min(end, other_end))
                     for start, end in a['dates'] for other_start, other_end in b['dates']]
            overlap = [slot for slot in shared_slots(a, b)
                       if any((WEEKDAYS[slot[0]] - start.weekday()) % 7 <= (end - start).days
                              for start, end in dates)]
            if not overlap:
                continue
            involved.update(indices)
            findings.append(dict(kind='room_schedule_overlap', period=period, locationAlias=False, room=room,
                                 evidence='Mesmo código de sala e faixa de aula sobreposta em datas compatíveis.',
                                 overlappingSlots=overlap, records=[describe(first), describe(second)],
                                 action='Confirmar a sala e a distribuição dos horários no SIGAA.'))

    findings.sort(key=lambda f:(f['period'],f['kind'],tuple(r['codigo'] for r in f['records'])))
    return dict(summarize_findings(findings, len(involved)),
                recordIndices=sorted(involved),
                excludedRecordsByCode=dict(Counter(rows[index]['codigo'] for index in involved)),
                policy='Registros sinalizados são excluídos dos indicadores até revisão; os arquivos originais são preservados. '
                       'os totais do painel representam ofertas por código, não turmas físicas únicas.')

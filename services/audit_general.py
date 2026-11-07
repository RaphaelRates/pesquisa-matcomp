"""Recalcula independentemente cada ponto dos gráficos gerais e rankings.

Este módulo não usa as funções de agregação do painel como referência. Somente
as definições curriculares e o catálogo declarativo dos rankings são partilhados.
"""
from collections import Counter, defaultdict
from fractions import Fraction
from math import isclose
import re
from statistics import median

from services.calc_metrics import sources, current, chart_groups, cohorts

DAYS = {'SEG': 'Seg', 'TER': 'Ter', 'QUA': 'Qua', 'QUI': 'Qui', 'SEX': 'Sex', 'SAB': 'Sáb', 'DOM': 'Dom'}
BANDS = ['Abaixo de 25%', '25% a menos de 50%', '50% a menos de 100%', '100% ou mais']
SCHEDULE = re.compile(r'\b(SEG|TER|QUA|QUI|SEX|SÁB|SAB|DOM) (\d{2}):(\d{2})-(\d{2}):(\d{2})')


def _codes(course, field=1):
    return set(sources[course][field].split())


ALL_OPT = set().union(*(_codes(c) for c in current))
ALL_REQ = set().union(*(_codes(c, 2) for c in current))
CHANGED = (_codes('Ciência da Computação (CC001)') & _codes('Ciência da Computação (CC002)', 2)) | (_codes('Ciência da Computação (CC001)', 2) & _codes('Ciência da Computação (CC002)'))
REQ = ALL_REQ - ALL_OPT - CHANGED
OPT_ONLY = ALL_OPT - ALL_REQ - CHANGED
OPT = OPT_ONLY | {'EM0057'}
MC_REQ = _codes('Matemática Computacional', 2)
MC_OPT = _codes('Matemática Computacional')


def _groups(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[key(row)].append(row)
    return grouped


def _m(rows):
    capacity = sum(r['capacidade'] for r in rows)
    enrolled = sum(r['matriculas'] for r in rows)
    return dict(n=len(rows), c=capacity, m=enrolled,
                rate=Fraction(enrolled, capacity) if capacity else None,
                full=sum(r['matriculas'] >= r['capacidade'] for r in rows),
                over=sum(r['matriculas'] > r['capacidade'] for r in rows),
                low=sum(4*r['matriculas'] < r['capacidade'] for r in rows),
                free=sum(max(0, r['capacidade']-r['matriculas']) for r in rows),
                extra=sum(max(0, r['matriculas']-r['capacidade']) for r in rows),
                zero=sum(r['matriculas'] == 0 for r in rows))


def _band_counts(rows):
    result = [0, 0, 0, 0]
    for row in rows:
        m, c = row['matriculas'], row['capacidade']
        result[0 if 4*m < c else 1 if 2*m < c else 2 if m < c else 3] += 1
    return result


def _slots(row, hours=range(7, 22)):
    result = set()
    for day, sh, sm, eh, em in SCHEDULE.findall(row['horario']):
        day = 'SAB' if day == 'SÁB' else day
        start, end = int(sh)*60+int(sm), int(eh)*60+int(em)
        for hour in hours:
            if start < 60*(hour+1) and end > 60*hour:
                result.add((day, hour))
    return result


def _shift(row):
    shifts = set()
    for _, sh, sm, eh, em in SCHEDULE.findall(row['horario']):
        start, end = int(sh)*60+int(sm), int(eh)*60+int(em)
        for label, lo, hi in [('Manhã', 0, 720), ('Tarde', 720, 1080), ('Noite', 1080, 1440)]:
            if start < hi and end > lo:
                shifts.add(label)
    return next(iter(shifts)) if len(shifts) == 1 else 'Misto' if shifts else 'Sem horário'


def _summary(label, rows):
    value = _m(rows)
    period_values = [_m(rs) for rs in _groups(rows, lambda r: r['periodo']).values()]
    return value | dict(label=label, periods=len(period_values),
                        recurring_full=sum(v['m'] >= v['c'] for v in period_values),
                        recurring_low=sum(4*v['m'] < v['c'] for v in period_values))


def _datasets(rows, slug):
    grouped = {
        'Disciplina': _groups(rows, lambda r: f"{r['codigo']} · {r['disciplina'].title()}"),
        'Semestre': _groups(rows, lambda r: r['periodo']),
        'Prefixo': _groups(rows, lambda r: re.match('[A-Z]+', r['codigo'])[0]),
        'Turno': _groups(rows, _shift),
        'Capacidade': _groups(rows, lambda r: f"{r['capacidade']} vagas"),
        'Dia e horário': defaultdict(list),
        'Matriz do curso': {},
    }
    # Nomes de disciplina são os do último registro de cada código na produção;
    # o agrupamento para o total é sempre por código, mesmo se o texto mudar.
    grouped['Disciplina'] = {f"{code} · {rs[-1]['disciplina'].title()}": rs for code, rs in _groups(rows, lambda r: r['codigo']).items()}
    for row in rows:
        for day, hour in _slots(row, range(24)):
            grouped['Dia e horário'][f'{DAYS[day]} {hour:02}h–{hour+1:02}h'].append(row)
    labels = ['Eng. Civil', 'Eng. de Materiais', 'Ciência da Computação', 'Mat. Computacional', 'Eng. de Software']
    for course, label in zip(current, labels):
        optional = _codes(course) | ({'EM0057'} if course == 'Engenharia de Materiais' else set())
        required = _codes(course, 2)
        allowed = {'optativas': optional, 'obrigatorias': required, 'geral': optional | required}[slug]
        subset = [r for r in rows if r['codigo'] in allowed]
        if subset:
            grouped['Matriz do curso'][label] = subset
    return {dimension: [_summary(label, rs) for label, rs in groups.items()]
            for dimension, groups in grouped.items()}


def _same(actual, expected):
    if isinstance(actual, (int, float, Fraction)) and isinstance(expected, (int, float, Fraction)):
        return isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-11)
    if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
        return len(actual) == len(expected) and all(_same(a, e) for a, e in zip(actual, expected))
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(_same(actual[k], expected[k]) for k in actual)
    return actual == expected


def _label(period):
    return period + ('*' if period == '2026.2' else '')


class _Reference:
    def __init__(self, rows, periods):
        self.rows, self.periods = rows, periods
        self.by_period = _groups(rows, lambda r: r['periodo'])
        self.mc = [r for r in rows if r['codigo'] in MC_REQ | MC_OPT]
        self.mc_period = _groups(self.mc, lambda r: r['periodo'])
        self.cohort_rows = {'obrigatorias': [r for r in rows if r['codigo'] in REQ],
                            'optativas': [r for r in rows if r['codigo'] in OPT],
                            'geral': [r for r in rows if r['codigo'] in REQ | OPT]}
        self.ranks = {slug: _datasets(rs, slug) for slug, rs in self.cohort_rows.items()}

    def rank(self, plot):
        slug, section, index = re.match(r'ufca-ranking-(.+)-(\d+)-(\d+)$', plot['id']).groups()
        _, dimension, metric, limit = chart_groups[int(section)-1][1][int(index)-1]
        def ordered(slug):
            candidates = self.ranks[slug][dimension]
            if dimension == 'Capacidade':
                candidates = [r for r in candidates if int(r['label'].split()[0]) in {20,25,30,40,50}]
            return sorted(candidates, key=lambda r: (r[metric] if limit < 0 else -r[metric], r['label']))[:abs(limit)]
        selected = ordered(slug)
        ceiling = max([r[metric] for group in self.ranks for r in ordered(group)] + [1])
        rows, last, position = [], None, 0
        for i, item in enumerate(selected, 1):
            if item[metric] != last:
                position = i
            last = item[metric]
            label = f"{position}. {item['label']}"
            value = f"{float(item[metric]):.1%}".replace('.', ',') if metric == 'rate' else f"{item[metric]:,}".replace(',', '.')
            if metric == 'rate' and dimension == 'Disciplina':
                value += f" · {item['m']}/{item['c']}"
            elif metric == 'rate' and dimension in {'Turno','Prefixo','Capacidade','Matriz do curso'}:
                label += f" ({item['n']} {'turma' if item['n'] == 1 else 'turmas'})"
            rows.append([label, value, round(float(item[metric]/ceiling)*100, 4)])
        records = [{'label': r['label'], 'value': float(r[metric])} for r in self.ranks[slug][dimension]
                   if dimension != 'Capacidade' or int(r['label'].split()[0]) in {20,25,30,40,50}]
        return rows, [float(r[metric]) for r in selected], records

    def mc_rank(self, plot):
        key = plot['id'].removeprefix('matcomp-')
        choices = {
            'matriculas-historico': ('m', False, False, None),
            'baixa-recorrente': ('recurring_low', False, False, None),
            'maior-ocupacao': ('rate', False, False, None),
            'menor-ocupacao': ('rate', True, False, None),
            'mais-vagas': ('c', False, False, None), 'mais-turmas': ('n', False, False, None),
            'mais-semestres': ('periods', False, False, None), 'sobras': ('free', False, True, None),
            'lotadas': ('full', False, True, None), 'acima-capacidade': ('extra', False, True, None),
            'obrigatorias-matriculas': ('m', False, False, MC_REQ),
            'optativas-matriculas': ('m', False, False, MC_OPT),
        }
        if key not in choices:
            return None
        metric, ascending, positive, allowed = choices[key]
        subset = self.mc if allowed is None else [r for r in self.mc if r['codigo'] in allowed]
        values = [_summary(f"{code} · {rs[-1]['disciplina'].title()}", rs) for code, rs in _groups(subset, lambda r: r['codigo']).items()]
        full_records = [{'label': r['label'], 'value': float(r[metric])} for r in values]
        selected = sorted([r for r in values if not positive or r[metric] > 0], key=lambda r: (r[metric] if ascending else -r[metric], r['label']))[:10]
        result, last, position = [], None, 0
        for i, item in enumerate(selected, 1):
            if item[metric] != last:
                position = i
            last = item[metric]
            result.append([f"{position}. {item['label']}", float(item[metric]) if metric == 'rate' else item[metric]])
        return result, full_records

    def rows_for(self, plot):
        id = plot['id']
        mc = id.startswith('matcomp-')
        rows = self.mc if mc else self.rows
        by_period = self.mc_period if mc else self.by_period
        suffix = id.removeprefix('matcomp-' if mc else 'ufca-')
        if suffix.startswith('indicador-'):
            key = suffix.removeprefix('indicador-')
            result = []
            for p in sorted(by_period):
                rs, m = by_period[p], _m(by_period[p])
                if not rs:
                    continue
                values = {'turmas': [m['n'], len({r['codigo'] for r in rs})], 'saldo': [m['free'],m['extra']],
                          'ocupacao': [m['rate']], 'extremos': [m['low']/m['n'],m['full']/m['n']]}[key]
                result.append([_label(p), *values])
            return result
        if id in {'ufca-capacidade-matriculas', 'matcomp-vagas'}:
            return [[_label(p), _m(by_period[p])['c'], _m(by_period[p])['m']] for p in self.periods if not mc or by_period[p]]
        if suffix == 'faixas':
            return [[_label(p), *_band_counts(by_period[p])] for p in self.periods]
        if id == 'matcomp-comparacao':
            return [[_label(p), _m(self.mc_period[p])['rate'],_m(self.by_period[p])['rate']] for p in self.periods]
        if id == 'matcomp-natureza':
            return [[_label(p), _m([r for r in by_period[p] if r['codigo'] in MC_REQ])['rate'],_m([r for r in by_period[p] if r['codigo'] in MC_OPT])['rate']] for p in self.periods]
        if suffix in {'historico-obrigatorias', 'historico-optativas'}:
            allowed = MC_REQ if suffix.endswith('obrigatorias') else MC_OPT
            codes = _groups(rows, lambda r: r['codigo'])
            return [[_label(p), f"{code} · {codes[code][-1]['disciplina'].title()}", _m([r for r in codes[code] if r['periodo'] == p])['rate']]
                    for code in sorted(allowed & codes.keys()) for p in self.periods]
        if id in {'ufca-prefixos','ufca-codigos'}:
            labels = ['CAR','CC','ECI','EM','ES','MC'] if id.endswith('prefixos') else ['CC0015','ECI0079','CAR0011','ECI0002','EM0105','EM0030','EM0043','EM0114']
            return [[_label(p), label, _m([r for r in rows if r['periodo'] == p and (re.match('[A-Z]+',r['codigo'])[0] if id.endswith('prefixos') else r['codigo']) == label])['rate']]
                    for label in labels for p in self.periods if id != 'ufca-prefixos' or by_period[p]]
        if id == 'ufca-grade-horaria':
            counts = Counter(s for r in rows for s in _slots(r))
            active_days = [d for d in DAYS if d != 'DOM' or any(day == d for day, _ in counts)]
            return [[DAYS[d], f'{h:02}h', counts[(d,h)]] for d in active_days for h in range(7,22)]
        if id == 'ufca-turnos':
            grouped = _groups(rows, _shift)
            return [[f'{s} · {len(grouped[s])} turmas',_m(grouped[s])['rate']] for s in ['Manhã','Tarde','Noite','Misto']]
        if id == 'ufca-tamanho':
            counts = Counter(r['capacidade'] for r in rows)
            return [[f'{c} vagas · {counts[c]} turmas',_m([r for r in rows if r['capacidade'] == c])['rate']] for c in sorted(c for c,_ in counts.most_common(5))]
        if id == 'ufca-opt-curso':
            labels = ['Civil','Materiais','Computação (CC002)','Matemática','Software']
            result = []
            for course, label in zip(current, labels):
                subset = [r for r in rows if r['codigo'] in _codes(course)]
                if subset:
                    result.append([label, _m(subset)['rate']])
            return result
        if id == 'ufca-opt-periodo':
            return [[p, _m([r for r in by_period[p] if r['codigo'] in OPT_ONLY])['rate'],_m([r for r in by_period[p] if r['codigo'] in REQ])['rate']] for p in self.periods if by_period[p]]
        if suffix == 'linha-ocupacao':
            return [[_label(p), median(r['matriculas']/r['capacidade'] for r in by_period[p]) if by_period[p] else None, _m(by_period[p])['rate']] for p in self.periods] if rows else []
        if suffix == 'linha-tamanho':
            return [[_label(p), _m(by_period[p])['c']/len(by_period[p]) if by_period[p] else None, _m(by_period[p])['m']/len(by_period[p]) if by_period[p] else None] for p in self.periods] if rows else []
        if suffix == 'rosca-historico':
            return [[label,count] for label,count in zip(BANDS,_band_counts(rows)) if count]
        if suffix == 'rosca-turnos':
            counts = Counter(map(_shift, rows))
            return [[s,counts[s]] for s in ['Manhã','Tarde','Noite','Misto','Sem horário'] if counts[s]]
        if suffix == 'dispersao':
            counts = Counter((r['capacidade'],r['matriculas']) for r in rows)
            return [[c,m,n] for (c,m),n in sorted(counts.items())]
        if suffix == 'pizza-capacidades':
            counts = Counter(r['capacidade'] for r in rows)
            main = counts.most_common(5)
            result = [[f'{c} vagas',n] for c,n in main]
            other = len(rows)-sum(n for _,n in main)
            return result + ([['Outras capacidades',other]] if other else [])
        if suffix == 'radar-faixas':
            return [[label,count/len(rows) if rows else None] for label,count in zip(BANDS,_band_counts(rows))]
        if suffix == 'faixas-percentual':
            return [[_label(p), *[n/len(by_period[p]) if by_period[p] else None for n in _band_counts(by_period[p])]] for p in self.periods]
        if suffix == 'bolhas-disciplinas':
            return [[f"{code} · {rs[-1]['disciplina'].title()}", _m(rs)['c'],_m(rs)['m'],len(rs)] for code,rs in sorted(_groups(rows,lambda r:r['codigo']).items())]
        if suffix == 'area-natureza':
            req,opt = (MC_REQ,MC_OPT) if mc else (REQ,OPT)
            result=[]
            for p in self.periods:
                values=[sum(r['matriculas'] for r in by_period[p] if (0 if r['codigo'] in req else 1 if r['codigo'] in opt else 2)==i) if by_period[p] else None for i in range(3)]
                result.append([_label(p),*values])
            return result
        raise KeyError(f'Gráfico sem auditoria: {id}')


def audit_general(offers, views):
    """Retorna uma verificação por gráfico, sem confiar nos totais do painel."""
    eligible = [r for r in offers if r['modalidade']=='Presencial' and r['capacidade']>0]
    historical = [r for r in eligible if r['situacao']=='CONSOLIDADA' and r['periodo']<'2026.2']
    periods = sorted({r['periodo'] for r in historical})
    baseline = periods[-1] if periods else None
    samples = {'accumulated': [r for r in eligible if '2023.1' <= r['periodo'] <= '2026.2' and (r['situacao']=='CONSOLIDADA' and r['periodo']<'2026.2' or r['situacao']=='ABERTA' and r['periodo']=='2026.2')],
               'historical': historical,
               'current': [r for r in eligible if r['situacao']=='ABERTA' and r['periodo']=='2026.2'],
               'baseline': [r for r in historical if r['periodo']==baseline]}
    checks=[]
    for view_name in ['historical','current','baseline','accumulated']:
        if view_name not in views:
            continue
        sample=samples[view_name]
        expected_periods=(views[view_name]['scope']['periods'] if view_name=='accumulated' else periods if view_name=='historical' else ['2026.2'] if view_name=='current' else [baseline] if baseline else [])
        reference=_Reference(sample, expected_periods)
        for panel in views[view_name]['paineis']:
            for section in panel['sections']:
                for plot in section['plots']:
                    if '-estat-' in plot['id']:
                        continue
                    try:
                        extra=[]
                        if plot['id'].startswith('ufca-ranking-'):
                            expected,values,records=reference.rank(plot)
                            extra=[('rankingValues',values),('comparisonRecords',records)]
                        elif (mc_rank:=reference.mc_rank(plot)) is not None:
                            expected,records=mc_rank
                            extra=[('comparisonRecords',records)]
                        else:
                            expected=reference.rows_for(plot)
                        sample_for_plot=reference.mc if plot['id'].startswith('matcomp-') else sample
                        if not sample_for_plot:
                            expected=[]
                        passed=_same(plot['rows'],expected)
                        detail=f'{len(expected)} linhas recalculadas independentemente'
                        for field,expected_extra in extra:
                            actual=plot.get(field)
                            if field=='comparisonRecords' and actual is not None:
                                actual=sorted(actual,key=lambda r:r['label'])
                                expected_extra=sorted(expected_extra,key=lambda r:r['label'])
                            passed=passed and _same(actual,expected_extra)
                        if not passed:
                            detail += '; divergência nos valores, categorias, ordem ou registros de comparação'
                        checks.append(dict(id=f'{view_name}/plot/{plot["id"]}',passed=passed,details=detail))
                    except (KeyError,TypeError,ValueError,ZeroDivisionError) as error:
                        checks.append(dict(id=f'{view_name}/plot/{plot["id"]}',passed=False,details=str(error)))
    return checks


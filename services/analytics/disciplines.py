"""Análises por código de disciplina, mantendo a oferta aberta separada."""

from statistics import median
from services.domain.courses import COURSES, curriculum

from services.analytics.metrics import (
    chart, codes, sources, days, distribution, group, hourly_slots, metrics,
    occupancy_bands, occupancy_details, rate, shift,
)


def discipline_analyses(offers):
    eligible = [r for r in offers if r['modalidade'] == 'Presencial' and r['capacidade'] > 0]
    hist = [r for r in eligible if r['situacao'] == 'CONSOLIDADA']
    opened = [r for r in eligible if r['situacao'] == 'ABERTA' and r['periodo'] == '2026.2']
    periods = sorted({r['periodo'] for r in hist + opened})
    return discipline_cohort_analyses(hist, opened, periods)


def discipline_cohort_analyses(primary_rows, comparison_rows, periods, known_disciplines=None):
    """Calcula a amostra principal sem reclassificar os registros de origem."""
    hist, opened = primary_rows, comparison_rows
    historical = group(hist, lambda r: r['codigo'])
    current = group(opened, lambda r: r['codigo'])
    known_disciplines = known_disciplines or {}
    result = []
    for code in sorted(historical.keys() | current.keys() | known_disciplines.keys()):
        past, latest = historical[code], current[code]
        rows = sorted(past + latest, key=lambda r: (r['periodo'], r['turma'], r['horario']))
        name = rows[-1]['disciplina'] if rows else known_disciplines[code]
        plots = []

        def add(key, title, description, spec, columns, values, details=None):
            plot = chart(f'cadeira-{code}-{key}', title, description, spec, columns, values, tooltips=details)
            plot['catalogKey'] = f'cadeira-{key}'
            plots.append(plot)

        by_period = group(rows, lambda r: r['periodo'])
        summaries = [(p + '*' if p == '2026.2' else p, metrics(by_period[p]), by_period[p]) for p in periods]
        note = ' *2026.2 representa turmas abertas; os demais semestres usam consolidadas. Sem oferta aparece como lacuna.'
        for key, title, description, series, values, percent in [
            ('oferta', 'Vagas e matrículas por semestre', 'Totais da disciplina por semestre.', ['Vagas', 'Matrículas'], lambda m, rs: [m['c'], m['m']], False),
            ('ocupacao', 'Ocupação geral e mediana por semestre', 'Compara a razão entre totais com a mediana das ocupações das turmas.', ['Ocupação geral', 'Mediana'], lambda m, rs: [m['rate'], median(map(rate, rs))], True),
            ('saldo', 'Vagas não preenchidas e matrículas excedentes', 'Calcula os saldos separadamente em cada turma antes de somar.', ['Vagas não preenchidas', 'Matrículas excedentes'], lambda m, rs: [m['free'], m['extra']], False),
            ('turmas', 'Quantidade de turmas por semestre', 'Acompanha a frequência da oferta da disciplina.', ['Turmas'], lambda m, rs: [m['n']], False),
        ]:
            spec = dict(type='line' if key == 'ocupacao' else 'bar', x='Semestre', y=series)
            if percent:
                spec['valueFormat'] = {'style': 'percent'}
            add(key, title, description + note, spec, ['Semestre', *series],
                [[p, *values(m, rs)] if rs else [p, *([None] * len(series))] for p, m, rs in summaries],
                [occupancy_details(m) for _, m, _ in summaries])

        add('por-turma', 'Ocupação de cada turma', 'Cada barra identifica uma turma no semestre. * indica oferta aberta em 2026.2.',
            dict(type='bar', x='Turma', y=['Ocupação'], valueFormat={'style': 'percent'}), ['Turma', 'Ocupação'],
            [[f"{r['periodo']}{'*' if r['situacao'] == 'ABERTA' else ''} · {r['turma']} · {i + 1}", rate(r)] for i, r in enumerate(rows)],
            [occupancy_details(metrics([r])) + '\n' + r['horario'] for r in rows])
        for key, title, subset in [('faixas', 'Faixas de ocupação das consolidadas', past), ('faixas-abertas', 'Faixas de ocupação da oferta aberta', latest)]:
            add(key, title, 'Conta turmas em faixas de ocupação; cada turma tem o mesmo peso.',
                dict(type='donut', x='Faixa', y='Turmas', categoryOrder=occupancy_bands), ['Faixa', 'Turmas'],
                [[label, count] for label, count in zip(occupancy_bands, distribution(subset))] if subset else [])
        shifts = group(past, shift)
        add('turnos', 'Ocupação por turno', 'Razão entre matrículas e vagas por turno, apenas das turmas consolidadas.',
            dict(type='horizontalBar', x=['Ocupação'], y='Turno', valueFormat={'style': 'percent'}), ['Turno', 'Ocupação'],
            [[label, metrics(rs)['rate']] for label, rs in sorted(shifts.items())],
            [occupancy_details(metrics(rs)) for _, rs in sorted(shifts.items())])
        hours = range(7, 22)
        slots = [hourly_slots(r, hours) for r in past]
        add('horarios', 'Oferta por dia e horário', 'Conta turmas consolidadas com aula em cada faixa. Uma turma pode ocupar várias células.',
            dict(type='heatmap', x='Dia', y='Horário', value='Turmas', xOrder=list(days.values()), yOrder=[f'{h:02d}h' for h in hours]),
            ['Dia', 'Horário', 'Turmas'], [[label, f'{h:02d}h', sum((day, h) in s for s in slots)] for day, label in days.items() for h in hours] if past else [])
        result.append(dict(code=code, name=name, summary=dict(historico=metrics(past), abertas=metrics(latest)),
                           offeredSemesters=len({r['periodo'] for r in past}), plots=plots))
    return {'cct': result, **{config['key']: [d for d in result if d['code'] in set.union(*curriculum(sources, config))]
                              for config in COURSES}}

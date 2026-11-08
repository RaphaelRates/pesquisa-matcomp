"""Recortes independentes para acumulado, histórico, oferta e referência.

As mesmas famílias de cálculos recebem amostras diferentes. Os registros ABERTA
continuam ABERTA; não se alteram as situações para simular uma consolidação.
"""

import re
from services.dashboard.scopes import scope_text as _scope_text, scope_plot as _scope_plot

from services.analytics.metrics import build_cohort_panels, codes, metrics, select
from services.dashboard.catalog import apply_catalog
from services.analytics.disciplines import discipline_cohort_analyses
from services.domain.courses import COURSES, curriculum
from services.analytics.metrics import sources


CURRENT_PERIOD = '2026.2'
START_PERIOD = '2023.1'


def _keep_plot(plot):
    key = plot['id']
    return not (
        re.match(r'ufca-ranking-.+-4-\d+$', key)
        or any(key.startswith(config["prefix"] + "-abertas-") for config in COURSES)
        or key.endswith('-rosca-abertas')
        or plot.get('catalogKey') == 'cadeira-faixas-abertas'
    )


def _summary(summary, rows, scope):
    summary['selected'] = metrics(rows)
    summary['historico'] = metrics([r for r in rows if r['situacao'] == 'CONSOLIDADA'
                                   and r['periodo'] < CURRENT_PERIOD])
    summary['abertas'] = metrics([r for r in rows if r['situacao'] == 'ABERTA'
                                 and r['periodo'] == CURRENT_PERIOD])
    summary['scope'] = scope


def _view(rows, periods, scope, known_disciplines):
    panels = build_cohort_panels(rows, [], periods)
    disciplines = discipline_cohort_analyses(rows, [], periods, known_disciplines)
    # O catálogo continua sendo a fonte de títulos, descrições e formatos.
    # Em seguida, ajustamos apenas as referências temporais do painel misto.
    apply_catalog(panels, disciplines)
    course_rows = {c["key"]: select(rows, set.union(*curriculum(sources, c))) for c in COURSES}
    for panel in panels:
        sample = course_rows[panel["courseKey"]] if panel.get("courseKey") else rows
        panel['scopeNote'] = scope['note']
        panel['scopeSummary'] = metrics(sample)
        for field in ('title', 'description'):
            if field in panel:
                panel[field] = _scope_text(panel[field], scope, title=field == 'title')
        if panel.get('summary') is not None:
            _summary(panel['summary'], sample, scope)
        if panel.get('statisticalSummary'):
            panel['statisticalSummary']['scope'] = scope['label']
            panel['statisticalSummary']['scopeNote'] = scope['note']
        sections = []
        for section in panel['sections']:
            section['plots'] = [p for p in section['plots'] if _keep_plot(p)]
            if not section['plots']:
                continue
            if section.get('title'):
                section['title'] = _scope_text(section['title'], scope, title=True)
            for plot in section['plots']:
                _scope_plot(plot, scope, len(sample))
            sections.append(section)
        panel['sections'] = sections
    panels.sort(key=lambda panel: (1, next(i for i,c in enumerate(COURSES) if c["key"] == panel["courseKey"])) if panel.get("courseKey") else (0, 0))
    by_code = {}
    for row in rows:
        by_code.setdefault(row['codigo'], []).append(row)
    # mc referencia os mesmos objetos de cct: personalizamos uma única vez.
    for discipline in disciplines['cct']:
        sample = by_code.get(discipline['code'], [])
        _summary(discipline['summary'], sample, scope)
        discipline['scopeNote'] = scope['note']
        discipline['plots'] = [p for p in discipline['plots'] if _keep_plot(p)]
        for plot in discipline['plots']:
            _scope_plot(plot, scope, len(sample))
    return dict(paineis=panels, disciplines=disciplines, scope=scope)


def build_period_views(offers):
    """Entrega quatro recortes independentes, incluindo amostras vazias válidas."""
    eligible = [r for r in offers if r['modalidade'] == 'Presencial' and r['capacidade'] > 0]
    historical = [r for r in eligible if r['situacao'] == 'CONSOLIDADA' and r['periodo'] < CURRENT_PERIOD]
    opened = [r for r in eligible if r['situacao'] == 'ABERTA' and r['periodo'] == CURRENT_PERIOD]
    accumulated = [r for r in historical + opened if r['periodo'] >= START_PERIOD]
    accumulated_periods = sorted({r['periodo'] for r in accumulated} | {CURRENT_PERIOD})
    historical_periods = sorted({r['periodo'] for r in historical})
    baseline_period = historical_periods[-1] if historical_periods else None
    baseline = [r for r in historical if r['periodo'] == baseline_period]
    known = {r['codigo']: r['disciplina'] for r in historical + opened}
    historical_label = (f'{historical_periods[0]} a {historical_periods[-1]}' if len(historical_periods) > 1
                        else historical_periods[0] if historical_periods else 'sem registros')
    scopes = {
        'accumulated': dict(id='accumulated', label=f'Acumulado · {START_PERIOD} a {CURRENT_PERIOD}',
                            note=f'Turmas presenciais de {START_PERIOD} a {CURRENT_PERIOD}: '
                                 'consolidadas até 2026.1 e abertas de 2026.2. '
                                 'Matrículas e ocupação de 2026.2 ainda podem mudar.',
                            periods=accumulated_periods, status='MISTA'),
        'historical': dict(id='historical', label=f'Histórico consolidado · {historical_label}',
                           note=f'Somente turmas presenciais consolidadas de {historical_label}. A oferta aberta é consultada separadamente.',
                           periods=historical_periods, status='CONSOLIDADA'),
        'current': dict(id='current', label='Oferta aberta · 2026.2',
                        note='Somente turmas presenciais abertas de 2026.2. Matrículas e ocupação ainda podem mudar.',
                        periods=[CURRENT_PERIOD], status='ABERTA'),
        'baseline': dict(id='baseline', label=f'Referência consolidada · {baseline_period or "sem registros"}',
                         note=f'Somente turmas presenciais consolidadas de {baseline_period or "referência indisponível"}.',
                         periods=[baseline_period] if baseline_period else [], status='CONSOLIDADA'),
    }
    return {
        'accumulated': _view(accumulated, accumulated_periods, scopes['accumulated'], known),
        'historical': _view(historical, historical_periods, scopes['historical'], known),
        'current': _view(opened, [CURRENT_PERIOD], scopes['current'], known),
        'baseline': _view(baseline, [baseline_period] if baseline_period else [], scopes['baseline'], known),
        'baselinePeriod': baseline_period,
        'historicalPeriods': historical_periods,
    }

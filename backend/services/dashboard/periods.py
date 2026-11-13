"""Recortes independentes para acumulado, histórico, oferta e referência.

As mesmas famílias de cálculos recebem amostras diferentes. Os registros ABERTA
continuam ABERTA; não se alteram as situações para simular uma consolidação.
"""

import re
from services.dashboard.scopes import course_scope, scope_text as _scope_text, scope_plot as _scope_plot

from services.analytics.metrics import build_cohort_panels, group, metrics, select
from services.dashboard.catalog import apply_catalog
from services.analytics.disciplines import discipline_cohort_analyses
from services.domain.courses import COURSES, curriculum
from services.analytics.metrics import sources
from services.data.selection import split_offers


def _keep_plot(plot):
    key = plot['id']
    return not (
        re.match(r'ufca-ranking-.+-4-\d+$', key)
        or any(key.startswith(config["prefix"] + "-abertas-") for config in COURSES)
        or key.endswith('-rosca-abertas')
        or plot.get('catalogKey') == 'cadeira-faixas-abertas'
    )


def scope_summary(rows, scope):
    return dict(
        selected=metrics(rows),
        historico=metrics([r for r in rows if r['situacao'] == 'CONSOLIDADA']),
        abertas=metrics([r for r in rows if r['situacao'] == 'ABERTA']),
        scope=scope,
    )


def period_breakdown(rows):
    by_semester = group(rows, lambda row: row['periodo'])
    by_year = group(rows, lambda row: row['periodo'].partition('.')[0])
    semesters = [
        dict(period=period, open=any(row['situacao'] == 'ABERTA' for row in sample), summary=metrics(sample))
        for period, sample in sorted(by_semester.items())
    ]
    years = [
        dict(year=year, periods=sorted({row['periodo'] for row in sample}),
             summary=metrics(sample))
        for year, sample in sorted(by_year.items())
    ]
    return dict(years=years, semesters=semesters)


def _view(rows, periods, scope, known_disciplines):
    panels = build_cohort_panels(rows, [], periods)
    disciplines = discipline_cohort_analyses(rows, [], periods, known_disciplines)
    # O catálogo continua sendo a fonte de títulos, descrições e formatos.
    # Em seguida, ajustamos apenas as referências temporais do painel misto.
    apply_catalog(panels, disciplines)
    course_rows = {c["key"]: select(rows, set.union(*curriculum(sources, c))) for c in COURSES}
    for panel in panels:
        course = panel.get('courseKey')
        sample = course_rows[course] if course else rows
        panel_scope = course_scope(scope, sample) if course else scope
        panel['scopeNote'] = panel_scope['note']
        panel['scopeSummary'] = metrics(sample)
        for field in ('title', 'description'):
            if field in panel:
                panel[field] = _scope_text(panel[field], panel_scope, title=field == 'title')
        if panel.get('summary') is not None:
            panel['summary'] = scope_summary(sample, panel_scope)
        if panel.get('statisticalSummary'):
            panel['statisticalSummary']['scope'] = panel_scope['label']
            panel['statisticalSummary']['scopeNote'] = panel_scope['note']
        sections = []
        for section in panel['sections']:
            section['plots'] = [p for p in section['plots'] if _keep_plot(p)]
            if not section['plots']:
                continue
            if section.get('title'):
                section['title'] = _scope_text(section['title'], panel_scope, title=True)
            for plot in section['plots']:
                _scope_plot(plot, panel_scope, len(sample))
            sections.append(section)
        panel['sections'] = sections
    panels.sort(key=lambda panel: (1, next(i for i,c in enumerate(COURSES) if c["key"] == panel["courseKey"])) if panel.get("courseKey") else (0, 0))
    by_code = {}
    for row in rows:
        by_code.setdefault(row['codigo'], []).append(row)
    # mc referencia os mesmos objetos de cct: personalizamos uma única vez.
    for discipline in disciplines['cct']:
        sample = by_code.get(discipline['code'], [])
        discipline['summary'] = scope_summary(sample, scope)
        discipline['scopeNote'] = scope['note']
        discipline['plots'] = [p for p in discipline['plots'] if _keep_plot(p)]
        for plot in discipline['plots']:
            _scope_plot(plot, scope, len(sample))
    return dict(paineis=panels, disciplines=disciplines, scope=scope)


def period_samples(offers):
    """Seleciona as amostras e os metadados usados pelas duas interfaces."""
    historical, opened = split_offers(offers)
    accumulated = historical + opened
    latest = max((row['periodo'] for row in accumulated), default=None)
    current = [r for r in opened if r['periodo'] == latest]
    current_period = latest if current else None
    baseline_period = max((r['periodo'] for r in historical
                           if current_period and r['periodo'] < current_period), default=None)
    baseline = [r for r in historical if r['periodo'] == baseline_period]
    samples = dict(accumulated=accumulated, historical=historical, current=current, baseline=baseline)
    scope_types = (
        ('accumulated', 'Acumulado', 'MISTA'), ('historical', 'Histórico consolidado', 'CONSOLIDADA'),
        ('current', 'Oferta aberta', 'ABERTA'), ('baseline', 'Referência consolidada', 'CONSOLIDADA'),
    )
    scopes = {key: course_scope(dict(id=key, label=label, status=status), samples[key], course=False)
              for key, label, status in scope_types}
    known = {r['codigo']: r['disciplina'] for r in sorted(accumulated, key=lambda row: row['periodo'])}
    return samples, scopes, known


def build_period_views(offers):
    """Entrega quatro recortes independentes, incluindo amostras vazias válidas."""
    samples, scopes, known = period_samples(offers)
    views = {key: _view(rows, scopes[key]['periods'], scopes[key], known) for key, rows in samples.items()}
    views['baselinePeriod'] = next(iter(scopes['baseline']['periods']), None)
    views['currentPeriod'] = next(iter(scopes['current']['periods']), None)
    views['historicalPeriods'] = scopes['historical']['periods']
    return views

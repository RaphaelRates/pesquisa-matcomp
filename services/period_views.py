"""Recortes independentes para histórico, oferta aberta e semestre de referência.

As mesmas famílias de cálculos recebem amostras diferentes. Os registros ABERTA
continuam ABERTA; não se alteram as situações para simular uma consolidação.
"""

import re

from services.calc_metrics import build_cohort_panels, codes, metrics, select
from services.chart_catalog import apply_catalog
from services.discipline_metrics import discipline_cohort_analyses


CURRENT_PERIOD = '2026.2'
SERIES_NAMES = {'Consolidadas': 'Recorte selecionado',
                'Consolidadas até 2026.1': 'Recorte selecionado'}


def _scope_text(text, scope, *, title=False):
    """Mantém o método e elimina avisos temporais do painel misto original."""
    if not text:
        return text
    if not title:
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ*])', text)
        text = ' '.join(sentence for sentence in sentences
                        if '2026.2' not in sentence and 'asterisco' not in sentence.lower())
    text = re.sub(r'\*Turmas abertas\.?', '', text, flags=re.I)
    text = re.sub(r'\s+até 2026\.1', '', text, flags=re.I)
    text = text.replace('somadas nos sete semestres', 'somadas no recorte selecionado')
    text = text.replace('histórico consolidado', 'recorte selecionado')
    if scope['id'] == 'current':
        text = re.sub(r'consolidadas', 'abertas', text, flags=re.I)
        text = re.sub(r'consolidada', 'aberta', text, flags=re.I)
        text = text.replace('histórico', 'recorte selecionado').replace('Histórico', 'Recorte selecionado')
    return text.strip()


def _drop_comparison_series(plot):
    """O recorte possui uma amostra; a comparação entre períodos é externa."""
    removed = [i for i, name in enumerate(plot['columns']) if name == 'Abertas em 2026.2']
    if not removed:
        return
    plot['columns'] = [name for i, name in enumerate(plot['columns']) if i not in removed]
    plot['rows'] = [[value for i, value in enumerate(row) if i not in removed] for row in plot['rows']]
    spec = plot.get('spec', {})
    for axis in ('x', 'y'):
        if isinstance(spec.get(axis), list):
            spec[axis] = [name for name in spec[axis] if name != 'Abertas em 2026.2']


def _scope_plot(plot, scope, row_count):
    _drop_comparison_series(plot)
    plot['columns'] = [SERIES_NAMES.get(name, name) for name in plot['columns']]
    spec = plot.get('spec', {})
    for axis in ('x', 'y'):
        value = spec.get(axis)
        if isinstance(value, list):
            spec[axis] = [SERIES_NAMES.get(name, name) for name in value]
        elif isinstance(value, str):
            spec[axis] = SERIES_NAMES.get(value, value)
    for field in ('title', 'description', 'method', 'interpretation'):
        if field in plot:
            plot[field] = _scope_text(plot[field], scope, title=field == 'title')
    if not plot['description']:
        plot['description'] = 'Indicadores calculados com as turmas do recorte selecionado.'
    if plot['id'].endswith('-radar-faixas'):
        plot['description'] = 'Cada eixo mostra a proporção de turmas do recorte na respectiva faixa de ocupação.'
    if plot['id'].endswith('-estat-histograma'):
        plot['description'] = 'Proporções das turmas do recorte em seis intervalos de ocupação.'
    if plot['id'] == 'ufca-opt-curso':
        plot['description'] = ('Ocupação dos códigos listados como optativos na matriz de referência de cada curso. '
                               'Cada razão usa matrículas e vagas das turmas do recorte selecionado.')
    if plot.get('tooltips'):
        plot['tooltips'] = [
            _scope_text('\n'.join(line for line in tip.split('\n') if not line.startswith('Abertas:'))
                        .replace('Consolidadas:', 'Recorte selecionado:'), scope)
            for tip in plot['tooltips']
        ]
    plot['scopeId'] = scope['id']
    plot['scope'] = scope['label']
    plot['scopeNote'] = scope['note']
    if not row_count:
        plot['rows'] = []
        if plot.get('tooltips') is not None:
            plot['tooltips'] = []
        if 'rankingValues' in plot:
            plot['rankingValues'] = []


def _keep_plot(plot):
    key = plot['id']
    return not (
        re.match(r'ufca-ranking-.+-4-\d+$', key)
        or key.startswith('matcomp-abertas-')
        or key.endswith('-rosca-abertas')
        or plot.get('catalogKey') == 'cadeira-faixas-abertas'
    )


def _summary(summary, rows, scope):
    summary['selected'] = metrics(rows)
    summary['historico'] = metrics([] if scope['id'] == 'current' else rows)
    summary['abertas'] = metrics(rows if scope['id'] == 'current' else [])
    summary['scope'] = scope


def _view(rows, periods, scope, known_disciplines):
    panels = build_cohort_panels(rows, [], periods)
    disciplines = discipline_cohort_analyses(rows, [], periods, known_disciplines)
    # O catálogo continua sendo a fonte de títulos, descrições e formatos.
    # Em seguida, ajustamos apenas as referências temporais do painel misto.
    apply_catalog(panels, disciplines)
    mc_codes = codes('Matemática Computacional') | codes('Matemática Computacional', 2)
    mc_rows = select(rows, mc_codes)
    for panel in panels:
        sample = mc_rows if panel['id'] == 'matematica-computacional' else rows
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
    panels.sort(key=lambda panel: panel['id'] == 'matematica-computacional')
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
    """Entrega três recortes independentes, incluindo amostras vazias válidas."""
    eligible = [r for r in offers if r['modalidade'] == 'Presencial' and r['capacidade'] > 0]
    historical = [r for r in eligible if r['situacao'] == 'CONSOLIDADA' and r['periodo'] < CURRENT_PERIOD]
    opened = [r for r in eligible if r['situacao'] == 'ABERTA' and r['periodo'] == CURRENT_PERIOD]
    historical_periods = sorted({r['periodo'] for r in historical})
    baseline_period = historical_periods[-1] if historical_periods else None
    baseline = [r for r in historical if r['periodo'] == baseline_period]
    known = {r['codigo']: r['disciplina'] for r in historical + opened}
    historical_label = (f'{historical_periods[0]} a {historical_periods[-1]}' if len(historical_periods) > 1
                        else historical_periods[0] if historical_periods else 'sem registros')
    scopes = {
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
        'historical': _view(historical, historical_periods, scopes['historical'], known),
        'current': _view(opened, [CURRENT_PERIOD], scopes['current'], known),
        'baseline': _view(baseline, [baseline_period] if baseline_period else [], scopes['baseline'], known),
        'baselinePeriod': baseline_period,
        'historicalPeriods': historical_periods,
    }

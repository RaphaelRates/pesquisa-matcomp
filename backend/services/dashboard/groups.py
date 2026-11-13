"""Gráficos agregados padronizados para os grupos selecionáveis do painel.

As turmas do centro são contadas diretamente, sem somar matrizes que podem
compartilhar códigos. Os recortes dos cursos seguem as mesmas matrizes das
análises específicas, incluindo disciplinas CAR presentes nessas matrizes.
"""

from collections import defaultdict
from fractions import Fraction

from services.analytics.metrics import chart, metrics, overview_panels, sources, varied_charts
from services.domain.curricula import changed
from services.analytics.statistics import statistical_panel, statistical_summary
from services.analytics.comparison import compare_plots, compare_statistics, compare_summary
from services.domain.courses import COURSES, curriculum
from services.dashboard.catalog import apply_catalog
from services.dashboard.periods import period_samples, scope_summary
from services.dashboard.scopes import course_scope, scope_plot as _scope_plot, scope_text as _scope_text


GROUPS = (
    dict(id='cct', label='CCT · Todos os cursos', title='Centro de Ciências e Tecnologia', courseKey=None),
    dict(id='mc', label='MC · Matemática Computacional', title='Matemática Computacional', courseKey='mc'),
    dict(id='cc', label='CC · Ciência da Computação', title='Ciência da Computação', courseKey='cc'),
    dict(id='em', label='EM · Engenharia de Materiais', title='Engenharia de Materiais', courseKey='materiais'),
    dict(id='eci', label='ECI · Engenharia Civil', title='Engenharia Civil', courseKey='civil'),
    dict(id='es', label='ES · Engenharia de Software', title='Engenharia de Software', courseKey='software'),
)
VIEW_KEYS = ('accumulated', 'historical', 'current', 'baseline')


def _rankings(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['codigo']].append(row)
    result = []
    definitions = (
        ('matriculas', 'Disciplinas com mais matrículas', 'Matrículas', 'm'),
        ('vagas', 'Disciplinas com mais vagas ofertadas', 'Vagas', 'c'),
        ('ocupacao', 'Disciplinas com maior ocupação', 'Ocupação', 'rate'),
        ('disponiveis', 'Disciplinas com mais vagas não preenchidas', 'Vagas não preenchidas', 'free'),
    )
    for key, title, column, measure in definitions:
        values = []
        for code, classes in grouped.items():
            summary = metrics(classes)
            value = Fraction(summary['m'], summary['c']) if measure == 'rate' else summary[measure]
            values.append((f"{code} · {classes[-1]['disciplina'].title()}", value))
        ordered = sorted(values, key=lambda item: (-item[1], item[0]))
        spec = dict(type='horizontalBar', x=column, y='Disciplina')
        if measure == 'rate':
            spec['valueFormat'] = {'style': 'percent'}
        plot = chart(f'geral-ranking-{key}', title,
                     'Até dez códigos ordenados pelo resultado no grupo e no recorte selecionados. '
                     'Cada turma contribui uma vez para o total de seu código.',
                     spec, ['Disciplina', column], [[label, float(value)] for label, value in ordered[:10]])
        plot.update(comparisonMetric=measure, comparisonDimension='Disciplina',
                    comparisonRecords=[dict(label=label, value=float(value)) for label, value in ordered])
        result.append(plot)
    return dict(title='Rankings do grupo', plots=result)


GROUP_FAMILIES = {
    'evolucao': 'Evolução do grupo por semestre',
    'horarios': 'Horários, turnos e capacidade',
    'distribuicao': 'Distribuição e composição do grupo',
    'rankings': 'Rankings do grupo',
    'estatisticas': 'Estatísticas do grupo',
}


def group_sections(rows, scope, definition, config, family, *, summary=None, catalog=None):
    if family in ('evolucao', 'horarios'):
        panel_id = 'evolucao' if family == 'evolucao' else 'horarios-capacidade'
        panel, = overview_panels(rows, [], scope['periods'], only=panel_id)
        sections = [dict(title=GROUP_FAMILIES[family], plots=panel['sections'][0]['plots'])]
    elif family == 'distribuicao':
        if config:
            classification = curriculum(sources, config)
        else:
            classifications = [curriculum(sources, course) for course in COURSES]
            required = set.union(*(required for required, _ in classifications))
            optional = set.union(*(optional for _, optional in classifications))
            classification = required - optional - changed, optional - required - changed
        plots = varied_charts('ufca', rows, [], scope['periods'], classification)
        sections = [dict(title=GROUP_FAMILIES[family],
                         plots=[p for p in plots if not p['id'].endswith('-rosca-abertas')])]
    elif family == 'rankings':
        sections = [_rankings(rows)]
    else:
        stats = statistical_panel('ufca', 'Estatísticas do grupo', rows, [], scope['periods'], summary=summary)
        sections = stats['sections']
    apply_catalog([dict(sections=sections)], {'cct': []}, catalog)
    for section in sections:
        section['title'] = _scope_text(section['title'], scope, title=True)
        for plot in section['plots']:
            original_id = plot['id']
            plot['catalogKey'] = original_id
            _scope_plot(plot, scope, len(rows))
            plot['id'] = f"group-{definition['id']}-{original_id}"
    return sections


def _build_group(rows, scope, definition, config):
    stats = statistical_summary(rows)
    sections = [section for family in GROUP_FAMILIES
                for section in group_sections(rows, scope, definition, config, family, summary=stats)]
    result = dict(**definition, scopeNote=scope['note'], summary=scope_summary(rows, scope),
                  statisticalSummary=stats, sections=sections,
                  description='Indicadores agregados das turmas do grupo selecionado. Os cursos seguem as matrizes '
                              'de referência, com os códigos compartilhados nelas presentes. CAR não é um curso.')
    result['statisticalSummary']['scope'] = scope['label']
    result['statisticalSummary']['scopeNote'] = scope['note']
    return result


def course_comparisons(rows, scope, catalog=None):
    summaries = []
    for config in COURSES:
        allowed = set.union(*curriculum(sources, config))
        selected = [row for row in rows if row['codigo'] in allowed]
        summaries.append((config['title'], metrics(selected)))
    description = ('Comparação das matrizes de referência no mesmo recorte. Códigos compartilhados podem aparecer '
                   'em mais de um curso; os valores dos cursos não devem ser somados para reconstruir o CCT.')
    plots = [
        chart('entre-cursos-ocupacao', 'Ocupação geral por curso', description,
              dict(type='horizontalBar', x='Ocupação', y='Curso', valueFormat={'style': 'percent'}),
              ['Curso', 'Ocupação'], [[name, value['rate']] for name, value in summaries]),
        chart('entre-cursos-volume', 'Vagas e matrículas por curso', description,
              dict(type='horizontalBar', x=['Vagas', 'Matrículas'], y='Curso'),
              ['Curso', 'Vagas', 'Matrículas'], [[name, value['c'], value['m']] for name, value in summaries]),
        chart('entre-cursos-turmas', 'Turmas ofertadas por curso', description,
              dict(type='horizontalBar', x='Turmas', y='Curso'),
              ['Curso', 'Turmas'], [[name, value['n']] for name, value in summaries]),
    ]
    for plot in plots:
        plot.update(catalogKey=plot['id'], scopeId=scope['id'], scopeNote=scope['note'])
    apply_catalog([dict(sections=[dict(plots=plots)])], {'cct': []}, catalog)
    return dict(title='Comparação entre cursos', description=description, plots=plots)


def enrich_groups(offers, views):
    """Acrescenta grupos padronizados e comparações entre cursos em cada recorte."""
    courses = {course['key']: course for course in COURSES}
    samples, _, _ = period_samples(offers)
    for key in VIEW_KEYS:
        if key not in views:
            continue
        view = views[key]
        rows = samples[key]
        groups = {}
        for definition in GROUPS:
            config = courses.get(definition['courseKey'])
            allowed = set.union(*curriculum(sources, config)) if config else None
            selected = rows if allowed is None else [r for r in rows if r['codigo'] in allowed]
            scope = course_scope(view['scope'], selected) if config else view['scope']
            groups[definition['id']] = _build_group(selected, scope, definition, config)
        view['groups'] = groups
        view['courseComparisons'] = course_comparisons(rows, view['scope'])
    return views


def _plots(view):
    return [plot for group in view.get('groups', {}).values() for section in group['sections'] for plot in section['plots']] + list(view.get('courseComparisons', {}).get('plots', []))


def attach_group_comparisons(views):
    """Compara a oferta aberta com a referência e compartilha a tabela entre as abas."""
    current = views['current']
    baseline = views.get('baseline', {})
    period = views.get('baselinePeriod')
    current_period = views.get('currentPeriod')
    old_plots = {plot['id']: plot for plot in _plots(baseline)}
    current_plots = {plot['id']: plot for plot in _plots(current)}
    for plot_id, plot in current_plots.items():
        old = old_plots.get(plot_id)
        plot['comparison'] = compare_plots(old, plot, period, current_period)
        if period and old is not None:
            plot['comparison']['baselinePlot'] = old
    for group_id, group in current['groups'].items():
        old = baseline.get('groups', {}).get(group_id, {})
        group['summary']['comparison'] = compare_summary(
            old.get('summary', {}).get('selected'), group['summary']['selected'], period, current_period)
        group['statisticalSummary']['comparison'] = compare_statistics(
            old.get('statisticalSummary'), group['statisticalSummary'], period, current_period)
    for key in ('accumulated', 'historical'):
        if key not in views:
            continue
        for plot in _plots(views[key]):
            plot['comparison'] = current_plots[plot['id']]['comparison']
        for group_id, group in views[key]['groups'].items():
            group['summary']['comparison'] = current['groups'][group_id]['summary']['comparison']
            group['statisticalSummary']['comparison'] = current['groups'][group_id]['statisticalSummary']['comparison']
    return views

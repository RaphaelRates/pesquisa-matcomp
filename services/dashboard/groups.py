"""Gráficos agregados padronizados para os grupos selecionáveis do painel.

As turmas do centro são contadas diretamente, sem somar matrizes que podem
compartilhar códigos. Os recortes dos cursos seguem as mesmas matrizes das
análises específicas, incluindo disciplinas CAR presentes nessas matrizes.
"""

from collections import defaultdict
from fractions import Fraction

from services.analytics.metrics import chart, metrics, overview_panels, sources, varied_charts
from services.analytics.statistics import statistical_panel
from services.analytics.comparison import compare_plots, compare_statistics, compare_summary
from services.domain.courses import COURSES, curriculum
from services.dashboard.catalog import apply_catalog
from services.dashboard.scopes import scope_plot as _scope_plot, scope_text as _scope_text


GROUPS = (
    dict(id='cct', label='CCT · Todos os cursos', title='Centro de Ciências e Tecnologia', courseKey=None),
    dict(id='mc', label='MC · Matemática Computacional', title='Matemática Computacional', courseKey='mc'),
    dict(id='cc', label='CC · Ciência da Computação', title='Ciência da Computação', courseKey='cc'),
    dict(id='em', label='EM · Engenharia de Materiais', title='Engenharia de Materiais', courseKey='materiais'),
    dict(id='eci', label='ECI · Engenharia Civil', title='Engenharia Civil', courseKey='civil'),
    dict(id='es', label='ES · Engenharia de Software', title='Engenharia de Software', courseKey='software'),
)
VIEW_KEYS = ('accumulated', 'historical', 'current', 'baseline')


def _scope_rows(offers, scope):
    def selected(row):
        if scope['status'] == 'MISTA':
            return '2023.1' <= row['periodo'] <= '2026.2' and (
                row['situacao'] == 'CONSOLIDADA' and row['periodo'] < '2026.2'
                or row['situacao'] == 'ABERTA' and row['periodo'] == '2026.2')
        return row['situacao'] == scope['status']
    return [row for row in offers if row['modalidade'] == 'Presencial' and row['capacidade'] > 0
            and row['periodo'] in scope['periods'] and selected(row)]


def _summary(rows, scope):
    return dict(selected=metrics(rows), scope=scope,
                historico=metrics([r for r in rows if r['situacao'] == 'CONSOLIDADA' and r['periodo'] < '2026.2']),
                abertas=metrics([r for r in rows if r['situacao'] == 'ABERTA' and r['periodo'] == '2026.2']))


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


def _build_group(rows, scope, definition, config):
    overview = {panel['id']: panel for panel in overview_panels(rows, [], scope['periods'])}
    stats = statistical_panel('ufca', 'Estatísticas do grupo', rows, [], scope['periods'])
    classification = curriculum(sources, config) if config else None
    explorations = varied_charts('ufca', rows, [], scope['periods'], classification)
    explorations = [plot for plot in explorations if not plot['id'].endswith('-rosca-abertas')]
    sections = [
        dict(title='Evolução do grupo por semestre', plots=overview['evolucao']['sections'][0]['plots']),
        dict(title='Horários, turnos e capacidade', plots=overview['horarios-capacidade']['sections'][0]['plots']),
        dict(title='Distribuição e composição do grupo', plots=explorations),
        _rankings(rows),
        *stats['sections'],
    ]
    result = dict(**definition, scopeNote=scope['note'], summary=_summary(rows, scope),
                  statisticalSummary=stats['statisticalSummary'], sections=sections,
                  description='Indicadores agregados das turmas do grupo selecionado. Os cursos seguem as matrizes '
                              'de referência, com os códigos compartilhados nelas presentes. CAR não é um curso.')
    apply_catalog([result], {'cct': []})
    for section in sections:
        section['title'] = _scope_text(section['title'], scope, title=True)
        for plot in section['plots']:
            original_id = plot['id']
            plot['catalogKey'] = original_id
            _scope_plot(plot, scope, len(rows))
            plot['id'] = f"group-{definition['id']}-{original_id}"
    result['statisticalSummary']['scope'] = scope['label']
    result['statisticalSummary']['scopeNote'] = scope['note']
    return result


def _course_comparisons(rows, scope):
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
    apply_catalog([dict(sections=[dict(plots=plots)])], {'cct': []})
    return dict(title='Comparação entre cursos', description=description, plots=plots)


def enrich_groups(offers, views):
    """Acrescenta grupos padronizados e comparações entre cursos em cada recorte."""
    courses = {course['key']: course for course in COURSES}
    for key in VIEW_KEYS:
        if key not in views:
            continue
        view = views[key]
        rows = _scope_rows(offers, view['scope'])
        groups = {}
        for definition in GROUPS:
            config = courses.get(definition['courseKey'])
            allowed = set.union(*curriculum(sources, config)) if config else None
            selected = rows if allowed is None else [r for r in rows if r['codigo'] in allowed]
            groups[definition['id']] = _build_group(selected, view['scope'], definition, config)
        view['groups'] = groups
        view['courseComparisons'] = _course_comparisons(rows, view['scope'])
    return views


def _plots(view):
    return [plot for group in view.get('groups', {}).values() for section in group['sections'] for plot in section['plots']] + list(view.get('courseComparisons', {}).get('plots', []))


def attach_group_comparisons(views):
    """Compara 2026.2 com a referência e compartilha a tabela entre as abas."""
    current = views['current']
    baseline = views.get('baseline', {})
    period = views.get('baselinePeriod')
    old_plots = {plot['id']: plot for plot in _plots(baseline)}
    current_plots = {plot['id']: plot for plot in _plots(current)}
    for plot_id, plot in current_plots.items():
        old = old_plots.get(plot_id)
        plot['comparison'] = compare_plots(old, plot, period)
        if period and old is not None:
            plot['comparison']['baselinePlot'] = old
    for group_id, group in current['groups'].items():
        old = baseline.get('groups', {}).get(group_id, {})
        group['summary']['comparison'] = compare_summary(old.get('summary', {}).get('selected'), group['summary']['selected'], period)
        group['statisticalSummary']['comparison'] = compare_statistics(old.get('statisticalSummary'), group['statisticalSummary'], period)
    for key in ('accumulated', 'historical'):
        if key not in views:
            continue
        for plot in _plots(views[key]):
            plot['comparison'] = current_plots[plot['id']]['comparison']
        for group_id, group in views[key]['groups'].items():
            group['summary']['comparison'] = current['groups'][group_id]['summary']['comparison']
            group['statisticalSummary']['comparison'] = current['groups'][group_id]['statisticalSummary']['comparison']
    return views

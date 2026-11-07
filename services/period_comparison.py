"""Diferenças descritivas entre dois semestres com categorias compatíveis.

Ausência de categoria não equivale a zero: os gráficos podem limitar rankings
ou omitir uma disciplina sem oferta. Turmas e pontos de dispersão não são
pareados artificialmente entre os semestres.
"""

from math import isfinite
from numbers import Real
import re
import unicodedata


CURRENT_PERIOD = '2026.2'
SUMMARY_METRICS = [
    ('n', 'Turmas', 'number'), ('c', 'Vagas ofertadas', 'number'),
    ('m', 'Matrículas', 'number'), ('rate', 'Ocupação geral', 'percent'),
    ('free', 'Vagas não preenchidas', 'number'),
    ('extra', 'Matrículas acima da capacidade', 'number'),
    ('full', 'Turmas com ocupação de 100% ou mais', 'number'),
    ('over', 'Turmas acima da capacidade', 'number'),
    ('low', 'Turmas abaixo de 25% de ocupação', 'number'),
    ('zero', 'Turmas sem matrículas', 'number'),
]


def _fold(value):
    return ''.join(c for c in unicodedata.normalize('NFD', str(value))
                   if not unicodedata.combining(c)).casefold().strip()


def _number(value):
    return float(value) if isinstance(value, Real) and not isinstance(value, bool) and isfinite(value) else None


def _row(category, metric, before, after, unit='number'):
    before, after = _number(before), _number(after)
    delta = after - before if before is not None and after is not None else None
    if before is None:
        status = 'no_baseline'
    elif after is None:
        status = 'no_current'
    elif before == 0:
        status = 'zero_baseline'
    else:
        status = 'comparable'
    # Variação relativa de índice/coeficiente ou base negativa é pouco legível;
    # nesses casos, a diferença absoluta conserva a interpretação da escala.
    relative = delta / before if delta is not None and before > 0 and unit != 'decimal' else None
    return dict(category=category, metric=metric, before=before, after=after,
                delta=delta, relativeChange=relative, unit=unit, status=status)


def _comparison(rows, baseline_period, note=''):
    return dict(baselinePeriod=baseline_period, currentPeriod=CURRENT_PERIOD, rows=rows, note=note)


def compare_summary(before, after, baseline_period):
    """Compara métricas de amostras de um semestre, nunca histórico acumulado."""
    before, after = (before or {}) if baseline_period else {}, after or {}
    return _comparison([
        _row('Total do semestre', name, before.get(key), after.get(key), unit)
        for key, name, unit in SUMMARY_METRICS
    ], baseline_period,
        'Cada coluna representa um semestre. Ocupação varia em pontos percentuais; '
        'a variação relativa não é definida com base zero. A oferta de 2026.2 ainda está aberta.')


def compare_statistics(before, after, baseline_period):
    before, after = (before or {}) if baseline_period else {}, after or {}
    fields = [
        ('occupancy', 'mean', 'Ocupação média por turma', 'percent'),
        ('occupancy', 'median', 'Mediana de ocupação', 'percent'),
        ('occupancy', 'q1', 'Primeiro quartil da ocupação', 'percent'),
        ('occupancy', 'q3', 'Terceiro quartil da ocupação', 'percent'),
        ('occupancy', 'standardDeviation', 'Desvio-padrão da ocupação', 'percent'),
        ('occupancy', 'iqr', 'Intervalo interquartil da ocupação', 'percent'),
        ('occupancy', 'mad', 'Desvio absoluto mediano da ocupação', 'percent'),
        ('occupancy', 'coefficientVariation', 'Coeficiente de variação', 'decimal'),
        ('occupancy', 'skewness', 'Assimetria', 'decimal'),
        ('occupancy', 'excessKurtosis', 'Excesso de curtose', 'decimal'),
        ('occupancy', 'outliersLow', 'Turmas abaixo da cerca de Tukey', 'number'),
        ('occupancy', 'outliersHigh', 'Turmas acima da cerca de Tukey', 'number'),
        ('concentration', 'disciplines', 'Disciplinas ofertadas', 'number'),
        ('concentration', 'gini', 'Gini das matrículas', 'decimal'),
        ('concentration', 'hhi', 'HHI', 'decimal'),
        ('concentration', 'effectiveDisciplines', 'Disciplinas efetivas (1/HHI)', 'decimal'),
        ('concentration', 'normalizedEntropy', 'Entropia normalizada', 'decimal'),
        ('concentration', 'top20Share', 'Parcela das 20% maiores disciplinas', 'percent'),
        ('association', 'pearson', 'Pearson: capacidade e ocupação', 'decimal'),
        ('association', 'spearman', 'Spearman: capacidade e ocupação', 'decimal'),
        ('association', 'rSquared', 'R² do ajuste descritivo', 'decimal'),
    ]
    return _comparison([
        _row('Estatísticas do semestre', name, before.get(section, {}).get(key),
             after.get(section, {}).get(key), unit)
        for section, key, name, unit in fields
    ], baseline_period, 'Os índices usam as distribuições de cada semestre. Diferenças são descritivas; '
        'índices e coeficientes são comparados na própria escala, sem variação relativa.')


def _category(value):
    """Categoria estável, sem posição, nome variável ou tamanho da amostra."""
    text = re.sub(r'^\s*\d+\.\s+', '', str(value)).strip()
    text = re.sub(r'\s*\(\d+ turmas?\)\s*$', '', text)
    text = re.sub(r'\s*·\s*\d+ turmas?\s*$', '', text)
    if re.fullmatch(r'\d{4}\.[12]\*?', text):
        return 'Total do semestre'
    code = re.match(r'^([A-Z]+\d+)\b', text)
    return code[1] if code else text


def _metric(value):
    text = str(value)
    names = {
        'm': 'Matrículas', 'c': 'Vagas ofertadas', 'n': 'Turmas',
        'rate': 'Ocupação', 'free': 'Vagas não preenchidas',
        'extra': 'Matrículas acima da capacidade', 'full': 'Turmas com ocupação de 100% ou mais',
        'low': 'Turmas abaixo de 25% de ocupação', 'periods': 'Semestres com oferta',
        'recurring_full': 'Semestres com ocupação de 100% ou mais',
        'recurring_low': 'Semestres abaixo de 25% de ocupação',
    }
    if text in names:
        return names[text]
    if _fold(text) in {'consolidadas', 'consolidadas ate 2026.1',
                       'abertas em 2026.2', 'abertas 2026.2', 'recorte selecionado'}:
        return 'Recorte selecionado'
    return text


def _unit(plot, metric=None):
    spec = plot.get('spec', {})
    if plot.get('rankingPercent') or spec.get('valueFormat', {}).get('style') == 'percent':
        return 'percent'
    if spec.get('valueFormat', {}).get('style') == 'decimal':
        return 'decimal'
    if any(word in _fold(metric or '') for word in ['gini', 'hhi', 'pearson', 'spearman', 'efetivo', 'r²']):
        return 'decimal'
    return 'number'


def _point_label(value, percent=False):
    if isinstance(value, Real):
        return f'{value * 100:g}%' if percent else f'{value:g}'
    return _category(value)


def _extract(plot):
    """Retorna {(categoria, métrica): (valor, unidade)} a partir dos eixos."""
    if not plot:
        return {}
    kind = plot.get('formato', plot.get('spec', {}).get('type'))
    records = plot.get('comparisonRecords')
    if records is not None:
        metric = _metric(plot.get('comparisonMetric', plot.get('title', 'Resultado')))
        return {(_category(r['label']), metric): (r['value'], _unit(plot, metric)) for r in records}
    if kind == 'ranking':
        return {(_category(row[0]), 'Resultado'): (value, _unit(plot))
                for row, value in zip(plot.get('rows', []), plot.get('rankingValues', []))}
    spec = plot.get('spec', {})
    columns = plot.get('columns', [])
    horizontal = kind == 'horizontalBar'
    dimensions = [spec.get('x'), spec.get('y')] if kind == 'heatmap' else [spec.get('y' if horizontal else 'x')]
    dimensions = [v for v in dimensions if isinstance(v, str)]
    raw_metrics = [spec.get('value')] if kind == 'heatmap' else spec.get('x' if horizontal else 'y', [])
    raw_metrics = [raw_metrics] if isinstance(raw_metrics, str) else raw_metrics
    result = {}
    for raw in plot.get('rows', []):
        row = dict(zip(columns, raw))
        categories = [_point_label(row.get(dim), spec.get('xValueFormat', {}).get('style') == 'percent')
                      for dim in dimensions if _fold(dim) not in {'semestre', 'periodo'}]
        category = ' · '.join(categories) or 'Total do semestre'
        for metric in raw_metrics or []:
            result[(category, _metric(metric))] = (row.get(metric), _unit(plot, metric))
    return result


def compare_plots(before, after, baseline_period):
    """Compara as medidas do gráfico por categoria e série compatível."""
    if not baseline_period:
        before = None
    plot = after or before or {}
    kind = plot.get('formato', plot.get('spec', {}).get('type'))
    if kind in {'scatter', 'bubble', 'statisticalScatter'} or plot.get('catalogKey') == 'cadeira-por-turma':
        return _comparison([], baseline_period,
            'Os pontos e as turmas não são as mesmas observações nos dois semestres. '
            'A comparação ponto a ponto não se aplica; consulte os indicadores do semestre e o gráfico de referência.')
    old, new = _extract(before), _extract(after)
    keys = list(dict.fromkeys([*new, *old]))
    rows = []
    for category, metric in keys:
        before_value, old_unit = old.get((category, metric), (None, None))
        after_value, new_unit = new.get((category, metric), (None, None))
        rows.append(_row(category, metric, before_value, after_value, new_unit or old_unit or 'number'))
    note = ('Diferença = 2026.2 menos o semestre de referência. Percentuais usam pontos percentuais. '
            'Sem valor indica ausência de categoria, oferta ou medida definida; não equivale a zero.')
    if kind in {'ranking', 'horizontalBar'}:
        note += ' Categorias fora de um ranking limitado não são tratadas como zero.'
    if plot.get('spec', {}).get('numericX'):
        # Não há interpolação de curvas ou preenchimento de limiares ausentes.
        note += ' As curvas só têm diferença nos mesmos valores do eixo horizontal; não há interpolação.'
    if any(_category(key[0]) == 'Outras' for key in keys):
        # O agrupamento de capacidades menos frequentes muda de composição.
        rows = [r for r in rows if r['category'] != 'Outras']
        note += ' O grupo Outras foi omitido da diferença porque sua composição pode variar entre semestres.'
    return _comparison(rows, baseline_period, note)


def _selected(summary):
    return (summary or {}).get('selected')


def attach_comparisons(current, baseline, baseline_period):
    """Acrescenta tabelas de diferenças sem modificar as medidas dos gráficos."""
    baseline = baseline or {'paineis': [], 'disciplines': {}}
    old_panels = {p['id']: p for p in baseline.get('paineis', [])}
    old_plots = {p['id']: p for panel in old_panels.values()
                 for section in panel.get('sections', []) for p in section.get('plots', [])}
    for panel in current.get('paineis', []):
        old_panel = old_panels.get(panel['id'], {})
        if 'summary' in panel:
            panel['summary']['comparison'] = compare_summary(_selected(old_panel.get('summary')),
                                                            _selected(panel['summary']), baseline_period)
        if 'statisticalSummary' in panel:
            panel['statisticalSummary']['comparison'] = compare_statistics(
                old_panel.get('statisticalSummary'), panel['statisticalSummary'], baseline_period)
        for section in panel.get('sections', []):
            for plot in section.get('plots', []):
                plot['comparison'] = compare_plots(old_plots.get(plot['id']), plot, baseline_period)
    # MC compartilha os objetos da lista CCT. Uma única passagem evita trabalho
    # duplicado e conserva o resultado em ambos os recortes.
    old_disciplines = {d['code']: d for d in baseline.get('disciplines', {}).get('cct', [])}
    for discipline in current.get('disciplines', {}).get('cct', []):
        old_discipline = old_disciplines.get(discipline['code'], {})
        discipline['summary']['comparison'] = compare_summary(_selected(old_discipline.get('summary')),
                                                              _selected(discipline['summary']), baseline_period)
        old_discipline_plots = {p['id']: p for p in old_discipline.get('plots', [])}
        for plot in discipline.get('plots', []):
            plot['comparison'] = compare_plots(old_discipline_plots.get(plot['id']), plot, baseline_period)
    return current

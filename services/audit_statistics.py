"""Recalcula as estatísticas sem usar as funções que produzem os gráficos.

O auditor usa statistics da biblioteca padrão, Gini por diferenças entre pares
e postos construídos por contagem, para não validar um cálculo com ele mesmo.
"""

from collections import Counter, defaultdict
from math import ceil, isclose, isfinite, log, sqrt
from statistics import StatisticsError, correlation, linear_regression, mean, median, pvariance, quantiles

from services.calc_metrics import codes


def _distribution(values):
    if not values:
        names = ('mean', 'median', 'q1', 'q3', 'iqr', 'variance', 'standardDeviation',
                 'mad', 'coefficientVariation', 'skewness', 'excessKurtosis',
                 'tukeyLower', 'tukeyUpper', 'outliersLow', 'outliersHigh')
        return dict.fromkeys(names) | {'n': 0}
    q1, _, q3 = quantiles(values, n=4, method='inclusive') if len(values) > 1 else [values[0]] * 3
    average, middle = mean(values), median(values)
    variance = pvariance(values)
    deviation, iqr = sqrt(variance), q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return dict(n=len(values), mean=average, median=middle, q1=q1, q3=q3, iqr=iqr,
                variance=variance, standardDeviation=deviation,
                mad=median([abs(x - middle) for x in values]),
                coefficientVariation=deviation / average if average else None,
                skewness=mean([(x - average) ** 3 for x in values]) / deviation ** 3 if deviation else None,
                excessKurtosis=mean([(x - average) ** 4 for x in values]) / deviation ** 4 - 3 if deviation else None,
                tukeyLower=lower, tukeyUpper=upper,
                outliersLow=sum(x < lower for x in values), outliersHigh=sum(x > upper for x in values))


def _association(rows):
    x = [r['capacidade'] for r in rows]
    y = [r['matriculas'] / r['capacidade'] for r in rows]
    def corr(a, b):
        if len(set(a)) < 2 or len(set(b)) < 2:
            return None
        try:
            return correlation(a, b)
        except StatisticsError:
            return None
    def ranks(values):
        counts = Counter(values)
        positions, offset = {}, 0
        for value in sorted(counts):
            positions[value] = offset + (counts[value] + 1) / 2
            offset += counts[value]
        return [positions[value] for value in values]
    pearson = corr(x, y)
    try:
        slope, intercept = linear_regression(x, y)
    except StatisticsError:
        slope = intercept = None
    return dict(pearson=pearson, spearman=corr(ranks(x), ranks(y)), slope=slope,
                intercept=intercept, rSquared=pearson ** 2 if pearson is not None else None)


def _concentration(rows):
    totals = defaultdict(int)
    for row in rows:
        totals[row['codigo']] += row['matriculas']
    values = list(totals.values())
    total, n = sum(values), len(values)
    if not total:
        return dict(disciplines=n, gini=None, hhi=None, effectiveDisciplines=None,
                    normalizedEntropy=None, top20Share=None)
    shares = [value / total for value in values]
    hhi = sum(p ** 2 for p in shares)
    # Definição por todas as diferenças, independente da fórmula de postos usada no painel.
    gini = sum(abs(a - b) for a in values for b in values) / (2 * n * total)
    return dict(disciplines=n, gini=gini, hhi=hhi, effectiveDisciplines=1 / hhi,
                normalizedEntropy=-sum(p * log(p) for p in shares if p) / log(n) if n > 1 else 0,
                top20Share=sum(sorted(values, reverse=True)[:ceil(n / 5)]) / total)


def _mismatch(actual, expected, path='valor'):
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return f'{path}: objeto ausente'
        for key, value in expected.items():
            error = _mismatch(actual.get(key), value, f'{path}.{key}')
            if error:
                return error
        return None
    if isinstance(expected, (list, tuple)):
        if not isinstance(actual, (list, tuple)) or len(actual) != len(expected):
            return f'{path}: tamanho recebido {len(actual) if isinstance(actual, (list, tuple)) else None}, esperado {len(expected)}'
        for i, (a, b) in enumerate(zip(actual, expected)):
            error = _mismatch(a, b, f'{path}[{i}]')
            if error:
                return error
        return None
    if expected is None:
        return None if actual is None else f'{path}: {actual!r}, esperado indefinido'
    if isinstance(expected, (int, float)):
        if isinstance(actual, (int, float)) and isfinite(actual) and isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12):
            return None
    elif actual == expected:
        return None
    return f'{path}: recebido {actual!r}; recalculado {expected!r}'


def _check(identifier, actual, expected):
    problem = _mismatch(actual, expected)
    def count(value):
        if isinstance(value, dict):
            return sum(count(v) for v in value.values())
        if isinstance(value, (list, tuple)):
            return sum(count(v) for v in value)
        return int(isinstance(value, (int, float)))
    return dict(id=identifier, passed=problem is None,
                details=problem or 'Conferido por cálculo independente a partir das turmas.',
                valuesChecked=count(expected))


def _expected(rows, periods):
    values = [r['matriculas'] / r['capacidade'] for r in rows]
    dist, conc, assoc = _distribution(values), _concentration(rows), _association(rows)
    groups = {p: [r for r in rows if r['periodo'] == p] for p in periods}
    groups = {p: rs for p, rs in groups.items() if rs}
    pd = {p: _distribution([r['matriculas'] / r['capacidade'] for r in rs]) for p, rs in groups.items()}
    pc = {p: _concentration(rs) for p, rs in groups.items()}
    pa = {p: _association(rs) for p, rs in groups.items()}
    totals = defaultdict(int)
    names = {}
    for row in rows:
        totals[row['codigo']] += row['matriculas']
        names[row['codigo']] = row['disciplina'].title()
    counts = Counter((r['capacidade'], r['matriculas'] / r['capacidade']) for r in rows)
    total = sum(totals.values())
    ordered = sorted(totals.values())
    cumulative = 0
    lorenz = [[0, 0, 0]] if total else []
    for i, value in enumerate(ordered, 1):
        cumulative += value
        if total:
            lorenz.append([i / len(ordered), cumulative / total, i / len(ordered)])
    histogram_labels = ['0% a <25%', '25% a <50%', '50% a <75%', '75% a <100%', '100% a <125%', '125% ou mais']
    # Intervalos explícitos, sem usar bisect do produtor.
    hist_counts = [sum(lo <= v < hi for v in values) for lo, hi in
                   [(0, .25), (.25, .5), (.5, .75), (.75, 1), (1, 1.25), (1.25, float('inf'))]]
    sd = dist['standardDeviation']
    result = {
        'histograma': [[label, hist_counts[i] / len(rows)] for i, label in enumerate(histogram_labels)] if rows else [],
        'quartis': [[p, d['q1'], d['median'], d['q3']] for p, d in pd.items()],
        'dispersao': [[p, d['coefficientVariation'], d['mad'] / d['median'] if d['median'] else None] for p, d in pd.items()],
        'momentos': [[p, d['skewness'], d['excessKurtosis']] for p, d in pd.items()],
        'tukey': [[p, d['outliersLow'], d['outliersHigh']] for p, d in pd.items()],
        'acumulada': [[t, sum(v <= t for v in values) / len(rows)] for t in sorted({0, *values})] if rows else [],
        'lorenz': lorenz,
        'concentracao': [[p, c['gini'], c['hhi']] for p, c in pc.items()],
        'diversidade': [[p, c['disciplines'], c['effectiveDisciplines']] for p, c in pc.items()],
        'participacao': [[f'{code} · {names[code]}', amount / total] for code, amount in
                         sorted(totals.items(), key=lambda pair: (-pair[1], pair[0]))[:10]] if total else [],
        'correlacoes': [[p, a['pearson'], a['spearman']] for p, a in pa.items()],
        'regressao': [[capacity, occupancy, count, f'{capacity} vagas · {occupancy:.1%} de ocupação'.replace('.', ',')]
                     for (capacity, occupancy), count in sorted(counts.items())],
        'markov': [[t, sum(v >= t for v in values) / len(rows), min(1, dist['mean'] / t)]
                   for t in [.25, .5, .75, 1, 1.25, 1.5, 2]] if rows else [],
        'chebyshev': [[k, sum(abs(v - dist['mean']) < k * sd for v in values) / len(rows) if sd else 1, 1 - 1 / k ** 2]
                      for k in [1.5, 2, 2.5, 3, 4]] if rows else [],
    }
    return dict(occupancy=dist, concentration=conc, association=assoc, open=_distribution([])), result


def audit_statistics(offers, views):
    """Confere resumos, todas as linhas e ajustes dos gráficos estatísticos.

    ``offers`` recebe registros já normalizados; ``views`` deve incluir as views
    historical/current/baseline/accumulated antes da remoção da referência no payload web.
    """
    checks = []
    mc = codes('Matemática Computacional') | codes('Matemática Computacional', 2)
    for view_name in ('historical', 'current', 'baseline', 'accumulated'):
        view = views.get(view_name)
        if view is None:
            continue
        scope = view['scope']
        def selected(row):
            if scope['status'] == 'MISTA':
                return '2023.1' <= row['periodo'] <= '2026.2' and (row['situacao'] == 'CONSOLIDADA' and row['periodo'] < '2026.2' or row['situacao'] == 'ABERTA' and row['periodo'] == '2026.2')
            return row['situacao'] == scope['status']
        scoped = [r for r in offers if r['modalidade'] == 'Presencial' and r['capacidade'] > 0
                  and selected(r) and r['periodo'] in scope['periods']]
        for prefix, panel_id, sample in [('ufca', 'ufca-estatistica', scoped),
                                        ('matcomp', 'matematica-computacional', [r for r in scoped if r['codigo'] in mc])]:
            panel = next((p for p in view['paineis'] if p['id'] == panel_id), None)
            label = f'{view_name}/{prefix}/estatisticas'
            if panel is None:
                checks.append(dict(id=label, passed=False, details='Painel estatístico ausente.'))
                continue
            summary, expected_plots = _expected(sample, scope['periods'])
            checks.append(_check(f'{label}/resumo', panel.get('statisticalSummary'), summary))
            actual = {p['id']: p for section in panel['sections'] for p in section['plots']}
            for key, rows in expected_plots.items():
                identifier = f'{prefix}-estat-{key}'
                plot = actual.get(identifier)
                checks.append(_check(f'{view_name}/plot/{identifier}', plot.get('rows') if plot else None, rows))
                if key == 'regressao' and plot:
                    checks.append(_check(f'{view_name}/plot/{identifier}/ajuste', plot['spec'].get('trend'),
                                         {k: summary['association'][k] for k in ('slope', 'intercept', 'rSquared')}))
    return checks

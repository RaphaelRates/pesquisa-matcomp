"""Estatísticas descritivas da distribuição empírica de turmas."""

from bisect import bisect_right
from collections import Counter, defaultdict
from math import ceil, fsum, log, sqrt
from statistics import mean, pvariance


PERCENT = {"style": "percent"}
DECIMAL = {"style": "decimal", "maximumFractionDigits": 3}


def quantile(values, probability):
    """Interpolação linear inclusiva, posição (n - 1) p, também chamada tipo 7."""
    ordered = sorted(values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def distribution_statistics(values):
    values = list(values)
    n = len(values)
    if not n:
        return dict.fromkeys(
            ("mean", "median", "q1", "q3", "iqr", "variance", "standardDeviation",
             "mad", "coefficientVariation", "skewness", "excessKurtosis",
             "tukeyLower", "tukeyUpper", "outliersLow", "outliersHigh"), None
        ) | {"n": 0}
    average = mean(values)
    middle = quantile(values, .5)
    q1, q3 = quantile(values, .25), quantile(values, .75)
    iqr = q3 - q1
    # A variância da biblioteca padrão usa somas exatas intermediárias. Evita
    # inventar dispersão quando uma ocupação como 0,1 se repete em todas as turmas.
    variance = pvariance(values)
    deviation = sqrt(variance)
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return {
        "n": n, "mean": average, "median": middle, "q1": q1, "q3": q3, "iqr": iqr,
        "variance": variance, "standardDeviation": deviation,
        "mad": quantile([abs(value - middle) for value in values], .5),
        "coefficientVariation": deviation / average if average else None,
        "skewness": fsum(((value - average) / deviation) ** 3 for value in values) / n if deviation else None,
        "excessKurtosis": fsum(((value - average) / deviation) ** 4 for value in values) / n - 3 if deviation else None,
        "tukeyLower": lower, "tukeyUpper": upper,
        "outliersLow": sum(value < lower for value in values),
        "outliersHigh": sum(value > upper for value in values),
    }


def mean_ranks(values):
    ordered = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and values[ordered[end]] == values[ordered[start]]:
            end += 1
        rank = (start + 1 + end) / 2
        for index in ordered[start:end]:
            ranks[index] = rank
        start = end
    return ranks


def pearson(x, y):
    if len(x) < 2 or len(set(x)) < 2 or len(set(y)) < 2:
        return None
    mean_x, mean_y = mean(x), mean(y)
    xx = fsum((value - mean_x) ** 2 for value in x)
    yy = fsum((value - mean_y) ** 2 for value in y)
    if not xx or not yy:
        return None
    xy = fsum((a - mean_x) * (b - mean_y) for a, b in zip(x, y, strict=True))
    return max(-1.0, min(1.0, xy / sqrt(xx * yy)))


def association_statistics(rows):
    x = [row["capacidade"] for row in rows]
    y = [row["matriculas"] / row["capacidade"] for row in rows]
    linear = pearson(x, y)
    rank = pearson(mean_ranks(x), mean_ranks(y))
    slope = intercept = None
    if len(x) > 1:
        mean_x, mean_y = mean(x), mean(y)
        denominator = fsum((value - mean_x) ** 2 for value in x)
        if denominator:
            slope = fsum((a - mean_x) * (b - mean_y) for a, b in zip(x, y, strict=True)) / denominator
            intercept = mean_y - slope * mean_x
    return {
        "pearson": linear, "spearman": rank, "slope": slope, "intercept": intercept,
        "rSquared": linear ** 2 if linear is not None else None,
    }


def concentration_statistics(rows):
    by_code = defaultdict(int)
    for row in rows:
        by_code[row["codigo"]] += row["matriculas"]
    values = sorted(by_code.values())
    n, total = len(values), sum(values)
    if not n or not total:
        return {
            "disciplines": n, "gini": None, "hhi": None, "effectiveDisciplines": None,
            "normalizedEntropy": None, "top20Share": None,
        }
    shares = [value / total for value in values]
    hhi = fsum(share ** 2 for share in shares)
    gini = fsum((2 * index - n - 1) * value for index, value in enumerate(values, 1)) / (n * total)
    entropy = -fsum(share * log(share) for share in shares if share)
    return {
        "disciplines": n, "gini": gini, "hhi": hhi, "effectiveDisciplines": 1 / hhi,
        "normalizedEntropy": entropy / log(n) if n > 1 else 0.0,
        "top20Share": sum(sorted(values, reverse=True)[:ceil(n * .2)]) / total,
    }


def statistical_panel(prefix, title, hist, latest, periods):
    """Monta 14 gráficos e um resumo, sem inferir uma população externa à base."""
    from services.calc_metrics import chart

    def rates(rows):
        return [row["matriculas"] / row["capacidade"] for row in rows]

    def percent(value):
        return "Sem registro" if value is None else f"{value:.1%}".replace(".", ",")

    def percentage_points(value):
        return "Sem registro" if value is None else f'{value * 100:.1f}'.replace(".", ",") + " p.p."

    def plot(key, name, description, spec, columns, rows, method, interpretation, tooltips=None):
        return chart(f"{prefix}-estat-{key}", name, description, spec, columns, rows, tooltips=tooltips) | {
            "method": method, "interpretation": interpretation, "scope": "Turmas consolidadas",
        }

    by_period = defaultdict(list)
    for row in hist:
        by_period[row["periodo"]].append(row)
    historical_periods = [period for period in periods if by_period[period]]
    by_period_stats = {period: distribution_statistics(rates(by_period[period])) for period in historical_periods}
    by_period_concentration = {period: concentration_statistics(by_period[period]) for period in historical_periods}
    by_period_association = {period: association_statistics(by_period[period]) for period in historical_periods}
    historical = distribution_statistics(rates(hist))
    opened = distribution_statistics(rates(latest))
    concentration = concentration_statistics(hist)
    association = association_statistics(hist)
    note = "Somente turmas presenciais consolidadas."
    population_note = (
        "A variável é a ocupação de uma turma escolhida com igual probabilidade entre as turmas consolidadas "
        "observadas. A média e a variância usam essa distribuição empírica."
    )
    row_details = [
        f'{by_period_stats[period]["n"]} turmas\n'
        f'Média aritmética: {percent(by_period_stats[period]["mean"])}\n'
        f'Desvio-padrão: {percentage_points(by_period_stats[period]["standardDeviation"])}'
        for period in historical_periods
    ]
    distribution_plots = []

    bounds = [0, .25, .5, .75, 1, 1.25]
    histogram_labels = ["0% a <25%", "25% a <50%", "50% a <75%", "75% a <100%", "100% a <125%", "125% ou mais"]
    hist_counts = Counter(min(bisect_right(bounds, value) - 1, 5) for value in rates(hist))
    open_counts = Counter(min(bisect_right(bounds, value) - 1, 5) for value in rates(latest))
    histogram_rows = [
        [label, hist_counts[index] / len(hist) if hist else None, open_counts[index] / len(latest) if latest else None]
        for index, label in enumerate(histogram_labels)
    ]
    distribution_plots.append(plot(
        "histograma", "Distribuição detalhada da ocupação",
        "Compara as proporções de turmas consolidadas e abertas em 2026.2 em seis intervalos de ocupação.",
        dict(type="bar", x="Intervalo", y=["Consolidadas", "Abertas em 2026.2"], valueFormat=PERCENT),
        ["Intervalo", "Consolidadas", "Abertas em 2026.2"], histogram_rows,
        "Histograma com classes de largura de 25 pontos percentuais e uma última classe aberta.",
        "O formato evidencia onde as turmas se concentram. Cada série é dividida pelo seu próprio total.",
        [f"Consolidadas: {hist_counts[i]} de {len(hist)}\nAbertas: {open_counts[i]} de {len(latest)}"
         for i in range(len(histogram_labels))],
    ) | {"scope": "Consolidadas e abertas de 2026.2, em séries separadas"})
    distribution_plots.append(plot(
        "quartis", "Faixa central de ocupação por semestre", note,
        dict(type="distributionBand", x="Semestre", y=["Q1", "Mediana", "Q3"], valueFormat=PERCENT),
        ["Semestre", "Q1", "Mediana", "Q3"],
        [[period, stats["q1"], stats["median"], stats["q3"]] for period, stats in by_period_stats.items()],
        "Quartis por interpolação linear inclusiva, posição (n − 1)p. A faixa entre Q1 e Q3 representa os 50% centrais.",
        "Faixas largas indicam maior dispersão da ocupação entre as turmas do semestre.", row_details,
    ))
    distribution_plots.append(plot(
        "dispersao", "Dispersão relativa da ocupação", note,
        dict(type="line", x="Semestre", y=["Coeficiente de variação", "MAD / mediana"], valueFormat=PERCENT),
        ["Semestre", "Coeficiente de variação", "MAD / mediana"],
        [[period, stats["coefficientVariation"], stats["mad"] / stats["median"] if stats["median"] else None]
         for period, stats in by_period_stats.items()],
        "CV = desvio-padrão populacional / média. MAD é a mediana dos desvios absolutos em relação à mediana.",
        "Os índices comparam dispersão com o nível central. Denominadores iguais a zero deixam o índice sem registro.",
        row_details,
    ))
    distribution_plots.append(plot(
        "momentos", "Assimetria e caudas da ocupação", note,
        dict(type="line", x="Semestre", y=["Assimetria", "Curtose excedente"], valueFormat=DECIMAL),
        ["Semestre", "Assimetria", "Curtose excedente"],
        [[period, stats["skewness"], stats["excessKurtosis"]] for period, stats in by_period_stats.items()],
        "Momentos padronizados populacionais de ordem 3 e 4. A curtose excedente subtrai 3 do quarto momento.",
        "Assimetria positiva indica cauda à direita. A curtose descreve extremos relativos ao desvio-padrão, "
        "sem estabelecer normalidade dos dados.", row_details,
    ))
    distribution_plots.append(plot(
        "tukey", "Turmas sinalizadas pela regra de Tukey", note,
        dict(type="stackedBar", x="Semestre", y=["Abaixo do limite", "Acima do limite"]),
        ["Semestre", "Abaixo do limite", "Acima do limite"],
        [[period, stats["outliersLow"], stats["outliersHigh"]] for period, stats in by_period_stats.items()],
        "Sinaliza valores abaixo de Q1 − 1,5 × IQR ou acima de Q3 + 1,5 × IQR, com IQR = Q3 − Q1.",
        "São observações para inspeção. O sinalizador preserva todas as turmas nos indicadores.",
        [f'Limite inferior: {percent(stats["tukeyLower"])}\nLimite superior: {percent(stats["tukeyUpper"])}\n'
         f'IQR: {percentage_points(stats["iqr"])}\nTurmas analisadas: {stats["n"]}'
         for stats in by_period_stats.values()],
    ))
    sorted_hist, sorted_open = sorted(rates(hist)), sorted(rates(latest))
    ecdf_thresholds = sorted({0, *sorted_hist, *sorted_open})
    distribution_plots.append(plot(
        "acumulada", "Distribuição acumulada da ocupação",
        "Compara a proporção de turmas com ocupação menor ou igual a cada valor do eixo horizontal.",
        dict(type="line", x="Ocupação", y=["Consolidadas", "Abertas em 2026.2"], numericX=True,
             xValueFormat=PERCENT, valueFormat=PERCENT, stepped="before", yDomain=[0, 1]),
        ["Ocupação", "Consolidadas", "Abertas em 2026.2"],
        [[threshold, bisect_right(sorted_hist, threshold) / len(hist) if hist else None,
          bisect_right(sorted_open, threshold) / len(latest) if latest else None] for threshold in ecdf_thresholds]
        if hist or latest else [],
        "Função de distribuição empírica F(t) = número de turmas com ocupação ≤ t / total de turmas do recorte.",
        "Uma curva mais alta em um limiar significa maior parcela de turmas com ocupação até esse valor.",
    ) | {"scope": "Consolidadas e abertas de 2026.2, em séries separadas"})

    by_code = defaultdict(int)
    for row in hist:
        by_code[row["codigo"]] += row["matriculas"]
    ordered_values = sorted(by_code.values())
    total = sum(ordered_values)
    lorenz_rows = [[0, 0, 0]] if total else []
    cumulative = 0
    for i, amount in enumerate(ordered_values, 1):
        cumulative += amount
        if total:
            share = i / len(ordered_values)
            lorenz_rows.append([share, cumulative / total, share])
    concentration_plots = [plot(
        "lorenz", "Concentração das matrículas entre disciplinas", note,
        dict(type="line", x="Parcela das disciplinas", y=["Matrículas acumuladas", "Igualdade"], numericX=True,
             xValueFormat=PERCENT, valueFormat=PERCENT, yDomain=[0, 1]),
        ["Parcela das disciplinas", "Matrículas acumuladas", "Igualdade"], lorenz_rows,
        "Curva de Lorenz com os códigos ordenados do menor para o maior total de matrículas, incluindo códigos com zero.",
        "Quanto maior a distância até a diagonal, maior a desigualdade entre os totais de matrículas dos códigos.",
    )]
    concentration_plots.append(plot(
        "concentracao", "Índices de concentração por semestre", note,
        dict(type="line", x="Semestre", y=["Gini", "HHI"], valueFormat=DECIMAL, yDomain=[0, 1]),
        ["Semestre", "Gini", "HHI"],
        [[period, values["gini"], values["hhi"]] for period, values in by_period_concentration.items()],
        "Gini é calculado sobre os totais por código. HHI = soma dos quadrados das participações nas matrículas, "
        "na escala de 0 a 1.",
        "Os índices descrevem concentração com fórmulas diferentes. O número de disciplinas ofertadas também "
        "influencia o resultado.", row_details,
    ))
    concentration_plots.append(plot(
        "diversidade", "Disciplinas ofertadas e diversidade efetiva", note,
        dict(type="mixed", x="Semestre", y=["Disciplinas ofertadas", "Número efetivo (HHI)"],
             lineSeries=["Número efetivo (HHI)"]),
        ["Semestre", "Disciplinas ofertadas", "Número efetivo (HHI)"],
        [[period, values["disciplines"], values["effectiveDisciplines"]]
         for period, values in by_period_concentration.items()],
        "O número efetivo é 1 / HHI. Ele representa quantas disciplinas de participação igual produziriam o mesmo HHI.",
        "Uma distância grande entre as duas séries indica concentração das matrículas em parte dos códigos ofertados.",
        row_details,
    ))
    top_codes = sorted(by_code.items(), key=lambda pair: (-pair[1], pair[0]))[:10]
    names = {row["codigo"]: row["disciplina"].title() for row in hist}
    concentration_plots.append(plot(
        "participacao", "Participação das dez maiores disciplinas nas matrículas", note,
        dict(type="horizontalBar", y="Disciplina", x="Parcela das matrículas", valueFormat=PERCENT, xDomain=[0, 1]),
        ["Disciplina", "Parcela das matrículas"],
        [[f"{code} · {names[code]}", amount / total] for code, amount in top_codes] if total else [],
        "Participação de cada código no total de matrículas das turmas consolidadas do recorte.",
        "As barras mostram contribuições individuais. As demais disciplinas completam o total de matrículas.",
        [f"{amount} de {total} matrículas" for _, amount in top_codes] if total else [],
    ))

    points = Counter((row["capacidade"], row["matriculas"] / row["capacidade"]) for row in hist)
    association_plots = [plot(
        "correlacoes", "Relação entre capacidade e ocupação por semestre", note,
        dict(type="line", x="Semestre", y=["Pearson", "Spearman"], valueFormat=DECIMAL, yDomain=[-1, 1]),
        ["Semestre", "Pearson", "Spearman"],
        [[period, values["pearson"], values["spearman"]] for period, values in by_period_association.items()],
        "Pearson usa os valores originais. Spearman aplica Pearson aos postos médios, preservando os empates.",
        "Valores próximos de ±1 indicam associação forte, linear em Pearson e monotônica em Spearman. "
        "A associação observada permite descrever relações, sem identificar suas causas.", row_details,
    )]
    association_plots.append(plot(
        "regressao", "Capacidade e ocupação com ajuste descritivo", note,
        dict(type="statisticalScatter", x="Capacidade", y="Ocupação", size="Turmas", label="Combinação",
             valueFormat=PERCENT, xValueFormat=DECIMAL, trend={
                 "slope": association["slope"], "intercept": association["intercept"],
                 "rSquared": association["rSquared"],
             }),
        ["Capacidade", "Ocupação", "Turmas", "Combinação"],
        [[capacity, occupancy, count, f"{capacity} vagas · {percent(occupancy)} de ocupação"]
         for (capacity, occupancy), count in sorted(points.items())],
        "A reta minimiza a soma dos resíduos ao quadrado usando cada turma como uma observação. "
        "Pontos iguais são agrupados apenas para desenhar.",
        "R² descreve a fração da variação de ocupação associada ao ajuste linear nesta base. "
        "A reta não é uma previsão de matrículas futuras.",
        [f"Turmas com essa combinação: {count}\nPearson: "
         f'{association["pearson"]:.3f}' if association["pearson"] is not None else
         f"Turmas com essa combinação: {count}\nCorrelação sem variação suficiente."
         for _, count in sorted(points.items())],
    ))

    thresholds = [.25, .5, .75, 1, 1.25, 1.5, 2]
    limit_plots = [plot(
        "markov", "Ocupação acima de um limiar e limite de Markov", note,
        dict(type="line", x="Limiar de ocupação", y=["Parcela observada", "Limite superior de Markov"],
             numericX=True, xValueFormat=PERCENT, valueFormat=PERCENT, yDomain=[0, 1]),
        ["Limiar de ocupação", "Parcela observada", "Limite superior de Markov"],
        [[threshold, sum(value >= threshold for value in sorted_hist) / len(hist),
          min(1, historical["mean"] / threshold)] for threshold in thresholds] if hist else [],
        f"Desigualdade de Markov para valores não negativos. P(X ≥ t) ≤ média / t, com t > 0. {population_note}",
        "O limite superior é uma garantia matemática sobre a distribuição empírica e pode ser pouco restritivo. "
        "A curva observada permite verificar a distância até essa garantia.",
    )]
    multipliers = [1.5, 2, 2.5, 3, 4]
    deviation = historical["standardDeviation"]
    limit_plots.append(plot(
        "chebyshev", "Concentração em torno da média e limite de Chebyshev", note,
        dict(type="line", x="Múltiplo do desvio-padrão", y=["Parcela observada", "Mínimo de Chebyshev"],
             numericX=True, valueFormat=PERCENT, yDomain=[0, 1]),
        ["Múltiplo do desvio-padrão", "Parcela observada", "Mínimo de Chebyshev"],
        [[k, sum(abs(value - historical["mean"]) < k * deviation for value in sorted_hist) / len(hist)
          if deviation else 1, 1 - 1 / k ** 2] for k in multipliers] if hist else [],
        "Para σ > 0, P(|X − média| < kσ) ≥ 1 − 1/k², com k > 1. "
        f"A variância é populacional, com divisor n. {population_note}",
        "Com dois desvios-padrão, o limite garante pelo menos 75% das turmas dentro da faixa. "
        "Quando σ = 0, todas as ocupações coincidem e a parcela observada é 100%, por esse caso degenerado.",
        [f'Média: {percent(historical["mean"])}\nDesvio-padrão: {percentage_points(deviation)}\n'
         f'Raio da faixa: {percentage_points(k * deviation)}' for k in multipliers] if hist else [],
    ))
    return {
        "id": f"{prefix}-estatistica", "title": title,
        "description": "Estatísticas descritivas, concentração e associações das turmas consolidadas. "
                       "As abertas de 2026.2 aparecem em séries próprias nas comparações de distribuição. "
                       "Os resultados descrevem a base observada.",
        "statisticalSummary": {
            "scope": "Turmas consolidadas", "occupancy": historical, "open": opened,
            "concentration": concentration, "association": association,
        },
        "sections": [
            {"title": "Distribuição e robustez", "plots": distribution_plots},
            {"title": "Concentração e diversidade", "plots": concentration_plots},
            {"title": "Associações e ajuste", "plots": association_plots},
            {"title": "Limites matemáticos", "plots": limit_plots},
        ],
    }

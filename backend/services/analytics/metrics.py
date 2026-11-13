"""Cálculos dos gráficos a partir dos registros individuais de turma."""


from collections import Counter, defaultdict
from fractions import Fraction
import re
from statistics import median
from services.analytics.statistics import statistical_panel
from services.data.selection import split_offers
from services.domain.courses import COURSES, curriculum
from services.domain.ppcs import PPCS
from services.domain.curricula import sources, current, codes, all_opt, all_required, cc_old, cc_new, changed, opt_only, req_only


timere = re.compile(r"\b(SEG|TER|QUA|QUI|SEX|SÁB|SAB|DOM) (\d{2}):(\d{2})-(\d{2}):(\d{2})")
days = dict(SEG="Seg",TER="Ter",QUA="Qua",QUI="Qui",SEX="Sex",SAB="Sáb",DOM="Dom")


def hourly_slots(row, hours):
    return {
        ("SAB" if day == "SÁB" else day, hour)
        for day, sh, sm, eh, em in timere.findall(row["horario"])
        for hour in hours
        if int(sh)*60 + int(sm) < (hour + 1)*60 and int(eh)*60 + int(em) > hour*60
    }

def group(rows, key):
    result = defaultdict(list)
    for r in rows:
        result[key(r)].append(r)
    return result

def rate(r):
    return r["matriculas"] / r["capacidade"]

def metrics(rows):
    m = sum(r["matriculas"] for r in rows)
    c = sum(r["capacidade"] for r in rows)
    return dict(n=len(rows), m=m, c=c, rate=m/c if c else None,
                full=sum(rate(r) >= 1 for r in rows),
                over=sum(rate(r) > 1 for r in rows),
                low=sum(rate(r) < .25 for r in rows),
                zero=sum(r["matriculas"] == 0 for r in rows),
                free=sum(max(r["capacidade"]-r["matriculas"],0) for r in rows),
                extra=sum(max(r["matriculas"]-r["capacidade"],0) for r in rows))


def shift(r):
    slots = timere.findall(r["horario"])
    categories = set()
    for _, sh, sm, eh, em in slots:
        start, end = int(sh)*60+int(sm), int(eh)*60+int(em)
        for label, lo, hi in [("Manhã",0,720), ("Tarde",720,1080), ("Noite",1080,1440)]:
            if start < hi and end > lo:
                categories.add(label)
    return next(iter(categories)) if len(categories) == 1 else "Misto" if categories else "Sem horário"


def select(rows, allowed):
    return [r for r in rows if r["codigo"] in allowed]


def semester_label(period, rows):
    return f'{period}*' if any(row['situacao'] == 'ABERTA' for row in rows) else period


notes = {
    "ufca-capacidade-matriculas": "Cada par de barras compara a soma das vagas informadas com a soma das matrículas registradas nas turmas presenciais de um semestre. As barras mostram totais absolutos. O asterisco identifica semestres que incluem turmas abertas.",
    "ufca-faixas": "Cada segmento conta quantas turmas ficaram em uma faixa de ocupação. A faixa de cada turma é definida pelas suas matrículas divididas pela sua capacidade. A altura total da barra é o número de turmas presenciais do semestre. O segmento de 100% ou mais inclui turmas lotadas e acima da capacidade. O asterisco identifica semestres que incluem turmas abertas.",
    "ufca-prefixos": "Cada célula cruza um prefixo de código, como EM ou ECI, com um semestre. A cor e o percentual mostram a soma das matrículas dividida pela soma das vagas nas turmas presenciais consolidadas daquele prefixo e semestre. A unidade de agrupamento é o prefixo da disciplina.",
    "ufca-codigos": "Cada linha acompanha um dos oito códigos selecionados. Em cada semestre, a célula soma matrículas e capacidade de todas as turmas incluídas daquele código e mostra a razão em porcentagem. Uma célula vazia indica ausência de turma no recorte. O asterisco identifica semestres que incluem turmas abertas.",
    "ufca-grade-horaria": "Cada célula conta as turmas com aula naquele dia da semana e naquela faixa de uma hora. A mesma turma aparece em todas as faixas em que tem aula. Consulte a célula para ver a contagem por semestre.",
    "ufca-turnos": "Cada barra divide o total de matrículas pelo total de vagas das turmas presenciais consolidadas classificadas naquele turno. Aulas antes das 12h entram na manhã, das 12h às 18h na tarde e a partir das 18h na noite. Turmas com aulas em mais de um turno entram em Misto. O rótulo informa o número de turmas.",
    "ufca-opt-curso": "Para cada curso, o gráfico seleciona os códigos listados como optativos na matriz pública de referência. A ocupação divide as matrículas pelas vagas das turmas selecionadas.",
    "ufca-opt-periodo": "Em cada semestre, as duas barras mostram a ocupação de optativas e obrigatórias presenciais consolidadas, calculada separadamente pela soma de matrículas dividida pela soma de vagas. O recorte original exclui códigos sem classificação ou com mudança de natureza conhecida e usa as matrizes de referência dessa análise.",
}

ranking = [
    ["Soma as matrículas registradas em todas as turmas de cada código. A ordem vai do maior para o menor total.",
     "Soma a capacidade cadastrada de todas as turmas de cada código, incluindo as vagas preenchidas e as que sobraram.",
     "Ordena os códigos pela maior razão entre matrículas e vagas acumuladas. O rótulo mostra a porcentagem e os dois totais usados.",
     "Ordena os códigos pela menor razão entre matrículas e vagas acumuladas. O rótulo mostra a porcentagem e os dois totais usados.",
     "Soma, para cada código, quantas matrículas excederam a capacidade em cada turma superlotada. Sobras em outras turmas não reduzem esse total.",
     "Soma, para cada código, as vagas que sobraram em cada turma. Matrículas excedentes em outras turmas não reduzem esse total.",
     "Soma matrículas e vagas por código em cada semestre. Depois conta em quantos semestres a ocupação desse código chegou a 100% ou mais.",
     "Soma matrículas e vagas por código em cada semestre. Depois conta em quantos semestres a ocupação desse código ficou abaixo de 25%.",
     "Conta os semestres distintos em que cada código teve turma no recorte. Duas ou mais turmas no mesmo semestre contam uma vez.",
     "Conta cada turma ofertada de um código. Duas ou mais turmas do mesmo código no mesmo semestre entram separadamente."],
    ["Ordena os semestres pela razão entre o total de matrículas e o total de vagas nas turmas do grupo.",
     "Ordena os semestres pela soma das matrículas registradas nas turmas do grupo.",
     "Conta, em cada semestre, as turmas com matrículas iguais ou superiores à capacidade. A comparação é feita turma a turma.",
     "Conta, em cada semestre, as turmas com menos de uma matrícula para cada quatro vagas. A comparação é feita turma a turma."],
    ["Ordena as combinações de dia da semana e intervalo de uma hora pelo número de turmas com aula naquele horário. Uma turma pode aparecer em mais de uma faixa.",
     "Divide matrículas por vagas dentro de cada turno. Turmas com aulas em mais de um turno entram em Misto. O rótulo mostra o número de turmas.",
     "Agrupa as turmas pelas letras iniciais do código da disciplina. Cada percentual usa as matrículas e vagas de todas as turmas daquele prefixo no recorte.",
     "Agrupa as turmas pelos códigos que constam na matriz de cada curso e divide matrículas por vagas. Códigos compartilhados podem aparecer em mais de um curso.",
     "Compara turmas com capacidade cadastrada de 20, 25, 30, 40 ou 50 vagas. Cada percentual divide as matrículas pelo total de vagas das turmas daquele tamanho."],
    ["Soma as matrículas das turmas abertas por código e mostra os maiores totais.",
     "Mostra os maiores percentuais de ocupação por código entre as turmas abertas. O rótulo informa a porcentagem e os totais de matrículas e vagas.",
     "Soma as vagas que sobraram em cada turma aberta, agrupadas por código. Turmas acima da capacidade contribuem com zero para esse total.",
     "Mostra os menores percentuais de ocupação por código entre as turmas abertas. O rótulo informa a porcentagem e os totais de matrículas e vagas."],
]


def chart(id, title, description, spec, columns, rows, height=300, tooltips=None):
    assert all(len(row) == len(columns) for row in rows)
    assert tooltips is None or len(tooltips) == len(rows)
    return dict(id=id, title=title, description=description, spec=spec,
                columns=columns, rows=rows, height=height, tooltips=tooltips)


def occupancy_details(m, include_rate=True):
    if not m["n"]:
        return ""
    totals = f'Turmas: {integer(m["n"])} · Matrículas: {integer(m["m"])} · Vagas: {integer(m["c"])}'
    return f'{totals}\nOcupação: {percent(m["rate"])}' if include_rate else totals


def schedule_heatmap(id, title, description, rows, *, hour_label, by_class=False):
    hours = range(7, 22)
    labels = [f'{hour:02d}h' for hour in hours]
    slots = defaultdict(list)
    scheduled = 0
    for row in rows:
        class_slots = hourly_slots(row, hours)
        scheduled += bool(class_slots)
        for slot in class_slots:
            slots[slot].append(row)

    values, details = [], []
    for day, label in days.items():
        for hour, hour_name in zip(hours, labels, strict=True):
            classes = slots[day, hour]
            values.append([label, hour_name, len(classes)])
            if by_class:
                ordered = sorted(classes, key=lambda row: (row['periodo'], row['turma']))
                details.append('\n'.join(
                    f"{semester_label(row['periodo'], [row])} · {row['turma']}" for row in ordered))
            else:
                by_period = group(classes, lambda row: row['periodo'])
                details.append('\n'.join(
                    f'{semester_label(period, sample)} · {integer(len(sample))}'
                    for period, sample in sorted(by_period.items())))
    plot = chart(id, title, description,
                 dict(type='heatmap', x='Dia', y=hour_label, value='Turmas',
                      xOrder=list(days.values()), yOrder=labels),
                 ['Dia', hour_label, 'Turmas'], values if rows else [], 520,
                 tooltips=details if rows else [])
    plot['scopeDetail'] = f'{integer(len(rows))} turmas no recorte · {integer(scheduled)} com horário no mapa.'
    return plot


def offer_indicators(prefix, by_period):
    semester = "Semestre"
    period_data = [
        (semester_label(p, rows), metrics(rows), len({r["codigo"] for r in rows}))
        for p, rows in sorted(by_period.items()) if rows
    ]
    note = "O asterisco identifica semestres que incluem turmas abertas."
    result = []
    for slug, title, description, series, values in [
        ("turmas", "Turmas e disciplinas ofertadas", "Cada código de disciplina é contado uma vez por semestre.",
         ["Turmas", "Disciplinas"], lambda m, distinct: [m["n"], distinct]),
        ("saldo", "Vagas não preenchidas e matrículas acima da capacidade",
         "Os dois totais são calculados turma a turma e somados separadamente.",
         ["Vagas não preenchidas", "Matrículas acima da capacidade"], lambda m, _: [m["free"], m["extra"]]),
        ("ocupacao", "Ocupação geral por semestre", "Divide o total de matrículas pelo total de vagas.",
         ["Ocupação"], lambda m, _: [m["rate"]]),
        ("extremos", "Percentual de turmas com baixa ocupação ou lotadas",
         "Mostra a parcela de turmas abaixo de 25% e a parcela com ocupação de 100% ou mais.",
         ["Abaixo de 25%", "100% ou mais"], lambda m, _: [m["low"] / m["n"], m["full"] / m["n"]]),
    ]:
        rows = [[period, *values(m, distinct)] for period, m, distinct in period_data]
        spec = dict(type="bar", x=semester, y=series)
        if slug == "turmas":
            spec.update(type="mixed", lineSeries=["Disciplinas"])
        if slug in {"ocupacao", "extremos"}:
            maximum = max((max(row[1:]) for row in rows), default=0)
            spec.update(valueFormat={"style": "percent"}, yLabel="Percentual", yDomain=[0, max(1, maximum)])
        details = [occupancy_details(m, include_rate=slug != "ocupacao") for _, m, _ in period_data]
        if slug == "extremos":
            details = [
                f'{detail}\nAbaixo de 25%: {integer(m["low"])} turmas · 100% ou mais: {integer(m["full"])} turmas'
                for detail, (_, m, _) in zip(details, period_data, strict=True)
            ]
        result.append(chart(f"{prefix}-indicador-{slug}", title, f"{description} {note}", spec,
                            [semester, *series], rows, tooltips=details))
    return result


occupancy_bands = ["Abaixo de 25%", "25% a menos de 50%", "50% a menos de 100%", "100% ou mais"]


def distribution(rows):
    counts = Counter(0 if rate(r)<.25 else 1 if rate(r)<.5 else 2 if rate(r)<1 else 3 for r in rows)
    return [counts[i] for i in range(len(occupancy_bands))]


def varied_charts(prefix, hist, latest, periods, classification=None):
    by_period = group(hist + latest, lambda row: row["periodo"])
    summaries = []
    for period in periods:
        rows = by_period[period]
        label = semester_label(period, rows)
        summaries.append((label, metrics(rows), median(map(rate, rows)) if rows else None))

    def line(key, title, description, series, values, percent_axis=False):
        spec = dict(type="line", x="Semestre", y=series)
        if percent_axis:
            spec["valueFormat"] = {"style": "percent"}
        return chart(f"{prefix}-{key}", title,
                     f"{description} O trecho tracejado indica um semestre que inclui turmas abertas.",
                     spec, ["Semestre", *series],
                     [[period, *values(m, middle)] if m["n"] else [period, None, None]
                      for period, m, middle in summaries] if hist or latest else [],
                     tooltips=[occupancy_details(m, include_rate=False)
                               for _, m, _ in summaries] if hist or latest else [])

    def donut(key, title, description, labels, counts):
        return chart(f"{prefix}-{key}", title, description,
                     dict(type="donut", x="Categoria", y="Turmas", categoryOrder=labels), ["Categoria", "Turmas"],
                     [[label, count] for label, count in zip(labels, counts, strict=True) if count])

    shifts = Counter(map(shift, hist))
    shift_labels = ["Manhã", "Tarde", "Noite", "Misto", "Sem horário"]
    points = Counter((r["capacidade"], r["matriculas"]) for r in hist)
    capacities = Counter(row["capacidade"] for row in hist)
    main_capacities = capacities.most_common(5)
    other_capacities = sum(capacities.values()) - sum(count for _, count in main_capacities)
    size_rows = [[f"{capacity} vagas", count] for capacity, count in main_capacities]
    if other_capacities:
        size_rows.append(["Outras capacidades", other_capacities])
    by_code = group(hist, lambda row: row["codigo"])
    bubble_rows = []
    bubble_details = []
    for code, rows in sorted(by_code.items()):
        m = metrics(rows)
        bubble_rows.append([f'{code} · {rows[-1]["disciplina"].title()}', m["c"], m["m"], m["n"]])
        bubble_details.append(occupancy_details(m))
    historical_bands, open_bands = distribution(hist), distribution(latest)
    nature_series = ["Obrigatórias", "Optativas", "Compartilhadas ou sem classificação"]
    if classification is not None:
        required, optional = classification
    elif prefix == "matcomp":
        required, optional = codes("Matemática Computacional", 2), codes("Matemática Computacional")
    else:
        required, optional = req_only, opt_codes
    nature_rows = []
    distribution_rows = []
    for label, m, _ in summaries:
        period = label.removesuffix("*")
        period_rows = by_period[period]
        sums = Counter()
        for row in period_rows:
            nature = 0 if row["codigo"] in required else 1 if row["codigo"] in optional else 2
            sums[nature] += row["matriculas"]
        nature_rows.append([label, *[sums[i] if m["n"] else None for i in range(3)]])
        distribution_rows.append([label, *[count / m["n"] if m["n"] else None
                                           for count in distribution(period_rows)]])
    return [
        line("linha-ocupacao", "Ocupação mediana e ocupação geral",
             "A mediana dá o mesmo peso a cada turma. A ocupação geral divide todas as matrículas por todas as vagas.",
             ["Mediana das turmas", "Ocupação geral"], lambda m, middle: [middle, m["rate"]], percent_axis=True),
        line("linha-tamanho", "Vagas e matrículas médias por turma",
             "Em cada semestre, divide vagas e matrículas pelo número de turmas presenciais.",
             ["Vagas por turma", "Matrículas por turma"], lambda m, _: [m["c"] / m["n"], m["m"] / m["n"]]),
        donut("rosca-historico", "Faixas de ocupação nas turmas consolidadas",
              "Cada fatia mostra a parcela das turmas consolidadas na respectiva faixa de ocupação.",
              occupancy_bands, distribution(hist)),
        donut("rosca-abertas", "Faixas de ocupação nas turmas abertas",
              "Cada fatia mostra a parcela das turmas abertas na respectiva faixa de ocupação.",
              occupancy_bands, distribution(latest)),
        donut("rosca-turnos", "Distribuição das turmas consolidadas por turno",
              "Turmas com aulas em mais de um turno entram em Misto.", shift_labels,
              [shifts[label] for label in shift_labels]),
        chart(f"{prefix}-dispersao", "Vagas e matrículas por turma consolidada",
              "O tamanho de cada ponto indica quantas turmas têm a mesma combinação de vagas e matrículas. "
              "Acima da diagonal, as matrículas superam as vagas.",
              dict(type="scatter", x="Vagas", y="Matrículas", size="Turmas"),
              ["Vagas", "Matrículas", "Turmas"],
              [[capacity, enrolled, count] for (capacity, enrolled), count in sorted(points.items())]),
        chart(f"{prefix}-pizza-capacidades", "Composição da oferta por capacidade",
              "Distribuição das turmas consolidadas entre as cinco capacidades mais frequentes. "
              "As demais capacidades são agrupadas em Outras.",
              dict(type="pie", x="Capacidade", y="Turmas"), ["Capacidade", "Turmas"], size_rows),
        chart(f"{prefix}-radar-faixas", "Perfil de ocupação por faixa",
              "Compara a proporção de turmas em cada faixa no histórico consolidado e nas abertas. "
              "Cada eixo mostra uma parcela do total de turmas do respectivo recorte.",
              dict(type="radar", x="Faixa", y=["Consolidadas", "Abertas"],
                   valueFormat={"style": "percent"}),
              ["Faixa", "Consolidadas", "Abertas"],
              [[label, a / len(hist) if hist else None, b / len(latest) if latest else None]
               for label, a, b in zip(occupancy_bands, historical_bands, open_bands, strict=True)],
              tooltips=[f"Consolidadas: {a} de {len(hist)} turmas\nAbertas: {b} de {len(latest)} turmas"
                        for a, b in zip(historical_bands, open_bands, strict=True)]),
        chart(f"{prefix}-faixas-percentual", "Composição da ocupação ao longo dos semestres",
              "As colunas representam 100% das turmas de cada semestre e facilitam a comparação das proporções. "
              "O asterisco identifica semestres que incluem turmas abertas.",
              dict(type="stackedPercent", x="Semestre", y=occupancy_bands, valueFormat={"style": "percent"}),
              ["Semestre", *occupancy_bands], distribution_rows,
              tooltips=[occupancy_details(m) for _, m, _ in summaries]),
        chart(f"{prefix}-bolhas-disciplinas", "Dimensão da oferta por disciplina",
              "Cada bolha representa uma disciplina no histórico consolidado. Os eixos somam vagas e matrículas. "
              "A área da bolha é proporcional ao número de turmas ofertadas.",
              dict(type="bubble", x="Vagas", y="Matrículas", size="Turmas", label="Disciplina"),
              ["Disciplina", "Vagas", "Matrículas", "Turmas"], bubble_rows, tooltips=bubble_details),
        chart(f"{prefix}-area-natureza", "Matrículas por natureza curricular",
              "As áreas empilhadas somam as matrículas de cada semestre, classificadas pelos códigos da matriz "
              "de referência. Códigos compartilhados ou sem classificação aparecem em uma categoria própria. "
              "O asterisco identifica semestres que incluem turmas abertas.",
              dict(type="area", x="Semestre", y=nature_series), ["Semestre", *nature_series], nature_rows,
              tooltips=[occupancy_details(m) for _, m, _ in summaries]),
    ]


def overview_panels(hist, latest, periods, *, only=None):
    percent = {"style":"percent", "maximumFractionDigits":1}

    by_period = group(hist + latest, lambda r: r["periodo"])
    shown = {p: semester_label(p, by_period[p]) for p in periods}

    panels = []

    def add(key, title, plots):
        panels.append(dict(id=key, title=title, sections=[dict(title=None, plots=plots)]))

    if only in (None, 'evolucao'):
        period_note = "Turmas presenciais do recorte selecionado."
        period_metrics = {p:metrics(by_period[p]) for p in periods}
        bands = occupancy_bands

        add("evolucao", "Oferta e matrículas por semestre", [
            chart("ufca-capacidade-matriculas", "Vagas e matrículas por semestre", period_note,
                  dict(type="bar", x="Semestre", y=["Capacidade", "Matrículas"], yLabel="Total"),
                  ["Semestre", "Capacidade", "Matrículas"],
                  [[shown[p], m["c"], m["m"]] for p,m in period_metrics.items()]),
            chart("ufca-faixas", "Distribuição das turmas por faixa de ocupação", period_note,
                  dict(type="stackedBar", x="Semestre", y=bands, yLabel="Turmas"),
                  ["Semestre", *bands], [[shown[p], *distribution(by_period[p])] for p in periods], 320),
            *offer_indicators("ufca", by_period),
        ])

    historical = sorted({row['periodo'] for row in hist})
    if only in (None, 'disciplinas'):
        def prefix(r):
            return re.match(r"[A-Z]+", r["codigo"]).group()

        by_prefix_period = group(hist, lambda r:(prefix(r),r["periodo"]))
        by_code_period = group(hist + latest, lambda r:(r["codigo"],r["periodo"]))
        selected_codes = ["CC0015", "ECI0079", "CAR0011", "ECI0002", "EM0105", "EM0030", "EM0043", "EM0114"]
        prefixes = ["CAR","CC","ECI","EM","ES","MC"]

        def occupancy_heat(id, title, note, groups, row_names, semester_list, y_label, max_rate, height):
            entries = [(shown[p], label, metrics(groups.get((label, p), [])))
                       for label in row_names for p in semester_list]
            return chart(id, title, note,
                         dict(type="heatmap", x="Semestre", y=y_label, value="Ocupação",
                              xOrder=[shown[p] for p in semester_list], yOrder=row_names,
                              showValues=True, valueFormat=percent, colorDomain=[0,max_rate]),
                         ["Semestre", y_label, "Ocupação"],
                         [[p, label, m["rate"]] for p, label, m in entries], height,
                         tooltips=[occupancy_details(m, include_rate=False) for _, _, m in entries])

        add("disciplinas", "Ocupação por prefixo e por disciplina", [
            occupancy_heat("ufca-prefixos", "Ocupação por prefixo de código", "Somente turmas presenciais consolidadas.",
                           by_prefix_period, prefixes, historical, "Prefixo", 1, 330),
            occupancy_heat("ufca-codigos", "Ocupação de oito disciplinas selecionadas",
                           "Agregada por código. Células vazias indicam ausência de registro no recorte. *Turmas abertas.",
                           by_code_period, selected_codes, periods, "Código", 1.12, 380),
        ])

    if only in (None, 'horarios-capacidade'):
        shifts = group(hist, shift)
        capacities = group(hist, lambda r:r["capacidade"])
        counts = Counter({capacity: len(rows) for capacity, rows in capacities.items()})
        common_sizes = sorted(capacity for capacity, _ in counts.most_common(5))
        covered = sum(counts[capacity] for capacity in common_sizes)

        add("horarios-capacidade", "Horários, turnos e tamanho das turmas", [
            schedule_heatmap("ufca-grade-horaria", "Concentração da oferta ao longo da semana",
                             notes["ufca-grade-horaria"], hist, hour_label="Hora"),
            chart("ufca-turnos", "Ocupação por turno",
                  "Turmas presenciais consolidadas. Misto abrange aulas em mais de um turno.",
                  dict(type="horizontalBar", y="Turno", x="Ocupação", xLabel="Matrículas ÷ capacidade",
                       xDomain=[0,1], valueFormat=percent, showValues=True),
                  ["Turno","Ocupação"],
                  [[f"{s} · {len(shifts.get(s, []))} turmas", metrics(shifts.get(s, []))["rate"]]
                   for s in ["Manhã","Tarde","Noite","Misto","Sem horário"] if s in shifts], 240),
            chart("ufca-tamanho", "Ocupação segundo o tamanho da turma",
                  f"Até cinco capacidades mais frequentes, que somam {integer(covered)} das "
                  f"{integer(len(hist))} turmas presenciais consolidadas. "
                  "A ocupação divide as matrículas pelo total de vagas em cada grupo.",
                  dict(type="horizontalBar", y="Capacidade", x="Ocupação", xLabel="Matrículas ÷ capacidade",
                       xDomain=[0,1], valueFormat=percent, showValues=True),
                  ["Capacidade","Ocupação"],
                  [[f"{n} vagas · {counts[n]} turmas", metrics(capacities[n])["rate"]] for n in common_sizes], 255),
        ])

    if only is not None:
        for plot in panels[0]["sections"][0]["plots"]:
            plot["description"] = notes.get(plot["id"], plot["description"])
        return panels

    format_pct = {"style":"percent","maximumFractionDigits":1}
    short = ["Civil","Materiais","Computação (CC002)","Matemática","Software"]
    course_rows = []
    for name, label in zip(current, short, strict=True):
        completed = metrics(select(hist,codes(name)))
        open_now = metrics(select(latest,codes(name)))
        if completed["n"] or open_now["n"]:
            course_rows.append([label,completed["rate"],open_now["rate"]])

    period_rows = []
    for period in historical:
        rows = [r for r in hist if r["periodo"] == period]
        period_rows.append([period,metrics(select(rows,opt_only))["rate"],metrics(select(rows,req_only))["rate"]])

    optional_plots = [
        {"id":"ufca-opt-curso","title":"Ocupação das disciplinas listadas como optativas",
         "description":"Natureza na matriz de referência de cada curso. Software não tem registros de optativas na base.",
         "height":320,"columns":["Curso","Consolidadas","Abertas"],"rows":course_rows,
         "spec":{"type":"horizontalBar","y":"Curso","x":["Consolidadas","Abertas"],
                 "xLabel":"Matrículas ÷ capacidade","xDomain":[0,1],"valueFormat":format_pct}},
        {"id":"ufca-opt-periodo","title":"Ocupação por semestre e natureza curricular",
         "description":"Turmas presenciais consolidadas. Códigos com mudança conhecida de natureza ou sem classificação nas listas de referência ficam fora.",
         "height":320,"columns":["Semestre","Optativas","Obrigatórias"],"rows":period_rows,
         "spec":{"type":"bar","x":"Semestre","y":["Optativas","Obrigatórias"],
                 "yLabel":"Matrículas ÷ capacidade","yDomain":[0,1],"valueFormat":format_pct}},
    ]

    add("optativas", "Optativas por curso e por semestre", optional_plots)

    for panel in panels:
        for plot in panel["sections"][0]["plots"]:
            plot["description"] = notes.get(plot["id"], plot["description"])

    add("graficos-variados", "Explorações visuais", varied_charts("ufca", hist, latest, periods))
    panels[0]["summary"] = {"historico": metrics(hist), "abertas": metrics(latest)}
    return panels


sizes = {20,25,30,40,50}
legacy_opt = {"EM0057"}
opt_codes = opt_only | legacy_opt
cohorts = [
    ("obrigatorias","Obrigatórias",req_only),
    ("optativas","Optativas",opt_codes),
    ("geral","Geral",req_only | opt_codes),
]


def integer(value):
    return f"{value:,}".replace(",",".")

def percent(value):
    return f"{float(value):.1%}".replace(".",",")

def label_prefix(r):
    return re.match(r"[A-Z]+",r["codigo"]).group()

def recurrences(rows):
    results = [metrics(rs) for rs in group(rows,lambda r:r["periodo"]).values()]
    return sum(m["m"]>=m["c"] for m in results), sum(4*m["m"]<m["c"] for m in results)

def summarize(label, rows):
    m = metrics(rows)
    periods = len({r["periodo"] for r in rows})
    recurring_full, recurring_low = recurrences(rows)
    return dict(m,label=label,rate=Fraction(m["m"],m["c"]),periods=periods,
                recurring_full=recurring_full,recurring_low=recurring_low,
                mid_low=sum(r["capacidade"]<=4*r["matriculas"]<2*r["capacidade"] for r in rows),
                mid_high=sum(r["capacidade"]<=2*r["matriculas"]<2*r["capacidade"] for r in rows))

def datasets(rows, slug):
    by_code = group(rows,lambda r:r["codigo"])
    by_slot = defaultdict(list)
    for row in rows:
        for day, hour in hourly_slots(row, range(24)):
            by_slot[f"{days[day]} {hour:02}h–{hour+1:02}h"].append(row)
    course_rows = []
    course_labels = ["Eng. Civil","Eng. de Materiais","Ciência da Computação","Mat. Computacional","Eng. de Software"]
    for course, label in zip(current,course_labels,strict=True):
        optional = codes(course) | (legacy_opt if course == "Engenharia de Materiais" else set())
        required = codes(course,2)
        allowed = {"optativas":optional,"obrigatorias":required,"geral":optional|required}[slug]
        matched = select(rows,allowed)
        if matched:
            course_rows.append(summarize(label,matched))
    return {
        "Disciplina": [summarize(f'{code} · {rs[-1]["disciplina"].title()}',rs)
                        for code,rs in by_code.items()],
        "Semestre": [summarize(key,rs) for key,rs in group(rows,lambda r:r["periodo"]).items()],
        "Matriz do curso": course_rows,
        "Prefixo": [summarize(key,rs) for key,rs in group(rows,label_prefix).items()],
        "Turno": [summarize(key,rs) for key,rs in group(rows,shift).items()],
        "Capacidade": [summarize(f"{key} vagas",rs) for key,rs in group(rows,lambda r:r["capacidade"]).items()],
        "Dia e horário": [summarize(key,rs) for key,rs in by_slot.items()],
    }

def ordered(rows,key,ascending=False):
    return sorted(rows,key=lambda r:(r[key] if ascending else -r[key],r["label"]))

def ranked_positions(rows,key,ascending=False):
    values = ordered(rows,key,ascending)
    ranks = {}
    last = None
    for index,row in enumerate(values,1):
        value = row[key]
        if value != last:
            position = index
        ranks[row["label"]] = position
        last = value
    return ranks


chart_groups = [
    ("Disciplinas · turmas consolidadas", [
        ("Mais matrículas","Disciplina","m",5),
        ("Mais vagas ofertadas","Disciplina","c",5),
        ("Maior ocupação acumulada","Disciplina","rate",5),
        ("Menor ocupação acumulada","Disciplina","rate",-5),
        ("Mais matrículas acima da capacidade","Disciplina","extra",5),
        ("Mais vagas não preenchidas","Disciplina","free",5),
        ("Mais semestres no limite ou acima","Disciplina","recurring_full",4),
        ("Mais semestres abaixo de 25%","Disciplina","recurring_low",4),
        ("Mais semestres com oferta","Disciplina","periods",5),
        ("Mais turmas ofertadas","Disciplina","n",5),
    ]),
    ("Semestres · turmas consolidadas", [
        ("Maior ocupação","Semestre","rate",7),
        ("Mais matrículas","Semestre","m",7),
        ("Mais turmas no limite ou acima","Semestre","full",7),
        ("Mais turmas abaixo de 25%","Semestre","low",7),
    ]),
    ("Oferta, turno e tamanho · turmas consolidadas", [
        ("Mais turmas por dia e faixa horária","Dia e horário","n",5),
        ("Ocupação por turno","Turno","rate",4),
        ("Ocupação por prefixo do código","Prefixo","rate",6),
        ("Ocupação por matriz de curso","Matriz do curso","rate",5),
        ("Ocupação nas cinco capacidades de referência","Capacidade","rate",5),
    ]),
    ("Turmas abertas", [
        ("Mais matrículas","Disciplina","m",5),
        ("Maior ocupação","Disciplina","rate",5),
        ("Mais vagas não preenchidas","Disciplina","free",5),
        ("Menor ocupação","Disciplina","rate",-5),
    ]),
]

def chart_rows(data,dimension,key,limit):
    rows = data[dimension]
    if dimension == "Capacidade":
        rows = [r for r in rows if int(r["label"].split()[0]) in sizes]
    return ordered(rows,key,limit<0)[:abs(limit)]


def plot_data(cohort, computed):
    output = []
    for index,(title,plots) in enumerate(chart_groups):
        di = 5 if index == 3 else 4
        chart_list = []
        for label,dimension,key,limit in plots:
            selected = chart_rows(cohort[di],dimension,key,limit)
            ceiling = max(
                [r[key] for c in computed for r in chart_rows(c[di],dimension,key,limit)]
                + ([Fraction(1)] if key == "rate" else [1])
            )
            rows = []
            ranks = ranked_positions(selected,key,limit<0)
            for row in selected:
                text = f'{ranks[row["label"]]}. {row["label"]}'
                value = percent(row[key]) if key == "rate" else integer(row[key])
                if key == "rate" and dimension == "Disciplina":
                    value += f' · {row["m"]}/{row["c"]}'
                elif key == "rate" and dimension in {"Turno","Prefixo","Capacidade","Matriz do curso"}:
                    unit = "turma" if row["n"] == 1 else "turmas"
                    text += f' ({row["n"]} {unit})'
                rows.append([text,value,round(float(row[key]/ceiling)*100,4)])
            chart_list.append(dict(title=label, rows=rows,
                                   rankingValues=[float(r[key]) for r in selected], rankingPercent=key == "rate",
                                   comparisonDimension=dimension, comparisonMetric=key,
                                   comparisonRecords=[dict(label=r['label'], value=float(r[key]))
                                                      for r in cohort[di][dimension]
                                                      if dimension != 'Capacidade' or int(r['label'].split()[0]) in sizes],
                                   tooltips=[occupancy_details(r, include_rate=key != "rate") for r in selected]))
        output.append(dict(title=title,plots=chart_list))
    return output


def course_panel(hist, latest, periods, config, *, specific_only=False):
    course, prefix = config["title"], config["prefix"]
    required, optional = curriculum(sources, config)
    allowed = required | optional
    past, opened = select(hist, allowed), select(latest, allowed)
    all_rows = hist + latest
    by_period = group(all_rows, lambda r: r["periodo"])
    course_by_period = group(past + opened, lambda r: r["periodo"])
    periods = [period for period in periods if period in course_by_period]
    code_by_period = group(past + opened, lambda r: (r["codigo"], r["periodo"]))
    by_code = group(past + opened, lambda r: r["codigo"])
    labels = {code: f'{code} · {rows[-1]["disciplina"].title()}' for code, rows in by_code.items()}
    shown = {p: semester_label(p, course_by_period[p]) for p in periods}
    pct = {"style": "percent"}
    note = "Turmas presenciais do recorte selecionado."

    def timeline(key, title, description, series, rows, kind="bar", percentage=False):
        spec = dict(type=kind, x="Semestre", y=series,
                    yLabel="Ocupação (%)" if percentage else "Total")
        if percentage:
            spec["valueFormat"] = pct
            maximum = max((value for row in rows for value in row[1:] if value is not None), default=0)
            spec["yDomain"] = [0, max(1, maximum)]
        return chart(f"{prefix}-{key}", title, description, spec, ["Semestre", *series], rows)

    def course_metrics(period, codes_for_chart=allowed):
        return metrics(select(course_by_period[period], codes_for_chart))

    volumes = [[shown[p], m["c"], m["m"]] for p in periods if (m := course_metrics(p))["n"]]
    overview = [
        timeline("vagas", "Vagas e matrículas por semestre", note, ["Vagas", "Matrículas"], volumes),
        timeline("comparacao", "Ocupação do curso e do CCT",
                 "Ocupação é a soma das matrículas dividida pela soma das vagas. O total do CCT inclui o curso. " + note,
                 [course, "CCT"], [[shown[p], course_metrics(p)["rate"], metrics(by_period[p])["rate"]]
                                   for p in periods], percentage=True),
        timeline("natureza", "Ocupação de obrigatórias e optativas",
                 "As disciplinas são agrupadas conforme a natureza indicada na matriz de referência do curso. " + note,
                 ["Obrigatórias", "Optativas"],
                 [[shown[p], course_metrics(p, required)["rate"], course_metrics(p, optional)["rate"]]
                  for p in periods], percentage=True),
        timeline("faixas", "Turmas por faixa de ocupação",
                 "Cada turma é contada na faixa correspondente às suas matrículas divididas pelas vagas. " + note,
                 occupancy_bands,
                 [[shown[p], *distribution(course_by_period[p])] for p in periods], kind="stackedBar"),
        *(plot for plot in offer_indicators(prefix, course_by_period)
          if plot["id"] != f"{prefix}-indicador-ocupacao"),
    ]

    def history_heat(key, title, allowed_codes):
        entries = [(shown[p], labels[code], metrics(code_by_period.get((code, p), [])))
                   for code in sorted(allowed_codes & by_code.keys()) for p in periods]
        return chart(f"{prefix}-{key}", title,
                     "Inclui os códigos com oferta na base. Um traço indica ausência de oferta no recorte. " + note,
                     dict(type="heatmap", x="Semestre", y="Disciplina", value="Ocupação",
                          colorDomain=[0, 1], valueFormat=pct),
                     ["Semestre", "Disciplina", "Ocupação"],
                     [[p, label, m["rate"]] for p, label, m in entries],
                     tooltips=[occupancy_details(m, include_rate=False) for _, _, m in entries])

    def required_heat(matrix):
        ordered = [(semester, code) for semester, codes in enumerate(matrix.semesters, 1) for code in codes.split()]
        y_order = [labels.get(code, code) for _, code in ordered]
        groups = {labels.get(code, code): f'{semester}º semestre curricular' for semester, code in ordered}
        entries = [(shown[p], labels.get(code, code), metrics(code_by_period.get((code, p), [])))
                   for _, code in ordered for p in periods]
        return chart(f'{prefix}-historico-obrigatorias', 'Ocupação das obrigatórias por disciplina',
                     'Disciplinas agrupadas pelo semestre previsto na matriz. As colunas mostram os semestres da oferta.',
                     dict(type='heatmap', x='Semestre', y='Disciplina', value='Ocupação',
                          xOrder=[shown[p] for p in periods], yOrder=y_order, yGroups=groups,
                          colorDomain=[0, 1], valueFormat=pct),
                     ['Semestre', 'Disciplina', 'Ocupação'],
                     [[p, label, m['rate']] for p, label, m in entries],
                     tooltips=[occupancy_details(m, include_rate=False) if m['n'] else '' for _, _, m in entries])

    def discipline_bars(key, title, description, source, metric, column, limit=None,
                        *, ascending=False, positive=False):
        values = [
            summarize(labels[code], rows)
            for code, rows in group(source, lambda r: r["codigo"]).items()
        ]
        comparison_records = [dict(label=r['label'], value=float(r[metric])) for r in values]
        if positive:
            values = [r for r in values if r[metric] > 0]
        selected = ordered(values, metric, ascending)[:limit]
        spec = dict(type="horizontalBar", y="Disciplina", x=column)
        if metric == "rate":
            spec.update(valueFormat=pct, xDomain=[0, float(max([1, *(r["rate"] for r in selected)]))])
        ranks = ranked_positions(selected, metric, ascending)
        return chart(f"{prefix}-{key}", title, description, spec, ["Disciplina", column],
                     [[f'{ranks[r["label"]]}. {r["label"]}', float(r[metric]) if metric == "rate" else r[metric]]
                      for r in selected],
                     tooltips=[f'{occupancy_details(r, include_rate=metric != "rate")}\n'
                               f'Semestres com oferta: {r["periods"]}' for r in selected]) | {
                                   'comparisonDimension': 'Disciplina', 'comparisonMetric': metric,
                                   'comparisonRecords': comparison_records,
                               }

    matrices = PPCS[config['key']]
    required_plot = required_heat(matrices[0])
    required_plot['curriculumOptions'] = [dict(id=m.id, label=m.label, source=m.source) for m in matrices]
    required_plot['curriculumAlternatives'] = {matrix.id: required_heat(matrix) for matrix in matrices[1:]}
    history = [
        required_plot,
        history_heat("historico-optativas", "Ocupação das optativas por disciplina", optional),
    ]
    historical_rankings = [
        discipline_bars("matriculas-historico", "Disciplinas com mais matrículas",
                        "As dez disciplinas com maior soma de matrículas nas turmas consolidadas.",
                        past, "m", "Matrículas", 10),
        discipline_bars("baixa-recorrente", "Disciplinas com mais semestres abaixo de 25% de ocupação",
                        "Mostra até dez disciplinas. A ocupação de cada código é calculada com as turmas consolidadas de cada semestre.",
                        past, "recurring_low", "Semestres", 10),
        discipline_bars("maior-ocupacao", "Disciplinas com maior ocupação acumulada",
                        "Até dez disciplinas pela razão entre matrículas e vagas no histórico consolidado.",
                        past, "rate", "Ocupação", 10),
        discipline_bars("menor-ocupacao", "Disciplinas com menor ocupação acumulada",
                        "Até dez disciplinas pela razão entre matrículas e vagas no histórico consolidado.",
                        past, "rate", "Ocupação", 10, ascending=True),
        discipline_bars("mais-vagas", "Disciplinas com mais vagas ofertadas",
                        "Até dez disciplinas pelo total de vagas nas turmas consolidadas.",
                        past, "c", "Vagas", 10),
        discipline_bars("mais-turmas", "Disciplinas com mais turmas",
                        "Até dez disciplinas pelo número de turmas consolidadas.",
                        past, "n", "Turmas", 10),
        discipline_bars("mais-semestres", "Disciplinas ofertadas em mais semestres",
                        "Até dez disciplinas pela frequência da oferta no histórico consolidado.",
                        past, "periods", "Semestres", 10),
        discipline_bars("sobras", "Disciplinas com mais vagas não preenchidas",
                        "Até dez disciplinas pela soma das vagas não preenchidas em cada turma consolidada.",
                        past, "free", "Vagas não preenchidas", 10, positive=True),
        discipline_bars("lotadas", "Disciplinas com mais turmas lotadas",
                        "Conta as turmas consolidadas com matrículas iguais ou acima da capacidade.",
                        past, "full", "Turmas lotadas", 10, positive=True),
        discipline_bars("acima-capacidade", "Disciplinas com mais matrículas acima da capacidade",
                        "Soma o excesso de matrículas das turmas consolidadas acima da capacidade.",
                        past, "extra", "Matrículas excedentes", 10, positive=True),
        discipline_bars("obrigatorias-matriculas", "Obrigatórias com mais matrículas",
                        "Até dez disciplinas obrigatórias pelo total de matrículas nas turmas consolidadas.",
                        select(past, required), "m", "Matrículas", 10),
        discipline_bars("optativas-matriculas", "Optativas com mais matrículas",
                        "Até dez disciplinas optativas pelo total de matrículas nas turmas consolidadas.",
                        select(past, optional), "m", "Matrículas", 10),
    ]
    result = dict(
        id=config["id"], title=course, courseKey=config["key"], chartPrefix=prefix,
        summary={"historico": metrics(past), "abertas": metrics(opened)},
        description="Recorte por códigos das disciplinas obrigatórias e optativas da matriz de referência. "
                    "Disciplinas CAR compartilhadas entram quando presentes na matriz; CAR não é um curso. "
                    "O recorte por matriz pode diferir de uma seleção por prefixo do código. "
                    "As matrículas são registros de turma e podem incluir estudantes de outros cursos.",
        sections=[
            dict(title="Evolução por semestre", plots=overview),
            dict(title="Histórico por disciplina", plots=history),
            dict(title="Rankings das turmas consolidadas", plots=historical_rankings),
        ],
    )
    if specific_only:
        return result
    current_charts = [
        discipline_bars("abertas-ocupacao", "Ocupação das disciplinas abertas",
                        "Todas as disciplinas com oferta aberta na oferta aberta, em ordem decrescente de ocupação.",
                        opened, "rate", "Ocupação"),
        discipline_bars("abertas-vagas", "Vagas ainda não preenchidas",
                        "Todas as disciplinas com oferta aberta na oferta aberta. Soma as vagas não preenchidas turma a turma.",
                        opened, "free", "Vagas não preenchidas"),
        discipline_bars("abertas-matriculas", "Mais matrículas nas turmas abertas",
                        "Até dez disciplinas pelo total de matrículas nas turmas abertas.",
                        opened, "m", "Matrículas", 10),
        discipline_bars("abertas-menor-ocupacao", "Menor ocupação nas turmas abertas",
                        "Até dez disciplinas pela menor razão entre matrículas e vagas na oferta aberta.",
                        opened, "rate", "Ocupação", 10, ascending=True),
    ]
    result['sections'].extend([
        dict(title="Rankings das turmas abertas", plots=current_charts),
        dict(title="Explorações visuais", plots=varied_charts(prefix, past, opened, periods, (required, optional))),
    ])
    stats = statistical_panel(prefix, f"Análises estatísticas de {course}", past, opened, periods)
    result['sections'].extend(stats['sections'])
    result['statisticalSummary'] = stats['statisticalSummary']
    return result


def mathematics_panel(hist, latest, periods):
    return course_panel(hist, latest, periods, COURSES[0])


def build_panels(offers):
    """Recalcula todos os gráficos a partir do JSON de ofertas."""
    if not isinstance(offers, list) or not offers:
        raise ValueError("O JSON deve conter uma lista de turmas.")
    hist, latest = split_offers(offers)
    periods = sorted({row["periodo"] for row in hist + latest})
    if not periods:
        raise ValueError("Não há turmas presenciais no recorte.")
    return build_cohort_panels(hist, latest, periods)


def build_cohort_panels(primary_rows, comparison_rows, periods):
    """Calcula as famílias para amostras já selecionadas, sem mudar sua situação.

    A apresentação de cada recorte é responsabilidade de period_views. Os nomes
    locais hist/latest identificam as séries originais das funções de cálculo.
    """
    hist, latest = primary_rows, comparison_rows
    panels = [*[course_panel(hist, latest, periods, config) for config in COURSES], *overview_panels(hist, latest, periods)]
    computed = []
    for slug, title, allowed in cohorts:
        past = select(hist, allowed)
        opened = select(latest, allowed)
        computed.append((slug, title, past, opened, datasets(past, slug), datasets(opened, slug)))
    for cohort in computed:
        slug, title = cohort[:2]
        sections = plot_data(cohort, computed)
        for i, (section, descriptions) in enumerate(zip(sections, ranking, strict=True), 1):
            for j, (plot, description) in enumerate(zip(section["plots"], descriptions, strict=True), 1):
                plot.update(id=f"ufca-ranking-{slug}-{i}-{j}", formato="ranking", description=description,
                            columns=["Posição e categoria", "Valor exibido", "Largura da barra (%)"])
        panels.append(dict(id=f"ranking-{slug}", title=f"Rankings · {title}", sections=sections))
    panels.append(statistical_panel("ufca", "Análises estatísticas do CCT", hist, latest, periods))
    return panels


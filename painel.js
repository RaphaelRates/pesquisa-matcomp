"use strict";

const colors = ["#3276dd", "#149485", "#e7a23b", "#9164ca", "#de6474", "#66798d"];
const integerFormat = new Intl.NumberFormat("pt-BR", {maximumFractionDigits: 0});
const percentFormat = new Intl.NumberFormat("pt-BR", {style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1});
const decimalFormat = new Intl.NumberFormat("pt-BR", {maximumFractionDigits: 1});
const preciseFormat = new Intl.NumberFormat("pt-BR", {maximumFractionDigits: 3});
const indexFormat = new Intl.NumberFormat("pt-BR", {maximumFractionDigits: 4});
const chartInstances = new Map();
let stopMounting = () => {};
let dashboardLoading = false;
const kinds = {
  bar: "Barras", horizontalBar: "Barras horizontais", ranking: "Ranking",
  stackedBar: "Barras empilhadas", stackedPercent: "Composição · 100%",
  line: "Linhas", area: "Área empilhada", mixed: "Barras + linha",
  donut: "Rosca", pie: "Pizza", radar: "Radar",
  scatter: "Dispersão", bubble: "Bolhas", heatmap: "Mapa de calor",
  distributionBand: "Faixa interquartil", statisticalScatter: "Associação descritiva",
};

function escapeHtml(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function format(value, percent = false) {
  return value == null ? "Sem registro" : (percent ? percentFormat : decimalFormat).format(value);
}

function measure(value, valueFormat = {}) {
  if (value == null) return "Sem registro";
  if (valueFormat.style === "percent") return percentFormat.format(value);
  return valueFormat.style === "decimal" ? preciseFormat.format(value) : decimalFormat.format(value);
}

function records(plot) {
  return plot.rows.map((row, index) => ({
    values: Object.fromEntries(plot.columns.map((column, i) => [column, row[i]])),
    detail: plot.tooltips?.[index],
  }));
}

function wrapLabel(label, limit = 34) {
  const lines = [];
  let line = "";
  for (const word of String(label).split(" ")) {
    if (line && line.length + word.length + 1 > limit) {
      lines.push(line);
      line = "";
    }
    line += (line ? " " : "") + word;
  }
  if (line) lines.push(line);
  return lines;
}

function tooltipAttrs(heading, value, detail) {
  const text = [heading, value, detail].filter(Boolean).join("\n");
  return `tabindex="0" data-tooltip="${escapeHtml(text)}" aria-label="${escapeHtml(text.replaceAll("\n", ". "))}"`;
}

function heatmap(plot) {
  const {spec} = plot;
  const rows = records(plot);
  const keyFor = (x, y) => JSON.stringify([x, y]);
  const cells = new Map(rows.map(({values, detail}) =>
    [keyFor(values[spec.x], values[spec.y]), {value: values[spec.value], detail}]));
  const columns = spec.xOrder ?? [...new Set(rows.map(({values}) => values[spec.x]))];
  const labels = spec.yOrder ?? [...new Set(rows.map(({values}) => values[spec.y]))];
  const [low, high] = spec.colorDomain ?? [0, Math.max(1, ...rows.map(({values}) => values[spec.value] ?? 0))];
  const header = columns.map(col => `<th scope="col">${escapeHtml(col)}</th>`).join("");
  const body = labels.map(label => {
    const line = columns.map(col => {
      const {value, detail} = cells.get(keyFor(col, label)) ?? {};
      const printed = format(value, spec.valueFormat?.style === "percent");
      const attrs = tooltipAttrs(`${label} · ${col}`, `${spec.value}: ${printed}`, detail);
      if (value == null) return `<td class="missing" ${attrs}>—</td>`;
      const intensity = Math.max(0, Math.min(1, (value - low) / (high - low))) * 78;
      return `<td style="--intensity:${intensity}%" ${attrs}>${printed}</td>`;
    }).join("");
    return `<tr><th scope="row">${escapeHtml(label)}</th>${line}</tr>`;
  }).join("");
  return `<div class="scroll heat-scroll"><table class="heat" aria-label="${escapeHtml(plot.title)}">
    <thead><tr><th scope="col">${escapeHtml(spec.y)}</th>${header}</tr></thead><tbody>${body}</tbody></table></div>
    <div class="heat-key"><span>Menor</span><i></i><span>Maior</span><span class="muted">— Sem registro</span></div>`;
}

function table(plot) {
  const {spec} = plot;
  const valueColumns = [spec?.value ?? (spec?.type === "horizontalBar" ? spec.x : spec?.y)].flat();
  const columns = plot.formato === "ranking" ? plot.columns.slice(0, 2) : plot.columns;
  const header = columns.map(col => `<th scope="col">${escapeHtml(col)}</th>`).join("");
  const body = plot.rows.map(row => `<tr>${row.slice(0, columns.length).map((value, i) => {
    const percent = (spec?.valueFormat?.style === "percent" && valueColumns.includes(columns[i])) ||
      (spec?.xValueFormat?.style === "percent" && columns[i] === spec.x);
    const text = value == null ? "—" : typeof value === "number" ?
      (percent ? format(value, true) : preciseFormat.format(value)) : value;
    return `<td>${escapeHtml(text)}</td>`;
  }).join("")}</tr>`).join("");
  return `<details id="${escapeHtml(plot.id)}-dados"><summary>Consultar dados</summary><div class="scroll">
    <table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table></div></details>`;
}

function methodNote(plot) {
  if (!plot.method && !plot.interpretation) return "";
  return `<details class="method-note"><summary>Método e interpretação</summary>
    ${plot.method ? `<p>${escapeHtml(plot.method)}</p>` : ""}
    ${plot.interpretation ? `<p>${escapeHtml(plot.interpretation)}</p>` : ""}</details>`;
}

function chartGrid(plots, heading) {
  return `<div class="chart-grid">${plots.map(plot => {
    const kind = plot.formato ?? plot.spec.type;
    const hasValues = plot.rows.length && (kind !== "heatmap" || plot.rows.some(row => row.at(-1) != null));
    const horizontal = kind === "ranking" || kind === "horizontalBar";
    const height = horizontal ? Math.max(290, plot.rows.length * 50) : 330;
    const graphic = kind === "heatmap" ? heatmap(plot) :
      `<div class="chart-frame ${horizontal ? "horizontal-chart" : ""}" style="--chart-height:${height}px">
        <canvas id="${escapeHtml(plot.id)}-canvas" data-plot-id="${escapeHtml(plot.id)}" tabindex="0" role="img"
          aria-label="${escapeHtml(plot.title)}. Use as setas para consultar os pontos."
          aria-describedby="${escapeHtml(plot.id)}-leitura">Consulte a tabela de dados abaixo.</canvas>
       </div><p class="sr-only" id="${escapeHtml(plot.id)}-leitura" aria-live="polite"></p>`;
    return `<article class="chart-card ${kind === "heatmap" ? "wide-card" : ""}" id="${escapeHtml(plot.id)}">
      <div class="card-kicker"><span class="chart-type">${kinds[kind]}</span><a href="#${escapeHtml(plot.id)}" aria-label="Link para este gráfico">↗</a></div>
      <${heading}>${escapeHtml(plot.title)}</${heading}>
      <p class="description">${escapeHtml(plot.description)}</p>
      ${hasValues ? graphic + methodNote(plot) + table(plot) :
        '<p class="empty-state">Sem turmas neste recorte.</p>' + methodNote(plot)}</article>`;
  }).join("")}</div>`;
}

function links(entries) {
  return `<ul>${entries.map(([id, name]) => `<li><a href="#${escapeHtml(id)}">${escapeHtml(name)}</a></li>`).join("")}</ul>`;
}

function summaryCards(summary) {
  const m = summary.historico;
  const entries = [["Turmas consolidadas", m.n], ["Vagas ofertadas", m.c], ["Matrículas registradas", m.m], ["Ocupação geral", format(m.rate, true)]];
  return `<div class="metrics">${entries.map(([name, value]) =>
    `<div class="metric"><span>${name}</span><strong>${typeof value === "number" ? integerFormat.format(value) : value}</strong></div>`).join("")}</div>
    <p class="data-note">2023.1 a 2026.1 · Matrículas contam registros nas turmas.
    <span>2026.2 tem ${integerFormat.format(summary.abertas.n)} turmas abertas, exibidas separadamente.</span></p>`;
}

function dataQuality(report, generatedAt) {
  if (!report) return "";
  const counts = [
    ["Registros lidos", report.inputRows], ["Registros válidos", report.validRows],
    ["Normalizados", report.normalizedRows], ["Inválidos descartados", report.discardedRows],
    ["Duplicatas removidas", report.duplicateRows], ["Grupos com conflito", report.conflictGroups],
  ];
  const issues = [...(report.issues ?? []), ...(report.exclusionReasons ?? []),
    ...(report.outOfScopeReasons ?? []), ...(report.warnings ?? [])].map(issue =>
    `<li>${escapeHtml(issue.reason)} <strong>${integerFormat.format(issue.count)}</strong></li>`).join("");
  const timestamp = generatedAt ? new Intl.DateTimeFormat("pt-BR", {dateStyle: "short", timeStyle: "medium"}).format(new Date(generatedAt)) : "";
  return `<section class="quality-panel" id="qualidade-dados" aria-labelledby="qualidade-titulo">
    <div class="quality-heading"><div><p class="eyebrow">DADOS PROCESSADOS NESTA CONSULTA</p>
    <h2 id="qualidade-titulo">Qualidade e preparação da base</h2></div>
    <button type="button" class="refresh-button" id="refresh-data">Recalcular dados ↻</button></div>
    <p class="quality-lead">${integerFormat.format(report.inputRows)} registros lidos ·
    ${integerFormat.format(report.inScopeRows ?? report.eligibleRows)} registros no recorte de análise.
    <span id="updated-status" role="status">Atualizado em ${timestamp}</span></p>
    <details><summary>Ver o tratamento aplicado aos dados</summary>
    <div class="quality-counts">${counts.map(([name, value]) =>
      `<div><strong>${integerFormat.format(value ?? 0)}</strong><span>${name}</span></div>`).join("")}</div>
    <p>Textos, códigos, semestres e contagens são validados antes dos indicadores. Duplicatas exatas com identidade
    de turma confirmada são removidas. Registros conflitantes são preservados e sinalizados.
    Matrículas acima da capacidade continuam na análise.</p>
    ${report.conflictGroups ? '<p class="quality-warning">Há versões conflitantes de turmas. Os resultados incluem esses registros e devem ser lidos considerando esse conflito.</p>' : ""}
    ${issues ? `<ul class="quality-issues">${issues}</ul>` : ""}
    <p class="muted">O arquivo original é preservado. A preparação ocorre em memória em cada consulta.</p>
    </details></section>`;
}

function statisticalOverview(stats) {
  if (!stats) return "";
  const o = stats.occupancy, c = stats.concentration, a = stats.association;
  const index = value => value == null ? "Indefinido no recorte" : indexFormat.format(value);
  const points = value => value == null ? "Sem registro" : decimalFormat.format(value * 100) + " p.p.";
  const prominent = [
    ["Mediana de ocupação", format(o.median, true), "Turma central da distribuição"],
    ["Desvio-padrão", points(o.standardDeviation), "Dispersão entre turmas"],
    ["Gini das matrículas", index(c.gini), "Concentração por disciplina · 0 a 1"],
    ["Pearson", index(a.pearson), "Capacidade × ocupação · −1 a 1"],
  ];
  const entries = [
    ["Turmas analisadas", integerFormat.format(o.n)],
    ["Média aritmética da ocupação", format(o.mean, true)],
    ["Primeiro quartil (Q1)", format(o.q1, true)], ["Terceiro quartil (Q3)", format(o.q3, true)],
    ["Intervalo interquartil (IQR)", points(o.iqr)], ["Desvio absoluto mediano (MAD)", points(o.mad)],
    ["Coeficiente de variação", format(o.coefficientVariation, true)],
    ["Assimetria", index(o.skewness)], ["Excesso de curtose", index(o.excessKurtosis)],
    ["Abaixo da cerca de Tukey", format(o.outliersLow)], ["Acima da cerca de Tukey", format(o.outliersHigh)],
    ["Disciplinas com oferta", integerFormat.format(c.disciplines)],
    ["HHI em frações", index(c.hhi)], ["Disciplinas efetivas (1/HHI)", index(c.effectiveDisciplines)],
    ["Entropia normalizada", index(c.normalizedEntropy)], ["Parcela das 20% maiores disciplinas", format(c.top20Share, true)],
    ["Spearman", index(a.spearman)], ["R² do ajuste linear", index(a.rSquared)],
  ];
  return `<section class="statistical-overview" aria-label="Resumo estatístico das turmas consolidadas">
    <div class="statistical-heading"><h3>Estatísticas das turmas consolidadas</h3><span>${o.n} turmas</span></div>
    <div class="statistical-cards">${prominent.map(([name, value, note]) =>
      `<div><span>${name}</span><strong>${value}</strong><small>${note}</small></div>`).join("")}</div>
    <details><summary>Explorar os indicadores estatísticos</summary>
    <dl class="statistical-values">${entries.map(([name, value]) =>
      `<div><dt>${name}</dt><dd>${value}</dd></div>`).join("")}</dl>
    <p class="statistical-caution">Cada turma tem o mesmo peso nas estatísticas de ocupação. A ocupação geral dos
    cartões anteriores pondera pela capacidade. Os coeficientes descrevem as associações do recorte.
    Capacidade também está no denominador da ocupação.</p></details></section>`;
}

function panelHeading(id, title, count) {
  return `<div class="panel-heading"><h3 id="${id}-titulo">${escapeHtml(title)}</h3>
    <span>${count} gráficos</span></div>`;
}

function dashboard({paineis, quality, generatedAt}) {
  const mcId = "matematica-computacional";
  const mc = paineis.find(panel => panel.id === mcId);
  const cct = paineis.filter(panel => panel.id !== mcId);
  const mcSections = mc.sections.map((section, i) => ({...section, id: `matcomp-secao-${i + 1}`}));
  const mcNav = links(mcSections.map(section => [section.id, section.title]));
  const cctNav = links(cct.map(panel => [panel.id, panel.title]));
  const mcCount = mc.sections.reduce((sum, section) => sum + section.plots.length, 0);
  const cctCount = cct.reduce((sum, panel) => sum + panel.sections.reduce((n, s) => n + s.plots.length, 0), 0);
  return `${dataQuality(quality, generatedAt)}<section class="area mc-area" id="${mcId}">
    <div class="area-heading"><div><p class="eyebrow">01 / FOCO NO CURSO</p><h2>${escapeHtml(mc.title)}</h2></div><span class="count-badge">${mcCount} gráficos</span></div>
    <p class="area-description">${escapeHtml(mc.description)}</p>
    ${summaryCards(mc.summary)}
    ${statisticalOverview(mc.statisticalSummary)}
    <nav class="section-nav" aria-label="Seções de Matemática Computacional">${mcNav}</nav>
    <p class="interaction-note">Passe o mouse para ver detalhes. Clique nas legendas para comparar séries.
    Com o teclado, use Tab e as setas nos gráficos.</p>
    ${mcSections.map(section => `<section class="panel" id="${section.id}" aria-labelledby="${section.id}-titulo">
      ${panelHeading(section.id, section.title, section.plots.length)}${chartGrid(section.plots, "h4")}
      <a class="back" href="#${mcId}">↑ Início de Matemática Computacional</a></section>`).join("")}
    </section><section class="area cct-area" id="cct">
    <div class="area-heading"><div><p class="eyebrow">02 / VISÃO DO CENTRO</p><h2>Resultados gerais do CCT</h2></div><span class="count-badge">${cctCount} gráficos</span></div>
    <p class="area-description">Oferta presencial do Centro de Ciências e Tecnologia. Os rankings por natureza curricular usam os códigos classificados nas matrizes de referência.</p>
    ${summaryCards(cct.find(panel => panel.id === "evolucao").summary)}
    ${statisticalOverview(cct.find(panel => panel.statisticalSummary)?.statisticalSummary)}
    <nav class="section-nav" aria-label="Seções do CCT">${cctNav}</nav>
    <p class="interaction-note">Passe o mouse para ver detalhes. As tabelas abaixo dos gráficos apresentam os valores completos.</p>
    ${cct.map(panel => `<section class="panel" id="${escapeHtml(panel.id)}" aria-labelledby="${escapeHtml(panel.id)}-titulo">
      ${panelHeading(panel.id, panel.title, panel.sections.reduce((sum, section) => sum + section.plots.length, 0))}
      ${panel.description ? `<p class="panel-description">${escapeHtml(panel.description)}</p>` : ""}
      ${panel.sections.map(section => section.title
        ? `<h4 class="section-heading">${escapeHtml(section.title)}</h4>${chartGrid(section.plots, "h5")}`
        : chartGrid(section.plots, "h4")).join("")}
      <a class="back" href="#cct">↑ Início dos resultados do CCT</a></section>`).join("")}</section>`;
}

function chartConfiguration(plot) {
  const kind = plot.formato ?? plot.spec.type;
  const spec = plot.spec ?? {};
  const rows = records(plot);
  const horizontal = kind === "ranking" || kind === "horizontalBar";
  const radial = ["donut", "pie", "radar"].includes(kind);
  const circular = kind === "donut" || kind === "pie";
  const points = ["scatter", "bubble", "statisticalScatter"].includes(kind);
  const statistical = kind === "statisticalScatter";
  const numericX = spec.numericX === true;
  const percent = plot.rankingPercent ?? spec.valueFormat?.style === "percent";
  const stacked = ["stackedBar", "stackedPercent", "area"].includes(kind);
  const line = ["line", "area", "distributionBand"].includes(kind);
  const type = kind === "donut" ? "doughnut" : kind === "pie" || kind === "radar" ? kind :
    points ? "bubble" : line ? "line" : "bar";
  const labels = kind === "ranking" ? plot.rows.map(row => row[0]) :
    rows.map(({values}) => values[horizontal ? spec.y : spec.x]);
  const series = kind === "ranking" ? ["Resultado"] : [horizontal ? spec.x : spec.y].flat();
  const datasets = points ? [{
    label: "Turmas",
    data: rows.map(({values}, rowIndex) => ({
      x: values[spec.x], y: values[spec.y],
      r: kind === "bubble" ? Math.sqrt(values[spec.size]) * 3 : 2.5 + Math.sqrt(values[spec.size] ?? 1) * 1.6,
      rowIndex,
    })),
    backgroundColor: rows.map(({values}) => !statistical && values[spec.y] > values[spec.x] ? colors[4] + "b3" : colors[0] + "80"),
    borderColor: rows.map(({values}) => !statistical && values[spec.y] > values[spec.x] ? colors[4] : colors[0]),
    borderWidth: 1, hoverBorderWidth: 2,
  }] : series.map((key, i) => ({
    label: key,
    data: kind === "ranking" ? plot.rankingValues : rows.map(({values}) =>
      numericX && values[key] != null ? {x: values[spec.x], y: values[key]} : values[key]),
    backgroundColor: circular ? labels.map(label => colors[(spec.categoryOrder ?? labels).indexOf(label) % colors.length]) :
      colors[i] + (line || kind === "radar" ? "35" : "d9"),
    borderColor: circular ? "#ffffff" : colors[i],
    borderWidth: circular ? 3 : line || kind === "radar" ? 2 : 0,
    borderRadius: !radial && !line ? 4 : 0,
    pointRadius: 3.5, pointHoverRadius: 6, pointHitRadius: 12,
    fill: kind === "area" ? (i === 0 ? "origin" : "-1") : kind === "radar",
    tension: numericX ? 0 : 0.15,
    spanGaps: false,
    ...(spec.stepped ? {stepped: spec.stepped} : {}),
    ...(numericX ? {pointRadius: rows.length > 40 ? 0 : 2.5} : {}),
    ...(kind === "distributionBand" ? {
      fill: i === 2 ? 0 : false, tension: 0, borderColor: i === 1 ? colors[0] : colors[0] + "70",
      backgroundColor: colors[0] + "20", borderWidth: i === 1 ? 2.5 : 1, pointRadius: i === 1 ? 3 : 2,
    } : {}),
    ...(kind === "mixed" ? {type: spec.lineSeries.includes(key) ? "line" : "bar",
      borderWidth: spec.lineSeries.includes(key) ? 2.5 : 0, order: spec.lineSeries.includes(key) ? 0 : 1} : {}),
    ...(line || kind === "mixed" ? {segment: {
      borderDash: ctx => String(labels[ctx.p1DataIndex]).endsWith("*") ? [5, 5] : undefined,
    }} : {}),
  }));

  if (points && kind === "scatter") {
    const maximum = Math.max(...datasets[0].data.flatMap(point => [point.x, point.y]), 1);
    datasets.push({type: "line", label: "100% de ocupação", data: [{x: 0, y: 0}, {x: maximum, y: maximum}],
      borderColor: "#8794a5", borderDash: [5, 5], borderWidth: 1, pointRadius: 0, pointHitRadius: 0, fill: false});
  }
  if (statistical && Number.isFinite(spec.trend?.slope) && Number.isFinite(spec.trend?.intercept)) {
    const xs = rows.map(({values}) => values[spec.x]);
    const ends = [Math.min(...xs), Math.max(...xs)];
    datasets.push({
      type: "line", label: "Ajuste linear descritivo",
      data: ends.map(x => ({x, y: spec.trend.intercept + spec.trend.slope * x})),
      borderColor: colors[2], borderDash: [6, 4], borderWidth: 2, pointRadius: 0, fill: false,
    });
  }
  const options = {
    responsive: true, maintainAspectRatio: false, animation: false,
    locale: "pt-BR", layout: {padding: {top: 8, right: 12}},
    interaction: {mode: points || circular || kind === "radar" ? "nearest" : "index", intersect: points || circular},
    plugins: {
      legend: {display: radial || series.length > 1 || points, position: "bottom",
        labels: {usePointStyle: true, pointStyle: "circle", boxWidth: 8, boxHeight: 8, padding: 18, font: {size: 11}}},
      tooltip: {
        backgroundColor: "#142940", titleColor: "#ffffff", bodyColor: "#e4ecf7",
        padding: 13, cornerRadius: 9, bodySpacing: 5,
        filter: item => !points || item.datasetIndex === 0,
        callbacks: {
          title: items => items.length ? wrapLabel(points ? rows[items[0].dataIndex].values[spec.label] ?? "Turmas consolidadas" :
            numericX ? `${spec.x}: ${format(rows[items[0].dataIndex].values[spec.x], spec.xValueFormat?.style === "percent")}` :
              labels[items[0].dataIndex], 48) : "",
          label: item => {
            const row = rows[item.dataIndex];
            if (statistical) return [
              `${spec.x}: ${format(row.values[spec.x], spec.xValueFormat?.style === "percent")}`,
              `${spec.y}: ${format(row.values[spec.y], percent)}`,
            ];
            if (points) return [`${format(row.values[spec.x])} vagas · ${format(row.values[spec.y])} matrículas`,
              `${format(row.values[spec.size])} turmas · ${format(row.values[spec.y] / row.values[spec.x], true)} de ocupação`];
            if (kind === "ranking") return plot.rows[item.dataIndex][1];
            if (circular) {
              const total = plot.rows.reduce((sum, values) => sum + values[1], 0);
              return [`${format(item.raw)} de ${format(total)} turmas`, `${format(item.raw / total, true)} do total`];
            }
            if (kind === "stackedBar") {
              const total = series.reduce((sum, key) => sum + (row.values[key] ?? 0), 0);
              return `${item.dataset.label}: ${format(item.raw)} (${format(total ? item.raw / total : 0, true)})`;
            }
            return `${item.dataset.label}: ${measure(numericX ? item.raw.y : item.raw, spec.valueFormat)}`;
          },
          afterBody: items => {
            if (!items.length) return [];
            const index = items[0].dataIndex;
            const value = rows[index].values;
            const detail = (plot.tooltips?.[index] ?? "").split("\n").filter(Boolean);
            const capacity = value.Vagas ?? value.Capacidade;
            if (capacity && value["Matrículas"] != null && !points) {
              detail.push(`Ocupação: ${format(value["Matrículas"] / capacity, true)}`);
            }
            if (kind === "stackedBar") {
              const total = series.reduce((sum, key) => sum + (value[key] ?? 0), 0);
              detail.push(`Total: ${format(total)} turmas`);
            }
            return detail.flatMap(text => wrapLabel(text, 55));
          },
        },
      },
    },
  };
  if (kind === "donut") options.cutout = "66%";
  if (kind === "radar") {
    options.scales = {r: {beginAtZero: true, suggestedMax: 1, ticks: {callback: value => format(value, true), stepSize: 0.25},
      pointLabels: {font: {size: 10}, callback: label => wrapLabel(label, 20)}, grid: {color: "#e0e7ef"}}};
  } else if (!radial) {
    options.indexAxis = horizontal ? "y" : "x";
    const valueScale = {
      beginAtZero: true, stacked, grid: {color: "#edf1f6"}, border: {display: false},
      ticks: {maxTicksLimit: 6, callback: value => measure(value, spec.valueFormat ?? (percent ? {style: "percent"} : {}))},
    };
    if (percent) valueScale.suggestedMax = 1;
    if (spec.yDomain && !horizontal) {
      valueScale.suggestedMin = spec.yDomain[0];
      valueScale.suggestedMax = spec.yDomain[1];
      if (spec.yDomain[0] < 0) {
        valueScale.min = spec.yDomain[0];
        valueScale.max = spec.yDomain[1];
      }
    }
    if (kind === "stackedPercent") valueScale.max = 1;
    const categoryScale = {stacked, grid: {display: false}, border: {display: false},
      ticks: {autoSkip: !horizontal, maxRotation: 0, font: {size: 11},
        callback: function(value) { return horizontal ? wrapLabel(this.getLabelForValue(value), this.chart.width < 420 ? 20 : 34) : this.getLabelForValue(value); }}};
    options.scales = horizontal ? {x: valueScale, y: categoryScale} : {x: categoryScale, y: valueScale};
    if (points) {
      options.scales.x = {type: "linear", beginAtZero: true, grid: {color: "#edf1f6"}, title: {display: true, text: spec.x}};
      options.scales.y.title = {display: true, text: spec.y};
    }
    if (numericX) {
      options.scales.x = {type: "linear", beginAtZero: true, grid: {color: "#edf1f6"},
        title: {display: true, text: spec.x}, ticks: {callback: value => format(value, spec.xValueFormat?.style === "percent")}};
    }
  }
  return {type, data: {labels: points || numericX ? undefined : labels, datasets}, options};
}

function enableKeyboard(canvas, chart) {
  const status = document.getElementById(canvas.dataset.plotId + "-leitura");
  let position = -1;
  function clear() {
    chart.setActiveElements([]);
    chart.tooltip.setActiveElements([], {x: 0, y: 0});
    chart.update("none");
  }
  canvas.addEventListener("keydown", event => {
    if (event.key === "Escape") { clear(); return; }
    if (!["ArrowRight", "ArrowLeft", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const elements = chart.data.datasets.flatMap((dataset, datasetIndex) =>
      chart.isDatasetVisible(datasetIndex) ? dataset.data.flatMap((value, index) =>
        value == null || ["100% de ocupação", "Ajuste linear descritivo"].includes(dataset.label) ||
          (["pie", "doughnut"].includes(chart.config.type) && !chart.getDataVisibility(index))
          ? [] : [{datasetIndex, index}]) : []);
    if (!elements.length) return;
    if (event.key === "Home") position = 0;
    else if (event.key === "End") position = elements.length - 1;
    else position = (position + (event.key === "ArrowLeft" || event.key === "ArrowUp" ? -1 : 1) + elements.length) % elements.length;
    const selected = elements[position];
    const element = chart.getDatasetMeta(selected.datasetIndex).data[selected.index];
    chart.setActiveElements([selected]);
    chart.tooltip.setActiveElements([selected], element.getCenterPoint());
    chart.update("none");
    status.textContent = [...chart.tooltip.title, ...chart.tooltip.body.flatMap(body => body.lines),
      ...chart.tooltip.afterBody].join(". ");
  });
  canvas.addEventListener("blur", clear);
}

function mountCharts(plots) {
  const create = canvas => {
    if (chartInstances.has(canvas.dataset.plotId)) return;
    const plot = plots.get(canvas.dataset.plotId);
    const chart = new Chart(canvas, chartConfiguration(plot));
    chartInstances.set(plot.id, chart);
    enableKeyboard(canvas, chart);
  };
  const canvases = document.querySelectorAll("canvas[data-plot-id]");
  if (!("IntersectionObserver" in window)) { canvases.forEach(create); return () => {}; }
  const observer = new IntersectionObserver(entries => {
    entries.filter(entry => entry.isIntersecting).forEach(entry => {
      observer.unobserve(entry.target);
      create(entry.target);
    });
  }, {rootMargin: "500px"});
  canvases.forEach(canvas => {
    observer.observe(canvas);
    canvas.addEventListener("focus", () => {
      if (!chartInstances.has(canvas.dataset.plotId)) {
        observer.unobserve(canvas);
        create(canvas);
      }
    }, {once: true});
  });
  return () => observer.disconnect();
}

async function loadDashboard() {
  if (dashboardLoading) return;
  dashboardLoading = true;
  const main = document.getElementById("painel");
  const index = document.getElementById("indice");
  const refresh = document.getElementById("refresh-data");
  main.setAttribute("aria-busy", "true");
  if (refresh) {
    refresh.disabled = true;
    refresh.textContent = "Processando…";
  }
  function clearCharts() {
    stopMounting();
    chartInstances.forEach(chart => chart.destroy());
    chartInstances.clear();
  }
  try {
    if (typeof Chart === "undefined") throw new Error("Não foi possível carregar o Chart.js local.");
    Chart.defaults.font.family = '"Segoe UI", system-ui, sans-serif';
    Chart.defaults.color = "#64748b";
    const response = await fetch("/api/painel");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    clearCharts();
    main.innerHTML = dashboard(data);
    index.innerHTML = links([["matematica-computacional", "01 · Matemática Computacional"], ["cct", "02 · Resultados gerais do CCT"]]);
    index.hidden = false;
    const plots = new Map(data.paineis.flatMap(panel => panel.sections.flatMap(section =>
      section.plots.map(plot => [plot.id, plot]))));
    stopMounting = mountCharts(plots);
    document.getElementById("chart-count").textContent = `${plots.size} visualizações`;
    document.getElementById(location.hash.slice(1))?.scrollIntoView();
  } catch (error) {
    console.error(error);
    clearCharts();
    main.innerHTML = '<div class="empty-state" role="alert"><p>Não foi possível processar os dados do painel. Confira o JSON e tente novamente.</p><button class="refresh-button" id="refresh-data" type="button">Tentar novamente ↻</button></div>';
  } finally {
    dashboardLoading = false;
    main.setAttribute("aria-busy", "false");
    document.getElementById("refresh-data")?.addEventListener("click", loadDashboard);
  }
}

loadDashboard();

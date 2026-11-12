import { format, measure, records } from '../../lib/format.js';

let chartLibrary;

export function loadChartLibrary() {
  chartLibrary ??= new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = '/vendor/chart.umd.min.js';
    script.onload = () => {
      const Chart = window.Chart;
      if (!Chart) {
        script.remove();
        reject(new Error('Não foi possível carregar o Chart.js.'));
        return;
      }
      Chart.defaults.font.family = '"Segoe UI", system-ui, sans-serif';
      Chart.defaults.color = '#64748b';
      resolve(Chart);
    };
    script.onerror = () => {
      script.remove();
      reject(new Error('Não foi possível carregar o Chart.js.'));
    };
    document.head.append(script);
  }).catch(error => {
    chartLibrary = undefined;
    throw error;
  });
  return chartLibrary;
}

export function drawChart(Chart, canvas, status, plot) {
  const chart = new Chart(canvas, chartConfiguration(plot));
  const stopKeyboard = enableKeyboard(canvas, chart, status);
  return () => {
    stopKeyboard();
    chart.destroy();
  };
}

const colors = ["#3276dd", "#149485", "#e7a23b", "#9164ca", "#de6474", "#66798d"];

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
    rows.map(({ values }) => values[horizontal ? spec.y : spec.x]);
  const series = kind === "ranking" ? ["Resultado"] : [horizontal ? spec.x : spec.y].flat();
  const datasets = points ? [{
    label: "Turmas",
    data: rows.map(({ values }, rowIndex) => ({
      x: values[spec.x], y: values[spec.y],
      r: kind === "bubble" ? Math.sqrt(values[spec.size]) * 3 : 2.5 + Math.sqrt(values[spec.size] ?? 1) * 1.6,
      rowIndex,
    })),
    backgroundColor: rows.map(({ values }) => !statistical && values[spec.y] > values[spec.x] ? colors[4] + "b3" : colors[0] + "80"),
    borderColor: rows.map(({ values }) => !statistical && values[spec.y] > values[spec.x] ? colors[4] : colors[0]),
    borderWidth: 1, hoverBorderWidth: 2,
  }] : series.map((key, i) => ({
    label: key,
    data: kind === "ranking" ? plot.rankingValues : rows.map(({ values }) =>
      numericX && values[key] != null ? { x: values[spec.x], y: values[key] } : values[key]),
    backgroundColor: circular ? labels.map(label => colors[(spec.categoryOrder ?? labels).indexOf(label) % colors.length]) :
      colors[i] + (line || kind === "radar" ? "35" : "d9"),
    borderColor: circular ? "#ffffff" : colors[i],
    borderWidth: circular ? 3 : line || kind === "radar" ? 2 : 0,
    borderRadius: !radial && !line ? 4 : 0,
    pointRadius: 3.5, pointHoverRadius: 6, pointHitRadius: 12,
    fill: kind === "area" ? (i === 0 ? "origin" : "-1") : kind === "radar",
    tension: numericX ? 0 : 0.15,
    spanGaps: false,
    ...(spec.stepped ? { stepped: spec.stepped } : {}),
    ...(numericX ? { pointRadius: rows.length > 40 ? 0 : 2.5 } : {}),
    ...(kind === "distributionBand" ? {
      fill: i === 2 ? 0 : false, tension: 0, borderColor: i === 1 ? colors[0] : colors[0] + "70",
      backgroundColor: colors[0] + "20", borderWidth: i === 1 ? 2.5 : 1, pointRadius: i === 1 ? 3 : 2,
    } : {}),
    ...(kind === "mixed" ? {
      type: spec.lineSeries.includes(key) ? "line" : "bar",
      borderWidth: spec.lineSeries.includes(key) ? 2.5 : 0, order: spec.lineSeries.includes(key) ? 0 : 1
    } : {}),
    ...(line || kind === "mixed" ? {
      segment: {
        borderDash: ctx => String(labels[ctx.p1DataIndex]).endsWith("*") ? [5, 5] : undefined,
      }
    } : {}),
  }));

  if (points && kind === "scatter") {
    const maximum = Math.max(...datasets[0].data.flatMap(point => [point.x, point.y]), 1);
    datasets.push({
      type: "line", label: "100% de ocupação", data: [{ x: 0, y: 0 }, { x: maximum, y: maximum }],
      borderColor: "#8794a5", borderDash: [5, 5], borderWidth: 1, pointRadius: 0, pointHitRadius: 0, fill: false
    });
  }
  if (statistical && Number.isFinite(spec.trend?.slope) && Number.isFinite(spec.trend?.intercept)) {
    const xs = rows.map(({ values }) => values[spec.x]);
    const ends = [Math.min(...xs), Math.max(...xs)];
    datasets.push({
      type: "line", label: "Ajuste linear descritivo",
      data: ends.map(x => ({ x, y: spec.trend.intercept + spec.trend.slope * x })),
      borderColor: colors[2], borderDash: [6, 4], borderWidth: 2, pointRadius: 0, fill: false,
    });
  }
  const options = {
    responsive: true, maintainAspectRatio: false, animation: false,
    locale: "pt-BR", layout: { padding: { top: 8, right: 12 } },
    interaction: { mode: points || circular || kind === "radar" ? "nearest" : "index", intersect: points || circular },
    plugins: {
      legend: {
        display: radial || series.length > 1 || points, position: "bottom",
        labels: { usePointStyle: true, pointStyle: "circle", boxWidth: 8, boxHeight: 8, padding: 18, font: { size: 11 } }
      },
      tooltip: {
        backgroundColor: "#142940", titleColor: "#ffffff", bodyColor: "#e4ecf7",
        padding: 13, cornerRadius: 9, bodySpacing: 5,
        filter: item => !points || item.datasetIndex === 0,
        callbacks: {
          title: items => items.length ? wrapLabel(points ? rows[items[0].dataIndex].values[spec.label] ?? "Turmas do recorte" :
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
    options.scales = {
      r: {
        beginAtZero: true, suggestedMax: 1, ticks: { callback: value => format(value, true), stepSize: 0.25 },
        pointLabels: { font: { size: 10 }, callback: label => wrapLabel(label, 20) }, grid: { color: "#e0e7ef" }
      }
    };
  } else if (!radial) {
    options.indexAxis = horizontal ? "y" : "x";
    const valueScale = {
      beginAtZero: true, stacked, grid: { color: "#edf1f6" }, border: { display: false },
      ticks: { maxTicksLimit: 6, callback: value => measure(value, spec.valueFormat ?? (percent ? { style: "percent" } : {})) },
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
    const categoryScale = {
      stacked, grid: { display: false }, border: { display: false },
      ticks: {
        autoSkip: !horizontal, maxRotation: 0, font: { size: 11 },
        callback: function (value) { return horizontal ? wrapLabel(this.getLabelForValue(value), this.chart.width < 420 ? 20 : 34) : this.getLabelForValue(value); }
      }
    };
    options.scales = horizontal ? { x: valueScale, y: categoryScale } : { x: categoryScale, y: valueScale };
    if (points) {
      options.scales.x = { type: "linear", beginAtZero: true, grid: { color: "#edf1f6" }, title: { display: true, text: spec.x } };
      options.scales.y.title = { display: true, text: spec.y };
    }
    if (numericX) {
      options.scales.x = {
        type: "linear", beginAtZero: true, grid: { color: "#edf1f6" },
        title: { display: true, text: spec.x }, ticks: { callback: value => format(value, spec.xValueFormat?.style === "percent") }
      };
    }
  }
  return { type, data: { labels: points || numericX ? undefined : labels, datasets }, options };
}

function enableKeyboard(canvas, chart, status) {
  let position = -1;
  function clear() {
    chart.setActiveElements([]);
    chart.tooltip.setActiveElements([], { x: 0, y: 0 });
    chart.update("none");
  }
  function readPoint(event) {
    if (event.key === "Escape") { clear(); return; }
    if (!["ArrowRight", "ArrowLeft", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const elements = chart.data.datasets.flatMap((dataset, datasetIndex) =>
      chart.isDatasetVisible(datasetIndex) ? dataset.data.flatMap((value, index) =>
        value == null || ["100% de ocupação", "Ajuste linear descritivo"].includes(dataset.label) ||
          (["pie", "doughnut"].includes(chart.config.type) && !chart.getDataVisibility(index))
          ? [] : [{ datasetIndex, index }]) : []);
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
  }
  canvas.addEventListener("keydown", readPoint);
  canvas.addEventListener("blur", clear);
  return () => {
    canvas.removeEventListener("keydown", readPoint);
    canvas.removeEventListener("blur", clear);
  };
}

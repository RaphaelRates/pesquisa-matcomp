"""Calcula os gráficos e gera o painel local a partir do JSON de turmas."""

import argparse
from datetime import datetime, timezone
from html import escape
import json
import math
from pathlib import Path
import webbrowser
from services.config import DEFAULT_DATA, TITLE, PROJECT_ROOT
from services.dashboard.payload import dashboard_data


PALETTE = ("#2675ad", "#247d62", "#b55a13", "#854e9e")


def number(value, percent=False):
    if value is None:
        return "Sem registro"
    if percent:
        return f"{value:.1%}".replace(".", ",")
    return f"{value:,.0f}".replace(",", ".")


def plot_data(plot):
    return [dict(zip(plot["columns"], row, strict=True)) for row in plot["rows"]]


def row_details(plot):
    return plot.get("tooltips") or [""] * len(plot["rows"])


def tooltip_attributes(heading, value, details=""):
    lines = "\n".join(part for part in (heading, value, details) if part)
    return f'tabindex="0" data-tooltip="{escape(lines)}" aria-label="{escape(lines.replace(chr(10), ". "))}"'


def related_values(row, series, key, percent):
    return "\n".join(f"{other}: {number(row[other], percent)}" for other in series if other != key)


def vertical(plot):
    spec = plot["spec"]
    rows = plot_data(plot)
    series = spec["y"]
    stacked = spec["type"] == "stackedBar"
    percent = spec.get("valueFormat", {}).get("style") == "percent"
    heights = [
        sum(row[key] or 0 for key in series) if stacked else max(row[key] or 0 for key in series)
        for row in rows
    ]
    bound = max(heights)
    top = spec.get("yDomain", [0, math.ceil(bound / 4) * 4 or 1])[1]
    left, bottom, width, height = 77, 210, 619, 170
    slot = width / len(rows)
    marks = []
    for i in range(5):
        y = bottom - height * i / 4
        tick = number(top * i / 4, percent)
        marks.append(f'<line x1="{left}" x2="{left + width}" y1="{y}" y2="{y}" class="gridline"/>')
        marks.append(f'<text x="{left - 9}" y="{y + 4}" text-anchor="end">{tick}</text>')
    for i, (row, details) in enumerate(zip(rows, row_details(plot), strict=True)):
        x = left + slot * (i + 0.5)
        category = str(row[spec["x"]])
        marks.append(f'<text x="{x}" y="233" text-anchor="middle">{escape(category)}</text>')
        bar_width = slot * 0.64 / (1 if stacked else len(series))
        offset = 0
        for j, key in enumerate(series):
            value = row[key]
            if value is None:
                continue
            rect_x = x - slot * 0.32 + (0 if stacked else j * bar_width)
            size = height * value / top
            draw_width = bar_width
            if stacked and not value:
                draw_width /= len(series)
                rect_x += j * draw_width
            draw_height = max(size, 2)
            rect_y = bottom - offset - draw_height
            if stacked:
                total = heights[i]
                related = f"Parcela do semestre: {number(value / total, True)}" if total else ""
                related = "\n".join(part for part in (f"Total de turmas: {number(total)}", related) if part)
            else:
                related = related_values(row, series, key, percent)
                capacity = row.get("Vagas", row.get("Capacidade"))
                if not percent and capacity and "Matrículas" in row:
                    related += f'\nOcupação: {number(row["Matrículas"] / capacity, True)}'
            attrs = tooltip_attributes(category, f"{key}: {number(value, percent)}",
                                       "\n".join(part for part in (related, details) if part))
            marks.append(
                f'<rect x="{rect_x}" y="{rect_y}" width="{draw_width}" height="{draw_height}" '
                f'fill="{PALETTE[j]}" {attrs}></rect>'
            )
            if stacked:
                offset += size
    axis = escape(spec.get("yLabel", "Total"))
    marks.append(f'<text x="{left}" y="22">{axis}</text>')
    legend = "".join(
        f'<span><i style="background:{PALETTE[i]}"></i>{escape(key)}</span>'
        for i, key in enumerate(series)
    )
    return (
        f'<div class="scroll"><svg viewBox="0 0 720 249" role="group" aria-label="{escape(plot["title"])}">'
        f'{"".join(marks)}</svg></div><div class="legend">{legend}</div>'
    )


def bar_item(label, value, width, color, measure, details):
    attrs = tooltip_attributes(label, f"{measure}: {value}", details)
    return (
        f'<li {attrs}><div class="bar-label"><span>{escape(label)}</span><b>{escape(value)}</b></div>'
        f'<div class="track" aria-hidden="true"><div style="width:{width:.4f}%;background:{color}"></div></div></li>'
    )


def horizontal(plot):
    if plot.get("formato") == "ranking":
        items = [bar_item(label, value, width, PALETTE[0], "Resultado", details)
                 for (label, value, width), details in zip(plot["rows"], row_details(plot), strict=True)]
        return '<ol class="bars">' + "".join(items) + "</ol>"
    spec = plot["spec"]
    rows = plot_data(plot)
    series = spec["x"] if isinstance(spec["x"], list) else [spec["x"]]
    percent = spec.get("valueFormat", {}).get("style") == "percent"
    ceiling = max(row[key] or 0 for key in series for row in rows)
    top = max(spec.get("xDomain", [0, 0])[1], ceiling) or 1
    items = []
    for row, details in zip(rows, row_details(plot), strict=True):
        label = str(row[spec["y"]])
        for i, key in enumerate(series):
            value = row[key]
            full_label = f"{label} · {key}" if len(series) > 1 else label
            context = "\n".join(part for part in (related_values(row, series, key, percent), details) if part)
            items.append(bar_item(full_label, number(value, percent), (value or 0) * 100 / top,
                                  PALETTE[i], key, context))
    return '<ul class="bars">' + "".join(items) + "</ul>"


def heatmap(plot):
    spec = plot["spec"]
    rows = plot_data(plot)
    x, y, measure = (spec[key] for key in ("x", "y", "value"))
    columns = spec.get("xOrder", list(dict.fromkeys(row[x] for row in rows)))
    labels = spec.get("yOrder", list(dict.fromkeys(row[y] for row in rows)))
    values = {(row[x], row[y]): row[measure] for row in rows}
    details = {(row[x], row[y]): detail for row, detail in zip(rows, row_details(plot), strict=True)}
    maximum = max(value for value in values.values() if value is not None)
    low, high = spec.get("colorDomain", [0, maximum or 1])
    percent = spec.get("valueFormat", {}).get("style") == "percent"
    cells = [f'<tr><th scope="col">{escape(y)}</th>']
    cells.extend(f'<th scope="col">{escape(str(col))}</th>' for col in columns)
    cells.append("</tr>")
    for label in labels:
        cells.append(f'<tr><th scope="row">{escape(str(label))}</th>')
        for col in columns:
            value = values.get((col, label))
            attrs = tooltip_attributes(f"{label} · {col}", f"{measure}: {number(value, percent)}",
                                       details.get((col, label), ""))
            if value is None:
                cells.append(f'<td class="missing" {attrs}>—</td>')
                continue
            intensity = max(0, min(1, (value - low) / (high - low)))
            cells.append(f'<td style="--intensity:{intensity * 74:.1f}%" {attrs}>{number(value, percent)}</td>')
        cells.append("</tr>")
    return f'<div class="scroll"><table class="heat" aria-label="{escape(plot["title"])}">{"".join(cells)}</table></div>'


def data_table(plot):
    def cell(value):
        if value is None:
            return "—"
        if isinstance(value, float):
            return escape(str(value).replace(".", ","))
        return escape(str(value))

    header = "".join(f'<th scope="col">{escape(col)}</th>' for col in plot["columns"])
    body = "".join("<tr>" + "".join(f"<td>{cell(value)}</td>" for value in row) + "</tr>" for row in plot["rows"])
    return (
        '<details><summary>Ver dados do gráfico</summary><div class="scroll">'
        f'<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div></details>'
    )


def figure(plot, heading):
    kind = plot["formato"] if "formato" in plot else plot["spec"]["type"]
    render = {
        "ranking": horizontal, "horizontalBar": horizontal, "heatmap": heatmap,
        "bar": vertical, "stackedBar": vertical,
    }.get(kind)
    if plot["rows"] and (kind != "heatmap" or any(row[-1] is not None for row in plot["rows"])):
        content = (render(plot) if render else "<p>Visualização disponível no painel web.</p>") + data_table(plot)
    else:
        content = "<p>Sem turmas neste recorte.</p>"
    return (
        f'<article id="{escape(plot["id"])}"><{heading}>{escape(plot["title"])}</{heading}>'
        f'<p class="description">{escape(plot["description"])}</p>{content}</article>'
    )


STYLE = """
:root {color-scheme:light; --bg:#f3f6f7; --ink:#172b35; --surface:#fff; --muted:#4b626e; --line:#d6e1e6;
       font-family:system-ui,sans-serif; color:var(--ink); background:var(--bg)}
* {box-sizing:border-box} body {margin:0} header,main {max-width:1160px; margin:auto; padding:1.35rem}
header {padding-top:2.1rem} h1,h2,h3,h4,h5,p {margin:0 0 .6rem} h1 {font-size:clamp(1.7rem,4vw,2.6rem)}
h2 {font-size:clamp(1.4rem,3vw,1.85rem)} h3 {font-size:1.25rem} h4,h5 {font-size:1.05rem}
.eyebrow {color:#14674e; font-weight:700; letter-spacing:.08em; font-size:.8rem}
.description,header p {color:var(--muted); line-height:1.55}
nav {margin-top:1.3rem} nav ul {list-style:none; display:flex; flex-wrap:wrap; gap:.5rem; margin:.55rem 0 0; padding:0}
nav a {display:block; padding:.45rem .75rem; border:1px solid var(--line); border-radius:.45rem; background:var(--surface)}
a {color:#175e8b; text-underline-offset:.18em}
#indice a {font-weight:650}
#indice a[href="#matematica-computacional"] {background:#14674e; border-color:#14674e; color:white}
.chart-grid {display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,430px),1fr)); gap:1rem}
.area {scroll-margin-top:1rem; border-top:3px solid #2675ad; padding-top:1.35rem}
.area + .area {margin-top:3rem}
.area nav {margin-bottom:1.2rem}
.panel {scroll-margin-top:1rem; border-top:1px solid var(--line); padding-top:1.25rem}
.panel + .panel {margin-top:2.35rem} .section-heading {margin-top:1.65rem}
.back {display:inline-block; font-size:.86rem; margin-top:1rem}
#matematica-computacional {border-top:3px solid #14674e}
#matematica-computacional h2 {color:#14674e}
#matcomp-historico-obrigatorias,#matcomp-historico-optativas {grid-column:1 / -1}
article {min-width:0; padding:1.05rem; background:var(--surface); border:1px solid var(--line); border-radius:.65rem}
.scroll {overflow-x:auto} svg {width:100%; min-width:510px; display:block} svg text {font-size:13px; fill:var(--ink)}
.gridline {stroke:var(--line)} .legend {display:flex; flex-wrap:wrap; gap:.45rem 1rem; font-size:.86rem}
.legend i {display:inline-block; width:.7rem; height:.7rem; margin-right:.35rem; border-radius:.12rem}
.bars {list-style:none; padding:0; display:grid; gap:.62rem; margin:.8rem 0}
.bar-label {display:flex; justify-content:space-between; align-items:baseline; gap:.65rem}
.bar-label b {white-space:nowrap; font-variant-numeric:tabular-nums; font-size:.89rem}
.track {height:.35rem; margin-top:.2rem; background:#e2ebef; border-radius:1rem; overflow:hidden}
.track div {height:100%}
table {border-collapse:collapse; width:100%; font-size:.87rem; margin-top:.55rem}
th,td {padding:.38rem .55rem; border-bottom:1px solid var(--line); text-align:left; white-space:nowrap}
.heat td {text-align:center; font-variant-numeric:tabular-nums;
          background:color-mix(in srgb,#7cb7d5 var(--intensity,0%),var(--surface))}
.heat .missing {color:var(--muted)} details {margin-top:.75rem} summary {cursor:pointer; color:#175e8b}
[data-tooltip] {cursor:help}
.bars li:hover {background:#edf4f6}
svg rect:hover,svg rect:focus-visible {stroke:var(--ink); stroke-width:1.5px}
svg circle[data-tooltip]:not(.donut-slice):is(:hover,:focus-visible) {stroke:var(--ink); stroke-width:2px; fill-opacity:1}
.donut-layout {display:flex; align-items:center; justify-content:center; flex-wrap:wrap; gap:.7rem}
.donut-layout .scroll {flex:0 1 185px}
svg.donut {min-width:0} svg .donut-total {font-size:23px; font-weight:700}
.donut-slice:hover,.donut-slice:focus-visible {stroke-width:32px}
.donut-legend {flex:1 1 205px; list-style:none; margin:0; padding:0; display:grid; gap:.55rem; font-size:.88rem}
.donut-legend li {display:grid; grid-template-columns:.7rem minmax(0,1fr) auto; gap:.45rem; align-items:center}
.donut-legend i {width:.7rem; height:.7rem; border-radius:.12rem}
.heat td:hover {box-shadow:inset 0 0 0 2px #175e8b}
#chart-tooltip {position:fixed; z-index:1; max-width:min(22rem,calc(100vw - 1rem)); padding:.65rem .8rem;
                background:#172b35; color:white; border-radius:.4rem; box-shadow:0 3px 12px #172b3540;
                font-size:.85rem; line-height:1.45; white-space:pre-line; overflow-wrap:anywhere; pointer-events:none}
:focus-visible {outline:2px solid #175e8b; outline-offset:3px}
"""


TOOLTIPS = """
const tooltip = document.getElementById("chart-tooltip");
let activeMark = null;

function showTooltip(mark, x, y) {
  activeMark = mark;
  tooltip.textContent = mark.dataset.tooltip;
  tooltip.hidden = false;
  const margin = 8;
  const gap = 12;
  const left = Math.max(margin, Math.min(x + gap, innerWidth - tooltip.offsetWidth - margin));
  const below = y + gap;
  const above = y - gap - tooltip.offsetHeight;
  tooltip.style.left = left + "px";
  tooltip.style.top = Math.max(margin, below + tooltip.offsetHeight > innerHeight - margin ? above : below) + "px";
}

function hideTooltip(mark) {
  if (mark !== activeMark) return;
  tooltip.hidden = true;
  activeMark = null;
}

const findMark = target => target instanceof Element ? target.closest("[data-tooltip]") : null;

function showFocusedTooltip(mark) {
  const rect = mark.getBoundingClientRect();
  if (rect.bottom <= 0 || rect.top >= innerHeight || rect.right <= 0 || rect.left >= innerWidth) {
    hideTooltip(mark);
    return;
  }
  showTooltip(mark, rect.left + Math.min(20, rect.width / 2), rect.bottom);
}

document.addEventListener("pointerover", event => {
  const mark = findMark(event.target);
  if (mark && mark !== findMark(event.relatedTarget)) showTooltip(mark, event.clientX, event.clientY);
});
document.addEventListener("pointerout", event => {
  const mark = findMark(event.target);
  if (mark && mark !== findMark(event.relatedTarget)) hideTooltip(mark);
});
document.addEventListener("focusin", event => {
  const mark = findMark(event.target);
  if (mark) requestAnimationFrame(() => {
    if (mark === document.activeElement) showFocusedTooltip(mark);
  });
});
document.addEventListener("focusout", event => hideTooltip(findMark(event.target)));
document.addEventListener("keydown", event => {
  if (event.key === "Escape") hideTooltip(activeMark);
});
document.addEventListener("scroll", () => {
  if (activeMark && activeMark === document.activeElement) showFocusedTooltip(activeMark);
  else hideTooltip(activeMark);
}, true);
window.addEventListener("resize", () => hideTooltip(activeMark));
"""


def link_list(entries):
    return "<ul>" + "".join(f'<li><a href="#{escape(key)}">{escape(label)}</a></li>'
                             for key, label in entries) + "</ul>"


def chart_grid(plots, heading):
    return '<div class="chart-grid">' + "".join(figure(plot, heading) for plot in plots) + "</div>"


def page(bundle):
    courses = [p for p in bundle['paineis'] if p.get('courseKey')]
    general = [dict(id=f'gerais-{key}', title=f"Gráficos gerais · {group['title']}", sections=group['sections'])
               for key, group in bundle['groups'].items()]
    comparison = bundle['courseComparisons']
    def sections(panels):
        return ''.join(f'<section class="panel" id="{escape(panel["id"])}-painel"><h3>{escape(panel["title"])}</h3>'
                       + ''.join((f'<h4>{escape(section["title"])}</h4>' if section['title'] else '')
                                 + chart_grid(section['plots'], 'h5') for section in panel['sections'])
                       + '</section>' for panel in panels)
    areas = [(p['id'], p['title']) for p in general] + [('comparacao-cursos', comparison['title'])] + [(p['id'], p['title']) for p in courses]
    content = ''.join(f'<section class="area" id="{escape(p["id"])}"><h2>{escape(p["title"])}</h2>{sections([p])}</section>' for p in general)
    content += f'<section class="area" id="comparacao-cursos"><h2>{escape(comparison["title"])}</h2>{chart_grid(comparison["plots"], "h3")}</section>'
    content += ''.join(f'<section class="area" id="{escape(p["id"])}"><h2>{escape(p["title"])}</h2>'
                       f'<p>{escape(p["description"])}</p>{sections([p])}</section>' for p in courses)
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(bundle['titulo'])}</title><style>{STYLE}</style></head>
<body><header><h1>{escape(bundle['titulo'])}</h1><p>{escape(bundle.get('scopeNote', ''))}</p>
<nav id="indice" aria-label="Áreas do painel">{link_list(areas)}</nav></header><main>{content}</main>
<div id="chart-tooltip" aria-hidden="true" hidden></div><script>{TOOLTIPS}</script></body></html>'''




def render_dashboard(data_path):
    bundle = dashboard_data(data_path)
    # A exportação acompanha o acumulado da base.
    return page({**bundle, 'paineis': bundle['views']['accumulated']['paineis'],
                 'groups': bundle['views']['accumulated']['groups'],
                 'courseComparisons': bundle['views']['accumulated']['courseComparisons'],
                 'scopeNote': bundle['views']['accumulated']['scope']['note']})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--saida", type=Path, default=PROJECT_ROOT / "ufca-cct-painel.html")
    parser.add_argument("--sem-abrir", action="store_true", help="Gera o HTML sem abrir o navegador.")
    args = parser.parse_args()
    if args.saida.resolve() == args.dados.resolve():
        parser.error("O arquivo de saída deve ser diferente do arquivo de dados.")
    try:
        args.saida.write_text(render_dashboard(args.dados), encoding="utf-8")
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
    print(f"Painel gerado em {args.saida.resolve()}")
    if not args.sem_abrir:
        webbrowser.open(args.saida.resolve().as_uri())


if __name__ == "__main__":
    main()

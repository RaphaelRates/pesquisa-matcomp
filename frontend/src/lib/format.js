export const integerFormat = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const percentFormat = new Intl.NumberFormat("pt-BR", { style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1 });
export const decimalFormat = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
export const preciseFormat = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 3 });
export const indexFormat = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 4 });

export function format(value, percent = false) {
  return value == null ? "Sem registro" : (percent ? percentFormat : decimalFormat).format(value);
}

export function measure(value, valueFormat = {}) {
  if (value == null) return "Sem registro";
  if (valueFormat.style === "percent") return percentFormat.format(value);
  return valueFormat.style === "decimal" ? preciseFormat.format(value) : decimalFormat.format(value);
}

export function records(plot) {
  return plot.rows.map((row, index) => ({
    values: Object.fromEntries(plot.columns.map((column, i) => [column, row[i]])),
    detail: plot.tooltips?.[index],
  }));
}

export function comparisonValue(value, unit) {
  return value == null ? 'Sem registro' : unit === 'percent' ? format(value, true) : preciseFormat.format(value);
}

export function signed(value, multiplier = 1) {
  const number = Math.abs(value) < 1e-12 ? 0 : value * multiplier;
  return `${number > 0 ? '+' : ''}${preciseFormat.format(number)}`;
}

export function deltaClass({ delta }) {
  return 'delta-' + (delta == null ? 'missing' : delta > 1e-12 ? 'up' : delta < -1e-12 ? 'down' : 'same');
}

export function changeDescription(row) {
  if (row.delta == null) return 'Sem comparação';
  return row.delta > 1e-12 ? 'Aumento' : row.delta < -1e-12 ? 'Redução' : 'Sem alteração';
}

export function deltaValue(row) {
  if (row.delta == null) return '—';
  return row.unit === 'percent' ? signed(row.delta, 100) + ' p.p.' : signed(row.delta);
}

export function relativeChange(row) {
  if (row.relativeChange != null) return signed(row.relativeChange, 100) + '%';
  if (row.unit === 'decimal') return 'Não se aplica a índices';
  return row.before === 0 ? 'Base zero · indefinida' : 'Sem comparação';
}

<script>
  import { format, preciseFormat } from '../../lib/format.js';

  let { plot } = $props();
  const columns = $derived(plot.formato === 'ranking' ? plot.columns.slice(0, 2) : plot.columns);
  const spec = $derived(plot.spec);
  const valueColumns = $derived([spec?.value ?? (spec?.type === 'horizontalBar' ? spec.x : spec?.y)].flat());

  function cell(value, column) {
    if (value == null) return '—';
    if (typeof value !== 'number') return value;
    const percent = (spec?.valueFormat?.style === 'percent' && valueColumns.includes(column))
      || (spec?.xValueFormat?.style === 'percent' && column === spec.x);
    return percent ? format(value, true) : preciseFormat.format(value);
  }
</script>

<div class="scroll">
  <table aria-label={plot.title}>
    <thead><tr>{#each columns as column}<th scope="col">{column}</th>{/each}</tr></thead>
    <tbody>
      {#each plot.rows as row}
        <tr>{#each columns as column, i}<td>{cell(row[i], column)}</td>{/each}</tr>
      {/each}
    </tbody>
  </table>
</div>

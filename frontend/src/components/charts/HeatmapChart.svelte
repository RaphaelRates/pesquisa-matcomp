<script>
  import { format, records } from '../../lib/format.js';

  let { plot } = $props();
  const spec = $derived(plot.spec);
  const rows = $derived(records(plot));
  const keyFor = (x, y) => JSON.stringify([x, y]);
  const cells = $derived(new Map(rows.map(({ values, detail }) =>
    [keyFor(values[spec.x], values[spec.y]), { value: values[spec.value], detail }])));
  const columns = $derived(spec.xOrder ?? [...new Set(rows.map(({ values }) => values[spec.x]))]);
  const labels = $derived(spec.yOrder ?? [...new Set(rows.map(({ values }) => values[spec.y]))]);
  const domain = $derived(spec.colorDomain ?? [0, rows.reduce((max, { values }) => Math.max(max, values[spec.value] ?? 0), 1)]);

  function intensity(value) {
    const [low, high] = domain;
    return high > low ? Math.max(0, Math.min(1, (value - low) / (high - low))) * 78 : 0;
  }
</script>

<div class="scroll heat-scroll">
  <table class="heat" aria-label={plot.title}>
    <thead><tr><th scope="col">{spec.y}</th>{#each columns as column}<th scope="col">{column}</th>{/each}</tr></thead>
    <tbody>
      {#each labels as label, index}
        {@const semester = spec.yGroups?.[label]}
        {#if semester && semester !== spec.yGroups[labels[index - 1]]}
          <tr class="heat-curriculum-group"><th colspan={columns.length + 1}>{semester}</th></tr>
        {/if}
        <tr>
          <th scope="row">{label}</th>
          {#each columns as column}
            {@const item = cells.get(keyFor(column, label))}
            {@const printed = format(item?.value, spec.valueFormat?.style === 'percent')}
            {@const tooltip = [`${label} · ${column}`, `${spec.value}: ${printed}`, item?.detail].filter(Boolean).join('\n')}
            <td class:missing={item?.value == null} style:--intensity={item?.value == null ? undefined : intensity(item.value) + '%'}>
              <button type="button" class="heat-cell" data-tooltip={tooltip} aria-label={tooltip.replaceAll('\n', '. ')}>
                {item?.value == null ? '—' : printed}
              </button>
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
<div class="heat-key"><span>Menor</span><i></i><span>Maior</span><span class="muted">— Sem registro</span></div>

<style>
  .heat-cell {
    width: 100%;
    border: 0;
    padding: 0;
    background: transparent;
    color: inherit;
    font: inherit;
    cursor: help;
  }
</style>

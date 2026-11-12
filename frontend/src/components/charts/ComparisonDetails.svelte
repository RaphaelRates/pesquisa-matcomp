<script>
  import ComparisonTable from './ComparisonTable.svelte';

  let { comparison, children } = $props();
  let opened = $state(false);
  const rows = $derived((comparison?.rows ?? []).filter(row => row.delta != null));
  const up = $derived(rows.filter(row => row.delta > 1e-12).length);
  const down = $derived(rows.filter(row => row.delta < -1e-12).length);
</script>

{#if comparison}
  <details class="period-comparison" ontoggle={event => { if (event.currentTarget.open) opened = true; }}>
    <summary>Comparar com {comparison.baselinePeriod ?? 'semestre anterior'} ·
      {rows.length ? `${up} aumentos, ${down} reduções, ${rows.length - up - down} estáveis` : 'sem medidas pareadas'}
    </summary>
    {#if opened}
      <p class="comparison-note">{comparison.note}</p>
      <ComparisonTable {comparison} />
      {@render children?.()}
    {/if}
  </details>
{/if}

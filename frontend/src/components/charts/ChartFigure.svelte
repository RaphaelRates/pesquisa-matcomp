<script>
  import CanvasChart from './CanvasChart.svelte';
  import ChartDataTable from './ChartDataTable.svelte';
  import HeatmapChart from './HeatmapChart.svelte';

  let { plot } = $props();
  const isHeatmap = $derived(plot.spec?.type === 'heatmap');
  const hasValues = $derived(plot.rows.length > 0
    && (!isHeatmap || plot.rows.some(row => row.at(-1) != null)));
  let showTable = $state(false);
</script>

{#if !hasValues}
  <p class="empty-state">Sem turmas neste recorte.</p>
{:else if isHeatmap}
  <HeatmapChart {plot} />
{:else}
  <CanvasChart {plot} />
{/if}

{#if plot.method || plot.interpretation}
  <details class="method-note">
    <summary>Método e interpretação</summary>
    {#if plot.method}<p>{plot.method}</p>{/if}
    {#if plot.interpretation}<p>{plot.interpretation}</p>{/if}
  </details>
{/if}

{#if hasValues}
  <details ontoggle={event => { if (event.currentTarget.open) showTable = true; }}>
    <summary>Consultar dados</summary>
    {#if showTable}<ChartDataTable {plot} />{/if}
  </details>
{/if}

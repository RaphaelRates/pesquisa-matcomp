<script>
  import { onMount } from 'svelte';
  import { drawChart, loadChartLibrary } from './chart.js';

  let { plot } = $props();
  let canvas = $state();
  let status = $state();
  let failed = $state(false);
  const horizontal = $derived(plot.formato === 'ranking' || plot.spec?.type === 'horizontalBar');
  const height = $derived(horizontal ? Math.max(290, plot.rows.length * 50) : 330);

  onMount(() => {
    let stopped = false;
    let cleanup;
    loadChartLibrary().then(Chart => {
      if (!stopped) cleanup = drawChart(Chart, canvas, status, plot);
    }).catch(() => {
      if (!stopped) failed = true;
    });
    return () => {
      stopped = true;
      cleanup?.();
    };
  });
</script>

{#if failed}
  <p class="empty-state">Visualização indisponível. Consulte a tabela de dados.</p>
{:else}
  <div class="chart-frame" class:horizontal-chart={horizontal} style:--chart-height={height + 'px'}>
    <canvas bind:this={canvas} data-plot-id={plot.id} tabindex="0"
      aria-label={plot.title + '. Use as setas para consultar os pontos.'}
      aria-describedby={plot.id + '-leitura'}>Consulte a tabela de dados abaixo.</canvas>
  </div>
  <p class="sr-only" id={plot.id + '-leitura'} bind:this={status} aria-live="polite"></p>
{/if}

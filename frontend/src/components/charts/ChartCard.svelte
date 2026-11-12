<script>
  import ChartFigure from './ChartFigure.svelte';
  import ComparisonDetails from './ComparisonDetails.svelte';
  import { nearViewport } from '../../lib/visibility.js';

  let { plot, anchor, hash } = $props();
  const kinds = {
    bar: 'Barras', horizontalBar: 'Barras horizontais', ranking: 'Ranking',
    stackedBar: 'Barras empilhadas', stackedPercent: 'Composição · 100%',
    line: 'Linhas', area: 'Área empilhada', mixed: 'Barras + linha',
    donut: 'Rosca', pie: 'Pizza', radar: 'Radar', scatter: 'Dispersão',
    bubble: 'Bolhas', heatmap: 'Mapa de calor', distributionBand: 'Faixa interquartil',
    statisticalScatter: 'Associação descritiva',
  };
  const kind = $derived(plot.formato ?? plot.spec.type);
  const id = $derived(anchor + plot.id);
  let visible = $state(false);
  let showBaseline = $state(false);

  function reveal() {
    visible = true;
  }

  $effect(() => {
    if (hash === id) reveal();
  });
</script>

<article class="chart-card chart-slot" class:wide-card={kind === 'heatmap'} {id}
  use:nearViewport={reveal} onfocusin={reveal} tabindex="-1">
  <div class="card-kicker">
    <span class="chart-type">{kinds[kind]}</span>
    <a href={'#' + id} aria-label="Link para este gráfico">↗</a>
  </div>
  <h4>{plot.title}</h4>
  {#if plot.scopeNote}<p class="scope-note">{plot.scopeNote}</p>{/if}
  <p class="description">{plot.description}</p>

  {#if visible}
    <ChartFigure {plot} />
    <ComparisonDetails comparison={plot.comparison}>
      {#if plot.comparison?.baselinePlot}
        <details class="baseline-preview" ontoggle={event => { showBaseline = event.currentTarget.open; }}>
          <summary>Ver gráfico de referência · {plot.comparison.baselinePeriod}</summary>
          {#if showBaseline}
            <div class="baseline-content">
              <h5>{plot.comparison.baselinePlot.title}</h5>
              <ChartFigure plot={{ ...plot.comparison.baselinePlot, id: plot.id + '-reference' }} />
            </div>
          {/if}
        </details>
      {/if}
    </ComparisonDetails>
  {/if}
</article>

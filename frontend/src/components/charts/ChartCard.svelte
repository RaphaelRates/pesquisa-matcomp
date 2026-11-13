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
  let selectedCurriculum = $state('');
  const curriculum = $derived(plot.curriculumOptions?.find(item => item.id === selectedCurriculum) ?? plot.curriculumOptions?.[0]);
  const activePlot = $derived(plot.curriculumAlternatives?.[curriculum?.id] ?? plot);

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
  {#if curriculum}
    <div class="curriculum-controls">
      {#if plot.curriculumOptions.length > 1}
        <label>Matriz curricular
          <select value={curriculum.id} onchange={event => selectedCurriculum = event.currentTarget.value}>
            {#each plot.curriculumOptions as option (option.id)}
              <option value={option.id}>{option.label}</option>
            {/each}
          </select>
        </label>
      {:else}
        <span>{curriculum.label}</span>
      {/if}
      <a href={curriculum.source} target="_blank" rel="noreferrer">Matriz da UFCA ↗</a>
    </div>
  {/if}
  <p class="description">{activePlot.description}</p>

  {#if visible}
    <ChartFigure plot={activePlot} />
    {#if activePlot.scopeId !== 'accumulated'}
      <ComparisonDetails comparison={activePlot.comparison}>
        {#if activePlot.comparison?.baselinePlot}
          <details class="baseline-preview" ontoggle={event => { showBaseline = event.currentTarget.open; }}>
            <summary>Ver gráfico de referência · {activePlot.comparison.baselinePeriod}</summary>
            {#if showBaseline}
              <div class="baseline-content">
                <h5>{activePlot.comparison.baselinePlot.title}</h5>
                <ChartFigure plot={{ ...activePlot.comparison.baselinePlot, id: plot.id + '-reference' }} />
              </div>
            {/if}
          </details>
        {/if}
      </ComparisonDetails>
    {/if}
  {/if}
</article>

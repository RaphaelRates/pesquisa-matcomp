<script>
  import { onDestroy, untrack } from 'svelte';
  import { requestDashboard } from '../../lib/api.js';
  import LazyChartSections from '../../components/charts/LazyChartSections.svelte';
  import LoadError from '../../components/feedback/LoadError.svelte';
  import { format } from '../../lib/format.js';
  import ComparisonOverview from './ComparisonOverview.svelte';
  import SummaryCards from './SummaryCards.svelte';
  import { nearViewport } from '../../lib/visibility.js';

  let { disciplines, scope, group, revision, hash, refresh, syncLocation } = $props();
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');
  const searchIndex = $derived(disciplines.map(item => ({ ...item, text: normalize(`${item.code} ${item.name}`) })));
  let search = $state('');
  const matches = $derived(searchIndex.filter(item => item.text.includes(normalize(search.trim()))));
  let preferred = $state(new URL(location.href).searchParams.get('disciplina') ?? '');
  const linked = $derived(hash.match(/^cadeira--cadeira-([A-Z]+\d+)-/)?.[1]);
  const code = $derived([linked, preferred].find(value => matches.some(item => item.code === value)) ?? matches[0]?.code ?? '');
  let visible = $state(false);
  let loading = $state(false);
  let payload = $state.raw();
  let error = $state.raw();
  let attempt = $state(0);
  let controller;

  function reveal() {
    visible = true;
  }

  function remember(value) {
    preferred = value;
    const url = new URL(location.href);
    if (value) url.searchParams.set('disciplina', value);
    else url.searchParams.delete('disciplina');
    if (url.hash.startsWith('#cadeira--')) {
      url.hash = '#cadeiras-individual';
    }
    history.replaceState(null, '', url);
    syncLocation();
  }

  async function load(selected) {
    controller?.abort();
    payload = undefined;
    error = undefined;
    loading = Boolean(selected);
    if (!selected) return;
    const { signal } = (controller = new AbortController());
    try {
      const response = await requestDashboard(group, scope.id, '/disciplinas/' + encodeURIComponent(selected), signal, revision);
      if (signal.aborted) return;
      payload = response.data;
    } catch (failure) {
      if (!signal.aborted) error = failure;
    } finally {
      if (!signal.aborted) loading = false;
    }
  }

  $effect(() => {
    if (hash === 'cadeiras-individual' || linked) reveal();
  });
  $effect(() => {
    if (visible) {
      const selected = code;
      // A tentativa permite repetir a mesma consulta após uma falha.
      attempt;
      untrack(() => load(selected));
    }
  });
  onDestroy(() => controller?.abort());
</script>

<section class="panel discipline-explorer" id="cadeiras-individual" aria-labelledby="cadeiras-individual-titulo"
  use:nearViewport={reveal} onfocusin={reveal}>
  <h2 id="cadeiras-individual-titulo">Análise individual das cadeiras</h2>
  <div class="discipline-controls">
    <label>Buscar por nome ou código<input type="search" bind:value={search}></label>
    <label>Cadeira
      <select value={code} disabled={!matches.length} onchange={event => remember(event.currentTarget.value)}>
        {#each matches as item (item.code)}
          <option value={item.code}>{item.code} · {item.name}</option>
        {/each}
      </select>
    </label>
  </div>
  <div id="analise-individual" aria-busy={loading}>
    {#if payload}
      {@const m = payload.summary.selected}
      <h3 class="section-heading">{payload.code} · {payload.name}</h3>
      <SummaryCards summary={payload.summary} {scope} />
      <ComparisonOverview comparison={payload.summary.comparison} heading="Comparação desta cadeira" />
      <p class="discipline-reading">
        {#if m.n}
          {format(m.free)} vagas não preenchidas e {format(m.extra)} matrículas acima da capacidade.
          {format(m.low)} turmas tiveram ocupação abaixo de 25% e {format(m.full)} chegaram a 100% ou mais.
        {:else}Sem oferta no recorte selecionado.{/if}
      </p>
      <LazyChartSections sections={payload.sections} anchor="cadeira--" {hash} />
    {:else if error}
      <LoadError {error} retry={() => attempt++} {refresh} />
    {:else if loading}
      <p class="loading-state" role="status">Calculando indicadores da cadeira…</p>
    {:else if !matches.length}
      <p class="empty-state">Nenhuma disciplina encontrada.</p>
    {/if}
  </div>
</section>

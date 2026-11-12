<script>
  import { onDestroy, untrack } from 'svelte';
  import { requestDashboard } from '../../lib/api.js';
  import LazyChartSections from '../../components/charts/LazyChartSections.svelte';
  import LoadError from '../../components/feedback/LoadError.svelte';
  import StatisticalOverview from './StatisticalOverview.svelte';
  import { nearViewport } from '../../lib/visibility.js';

  let { section, group, scope, revision, hash, refresh } = $props();
  let payload = $state.raw();
  let error = $state.raw();
  let loading = $state(false);
  let controller;
  const anchor = $derived(section.id + '--');

  async function load() {
    if (loading || payload) return;
    error = undefined;
    loading = true;
    const { signal } = (controller = new AbortController());
    try {
      const response = await requestDashboard(group, scope, '/secoes/' + section.id, signal, revision);
      if (signal.aborted) return;
      payload = response.data;
    } catch (failure) {
      if (!signal.aborted) error = failure;
    } finally {
      if (!signal.aborted) loading = false;
    }
  }

  $effect(() => {
    if (hash === section.id || hash.startsWith(anchor)) untrack(load);
  });
  onDestroy(() => controller?.abort());
</script>

<section class="panel dashboard-section" id={section.id} aria-labelledby={section.id + '-titulo'} use:nearViewport={load}>
  <div class="panel-heading"><h2 id={section.id + '-titulo'}>{section.title}</h2></div>
  <div class="section-body" aria-busy={loading}>
    {#if payload}
      {#if payload.description}<p class="area-description">{payload.description}</p>{/if}
      {#if payload.statisticalSummary}<StatisticalOverview stats={payload.statisticalSummary} />{/if}
      <div class="section-charts"><LazyChartSections sections={payload.sections} {anchor} {hash} /></div>
    {:else if error}
      <LoadError {error} retry={load} {refresh} />
    {:else if loading}
      <p class="loading-state" role="status">Calculando gráficos…</p>
    {:else}
      <button class="refresh-button" type="button" onclick={load}>Carregar gráficos</button>
    {/if}
  </div>
</section>

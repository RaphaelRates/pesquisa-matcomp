<script>
  let { sections, anchor, hash } = $props();
  const chartModule = import('./ChartSections.svelte').then(module => module.default);
</script>

{#await chartModule}
  <p class="loading-state" role="status">Preparando gráficos…</p>
{:then ChartSections}
  <ChartSections {sections} {anchor} {hash} />
{:catch}
  <div class="empty-state" role="alert">
    <p>Não foi possível carregar os componentes dos gráficos.</p>
    <button class="refresh-button" type="button" onclick={() => location.reload()}>Recarregar painel</button>
  </div>
{/await}

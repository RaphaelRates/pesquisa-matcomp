<script>
  import { onMount, tick, untrack } from 'svelte';
  import { requestDashboard } from '../lib/api.js';
  import { courseUrl, readGroup, readScope } from '../lib/navigation.js';
  import DashboardSection from '../features/dashboard/DashboardSection.svelte';
  import DisciplineExplorer from '../features/dashboard/DisciplineExplorer.svelte';
  import Header from '../components/layout/Header.svelte';
  import LoadError from '../components/feedback/LoadError.svelte';
  import ComparisonOverview from '../features/dashboard/ComparisonOverview.svelte';
  import DataQuality from '../features/dashboard/DataQuality.svelte';
  import SummaryCards from '../features/dashboard/SummaryCards.svelte';

  let { group: initialGroup, title: initialTitle, siteTitle, courses, currentPeriod } = $props();
  let group = $state(untrack(() => initialGroup));
  const title = $derived(courses.find(course => course.id === group)?.title ?? initialTitle);
  let scope = $state(readScope());
  let hash = $state(location.hash.slice(1));
  let page = $state.raw();
  let error = $state.raw();
  let loading = $state(true);
  let dataStatus = $state('');
  let previousHash;
  let controller;

  async function load(focus) {
    controller?.abort();
    const { signal } = (controller = new AbortController());
    loading = true;
    error = undefined;
    page = undefined;
    try {
      const response = await requestDashboard(group, scope, '', signal);
      if (signal.aborted) return;
      const fingerprint = response.data.source.sha256;
      dataStatus = previousHash === undefined ? 'Base carregada.'
        : previousHash === fingerprint ? 'Base sem alterações.' : 'A base mudou desde a consulta anterior.';
      previousHash = fingerprint;
      page = response;
      await tick();
      if (signal.aborted) return;
      if (focus) document.getElementById(focus)?.focus();
      if (hash) {
        const target = document.getElementById(hash) ?? document.getElementById(hash.split('--')[0]);
        target?.scrollIntoView();
      }
    } catch (failure) {
      if (!signal.aborted) error = failure;
    } finally {
      if (!signal.aborted) loading = false;
    }
  }

  function changeScope(value) {
    if (value === scope) return;
    scope = value;
    const url = new URL(location.href);
    if (value === 'accumulated') url.searchParams.delete('recorte');
    else url.searchParams.set('recorte', value);
    url.hash = '';
    hash = '';
    history.pushState(null, '', url);
    load('recorte-' + value);
  }

  async function changeCourse(value) {
    if (value === group) return;
    group = value;
    void load();
    await tick();
    if (group === value) {
      if (!hash) window.scrollTo({ top: 0, behavior: 'instant' });
      document.getElementById('curso-titulo')?.focus({ preventScroll: true });
    }
  }

  function navigate(value) {
    if (value === group) return;
    history.pushState(null, '', courseUrl(value, scope));
    hash = '';
    void changeCourse(value);
  }

  function syncLocation() {
    hash = location.hash.slice(1);
    const course = readGroup();
    const nextScope = readScope();
    if (course !== group && courses.some(item => item.id === course)) {
      scope = nextScope;
      void changeCourse(course);
    } else if (nextScope !== scope) {
      scope = nextScope;
      load();
    }
  }

  onMount(() => {
    load();
    return () => controller?.abort();
  });
</script>

<svelte:window onpopstate={syncLocation} onhashchange={syncLocation} />
<svelte:head><title>{title} | {siteTitle}</title></svelte:head>

<a class="skip-link" href="#painel">Ir para os gráficos</a>
<Header {courses} {group} {scope} {navigate} />
<main id="painel" tabindex="-1" aria-busy={loading}>
  <h1 class="page-title" id="curso-titulo" tabindex="-1">{title}</h1>
  {#if page}
    {@const data = page.data}
    <section class="period-controls" aria-labelledby="recorte-titulo">
      <h2 id="recorte-titulo">Recorte dos gráficos</h2>
      <div class="period-buttons" role="group" aria-label="Recorte dos gráficos">
        {#each data.scopes as option (option.id)}
          <button type="button" id={'recorte-' + option.id} aria-pressed={option.id === scope}
            onclick={() => changeScope(option.id)}>{option.label}</button>
        {/each}
      </div>
      <p class="selected-scope">{data.scope.note}</p>
    </section>
    <SummaryCards summary={data.summary} scope={data.scope} />
    <ComparisonOverview comparison={data.summary.comparison} />
    <nav class="section-nav" aria-label="Seções desta página">
      <ul>
        {#each data.sections as section (section.id)}
          <li><a href={'#' + section.id}>{section.title}</a></li>
        {/each}
        <li><a href="#cadeiras-individual">Análise por cadeira</a></li>
        <li><a href="#qualidade-dados">Qualidade da base</a></li>
      </ul>
    </nav>
    {#each data.sections as section (section.id)}
      <DashboardSection {section} {group} scope={data.scope.id} revision={page.meta.revision} {hash} refresh={() => load()} />
    {/each}
    <DisciplineExplorer disciplines={data.disciplines} scope={data.scope} {group}
      revision={page.meta.revision} {hash} refresh={() => load()} {syncLocation} />
    <DataQuality report={data.quality} generatedAt={data.generatedAt} source={data.source}
      {dataStatus} {currentPeriod} refresh={() => load('refresh-data')} />
  {:else if error}
    <LoadError {error} retry={() => load()} />
  {:else}
    <p class="loading-state" role="status">Carregando indicadores…</p>
  {/if}
</main>
<footer class="site-footer">
  <strong>UFCA · CCT</strong>
  <p>Indicadores de turmas presenciais. As turmas abertas de {currentPeriod} são identificadas nos gráficos.</p>
  <a href="#inicio">↑ Voltar ao início</a>
</footer>

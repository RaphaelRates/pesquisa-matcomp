<script>
  import ComparisonTable from '../../components/charts/ComparisonTable.svelte';
  import { changeDescription, comparisonValue, deltaClass, deltaValue, signed } from '../../lib/format.js';

  let { comparison: result, heading = 'Comparação entre semestres', id = 'comparacao-semestres' } = $props();
</script>

{#if result?.currentPeriod}
  <section class="comparison-overview" {id} aria-label={heading}>
    <div class="comparison-heading">
      {#if id}<h2>{heading}</h2>{:else}<h3>{heading}</h3>{/if}
      <span>{result.baselinePeriod ?? 'Sem referência'} → {result.currentPeriod}</span>
    </div>
    <div class="comparison-cards">
      {#each result.rows.slice(0, 4) as row}
        <div>
          <span>{row.metric}</span>
          <small>{comparisonValue(row.before, row.unit)} → {comparisonValue(row.after, row.unit)}</small>
          <strong class={deltaClass(row)}>{deltaValue(row)}</strong>
          <small>{changeDescription(row)}{row.relativeChange == null ? '' : ` · ${signed(row.relativeChange, 100)}%`}</small>
        </div>
      {/each}
    </div>
    <details><summary>Ver todas as métricas comparadas</summary><ComparisonTable comparison={result} /></details>
  </section>
{/if}

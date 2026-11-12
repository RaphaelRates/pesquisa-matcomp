<script>
  import ComparisonTable from '../../components/charts/ComparisonTable.svelte';
  import { changeDescription, comparisonValue, deltaClass, deltaValue, signed } from '../../lib/format.js';

  let { comparison, heading = 'Comparação entre semestres' } = $props();
</script>

{#if comparison}
  <section class="comparison-overview" aria-label={heading}>
    <div class="comparison-heading">
      <h3>{heading}</h3><span>{comparison.baselinePeriod ?? 'Sem referência'} → {comparison.currentPeriod}</span>
    </div>
    <p>Compara a oferta aberta com o último semestre consolidado.</p>
    <div class="comparison-cards">
      {#each comparison.rows.slice(0, 4) as row}
        <div>
          <span>{row.metric}</span>
          <small>{comparisonValue(row.before, row.unit)} → {comparisonValue(row.after, row.unit)}</small>
          <strong class={deltaClass(row)}>{deltaValue(row)}</strong>
          <small>{changeDescription(row)}{row.relativeChange == null ? '' : ` · ${signed(row.relativeChange, 100)}%`}</small>
        </div>
      {/each}
    </div>
    <details><summary>Ver todas as métricas comparadas</summary><ComparisonTable {comparison} /></details>
    <p class="comparison-note">A diferença entre semestres também pode refletir o calendário da oferta de disciplinas.</p>
  </section>
{/if}

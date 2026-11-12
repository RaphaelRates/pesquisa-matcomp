<script>
  import { changeDescription, comparisonValue, deltaClass, deltaValue, relativeChange } from '../../lib/format.js';

  let { comparison } = $props();
</script>

{#if comparison.rows?.length}
  <div class="scroll comparison-scroll">
    <table>
      <caption>{comparison.currentPeriod} em relação a {comparison.baselinePeriod ?? 'semestre de referência indisponível'}</caption>
      <thead>
        <tr>
          <th scope="col">Categoria / métrica</th><th scope="col">{comparison.baselinePeriod ?? 'Referência'}</th>
          <th scope="col">{comparison.currentPeriod} · aberta</th><th scope="col">Diferença</th>
          <th scope="col">Variação relativa</th>
        </tr>
      </thead>
      <tbody>
        {#each comparison.rows as row}
          <tr>
            <th scope="row">{[row.category, row.metric].filter(Boolean).join(' · ')}</th>
            <td>{comparisonValue(row.before, row.unit)}</td><td>{comparisonValue(row.after, row.unit)}</td>
            <td class={deltaClass(row)}>{changeDescription(row)} {deltaValue(row)}</td><td>{relativeChange(row)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

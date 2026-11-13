<script>
  import { format, integerFormat } from '../../lib/format.js';

  let { summary, scope } = $props();
  const metrics = $derived(summary.selected ?? summary.historico);
  const labels = { current: 'Turmas abertas', accumulated: 'Turmas no acumulado', historical: 'Turmas consolidadas' };
  const entries = $derived([
    [labels[scope.id] ?? 'Turmas nos semestres selecionados', integerFormat.format(metrics.n)], ['Vagas ofertadas', integerFormat.format(metrics.c)],
    ['Matrículas registradas', integerFormat.format(metrics.m)], ['Ocupação geral', format(metrics.rate, true)],
  ]);
  const periodCount = $derived(scope.periods.length);
</script>

<div class="metrics">
  {#each entries as [label, value]}<div class="metric"><span>{label}</span><strong>{value}</strong></div>{/each}
</div>
<p class="data-note">
  {#if periodCount && scope.id !== 'current'}
    Totais de {periodCount} {periodCount === 1 ? 'semestre' : 'semestres'}. As vagas são somadas ao longo do período.
  {/if}
  Turmas contam ofertas por código após os filtros da base. Matrículas são registros de turma.
</p>

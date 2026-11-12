<script>
  import ComparisonDetails from '../../components/charts/ComparisonDetails.svelte';
  import { decimalFormat, format, indexFormat, integerFormat } from '../../lib/format.js';

  let { stats } = $props();
  const o = $derived(stats.occupancy);
  const c = $derived(stats.concentration);
  const a = $derived(stats.association);
  const index = value => value == null ? "Indefinido no recorte" : indexFormat.format(value);
  const points = value => value == null ? "Sem registro" : decimalFormat.format(value * 100) + " p.p.";
  const prominent = $derived([
    ["Mediana de ocupação", format(o.median, true), "Turma central da distribuição"],
    ["Desvio-padrão", points(o.standardDeviation), "Dispersão entre turmas"],
    ["Gini das matrículas", index(c.gini), "Concentração por disciplina · 0 a 1"],
    ["Pearson", index(a.pearson), "Capacidade × ocupação · −1 a 1"],
  ]);
  const entries = $derived([
    ["Turmas analisadas", integerFormat.format(o.n)],
    ["Média aritmética da ocupação", format(o.mean, true)],
    ["Primeiro quartil (Q1)", format(o.q1, true)], ["Terceiro quartil (Q3)", format(o.q3, true)],
    ["Intervalo interquartil (IQR)", points(o.iqr)], ["Desvio absoluto mediano (MAD)", points(o.mad)],
    ["Coeficiente de variação", format(o.coefficientVariation, true)],
    ["Assimetria", index(o.skewness)], ["Excesso de curtose", index(o.excessKurtosis)],
    ["Abaixo da cerca de Tukey", format(o.outliersLow)], ["Acima da cerca de Tukey", format(o.outliersHigh)],
    ["Disciplinas com oferta", integerFormat.format(c.disciplines)],
    ["HHI em frações", index(c.hhi)], ["Disciplinas efetivas (1/HHI)", index(c.effectiveDisciplines)],
    ["Entropia normalizada", index(c.normalizedEntropy)], ["Parcela das 20% maiores disciplinas", format(c.top20Share, true)],
    ["Spearman", index(a.spearman)], ["R² do ajuste linear", index(a.rSquared)],
  ]);
</script>

<section class="statistical-overview" aria-label="Resumo estatístico do recorte selecionado">
  <div class="statistical-heading"><h3>Estatísticas do recorte selecionado</h3><span>{o.n} turmas</span></div>
  <div class="statistical-cards">
    {#each prominent as [name, value, note]}
      <div><span>{name}</span><strong>{value}</strong><small>{note}</small></div>
    {/each}
  </div>
  <details>
    <summary>Explorar os indicadores estatísticos</summary>
    <dl class="statistical-values">
      {#each entries as [name, value]}<div><dt>{name}</dt><dd>{value}</dd></div>{/each}
    </dl>
    <p class="statistical-caution">Cada turma tem o mesmo peso nas estatísticas de ocupação. A ocupação geral
      pondera pela capacidade. Os coeficientes descrevem as associações do recorte.</p>
  </details>
  <ComparisonDetails comparison={stats.comparison} />
</section>

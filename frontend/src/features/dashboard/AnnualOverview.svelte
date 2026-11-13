<script>
  import { format, integerFormat } from '../../lib/format.js';

  let { years, semesters } = $props();
  const openPeriods = $derived(new Set(semesters.filter(item => item.open).map(item => item.period)));
</script>

<section class="comparison-overview annual-overview" id="resumo-anual" aria-labelledby="resumo-anual-titulo">
  <h2 id="resumo-anual-titulo">Resumo anual</h2>
  {#if years.length}
    <!-- svelte-ignore a11y_no_noninteractive_tabindex (permite rolar a tabela pelo teclado) -->
    <div class="scroll" tabindex="0" role="region" aria-labelledby="resumo-anual-titulo">
      <table>
        <thead>
          <tr>
            <th scope="col">Ano</th><th scope="col">Semestres com oferta</th><th scope="col">Turmas</th>
            <th scope="col">Vagas</th><th scope="col">Matrículas</th><th scope="col">Ocupação geral</th>
          </tr>
        </thead>
        <tbody>
          {#each years as { year, periods, summary } (year)}
            <tr>
              <th scope="row">{year}</th>
              <td>{periods.map(period => openPeriods.has(period) ? period + '*' : period).join(', ')}</td>
              <td>{integerFormat.format(summary.n)}</td>
              <td>{integerFormat.format(summary.c)}</td>
              <td>{integerFormat.format(summary.m)}</td>
              <td>{format(summary.rate, true)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p>Ocupação anual = matrículas ÷ vagas nos semestres com oferta.
      {#if years.some(item => item.periods.some(period => openPeriods.has(period)))}
        * Inclui turmas abertas.
      {/if}
    </p>
  {:else}
    <p>Sem oferta no recorte selecionado.</p>
  {/if}
</section>

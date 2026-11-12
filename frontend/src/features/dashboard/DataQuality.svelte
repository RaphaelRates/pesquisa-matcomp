<script>
  import { format, integerFormat } from '../../lib/format.js';

  let { report, generatedAt, source, dataStatus, currentPeriod, refresh } = $props();
  const consistency = $derived(report.consistency);
  const irregular = $derived(consistency?.excludedRecords ?? 0);
  const used = $derived(report.inScopeRows ?? report.eligibleRows);
  const selection = $derived([
    ['Registros lidos', report.inputRows], ['Excluídos por possíveis irregularidades', irregular],
    ['Outras exclusões do recorte', report.validRows - used - irregular], ['Usados nos gráficos', used],
  ]);
  const counts = $derived([
    ['Formatos inválidos descartados', report.discardedRows], ['Duplicatas exatas removidas', report.duplicateRows],
    ['Registros normalizados', report.normalizedRows], ['Conflitos cadastrais', report.conflictGroups],
  ].filter(([, value]) => value > 0));
  const reasons = $derived([...(report.issues ?? []), ...(report.exclusionReasons ?? []), ...(report.outOfScopeReasons ?? [])]);
  const timestamp = $derived(generatedAt && new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'medium' }).format(new Date(generatedAt)));
  const names = {
    possible_joint_class: 'Possível turma conjunta · mesmo nome',
    simultaneous_different_subjects: 'Coincidência entre disciplinas diferentes',
    teacher_schedule_overlap: 'Sobreposição de horário de docente',
  };
</script>

{#snippet counters(entries, highlighted = false)}
  <div class="quality-counts" class:quality-selection={highlighted}>
    {#each entries as [name, value]}
      <div><strong>{integerFormat.format(value)}</strong><span>{name}</span></div>
    {/each}
  </div>
{/snippet}

{#snippet issues(title, entries)}
  {#if entries?.length}
    <p>{title}</p>
    <ul class="quality-issues">
      {#each entries as issue}<li>{issue.reason} <strong>{integerFormat.format(issue.count)}</strong></li>{/each}
    </ul>
  {/if}
{/snippet}

<div class="quality-area">
  <section class="quality-panel" id="qualidade-dados" aria-labelledby="qualidade-titulo">
    <h2 id="qualidade-titulo">Qualidade e preparação da base</h2>
    <p class="quality-lead">{integerFormat.format(report.inputRows)} registros lidos ·
      {integerFormat.format(used)} registros no recorte de análise.
      {#if timestamp}<span id="updated-status" role="status">Calculado em {timestamp}</span>{/if}
    </p>
    {@render counters(selection, true)}
    {#if source}
      <div class="source-verification">
        <strong>{dataStatus}</strong>
        <p>Fonte: {source.name} · {source.files?.length ?? 1} arquivo(s) de turmas · identificação da base: <code>{source.sha256.slice(0, 12)}</code>.</p>
        <p>{currentPeriod}: {format(source.currentRows)} registros na base; {format(source.currentEligibleRows)} turmas presenciais abertas com capacidade positiva no painel.</p>
      </div>
    {/if}
    {#if consistency?.findings?.length}
      <div class="quality-warning consistency-warning">
        <p><strong>{format(irregular)} registros excluídos dos cálculos.</strong>
          {format(consistency.candidateGroups)} grupos de possível oferta conjunta e {format(consistency.overlappingPairs)} pares com sobreposição de docente.
        </p>
        <details>
          <summary>Ver os casos sinalizados</summary>
          {#each consistency.findings as finding}
            <section class="consistency-case">
              <h3>{finding.period} · {names[finding.kind] ?? finding.kind}</h3>
              <p>{finding.evidence}</p>
              <ul>
                {#each finding.records as row}
                  <li><strong>{row.codigo} · {row.disciplina}</strong> · {row.turma} ·
                    {format(row.matriculas)}/{format(row.capacidade)} matrículas/vagas<br>
                    {row.docentes ?? ''} · {row.local ?? ''}<br>{row.horario ?? ''}
                  </li>
                {/each}
              </ul>
              <p>{finding.action}</p>
            </section>
          {/each}
        </details>
      </div>
    {/if}
    <details>
      <summary>Ver o tratamento aplicado aos dados</summary>
      {@render counters(counts)}
      <p>Após os filtros da base, {integerFormat.format(used)} registros entram nos cálculos.</p>
      {#if report.conflictGroups}
        <p class="quality-warning">Os resultados incluem versões conflitantes de turmas sinalizadas para revisão.</p>
      {/if}
      {@render issues('Motivos de exclusão', reasons)}
      {@render issues('Avisos de preenchimento', report.warnings)}
    </details>
  </section>
  <button id="refresh-data" class="refresh-button" type="button" onclick={refresh}>Atualizar dados ↻</button>
</div>

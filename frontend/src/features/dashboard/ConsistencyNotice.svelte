<script>
  import { integerFormat } from '../../lib/format.js';

  let { consistency, course = false, expanded = false } = $props();
  let opened = $state(false);
  const names = {
    possible_joint_class: 'Possível oferta conjunta',
    simultaneous_different_subjects: 'Coincidência entre disciplinas diferentes',
    teacher_schedule_overlap: 'Choque de horário de docente',
    room_schedule_overlap: 'Choque de horário na mesma sala',
  };
  const counts = $derived([
    [consistency?.candidateGroups, 'grupos de possível oferta conjunta'],
    [consistency?.overlappingPairs, 'pares com choque de docente'],
    [consistency?.roomOverlappingPairs, 'pares adicionais com choque de sala'],
  ].filter(([count]) => count > 0));

  function clock(minutes) {
    const hour = String(Math.floor(minutes / 60)).padStart(2, '0');
    return hour + ':' + String(minutes % 60).padStart(2, '0');
  }
</script>

{#if consistency?.findings?.length}
  <section id="inconsistencias" class="notice" aria-labelledby="inconsistencias-titulo">
    <div class="notice-heading">
      <span class="warning-icon" aria-hidden="true">!</span>
      <div>
        <h2 id="inconsistencias-titulo">Possíveis inconsistências nas turmas</h2>
        <p><strong>{integerFormat.format(consistency.excludedRecords)} registros {course ? 'da matriz do curso' : 'da base'} foram excluídos dos cálculos</strong> até revisão.</p>
      </div>
    </div>
    {#if counts.length}
      <ul class="counts" aria-label="Casos por tipo">
        {#each counts as [count, label]}
          <li><strong>{integerFormat.format(count)}</strong> {label}</li>
        {/each}
      </ul>
    {/if}
    <details open={expanded} ontoggle={event => { opened = event.currentTarget.open; }}>
      <summary>Ver os casos sinalizados ({integerFormat.format(consistency.findings.length)})</summary>
      {#if opened || expanded}
        <ol class="findings">
          {#each consistency.findings as finding}
            <li class="finding">
              <h3>{finding.period} · {names[finding.kind] ?? finding.kind}</h3>
              <p>{finding.evidence}</p>
              {#if finding.room || finding.overlappingSlots?.length}
                <p class="overlap">
                  {#if finding.room}<strong>Sala {finding.room}</strong>{/if}
                  {#if finding.room && finding.overlappingSlots?.length} · {/if}
                  {#each finding.overlappingSlots ?? [] as [day, start, end], i}
                    {i ? ' · ' : ''}{day} {clock(start)}–{clock(end)}
                  {/each}
                </p>
              {/if}
              <ul class="offers">
                {#each finding.records as row}
                  <li>
                    <h4>{row.codigo} · {row.disciplina}</h4>
                    <p>{row.turma} · {integerFormat.format(row.matriculas)}/{integerFormat.format(row.capacidade)} matrículas/vagas</p>
                    <dl>
                      <dt>Local</dt><dd>{row.local || 'Sem registro'}</dd>
                      <dt>Docentes</dt><dd>{row.docentes || 'Sem registro'}</dd>
                      <dt>Horário e datas</dt><dd class="schedule">{row.horario || 'Sem registro'}</dd>
                    </dl>
                  </li>
                {/each}
              </ul>
              <p class="action">{finding.action}</p>
            </li>
          {/each}
        </ol>
      {/if}
    </details>
  </section>
{/if}

<style>
  .notice {
    margin-bottom: 24px;
    padding: clamp(16px, 2.5vw, 24px);
    border: 1px solid #d9a833;
    border-inline-start: 5px solid #ba8209;
    border-radius: 12px;
    background: #fff3c7;
    color: #513700;
    scroll-margin-top: 86px;
  }

  .notice-heading {
    display: flex;
    gap: 12px;
    align-items: flex-start;
  }

  .warning-icon {
    display: grid;
    flex: 0 0 26px;
    height: 26px;
    place-items: center;
    border-radius: 50%;
    background: #f4cf59;
    font-weight: 800;
  }

  h2 {
    margin-bottom: 4px;
    font-size: 1.08rem;
  }

  .counts {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 18px;
    margin: 12px 0 0;
    padding: 0;
    list-style: none;
    font-size: 0.88rem;
  }

  details {
    border-top-color: #e4cb80;
  }

  summary {
    color: inherit;
    font-size: 0.9rem;
    font-weight: 700;
  }

  .findings,
  .offers {
    display: grid;
    gap: 12px;
    margin: 12px 0 0;
    padding: 0;
    list-style: none;
  }

  .finding {
    padding: 14px;
    border: 1px solid #e4cb80;
    border-radius: 8px;
    background: #fffbec;
  }

  .finding h3,
  .offers h4 {
    margin-bottom: 4px;
    font-size: 0.95rem;
  }

  .overlap,
  .action {
    margin-top: 8px;
  }

  .offers {
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
  }

  .offers > li {
    min-width: 0;
    padding: 10px;
    border-radius: 6px;
    background: #fff;
    overflow-wrap: anywhere;
  }

  dl {
    margin-bottom: 0;
    font-size: 0.88rem;
  }

  dt {
    font-weight: 700;
  }

  dd {
    margin: 0 0 6px;
  }

  .schedule {
    white-space: pre-line;
  }
</style>

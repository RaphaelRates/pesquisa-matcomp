<script>
  import { courseUrl } from '../../lib/navigation.js';

  let { courses, group, scope, navigate } = $props();
  let drawer;
  let trigger;
  let open = $state(false);
  let restoreFocus = true;

  function toggle() {
    if (drawer.open) {
      drawer.close();
    } else {
      drawer.showModal();
      open = true;
    }
  }

  function closed() {
    open = false;
    if (restoreFocus && trigger.getClientRects().length) trigger.focus();
    restoreFocus = true;
  }

  function follow(event, course) {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey
      || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (drawer?.open) {
      restoreFocus = course === group;
      drawer.close();
    }
    navigate(course);
  }

  function closeOnDesktop() {
    if (drawer?.open && matchMedia('(min-width: 901px)').matches) drawer.close();
  }
</script>

<svelte:window onresize={closeOnDesktop} />

{#snippet courseLinks(compact)}
  <ul class="course-links">
    {#each courses as course (course.id)}
      <li>
        <a href={courseUrl(course.id, scope)} aria-current={course.id === group ? 'page' : undefined}
          aria-label={compact && course.id !== 'cct' ? course.title : undefined}
          title={compact && course.id !== 'cct' ? course.title : undefined}
          onclick={event => follow(event, course.id)}>
          {#if compact}
            {course.id === 'cct' ? 'Panorama do CCT' : course.id.toUpperCase()}
          {:else}
            <span class="course-code">{course.id.toUpperCase()}</span>
            {course.id === 'cct' ? 'Panorama do CCT' : course.title}
          {/if}
        </a>
      </li>
    {/each}
  </ul>
{/snippet}

<header class="topbar" id="inicio">
  <div class="topbar-inner">
    <a href={courseUrl('cct', scope)} class="topbar-brand" onclick={event => follow(event, 'cct')}>
      <span class="brand-mark" aria-hidden="true">∑</span>
      <span><strong>UFCA · CCT</strong><small>Oferta de disciplinas</small></span>
    </a>
    <nav class="desktop-nav" aria-label="Cursos">
      {@render courseLinks(true)}
    </nav>
    <button class="menu-toggle" type="button" aria-label={open ? 'Fechar menu de cursos' : 'Abrir menu de cursos'}
      aria-expanded={open} aria-controls="menu-cursos" bind:this={trigger} onclick={toggle}>
      <span class="hamburger" aria-hidden="true"><i></i><i></i><i></i></span>
    </button>
  </div>
</header>

<dialog class="course-drawer" id="menu-cursos" aria-labelledby="menu-cursos-titulo"
  bind:this={drawer} onclose={closed}>
  <form method="dialog" class="drawer-backdrop">
    <button type="submit" aria-label="Fechar menu de cursos" tabindex="-1"></button>
  </form>
  <div class="drawer-panel">
    <div class="drawer-heading">
      <h2 id="menu-cursos-titulo">Cursos</h2>
      <form method="dialog">
        <button class="menu-toggle drawer-close" type="submit" aria-label="Fechar menu de cursos">
          <span class="hamburger" aria-hidden="true"><i></i><i></i><i></i></span>
        </button>
      </form>
    </div>
    <nav aria-label="Cursos">
      {@render courseLinks(false)}
    </nav>
  </div>
</dialog>

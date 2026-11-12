<script>
  import { onMount } from 'svelte';
  import ChartCard from './ChartCard.svelte';

  let { sections, anchor, hash } = $props();

  onMount(() => {
    if (hash.startsWith(anchor)) document.getElementById(hash)?.scrollIntoView();
  });
</script>

{#each sections as section}
  {#if section.title}<h3 class="section-heading">{section.title}</h3>{/if}
  <div class="chart-grid">
    {#each section.plots as plot (plot.id)}
      <ChartCard {plot} {anchor} {hash} />
    {/each}
  </div>
{/each}

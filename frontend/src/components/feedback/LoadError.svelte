<script>
  let { error, retry, refresh = retry } = $props();
  const outdated = $derived(error.code === 'revision_changed');
</script>

<div class="empty-state" role="alert">
  <p>{error.message}</p>
  <button type="button" class="refresh-button" onclick={outdated ? refresh : retry}>
    {outdated ? 'Atualizar dados' : 'Tentar novamente'}
  </button>
</div>

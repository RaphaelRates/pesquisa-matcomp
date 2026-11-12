let apiOrigin;

export function configureApi(port) {
  const url = new URL(location.origin);
  url.port = port;
  apiOrigin = url.origin;
}

export async function requestDashboard(group, scope, resource, signal, revision) {
  const params = new URLSearchParams({ recorte: scope });
  if (revision) params.set('revisao', revision);
  const response = await fetch(`${apiOrigin}/api/v1/painel/${group}${resource}?${params}`, { signal });
  const payload = await response.json();
  if (!response.ok) {
    const error = new Error(payload.error?.message ?? `HTTP ${response.status}`);
    error.code = payload.error?.code;
    throw error;
  }
  return payload;
}

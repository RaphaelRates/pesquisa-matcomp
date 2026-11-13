const scopes = new Set(['accumulated', 'latest', 'compare']);

export function readScope() {
  const scope = new URL(location.href).searchParams.get('recorte');
  return scopes.has(scope) ? scope : 'accumulated';
}

export function readPair() {
  const params = new URL(location.href).searchParams;
  const pair = [params.get('referencia'), params.get('semestre')];
  return pair.every(Boolean) ? pair : undefined;
}

export function readGroup() {
  if (location.pathname === '/') return 'cct';
  return /^\/cursos\/([^/]+)\/*$/.exec(location.pathname)?.[1];
}

export function courseUrl(group, scope) {
  const path = group === 'cct' ? '/' : `/cursos/${group}`;
  return scope === 'accumulated' ? path : `${path}?recorte=${scope}`;
}

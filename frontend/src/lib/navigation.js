const scopes = new Set(['accumulated', 'historical', 'current']);

export function readScope() {
  const scope = new URL(location.href).searchParams.get('recorte');
  return scopes.has(scope) ? scope : 'accumulated';
}

export function readGroup() {
  if (location.pathname === '/') return 'cct';
  return /^\/cursos\/([^/]+)\/*$/.exec(location.pathname)?.[1];
}

export function courseUrl(group, scope) {
  const path = group === 'cct' ? '/' : `/cursos/${group}`;
  return scope === 'accumulated' ? path : `${path}?recorte=${scope}`;
}

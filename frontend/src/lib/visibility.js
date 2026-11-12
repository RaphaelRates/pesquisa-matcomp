// Um observador compartilhado evita criar um por seção e gráfico.
const callbacks = new Map();
let observer;

export function nearViewport(node, callback) {
  if (!('IntersectionObserver' in window)) {
    callback();
    return;
  }
  observer ??= new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      const load = callbacks.get(entry.target);
      observer.unobserve(entry.target);
      callbacks.delete(entry.target);
      load?.();
    }
  }, { rootMargin: '240px' });
  callbacks.set(node, callback);
  observer.observe(node);
  return {
    destroy() {
      observer.unobserve(node);
      callbacks.delete(node);
    },
  };
}

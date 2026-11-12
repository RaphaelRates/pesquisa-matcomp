"""Aplica o catálogo editável aos gráficos sem alterar seus cálculos."""

import json
from services.config import CATALOG_PATH




def allowed_types(plot):
    kind = plot.get('formato', plot.get('spec', {}).get('type'))
    if kind in {'bar', 'line', 'stackedBar', 'area'}:
        return ['bar', 'line', 'stackedBar', 'area']
    if kind in {'pie', 'donut'}:
        return ['donut', 'pie']
    return [kind]


def load_catalog_entries(content=None):
    if content is None:
        content = CATALOG_PATH.read_text(encoding='utf-8')
    catalog = json.loads(content)
    if not isinstance(catalog, dict) or not isinstance(catalog.get('graficos'), dict):
        raise ValueError('O catálogo deve conter um objeto graficos.')
    return catalog['graficos']


def apply_catalog(panels, disciplines, entries=None):
    if entries is None:
        entries = load_catalog_entries()
    plots = [p for panel in panels for section in panel['sections'] for p in section['plots']]
    plots.extend(p for d in disciplines['cct'] for p in d['plots'])
    for plot in plots:
        key = plot.get('catalogKey', plot['id'])
        entry = entries.get(key)
        if entry is None:
            continue  # Bases futuras podem introduzir gráficos sem personalização.
        if not isinstance(entry, dict):
            raise ValueError(f'A entrada {key} deve ser um objeto.')
        kind = entry.get('tipo')
        if kind not in allowed_types(plot):
            raise ValueError(f'Tipo incompatível no catálogo: {key}: {kind}')
        for field in ['nome', 'descricao']:
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError(f'Campo {field} inválido no gráfico {key}')
        plot['title'], plot['description'] = entry['nome'], entry['descricao']
        if 'formato' in plot:
            plot['formato'] = kind
        else:
            plot['spec']['type'] = kind

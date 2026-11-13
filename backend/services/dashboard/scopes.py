"""Ajusta séries, textos e identificação ao recorte exibido no painel."""

import re

SERIES_NAMES = {'Consolidadas': 'Recorte selecionado'}


def course_scope(scope, rows, *, course=True):
    """Descreve os semestres com oferta elegível no recorte."""
    periods = sorted({row['periodo'] for row in rows})
    open_periods = sorted({row['periodo'] for row in rows if row['situacao'] == 'ABERTA'})
    title = scope['label'].partition(' · ')[0]
    group = ' do curso' if course else ''
    if not periods:
        return dict(scope, periods=periods, label=f'{title} · sem oferta',
                    note=f'Sem turmas elegíveis{group} neste recorte.')

    span = f'{periods[0]} a {periods[-1]}' if len(periods) > 1 else periods[0]
    status = {'ABERTA': ' abertas', 'CONSOLIDADA': ' consolidadas'}.get(scope['status'], '')
    note = f'Turmas presenciais{status}{group} no recorte de {span}.'
    if open_periods:
        if scope['id'] != 'current' or scope['status'] == 'MISTA':
            note += f' Inclui turmas abertas de {", ".join(open_periods)}.'
        note += ' Matrículas e ocupação da oferta aberta ainda podem mudar.'
    return dict(scope, periods=periods, label=f'{title} · {span}', note=note)


def scope_text(text, scope, *, title=False):
    """Mantém o método e elimina avisos temporais do painel misto original."""
    if not text:
        return text
    if not title:
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ*])', text)
        text = ' '.join(sentence for sentence in sentences
                        if not sentence.startswith('*') and 'asterisco' not in sentence.lower())
    text = re.sub(r'\*Turmas abertas\.?', '', text, flags=re.I)
    text = text.replace('histórico consolidado', 'recorte selecionado')
    if scope['status'] == 'ABERTA':
        text = re.sub(r'consolidadas', 'abertas', text, flags=re.I)
        text = re.sub(r'consolidada', 'aberta', text, flags=re.I)
        text = text.replace('histórico', 'recorte selecionado').replace('Histórico', 'Recorte selecionado')
    elif scope['status'] == 'MISTA':
        text = re.sub(r'consolidadas?', 'do recorte', text, flags=re.I)
    return text.strip()


def _drop_comparison_series(plot):
    """O recorte possui uma amostra; a comparação entre períodos é externa."""
    removed = [i for i, name in enumerate(plot['columns']) if name == 'Abertas']
    if not removed:
        return
    plot['columns'] = [name for i, name in enumerate(plot['columns']) if i not in removed]
    plot['rows'] = [[value for i, value in enumerate(row) if i not in removed] for row in plot['rows']]
    spec = plot.get('spec', {})
    for axis in ('x', 'y'):
        if isinstance(spec.get(axis), list):
            spec[axis] = [name for name in spec[axis] if name != 'Abertas']


def scope_plot(plot, scope, row_count):
    _drop_comparison_series(plot)
    plot['columns'] = [SERIES_NAMES.get(name, name) for name in plot['columns']]
    spec = plot.get('spec', {})
    for axis in ('x', 'y'):
        value = spec.get(axis)
        if isinstance(value, list):
            spec[axis] = [SERIES_NAMES.get(name, name) for name in value]
        elif isinstance(value, str):
            spec[axis] = SERIES_NAMES.get(value, value)
    for field in ('title', 'description', 'method', 'interpretation'):
        if field in plot:
            plot[field] = scope_text(plot[field], scope, title=field == 'title')
    if not plot['description']:
        plot['description'] = 'Indicadores calculados com as turmas do recorte selecionado.'
    if plot['id'].endswith('-radar-faixas'):
        plot['description'] = 'Cada eixo mostra a proporção de turmas do recorte na respectiva faixa de ocupação.'
    if plot['id'].endswith('-estat-histograma'):
        plot['description'] = 'Proporções das turmas do recorte em seis intervalos de ocupação.'
    if plot['id'] == 'ufca-opt-curso':
        plot['description'] = ('Ocupação dos códigos listados como optativos na matriz de referência de cada curso. '
                               'Cada razão usa matrículas e vagas das turmas do recorte selecionado.')
    if plot.get('tooltips'):
        plot['tooltips'] = [
            scope_text('\n'.join(line for line in tip.split('\n') if not line.startswith('Abertas:'))
                        .replace('Consolidadas:', 'Recorte selecionado:'), scope)
            for tip in plot['tooltips']
        ]
    plot['scopeId'] = scope['id']
    plot['scope'] = scope['label']
    plot['scopeNote'] = scope['note']
    if not row_count:
        plot['rows'] = []
        if plot.get('tooltips') is not None:
            plot['tooltips'] = []
        if 'rankingValues' in plot:
            plot['rankingValues'] = []
    for alternative in plot.get('curriculumAlternatives', {}).values():
        scope_plot(alternative, scope, row_count)


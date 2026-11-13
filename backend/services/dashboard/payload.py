"""Monta os dados do painel a partir dos arquivos de semestre."""

from datetime import datetime, timezone
from services.config import DEFAULT_DATA, TITLE
from services.data.loader import load_offers
from services.data.preprocessing import preprocess_offers
from services.dashboard.periods import build_period_views
from services.analytics.comparison import attach_comparisons
from services.domain.courses import COURSES
from services.dashboard.groups import GROUPS, enrich_groups, attach_group_comparisons


def dashboard_data(data_path=DEFAULT_DATA):
    raw, source = load_offers(data_path)
    offers, report = preprocess_offers(raw)
    views = build_period_views(offers)
    enrich_groups(offers, views)
    baseline = views['baseline']
    attach_comparisons(views['current'], baseline, views['baselinePeriod'], views['currentPeriod'])
    attach_group_comparisons(views)
    views.pop('baseline')

    def plots(view):
        return [p for panel in view['paineis'] for section in panel['sections'] for p in section['plots']] + [
            p for discipline in view['disciplines']['cct'] for p in discipline['plots']] + [
            p for group in view['groups'].values() for section in group['sections'] for p in section['plots']
        ] + view['courseComparisons']['plots']

    reference_plots = {p['id']: p for p in plots(baseline)}
    current_plots = {p['id']: p for p in plots(views['current'])}
    for plot in current_plots.values():
        if views['baselinePeriod'] and plot['id'] in reference_plots:
            plot['comparison']['baselinePlot'] = reference_plots[plot['id']]
    for scope in ('historical', 'accumulated'):
        for plot in plots(views[scope]):
            if plot['id'] in current_plots:
                plot['comparison'] = current_plots[plot['id']]['comparison']
    current_panels = {p['id']: p for p in views['current']['paineis']}
    for scope in ('historical', 'accumulated'):
        for panel in views[scope]['paineis']:
            current = current_panels[panel['id']]
            for key in ('summary', 'statisticalSummary'):
                if key in panel and 'comparison' in current.get(key, {}):
                    panel[key]['comparison'] = current[key]['comparison']
    current_disciplines = {d['code']: d for d in views['current']['disciplines']['cct']}
    for scope in ('historical', 'accumulated'):
        for discipline in views[scope]['disciplines']['cct']:
            discipline['summary']['comparison'] = current_disciplines[discipline['code']]['summary']['comparison']
    # Registros auxiliares completos dos rankings servem ao cálculo das diferenças.
    # O navegador recebe apenas os resultados e os gráficos de referência.
    for view in (views['current'], views['historical'], views['accumulated'], baseline):
        for plot in plots(view):
            plot.pop('comparisonRecords', None)
    # Uma comparação por ID atende as duas abas e os códigos compartilhados com
    # MC, sem repetir grandes tabelas e gráficos de referência na transferência.
    comparisons = {key: plot.pop('comparison') for key, plot in current_plots.items()}
    for scope in ('historical', 'accumulated'):
        for plot in plots(views[scope]):
            plot.pop('comparison', None)
    source['currentEligibleRows'] = views['current']['groups']['cct']['summary']['selected']['n']
    return {"titulo": TITLE, "courses": list(COURSES), "groups": list(GROUPS), "views": views, "plotComparisons": comparisons, "source": source, "quality": report,
            "generatedAt": datetime.now(timezone.utc).isoformat()}


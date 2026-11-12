"""Cálculos sob demanda do painel web, com uma versão da base por consulta."""

from datetime import datetime, timezone
import hashlib
from threading import Lock

from services.analytics.comparison import compare_plots, compare_statistics, compare_summary
from services.analytics.disciplines import discipline_cohort_analyses
from services.analytics.metrics import course_panel, metrics, sources
from services.analytics.statistics import statistical_summary
from services.config import CATALOG_PATH, CURRENT_PERIOD
from services.dashboard.catalog import apply_catalog, load_catalog_entries
from services.dashboard.groups import GROUPS, GROUP_FAMILIES, course_comparisons, group_sections
from services.dashboard.periods import _keep_plot, period_samples, scope_summary
from services.dashboard.scopes import course_scope, scope_plot, scope_text
from services.data.loader import load_offers
from services.data.preprocessing import preprocess_offers
from services.domain.courses import COURSES, curriculum


GROUP_BY_ID = {group['id']: group for group in GROUPS}
COURSE_BY_KEY = {course['key']: course for course in COURSES}
SCOPES = ('accumulated', 'historical', 'current')
FAMILIES = {**GROUP_FAMILIES, 'curso': 'Análises específicas do curso', 'comparacao': 'Comparação entre cursos'}
SPECIFIC_CHARTS = {
    'comparacao', 'natureza', 'historico-obrigatorias', 'historico-optativas',
    'matriculas-historico', 'baixa-recorrente', 'maior-ocupacao', 'menor-ocupacao',
    'mais-vagas', 'mais-turmas', 'mais-semestres', 'sobras', 'lotadas', 'acima-capacidade',
    'obrigatorias-matriculas', 'optativas-matriculas',
}


class DisciplineNotFound(LookupError):
    """Código ausente do grupo consultado."""


class DashboardSnapshot:
    def __init__(self, offers, quality, source, catalog, revision):
        self.quality = quality
        self.catalog = catalog
        self.revision = revision
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.samples, self.scopes, self.known = period_samples(offers)
        self.source = dict(source, currentEligibleRows=len(self.samples['current']))
        self.baseline = next(iter(self.scopes['baseline']['periods']), None)

    def page(self, group_id, scope_id):
        group = GROUP_BY_ID[group_id]
        course = COURSE_BY_KEY.get(group['courseKey'])
        allowed = set.union(*curriculum(sources, course)) if course else self.known.keys()
        samples, scopes = self.samples, self.scopes
        if course:
            samples = {key: [row for row in rows if row['codigo'] in allowed]
                       for key, rows in self.samples.items()}
            scopes = {key: course_scope(self.scopes[key], rows) for key, rows in samples.items()}
        scope = scopes[scope_id]
        selected, current, baseline = (
            samples[key] for key in (scope_id, 'current', 'baseline')
        )
        summary = scope_summary(selected, scope)
        summary['comparison'] = compare_summary(
            metrics(baseline) if self.baseline else None, metrics(current), self.baseline)
        sections = list(GROUP_FAMILIES) + (['curso'] if course else ['comparacao'])
        return dict(group=group, scope=scope, scopes=[scopes[key] for key in SCOPES],
                    summary=summary, source=self.source, quality=self.quality, generatedAt=self.generated_at,
                    sections=[dict(id=key, title=FAMILIES[key]) for key in sections],
                    disciplines=[dict(code=code, name=self.known[code]) for code in sorted(allowed & self.known.keys())],
                    currentPeriod=CURRENT_PERIOD, baselinePeriod=self.baseline)

    def charts(self, group_id, scope_id, family=None, code=None):
        group = GROUP_BY_ID[group_id]
        course = COURSE_BY_KEY.get(group['courseKey'])
        allowed = set.union(*curriculum(sources, course)) if course else self.known.keys()
        if code is not None and (code not in self.known or code not in allowed):
            raise DisciplineNotFound(code)

        def sample(key):
            rows, scope = self.samples[key], self.scopes[key]
            selected = [row for row in rows if row['codigo'] in allowed] if course else rows
            if course:
                scope = course_scope(scope, selected)
            if code is not None:
                return self._discipline([row for row in selected if row['codigo'] == code], scope, code)
            if family == 'comparacao':
                result = course_comparisons(rows, scope, self.catalog)
                return dict(description=result['description'], sections=[dict(plots=result['plots'])])
            if family == 'curso':
                return self._course(rows, scope, course, len(selected))
            stats = statistical_summary(selected) if family == 'estatisticas' else None
            if stats is not None:
                stats.update(scope=scope['label'], scopeNote=scope['note'])
            return dict(statisticalSummary=stats, sections=group_sections(
                selected, scope, group, course, family, summary=stats, catalog=self.catalog))

        current, baseline = sample('current'), sample('baseline')
        result = current if scope_id == 'current' else sample(scope_id)

        def plots(payload):
            return {p['id']: p for section in payload['sections'] for p in section['plots']}

        current_plots, reference = plots(current), plots(baseline)
        for key, plot in plots(result).items():
            old = reference.get(key)
            comparison = compare_plots(old, current_plots[key], self.baseline)
            if self.baseline and old is not None:
                old.pop('comparisonRecords', None)
                comparison['baselinePlot'] = old
            plot.pop('comparisonRecords', None)
            plot['comparison'] = comparison
        if 'summary' in result:
            result['summary']['comparison'] = compare_summary(
                baseline['summary']['selected'], current['summary']['selected'], self.baseline)
        if result.get('statisticalSummary'):
            result['statisticalSummary']['comparison'] = compare_statistics(
                baseline['statisticalSummary'], current['statisticalSummary'], self.baseline)
        return result

    def _course(self, rows, scope, course, count):
        result = course_panel(rows, [], scope['periods'], course, specific_only=True)
        for section in result['sections']:
            section['title'] = scope_text(section['title'], scope, title=True)
            section['plots'] = [p for p in section['plots']
                                if p['id'].removeprefix(course['prefix'] + '-') in SPECIFIC_CHARTS]
        apply_catalog([result], {'cct': []}, self.catalog)
        for section in result['sections']:
            for plot in section['plots']:
                scope_plot(plot, scope, count)
        return dict(description=result['description'], sections=result['sections'])

    def _discipline(self, rows, scope, code):
        items = discipline_cohort_analyses(rows, [], scope['periods'], {code: self.known[code]}, only=code)
        result, = items['cct']
        apply_catalog([], items, self.catalog)
        result['summary'] = scope_summary(rows, scope)
        plots = [plot for plot in result.pop('plots') if _keep_plot(plot)]
        for plot in plots:
            scope_plot(plot, scope, len(rows))
        result['sections'] = [dict(plots=plots)]
        return result


class DashboardSnapshots:
    def __init__(self, data_path):
        self.data_path = data_path
        self.lock = Lock()
        self.snapshot = None

    def reload(self):
        with self.lock:
            raw, source = load_offers(self.data_path)
            catalog_text = CATALOG_PATH.read_text(encoding='utf-8')
            revision = hashlib.sha256((source['sha256'] + catalog_text).encode('utf-8')).hexdigest()
            if self.snapshot is None or self.snapshot.revision != revision:
                catalog = load_catalog_entries(catalog_text)
                offers, quality = preprocess_offers(raw)
                self.snapshot = DashboardSnapshot(offers, quality, source, catalog, revision)
            return self.snapshot

    def get(self, revision):
        with self.lock:
            if self.snapshot and self.snapshot.revision == revision:
                return self.snapshot
        return None

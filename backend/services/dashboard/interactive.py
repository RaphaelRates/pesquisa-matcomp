"""Cálculos sob demanda do painel web, com uma versão da base por consulta."""

from datetime import datetime, timezone
import hashlib
from threading import Lock

from services.analytics.comparison import compare_plots, compare_statistics, compare_summary
from services.analytics.disciplines import discipline_cohort_analyses
from services.analytics.metrics import course_panel, metrics, sources
from services.analytics.statistics import statistical_summary
from services.config import CATALOG_PATH
from services.dashboard.catalog import apply_catalog, load_catalog_entries
from services.dashboard.groups import GROUPS, GROUP_FAMILIES, course_comparisons, group_sections
from services.dashboard.periods import _keep_plot, period_breakdown, period_samples, scope_summary
from services.dashboard.scopes import course_scope, scope_plot, scope_text
from services.data.consistency import course_consistency
from services.data.loader import load_offers
from services.data.preprocessing import preprocess_offers
from services.domain.courses import COURSES, curriculum


GROUP_BY_ID = {group['id']: group for group in GROUPS}
COURSE_BY_KEY = {course['key']: course for course in COURSES}
SCOPES = ('accumulated', 'historical', 'current')
COMPARISON_SCOPES = ('latest', 'compare')
FAMILIES = {**GROUP_FAMILIES, 'curso': 'Análises específicas do curso', 'comparacao': 'Comparação entre cursos'}
SPECIFIC_CHARTS = {
    'comparacao', 'natureza', 'historico-obrigatorias', 'historico-optativas',
    'matriculas-historico', 'baixa-recorrente', 'maior-ocupacao', 'menor-ocupacao',
    'mais-vagas', 'mais-turmas', 'mais-semestres', 'sobras', 'lotadas', 'acima-capacidade',
    'obrigatorias-matriculas', 'optativas-matriculas',
}


class DisciplineNotFound(LookupError):
    """Código ausente do grupo consultado."""


class InvalidSemesterPair(ValueError):
    """A comparação exige dois semestres distintos com oferta no grupo."""


class DashboardSnapshot:
    def __init__(self, offers, quality, source, catalog, revision):
        self.quality = quality
        self.catalog = catalog
        self.revision = revision
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.samples, self.scopes, self.known = period_samples(offers)
        self.source = dict(source, currentEligibleRows=len(self.samples['current']))
        self.current = next(iter(self.scopes['current']['periods']), None)
        self.baseline = next(iter(self.scopes['baseline']['periods']), None)

    def _context(self, group_id, scope_id, pair):
        group = GROUP_BY_ID[group_id]
        course = COURSE_BY_KEY.get(group['courseKey'])
        allowed = set.union(*curriculum(sources, course)) if course else self.known.keys()
        samples, scopes = dict(self.samples), dict(self.scopes)
        if course:
            scopes = {key: course_scope(self.scopes[key], [row for row in rows if row['codigo'] in allowed])
                      for key, rows in self.samples.items()}
        baseline_period, current_period = self.baseline, self.current
        if scope_id in COMPARISON_SCOPES:
            periods = scopes['accumulated']['periods']
            if scope_id == 'latest' or pair is None:
                pair = tuple(([None, None] + periods)[-2:])
            elif pair[0] == pair[1] or any(period not in periods for period in pair):
                raise InvalidSemesterPair
            baseline_period, current_period = pair
            all_rows = self.samples['accumulated']
            definitions = (
                ('baseline', 'Semestre de referência', (baseline_period,)),
                ('current', 'Semestre comparado', (current_period,)),
                (scope_id, 'Semestres selecionados', pair),
            )
            for key, label, selected_periods in definitions:
                samples[key] = [row for row in all_rows if row['periodo'] in selected_periods]
                selected = [row for row in samples[key] if row['codigo'] in allowed]
                scopes[key] = course_scope(dict(id=key, label=label, status='MISTA'), selected, course=bool(course))
        return group, course, allowed, samples, scopes, baseline_period, current_period

    def page(self, group_id, scope_id, pair=None):
        group, course, allowed, samples, scopes, baseline_period, current_period = self._context(group_id, scope_id, pair)
        scope = scopes[scope_id]
        selected, current, baseline = (
            [row for row in samples[key] if row['codigo'] in allowed] for key in (scope_id, 'current', 'baseline')
        )
        summary = scope_summary(selected, scope)
        if current_period:
            summary['comparison'] = compare_summary(
                metrics(baseline) if baseline else None, metrics(current) if current else None,
                baseline_period, current_period)
        breakdown = period_breakdown(selected)
        available_semesters = period_breakdown(
            [row for row in samples['accumulated'] if row['codigo'] in allowed]
        )['semesters'] if scope_id in COMPARISON_SCOPES else breakdown['semesters']
        sections = list(GROUP_FAMILIES) + (['curso'] if course else ['comparacao'])
        disciplines = {row['codigo'] for row in selected} if scope_id in COMPARISON_SCOPES else allowed & self.known.keys()
        context = {'consistency': course_consistency(self.quality['consistency'], allowed)} if course else {}
        return dict(group=group, scope=scope, scopes=[scopes[key] for key in SCOPES],
                    summary=summary, periodBreakdown=breakdown, availableSemesters=available_semesters,
                    source=self.source, quality=self.quality,
                    generatedAt=self.generated_at,
                    sections=[dict(id=key, title=FAMILIES[key]) for key in sections],
                    disciplines=[dict(code=code, name=self.known[code]) for code in sorted(disciplines)],
                    currentPeriod=self.current, baselinePeriod=baseline_period,
                    comparedPeriod=current_period if scope_id in COMPARISON_SCOPES else None, **context)

    def charts(self, group_id, scope_id, family=None, code=None, pair=None):
        group, course, allowed, samples, scopes, baseline_period, current_period = self._context(group_id, scope_id, pair)
        if code is not None and (code not in self.known or code not in allowed):
            raise DisciplineNotFound(code)

        def sample(key):
            rows, scope = samples[key], scopes[key]
            selected = [row for row in rows if row['codigo'] in allowed] if course else rows
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

        if not current_period or not baseline_period:
            result = sample(scope_id)
            for section in result['sections']:
                for plot in section['plots']:
                    plot.pop('comparisonRecords', None)
            return result
        current = sample('current')
        baseline = sample('baseline')
        result = current if scope_id == 'current' else sample(scope_id)

        def plots(payload):
            return {p['id']: p for section in payload['sections'] for p in section['plots']}

        current_plots, reference = plots(current), plots(baseline)

        def attach(plot, old, new):
            comparison = compare_plots(old, new, baseline_period, current_period)
            if old is not None:
                old.pop('comparisonRecords', None)
                comparison['baselinePlot'] = {key: value for key, value in old.items()
                                              if key not in {'curriculumOptions', 'curriculumAlternatives'}}
            plot.pop('comparisonRecords', None)
            plot['comparison'] = comparison

        for key, plot in plots(result).items():
            old = reference.get(key)
            new = current_plots[key]
            for matrix, variant in plot.get('curriculumAlternatives', {}).items():
                attach(variant, old['curriculumAlternatives'][matrix], new['curriculumAlternatives'][matrix])
            attach(plot, old, new)
        if 'summary' in result:
            result['summary']['comparison'] = compare_summary(
                baseline['summary']['selected'] if baseline['summary']['selected']['n'] else None,
                current['summary']['selected'] if current['summary']['selected']['n'] else None,
                baseline_period, current_period)
        if result.get('statisticalSummary'):
            result['statisticalSummary']['comparison'] = compare_statistics(
                baseline['statisticalSummary'], current['statisticalSummary'], baseline_period, current_period)
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
        discipline_scope = course_scope(scope, rows, course=False)
        result['summary'] = scope_summary(rows, discipline_scope)
        plots = [plot for plot in result.pop('plots') if _keep_plot(plot)]
        for plot in plots:
            scope_plot(plot, discipline_scope, len(rows))
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

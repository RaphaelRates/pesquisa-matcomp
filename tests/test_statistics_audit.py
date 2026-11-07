"""A auditoria deve detectar erro no produto, inclusive sem mudar seus totais."""

import copy
import unittest

from services.audit_statistics import _association, _concentration, _distribution, audit_statistics
from services.period_views import build_period_views
from services.statistics_metrics import distribution_statistics, association_statistics


def offer(code, period, seats, enrolled, status='CONSOLIDADA'):
    return dict(codigo=code, disciplina='Disciplina', periodo=period, capacidade=seats,
                matriculas=enrolled, situacao=status, modalidade='Presencial',
                turma='01', horario='SEG 08:00-10:00')


class StatisticsAuditTests(unittest.TestCase):
    def setUp(self):
        self.offers = [offer('MC0001', '2026.1', 10, 0), offer('MC0001', '2026.1', 20, 10),
                       offer('MC0002', '2026.1', 10, 20), offer('CC0001', '2026.1', 50, 25),
                       offer('MC0001', '2026.2', 10, 0, 'ABERTA'),
                       offer('MC0014', '2026.2', 10, 0, 'ABERTA'),
                       offer('CC0001', '2026.2', 10, 0, 'ABERTA')]
        self.views = build_period_views(self.offers)

    def test_all_statistics_and_graph_rows_match_independent_recalculation(self):
        checks = audit_statistics(self.offers, self.views)
        self.assertEqual(len(checks), 32 * sum(k in self.views for k in ('historical', 'current', 'baseline', 'accumulated')))
        self.assertTrue(all(c['passed'] for c in checks), [c for c in checks if not c['passed']])

    def test_wrong_histogram_cell_is_detected_even_if_the_summary_is_unchanged(self):
        view = copy.deepcopy(self.views)
        panel = next(p for p in view['current']['paineis'] if p['id'] == 'ufca-estatistica')
        plot = next(p for s in panel['sections'] for p in s['plots'] if p['id'] == 'ufca-estat-histograma')
        plot['rows'][0][1] = .9
        failures = [c for c in audit_statistics(self.offers, view) if not c['passed']]
        self.assertEqual([c['id'] for c in failures], ['current/plot/ufca-estat-histograma'])

    def test_wrong_regression_trend_and_summary_index_are_detected(self):
        view = copy.deepcopy(self.views)
        panel = next(p for p in view['historical']['paineis'] if p['id'] == 'ufca-estatistica')
        panel['statisticalSummary']['concentration']['gini'] = -.5
        plot = next(p for s in panel['sections'] for p in s['plots'] if p['id'] == 'ufca-estat-regressao')
        plot['spec']['trend']['slope'] = 123
        failures = [c['id'] for c in audit_statistics(self.offers, view) if not c['passed']]
        self.assertIn('historical/ufca/estatisticas/resumo', failures)
        self.assertIn('historical/plot/ufca-estat-regressao/ajuste', failures)

    def test_reference_formulas_have_known_hand_calculated_values(self):
        d = _distribution([0, 1, 2, 3])
        self.assertEqual((d['q1'], d['median'], d['q3'], d['variance']), (.75, 1.5, 2.25, 1.25))
        c = _concentration([offer('A0001', '2026.1', 10, 1), offer('A0002', '2026.1', 10, 3)])
        self.assertEqual(c['gini'], .25)
        self.assertEqual(c['hhi'], .625)
        a = _association([offer('A0001', '2026.1', 10, 1), offer('A0002', '2026.1', 20, 4),
                          offer('A0003', '2026.1', 30, 9)])
        self.assertAlmostEqual(a['slope'], .01)
        self.assertAlmostEqual(a['intercept'], 0)
        self.assertAlmostEqual(a['pearson'], 1)
        self.assertAlmostEqual(a['spearman'], 1)

    def test_empty_references_and_constant_occupancies_stay_undefined(self):
        offers = [offer('MC0001', '2026.2', 10, 0, 'ABERTA')]
        checks = audit_statistics(offers, build_period_views(offers))
        self.assertTrue(all(c['passed'] for c in checks), [c for c in checks if not c['passed']])

    def test_non_binary_constant_occupancy_does_not_invent_variance_or_correlation(self):
        rows = [offer('MC0001', '2026.2', capacity, capacity // 10, 'ABERTA')
                for capacity in [10, 20, 30]]
        stats = distribution_statistics([r['matriculas'] / r['capacidade'] for r in rows])
        self.assertEqual(stats['mean'], .1)
        self.assertEqual(stats['variance'], 0)
        self.assertEqual(stats['standardDeviation'], 0)
        self.assertIsNone(stats['skewness'])
        self.assertIsNone(stats['excessKurtosis'])
        self.assertIsNone(association_statistics(rows)['pearson'])
        self.assertIsNone(association_statistics(rows)['rSquared'])
        checks = audit_statistics(rows, build_period_views(rows))
        self.assertTrue(all(c['passed'] for c in checks), [c for c in checks if not c['passed']])


if __name__ == '__main__':
    unittest.main()

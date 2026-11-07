"""A segunda conta precisa detectar erros e cobrir todos os gráficos."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from services.period_views import build_period_views
from services.period_comparison import attach_comparisons
from services.preprocessing import preprocess_offers
from services.recalculation import audit_calculations, audit_disciplines, audit_comparisons, selected_rows


def offer(period, enrolled, capacity=10, status='CONSOLIDADA'):
    return dict(periodo=period, codigo='MC0001', disciplina='Cálculo I', turma='01',
                docentes='Docente', tipo='REGULAR', modalidade='Presencial', situacao=status,
                horario='SEG 08:00-10:00', local='Sala', matriculas=enrolled, capacidade=capacity)


def prepare(rows):
    views = build_period_views(rows)
    attach_comparisons(views['current'], views['baseline'], views['baselinePeriod'])
    return views


class RecalculationTests(unittest.TestCase):
    def test_all_real_charts_are_recomputed_and_covered(self):
        path = Path(__file__).resolve().parents[1] / 'data' / 'ufca-cct-ofertas-2023-2026.json'
        rows, _ = preprocess_offers(json.loads(path.read_text(encoding='utf-8-sig')))
        report = audit_calculations(rows, prepare(rows))
        self.assertEqual(report['failures'], [])
        self.assertTrue(report['passed'])
        self.assertEqual(report['checkedCharts'], report['expectedCharts'])
        self.assertGreater(report['checkedCharts'], 7000)
        historical = report['totals']['historical']['cct']
        self.assertEqual((historical['n'], historical['c'], historical['m']), (1208, 48726, 26094))
        self.assertEqual(sum(r['cct']['c'] for r in report['bySemester'] if r['status'] == 'CONSOLIDADA'), historical['c'])
        self.assertAlmostEqual(historical['rate'], 26094 / 48726)
        accumulated = report['totals']['accumulated']['cct']
        self.assertEqual((accumulated['n'], accumulated['c'], accumulated['m']), (1380, 55721, 30126))
        mc = report['totals']['accumulated']['mc']
        self.assertEqual((mc['n'], mc['c'], mc['m']), (137, 6348, 2921))
        for field in ('n', 'c', 'm'):
            self.assertEqual(sum(r['cct'][field] for r in report['bySemester']), accumulated[field])
        self.assertEqual(len(report['bySemester']), 8)

    def test_accumulated_selects_mixed_statuses_without_future_or_old_records(self):
        rows = [offer('2022.2', 9), offer('2023.1', 1),
                offer('2026.2', 2, status='ABERTA'), offer('2026.2', 7),
                offer('2027.1', 8), offer('2025.2', 6, status='ABERTA')]
        views = prepare(rows)
        chosen = selected_rows(rows, views['accumulated'])
        self.assertEqual([(r['periodo'], r['situacao']) for r in chosen],
                         [('2023.1', 'CONSOLIDADA'), ('2026.2', 'ABERTA')])
        report = audit_calculations(rows, views)
        self.assertTrue(report['passed'], report['failures'][:3])
        self.assertEqual(report['totals']['accumulated']['cct']['m'], 3)
        # Chamadores que fornecem as três views anteriores continuam cobertos.
        views.pop('accumulated')
        report = audit_calculations(rows, views)
        self.assertTrue(report['passed'], report['failures'][:3])
        self.assertNotIn('accumulated', report['totals'])

    def test_accumulated_discipline_changes_are_audited(self):
        rows = [offer('2026.1', 3), offer('2026.2', 7, status='ABERTA')]
        views = prepare(rows)
        discipline = views['accumulated']['disciplines']['cct'][0]
        discipline['plots'][0]['rows'][0][1] = 999
        failures = [c for c in audit_disciplines(rows, views) if not c['passed']]
        self.assertEqual([c['id'] for c in failures], ['accumulated/plot/cadeira-MC0001-oferta'])

    def test_modified_discipline_cell_and_summary_are_detected(self):
        rows = [offer('2026.1', 3), offer('2026.2', 7, status='ABERTA')]
        views = prepare(rows)
        discipline = views['current']['disciplines']['cct'][0]
        discipline['plots'][0]['rows'][0][1] = 999
        discipline['summary']['selected']['c'] = 999
        failures = [c for c in audit_disciplines(rows, views) if not c['passed']]
        self.assertEqual(len(failures), 2)

    def test_mutated_difference_is_detected(self):
        rows = [offer('2026.1', 3), offer('2026.2', 7, status='ABERTA')]
        views = prepare(rows)
        current = next(p for p in views['current']['paineis'] if p['id'] == 'evolucao')
        current['summary']['comparison']['rows'][0]['delta'] = 999
        self.assertTrue(any(not c['passed'] for c in audit_comparisons(views)))

    def test_empty_and_zero_baseline_are_verified(self):
        for rows in ([offer('2026.2', 1, status='ABERTA')], [offer('2026.1', 0), offer('2026.2', 0, status='ABERTA')]):
            report = audit_calculations(rows, prepare(rows))
            self.assertTrue(report['passed'], report['failures'][:3])


if __name__ == '__main__':
    unittest.main()

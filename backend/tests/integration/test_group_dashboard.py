"""Grupos selecionáveis mantêm recorte, totais e comparações consistentes."""

import json
import unittest

from services.dashboard.groups import GROUPS, attach_group_comparisons, enrich_groups
from services.dashboard.periods import build_period_views
from services.config import DEFAULT_DATA
from services.data.loader import load_offers
from services.data.preprocessing import preprocess_offers


def offer(code, enrolled, seats=10, period='2026.2', status='ABERTA'):
    return dict(codigo=code, disciplina=f'Disciplina {code}', periodo=period,
                capacidade=seats, matriculas=enrolled, situacao=status,
                modalidade='Presencial', turma='01', horario='SEG 08:00-10:00')


def prepare(rows):
    views = build_period_views(rows)
    enrich_groups(rows, views)
    attach_group_comparisons(views)
    return views


class GroupDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [offer('MC0001', 2), offer('CC0001', 5), offer('EM0004', 8),
                    offer('ECI0079', 9), offer('ES0001', 10),
                    offer('MC0001', 4, period='2026.1', status='CONSOLIDADA')]
        cls.views = prepare(cls.rows)

    def test_all_groups_have_same_chart_families_and_unique_ids(self):
        for key in ('accumulated', 'historical', 'current', 'baseline'):
            view = self.views[key]
            self.assertEqual(list(view['groups']), [group['id'] for group in GROUPS])
            self.assertNotIn('car', view['groups'])
            ids = []
            for group in view['groups'].values():
                plots = [p for section in group['sections'] for p in section['plots']]
                self.assertEqual(len(plots), 37)
                self.assertIn('statisticalSummary', group)
                ids.extend(plot['id'] for plot in plots)
            ids.extend(p['id'] for p in view['courseComparisons']['plots'])
            self.assertEqual(len(ids), len(set(ids)))

    def test_groups_select_different_data_without_adding_course_totals(self):
        groups = self.views['current']['groups']
        self.assertEqual(groups['cct']['summary']['selected']['m'], 34)
        for key, enrolled in [('mc', 2), ('cc', 5), ('em', 8), ('eci', 9), ('es', 10)]:
            self.assertEqual(groups[key]['summary']['selected']['m'], enrolled)
            self.assertEqual(groups[key]['summary']['selected']['n'], 1)
            plot = next(p for section in groups[key]['sections'] for p in section['plots']
                        if p['id'].endswith('-ufca-capacidade-matriculas'))
            self.assertEqual(plot['rows'], [['2026.2*', 10, enrolled]])

    def test_group_comparison_uses_single_reference_semester(self):
        group = self.views['accumulated']['groups']['mc']
        self.assertEqual(group['summary']['selected']['m'], 6)
        comparison = group['summary']['comparison']
        enrolled = next(row for row in comparison['rows'] if row['metric'] == 'Matrículas')
        self.assertEqual((enrolled['before'], enrolled['after'], enrolled['delta']), (4, 2, -2))
        plot = next(p for section in group['sections'] for p in section['plots']
                    if p['id'].endswith('-ufca-capacidade-matriculas'))
        self.assertEqual(plot['comparison']['baselinePlot']['rows'], [['2026.1', 10, 4]])

    def test_shared_car_does_not_duplicate_cct(self):
        groups = prepare([offer('CAR0010', 7)])['accumulated']['groups']
        self.assertEqual(groups['cct']['summary']['selected']['n'], 1)
        self.assertEqual(groups['cct']['summary']['selected']['m'], 7)
        self.assertGreater(sum(g['summary']['selected']['n'] for k, g in groups.items() if k != 'cct'), 1)

    def test_empty_group_has_undefined_occupancy_and_no_fake_points(self):
        groups = prepare([offer('MC0001', 0)])['current']['groups']
        self.assertEqual(groups['mc']['summary']['selected']['rate'], 0)
        self.assertIsNone(groups['em']['summary']['selected']['rate'])
        self.assertEqual(groups['em']['summary']['scope']['periods'], [])
        self.assertTrue(all(not p['rows'] for s in groups['em']['sections'] for p in s['plots']))
        json.dumps(groups, allow_nan=False)

    def test_semester_files_preserve_real_cct_totals_in_every_group_view(self):
        raw, _ = load_offers(DEFAULT_DATA)
        rows, _ = preprocess_offers(raw)
        views = prepare(rows)
        for scope, expected in [('historical', (2330, 96830, 51512)),
                                ('current', (168, 6845, 3948)),
                                ('accumulated', (2500, 103735, 55460))]:
            group = views[scope]['groups']['cct']['summary']['selected']
            self.assertEqual((group['n'], group['c'], group['m']), expected)
            self.assertAlmostEqual(group['rate'], expected[2] / expected[1])
        for key, n in [('mc', 222), ('cc', 323), ('em', 902), ('eci', 1043), ('es', 31)]:
            self.assertEqual(views['accumulated']['groups'][key]['summary']['selected']['n'], n)
        view = views['accumulated']
        software = view['groups']['es']
        self.assertEqual(software['summary']['scope']['periods'], ['2025.1', '2025.2', '2026.1', '2026.2'])
        panel = next(p for p in view['paineis'] if p.get('courseKey') == 'software')
        plot = next(p for s in panel['sections'] for p in s['plots'] if p['id'] == 'software-comparacao')
        self.assertEqual([row[0] for row in plot['rows']], ['2025.1', '2025.2', '2026.1', '2026.2*'])


if __name__ == '__main__':
    unittest.main()

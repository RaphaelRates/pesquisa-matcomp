"""O acumulado inclui as abertas de 2026.2, preservando suas situações."""

from copy import deepcopy
import unittest

from services.dashboard.periods import build_period_views
from services.data.preprocessing import preprocess_offers
from services.data.loader import load_offers
from services.config import DEFAULT_DATA


def offer(period, seats, enrolled, status='CONSOLIDADA'):
    return dict(codigo='MC0001', disciplina='Cálculo I', periodo=period, capacidade=seats,
                matriculas=enrolled, situacao=status, modalidade='Presencial',
                turma='01', horario='SEG 08:00-10:00')


def panel(view, key):
    return next(p for p in view['paineis'] if p['id'] == key)


class AccumulatedViewTests(unittest.TestCase):
    def test_included_dataset_totals_include_open_2026_2(self):
        raw, _ = load_offers(DEFAULT_DATA)
        offers, _ = preprocess_offers(raw)
        original = deepcopy(offers)
        view = build_period_views(offers)['accumulated']
        self.assertEqual(offers, original)
        cct = panel(view, 'evolucao')['summary']
        mc = panel(view, 'matematica-computacional')['summary']
        for summary, expected in [(cct, (1350, 54478, 29421)), (mc, (134, 6195, 2844))]:
            m = summary['selected']
            self.assertEqual((m['n'], m['c'], m['m']), expected)
            self.assertAlmostEqual(m['rate'], expected[2] / expected[1])
            self.assertEqual(summary['historico']['n'] + summary['abertas']['n'], m['n'])
        self.assertEqual(cct['historico']['n'], 1182)
        self.assertEqual(cct['abertas']['n'], 168)
        chart = next(p for s in panel(view, 'evolucao')['sections'] for p in s['plots']
                     if p['id'] == 'ufca-capacidade-matriculas')
        self.assertEqual(chart['rows'][-1], ['2026.2*', 6845, 3948])
        self.assertIn('2023.1', view['scope']['periods'])
        self.assertIn('2026.2', view['scope']['periods'])
        self.assertEqual(view['scope']['status'], 'MISTA')

    def test_accumulated_excludes_before_2023_1_and_unselected_statuses(self):
        offers = [offer('2022.2', 99, 99), offer('2023.1', 10, 2), offer('2026.1', 20, 10),
                  offer('2026.2', 30, 18, 'ABERTA'), offer('2026.2', 99, 99),
                  offer('2027.1', 99, 99)]
        original = deepcopy(offers)
        views = build_period_views(offers)
        summary = panel(views['accumulated'], 'evolucao')['summary']
        self.assertEqual(offers, original)
        self.assertEqual((summary['selected']['n'], summary['selected']['c'], summary['selected']['m']), (3, 60, 30))
        self.assertEqual(summary['historico']['n'], 2)
        self.assertEqual(summary['abertas']['n'], 1)
        self.assertEqual(panel(views['historical'], 'evolucao')['summary']['selected']['n'], 3)
        self.assertEqual(views['accumulated']['scope']['periods'], ['2023.1', '2026.1', '2026.2'])

    def test_accumulated_metadata_describes_mixed_offering(self):
        view = build_period_views([offer('2026.1', 10, 5), offer('2026.2', 10, 8, 'ABERTA')])['accumulated']
        for p in view['paineis']:
            for section in p['sections']:
                for chart in section['plots']:
                    for field in ('title', 'description', 'method', 'interpretation'):
                        self.assertNotIn('consolidada', chart.get(field, '').lower(), (chart['id'], field))
                    self.assertIn('abertas de 2026.2', chart['scopeNote'])
        discipline = next(d for d in view['disciplines']['mc'] if d['code'] == 'MC0001')
        self.assertEqual(discipline['summary']['selected']['n'], 2)
        self.assertEqual(discipline['summary']['historico']['n'], 1)
        self.assertEqual(discipline['summary']['abertas']['n'], 1)


if __name__ == '__main__':
    unittest.main()

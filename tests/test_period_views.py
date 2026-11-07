"""Os recortes devem se manter separados em todas as famílias de gráficos."""

from copy import deepcopy
import json
import unittest

from services.period_views import build_period_views


def offer(code, period, seats, enrolled, status='CONSOLIDADA', modality='Presencial'):
    return dict(codigo=code, disciplina=code + ' disciplina', periodo=period,
                capacidade=seats, matriculas=enrolled, situacao=status,
                modalidade=modality, turma='01', horario='SEG 08:00-10:00')


def panel(view, key):
    return next(p for p in view['paineis'] if p['id'] == key)


def plot(view, key):
    return next(p for panel in view['paineis'] for section in panel['sections']
                for p in section['plots'] if p['id'] == key)


class PeriodViewTests(unittest.TestCase):
    def setUp(self):
        self.offers = [
            offer('MC0001', '2025.2', 10, 2),
            offer('MC0001', '2026.1', 20, 10),
            offer('CC0001', '2026.1', 10, 9),
            offer('MC0001', '2026.2', 20, 18, 'ABERTA'),
            offer('CC0001', '2026.2', 10, 5, 'ABERTA'),
            offer('MC0001', '2026.2', 99, 99),  # Situação diferente da oferta aberta.
            offer('MC0001', '2027.1', 99, 99),  # Não pertence ao histórico anterior.
            offer('MC0001', '2026.2', 99, 99, 'ABERTA', 'A Distância'),
            offer('MC0001', '2026.2', 0, 0, 'ABERTA'),
        ]

    def test_scopes_do_not_mix_or_reclassify_original_records(self):
        original = deepcopy(self.offers)
        views = build_period_views(self.offers)
        self.assertEqual(self.offers, original)
        self.assertEqual(views['baselinePeriod'], '2026.1')
        self.assertEqual(views['historicalPeriods'], ['2025.2', '2026.1'])
        for key, counts in [('historical', (3, 40, 21)), ('current', (2, 30, 23)), ('baseline', (2, 30, 19))]:
            summary = panel(views[key], 'evolucao')['summary']['selected']
            self.assertEqual((summary['n'], summary['c'], summary['m']), counts)
        self.assertEqual(panel(views['current'], 'evolucao')['summary']['historico']['n'], 0)
        self.assertEqual(panel(views['historical'], 'evolucao')['summary']['abertas']['n'], 0)
        json.dumps(views, allow_nan=False)

    def test_current_uses_its_own_turns_rankings_statistics_and_discipline_charts(self):
        views = build_period_views(self.offers)
        current, baseline = views['current'], views['baseline']
        turns = plot(current, 'ufca-turnos')
        self.assertAlmostEqual(turns['rows'][0][1], 23 / 30)
        stats = panel(current, 'ufca-estatistica')['statisticalSummary']
        self.assertEqual(stats['occupancy']['n'], 2)
        self.assertAlmostEqual(stats['occupancy']['mean'], .7)
        histogram = plot(current, 'ufca-estat-histograma')
        self.assertEqual(histogram['columns'], ['Intervalo', 'Recorte selecionado'])
        self.assertEqual(histogram['spec']['y'], ['Recorte selecionado'])
        current_ranking = plot(current, 'ufca-ranking-geral-1-1')
        self.assertEqual({r['label'].split(' · ')[0]: r['value'] for r in current_ranking['comparisonRecords']},
                         {'MC0001': 18.0, 'CC0001': 5.0})
        baseline_ranking = plot(baseline, 'ufca-ranking-geral-1-1')
        self.assertEqual({r['label'].split(' · ')[0]: r['value'] for r in baseline_ranking['comparisonRecords']},
                         {'MC0001': 10.0, 'CC0001': 9.0})
        mc = next(d for d in current['disciplines']['mc'] if d['code'] == 'MC0001')
        self.assertEqual(mc['summary']['selected']['m'], 18)
        self.assertEqual(len(mc['plots']), 8)
        self.assertAlmostEqual(next(p for p in mc['plots'] if p['catalogKey'] == 'cadeira-turnos')['rows'][0][1], .9)

    def test_absent_current_offer_stays_selectable_without_fabricating_zero_occupancy(self):
        views = build_period_views([offer('MC0001', '2026.1', 10, 5), offer('CC0001', '2026.2', 10, 7, 'ABERTA')])
        mc = next(d for d in views['current']['disciplines']['mc'] if d['code'] == 'MC0001')
        self.assertEqual(mc['summary']['selected']['n'], 0)
        self.assertIsNone(mc['summary']['selected']['rate'])
        self.assertTrue(all(p['rows'] == [] for p in mc['plots']))

    def test_missing_baseline_or_current_is_valid(self):
        only_current = build_period_views([offer('MC0001', '2026.2', 10, 7, 'ABERTA')])
        self.assertIsNone(only_current['baselinePeriod'])
        self.assertEqual(panel(only_current['baseline'], 'evolucao')['summary']['selected']['n'], 0)
        only_history = build_period_views([offer('MC0001', '2026.1', 10, 7)])
        self.assertEqual(panel(only_history['current'], 'evolucao')['summary']['selected']['n'], 0)
        self.assertTrue(all(p['rows'] == [] for p in panel(only_history['current'], 'matematica-computacional')['sections'][0]['plots']))


if __name__ == '__main__':
    unittest.main()

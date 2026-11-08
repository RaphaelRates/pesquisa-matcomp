"""Evita diferenças enganosas por mudanças de ranking ou ausência de oferta."""

import json
import unittest

from services.analytics.comparison import (
    attach_comparisons, compare_plots, compare_statistics, compare_summary,
)


def plot(kind, columns, rows, **spec):
    return dict(id='example', columns=columns, rows=rows, spec=dict(type=kind, **spec))


class PeriodComparisonTests(unittest.TestCase):
    def test_percentage_points_differ_from_relative_percentage(self):
        before = plot('line', ['Semestre', 'Ocupação'], [['2026.1', .4]],
                      x='Semestre', y=['Ocupação'], valueFormat={'style': 'percent'})
        after = plot('line', ['Semestre', 'Ocupação'], [['2026.2*', .6]],
                     x='Semestre', y=['Ocupação'], valueFormat={'style': 'percent'})
        row = compare_plots(before, after, '2026.1')['rows'][0]
        self.assertEqual(row['category'], 'Total do semestre')
        self.assertAlmostEqual(row['delta'], .2)
        self.assertAlmostEqual(row['relativeChange'], .5)
        self.assertEqual(row['unit'], 'percent')

    def test_zero_baseline_has_absolute_difference_without_infinity(self):
        compared = compare_summary({'m': 0, 'rate': 0}, {'m': 10, 'rate': .5}, '2026.1')
        row = next(r for r in compared['rows'] if r['metric'] == 'Matrículas')
        self.assertEqual(row['delta'], 10)
        self.assertIsNone(row['relativeChange'])
        self.assertEqual(row['status'], 'zero_baseline')
        json.dumps(compared, allow_nan=False)

    def test_missing_reference_semester_does_not_become_zero_baseline(self):
        comparison = compare_summary({'n': 0, 'c': 0}, {'n': 10, 'c': 500}, None)
        self.assertIsNone(comparison['rows'][0]['before'])
        self.assertIsNone(comparison['rows'][0]['delta'])
        self.assertEqual(comparison['rows'][0]['status'], 'no_baseline')

    def test_rank_positions_and_bar_width_are_not_comparison_values(self):
        before = dict(id='r', formato='ranking', rows=[['1. CC0001 · Nome antigo', '40', 100]],
                      rankingValues=[40], rankingPercent=False)
        after = dict(id='r', formato='ranking', rows=[['3. CC0001 · Nome novo', '50', 20]],
                     rankingValues=[50], rankingPercent=False)
        row = compare_plots(before, after, '2026.1')['rows'][0]
        self.assertEqual(row['category'], 'CC0001')
        self.assertEqual((row['before'], row['after'], row['delta']), (40, 50, 10))

    def test_full_ranking_records_compare_code_outside_displayed_top(self):
        before = dict(id='r', formato='ranking', rows=[['1. MC0001', '50', 100]],
                      rankingValues=[50], comparisonMetric='Matrículas',
                      comparisonRecords=[{'label': 'MC0001 · Cálculo', 'value': 50},
                                         {'label': 'MC0002 · Geometria', 'value': 30}])
        after = dict(id='r', formato='ranking', rows=[['1. MC0002', '60', 100]],
                     rankingValues=[60], comparisonMetric='Matrículas',
                     comparisonRecords=[{'label': 'MC0001 · Cálculo', 'value': 20},
                                        {'label': 'MC0002 · Geometria', 'value': 60}])
        rows = {r['category']: r for r in compare_plots(before, after, '2026.1')['rows']}
        self.assertEqual(rows['MC0001']['delta'], -30)
        self.assertEqual(rows['MC0002']['delta'], 30)

    def test_absent_category_is_not_treated_as_zero(self):
        before = plot('horizontalBar', ['Disciplina', 'Matrículas'], [['CC0001 · Cálculo', 20]],
                      y='Disciplina', x='Matrículas')
        after = plot('horizontalBar', ['Disciplina', 'Matrículas'], [['CC0002 · Geometria', 30]],
                     y='Disciplina', x='Matrículas')
        rows = {r['category']: r for r in compare_plots(before, after, '2026.1')['rows']}
        self.assertEqual(rows['CC0001']['status'], 'no_current')
        self.assertIsNone(rows['CC0001']['delta'])
        self.assertEqual(rows['CC0002']['status'], 'no_baseline')
        self.assertIsNone(rows['CC0002']['delta'])

    def test_heatmap_preserves_both_non_temporal_dimensions(self):
        before = plot('heatmap', ['Dia', 'Hora', 'Turmas'], [['Seg', '08h', 3], ['Ter', '08h', 5]],
                      x='Dia', y='Hora', value='Turmas')
        after = plot('heatmap', ['Dia', 'Hora', 'Turmas'], [['Seg', '08h', 4], ['Ter', '08h', 2]],
                     x='Dia', y='Hora', value='Turmas')
        rows = {r['category']: r for r in compare_plots(before, after, '2026.1')['rows']}
        self.assertEqual(rows['Seg · 08h']['delta'], 1)
        self.assertEqual(rows['Ter · 08h']['delta'], -3)

    def test_class_count_suffix_and_semester_labels_are_not_categories(self):
        before = plot('horizontalBar', ['Turno', 'Ocupação'], [['Manhã · 3 turmas', .5]],
                      y='Turno', x='Ocupação', valueFormat={'style': 'percent'})
        after = plot('horizontalBar', ['Turno', 'Ocupação'], [['Manhã · 4 turmas', .75]],
                     y='Turno', x='Ocupação', valueFormat={'style': 'percent'})
        rows = compare_plots(before, after, '2026.1')['rows']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['category'], 'Manhã')
        self.assertEqual(rows[0]['delta'], .25)

    def test_no_artificial_pairing_of_classes_or_scatter_points(self):
        for kind in ['scatter', 'bubble', 'statisticalScatter']:
            p = plot(kind, ['Vagas', 'Matrículas'], [[50, 30]], x='Vagas', y='Matrículas')
            result = compare_plots(p, p, '2026.1')
            self.assertEqual(result['rows'], [])
            self.assertIn('não são as mesmas', result['note'])
        p = plot('bar', ['Turma', 'Ocupação'], [['Turma 01', .5]], x='Turma', y=['Ocupação'])
        p['catalogKey'] = 'cadeira-por-turma'
        self.assertEqual(compare_plots(p, p, '2026.1')['rows'], [])

    def test_different_curve_thresholds_are_not_interpolated(self):
        before = plot('line', ['Ocupação', 'Recorte selecionado'], [[0, 0], [.5, .7]],
                      x='Ocupação', y=['Recorte selecionado'], numericX=True,
                      xValueFormat={'style': 'percent'}, valueFormat={'style': 'percent'})
        after = plot('line', ['Ocupação', 'Recorte selecionado'], [[0, 0], [.75, .9]],
                     x='Ocupação', y=['Recorte selecionado'], numericX=True,
                     xValueFormat={'style': 'percent'}, valueFormat={'style': 'percent'})
        rows = {r['category']: r for r in compare_plots(before, after, '2026.1')['rows']}
        self.assertEqual(rows['0%']['delta'], 0)
        self.assertIsNone(rows['50%']['delta'])
        self.assertIsNone(rows['75%']['delta'])

    def test_indices_have_signed_difference_without_relative_percentage(self):
        comparison = compare_statistics({'association': {'pearson': -.5}},
                                        {'association': {'pearson': .3}}, '2026.1')
        row = next(r for r in comparison['rows'] if r['metric'].startswith('Pearson'))
        self.assertAlmostEqual(row['delta'], .8)
        self.assertIsNone(row['relativeChange'])
        self.assertEqual(row['unit'], 'decimal')

    def test_attaches_plot_and_selected_summary_comparisons(self):
        p = plot('bar', ['Semestre', 'Turmas'], [['2026.2*', 10]], x='Semestre', y=['Turmas'])
        old = plot('bar', ['Semestre', 'Turmas'], [['2026.1', 12]], x='Semestre', y=['Turmas'])
        current = {'paineis': [{'id': 'evolucao', 'summary': {'selected': {'n': 10}},
                               'sections': [{'plots': [p]}]}], 'disciplines': {'cct': []}}
        baseline = {'paineis': [{'id': 'evolucao', 'summary': {'selected': {'n': 12}},
                                'sections': [{'plots': [old]}]}], 'disciplines': {'cct': []}}
        attach_comparisons(current, baseline, '2026.1')
        self.assertEqual(p['comparison']['rows'][0]['delta'], -2)
        self.assertEqual(current['paineis'][0]['summary']['comparison']['rows'][0]['delta'], -2)
        self.assertEqual(p['rows'], [['2026.2*', 10]])

    def test_other_capacities_are_not_a_stable_comparison_category(self):
        before = plot('pie', ['Capacidade', 'Turmas'], [['50 vagas', 3], ['Outras capacidades', 4]],
                      x='Capacidade', y='Turmas')
        after = plot('pie', ['Capacidade', 'Turmas'], [['50 vagas', 4], ['Outras capacidades', 7]],
                     x='Capacidade', y='Turmas')
        result = compare_plots(before, after, '2026.1')
        self.assertEqual([row['category'] for row in result['rows']], ['50 vagas'])
        self.assertEqual(result['rows'][0]['delta'], 1)
        self.assertIn('omitido', result['note'])

    def test_distinct_close_numeric_thresholds_are_not_paired(self):
        before = plot('line', ['Ocupação', 'Recorte selecionado'], [[.50000001, .4]],
                      x='Ocupação', y=['Recorte selecionado'], numericX=True,
                      xValueFormat={'style': 'percent'}, valueFormat={'style': 'percent'})
        after = plot('line', ['Ocupação', 'Recorte selecionado'], [[.50000002, .6]],
                     x='Ocupação', y=['Recorte selecionado'], numericX=True,
                     xValueFormat={'style': 'percent'}, valueFormat={'style': 'percent'})
        rows = compare_plots(before, after, '2026.1')['rows']
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row['delta'] is None for row in rows))


if __name__ == '__main__':
    unittest.main()

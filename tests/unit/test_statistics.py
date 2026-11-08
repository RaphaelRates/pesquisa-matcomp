"""Definições estatísticas e casos de ocupação sem variabilidade."""

import unittest

from services.analytics.statistics import (
    association_statistics,
    concentration_statistics,
    distribution_statistics,
    quantile,
)


def offer(code, seats, enrolled):
    return dict(codigo=code, capacidade=seats, matriculas=enrolled)


class StatisticsTests(unittest.TestCase):
    def test_distribution_has_known_hand_calculated_values(self):
        result = distribution_statistics([0, 1, 2, 3])
        self.assertEqual((result['q1'], result['median'], result['q3']), (.75, 1.5, 2.25))
        self.assertEqual(result['variance'], 1.25)
        self.assertEqual(result['iqr'], 1.5)
        self.assertEqual(result['mad'], 1)
        self.assertEqual(result['outliersLow'], 0)
        self.assertEqual(result['outliersHigh'], 0)

    def test_concentration_has_known_hand_calculated_values(self):
        result = concentration_statistics([offer('A0001', 10, 1), offer('A0002', 10, 3)])
        self.assertEqual(result['gini'], .25)
        self.assertEqual(result['hhi'], .625)
        self.assertEqual(result['effectiveDisciplines'], 1.6)
        self.assertEqual(result['top20Share'], .75)

    def test_linear_relationship_preserves_coefficient_and_fit(self):
        result = association_statistics([offer('A0001', 10, 1), offer('A0002', 20, 4), offer('A0003', 30, 9)])
        self.assertAlmostEqual(result['slope'], .01)
        self.assertAlmostEqual(result['intercept'], 0)
        self.assertAlmostEqual(result['pearson'], 1)
        self.assertAlmostEqual(result['spearman'], 1)
        self.assertAlmostEqual(result['rSquared'], 1)

    def test_empty_and_zero_total_values_remain_undefined(self):
        self.assertEqual(distribution_statistics([])['n'], 0)
        self.assertIsNone(distribution_statistics([])['mean'])
        self.assertIsNone(quantile([], .5))
        result = concentration_statistics([offer('A0001', 10, 0)])
        self.assertEqual(result['disciplines'], 1)
        self.assertIsNone(result['gini'])
        self.assertIsNone(result['hhi'])
        self.assertIsNone(association_statistics([])['pearson'])

    def test_constant_non_binary_occupancy_does_not_invent_variance(self):
        rows = [offer('MC0001', capacity, capacity // 10) for capacity in (10, 20, 30)]
        result = distribution_statistics([r['matriculas'] / r['capacidade'] for r in rows])
        self.assertEqual(result['mean'], .1)
        self.assertEqual(result['variance'], 0)
        self.assertEqual(result['standardDeviation'], 0)
        self.assertIsNone(result['skewness'])
        self.assertIsNone(result['excessKurtosis'])
        self.assertIsNone(association_statistics(rows)['pearson'])
        self.assertIsNone(association_statistics(rows)['rSquared'])


if __name__ == '__main__':
    unittest.main()

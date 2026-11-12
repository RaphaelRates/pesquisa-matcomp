"""Verifica a integração dos recortes, diferenças e identidade da fonte."""

import json
from pathlib import Path
import tempfile
import unittest

from services.dashboard.payload import dashboard_data


def offer(period, enrolled, status):
    return dict(periodo=period, codigo='MC0001', disciplina='Cálculo I', turma='01',
                docentes='Docente', tipo='REGULAR', modalidade='Presencial', situacao=status,
                horario='SEG 08:00-10:00', local='Sala', matriculas=enrolled, capacidade=10)


class DashboardPeriodsTests(unittest.TestCase):
    def test_source_changes_only_when_the_file_changes_and_metrics_follow(self):
        root = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(dir=root) as directory:
            self.assertTrue(Path(directory).resolve().is_relative_to(root))
            source = Path(directory) / 'turmas.json'
            rows = [offer('2026.1', 5, 'CONSOLIDADA'), offer('2026.2', 7, 'ABERTA')]
            source.write_text(json.dumps(rows), encoding='utf-8')
            first, again = dashboard_data(source), dashboard_data(source)
            self.assertEqual(first['source']['sha256'], again['source']['sha256'])
            self.assertEqual(len(first['source']['sha256']), 64)
            rows[1]['matriculas'] = 8
            source.write_text(json.dumps(rows), encoding='utf-8')
            changed = dashboard_data(source)
            self.assertNotEqual(first['source']['sha256'], changed['source']['sha256'])
            delta = next(row for row in changed['plotComparisons']['ufca-capacidade-matriculas']['rows']
                         if row['metric'] == 'Matrículas')
            self.assertEqual((delta['before'], delta['after'], delta['delta']), (5, 8, 3))
            current = next(p for p in changed['views']['current']['paineis'] if p['id'] == 'evolucao')
            historical = next(p for p in changed['views']['historical']['paineis'] if p['id'] == 'evolucao')
            self.assertEqual(current['summary']['selected']['m'], 8)
            self.assertEqual(historical['summary']['selected']['m'], 5)
            json.dumps(changed, allow_nan=False)

    def test_missing_reference_has_no_artificial_zero_differences(self):
        root = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(dir=root) as directory:
            self.assertTrue(Path(directory).resolve().is_relative_to(root))
            source = Path(directory) / 'turmas.json'
            source.write_text(json.dumps([offer('2026.2', 7, 'ABERTA')]), encoding='utf-8')
            data = dashboard_data(source)
            self.assertIsNone(data['views']['baselinePeriod'])
            for comparison in data['plotComparisons'].values():
                self.assertNotIn('baselinePlot', comparison)
                self.assertTrue(all(row['delta'] is None for row in comparison['rows']))


if __name__ == '__main__':
    unittest.main()

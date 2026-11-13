"""Verifica a integração dos recortes, diferenças e identidade da fonte."""

import json
from pathlib import Path
import tempfile
import unittest

from services.dashboard.interactive import DashboardSnapshots
from services.dashboard.payload import dashboard_data


def offer(period, enrolled, status):
    return dict(periodo=period, codigo='MC0001', disciplina='Cálculo I', turma='01',
                docentes='Docente', tipo='REGULAR', modalidade='Presencial', situacao=status,
                horario='SEG 08:00-10:00', local='Sala', matriculas=enrolled, capacidade=10)


class DashboardPeriodsTests(unittest.TestCase):
    def test_new_semester_files_extend_course_totals_and_move_open_offer(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            directory = Path(temporary)

            def write(period, *rows):
                path = directory / f'{period}.json'
                path.write_text(json.dumps(rows), encoding='utf-8')
                return path

            write('2026.1', offer('2026.1', 4, 'CONSOLIDADA'))
            write('2026.2', offer('2026.2', 6, 'ABERTA'))
            snapshots = DashboardSnapshots(directory)
            first = snapshots.reload()
            self.assertEqual(first.page('mc', 'accumulated')['scope']['periods'], ['2026.1', '2026.2'])

            write('2018.2', offer('2018.2', 2, 'CONSOLIDADA'))
            extra = offer('2027.1', 9, 'ABERTA') | {'codigo': 'ES0001'}
            new_file = write('2027.1', extra)
            updated = snapshots.reload()
            self.assertNotEqual(updated.revision, first.revision)
            self.assertIsNone(snapshots.get(first.revision))
            math = updated.page('mc', 'accumulated')
            self.assertEqual(math['scope']['periods'], ['2018.2', '2026.1', '2026.2'])
            years = math['periodBreakdown']['years']
            self.assertEqual([(year['year'], year['periods']) for year in years],
                             [('2018', ['2018.2']), ('2026', ['2026.1', '2026.2'])])
            self.assertEqual(years[-1]['summary']['rate'], 10 / 20)
            self.assertEqual(math['summary']['selected']['n'], 3)
            self.assertEqual(updated.page('es', 'current')['scope']['periods'], ['2027.1'])
            cct = updated.page('cct', 'accumulated')
            self.assertEqual(cct['currentPeriod'], '2027.1')
            self.assertEqual(cct['source']['currentRows'], 1)
            self.assertEqual(cct['quality']['inScopeRows'], cct['summary']['selected']['n'])
            chart = updated.charts('cct', 'accumulated', 'evolucao')['sections'][0]['plots'][0]
            self.assertEqual(chart['rows'][-1], ['2027.1*', 10, 9])
            self.assertEqual(chart['comparison']['currentPeriod'], '2027.1')
            self.assertEqual(chart['comparison']['baselinePeriod'], '2026.1')

            write('2027.1', extra | {'situacao': 'CONSOLIDADA'})
            consolidated_snapshot = snapshots.reload()
            consolidated = consolidated_snapshot.page('es', 'historical')
            self.assertIsNone(consolidated['currentPeriod'])
            self.assertEqual(consolidated['scope']['periods'], ['2027.1'])
            latest = consolidated_snapshot.page('cct', 'latest')
            self.assertEqual(latest['scope']['periods'], ['2026.2', '2027.1'])
            self.assertEqual(latest['comparedPeriod'], '2027.1')
            self.assertEqual(latest['summary']['comparison']['rows'][2]['after'], 9)

            new_file.write_text('[{"periodo":"2027.2"}]', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, '2027.1.json'):
                snapshots.reload()
            new_file.write_text('[NaN]', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'JSON UTF-8'):
                snapshots.reload()

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

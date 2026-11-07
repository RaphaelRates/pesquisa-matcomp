"""O relatório de preparação deve contar o mesmo recorte que os gráficos."""

import unittest

from services.preprocessing import preprocess_offers
from services.period_views import build_period_views


def offer(period, status, *, code='MC0001', modality='Presencial', capacity=10):
    return dict(periodo=period, codigo=code, turma='01', disciplina='Cálculo I',
                modalidade=modality, situacao=status, capacidade=capacity,
                matriculas=3 if capacity else 0, horario='SEG 08:00-10:00')


class SourceAuditTests(unittest.TestCase):
    def test_quality_count_excludes_current_or_future_consolidated_classes(self):
        raw = [offer('2026.1', 'CONSOLIDADA'), offer('2026.2', 'ABERTA'),
               offer('2026.2', 'CONSOLIDADA', code='MC0002'),
               offer('2027.1', 'CONSOLIDADA'), offer('2025.2', 'ABERTA'),
               offer('2026.1', 'CONSOLIDADA', modality='A Distância'),
               offer('2026.1', 'CONSOLIDADA', code='MC0003', capacity=0)]
        rows, report = preprocess_offers(raw)
        self.assertEqual(report['inScopeRows'], 2)
        self.assertEqual(report['outOfScopeRows'], 3)
        self.assertEqual(report['excludedRows'], 2)
        views = build_period_views(rows)
        displayed = sum(next(p for p in views[key]['paineis'] if p['id'] == 'evolucao')
                        ['summary']['selected']['n'] for key in ['historical', 'current'])
        self.assertEqual(report['inScopeRows'], displayed)

    def test_duplicate_provenance_does_not_double_count_but_conflict_is_preserved(self):
        original = offer('2026.1', 'CONSOLIDADA')
        duplicate = dict(original, origem='outra cópia', linha=99)
        conflict = dict(original, matriculas=4)
        rows, report = preprocess_offers([original, duplicate, conflict])
        self.assertEqual(len(rows), 2)
        self.assertEqual(report['duplicateRows'], 1)
        self.assertEqual(report['conflictGroups'], 1)
        self.assertEqual(report['inScopeRows'], 2)


if __name__ == '__main__':
    unittest.main()

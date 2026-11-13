"""O relatório de preparação deve contar o mesmo recorte que os gráficos."""

import unittest

from services.data.preprocessing import preprocess_offers
from services.dashboard.periods import build_period_views
from services.data.consistency import find_consistency_issues


def offer(period, status, *, code='MC0001', modality='Presencial', capacity=10):
    return dict(periodo=period, codigo=code, turma='01', disciplina='Cálculo I',
                modalidade=modality, situacao=status, capacidade=capacity,
                matriculas=3 if capacity else 0, horario='SEG 08:00-10:00')


class PreprocessingTests(unittest.TestCase):
    def joint(self, **changes):
        return dict(offer('2023.2', 'CONSOLIDADA'), docentes='Docente (32h)',
                    local='Sala A24-S', horario='TER 10:00-12:00\nQUI 10:00-12:00\n(27/11/2023 - 13/04/2024)') | changes

    def test_joint_candidates_are_excluded_without_changing_source(self):
        first = self.joint(codigo='CC0017', disciplina='Algoritmos em Grafos', matriculas=36, capacidade=60)
        second = self.joint(codigo='MC0016', disciplina='Algoritmos em Grafos', matriculas=3, capacidade=50)
        rows, report = preprocess_offers([first, second])
        self.assertEqual(rows, [])
        self.assertEqual((first['matriculas'],first['capacidade'],second['matriculas'],second['capacidade']), (36,60,3,50))
        self.assertEqual(report['excludedRows'],2)
        self.assertEqual(report['inScopeRows'],0)
        self.assertEqual(report['duplicateRows'], 0)
        self.assertEqual(report['consistency']['candidateGroups'], 1)
        self.assertEqual(report['consistency']['findings'][0]['kind'], 'possible_joint_class')

    def test_same_days_but_different_hours_are_not_duplicates(self):
        rows = [self.joint(codigo='CC0001'), self.joint(codigo='CC0051', horario='TER 16:00-18:00\nQUI 16:00-18:00\n(27/11/2023 - 13/04/2024)')]
        self.assertEqual(find_consistency_issues(rows)['findings'], [])

    def test_disjoint_dates_and_missing_metadata_do_not_invent_matches(self):
        self.assertEqual(find_consistency_issues([self.joint(), self.joint(codigo='CC0017', horario='TER 10:00-12:00\nQUI 10:00-12:00\n(14/04/2024 - 20/04/2024)')])['findings'], [])
        self.assertEqual(find_consistency_issues([
            self.joint(docentes='', local=''), self.joint(codigo='CC0017', docentes='', local='')
        ])['findings'], [])

    def test_room_alias_is_explicitly_inferred(self):
        report = find_consistency_issues([self.joint(local='SALA K 101'), self.joint(codigo='EM0028',local='Bloco K 101')])
        self.assertEqual(report['candidateGroups'], 1)
        self.assertTrue(report['findings'][0]['locationAlias'])

    def test_partial_teacher_overlap_is_separate_from_joint_candidates(self):
        rows = [self.joint(), self.joint(codigo='CC0017', horario='TER 11:00-13:00\n(27/11/2023 - 13/04/2024)',local='Sala B')]
        result = find_consistency_issues(rows)
        self.assertEqual(result['candidateGroups'], 0)
        self.assertEqual(result['overlappingPairs'], 1)

    def test_room_conflict_excludes_both_offers_with_different_teachers(self):
        first = self.joint(codigo='CC0017')
        second = self.joint(codigo='MC0016', docentes='Outro docente (32h)', local='A24S',
                            horario='TER 11:00-13:00\n(27/11/2023 - 13/04/2024)')
        rows, report = preprocess_offers([first, second])
        self.assertEqual(rows, [])
        self.assertEqual(report['inScopeRows'], 0)
        self.assertEqual(report['consistency']['roomOverlappingPairs'], 1)
        finding, = report['consistency']['findings']
        self.assertEqual(finding['kind'], 'room_schedule_overlap')
        self.assertEqual(finding['room'], 'A24S')
        self.assertEqual(finding['overlappingSlots'], [('TER', 660, 720)])

    def test_room_conflict_requires_a_room_and_a_matching_class_date(self):
        first = self.joint(docentes='Primeiro docente (32h)')
        second = self.joint(codigo='CC0017', docentes='Outro docente (32h)')
        for changes in [
            {'local': 'Bloco A'},
            {'local': 'Sala A24-S e sala B01'},
            {'horario': 'TER 10:00-12:00\n(27/11/2023 - 27/11/2023)'},
            {'horario': 'TER 12:00-14:00\n(27/11/2023 - 13/04/2024)'},
            {'situacao': 'INTERROMPIDA'},
        ]:
            with self.subTest(changes=changes):
                self.assertEqual(find_consistency_issues([first, second | changes])['findings'], [])

    def test_distinct_sections_of_the_same_discipline_can_conflict_without_teacher_metadata(self):
        first = self.joint(turma='01', docentes='')
        second = self.joint(turma='02', docentes='')
        result = find_consistency_issues([first, second])
        self.assertEqual(result['roomOverlappingPairs'], 1)
        self.assertEqual(result['recordIndices'], [0, 1])
        self.assertEqual(find_consistency_issues([first, dict(first)])['findings'], [])

    def test_quality_count_includes_eligible_classes_from_all_semesters(self):
        raw = [offer('2026.1', 'CONSOLIDADA'), offer('2026.2', 'ABERTA'),
               offer('2026.2', 'CONSOLIDADA', code='MC0002'),
               offer('2027.1', 'CONSOLIDADA'), offer('2025.2', 'ABERTA'),
               offer('2026.1', 'CONSOLIDADA', modality='A Distância'),
               offer('2026.1', 'CONSOLIDADA', code='MC0003', capacity=0)]
        rows, report = preprocess_offers(raw)
        self.assertEqual(report['inScopeRows'], 5)
        self.assertEqual(report['outOfScopeRows'], 0)
        self.assertEqual(report['excludedRows'], 2)
        views = build_period_views(rows)
        displayed = next(p for p in views['accumulated']['paineis'] if p['id'] == 'evolucao')['summary']['selected']['n']
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

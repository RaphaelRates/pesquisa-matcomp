"""Os cinco cursos usam o mesmo conjunto de análises sem duplicar o CCT."""

from copy import deepcopy
import unittest

from services.analytics.metrics import sources
from services.domain.courses import COURSES, curriculum
from services.dashboard.periods import build_period_views
from services.analytics.comparison import attach_comparisons


def offer(code, enrolled=7, period='2026.2', status='ABERTA'):
    return dict(codigo=code, disciplina=f'Disciplina {code}', periodo=period, capacidade=10,
                matriculas=enrolled, situacao=status, modalidade='Presencial', turma='01', horario='SEG 08:00-10:00')


class AllCoursesTests(unittest.TestCase):
    def test_every_course_has_same_sections_unique_ids_and_own_disciplines(self):
        rows = [offer(code) for code in ('MC0001', 'CC0001', 'ECI0079', 'EM0004', 'ES0001')]
        original = deepcopy(rows)
        views = build_period_views(rows)
        self.assertEqual(rows, original)
        for scope in ('historical', 'current', 'baseline', 'accumulated'):
            view = views[scope]
            panels = [p for p in view['paineis'] if p.get('courseKey')]
            self.assertEqual([p['courseKey'] for p in panels], [c['key'] for c in COURSES])
            for p in panels:
                self.assertEqual(len([g for s in p['sections'] for g in s['plots']]), 45)
                self.assertEqual(len(p['sections']), 8)
                self.assertIn('statisticalSummary', p)
            ids = [g['id'] for p in view['paineis'] for s in p['sections'] for g in s['plots']]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertNotIn('car', view['disciplines'])
            for config in COURSES:
                allowed = set.union(*curriculum(sources, config))
                self.assertEqual([d['code'] for d in view['disciplines'][config['key']]], sorted(r['codigo'] for r in rows if r['codigo'] in allowed))
        attach_comparisons(views['current'], views['baseline'], views['baselinePeriod'])
        for panel in views['current']['paineis']:
            if panel.get('courseKey'):
                self.assertIn('comparison', panel['summary'])
                self.assertTrue(all('comparison' in p for s in panel['sections'] for p in s['plots']))

    def test_shared_car_classes_are_counted_once_in_cct(self):
        view = build_period_views([offer('CAR0010')])['accumulated']
        cct = next(p for p in view['paineis'] if p['id'] == 'evolucao')
        self.assertEqual(cct['summary']['selected']['n'], 1)
        shared = 0
        for p in view['paineis']:
            if p.get('courseKey'):
                config = next(c for c in COURSES if c['key'] == p['courseKey'])
                expected = int('CAR0010' in set.union(*curriculum(sources, config)))
                shared += expected
                self.assertEqual(p['summary']['selected']['n'], expected)
                self.assertEqual([d['code'] for d in view['disciplines'][p['courseKey']]], ['CAR0010'] if expected else [])
        self.assertGreater(shared, 1)

    def test_computing_keeps_legacy_only_codes_and_current_classification(self):
        config = next(c for c in COURSES if c['key'] == 'cc')
        required, optional = curriculum(sources, config)
        self.assertIn('CC0058', optional)
        self.assertIn('CC0044', required)
        self.assertNotIn('CC0044', optional)
        view = build_period_views([offer('CC0058'), offer('CC0044')])['accumulated']
        cc = next(p for p in view['paineis'] if p.get('courseKey') == 'cc')
        self.assertEqual(cc['summary']['selected']['n'], 2)


if __name__ == '__main__':
    unittest.main()

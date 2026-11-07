"""Regressões da reconferência independente dos gráficos gerais."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from services.audit_general import audit_general
from services.period_views import build_period_views
from services.preprocessing import preprocess_offers


def offer(code, period, capacity, enrolled, status='CONSOLIDADA'):
    return dict(codigo=code, disciplina=f'Disciplina {code}', periodo=period, capacidade=capacity,
                matriculas=enrolled, situacao=status, modalidade='Presencial',
                turma='01', horario='SEG 08:00-10:00\nQUA 14:00-16:00')


class GeneralAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [offer(f'MC{i:04}', p, 10*i, i*4, s)
                    for p,s in [('2025.2','CONSOLIDADA'),('2026.1','CONSOLIDADA'),('2026.2','ABERTA')]
                    for i in range(1,7)]
        cls.rows += [offer('EM0105','2026.1',20,25), offer('EM0105','2026.2',30,3,'ABERTA')]
        cls.views = build_period_views(cls.rows)

    def test_recalculates_every_non_statistical_chart_in_each_scope(self):
        checks = audit_general(self.rows,self.views)
        self.assertEqual(len(checks),111 * sum(k in self.views for k in ['historical','current','baseline','accumulated']))
        self.assertTrue(all(c['passed'] for c in checks),[c for c in checks if not c['passed']])
        expected = {f'{scope}/plot/{plot["id"]}' for scope in ['historical','current','baseline','accumulated'] if scope in self.views
                    for panel in self.views[scope]['paineis'] for section in panel['sections']
                    for plot in section['plots'] if '-estat-' not in plot['id']}
        self.assertEqual({c['id'] for c in checks},expected)

    def test_detects_changed_cell_in_ordinary_chart(self):
        views = deepcopy(self.views)
        plot = next(p for panel in views['current']['paineis'] for s in panel['sections'] for p in s['plots'] if p['id']=='ufca-capacidade-matriculas')
        plot['rows'][0][1] += 1
        failed = [c['id'] for c in audit_general(self.rows,views) if not c['passed']]
        self.assertEqual(failed,['current/plot/ufca-capacidade-matriculas'])

    def test_detects_full_ranking_record_even_outside_displayed_top(self):
        views = deepcopy(self.views)
        plot = next(p for panel in views['current']['paineis'] for s in panel['sections'] for p in s['plots'] if p['id']=='ufca-ranking-obrigatorias-1-1')
        self.assertGreater(len(plot['comparisonRecords']),len(plot['rows']))
        displayed = {r[0].split(' · ')[0].split('. ',1)[1] for r in plot['rows']}
        hidden = next(r for r in plot['comparisonRecords'] if r['label'].split(' · ')[0] not in displayed)
        hidden['value'] += 1
        checks = audit_general(self.rows,views)
        self.assertFalse(next(c for c in checks if c['id']=='current/plot/ufca-ranking-obrigatorias-1-1')['passed'])

    def test_empty_current_or_reference_is_audited(self):
        for rows in [[offer('MC0001','2026.2',10,2,'ABERTA')],[offer('MC0001','2026.1',10,2)]]:
            views = build_period_views(rows)
            checks = audit_general(rows,views)
            self.assertEqual(len(checks),111 * sum(k in views for k in ['historical','current','baseline','accumulated']))
            self.assertTrue(all(c['passed'] for c in checks),[c for c in checks if not c['passed']])

    def test_included_dataset_has_no_general_chart_divergence(self):
        path=Path(__file__).resolve().parents[1]/'data'/'ufca-cct-ofertas-2023-2026.json'
        rows,_=preprocess_offers(json.loads(path.read_text(encoding='utf-8-sig')))
        views=build_period_views(rows)
        checks=audit_general(rows,views)
        self.assertEqual(len(checks),111 * sum(k in views for k in ['historical','current','baseline','accumulated']))
        self.assertTrue(all(c['passed'] for c in checks),[c for c in checks if not c['passed']])


if __name__ == '__main__':
    unittest.main()

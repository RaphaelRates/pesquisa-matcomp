"""Confere as origens dos operandos, além da aritmética das diferenças."""
from copy import deepcopy
import unittest

from services.audit_comparison_values import audit_comparison_values
from services.period_comparison import attach_comparisons, compare_plots


def make_plot(kind,columns,rows,**spec):
    return dict(id='example',columns=columns,rows=rows,spec=dict(type=kind,**spec))


def compare(before,after,period='2026.1'):
    def view(plot):
        return dict(paineis=[dict(id='p',sections=[dict(plots=[plot])])],disciplines={'cct':[]})
    views=dict(current=view(after),baseline=view(before),baselinePeriod=period)
    attach_comparisons(views['current'],views['baseline'],period)
    return views


class ComparisonValuesAuditTests(unittest.TestCase):
    def test_detects_operand_change_even_if_delta_stays_arithmetically_correct(self):
        before=make_plot('line',['Semestre','Matrículas'],[['2026.1',30]],x='Semestre',y=['Matrículas'])
        after=make_plot('line',['Semestre','Matrículas'],[['2026.2*',40]],x='Semestre',y=['Matrículas'])
        views=compare(before,after)
        self.assertTrue(all(c['passed'] for c in audit_comparison_values(views)))
        row=after['comparison']['rows'][0]
        row['before']+=5
        row['after']+=5
        row['relativeChange']=row['delta']/row['before']
        check=audit_comparison_values(views)[0]
        self.assertFalse(check['passed'])
        self.assertIn('Operandos',check['details'])

    def test_detects_wrong_percentage_unit(self):
        before=make_plot('line',['Semestre','Ocupação'],[['2026.1',.4]],x='Semestre',y=['Ocupação'],valueFormat={'style':'percent'})
        after=make_plot('line',['Semestre','Ocupação'],[['2026.2*',.6]],x='Semestre',y=['Ocupação'],valueFormat={'style':'percent'})
        views=compare(before,after)
        after['comparison']['rows'][0]['unit']='decimal'
        self.assertFalse(audit_comparison_values(views)[0]['passed'])

    def test_detects_wrong_code_pairing_independent_of_rank(self):
        before=make_plot('horizontalBar',['Disciplina','Matrículas'],[['1. MC0001 · Primeiro',30],['2. MC0002 · Segundo',10]],y='Disciplina',x='Matrículas')
        after=make_plot('horizontalBar',['Disciplina','Matrículas'],[['1. MC0002 · Segundo',40],['2. MC0001 · Primeiro',20]],y='Disciplina',x='Matrículas')
        views=compare(before,after)
        self.assertTrue(audit_comparison_values(views)[0]['passed'])
        rows=after['comparison']['rows']
        rows[0]['category'],rows[1]['category']=rows[1]['category'],rows[0]['category']
        self.assertFalse(audit_comparison_values(views)[0]['passed'])

    def test_other_capacities_are_not_a_stable_comparison_category(self):
        before=make_plot('pie',['Capacidade','Turmas'],[['50 vagas',3],['Outras capacidades',4]],x='Capacidade',y='Turmas')
        after=make_plot('pie',['Capacidade','Turmas'],[['50 vagas',4],['Outras capacidades',7]],x='Capacidade',y='Turmas')
        views=compare(before,after)
        self.assertEqual([r['category'] for r in after['comparison']['rows']],['50 vagas'])
        self.assertTrue(audit_comparison_values(views)[0]['passed'])
        self.assertIn('omitido',after['comparison']['note'])

    def test_distinct_close_numeric_thresholds_are_not_paired(self):
        before=make_plot('line',['Ocupação','Recorte selecionado'],[[.50000001,.4]],x='Ocupação',y=['Recorte selecionado'],numericX=True,xValueFormat={'style':'percent'},valueFormat={'style':'percent'})
        after=make_plot('line',['Ocupação','Recorte selecionado'],[[.50000002,.6]],x='Ocupação',y=['Recorte selecionado'],numericX=True,xValueFormat={'style':'percent'},valueFormat={'style':'percent'})
        views=compare(before,after)
        rows=after['comparison']['rows']
        self.assertEqual(len(rows),2)
        self.assertTrue(all(r['delta'] is None for r in rows))
        self.assertTrue(audit_comparison_values(views)[0]['passed'])

    def test_missing_reference_does_not_pair_empty_placeholder(self):
        before=make_plot('bar',['Semestre','Turmas'],[],x='Semestre',y=['Turmas'])
        after=make_plot('bar',['Semestre','Turmas'],[['2026.2*',3]],x='Semestre',y=['Turmas'])
        views=compare(before,after,None)
        self.assertTrue(audit_comparison_values(views)[0]['passed'])
        self.assertIsNone(after['comparison']['rows'][0]['before'])


if __name__=='__main__':
    unittest.main()

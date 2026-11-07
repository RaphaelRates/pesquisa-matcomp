"""Reconcilia operandos de cada comparação com seus gráficos de origem.

As tabelas comparadas já foram conferidas contra as turmas. Esta segunda etapa
refaz somente o pareamento por dimensão e série, sem utilizar os extratores da
implementação de comparação do painel.
"""
from decimal import Decimal
from math import isclose, isfinite
import re


METRICS = {
    'm': 'Matrículas', 'c': 'Vagas ofertadas', 'n': 'Turmas', 'rate': 'Ocupação',
    'free': 'Vagas não preenchidas', 'extra': 'Matrículas acima da capacidade',
    'full': 'Turmas com ocupação de 100% ou mais', 'low': 'Turmas abaixo de 25% de ocupação',
    'periods': 'Semestres com oferta', 'recurring_full': 'Semestres com ocupação de 100% ou mais',
    'recurring_low': 'Semestres abaixo de 25% de ocupação',
}
SEMESTER_METRICS = [
    ('n','Turmas','number'),('c','Vagas ofertadas','number'),('m','Matrículas','number'),
    ('rate','Ocupação geral','percent'),('free','Vagas não preenchidas','number'),
    ('extra','Matrículas acima da capacidade','number'),('full','Turmas com ocupação de 100% ou mais','number'),
    ('over','Turmas acima da capacidade','number'),('low','Turmas abaixo de 25% de ocupação','number'),
    ('zero','Turmas sem matrículas','number'),
]
STAT_METRICS = [
    ('occupancy','mean','Ocupação média por turma','percent'),
    ('occupancy','median','Mediana de ocupação','percent'),
    ('occupancy','q1','Primeiro quartil da ocupação','percent'),
    ('occupancy','q3','Terceiro quartil da ocupação','percent'),
    ('occupancy','standardDeviation','Desvio-padrão da ocupação','percent'),
    ('occupancy','iqr','Intervalo interquartil da ocupação','percent'),
    ('occupancy','mad','Desvio absoluto mediano da ocupação','percent'),
    ('occupancy','coefficientVariation','Coeficiente de variação','decimal'),
    ('occupancy','skewness','Assimetria','decimal'),('occupancy','excessKurtosis','Excesso de curtose','decimal'),
    ('occupancy','outliersLow','Turmas abaixo da cerca de Tukey','number'),
    ('occupancy','outliersHigh','Turmas acima da cerca de Tukey','number'),
    ('concentration','disciplines','Disciplinas ofertadas','number'),
    ('concentration','gini','Gini das matrículas','decimal'),('concentration','hhi','HHI','decimal'),
    ('concentration','effectiveDisciplines','Disciplinas efetivas (1/HHI)','decimal'),
    ('concentration','normalizedEntropy','Entropia normalizada','decimal'),
    ('concentration','top20Share','Parcela das 20% maiores disciplinas','percent'),
    ('association','pearson','Pearson: capacidade e ocupação','decimal'),
    ('association','spearman','Spearman: capacidade e ocupação','decimal'),
    ('association','rSquared','R² do ajuste descritivo','decimal'),
]


def _equal(a,b):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a,(float,int)) and isinstance(b,(float,int)):
        return isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
    return a==b


def _numeric(value):
    return float(value) if isinstance(value,(int,float)) and not isinstance(value,bool) and isfinite(value) else None


def _metric(name):
    if name in ['Consolidadas','Consolidadas até 2026.1','Abertas em 2026.2','Abertas 2026.2','Recorte selecionado']:
        return 'Recorte selecionado'
    return METRICS.get(name,name)


def _dimension(value, percent=False):
    if isinstance(value,(float,int)):
        number=Decimal(str(value))*(100 if percent else 1)
        result=format(number,'f')
        if '.' in result:
            result=result.rstrip('0').rstrip('.')
        return result+('%' if percent else '')
    text=str(value).strip()
    # Rank, nome da disciplina e contagem de turmas não identificam categorias.
    text=re.sub(r'^\d+\.\s+','',text)
    text=re.sub(r'\s*\(\d+ turmas?\)$','',text)
    text=re.sub(r'\s*·\s*\d+ turmas?$','',text)
    if re.fullmatch(r'\d{4}\.[12]\*?',text):
        return 'Total do semestre'
    code=re.match(r'^([A-Z]+\d+)\b',text)
    return code.group(1) if code else text


def _unit(plot,metric):
    declared=plot.get('spec',{}).get('valueFormat',{}).get('style')
    if plot.get('rankingPercent') or declared=='percent':
        return 'percent'
    decimal_names={'Gini','HHI','Pearson','Spearman','Número efetivo (HHI)','Número efetivo de disciplinas','R²'}
    if declared=='decimal' or metric in decimal_names:
        return 'decimal'
    return 'number'


def _source_values(plot):
    result={}
    if not plot:
        return result
    spec=plot.get('spec',{})
    def insert(category,metric,value):
        if category.casefold() in {'outras','outras capacidades'}:
            return
        key=(category,metric)
        if key in result:
            raise ValueError(f'Chave de categoria/métrica repetida: {key}')
        result[key]=(_numeric(value),_unit(plot,metric))
    if 'comparisonRecords' in plot:
        metric=_metric(plot.get('comparisonMetric',plot.get('title','Resultado')))
        for row in plot['comparisonRecords']:
            insert(_dimension(row['label']),metric,row['value'])
        return result
    kind=plot.get('formato',spec.get('type'))
    if kind=='ranking':
        for row,value in zip(plot.get('rows',[]),plot.get('rankingValues',[]),strict=True):
            insert(_dimension(row[0]),'Resultado',value)
        return result
    if kind=='heatmap':
        dimensions=[spec['x'],spec['y']]
        metric_names=[spec['value']]
    else:
        dimensions=[spec['y'] if kind=='horizontalBar' else spec['x']]
        metric_names=spec['x'] if kind=='horizontalBar' else spec['y']
        metric_names=[metric_names] if isinstance(metric_names,str) else metric_names
    for values in plot.get('rows',[]):
        record=dict(zip(plot['columns'],values,strict=True))
        dimensions_used=[d for d in dimensions if d.casefold() not in {'semestre','periodo','período'}]
        parts=[_dimension(record[d],spec.get('xValueFormat',{}).get('style')=='percent') for d in dimensions_used]
        category=' · '.join(parts) if parts else 'Total do semestre'
        for name in metric_names:
            insert(category,_metric(name),record.get(name))
    return result


def _verify(comparison,before,after):
    if not isinstance(comparison,dict):
        return False,'Comparação ausente'
    expected=set(before)|set(after)
    actual=comparison.get('rows',[])
    labels=[(r.get('category'),r.get('metric')) for r in actual]
    if len(labels)!=len(set(labels)) or set(labels)!=expected:
        return False,'Categorias/métricas ausentes, extras, duplicadas ou pareadas incorretamente'
    for row in actual:
        key=(row['category'],row['metric'])
        old,old_unit=before.get(key,(None,None))
        new,new_unit=after.get(key,(None,None))
        if not _equal(row.get('before'),old) or not _equal(row.get('after'),new):
            return False,f'Operandos diferentes da origem: {key}'
        if row.get('unit')!=(new_unit or old_unit):
            return False,f'Unidade incorreta: {key}'
    return True,f'{len(expected)} pares de categoria/métrica reconciliados com suas origens'


def _plots(view):
    return [p for panel in view.get('paineis',[]) for section in panel['sections'] for p in section['plots']]+[
        p for d in view.get('disciplines',{}).get('cct',[]) for p in d['plots']]


def audit_comparison_values(views):
    """Valida o pareamento e os operandos de todos gráficos, resumos e índices."""
    current=views['current']
    baseline=views.get('baseline',{}) if views.get('baselinePeriod') else {}
    old_plots={p['id']:p for p in _plots(baseline)}
    checks=[]
    for plot in _plots(current):
        identifier='comparison-values/'+plot['id']
        try:
            old=old_plots.get(plot['id'])
            kind=plot.get('formato',plot.get('spec',{}).get('type'))
            non_paired=kind in {'scatter','bubble','statisticalScatter'} or plot.get('catalogKey')=='cadeira-por-turma'
            a,b=({}, {}) if non_paired else (_source_values(old),_source_values(plot))
            passed,detail=_verify(plot.get('comparison'),a,b)
            checks.append(dict(id=identifier,passed=passed,details=detail))
        except (KeyError,TypeError,ValueError) as error:
            checks.append(dict(id=identifier,passed=False,details=str(error)))
    old_panels={p['id']:p for p in baseline.get('paineis',[])}
    old_disciplines={d['code']:d for d in baseline.get('disciplines',{}).get('cct',[])}
    entities=[(p['id'],p,old_panels.get(p['id'],{})) for p in current.get('paineis',[])]+[
        ('cadeira-'+d['code'],d,old_disciplines.get(d['code'],{})) for d in current.get('disciplines',{}).get('cct',[])]
    for identifier,new,old in entities:
        if 'summary' in new:
            before=old.get('summary',{}).get('selected',{})
            after=new['summary'].get('selected',{})
            a={('Total do semestre',name):(_numeric(before.get(key)),unit) for key,name,unit in SEMESTER_METRICS}
            b={('Total do semestre',name):(_numeric(after.get(key)),unit) for key,name,unit in SEMESTER_METRICS}
            passed,detail=_verify(new['summary'].get('comparison'),a,b)
            checks.append(dict(id='comparison-values/summary/'+identifier,passed=passed,details=detail))
        if 'statisticalSummary' in new:
            before=old.get('statisticalSummary',{})
            after=new['statisticalSummary']
            a={('Estatísticas do semestre',name):(_numeric(before.get(section,{}).get(key)),unit) for section,key,name,unit in STAT_METRICS}
            b={('Estatísticas do semestre',name):(_numeric(after.get(section,{}).get(key)),unit) for section,key,name,unit in STAT_METRICS}
            passed,detail=_verify(after.get('comparison'),a,b)
            checks.append(dict(id='comparison-values/statistics/'+identifier,passed=passed,details=detail))
    return checks

"""Confere os resultados por uma segunda implementação das contas.

Este módulo não usa metrics, distribution, shift ou hourly_slots do painel
para calcular os valores esperados. As listas curriculares são definições do
recorte, compartilhadas com a aplicação, e não resultados de cálculo.
"""

from collections import defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
import re
from statistics import median

from services.calc_metrics import sources


def same(actual, expected):
    if expected is None or actual is None:
        return actual is expected
    if isinstance(expected, (int, float, Fraction)) and not isinstance(expected, bool):
        return isinstance(actual, (int, float, Fraction)) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-10)
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(key in actual and same(actual[key], value) for key, value in expected.items())
    if isinstance(expected, (list, tuple)):
        return isinstance(actual, (list, tuple)) and len(actual) == len(expected) and all(same(a, b) for a, b in zip(actual, expected))
    return actual == expected


def check(key, actual, expected):
    passed = same(actual, expected)
    return dict(id=key, passed=passed, details='Conferido por recálculo independente.' if passed else
                f'Esperado: {str(expected)[:500]}; recebido: {str(actual)[:500]}')


def selected_rows(offers, view):
    scope = view['scope']
    def included(row):
        if scope['status'] == 'MISTA':
            return '2023.1' <= row['periodo'] <= '2026.2' and (
                row['situacao'] == 'CONSOLIDADA' and row['periodo'] < '2026.2' or
                row['situacao'] == 'ABERTA' and row['periodo'] == '2026.2')
        return row['situacao'] == scope['status']
    return [r for r in offers if r['modalidade'] == 'Presencial' and r['capacidade'] > 0
            and included(r) and r['periodo'] in scope['periods']]


def totals(rows):
    enrolled = sum(r['matriculas'] for r in rows)
    seats = sum(r['capacidade'] for r in rows)
    return dict(n=len(rows), c=seats, m=enrolled, rate=float(Fraction(enrolled, seats)) if seats else None,
                full=sum(r['matriculas'] >= r['capacidade'] for r in rows),
                over=sum(r['matriculas'] > r['capacidade'] for r in rows),
                low=sum(4 * r['matriculas'] < r['capacidade'] for r in rows),
                zero=sum(r['matriculas'] == 0 for r in rows),
                free=sum(max(0, r['capacidade'] - r['matriculas']) for r in rows),
                extra=sum(max(0, r['matriculas'] - r['capacidade']) for r in rows))


def schedule(row):
    slots = set()
    shifts = set()
    for day, sh, sm, eh, em in re.findall(r'\b(SEG|TER|QUA|QUI|SEX|SAB|SÁB|DOM) (\d{2}):(\d{2})-(\d{2}):(\d{2})', row['horario']):
        day = day.replace('Á', 'A')
        start, end = int(sh) * 60 + int(sm), int(eh) * 60 + int(em)
        for hour in range(7, 22):
            if max(start, hour * 60) < min(end, (hour + 1) * 60):
                slots.add((day, hour))
        for label, lo, hi in [('Manhã', 0, 720), ('Tarde', 720, 1080), ('Noite', 1080, 1440)]:
            if max(start, lo) < min(end, hi):
                shifts.add(label)
    return slots, next(iter(shifts)) if len(shifts) == 1 else 'Misto' if shifts else 'Sem horário'


def audit_disciplines(offers, views):
    checks = []
    mc_codes = set((sources['Matemática Computacional'][1] + ' ' + sources['Matemática Computacional'][2]).split())
    known = {r['codigo'] for r in offers if r['modalidade'] == 'Presencial' and r['capacidade'] > 0
             and (r['situacao'] == 'CONSOLIDADA' and r['periodo'] < '2026.2' or r['situacao'] == 'ABERTA' and r['periodo'] == '2026.2')}
    for scope_id in (key for key in ('historical', 'current', 'baseline', 'accumulated') if key in views):
        view = views[scope_id]
        rows = selected_rows(offers, view)
        by_code = defaultdict(list)
        for row in rows:
            by_code[row['codigo']].append(row)
        panels = {panel['id']: panel for panel in view['paineis']}
        for panel_id, sample in [('evolucao', rows), ('matematica-computacional', [r for r in rows if r['codigo'] in mc_codes])]:
            checks.append(check(f'{scope_id}/summary/{panel_id}', panels[panel_id]['summary']['selected'], totals(sample)))
        checks.append(check(f'{scope_id}/discipline-codes', [d['code'] for d in view['disciplines']['cct']], sorted(known)))
        checks.append(check(f'{scope_id}/mc-codes', [d['code'] for d in view['disciplines']['mc']], sorted(known & mc_codes)))
        for discipline in view['disciplines']['cct']:
            code = discipline['code']
            sample = sorted(by_code[code], key=lambda r: (r['periodo'], r['turma'], r['horario']))
            prefix = f'{scope_id}/discipline/{code}'
            checks.append(check(f'{prefix}/summary', discipline['summary']['selected'], totals(sample)))
            expected = {}
            for key in ('oferta', 'ocupacao', 'saldo', 'turmas'):
                values = []
                for period in view['scope']['periods']:
                    subset = [r for r in sample if r['periodo'] == period]
                    m = totals(subset)
                    series = {'oferta': [m['c'], m['m']],
                              'ocupacao': [m['rate'], float(median([Fraction(r['matriculas'], r['capacidade']) for r in subset])) if subset else None],
                              'saldo': [m['free'], m['extra']], 'turmas': [m['n']]}[key]
                    values.append([period + ('*' if period == '2026.2' else ''), *(series if subset else [None] * len(series))])
                expected[key] = values if sample else []
            expected['por-turma'] = [[f"{r['periodo']}{'*' if r['situacao'] == 'ABERTA' else ''} · {r['turma']} · {index}",
                                       float(Fraction(r['matriculas'], r['capacidade']))] for index, r in enumerate(sample, 1)]
            labels = ['Abaixo de 25%', '25% a menos de 50%', '50% a menos de 100%', '100% ou mais']
            counts = [0, 0, 0, 0]
            by_shift = defaultdict(list)
            slots = []
            for row in sample:
                fraction = Fraction(row['matriculas'], row['capacidade'])
                counts[0 if fraction < Fraction(1, 4) else 1 if fraction < Fraction(1, 2) else 2 if fraction < 1 else 3] += 1
                assigned, shift = schedule(row)
                by_shift[shift].append(row)
                slots.append(assigned)
            expected['faixas'] = [[label, count] for label, count in zip(labels, counts)] if sample else []
            expected['turnos'] = [[label, totals(subset)['rate']] for label, subset in sorted(by_shift.items())]
            days = [('SEG', 'Seg'), ('TER', 'Ter'), ('QUA', 'Qua'), ('QUI', 'Qui'), ('SEX', 'Sex'), ('SAB', 'Sáb'), ('DOM', 'Dom')]
            expected['horarios'] = [[label, f'{hour:02d}h', sum((day, hour) in assigned for assigned in slots)]
                                    for day, label in days for hour in range(7, 22)] if sample else []
            for plot in discipline['plots']:
                key = plot['catalogKey'].removeprefix('cadeira-')
                checks.append(check(f"{scope_id}/plot/{plot['id']}", plot['rows'], expected.get(key, 'Gráfico sem conferência definida')))
    return checks


def audit_comparisons(views):
    """Confere toda diferença publicada e sua unidade a partir dos operandos."""
    checks = []
    objects = []
    current = views['current']
    for panel in current['paineis']:
        for key in ('summary', 'statisticalSummary'):
            if panel.get(key, {}).get('comparison'):
                objects.append((panel['id'] + '/' + key, panel[key]['comparison']))
        objects.extend((p['id'], p['comparison']) for section in panel['sections'] for p in section['plots'])
    for discipline in current['disciplines']['cct']:
        objects.append((discipline['code'] + '/summary', discipline['summary']['comparison']))
        objects.extend((p['id'], p['comparison']) for p in discipline['plots'])
    for key, comparison in objects:
        valid = True
        for row in comparison['rows']:
            before, after = row['before'], row['after']
            delta = after - before if before is not None and after is not None else None
            relative = delta / before if delta is not None and before > 0 and row['unit'] != 'decimal' else None
            valid = valid and same(row['delta'], delta) and same(row['relativeChange'], relative)
            valid = valid and (views['baselinePeriod'] is not None or before is None)
        checks.append(dict(id=f'comparison/{key}', passed=valid,
                           details=f"{len(comparison['rows'])} diferenças conferidas; ausência de base e base zero preservadas."))
    return checks


def audit_calculations(offers, views):
    from services.audit_general import audit_general
    from services.audit_statistics import audit_statistics
    from services.audit_comparison_values import audit_comparison_values
    checks = [*audit_disciplines(offers, views), *audit_general(offers, views),
              *audit_statistics(offers, views), *audit_comparisons(views), *audit_comparison_values(views)]
    failures = [entry for entry in checks if not entry['passed']]
    charts = [entry for entry in checks if '/plot/' in entry['id'] and entry['id'].count('/') == 2]
    # Cobertura é uma verificação própria: nenhum gráfico gerado fica sem teste.
    expected_ids = {f"{scope}/plot/{p['id']}" for scope in ('historical', 'current', 'baseline', 'accumulated') if scope in views
                    for p in [*[p for panel in views[scope]['paineis'] for section in panel['sections'] for p in section['plots']],
                              *[p for d in views[scope]['disciplines']['cct'] for p in d['plots']]]}
    covered_ids = {entry['id'] for entry in charts}
    coverage = check('coverage/all-plots', sorted(covered_ids), sorted(expected_ids))
    checks.append(coverage)
    if not coverage['passed']:
        failures.append(coverage)
    totals_by_scope = {scope: {area: totals([r for r in selected_rows(offers, views[scope])
                                            if area == 'cct' or r['codigo'] in set((sources['Matemática Computacional'][1] + ' ' + sources['Matemática Computacional'][2]).split())])
                              for area in ('cct', 'mc')} for scope in ('historical', 'current', 'baseline', 'accumulated') if scope in views}
    periods = sorted({period for scope in ('historical', 'current') for period in views[scope]['scope']['periods']})
    mc_codes = set((sources['Matemática Computacional'][1] + ' ' + sources['Matemática Computacional'][2]).split())
    included = [*selected_rows(offers, views['historical']), *selected_rows(offers, views['current'])]
    by_semester = [dict(period=period, status='ABERTA' if period == '2026.2' else 'CONSOLIDADA',
                        cct=totals([r for r in included if r['periodo'] == period]),
                        mc=totals([r for r in included if r['periodo'] == period and r['codigo'] in mc_codes]))
                   for period in periods]
    return dict(passed=not failures, checkedAt=datetime.now(timezone.utc).isoformat(),
                checksRun=len(checks), checkedCharts=len(covered_ids & expected_ids), expectedCharts=len(expected_ids),
                failures=failures, totals=totals_by_scope, bySemester=by_semester, checks=checks,
                method='Recálculo independente a partir das turmas tratadas; ocupação geral = soma(matrículas) / soma(capacidade).')


def main():
    import argparse
    import hashlib
    from pathlib import Path
    from services.period_views import build_period_views
    from services.period_comparison import attach_comparisons
    from services.preprocessing import preprocess_offers

    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dados', type=Path, default=root / 'data' / 'ufca-cct-ofertas-2023-2026.json')
    parser.add_argument('--saida', type=Path, default=root / 'data' / 'recalculo-graficos.json')
    args = parser.parse_args()
    if args.saida.resolve() == args.dados.resolve():
        parser.error('O relatório deve ser salvo em um arquivo diferente da base.')
    raw_bytes = args.dados.read_bytes()
    offers, quality = preprocess_offers(json.loads(raw_bytes.decode('utf-8-sig')))
    views = build_period_views(offers)
    attach_comparisons(views['current'], views['baseline'], views['baselinePeriod'])
    report = audit_calculations(offers, views)
    report.update(source=dict(name=args.dados.name, sha256=hashlib.sha256(raw_bytes).hexdigest()), quality=quality)
    args.saida.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(f"{report['checkedCharts']}/{report['expectedCharts']} gráficos conferidos; {report['checksRun']} verificações; {len(report['failures'])} divergências.")
    if not report['passed']:
        for failure in report['failures'][:12]:
            print(failure['id'], failure['details'][:300])
        raise SystemExit(1)


if __name__ == '__main__':
    main()

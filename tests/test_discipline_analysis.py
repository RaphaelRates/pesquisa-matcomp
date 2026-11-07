"""Casos de borda que afetam a interpretação da oferta e do catálogo."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from services.chart_catalog import apply_catalog
from services.discipline_metrics import discipline_analyses


def offer(code, period, seats, enrolled, status='CONSOLIDADA'):
    return dict(codigo=code, disciplina='Disciplina', periodo=period, capacidade=seats,
                matriculas=enrolled, situacao=status, modalidade='Presencial',
                turma='01', horario='SEG 08:00-10:00')


class DisciplineAnalysisTests(unittest.TestCase):
    def test_missing_offer_is_distinct_from_empty_class_and_open_offer(self):
        bundle = discipline_analyses([
            offer('MC0001', '2023.1', 10, 0),
            offer('CC0001', '2023.2', 20, 10),
            offer('MC0001', '2026.2', 10, 12, 'ABERTA'),
            offer('MC0001', '2024.1', 0, 0),
        ])
        d = next(d for d in bundle['cct'] if d['code'] == 'MC0001')
        occupancy = next(p for p in d['plots'] if p['catalogKey'] == 'cadeira-ocupacao')
        self.assertEqual(occupancy['rows'], [['2023.1', 0, 0], ['2023.2', None, None], ['2026.2*', 1.2, 1.2]])
        self.assertEqual(d['summary']['historico']['m'], 0)
        self.assertEqual(d['summary']['abertas']['m'], 12)
        self.assertEqual(d['summary']['abertas']['extra'], 2)
        self.assertEqual([r['code'] for r in bundle['mc']], ['MC0001'])

    def test_shortage_and_excess_do_not_cancel_between_classes(self):
        d = discipline_analyses([offer('MC0001', '2023.1', 10, 5), offer('MC0001', '2023.1', 10, 15)])['cct'][0]
        self.assertEqual(d['summary']['historico']['rate'], 1)
        self.assertEqual(d['summary']['historico']['free'], 5)
        self.assertEqual(d['summary']['historico']['extra'], 5)
        schedule = next(p for p in d['plots'] if p['catalogKey'] == 'cadeira-horarios')
        self.assertEqual(sum(r[-1] for r in schedule['rows']), 4)

    def test_catalog_edits_apply_to_both_areas_and_reject_incompatible_type(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            assert Path(directory).resolve().is_relative_to(Path(__file__).resolve().parent)
            catalog = Path(directory) / 'catalog.json'
            entry = dict(nome='Oferta personalizada', descricao='Descrição editada', tipo='line')
            def save():
                catalog.write_text(json.dumps({'graficos': {'cadeira-oferta': entry}}), encoding='utf-8')
            save()
            with patch('services.chart_catalog.CATALOG_PATH', catalog):
                bundle = discipline_analyses([offer('MC0001', '2023.1', 10, 5)])
                apply_catalog([], bundle)
                for area in ['cct', 'mc']:
                    plot = bundle[area][0]['plots'][0]
                    self.assertEqual(plot['title'], entry['nome'])
                    self.assertEqual(plot['description'], entry['descricao'])
                    self.assertEqual(plot['spec']['type'], 'line')
                entry['tipo'] = 'heatmap'
                save()
                with self.assertRaises(ValueError):
                    apply_catalog([], bundle)


if __name__ == '__main__':
    unittest.main()

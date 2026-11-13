"""Contrato HTTP do servidor, sem iniciar portas de rede nos testes."""

from io import BytesIO
import json
from threading import BoundedSemaphore
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app import DashboardHandler, FrontendHandler
from services.config import DEFAULT_DATA
from services.dashboard.interactive import DashboardSnapshots


class HttpTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshots = DashboardSnapshots(DEFAULT_DATA)

    def request(self, path, handler_class=DashboardHandler):
        handler = object.__new__(handler_class)
        handler.path = path
        handler.server = SimpleNamespace(data_path=DEFAULT_DATA, snapshots=self.snapshots, api_port=8001,
                                         calculations=BoundedSemaphore(1))
        result = []
        handler.respond = lambda *args, **kwargs: result.append(args)
        handler.log_error = lambda *args: None
        handler.do_GET()
        return result[0]

    def exchange(self, method='GET', path='/api/v1/painel/cct', headers=('Host: localhost:8001',)):
        handler = object.__new__(DashboardHandler)
        handler.rfile = BytesIO('\r\n'.join([f'{method} {path} HTTP/1.1', *headers, '', '']).encode())
        handler.wfile = BytesIO()
        handler.log_message = lambda *args: None
        handler.log_error = lambda *args: None
        handler.server = SimpleNamespace(data_path=DEFAULT_DATA, snapshots=self.snapshots,
                                         server_port=8001, frontend_origin='http://localhost:8000',
                                         calculations=BoundedSemaphore(1))
        handler.handle_one_request()
        return handler.wfile.getvalue().split(b'\r\n\r\n', 1)

    def test_rejects_invalid_authority_origin_and_methods(self):
        host = 'Host: localhost:8001'
        cases = [
            ('GET', ('Host: outro.example:8001',), b'400', 'invalid_host'),
            ('GET', (host, host), b'400', 'invalid_host'),
            ('GET', (host, 'Origin: https://outro.example'), b'403', 'origin_not_allowed'),
            ('GET', (host, 'Sec-Fetch-Site: cross-site'), b'403', 'origin_not_allowed'),
            ('POST', (host,), b'405', 'method_not_allowed'),
            ('GET', (host, 'Content-Length: 1'), b'400', 'unexpected_body'),
        ]
        with patch.object(self.snapshots, 'reload') as reload:
            for method, headers, status, code in cases:
                with self.subTest(method=method, headers=headers):
                    head, body = self.exchange(method=method, headers=headers)
                    self.assertEqual(head.split()[1], status)
                    self.assertEqual(json.loads(body)['error']['code'], code)
                    self.assertIn(b'X-Content-Type-Options: nosniff', head)
            reload.assert_not_called()

    def test_exact_cors_origin_and_gzip_opt_out(self):
        headers = ('Host: localhost:8001', 'Origin: http://localhost:8000', 'Accept-Encoding: gzip;q=0')
        head, body = self.exchange(headers=headers)
        self.assertEqual(head.split()[1], b'200')
        self.assertIn(b'Access-Control-Allow-Origin: http://localhost:8000', head)
        self.assertNotIn(b'Content-Encoding:', head)
        self.assertIn('sections', json.loads(body)['data'])

    def test_limits_query_fields_before_calculating(self):
        with patch.object(self.snapshots, 'reload') as reload:
            head, body = self.exchange(path='/api/v1/painel/cct?recorte=current&a=1&b=2')
            self.assertEqual(head.split()[1], b'400')
            self.assertEqual(json.loads(body)['error']['code'], 'invalid_query')
            reload.assert_not_called()

    def test_api_returns_dashboard_json(self):
        with patch('app.dashboard_data', return_value={'views': {}, 'source': {}}) as calculate:
            status, body, media_type = self.request('/api/painel')
            self.assertEqual(status, 200)
            self.assertEqual(media_type, 'application/json')
            self.assertEqual(json.loads(body), {'views': {}, 'source': {}})
            calculate.assert_called_once_with(DEFAULT_DATA)

    def test_unknown_route_does_not_calculate_or_export_data(self):
        with patch('app.dashboard_data') as calculate:
            self.assertEqual(self.request('/rota-inexistente')[0], 404)
            calculate.assert_not_called()

    def test_invalid_data_has_recoverable_error_response(self):
        with patch('app.dashboard_data', side_effect=ValueError('Dados inválidos')):
            status, body, media_type = self.request('/api/painel')
            self.assertEqual(status, 503)
            self.assertEqual(media_type, 'application/json')
            self.assertIn('erro', json.loads(body))

    def test_course_page_and_deferred_section(self):
        status, html, _ = self.request('/cursos/mc?recorte=historical', FrontendHandler)
        self.assertEqual(status, 200)
        config = html.split('id="dashboard-config">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(config)['group'], 'mc')
        self.assertEqual(json.loads(config)['apiPort'], 8001)
        self.assertIn('<h1>Matemática Computacional</h1>', html)
        self.assertEqual(self.request('/cursos/mc')[0], 404)
        self.assertEqual(self.request('/api/v1/painel/mc', FrontendHandler)[0], 404)
        status, body, _ = self.request('/api/v1/painel/mc?recorte=historical')
        self.assertEqual(status, 200)
        page = json.loads(body)
        self.assertEqual(page['data']['scope']['id'], 'historical')
        self.assertEqual(page['data']['summary']['selected']['n'], 205)
        self.assertEqual(page['data']['sections'][0]['id'], 'evolucao')
        revision = page['meta']['revision']
        status, body, _ = self.request(f'/api/v1/painel/mc/secoes/evolucao?recorte=historical&revisao={revision}')
        self.assertEqual(status, 200)
        plot = json.loads(body)['data']['sections'][0]['plots'][0]
        self.assertEqual(plot['rows'][0], ['2019.1', 210, 159])
        self.assertEqual(plot['comparison']['baselinePeriod'], '2026.1')

    def test_api_v1_error_envelope(self):
        for route, expected, code in [
            ('/api/v1/painel/cct?recorte=invalido', 400, 'invalid_query'),
            ('/api/v1/painel/mc/secoes/comparacao', 404, 'not_found'),
            ('/api/v1/painel/cct/secoes/evolucao', 400, 'invalid_query'),
            ('/api/v1/painel/cct/secoes/evolucao?revisao=desatualizada', 409, 'revision_changed'),
        ]:
            with self.subTest(route=route):
                status, body, media_type = self.request(route)
                self.assertEqual((status, media_type), (expected, 'application/json'))
                payload = json.loads(body)
                self.assertIsNone(payload['data'])
                self.assertEqual(payload['meta'], {'version': 1, 'revision': None})
                self.assertEqual(payload['error']['code'], code)

    def test_software_uses_only_its_offered_semesters(self):
        route = '/api/v1/painel/es'
        status, body, _ = self.request(route)
        self.assertEqual(status, 200)
        page = json.loads(body)
        periods = ['2025.1', '2025.2', '2026.1', '2026.2']
        self.assertEqual(page['data']['scope']['periods'], periods)
        self.assertEqual(page['data']['scope']['label'], 'Acumulado · 2025.1 a 2026.2')
        self.assertEqual(page['data']['summary']['selected']['n'], 31)
        scopes = {scope['id']: scope for scope in page['data']['scopes']}
        self.assertEqual(scopes['historical']['periods'], periods[:-1])
        self.assertEqual(scopes['current']['periods'], periods[-1:])
        shown = periods[:-1] + ['2026.2*']
        revision = page['meta']['revision']
        for endpoint, plot_id in [
            ('secoes/evolucao', 'group-es-ufca-capacidade-matriculas'),
            ('secoes/curso', 'software-comparacao'),
            ('disciplinas/ES0001', 'cadeira-ES0001-oferta'),
        ]:
            status, body, _ = self.request(f'{route}/{endpoint}?revisao={revision}')
            self.assertEqual(status, 200)
            plot = next(p for section in json.loads(body)['data']['sections']
                        for p in section['plots'] if p['id'] == plot_id)
            self.assertEqual([row[0] for row in plot['rows']], periods if endpoint.startswith('disciplinas/') else shown)
            self.assertNotIn('2019.1', plot['scopeNote'])
        _, body, _ = self.request('/api/v1/painel/cct')
        self.assertEqual(json.loads(body)['data']['scope']['periods'][0], '2019.1')

    def test_semester_pair_changes_page_charts_and_discipline(self):
        route = '/api/v1/painel/mc'
        status, body, _ = self.request(route + '?recorte=latest')
        latest = json.loads(body)['data']
        self.assertEqual(status, 200)
        self.assertEqual(latest['scope']['periods'], ['2026.1', '2026.2'])
        self.assertEqual(latest['summary']['comparison']['baselinePeriod'], '2026.1')

        query = '?recorte=compare&referencia=2019.1&semestre=2020.2'
        status, body, _ = self.request(route + query)
        self.assertEqual(status, 200)
        page = json.loads(body)
        data = page['data']
        self.assertEqual(data['scope']['periods'], ['2019.1', '2020.2'])
        self.assertEqual([row['year'] for row in data['periodBreakdown']['years']], ['2019', '2020'])
        self.assertEqual([row['period'] for row in data['periodBreakdown']['semesters']], ['2019.1', '2020.2'])
        self.assertIn('2026.2', [row['period'] for row in data['availableSemesters']])
        self.assertIn('2019.1 e 2020.2', data['scope']['note'])
        self.assertEqual((data['baselinePeriod'], data['comparedPeriod']), ('2019.1', '2020.2'))
        self.assertEqual(data['summary']['selected']['m'], 159 + 162)
        for endpoint in ('secoes/evolucao', 'disciplinas/MC0001'):
            status, body, _ = self.request(f"{route}/{endpoint}{query}&revisao={page['meta']['revision']}")
            self.assertEqual(status, 200)
            chart = json.loads(body)['data']['sections'][0]['plots'][0]
            self.assertEqual([row[0] for row in chart['rows']], ['2019.1', '2020.2'])
            self.assertEqual(chart['comparison']['currentPeriod'], '2020.2')
            self.assertEqual(chart['comparison']['baselinePeriod'], '2019.1')
        self.assertEqual(self.request(route + '?recorte=compare&referencia=2019.1&semestre=2019.1')[0], 400)
        self.assertEqual(self.request(route.replace('/mc', '/es') + query)[0], 400)

    def test_required_heatmap_lists_curriculum_semesters_and_versions(self):
        for course, prefix, count in [('cc', 'computacao', 2), ('em', 'materiais', 2), ('eci', 'civil', 3),
                                      ('mc', 'matcomp', 2), ('es', 'software', 1)]:
            route = f'/api/v1/painel/{course}'
            status, body, _ = self.request(route + '?recorte=latest')
            self.assertEqual(status, 200)
            page = json.loads(body)
            status, body, _ = self.request(f"{route}/secoes/curso?recorte=latest&revisao={page['meta']['revision']}")
            self.assertEqual(status, 200)
            data = json.loads(body)['data']
            plot = next(plot for section in data['sections'] for plot in section['plots']
                        if plot['id'] == prefix + '-historico-obrigatorias')
            variants = plot['curriculumAlternatives']
            self.assertEqual(len(plot['curriculumOptions']), count)
            self.assertEqual(set(variants), {item['id'] for item in plot['curriculumOptions'][1:]})
            for chart in (plot, *variants.values()):
                spec = chart['spec']
                groups = [int(spec['yGroups'][label].split('º')[0]) for label in spec['yOrder']]
                self.assertEqual(groups, sorted(groups))
                self.assertEqual([period.rstrip('*') for period in spec['xOrder']], ['2026.1', '2026.2'])
                self.assertEqual(chart['comparison']['baselinePeriod'], '2026.1')
            if course == 'cc':
                self.assertTrue(any(label.startswith('CC0003') for label in variants['cc001']['spec']['yOrder']))
                self.assertFalse(any(label.startswith('CC0003') for label in plot['spec']['yOrder']))
            if course == 'mc':
                legacy = variants['mc001']['spec']
                label = next(label for label in legacy['yOrder'] if label.startswith('MC0018'))
                self.assertEqual(legacy['yGroups'][label], '4º semestre curricular')
                label = next(label for label in plot['spec']['yOrder'] if label.startswith('MC0018'))
                self.assertEqual(plot['spec']['yGroups'][label], '2º semestre curricular')

    def test_course_notice_filters_cases_and_preserves_cross_course_evidence(self):
        reports = {}
        for group in ('cct', 'es', 'cc', 'eci'):
            status, body, _ = self.request(f'/api/v1/painel/{group}')
            self.assertEqual(status, 200)
            data = json.loads(body)['data']
            reports[group] = data.get('consistency', data['quality']['consistency'])
        self.assertEqual(reports['cct']['excludedRecords'], 131)
        self.assertEqual(len(reports['cct']['findings']), 68)
        self.assertEqual(reports['es']['findings'], [])
        self.assertEqual(reports['es']['excludedRecords'], 0)
        self.assertEqual(len(reports['cc']['findings']), 20)
        self.assertEqual(len(reports['eci']['findings']), 47)
        cross_course = next(finding for finding in reports['cc']['findings']
                            if any(row['codigo'] == 'ECI0097' for row in finding['records']))
        self.assertEqual({row['codigo'] for row in cross_course['records']}, {'ECI0097', 'CC0026'})

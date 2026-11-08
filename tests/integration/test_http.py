"""Contrato HTTP do servidor, sem iniciar portas de rede nos testes."""

import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app import DashboardHandler
from services.config import DEFAULT_DATA


class HttpTests(TestCase):
    def request(self, path):
        handler = object.__new__(DashboardHandler)
        handler.path = path
        handler.server = SimpleNamespace(data_path=DEFAULT_DATA)
        result = []
        handler.respond = lambda *args: result.append(args)
        handler.log_error = lambda *args: None
        handler.serve_dashboard()
        return result[0]

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

"""Serve o painel da UFCA a partir do JSON de turmas."""

import argparse
from base64 import b64encode
from contextlib import ExitStack
import gzip
from hashlib import sha256
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
from pathlib import Path
import re
from threading import BoundedSemaphore, Thread
from urllib.parse import parse_qs

from services.config import CATALOG_PATH, CURRENT_PERIOD, DEFAULT_DATA, PROJECT_ROOT, TITLE
from services.dashboard.groups import GROUPS
from services.dashboard.interactive import DashboardSnapshots, DisciplineNotFound, FAMILIES, GROUP_BY_ID, SCOPES
from services.presentation.export import TOOLTIPS
from services.dashboard.payload import dashboard_data


FRONTEND = PROJECT_ROOT / 'frontend'
HTTP_LOGGER = logging.getLogger('painel.http')
LOG_CONTROL = re.compile(r'[\x00-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]')
GZIP_ENCODING = re.compile(r'\s*gzip\s*(?:;\s*q\s*=\s*(?:1(?:\.0{0,3})?|0\.(?=\d*[1-9])\d{1,3}))?\s*')
TOOLTIP_HASH = b64encode(sha256(TOOLTIPS.encode('utf-8')).digest()).decode('ascii')
MAX_QUERY_FIELDS = 2
MAX_TARGET_LENGTH = 2048
CHUNK_PATH = re.compile(r'/chunks/[A-Za-z0-9_-]+\.js')
ASSETS = {
    "/painel.js": (FRONTEND / "dist" / "painel.js", "text/javascript"),
    "/painel.css": (FRONTEND / "dist" / "painel.css", "text/css"),
    "/vendor/chart.umd.min.js": (FRONTEND / "vendor" / "chart.umd.min.js", "text/javascript"),
}


def dashboard_shell(group_id, api_port):
    group = GROUP_BY_ID[group_id]
    config = json.dumps(dict(group=group_id, title=group['title'], siteTitle=TITLE, courses=GROUPS,
                             currentPeriod=CURRENT_PERIOD, apiPort=api_port),
                        ensure_ascii=False).replace('<', '\\u003c')
    assets_ready = all(ASSETS[url][0].is_file() for url in ('/painel.js', '/painel.css'))
    assets = ('<link rel="stylesheet" href="/painel.css"><script type="module" src="/painel.js"></script>'
              if assets_ready else '')
    status = ('Carregando indicadores…' if assets_ready else
              'Compile o frontend com <code>npm --prefix frontend ci</code> e <code>npm --prefix frontend run build</code>.')
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{group['title']} | {TITLE}</title>{assets}</head>
<body><div id="dashboard"><main><h1>{group['title']}</h1><p role="status">{status}</p>
<noscript><p>Ative o JavaScript para carregar os gráficos do painel.</p></noscript>
</main></div>
<script type="application/json" id="dashboard-config">{config}</script>
<div id="chart-tooltip" aria-hidden="true" hidden></div>
<script>{TOOLTIPS}</script>
</body></html>
"""


class LocalServer(ThreadingHTTPServer):
    def __init__(self, address, handler):
        self.connections = BoundedSemaphore(32)
        super().__init__(address, handler)

    def process_request(self, request, address):
        if not self.connections.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.connections.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.connections.release()


class DashboardServer(LocalServer):
    def __init__(self, address, data_path):
        self.data_path = data_path
        self.snapshots = DashboardSnapshots(data_path)
        self.calculations = BoundedSemaphore(8)
        super().__init__(address, DashboardHandler)


class LocalHandler(BaseHTTPRequestHandler):
    timeout = 10
    server_version = 'Painel'
    sys_version = ''

    def parse_request(self):
        if not super().parse_request():
            return False
        port = self.server.server_port
        hosts = {f'localhost:{port}', f'127.0.0.1:{port}'}
        if port == 80:
            hosts.update(('localhost', '127.0.0.1'))
        authorities = self.headers.get_all('Host', [])
        if len(authorities) != 1 or authorities[0].lower() not in hosts:
            self.reject(HTTPStatus.BAD_REQUEST, 'invalid_host', 'Use o endereço local e a porta do serviço.')
            return False
        if self.command not in ('GET', 'HEAD'):
            self.reject(HTTPStatus.METHOD_NOT_ALLOWED, 'method_not_allowed', 'Use GET ou HEAD.',
                        headers={'Allow': 'GET, HEAD'})
            return False
        if (self.headers.get_all('Transfer-Encoding') is not None
                or self.headers.get_all('Content-Length', []) not in ([], ['0'])):
            self.reject(HTTPStatus.BAD_REQUEST, 'unexpected_body', 'Esta consulta não aceita corpo.')
            return False
        if not self.path.startswith('/') or len(self.path) > MAX_TARGET_LENGTH:
            self.reject(HTTPStatus.BAD_REQUEST, 'invalid_target', 'Endereço da requisição inválido.')
            return False
        return True

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, message, *args):
        HTTP_LOGGER.info('%s', LOG_CONTROL.sub('?', message % args))

    def log_error(self, message, *args):
        HTTP_LOGGER.error('%s', LOG_CONTROL.sub('?', message % args))

    def reject(self, status, code, message, *, headers=None):
        self.respond(status, message, 'text/plain', headers=headers)

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        super().end_headers()

    def respond(self, status, content, media_type, *, headers=None):
        body = content.encode("utf-8")
        encodings = self.headers.get('Accept-Encoding', '').lower().split(',')
        compressed = len(body) >= 512 and any(GZIP_ENCODING.fullmatch(item) for item in encodings)
        if compressed:
            body = gzip.compress(body, compresslevel=5)
        self.send_response(status)
        self.send_header("Content-Type", f"{media_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if compressed:
            self.send_header('Content-Encoding', 'gzip')
        self.send_header('Vary', 'Accept-Encoding')
        self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)


class FrontendHandler(LocalHandler):
    def end_headers(self):
        port = self.server.api_port
        self.send_header('Content-Security-Policy',
                         f"default-src 'none'; script-src 'self' 'sha256-{TOOLTIP_HASH}'; "
                         f"style-src 'self'; connect-src http://localhost:{port} http://127.0.0.1:{port}; "
                         "base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        super().end_headers()

    def do_GET(self):
        route = self.path.partition("?")[0]
        group = route.removeprefix('/cursos/').rstrip('/')
        if route == "/" or (route.startswith('/cursos/') and group in GROUP_BY_ID and group != 'cct'):
            html = dashboard_shell('cct' if route == '/' else group, self.server.api_port)
            self.respond(HTTPStatus.OK, html, "text/html")
            return
        asset = ASSETS.get(route)
        if CHUNK_PATH.fullmatch(route):
            asset = (FRONTEND / 'dist' / 'chunks' / route.rsplit('/', 1)[1], 'text/javascript')
        if asset:
            path, media_type = asset
            try:
                content = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                self.respond(HTTPStatus.NOT_FOUND, "Recurso não encontrado.", "text/plain")
                return
            self.respond(HTTPStatus.OK, content, media_type)
            return
        self.respond(HTTPStatus.NOT_FOUND, "Página não encontrada.", "text/plain")


class DashboardHandler(LocalHandler):
    def parse_request(self):
        if not super().parse_request():
            return False
        origins = self.headers.get_all('Origin', [])
        if (origins and origins != [self.server.frontend_origin]) or self.headers.get('Sec-Fetch-Site') == 'cross-site':
            self.reject(HTTPStatus.FORBIDDEN, 'origin_not_allowed', 'Origem não autorizada para a API local.')
            return False
        return True

    def do_GET(self):
        if not self.server.calculations.acquire(blocking=False):
            self.reject(HTTPStatus.SERVICE_UNAVAILABLE, 'server_busy', 'Servidor ocupado. Tente novamente.',
                        headers={'Retry-After': '1'})
            return
        try:
            self.serve_dashboard()
        finally:
            self.server.calculations.release()

    def reject(self, status, code, message, *, headers=None):
        self.api_response(status, error=dict(code=code, message=message), headers=headers)

    def end_headers(self):
        headers = getattr(self, 'headers', None)
        if headers and headers.get_all('Origin', []) == [self.server.frontend_origin]:
            self.send_header('Access-Control-Allow-Origin', self.server.frontend_origin)
        self.send_header('Vary', 'Origin')
        super().end_headers()

    def serve_dashboard(self):
        route, _, query = self.path.partition("?")
        if route.startswith('/api/v1/'):
            try:
                params = parse_qs(query, keep_blank_values=True, strict_parsing=True,
                                  errors='strict', max_num_fields=MAX_QUERY_FIELDS)
            except ValueError:
                self.reject(HTTPStatus.BAD_REQUEST, 'invalid_query', 'Parâmetros de consulta inválidos.')
                return
            self.serve_api(route, params)
            return
        if route == "/api/graficos":
            try:
                content = CATALOG_PATH.read_text(encoding="utf-8")
            except FileNotFoundError:
                self.respond(HTTPStatus.NOT_FOUND, "Recurso não encontrado.", "text/plain")
                return
            self.respond(HTTPStatus.OK, content, "application/json")
            return
        if route != "/api/painel":
            self.respond(HTTPStatus.NOT_FOUND, "Página não encontrada.", "text/plain")
            return
        try:
            payload = json.dumps(dashboard_data(self.server.data_path), ensure_ascii=False, allow_nan=False)
        except (OSError, ValueError, TypeError, KeyError) as error:
            self.log_error("Falha ao carregar os dados: %s", error)
            self.respond(HTTPStatus.SERVICE_UNAVAILABLE,
                         json.dumps({"erro": "O painel não conseguiu carregar os dados de turmas."},
                                    ensure_ascii=False), "application/json")
            return
        self.respond(HTTPStatus.OK, payload, "application/json")

    def api_response(self, status, *, data=None, revision=None, error=None, headers=None):
        payload = dict(data=data, meta=dict(version=1, revision=revision), error=error)
        content = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        self.respond(status, content, 'application/json', headers=headers)

    def serve_api(self, route, query):
        parts = route.removeprefix('/api/v1/').strip('/').split('/')
        if parts == ['graficos']:
            if query:
                self.api_response(HTTPStatus.BAD_REQUEST, error=dict(
                    code='invalid_query', message='O catálogo não aceita parâmetros de consulta.'))
                return
            try:
                catalog = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
                self.api_response(HTTPStatus.OK, data=catalog)
            except (OSError, ValueError) as error:
                self.log_error('Falha ao ler o catálogo: %s', error)
                self.api_response(HTTPStatus.SERVICE_UNAVAILABLE, error=dict(
                    code='data_unavailable', message='O catálogo de gráficos está indisponível.'))
            return
        if len(parts) not in (2, 4) or parts[0] != 'painel' or parts[1] not in GROUP_BY_ID:
            self.api_response(HTTPStatus.NOT_FOUND, error=dict(code='not_found', message='Recurso não encontrado.'))
            return
        group = parts[1]
        page = len(parts) == 2
        if not page:
            resource, identifier = parts[2:]
            if not (resource == 'disciplinas' or resource == 'secoes' and identifier in FAMILIES
                    and (identifier != 'curso' or group != 'cct')
                    and (identifier != 'comparacao' or group == 'cct')):
                self.api_response(HTTPStatus.NOT_FOUND, error=dict(code='not_found', message='Recurso não encontrado.'))
                return
        allowed_params = {'recorte'} if page else {'recorte', 'revisao'}
        scope = query.get('recorte', ['accumulated'])[0]
        revision = query.get('revisao', [''])[0]
        if (query.keys() - allowed_params or any(len(values) != 1 for values in query.values())
                or scope not in SCOPES or (not page and not revision)):
            self.api_response(HTTPStatus.BAD_REQUEST, error=dict(
                code='invalid_query', message='Informe um recorte válido e, ao consultar gráficos, a revisão da página.'))
            return
        try:
            snapshot = self.server.snapshots.reload() if page else self.server.snapshots.get(revision)
            if snapshot is None:
                self.api_response(HTTPStatus.CONFLICT, error=dict(
                    code='revision_changed', message='A base mudou. Atualize os dados para consultar esta revisão.'))
                return
            if page:
                data = snapshot.page(group, scope)
            elif resource == 'secoes':
                data = snapshot.charts(group, scope, family=identifier)
            else:
                data = snapshot.charts(group, scope, code=identifier)
            self.api_response(HTTPStatus.OK, data=data, revision=snapshot.revision)
        except DisciplineNotFound:
            self.api_response(HTTPStatus.NOT_FOUND, error=dict(
                code='not_found', message='Disciplina não encontrada neste grupo.'))
        except (OSError, ValueError, TypeError, KeyError) as error:
            self.api_data_error(error)

    def api_data_error(self, error):
        self.log_error('Falha ao carregar os dados: %s', error)
        self.api_response(HTTPStatus.SERVICE_UNAVAILABLE, error=dict(
            code='data_unavailable', message='O painel não conseguiu carregar os dados de turmas.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=os.getenv("DATA_PATH") or DEFAULT_DATA,
                        help="Pasta de semestres ou arquivo JSON de turmas (DATA_PATH).")
    parser.add_argument("--porta", type=int, default=os.getenv("FRONTEND_PORT", "8000"),
                        help="Porta do frontend (FRONTEND_PORT, padrão: 8000).")
    parser.add_argument("--porta-api", type=int, default=os.getenv("API_PORT", "8001"),
                        help="Porta da API (API_PORT, padrão: 8001).")
    parser.add_argument("--host", default=os.getenv("HOST", "localhost"),
                        help="Endereço de escuta (HOST, padrão: localhost).")
    parser.add_argument("--log-level", type=str.upper, default=os.getenv("LOG_LEVEL", "INFO"),
                        help="Nível de log (LOG_LEVEL, padrão: INFO).")
    args = parser.parse_args()
    if not all(0 <= port <= 65535 for port in (args.porta, args.porta_api)):
        parser.error("As portas devem estar entre 0 e 65535.")
    if args.porta and args.porta == args.porta_api:
        parser.error("FRONTEND_PORT e API_PORT devem usar portas diferentes.")
    if args.log_level not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
        parser.error("LOG_LEVEL deve ser DEBUG, INFO, WARNING, ERROR ou CRITICAL.")
    logging.basicConfig(level=args.log_level, format='%(levelname)s %(message)s')

    with ExitStack() as stack:
        try:
            frontend = stack.enter_context(LocalServer((args.host, args.porta), FrontendHandler))
            api = stack.enter_context(DashboardServer((args.host, args.porta_api), args.dados.resolve()))
        except OSError as error:
            parser.error(f"Não foi possível iniciar o painel: {error}")

        frontend.api_port = api.server_port
        api.frontend_origin = ('http://localhost' if frontend.server_port == 80
                               else f'http://localhost:{frontend.server_port}')
        worker = Thread(target=api.serve_forever, daemon=True)
        worker.start()
        print(f"Frontend: http://localhost:{frontend.server_port}/", flush=True)
        print(f"API: http://localhost:{api.server_port}/api/v1/painel/cct", flush=True)
        try:
            frontend.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            api.shutdown()
            worker.join()


if __name__ == "__main__":
    main()

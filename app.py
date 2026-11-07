"""Serve o painel da UFCA a partir do JSON de turmas."""

import argparse
import gzip
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

from services.graph import DEFAULT_DATA, TITLE, TOOLTIPS, dashboard_data


SCRIPT_PATH = Path(__file__).resolve().with_name("painel.js")
ASSETS = {
    "/api/graficos": (SCRIPT_PATH.parent / "data" / "graficos.json", "application/json"),
    "/painel.js": (SCRIPT_PATH, "text/javascript"),
    "/painel.css": (SCRIPT_PATH.with_suffix(".css"), "text/css"),
    "/vendor/chart.umd.min.js": (SCRIPT_PATH.parent / "vendor" / "chart.umd.min.js", "text/javascript"),
}


def dashboard_shell():
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE}</title><link rel="stylesheet" href="/painel.css">
<script src="/vendor/chart.umd.min.js" defer></script>
<script src="/painel.js" defer></script></head>
<body><a class="skip-link" href="#painel">Ir para os gráficos</a>
<header class="hero">
<div class="site-bar"><span class="brand-mark" aria-hidden="true">∑</span>
<span>UFCA <span class="brand-divider">/</span> Centro de Ciências e Tecnologia</span>
<span class="source-tag">DADOS DE OFERTA</span></div>
<div class="hero-content"><div>
<p class="eyebrow">PAINEL ACADÊMICO</p>
<h1>Oferta de disciplinas<br>do CCT da UFCA<span>.</span></h1>
<p class="hero-description">Explore vagas, matrículas e ocupação. Do panorama do CCT aos detalhes de Matemática Computacional.</p>
<div class="hero-tags"><span>2023.1 — 2026.2</span><span id="chart-count">Carregando visualizações</span><span>Fonte · JSON de turmas</span></div>
</div><div class="hero-aside" aria-hidden="true">
<span class="aside-label">OFERTA / OCUPAÇÃO / EVOLUÇÃO</span>
<div class="hero-chart"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
<span class="aside-caption">Série histórica e turmas abertas</span>
</div></div></header>
<nav class="global-nav" id="indice" aria-label="Áreas do painel" hidden></nav>
<main id="painel" aria-busy="true">
<div class="loading-state" role="status"><span class="loading-dot"></span>Carregando os indicadores do JSON…</div>
<noscript><p>Ative o JavaScript para carregar os gráficos do painel.</p></noscript>
</main>
<footer class="site-footer"><strong>UFCA · CCT</strong><p>Dados calculados a partir dos registros de turmas presenciais.
As turmas abertas de 2026.2 são identificadas nos gráficos.</p>
<a href="#indice">↑ Voltar à navegação</a></footer>
<div id="chart-tooltip" aria-hidden="true" hidden></div>
<script>{TOOLTIPS}</script>
</body></html>
"""


class DashboardServer(ThreadingHTTPServer):
    def __init__(self, address, data_path):
        self.data_path = data_path
        super().__init__(address, DashboardHandler)


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.serve_dashboard()

    def do_HEAD(self):
        self.serve_dashboard()

    def serve_dashboard(self):
        route = self.path.partition("?")[0]
        if route == "/":
            self.respond(HTTPStatus.OK, dashboard_shell(), "text/html")
            return
        if route in ASSETS:
            path, media_type = ASSETS[route]
            self.respond(HTTPStatus.OK, path.read_text(encoding="utf-8"), media_type)
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

    def respond(self, status, content, media_type):
        body = content.encode("utf-8")
        compressed = media_type == 'application/json' and 'gzip' in self.headers.get('Accept-Encoding', '')
        if compressed:
            body = gzip.compress(body, compresslevel=5)
        self.send_response(status)
        self.send_header("Content-Type", f"{media_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if compressed:
            self.send_header('Content-Encoding', 'gzip')
        self.send_header('Vary', 'Accept-Encoding')
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=DEFAULT_DATA, help="Caminho do JSON de turmas.")
    parser.add_argument("--porta", type=int, default=8000, help="Porta local (padrão: 8000).")
    args = parser.parse_args()
    if not 0 <= args.porta <= 65535:
        parser.error("A porta deve estar entre 0 e 65535.")

    try:
        server = DashboardServer(("127.0.0.1", args.porta), args.dados.resolve())
    except OSError as error:
        parser.error(f"Não foi possível iniciar o painel: {error}")

    with server:
        print(f"Painel disponível em http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()

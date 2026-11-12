"""Caminhos e configurações compartilhados da aplicação."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = PROJECT_ROOT / 'data' / 'ufca'
CATALOG_PATH = PROJECT_ROOT / 'data' / 'graficos.json'
TITLE = 'Oferta de disciplinas do CCT da UFCA'
START_PERIOD = '2022.1'
CURRENT_PERIOD = '2026.2'

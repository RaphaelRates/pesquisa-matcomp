"""Regras de seleção usadas pelos indicadores e pelo relatório da base."""


def is_eligible(row):
    return row['modalidade'] == 'Presencial' and row['capacidade'] > 0


def split_offers(rows):
    """Separa turmas consolidadas e abertas sem limitar as datas da série."""
    eligible = [row for row in rows if is_eligible(row)]
    historical = [row for row in eligible if row['situacao'] == 'CONSOLIDADA']
    opened = [row for row in eligible if row['situacao'] == 'ABERTA']
    return historical, opened

"""Normaliza os registros de turma e descreve o tratamento aplicado à base."""

from collections import Counter, defaultdict
from decimal import Decimal
import json
import math
import re
import unicodedata
from services.data.consistency import find_consistency_issues


MAX_SAFE_INTEGER = 2**53 - 1
PERIOD_PATTERN = re.compile(r"([1-9]\d{3})\s*[./_-]\s*([12])")
CODE_PATTERN = re.compile(r"[A-Z]+\d+")
INTEGER_PATTERN = re.compile(r"[+-]?\d+(?:[.,]0+)?")
SCHEDULE_PATTERN = re.compile(r"\b(?:SEG|TER|QUA|QUI|SEX|SAB|DOM) \d{2}:\d{2}-\d{2}:\d{2}")


def normalize_text(value, field, *, required=False, multiline=False):
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValueError(f"O campo {field} deve conter texto.")
    text = unicodedata.normalize("NFC", value)
    if multiline:
        text = "\n".join(" ".join(line.split()) for line in text.splitlines()).strip()
    else:
        text = " ".join(text.split())
    if required and not text:
        raise ValueError(f"O campo {field} está ausente ou vazio.")
    return text


def folded(text):
    return "".join(char for char in unicodedata.normalize("NFD", text)
                   if not unicodedata.combining(char)).casefold()


def nonnegative_integer(value, field):
    if isinstance(value, bool):
        raise ValueError(f"O campo {field} deve conter um inteiro não negativo.")
    if isinstance(value, str):
        text = value.strip()
        if not INTEGER_PATTERN.fullmatch(text):
            raise ValueError(f"O campo {field} deve conter um inteiro não negativo.")
        value = Decimal(text.replace(",", "."))
    if not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"O campo {field} deve conter um inteiro não negativo.")
    if not math.isfinite(value) or value < 0 or value > MAX_SAFE_INTEGER or value != int(value):
        raise ValueError(f"O campo {field} deve conter um inteiro não negativo representável no navegador.")
    return int(value)


def normalize_record(row):
    if not isinstance(row, dict):
        raise ValueError("O registro deve ser um objeto de turma.")
    clean = dict(row)
    for field, value in row.items():
        if isinstance(value, str) and field != "horario":
            clean[field] = normalize_text(value, field)

    period = normalize_text(row.get("periodo"), "periodo", required=True)
    match = PERIOD_PATTERN.fullmatch(period)
    if not match:
        raise ValueError("O campo periodo deve identificar um semestre, como 2026.2.")
    clean["periodo"] = f"{match[1]}.{match[2]}"

    code = normalize_text(row.get("codigo"), "codigo", required=True)
    clean["codigo"] = "".join(code.split()).upper()
    if not CODE_PATTERN.fullmatch(clean["codigo"]):
        raise ValueError("O campo codigo deve conter letras seguidas de números.")
    clean["disciplina"] = normalize_text(row.get("disciplina"), "disciplina", required=True)
    clean["turma"] = normalize_text(row.get("turma"), "turma")
    mode = normalize_text(row.get("modalidade"), "modalidade", required=True)
    clean["modalidade"] = {
        "presencial": "Presencial",
        "ead": "A Distância",
        "a distancia": "A Distância",
        "educacao a distancia": "A Distância",
        "ensino a distancia": "A Distância",
        "remota": "Remota",
        "hibrida": "Híbrida",
    }.get(folded(mode), mode.title())
    clean["situacao"] = normalize_text(row.get("situacao"), "situacao", required=True).upper()
    clean["horario"] = normalize_text(row.get("horario"), "horario", multiline=True).upper().replace("SÁB", "SAB")
    clean["horario"] = clean["horario"].replace("–", "-").replace("—", "-")
    clean["horario"] = re.sub(r"(?<=\d{2}:\d{2})\s*-\s*(?=\d{2}:\d{2})", "-", clean["horario"])
    clean["matriculas"] = nonnegative_integer(row.get("matriculas"), "matriculas")
    clean["capacidade"] = nonnegative_integer(row.get("capacidade"), "capacidade")
    return clean


def preprocess_offers(raw):
    """Retorna os registros tratados e um relatório JSON do processamento.

    A identidade segura de uma turma exige semestre, código, turma e modalidade.
    Registros com essa identidade só são deduplicados quando o conteúdo tratado
    também coincide, exceto pelos campos de proveniência origem e linha.
    Conteúdos conflitantes são preservados e contabilizados no relatório.
    """
    if not isinstance(raw, list):
        raise ValueError("O JSON deve conter uma lista de turmas.")
    cleaned = []
    issues = Counter()
    warnings = Counter()
    examples = []
    warning_examples = []
    identities = defaultdict(set)
    duplicate_rows = 0
    normalized_rows = 0

    for index, row in enumerate(raw, 1):
        try:
            clean = normalize_record(row)
            # A comparação inclui campos adicionais que distinguem registros,
            # preservando diferenças em local, tipo ou docentes.
            signature = json.dumps({key: value for key, value in clean.items()
                                    if key not in {"origem", "linha"}},
                                   sort_keys=True, ensure_ascii=False, allow_nan=False)
        except (ValueError, TypeError, OverflowError) as error:
            reason = str(error)
            issues[reason] += 1
            if len(examples) < 5:
                examples.append({"row": index, "reason": reason})
            continue

        identity = (clean["periodo"], clean["codigo"], clean["turma"], clean["modalidade"])
        if clean["turma"]:
            if signature in identities[identity]:
                duplicate_rows += 1
                continue
            identities[identity].add(signature)

        changed = clean.keys() != row.keys() or any(
            type(value) is not type(row.get(key)) or value != row.get(key)
            for key, value in clean.items()
        )
        normalized_rows += int(changed)
        if not SCHEDULE_PATTERN.search(clean["horario"]):
            reason = "Horário ausente ou sem formato reconhecido."
            warnings[reason] += 1
            if len(warning_examples) < 5:
                warning_examples.append({"row": index, "periodo": clean["periodo"],
                                         "codigo": clean["codigo"], "reason": reason})
        cleaned.append(clean)

    consistency = find_consistency_issues(cleaned)
    suspicious = set(consistency.pop('recordIndices'))
    accepted = [row for index, row in enumerate(cleaned) if index not in suspicious]
    excluded = Counter()
    if suspicious:
        excluded['Registros sinalizados por possível oferta conjunta ou sobreposição de docente.'] = len(suspicious)
    in_scope = 0
    eligible = 0
    out_of_scope = Counter()
    for row in accepted:
        if row["modalidade"] != "Presencial":
            excluded["Modalidade diferente de Presencial."] += 1
        elif row["capacidade"] == 0:
            excluded["Capacidade cadastrada igual a zero."] += 1
        else:
            eligible += 1
            if (row["situacao"] == "CONSOLIDADA" and row["periodo"] < "2026.2") or (
                row["situacao"] == "ABERTA" and row["periodo"] == "2026.2"
            ):
                in_scope += 1
            else:
                out_of_scope["Situação ou semestre fora do recorte consolidado e aberto de 2026.2."] += 1

    conflicts = [(identity, len(signatures)) for identity, signatures in identities.items()
                 if len(signatures) > 1]
    report = {
        "inputRows": len(raw),
        "validRows": len(cleaned),
        "discardedRows": sum(issues.values()),
        "duplicateRows": duplicate_rows,
        "normalizedRows": normalized_rows,
        "conflictGroups": len(conflicts),
        "conflictingRows": sum(count for _, count in conflicts),
        "eligibleRows": eligible,
        "excludedRows": sum(excluded.values()),
        "inScopeRows": in_scope,
        "outOfScopeRows": sum(out_of_scope.values()),
        "issues": [{"reason": reason, "count": count} for reason, count in sorted(issues.items())],
        "exclusionReasons": [{"reason": reason, "count": count} for reason, count in sorted(excluded.items())],
        "outOfScopeReasons": [{"reason": reason, "count": count} for reason, count in sorted(out_of_scope.items())],
        "warnings": [{"reason": reason, "count": count} for reason, count in sorted(warnings.items())],
        "examples": examples,
        "warningExamples": warning_examples,
        "conflictExamples": [
            {"periodo": identity[0], "codigo": identity[1], "turma": identity[2], "records": count}
            for identity, count in conflicts[:5]
        ],
        "policy": "Campos textuais e contagens são normalizados antes dos cálculos. "
                  "Valores numéricos ausentes ou inválidos são descartados. "
                  "Duplicatas com identidade e conteúdo coincidentes são removidas. "
                  "Registros conflitantes são preservados para revisão.",
    }
    report['consistency'] = consistency
    return accepted, report

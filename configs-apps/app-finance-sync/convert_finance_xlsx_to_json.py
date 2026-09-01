#!/usr/bin/env python3
"""Convert a finance workbook into the JSON expected by dashboard.html.

Expected Excel layout:
- One sheet with columns: mes, receita, contas_mensais, extras, despesas, saldo, reserva, investimentos
- Optional second sheet with columns: item, total (for categorias)
- Optional third sheet with columns: item, valor (for investimentos_recentes.itens)
- Optional cell/row with the month label for investimentos_recentes.mes

If the file is not shaped like that, the script will print a helpful error and exit.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Iterable
from urllib.request import Request, urlopen

try:
    from openpyxl import load_workbook
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Dependency missing: install with `pip install -r requirements.txt`") from exc


def normalize_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return value


def parse_decimal(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace("R$", "").replace(" ", "")
    if text in ("", "-", "—"):
        return 0.0

    if "." in text and "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text and "." not in text:
        text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return 0.0


def normalize_key(value: Any) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def header_aliases() -> dict[str, set[str]]:
    return {
        "mes": {"mes", "meses", "mês"},
        "receita": {"receita", "receitas"},
        "contas_mensais": {"contas_mensais", "contas_fixas", "contasfixas", "contas_fixas", "fixas"},
        "extras": {"extras", "extra"},
        "despesas": {"despesas", "despesa", "gastos"},
        "saldo": {"saldo", "saldo_geral", "saldogerald"},
        "reserva": {"reserva", "reservas"},
        "investimentos": {"investimentos", "investimento"},
        "item": {"item", "categoria", "classe", "nome"},
        "total": {"total", "valor_total", "valor", "valor_total_mensal"},
        "valor": {"valor", "total", "total_mensal", "valor_total"},
    }


def header_index(headers: Iterable[Any], desired: Iterable[str]) -> dict[str, int]:
    normalized = [normalize_key(h) for h in headers]
    aliases = header_aliases()
    result: dict[str, int] = {}
    for target in desired:
        accepted = {normalize_key(v) for v in aliases.get(target, {target})} | {target}
        for idx, header in enumerate(normalized):
            if header in accepted:
                result[target] = idx
                break
    return result


def first_sheet_with_header(workbook, candidates: list[str]):
    for ws in workbook.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        headers = [normalize_key(v) for v in rows[0]]
        normalized_candidates = {normalize_key(c) for c in candidates}
        if any(c in headers for c in normalized_candidates):
            return ws
    return None


def load_month_rows(workbook):
    expected = [
        "mes",
        "receita",
        "contas_mensais",
        "extras",
        "despesas",
        "saldo",
        "reserva",
        "investimentos",
    ]
    ws = first_sheet_with_header(workbook, ["mes", "receita", "despesas"])
    if ws is None:
        raise ValueError(
            "Nenhuma aba com colunas de meses foi identificada. Use colunas como: "
            "mes, receita, contas_mensais, extras, despesas, saldo, reserva, investimentos."
        )

    rows = list(ws.iter_rows(values_only=True))
    headers = rows[0]
    indexes = header_index(headers, expected)

    missing = [key for key in expected if key not in indexes]
    if missing:
        raise ValueError(
            "A aba de meses está incompleta. Faltam colunas: " + ", ".join(missing)
        )

    months = []
    for row in rows[1:]:
        if not any(normalize_value(v) not in (None, "") for v in row):
            continue

        label = normalize_value(row[indexes["mes"]]) if indexes["mes"] < len(row) else ""
        if not label:
            continue

        month_data = {
            "label": str(label),
            "receita": parse_decimal(row[indexes["receita"]] if indexes["receita"] < len(row) else 0),
            "contas_mensais": parse_decimal(row[indexes["contas_mensais"]] if indexes["contas_mensais"] < len(row) else 0),
            "extras": parse_decimal(row[indexes["extras"]] if indexes["extras"] < len(row) else 0),
            "despesas": parse_decimal(row[indexes["despesas"]] if indexes["despesas"] < len(row) else 0),
            "saldo": parse_decimal(row[indexes["saldo"]] if indexes["saldo"] < len(row) else 0),
            "reserva": parse_decimal(row[indexes["reserva"]] if indexes["reserva"] < len(row) else 0),
            "investimentos": parse_decimal(row[indexes["investimentos"]] if indexes["investimentos"] < len(row) else 0),
        }
        months.append(month_data)

    if not months:
        raise ValueError("Nenhuma linha de meses foi encontrada na planilha.")

    labels = [m["label"] for m in months]
    return labels, months


def load_categories(workbook):
    candidates = ["categorias", "categoria", "contas_fixas", "contas_fixas"]
    ws = first_sheet_with_header(workbook, candidates)
    if ws is None:
        return []

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    headers = [normalize_key(v) for v in rows[0]]
    target = ["item", "total"]
    indexes = header_index(headers, target)
    if "item" not in indexes or "total" not in indexes:
        return []

    result = []
    for row in rows[1:]:
        item = row[indexes["item"]] if indexes["item"] < len(row) else ""
        total = row[indexes["total"]] if indexes["total"] < len(row) else 0
        if not item:
            continue
        result.append({"item": str(item), "total": parse_decimal(total)})
    return result


def load_investment_recent(workbook):
    ws = first_sheet_with_header(workbook, ["investimentos_recentes", "carteira", "investimento", "classe"])
    if ws is None:
        return {"mes": "", "itens": []}

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return {"mes": "", "itens": []}

    headers = [normalize_key(v) for v in rows[0]]
    idx = header_index(headers, ["mes", "item", "valor"])

    month_name = ""
    items = []
    for row in rows[1:]:
        if len(row) == 0:
            continue
        if "mes" in idx and idx["mes"] < len(row) and row[idx["mes"]] not in (None, ""):
            month_name = str(row[idx["mes"]]).strip()
            continue
        if "item" in idx and "valor" in idx:
            item = row[idx["item"]] if idx["item"] < len(row) else ""
            value = row[idx["valor"]] if idx["valor"] < len(row) else 0
            if item not in (None, ""):
                items.append({"item": str(item), "valor": parse_decimal(value)})

    return {"mes": month_name, "itens": items}


def build_payload(workbook):
    labels, months = load_month_rows(workbook)
    categories = load_categories(workbook)
    recent = load_investment_recent(workbook)

    if not recent.get("itens"):
        recent = {
            "mes": labels[-1] if labels else "",
            "itens": [
                {"item": "cripto", "valor": 0},
                {"item": "Invest ações", "valor": 0},
                {"item": "Dollar", "valor": 0},
                {"item": "tesouro", "valor": 0},
                {"item": "Reservas", "valor": 0},
            ],
        }

    return {
        "labels": labels,
        "months": months,
        "categorias": categories,
        "investimentos_recentes": recent,
    }


def is_url(value: str) -> bool:
    return value.startswith(("http://", "https://", "file://"))


def append_download_param(url: str) -> str:
    if "download=1" in url:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}download=1"


def resolve_source_path(source: str) -> Path:
    if not is_url(source):
        return Path(source)

    if source.startswith("file://"):
        return Path(source[7:])

    download_url = append_download_param(source)
    request = Request(download_url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(request, timeout=60) as response:
        content_disposition = response.headers.get("Content-Disposition", "")
        filename_match = re.search(r'filename\s*=\s*"?([^";]+)"?', content_disposition)
        suffix = ".xlsx"
        if filename_match:
            suffix = Path(filename_match.group(1)).suffix or suffix
        temp_fd, temp_path = tempfile.mkstemp(prefix="finance_", suffix=suffix)
        os.close(temp_fd)
        with open(temp_path, "wb") as file_obj:
            shutil.copyfileobj(response, file_obj)

    return Path(temp_path)


def main():
    parser = argparse.ArgumentParser(description="Converte a planilha financeira em JSON usado pelo dashboard.")
    parser.add_argument("source", help="Arquivo .xlsx local ou link compartilhado do OneDrive/Google Drive")
    parser.add_argument("--output", default="finance-data.json", help="Arquivo JSON de saída")
    args = parser.parse_args()

    source = resolve_source_path(args.source)
    if not source.exists():
        raise SystemExit(f"Arquivo não encontrado: {source}")

    wb = load_workbook(source, data_only=True)
    payload = build_payload(wb)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Arquivo gerado: {out}")


if __name__ == "__main__":
    main()

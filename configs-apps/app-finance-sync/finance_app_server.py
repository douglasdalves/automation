#!/usr/bin/env python3
"""Serve the finance dashboard and persist manual entries in SQLite."""

from __future__ import annotations

import json
import mimetypes
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATABASE_FILE = Path(os.environ.get("FINANCE_DB_PATH", str(ROOT / "finance.db")))
PORT = 8001

DEFAULT_PAYLOAD = {
    "labels": ["Set/26"],
    "months": [
        {
            "label": "Set/26",
            "receita": 0,
            "saldo_anterior": 0,
            "contas_mensais": 0,
            "extras": 0,
            "despesas": 0,
            "saldo": 0,
            "reserva": 0,
            "investimentos": 0,
            "extras_itens": [],
        }
    ],
    "categorias": [],
    "investimentos_recentes": {"mes": "Set/26", "itens": []},
}


def normalize_month_index(label: str) -> int:
    text = str(label or "").lower()
    month_map = {
        "jan": 1,
        "fev": 2,
        "mar": 3,
        "abr": 4,
        "mai": 5,
        "jun": 6,
        "jul": 7,
        "ago": 8,
        "set": 9,
        "out": 10,
        "nov": 11,
        "dez": 12,
    }

    for name, month_no in month_map.items():
        if name in text:
            import re

            year_match = re.search(r"(19|20)\d{2}|\d{2}", text)
            year = int(year_match.group(0)) if year_match else 2026
            year = 2000 + year if year < 100 else year
            return (year * 12) + month_no
    return 0


def build_fresh_baseline() -> dict:
    return json.loads(json.dumps(DEFAULT_PAYLOAD))


def connect_database() -> sqlite3.Connection:
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE)
    connection.execute("PRAGMA journal_mode=WAL")
    return connection


def initialize_database() -> None:
    with connect_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS months (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL UNIQUE,
                payload TEXT NOT NULL
            )
            """
        )
        has_data = connection.execute("SELECT 1 FROM months LIMIT 1").fetchone()
        if has_data:
            return
        migrated = build_fresh_baseline()
        connection.executemany(
            "INSERT INTO months (label, payload) VALUES (?, ?)",
            [(month["label"], json.dumps(month, ensure_ascii=False)) for month in migrated["months"]],
        )


def write_database_payload(payload: dict) -> dict:
    cleaned = ensure_clean_payload(payload)
    with connect_database() as connection:
        connection.execute("DELETE FROM months")
        connection.executemany(
            "INSERT INTO months (label, payload) VALUES (?, ?)",
            [(month["label"], json.dumps(month, ensure_ascii=False)) for month in cleaned["months"]],
        )
    return cleaned


def merge_item_lists(previous: list, incoming: list, value_key: str) -> list:
    items: dict[str, float] = {}
    for item in previous or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("item") or "").strip()
        value = float(item.get(value_key) or 0)
        if not name or value == 0:
            continue
        items[name] = value
    for item in incoming or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("item") or "").strip()
        value = float(item.get(value_key) or 0)
        if name and value != 0:
            items[name] = value
    return [{"item": name, value_key: value} for name, value in items.items()]


def ensure_clean_payload(payload: dict | None) -> dict:
    if not isinstance(payload, dict) or not isinstance(payload.get("months"), list):
        return build_fresh_baseline()

    months = payload["months"]
    if not months:
        return build_fresh_baseline()

    start_index = normalize_month_index("Ago/26")
    filtered = [month for month in months if isinstance(month, dict) and normalize_month_index(str(month.get("label", ""))) >= start_index]
    if not filtered:
        return build_fresh_baseline()

    legacy_categories = payload.get("categorias", []) or []
    legacy_recent = payload.get("investimentos_recentes", {}) or {}
    legacy_recent_month = str(legacy_recent.get("mes") or "").strip() if isinstance(legacy_recent, dict) else ""
    legacy_categories_total = sum(float(item.get("total") or 0) for item in legacy_categories if isinstance(item, dict))
    for month in filtered:
        if "categorias" not in month and legacy_categories_total and float(month.get("contas_mensais") or 0) == legacy_categories_total:
            month["categorias"] = legacy_categories
        if "investimentos_itens" not in month and isinstance(legacy_recent, dict) and str(month.get("label") or "").strip() == legacy_recent_month:
            month["investimentos_itens"] = legacy_recent.get("itens", [])

    cleaned = {
        "labels": [month.get("label", "Set/26") for month in filtered],
        "months": filtered,
        "categorias": payload.get("categorias", []),
        "investimentos_recentes": payload.get("investimentos_recentes", {"mes": filtered[-1].get("label", "Set/26"), "itens": []}),
    }

    if len(cleaned["months"]) == 1 and legacy_categories:
        category_total = sum(
            float(category.get("total") or 0)
            for category in (cleaned["categorias"] or [])
            if isinstance(category, dict)
        )
        cleaned["months"][0]["contas_mensais"] = category_total

    recent = cleaned["investimentos_recentes"]
    if isinstance(recent, dict):
        recent_month = str(recent.get("mes") or "").strip()
        recent_total = sum(
            float(item.get("valor") or 0)
            for item in (recent.get("itens") or [])
            if isinstance(item, dict)
        )
        for month in cleaned["months"]:
            if str(month.get("label") or "").strip() == recent_month:
                month["investimentos"] = recent_total

    for month in cleaned["months"]:
        month["investimentos"] = sum(
            float(item.get("valor") or 0)
            for item in (month.get("investimentos_itens") or [])
            if isinstance(item, dict)
        )

    cleaned.pop("categorias", None)
    cleaned.pop("investimentos_recentes", None)

    return cleaned


def load_data() -> dict:
    initialize_database()
    with connect_database() as connection:
        rows = connection.execute("SELECT label, payload FROM months ORDER BY id").fetchall()

    if not rows:
        return write_database_payload(build_fresh_baseline())

    months = [json.loads(payload) for _, payload in rows]
    return {"labels": [month["label"] for month in months], "months": months}


def merge_payload(existing: dict, incoming: dict) -> dict:
    base = ensure_clean_payload(existing)
    if not isinstance(incoming, dict):
        return base

    merged = json.loads(json.dumps(base))
    new_months = incoming.get("months") or []
    if isinstance(new_months, list):
        by_label = {str(item.get("label", "")): item for item in merged.get("months", []) if isinstance(item, dict) and item.get("label")}
        for month in new_months:
            if not isinstance(month, dict):
                continue
            label = str(month.get("label", "")).strip()
            if not label:
                continue
            previous = by_label.get(label, {})
            categorias = merge_item_lists(previous.get("categorias", []), month.get("categorias", []), "total")
            investimentos_itens = merge_item_lists(previous.get("investimentos_itens", []), month.get("investimentos_itens", []), "valor")
            extras_itens = merge_item_lists(previous.get("extras_itens", []), month.get("extras_itens", []), "valor")
            normalized = {
                "label": label,
                "receita": float(month.get("receita", previous.get("receita", 0)) or 0),
                "saldo_anterior": float(month.get("saldo_anterior", previous.get("saldo_anterior", 0)) or 0),
                "contas_mensais": sum(item["total"] for item in categorias),
                "extras": sum(item["valor"] for item in extras_itens),
                "despesas": float(month.get("despesas", previous.get("despesas", 0)) or 0),
                "saldo": float(month.get("saldo", previous.get("saldo", 0)) or 0),
                "reserva": float(month.get("reserva", previous.get("reserva", 0)) or 0),
                "investimentos": sum(item["valor"] for item in investimentos_itens),
                "extras_itens": extras_itens,
                "categorias": categorias,
                "investimentos_itens": investimentos_itens,
            }
            if label in by_label:
                by_label[label] = normalized
            else:
                merged.setdefault("months", []).append(normalized)
                by_label[label] = normalized

        merged["months"] = list(by_label.values())
        merged["labels"] = [item.get("label") for item in merged["months"] if isinstance(item, dict) and item.get("label")]

    existing_categorias = merged.get("categorias", []) or []
    incoming_categorias = incoming.get("categorias") or []
    category_map: dict[str, float] = {}
    for category in existing_categorias:
        if isinstance(category, dict):
            key = str(category.get("item") or "").strip()
            if key:
                category_map[key] = float(category.get("total") or 0)
    for category in incoming_categorias:
        if not isinstance(category, dict):
            continue
        key = str(category.get("item") or "").strip()
        total = float(category.get("total") or 0)
        if not key or total == 0:
            continue
        category_map[key] = total
    if "categorias" in incoming:
        merged["categorias"] = [{"item": key, "total": value} for key, value in category_map.items()]

    recent = merged.get("investimentos_recentes", {"mes": "", "itens": []})
    if "investimentos_recentes" not in incoming:
        return ensure_clean_payload(merged)
    incoming_recent = incoming.get("investimentos_recentes") or {"mes": "", "itens": []}
    if not isinstance(recent, dict):
        recent = {"mes": "", "itens": []}
    if not isinstance(incoming_recent, dict):
        incoming_recent = {"mes": "", "itens": []}

    current_items = recent.get("itens") or []
    new_items = incoming_recent.get("itens") or []
    if incoming_recent.get("mes") and incoming_recent.get("mes") != recent.get("mes"):
        current_items = []
    merged_map: dict[str, float] = {}
    for item in current_items:
        if not isinstance(item, dict):
            continue
        key = str(item.get("item") or "").strip()
        if key:
            merged_map[key] = float(item.get("valor") or 0)
    for item in new_items:
        if not isinstance(item, dict):
            continue
        key = str(item.get("item") or "").strip()
        value = float(item.get("valor") or 0)
        if key and value != 0:
            merged_map[key] = value

    recent_month = incoming_recent.get("mes") or recent.get("mes") or (merged.get("months", [])[-1].get("label") if merged.get("months") else "")
    merged["investimentos_recentes"] = {
        "mes": recent_month,
        "itens": [{"item": key, "valor": value} for key, value in merged_map.items()],
    }

    return ensure_clean_payload(merged)


def clear_month_data(month_label: str) -> dict:
    current = load_data()
    target = str(month_label or "").strip()
    if not target:
        return current

    months = []
    for item in current.get("months", []):
        if isinstance(item, dict) and str(item.get("label") or "").strip() == target:
            continue
        months.append(item)

    payload = {"months": months}
    if not payload["months"]:
        payload = build_fresh_baseline()
    return write_database_payload(payload)


def clear_category_data(category_name: str) -> dict:
    current = load_data()
    target = str(category_name or "").strip()
    if not target:
        return current

    months = []
    for month in current.get("months", []):
        updated = json.loads(json.dumps(month))
        updated["categorias"] = [
            item for item in (updated.get("categorias") or [])
            if not (isinstance(item, dict) and str(item.get("item") or "").strip() == target)
        ]
        months.append(updated)
    return write_database_payload({"months": months})


def save_data(payload: dict) -> dict:
    existing = load_data()
    merged = merge_payload(existing, payload)
    return write_database_payload(merged)


class FinanceHandler(BaseHTTPRequestHandler):
    server_version = "FinanceAppServer/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in {"/api/data", "/api/data/"}:
            self._send_json(load_data())
            return

        if path in {"/api/reset", "/api/reset/"}:
            self._send_json(save_data(build_fresh_baseline()))
            return

        relative = path.strip("/") or "index.html"
        if relative.startswith(".."):
            self.send_error(403, "Acesso negado")
            return

        target = (ROOT / relative).resolve()
        if ROOT not in target.parents and target != ROOT:
            self.send_error(403, "Acesso negado")
            return

        if target.is_dir():
            target = target / "index.html"

        if not target.exists():
            self.send_error(404, "Arquivo não encontrado")
            return

        content = target.read_bytes()
        content_type, _ = mimetypes.guess_type(str(target))
        if content_type is None:
            content_type = "application/octet-stream"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path in {"/api/save", "/api/save/"}:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0

            body = self.rfile.read(length)
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json({"ok": False, "error": "JSON inválido"}, status=400)
                return

            try:
                saved = save_data(payload)
            except Exception as exc:  # pragma: no cover - defensive path
                self._send_json({"ok": False, "error": str(exc)}, status=500)
                return

            self._send_json({"ok": True, "data": saved})
            return

        if parsed.path in {"/api/clear-month", "/api/clear-month/"}:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0

            body = self.rfile.read(length)
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json({"ok": False, "error": "JSON inválido"}, status=400)
                return

            try:
                month_label = payload.get("month") or payload.get("label") or ""
                cleared = clear_month_data(month_label)
                self._send_json({"ok": True, "data": cleared})
                return
            except Exception as exc:  # pragma: no cover - defensive path
                self._send_json({"ok": False, "error": str(exc)}, status=500)
                return

        if parsed.path in {"/api/clear-category", "/api/clear-category/"}:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0

            body = self.rfile.read(length)
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json({"ok": False, "error": "JSON inválido"}, status=400)
                return

            try:
                item_name = payload.get("item") or payload.get("category") or ""
                cleared = clear_category_data(item_name)
                self._send_json({"ok": True, "data": cleared})
                return
            except Exception as exc:  # pragma: no cover - defensive path
                self._send_json({"ok": False, "error": str(exc)}, status=500)
                return

        self.send_error(404, "Endpoint não encontrado")

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), FinanceHandler)
    print(f"Finance app server listening on http://0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

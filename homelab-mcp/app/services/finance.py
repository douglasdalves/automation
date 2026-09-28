"""Read the monthly summary published by the finance dashboard."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

import httpx

from app.config import Config

_MONTHS = (
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)


def _month_label(today: date | None = None) -> str:
    if today is None:
        today = datetime.now(tz=timezone.utc).date()
    return f"{_MONTHS[today.month - 1]}/{today.year % 100:02d}"


def _month_index(label: str) -> int:
    """Parse dashboard labels such as ``set/26`` into a sortable index."""
    text = str(label or "").lower()
    month = next(
        (number for number, name in enumerate(_MONTHS, start=1) if name in text),
        None,
    )
    if month is None:
        return 0

    year_match = re.search(r"(19|20)\d{2}|\d{2}", text)
    year = int(year_match.group(0)) if year_match else 2026
    if year < 100:
        year += 2000
    return year * 12 + month


def get_current_month_summary() -> dict:
    """Return the dashboard summary for the current calendar month."""
    if not Config.FINANCE_DASHBOARD_DATA_URL:
        return {
            "success": False,
            "error": "FINANCE_DASHBOARD_DATA_URL não está configurada no arquivo .env.",
        }

    try:
        response = httpx.get(Config.FINANCE_DASHBOARD_DATA_URL, timeout=10.0)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {
            "success": False,
            "error": f"Não foi possível consultar o painel financeiro: {exc}",
        }

    months = payload.get("months", []) if isinstance(payload, dict) else []
    if not isinstance(months, list) or not months:
        return {
            "success": False,
            "error": "O painel financeiro não possui meses cadastrados.",
        }

    today = datetime.now(tz=timezone.utc).date()
    current_label = _month_label(today)
    current_index = today.year * 12 + today.month
    selected = next(
        (
            month
            for month in months
            if isinstance(month, dict)
            and _month_index(month.get("label", "")) == current_index
        ),
        None,
    )
    if selected is None:
        selected = next(
            (month for month in reversed(months) if isinstance(month, dict)), None
        )
    if selected is None:
        return {
            "success": False,
            "error": "Os dados do painel financeiro são inválidos.",
        }

    fields = (
        "saldo_anterior",
        "receita",
        "ganho_extra",
        "despesas",
        "extras",
        "investimentos",
        "saldo",
    )
    summary = {field: float(selected.get(field) or 0) for field in fields}
    return {
        "success": True,
        "requested_month": current_label,
        "month": selected.get("label", current_label),
        "is_current_month": _month_index(selected.get("label", "")) == current_index,
        "summary": summary,
    }


def get_current_month_investments() -> dict:
    """Return investment items shown by the dashboard for the current month."""
    if not Config.FINANCE_DASHBOARD_DATA_URL:
        return {
            "success": False,
            "error": "FINANCE_DASHBOARD_DATA_URL não está configurada no arquivo .env.",
        }

    try:
        response = httpx.get(Config.FINANCE_DASHBOARD_DATA_URL, timeout=10.0)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {
            "success": False,
            "error": f"Não foi possível consultar o painel financeiro: {exc}",
        }

    months = payload.get("months", []) if isinstance(payload, dict) else []
    if not isinstance(months, list) or not months:
        return {
            "success": False,
            "error": "O painel financeiro não possui meses cadastrados.",
        }

    today = datetime.now(tz=timezone.utc).date()
    current_index = today.year * 12 + today.month
    selected = next(
        (
            month
            for month in months
            if isinstance(month, dict)
            and _month_index(month.get("label", "")) == current_index
        ),
        None,
    )
    is_current_month = selected is not None
    if selected is None:
        selected = next(
            (month for month in reversed(months) if isinstance(month, dict)), None
        )
    if selected is None:
        return {
            "success": False,
            "error": "Os dados do painel financeiro são inválidos.",
        }

    items = selected.get("investimentos_itens", [])
    if not isinstance(items, list):
        items = []
    return {
        "success": True,
        "month": selected.get("label", _month_label(today)),
        "is_current_month": is_current_month,
        "total": float(selected.get("investimentos") or 0),
        "items": [
            {
                "item": str(item.get("item") or "Investimento"),
                "valor": float(item.get("valor") or 0),
            }
            for item in items
            if isinstance(item, dict)
        ],
    }


def get_current_month_accounts() -> dict:
    """Return fixed and extra bill items shown for the current dashboard month."""
    if not Config.FINANCE_DASHBOARD_DATA_URL:
        return {
            "success": False,
            "error": "FINANCE_DASHBOARD_DATA_URL não está configurada no arquivo .env.",
        }

    try:
        response = httpx.get(Config.FINANCE_DASHBOARD_DATA_URL, timeout=10.0)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {
            "success": False,
            "error": f"Não foi possível consultar o painel financeiro: {exc}",
        }

    months = payload.get("months", []) if isinstance(payload, dict) else []
    if not isinstance(months, list) or not months:
        return {
            "success": False,
            "error": "O painel financeiro não possui meses cadastrados.",
        }

    today = datetime.now(tz=timezone.utc).date()
    current_index = today.year * 12 + today.month
    selected = next(
        (
            month
            for month in months
            if isinstance(month, dict)
            and _month_index(month.get("label", "")) == current_index
        ),
        None,
    )
    is_current_month = selected is not None
    if selected is None:
        selected = next(
            (month for month in reversed(months) if isinstance(month, dict)), None
        )
    if selected is None:
        return {
            "success": False,
            "error": "Os dados do painel financeiro são inválidos.",
        }

    def normalize_items(key: str, value_key: str) -> list[dict]:
        items = selected.get(key, [])
        if not isinstance(items, list):
            return []
        return [
            {
                "item": str(item.get("item") or "Conta"),
                "valor": float(item.get(value_key) or 0),
            }
            for item in items
            if isinstance(item, dict)
        ]

    fixed = normalize_items("categorias", "total")
    extras = normalize_items("extras_itens", "valor")
    return {
        "success": True,
        "month": selected.get("label", _month_label(today)),
        "is_current_month": is_current_month,
        "fixed_total": sum(item["valor"] for item in fixed),
        "fixed_items": fixed,
        "extras_total": sum(item["valor"] for item in extras),
        "extra_items": extras,
    }

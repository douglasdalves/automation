"""Read the monthly summary published by the finance dashboard."""

from __future__ import annotations

from datetime import date, timezone

import httpx
from app.config import Config

_MONTHS = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


def _month_label(today: date | None = None) -> str:
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date()


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
        return {"success": False, "error": f"Não foi possível consultar o painel financeiro: {exc}"}

    months = payload.get("months", []) if isinstance(payload, dict) else []
    if not isinstance(months, list) or not months:
        return {"success": False, "error": "O painel financeiro não possui meses cadastrados."}

    current_label = _month_label()
    selected = next(
        (month for month in months if isinstance(month, dict) and month.get("label") == current_label),
        None,
    )
    if selected is None:
        selected = next((month for month in reversed(months) if isinstance(month, dict)), None)
    if selected is None:
        return {"success": False, "error": "Os dados do painel financeiro são inválidos."}

    fields = ("saldo_anterior", "receita", "ganho_extra", "despesas", "extras", "investimentos", "saldo")
    summary = {field: float(selected.get(field) or 0) for field in fields}
    return {
        "success": True,
        "requested_month": current_label,
        "month": selected.get("label", current_label),
        "is_current_month": selected.get("label") == current_label,
        "summary": summary,
    }

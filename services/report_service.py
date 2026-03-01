from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app import db
from app.models import LedgerEntry


class ReportService:
    """Read-only reporting facade based on immutable ledger data."""

    @staticmethod
    def account_period_summary(*, user_id: int, account_id: int, year: int, month: int):
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        entries = LedgerEntry.query.filter(
            LedgerEntry.user_id == user_id,
            LedgerEntry.account_id == account_id,
            LedgerEntry.created_at >= start,
            LedgerEntry.created_at < end,
        ).all()

        receitas = Decimal("0")
        despesas = Decimal("0")
        for e in entries:
            value = Decimal(str(e.amount or 0))
            if value >= 0:
                receitas += value
            else:
                despesas += abs(value)

        balance = receitas - despesas
        return {
            "year": year,
            "month": month,
            "receitas": receitas,
            "despesas": despesas,
            "balance": balance,
            "entries": entries,
        }

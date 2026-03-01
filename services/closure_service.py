from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from typing import Tuple

from app import db
from app.models import LedgerEntry, MonthlyClosure


class ClosureService:
    """Monthly closure and locking rules."""

    @staticmethod
    def get_period_bounds(year: int, month: int) -> Tuple[datetime, datetime]:
        start = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        end = datetime(year, month, last_day, 23, 59, 59)
        return start, end

    @staticmethod
    def is_period_locked(*, user_id: int, account_id: int, year: int, month: int) -> bool:
        closure = MonthlyClosure.query.filter_by(
            user_id=user_id,
            account_id=account_id,
            year=year,
            month=month,
        ).first()
        return bool(closure and closure.locked)

    @staticmethod
    def ensure_period_open(*, user_id: int, account_id: int, date_value):
        if isinstance(date_value, datetime):
            dt = date_value
        elif isinstance(date_value, date):
            dt = datetime.combine(date_value, datetime.min.time())
        else:
            raise ValueError("Data invalida para validacao de fechamento mensal")

        if ClosureService.is_period_locked(
            user_id=user_id,
            account_id=account_id,
            year=dt.year,
            month=dt.month,
        ):
            raise ValueError("Periodo fechado. Lancamento bloqueado por fechamento mensal")

    @staticmethod
    def close_month(*, user_id: int, account_id: int, year: int, month: int) -> MonthlyClosure:
        start, end = ClosureService.get_period_bounds(year, month)

        period_entries = LedgerEntry.query.filter(
            LedgerEntry.user_id == user_id,
            LedgerEntry.account_id == account_id,
            LedgerEntry.created_at >= start,
            LedgerEntry.created_at <= end,
        ).all()

        total_receitas = Decimal("0")
        total_despesas = Decimal("0")
        for entry in period_entries:
            value = Decimal(str(entry.amount or 0))
            if value >= 0:
                total_receitas += value
            else:
                total_despesas += abs(value)

        cumulative = (
            db.session.query(db.func.sum(LedgerEntry.amount))
            .filter(
                LedgerEntry.user_id == user_id,
                LedgerEntry.account_id == account_id,
                LedgerEntry.created_at <= end,
            )
            .scalar()
        )
        closing_balance = Decimal(str(cumulative or 0))

        last_entry = (
            LedgerEntry.query.filter(
                LedgerEntry.user_id == user_id,
                LedgerEntry.account_id == account_id,
                LedgerEntry.created_at <= end,
            )
            .order_by(LedgerEntry.id.desc())
            .first()
        )

        closure = MonthlyClosure.query.filter_by(
            user_id=user_id,
            account_id=account_id,
            year=year,
            month=month,
        ).first()

        if not closure:
            closure = MonthlyClosure(
                user_id=user_id,
                account_id=account_id,
                year=year,
                month=month,
            )
            db.session.add(closure)

        closure.closing_balance = closing_balance
        closure.total_receitas = total_receitas
        closure.total_despesas = total_despesas
        closure.ledger_hash_snapshot = last_entry.current_hash if last_entry else None
        closure.locked = True

        db.session.commit()
        return closure

    @staticmethod
    def unlock_month(*, user_id: int, account_id: int, year: int, month: int):
        closure = MonthlyClosure.query.filter_by(
            user_id=user_id,
            account_id=account_id,
            year=year,
            month=month,
        ).first()
        if closure:
            closure.locked = False
            db.session.commit()

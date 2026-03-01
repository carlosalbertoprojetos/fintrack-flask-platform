from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from app import db
from app.models import LedgerEntry, MonthlyClosure, Transaction
from services.ledger_service import LedgerService


class DataQualityService:
    """Data quality checks for operational and audit consistency."""

    @staticmethod
    def transaction_issues(*, user_id: int) -> List[Dict]:
        issues = []
        txs = Transaction.query.filter_by(user_id=user_id).all()

        for tx in txs:
            if tx.amount is None or float(tx.amount) <= 0:
                issues.append({"type": "invalid_amount", "transaction_id": tx.id})
            if not tx.conta_id:
                issues.append({"type": "missing_account", "transaction_id": tx.id})
            if tx.paid and not tx.payment_date:
                issues.append({"type": "paid_without_payment_date", "transaction_id": tx.id})
            if tx.type not in {"receita", "despesa"}:
                issues.append({"type": "invalid_type", "transaction_id": tx.id})

        return issues

    @staticmethod
    def ledger_integrity_report(*, user_id: int, account_id: Optional[int] = None) -> Dict:
        ok, message = LedgerService.validate_integrity(user_id=user_id, account_id=account_id)
        count_query = LedgerEntry.query.filter_by(user_id=user_id)
        if account_id is not None:
            count_query = count_query.filter_by(account_id=account_id)

        return {
            "ok": ok,
            "message": message,
            "entries": count_query.count(),
        }

    @staticmethod
    def closure_consistency(*, user_id: int, account_id: int, year: int, month: int) -> Dict:
        closure = MonthlyClosure.query.filter_by(
            user_id=user_id,
            account_id=account_id,
            year=year,
            month=month,
        ).first()

        if not closure:
            return {"ok": False, "message": "closure_not_found"}

        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        period_total = (
            db.session.query(db.func.sum(LedgerEntry.amount))
            .filter(
                LedgerEntry.user_id == user_id,
                LedgerEntry.account_id == account_id,
                LedgerEntry.created_at >= start,
                LedgerEntry.created_at < end,
            )
            .scalar()
        )
        ledger_total = Decimal(str(period_total or 0))
        closure_total = Decimal(str(closure.total_receitas or 0)) - Decimal(str(closure.total_despesas or 0))

        return {
            "ok": ledger_total == closure_total,
            "ledger_total": float(ledger_total),
            "closure_total": float(closure_total),
            "difference": float(ledger_total - closure_total),
        }

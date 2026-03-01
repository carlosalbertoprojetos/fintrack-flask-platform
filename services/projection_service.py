from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Dict, List, Optional

from app.models import SimulationSession, Transaction
from services.ledger_service import LedgerService


class ProjectionService:
    """Local projections and scenario simulation helpers."""

    @staticmethod
    def _cashflow_points(*, user_id: int, account_id: Optional[int] = None) -> List[Dict]:
        query = Transaction.query.filter_by(user_id=user_id, paid=True)
        if account_id is not None:
            query = query.filter_by(conta_id=account_id)

        txs = query.order_by(Transaction.payment_date.asc(), Transaction.date.asc(), Transaction.id.asc()).all()

        buckets = defaultdict(float)
        for tx in txs:
            effective = tx.payment_date or tx.date
            key = effective.strftime("%Y-%m")
            amount = float(tx.amount or 0)
            discount = float(tx.discount or 0)
            if tx.type == "despesa":
                amount = -(amount - discount)
            buckets[key] += amount

        points = []
        for key in sorted(buckets.keys()):
            points.append({"period": key, "balance": float(buckets[key])})
        return points

    @staticmethod
    def _weighted_average(values: List[float]) -> float:
        if not values:
            return 0.0
        weights = list(range(1, len(values) + 1))
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        return weighted_sum / sum(weights)

    @staticmethod
    def project_next_month(*, user_id: int, account_id: Optional[int] = None, lookback_months: int = 6):
        series = ProjectionService._cashflow_points(user_id=user_id, account_id=account_id)
        recent = [p["balance"] for p in series[-lookback_months:]]

        projection = ProjectionService._weighted_average(recent)
        confidence = 0.0
        if len(recent) >= 2:
            avg = mean(recent)
            variance = mean([(x - avg) ** 2 for x in recent])
            confidence = max(0.0, min(1.0, 1 - (variance / (abs(avg) + 1))))

        return {
            "series": series,
            "projected_balance": round(float(projection), 2),
            "confidence": round(float(confidence), 4),
            "lookback_months": lookback_months,
        }

    @staticmethod
    def financial_health_score(*, user_id: int, account_id: Optional[int] = None):
        projection = ProjectionService.project_next_month(user_id=user_id, account_id=account_id)
        series = projection["series"]
        recent = [p["balance"] for p in series[-3:]]

        if not recent:
            return {"score": 50, "status": "neutral", "reason": "insufficient_data"}

        avg_balance = mean(recent)
        positive_ratio = sum(1 for v in recent if v >= 0) / len(recent)

        score = 50
        upside = min(30, int(max(0, avg_balance / 100)))
        downside = min(30, int(max(0, (-avg_balance) / 100)))
        score += upside
        score -= downside
        score += int(20 * positive_ratio)
        score = max(0, min(100, score))

        if score >= 80:
            status = "healthy"
        elif score >= 60:
            status = "stable"
        elif score >= 40:
            status = "attention"
        else:
            status = "critical"

        return {
            "score": score,
            "status": status,
            "avg_recent_balance": round(float(avg_balance), 2),
            "positive_ratio": round(float(positive_ratio), 4),
        }

    @staticmethod
    def start_simulation(*, user_id: int, account_id: int, name: str = "Simulacao") -> SimulationSession:
        return LedgerService.create_simulation_session(user_id=user_id, account_id=account_id, name=name)

    @staticmethod
    def simulate_monthly_change(*, simulation_session_id: int, amount: float, reference_id: Optional[int] = None):
        return LedgerService.append_simulation_entry_for_session(
            simulation_session_id=simulation_session_id,
            reference_type="projection_scenario",
            reference_id=reference_id,
            amount=amount,
            created_at=datetime.utcnow(),
        )

    @staticmethod
    def simulation_balance(*, simulation_session_id: int):
        return LedgerService.get_simulation_balance(simulation_session_id=simulation_session_id)

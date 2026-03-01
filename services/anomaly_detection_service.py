from __future__ import annotations

from statistics import mean, pstdev

from app.models import Transaction


class AnomalyDetectionService:
    """Local anomaly detection using statistical fallback."""

    @staticmethod
    def detect_user_transaction_anomalies(*, user_id: int, threshold: float = 3.0):
        txs = Transaction.query.filter_by(user_id=user_id).all()
        values = [float(t.amount or 0) for t in txs]
        if len(values) < 5:
            return []

        mu = mean(values)
        sigma = pstdev(values)
        if sigma == 0:
            return []

        anomalies = []
        for tx in txs:
            z = abs((float(tx.amount or 0) - mu) / sigma)
            if z >= threshold:
                anomalies.append({"transaction_id": tx.id, "z_score": z, "amount": tx.amount})
        return anomalies

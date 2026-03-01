from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from app import db
from app.models import AIModelMetadata, Transaction


class AIClassificationService:
    """Local-only per-user text classifier infrastructure."""

    MODEL_DIR = Path("instance") / "ai_models"

    @classmethod
    def _model_file(cls, user_id: int):
        cls.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        return cls.MODEL_DIR / f"classifier_user_{user_id}.json"

    @classmethod
    def train_user_model(cls, *, user_id: int):
        txs = Transaction.query.filter_by(user_id=user_id).all()
        token_map = defaultdict(Counter)

        for tx in txs:
            label = tx.category_id
            text = f"{tx.description or ''} {tx.details or ''} {tx.notes or ''}".lower()
            for token in [t for t in text.split() if len(t) > 2]:
                token_map[str(label)][token] += 1

        serializable = {k: dict(v) for k, v in token_map.items()}
        model_path = cls._model_file(user_id)
        model_path.write_text(json.dumps(serializable, ensure_ascii=False), encoding="utf-8")

        metadata = AIModelMetadata.query.filter_by(user_id=user_id, model_type="transaction_classifier").first()
        if not metadata:
            metadata = AIModelMetadata(
                user_id=user_id,
                model_type="transaction_classifier",
                model_path=str(model_path),
            )
            db.session.add(metadata)

        metadata.metrics_json = json.dumps({"samples": len(txs)}, ensure_ascii=False)
        db.session.commit()
        return metadata

    @classmethod
    def classify(cls, *, user_id: int, text: str):
        model_path = cls._model_file(user_id)
        if not model_path.exists():
            return None

        model_data = json.loads(model_path.read_text(encoding="utf-8"))
        scores = Counter()
        tokens = [t for t in (text or "").lower().split() if len(t) > 2]

        for label, token_weights in model_data.items():
            label_score = 0
            for token in tokens:
                label_score += token_weights.get(token, 0)
            if label_score > 0:
                scores[label] = label_score

        if not scores:
            return None
        return int(scores.most_common(1)[0][0])

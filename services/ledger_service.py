from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional, Tuple

from app import db
from app.models import (
    Conta,
    LedgerEntry,
    MovimentacaoInvestimento,
    SimulationLedgerEntry,
    SimulationSession,
    Transaction,
)


class LedgerService:
    """Central service for immutable ledger operations."""

    CENT = Decimal("0.01")

    @staticmethod
    def _to_decimal(value) -> Decimal:
        if isinstance(value, Decimal):
            val = value
        else:
            val = Decimal(str(value or 0))
        return val.quantize(LedgerService.CENT, rounding=ROUND_HALF_UP)

    @staticmethod
    def _last_entry(user_id: int, account_id: int):
        return (
            LedgerEntry.query.filter_by(user_id=user_id, account_id=account_id)
            .order_by(LedgerEntry.id.desc())
            .first()
        )

    @staticmethod
    def _last_sim_entry(simulation_session_id: int, user_id: int, account_id: int):
        return (
            SimulationLedgerEntry.query.filter_by(
                simulation_session_id=simulation_session_id,
                user_id=user_id,
                account_id=account_id,
            )
            .order_by(SimulationLedgerEntry.id.desc())
            .first()
        )

    @staticmethod
    def append_entry(
        *,
        user_id: int,
        account_id: int,
        reference_type: str,
        reference_id: Optional[int],
        amount,
        created_at: Optional[datetime] = None,
    ) -> LedgerEntry:
        created = created_at or datetime.utcnow()
        signed_amount = LedgerService._to_decimal(amount)

        previous = LedgerService._last_entry(user_id=user_id, account_id=account_id)
        previous_hash = previous.current_hash if previous else None
        current_hash = LedgerEntry.build_hash(
            user_id=user_id,
            account_id=account_id,
            reference_type=reference_type,
            reference_id=reference_id,
            amount=signed_amount,
            created_at=created,
            previous_hash=previous_hash,
        )

        entry = LedgerEntry(
            user_id=user_id,
            account_id=account_id,
            reference_type=reference_type,
            reference_id=reference_id,
            amount=signed_amount,
            created_at=created,
            previous_hash=previous_hash,
            current_hash=current_hash,
        )
        db.session.add(entry)
        return entry

    @staticmethod
    def append_simulation_entry(
        *,
        simulation_session_id: int,
        user_id: int,
        account_id: int,
        reference_type: str,
        reference_id: Optional[int],
        amount,
        created_at: Optional[datetime] = None,
    ) -> SimulationLedgerEntry:
        created = created_at or datetime.utcnow()
        signed_amount = LedgerService._to_decimal(amount)

        previous = LedgerService._last_sim_entry(
            simulation_session_id=simulation_session_id,
            user_id=user_id,
            account_id=account_id,
        )
        previous_hash = previous.current_hash if previous else None
        current_hash = SimulationLedgerEntry.build_hash(
            user_id=user_id,
            account_id=account_id,
            reference_type=reference_type,
            reference_id=reference_id,
            amount=signed_amount,
            created_at=created,
            previous_hash=previous_hash,
        )

        entry = SimulationLedgerEntry(
            simulation_session_id=simulation_session_id,
            user_id=user_id,
            account_id=account_id,
            reference_type=reference_type,
            reference_id=reference_id,
            amount=signed_amount,
            created_at=created,
            previous_hash=previous_hash,
            current_hash=current_hash,
        )
        db.session.add(entry)
        return entry

    @staticmethod
    def validate_integrity(*, user_id: int, account_id: Optional[int] = None) -> Tuple[bool, str]:
        query = LedgerEntry.query.filter_by(user_id=user_id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        entries = query.order_by(LedgerEntry.account_id.asc(), LedgerEntry.id.asc()).all()
        grouped = {}
        for entry in entries:
            grouped.setdefault(entry.account_id, []).append(entry)

        for account_entries in grouped.values():
            ok, msg = LedgerEntry.validate_chain(account_entries)
            if not ok:
                return ok, msg
        return True, "ok"

    @staticmethod
    def validate_simulation_integrity(*, simulation_session_id: int) -> Tuple[bool, str]:
        entries = (
            SimulationLedgerEntry.query.filter_by(simulation_session_id=simulation_session_id)
            .order_by(SimulationLedgerEntry.account_id.asc(), SimulationLedgerEntry.id.asc())
            .all()
        )
        grouped = {}
        for entry in entries:
            grouped.setdefault(entry.account_id, []).append(entry)

        for account_entries in grouped.values():
            previous = None
            for entry in account_entries:
                expected = SimulationLedgerEntry.build_hash(
                    user_id=entry.user_id,
                    account_id=entry.account_id,
                    reference_type=entry.reference_type,
                    reference_id=entry.reference_id,
                    amount=entry.amount,
                    created_at=entry.created_at,
                    previous_hash=entry.previous_hash,
                )
                if entry.previous_hash != previous:
                    return False, f"Invalid previous hash at simulation_ledger_entry.id={entry.id}"
                if entry.current_hash != expected:
                    return False, f"Invalid current hash at simulation_ledger_entry.id={entry.id}"
                previous = entry.current_hash

        return True, "ok"

    @staticmethod
    def get_account_balance(*, user_id: int, account_id: int) -> Decimal:
        conta = Conta.query.filter_by(id=account_id, user_id=user_id).first()
        if not conta:
            return Decimal("0.00")

        movement_sum = (
            db.session.query(db.func.sum(LedgerEntry.amount))
            .filter_by(user_id=user_id, account_id=account_id)
            .scalar()
        )
        ledger_total = Decimal(str(movement_sum or 0))
        return (Decimal(str(conta.saldo_inicial or 0)) + ledger_total).quantize(
            LedgerService.CENT,
            rounding=ROUND_HALF_UP,
        )

    @staticmethod
    def rebuild_account_balances(*, conta_id: Optional[int] = None, user_id: Optional[int] = None):
        query = Conta.query
        if conta_id is not None:
            query = query.filter_by(id=conta_id)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)

        contas = query.all()
        for conta in contas:
            ledger_count = LedgerEntry.query.filter_by(user_id=conta.user_id, account_id=conta.id).count()
            if ledger_count == 0:
                has_legacy_data = (
                    Transaction.query.filter_by(user_id=conta.user_id, conta_id=conta.id).count() > 0
                    or MovimentacaoInvestimento.query.filter_by(user_id=conta.user_id, conta_id=conta.id).count() > 0
                )
                if has_legacy_data:
                    LedgerService.backfill_account_ledger(
                        user_id=conta.user_id,
                        account_id=conta.id,
                        commit=False,
                        rebuild=False,
                    )

            db.session.flush()
            saldo = LedgerService.get_account_balance(user_id=conta.user_id, account_id=conta.id)
            conta.saldo_atual = float(saldo)
            db.session.add(conta)

        db.session.commit()

    @staticmethod
    def apply_legacy_investment_balance_adjustment(*, conta: Conta, tipo_movimentacao: str, valor, operacao: str):
        """
        Compatibility layer used by legacy code paths while migration is in progress.
        Direct mutation is still avoided in business routes by preferring ledger entries.
        """
        amount = LedgerService._to_decimal(valor)

        if tipo_movimentacao == "aplicacao":
            delta = -amount if operacao == "adicionar" else amount
        elif tipo_movimentacao == "resgate":
            delta = amount if operacao == "adicionar" else -amount
        else:
            delta = Decimal("0.00")

        if delta == 0:
            return

        # Keep legacy semantics: do not allow negative balances in this compatibility hook.
        current_balance = LedgerService.get_account_balance(user_id=conta.user_id, account_id=conta.id)
        if delta < 0 and current_balance + delta < 0:
            delta = -current_balance

        LedgerService.append_entry(
            user_id=conta.user_id,
            account_id=conta.id,
            reference_type=f"legacy_investment_{tipo_movimentacao}",
            reference_id=None,
            amount=delta,
        )
        db.session.flush()
        updated = LedgerService.get_account_balance(user_id=conta.user_id, account_id=conta.id)
        conta.saldo_atual = float(updated)

    @staticmethod
    def backfill_account_ledger(
        *,
        user_id: int,
        account_id: int,
        commit: bool = True,
        rebuild: bool = True,
        clear_existing: bool = True,
    ):
        """
        Rebuild ledger entries from historical paid transactions and investment moves.
        Existing ledger entries for this scope are removed first.
        """
        if clear_existing:
            LedgerEntry.query.filter_by(user_id=user_id, account_id=account_id).delete()

        txs = (
            Transaction.query.filter_by(user_id=user_id, conta_id=account_id, paid=True)
            .order_by(Transaction.payment_date.asc(), Transaction.date.asc(), Transaction.id.asc())
            .all()
        )

        for tx in txs:
            if tx.type == "receita":
                effect = Decimal(str(tx.amount or 0))
            else:
                effect = -(Decimal(str(tx.amount or 0)) - Decimal(str(tx.discount or 0)))
            if effect != 0:
                LedgerService.append_entry(
                    user_id=user_id,
                    account_id=account_id,
                    reference_type="backfill_transaction",
                    reference_id=tx.id,
                    amount=effect,
                    created_at=tx.payment_date or tx.date,
                )

        movs = (
            MovimentacaoInvestimento.query.filter_by(user_id=user_id, conta_id=account_id)
            .order_by(MovimentacaoInvestimento.data_movimentacao.asc(), MovimentacaoInvestimento.id.asc())
            .all()
        )
        for mov in movs:
            if mov.tipo_movimentacao == "aplicacao":
                effect = -Decimal(str(mov.valor or 0))
            elif mov.tipo_movimentacao == "resgate":
                effect = Decimal(str(mov.valor or 0))
            else:
                effect = Decimal("0")

            if effect != 0:
                LedgerService.append_entry(
                    user_id=user_id,
                    account_id=account_id,
                    reference_type="backfill_investment_move",
                    reference_id=mov.id,
                    amount=effect,
                    created_at=datetime.combine(mov.data_movimentacao, datetime.min.time()),
                )

        if commit:
            db.session.commit()
        if rebuild:
            LedgerService.rebuild_account_balances(conta_id=account_id)

    @staticmethod
    def create_simulation_session(*, user_id: int, account_id: int, name: str = "Simulacao") -> SimulationSession:
        session = SimulationSession(
            user_id=user_id,
            account_id=account_id,
            name=name or "Simulacao",
            status="active",
        )
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def append_simulation_entry_for_session(
        *,
        simulation_session_id: int,
        reference_type: str,
        reference_id: Optional[int],
        amount,
        created_at: Optional[datetime] = None,
    ) -> SimulationLedgerEntry:
        session = SimulationSession.query.get(simulation_session_id)
        if not session:
            raise ValueError("Sessao de simulacao nao encontrada")
        if session.status != "active":
            raise ValueError("Sessao de simulacao nao esta ativa")

        entry = LedgerService.append_simulation_entry(
            simulation_session_id=simulation_session_id,
            user_id=session.user_id,
            account_id=session.account_id,
            reference_type=reference_type,
            reference_id=reference_id,
            amount=amount,
            created_at=created_at,
        )
        db.session.commit()
        return entry

    @staticmethod
    def get_simulation_balance(*, simulation_session_id: int) -> Decimal:
        session = SimulationSession.query.get(simulation_session_id)
        if not session:
            raise ValueError("Sessao de simulacao nao encontrada")

        base_balance = LedgerService.get_account_balance(user_id=session.user_id, account_id=session.account_id)
        simulation_total = (
            db.session.query(db.func.sum(SimulationLedgerEntry.amount))
            .filter_by(simulation_session_id=simulation_session_id)
            .scalar()
        )
        return LedgerService._to_decimal(base_balance + Decimal(str(simulation_total or 0)))

    @staticmethod
    def close_simulation_session(*, simulation_session_id: int):
        session = SimulationSession.query.get(simulation_session_id)
        if not session:
            raise ValueError("Sessao de simulacao nao encontrada")
        session.status = "closed"
        db.session.commit()

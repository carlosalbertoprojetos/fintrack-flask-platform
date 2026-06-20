from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from app import db
from app.models import Transaction
from services.closure_service import ClosureService
from services.ledger_service import LedgerService


class TransactionService:
    """Business rules for transaction lifecycle with immutable ledger support."""

    @staticmethod
    def _effective_date(tx: Transaction) -> datetime:
        return tx.payment_date or tx.due_date or tx.date or datetime.utcnow()

    @staticmethod
    def _calculate_effect(*, tx_type: str, amount, discount, paid: bool, is_saldo_inicial: bool = False) -> Decimal:
        # Lancamentos de saldo inicial nao movimentam o ledger: o valor ja e
        # representado pela coluna ``Conta.saldo_inicial`` (semente do saldo).
        # Eles existem apenas como receita visivel em relatorios.
        if is_saldo_inicial:
            return Decimal("0.00")

        if not paid:
            return Decimal("0.00")

        value = Decimal(str(amount or 0))
        discount_value = Decimal(str(discount or 0))

        if tx_type == "receita":
            return value
        return -(value - discount_value)

    @staticmethod
    def _ensure_period_open_for_payload(user_id: int, account_id: int, payload: Dict):
        effective_date = payload.get("payment_date") or payload.get("due_date") or payload.get("date")
        if effective_date:
            ClosureService.ensure_period_open(user_id=user_id, account_id=account_id, date_value=effective_date)

    @staticmethod
    def _validate_lookup_ownership(*, user_id: int, payload: Dict):
        from app.models import Category, Conta, Expense, PaymentMethod

        conta_id = payload.get("conta_id")
        conta = Conta.query.filter_by(id=conta_id, user_id=user_id).first()
        if conta is None:
            raise ValueError("Conta nao pertence ao usuario")

        category_id = payload.get("category_id")
        category = Category.query.filter_by(id=category_id, user_id=user_id).first()
        if category is None:
            raise ValueError("Categoria nao pertence ao usuario")

        expense_id = payload.get("expense_id")
        if expense_id:
            expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
            if expense is None:
                raise ValueError("Descricao nao pertence ao usuario")
            if expense.category_id and expense.category_id != category.id:
                raise ValueError("Descricao nao pertence a categoria selecionada")

        payment_method_id = payload.get("payment_method_id")
        if payment_method_id:
            payment_method = PaymentMethod.query.filter_by(id=payment_method_id, user_id=user_id).first()
            if payment_method is None:
                raise ValueError("Forma de pagamento nao pertence ao usuario")

    @staticmethod
    def create_transaction(*, user_id: int, payload: Dict) -> Transaction:
        conta_id = payload.get("conta_id")
        if not conta_id:
            raise ValueError("Conta obrigatoria para lancamento")

        TransactionService._validate_lookup_ownership(user_id=user_id, payload=payload)
        TransactionService._ensure_period_open_for_payload(user_id=user_id, account_id=conta_id, payload=payload)

        tx = Transaction(
            type=payload.get("type"),
            date=payload.get("date"),
            due_date=payload.get("due_date"),
            payment_date=payload.get("payment_date"),
            amount=float(payload.get("amount") or 0),
            discount=float(payload.get("discount") or 0),
            paid=bool(payload.get("paid")),
            category_id=payload.get("category_id"),
            expense_id=payload.get("expense_id"),
            description=payload.get("description"),
            payment_method_id=payload.get("payment_method_id"),
            recurrence=payload.get("recurrence") or "none",
            details=payload.get("details"),
            notes=payload.get("notes"),
            is_saldo_inicial=bool(payload.get("is_saldo_inicial")),
            user_id=user_id,
            conta_id=conta_id,
        )

        db.session.add(tx)
        db.session.flush()

        effect = TransactionService._calculate_effect(
            tx_type=tx.type,
            amount=tx.amount,
            discount=tx.discount,
            paid=tx.paid,
            is_saldo_inicial=tx.is_saldo_inicial,
        )
        if effect != 0:
            LedgerService.append_entry(
                user_id=user_id,
                account_id=tx.conta_id,
                reference_type="transaction_create",
                reference_id=tx.id,
                amount=effect,
                created_at=TransactionService._effective_date(tx),
            )

        db.session.commit()
        LedgerService.rebuild_account_balances(conta_id=tx.conta_id)
        return tx

    @staticmethod
    def update_transaction(*, user_id: int, tx: Transaction, payload: Dict) -> Transaction:
        if tx.user_id != user_id:
            raise ValueError("Transacao nao pertence ao usuario")

        ClosureService.ensure_period_open(user_id=user_id, account_id=tx.conta_id, date_value=TransactionService._effective_date(tx))
        TransactionService._validate_lookup_ownership(user_id=user_id, payload=payload)

        old_account_id = tx.conta_id
        old_effect = TransactionService._calculate_effect(
            tx_type=tx.type,
            amount=tx.amount,
            discount=tx.discount,
            paid=tx.paid,
            is_saldo_inicial=tx.is_saldo_inicial,
        )

        tx.type = payload.get("type")
        tx.date = payload.get("date")
        tx.due_date = payload.get("due_date")
        tx.payment_date = payload.get("payment_date")
        tx.amount = float(payload.get("amount") or 0)
        tx.discount = float(payload.get("discount") or 0)
        tx.paid = bool(payload.get("paid"))
        tx.category_id = payload.get("category_id")
        tx.expense_id = payload.get("expense_id")
        tx.description = payload.get("description")
        tx.payment_method_id = payload.get("payment_method_id")
        tx.recurrence = payload.get("recurrence") or "none"
        tx.details = payload.get("details")
        tx.notes = payload.get("notes")
        tx.conta_id = payload.get("conta_id")
        if "is_saldo_inicial" in payload:
            tx.is_saldo_inicial = bool(payload.get("is_saldo_inicial"))

        TransactionService._ensure_period_open_for_payload(user_id=user_id, account_id=tx.conta_id, payload=payload)

        db.session.flush()

        new_effect = TransactionService._calculate_effect(
            tx_type=tx.type,
            amount=tx.amount,
            discount=tx.discount,
            paid=tx.paid,
            is_saldo_inicial=tx.is_saldo_inicial,
        )

        if old_account_id == tx.conta_id:
            delta = new_effect - old_effect
            if delta != 0:
                LedgerService.append_entry(
                    user_id=user_id,
                    account_id=tx.conta_id,
                    reference_type="transaction_adjustment",
                    reference_id=tx.id,
                    amount=delta,
                    created_at=TransactionService._effective_date(tx),
                )
        else:
            if old_effect != 0:
                LedgerService.append_entry(
                    user_id=user_id,
                    account_id=old_account_id,
                    reference_type="transaction_transfer_out",
                    reference_id=tx.id,
                    amount=-old_effect,
                    created_at=datetime.utcnow(),
                )
            if new_effect != 0:
                LedgerService.append_entry(
                    user_id=user_id,
                    account_id=tx.conta_id,
                    reference_type="transaction_transfer_in",
                    reference_id=tx.id,
                    amount=new_effect,
                    created_at=TransactionService._effective_date(tx),
                )

        db.session.commit()
        LedgerService.rebuild_account_balances(conta_id=old_account_id)
        if tx.conta_id != old_account_id:
            LedgerService.rebuild_account_balances(conta_id=tx.conta_id)
        return tx

    @staticmethod
    def delete_transaction(*, user_id: int, tx: Transaction):
        if tx.user_id != user_id:
            raise ValueError("Transacao nao pertence ao usuario")

        ClosureService.ensure_period_open(user_id=user_id, account_id=tx.conta_id, date_value=TransactionService._effective_date(tx))

        effect = TransactionService._calculate_effect(
            tx_type=tx.type,
            amount=tx.amount,
            discount=tx.discount,
            paid=tx.paid,
            is_saldo_inicial=tx.is_saldo_inicial,
        )
        account_id = tx.conta_id

        if effect != 0:
            LedgerService.append_entry(
                user_id=user_id,
                account_id=account_id,
                reference_type="transaction_delete",
                reference_id=tx.id,
                amount=-effect,
                created_at=datetime.utcnow(),
            )

        db.session.delete(tx)
        db.session.commit()
        LedgerService.rebuild_account_balances(conta_id=account_id)

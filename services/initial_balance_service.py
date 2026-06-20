"""Servico responsavel por refletir o saldo inicial de uma conta como receita.

Sempre que uma conta possui ``saldo_inicial`` informado, mantemos uma receita
"espelho" (categoria *Outros*, descricao *Saldo inicial*) para que o valor
apareca nos relatorios e calculos baseados em transacoes.

Para evitar contagem dupla de saldo, essa receita e marcada com
``Transaction.is_saldo_inicial = True`` e NAO movimenta o ledger imovel: o
valor do saldo continua sendo a semente ``Conta.saldo_inicial``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app import db
from app.models import Category, Conta, Expense, Transaction
from services.transaction_service import TransactionService

CATEGORIA_SALDO_INICIAL = "Outros"
DESCRICAO_SALDO_INICIAL = "Saldo inicial"


class InitialBalanceService:
    EPSILON = 0.005

    @staticmethod
    def _get_or_create_outros_category(user_id: int) -> Category:
        category = (
            Category.query.filter_by(user_id=user_id, name=CATEGORIA_SALDO_INICIAL, type="receita")
            .first()
        )
        if category is None:
            category = Category(
                user_id=user_id,
                name=CATEGORIA_SALDO_INICIAL,
                type="receita",
                exclusive=False,
                icon="bx-plus",
                color="#6c757d",
            )
            db.session.add(category)
            db.session.flush()
        return category

    @staticmethod
    def _find_saldo_inicial_expense(user_id: int, category_id: int) -> Optional[Expense]:
        return (
            Expense.query.filter_by(
                user_id=user_id,
                name=DESCRICAO_SALDO_INICIAL,
                category_id=category_id,
            ).first()
        )

    @staticmethod
    def find_existing(*, user_id: int, conta_id: int) -> Optional[Transaction]:
        return (
            Transaction.query.filter_by(
                user_id=user_id,
                conta_id=conta_id,
                is_saldo_inicial=True,
            )
            .order_by(Transaction.id.asc())
            .first()
        )

    @staticmethod
    def _build_payload(*, conta: Conta, category: Category, expense_id, valor: float) -> dict:
        today = datetime.now()
        return {
            "type": "receita",
            "date": today,
            "due_date": None,
            "payment_date": today,
            "amount": float(valor),
            "discount": 0.0,
            "paid": True,
            "category_id": category.id,
            "expense_id": expense_id,
            "description": DESCRICAO_SALDO_INICIAL,
            "payment_method_id": None,
            "recurrence": "none",
            "details": f"Saldo Inicial da conta {conta.nome}",
            "notes": None,
            "conta_id": conta.id,
            "is_saldo_inicial": True,
        }

    @staticmethod
    def sync_for_account(*, user_id: int, conta: Conta) -> Optional[Transaction]:
        """Cria, atualiza ou remove a receita de saldo inicial da conta.

        Deve ser chamado depois que ``conta.saldo_inicial`` ja foi persistido.
        Retorna a transacao resultante (ou ``None`` quando removida).
        """
        valor = float(conta.saldo_inicial or 0.0)
        existing = InitialBalanceService.find_existing(user_id=user_id, conta_id=conta.id)

        # Saldo inicial zerado (ou negativo): nao mantemos receita espelho.
        if valor <= InitialBalanceService.EPSILON:
            if existing is not None:
                TransactionService.delete_transaction(user_id=user_id, tx=existing)
            return None

        category = InitialBalanceService._get_or_create_outros_category(user_id)
        expense = InitialBalanceService._find_saldo_inicial_expense(user_id, category.id)
        expense_id = expense.id if expense else None

        payload = InitialBalanceService._build_payload(
            conta=conta,
            category=category,
            expense_id=expense_id,
            valor=valor,
        )

        if existing is None:
            return TransactionService.create_transaction(user_id=user_id, payload=payload)

        # Mantemos a data original de pagamento da receita ja existente para
        # nao reescrever historico a cada edicao da conta.
        payload["date"] = existing.date or payload["date"]
        payload["payment_date"] = existing.payment_date or payload["payment_date"]
        return TransactionService.update_transaction(user_id=user_id, tx=existing, payload=payload)

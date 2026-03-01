from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from app import db
from app.models import Investimento, MovimentacaoInvestimento
from services.closure_service import ClosureService
from services.ledger_service import LedgerService


class InvestmentService:
    """Investment lifecycle with ledger side effects."""

    @staticmethod
    def _account_effect(tipo_movimentacao: str, valor) -> Decimal:
        value = Decimal(str(valor or 0))
        if tipo_movimentacao == "aplicacao":
            return -value
        if tipo_movimentacao == "resgate":
            return value
        return Decimal("0")

    @staticmethod
    def recalculate_movement_balances(*, investimento_id: int):
        investimento = Investimento.query.get(investimento_id)
        if not investimento:
            return False

        saldo = Decimal("0")
        movimentacoes = (
            MovimentacaoInvestimento.query.filter_by(investimento_id=investimento_id)
            .order_by(MovimentacaoInvestimento.data_movimentacao.asc(), MovimentacaoInvestimento.id.asc())
            .all()
        )
        for mov in movimentacoes:
            mov.saldo_anterior = float(saldo)
            if mov.tipo_movimentacao == "aplicacao":
                saldo += Decimal(str(mov.valor))
            elif mov.tipo_movimentacao == "resgate":
                saldo -= Decimal(str(mov.valor))
            else:
                saldo += Decimal(str(mov.valor))
            mov.saldo_atual = float(saldo)
            db.session.add(mov)

        db.session.flush()
        return True

    @staticmethod
    def create_investment(*, user_id: int, tipo_investimento_id: int, conta_id: int) -> Investimento:
        inv = Investimento(tipo_investimento_id=tipo_investimento_id)
        db.session.add(inv)
        db.session.flush()

        initial_move = MovimentacaoInvestimento(
            investimento_id=inv.id,
            data_movimentacao=date.today(),
            tipo_movimentacao="aplicacao",
            valor=0.0,
            saldo_anterior=0.0,
            saldo_atual=0.0,
            observacoes="Investimento criado - aguardando primeira aplicacao",
            user_id=user_id,
            conta_id=conta_id,
        )
        db.session.add(initial_move)
        db.session.commit()
        return inv

    @staticmethod
    def create_movement(
        *,
        user_id: int,
        investimento: Investimento,
        conta_id: int,
        data_movimentacao,
        tipo_movimentacao: str,
        valor,
        observacoes: str,
    ) -> MovimentacaoInvestimento:
        ClosureService.ensure_period_open(
            user_id=user_id,
            account_id=conta_id,
            date_value=data_movimentacao,
        )

        saldo_anterior = Decimal(str(investimento.saldo_atual or 0))
        value = Decimal(str(valor or 0))

        if tipo_movimentacao == "aplicacao":
            saldo_novo = saldo_anterior + value
        elif tipo_movimentacao == "resgate":
            saldo_novo = saldo_anterior - value
        else:
            saldo_novo = saldo_anterior + value

        mov = MovimentacaoInvestimento(
            investimento_id=investimento.id,
            data_movimentacao=data_movimentacao,
            tipo_movimentacao=tipo_movimentacao,
            valor=float(value),
            saldo_anterior=float(saldo_anterior),
            saldo_atual=float(saldo_novo),
            observacoes=observacoes,
            user_id=user_id,
            conta_id=conta_id,
        )
        db.session.add(mov)
        db.session.flush()

        effect = InvestmentService._account_effect(tipo_movimentacao=tipo_movimentacao, valor=value)
        if effect != 0:
            LedgerService.append_entry(
                user_id=user_id,
                account_id=conta_id,
                reference_type="investment_movement_create",
                reference_id=mov.id,
                amount=effect,
                created_at=datetime.combine(data_movimentacao, datetime.min.time()),
            )

        db.session.commit()
        LedgerService.rebuild_account_balances(conta_id=conta_id)
        return mov

    @staticmethod
    def update_movement(
        *,
        user_id: int,
        mov: MovimentacaoInvestimento,
        data_movimentacao,
        valor,
        observacoes,
    ) -> MovimentacaoInvestimento:
        if mov.user_id != user_id:
            raise ValueError("Movimentacao nao pertence ao usuario")

        ClosureService.ensure_period_open(
            user_id=user_id,
            account_id=mov.conta_id,
            date_value=mov.data_movimentacao,
        )
        ClosureService.ensure_period_open(
            user_id=user_id,
            account_id=mov.conta_id,
            date_value=data_movimentacao,
        )

        old_effect = InvestmentService._account_effect(mov.tipo_movimentacao, mov.valor)

        mov.data_movimentacao = data_movimentacao
        mov.valor = float(valor)
        mov.observacoes = observacoes

        db.session.flush()
        InvestmentService.recalculate_movement_balances(investimento_id=mov.investimento_id)

        new_effect = InvestmentService._account_effect(mov.tipo_movimentacao, mov.valor)
        delta = new_effect - old_effect

        if delta != 0:
            LedgerService.append_entry(
                user_id=user_id,
                account_id=mov.conta_id,
                reference_type="investment_movement_adjustment",
                reference_id=mov.id,
                amount=delta,
                created_at=datetime.combine(mov.data_movimentacao, datetime.min.time()),
            )

        db.session.commit()
        LedgerService.rebuild_account_balances(conta_id=mov.conta_id)
        return mov

    @staticmethod
    def delete_movement(*, user_id: int, mov: MovimentacaoInvestimento):
        if mov.user_id != user_id:
            raise ValueError("Movimentacao nao pertence ao usuario")

        ClosureService.ensure_period_open(
            user_id=user_id,
            account_id=mov.conta_id,
            date_value=mov.data_movimentacao,
        )

        effect = InvestmentService._account_effect(mov.tipo_movimentacao, mov.valor)
        conta_id = mov.conta_id
        investimento_id = mov.investimento_id

        if effect != 0:
            LedgerService.append_entry(
                user_id=user_id,
                account_id=conta_id,
                reference_type="investment_movement_delete",
                reference_id=mov.id,
                amount=-effect,
                created_at=datetime.utcnow(),
            )

        db.session.delete(mov)
        db.session.flush()
        InvestmentService.recalculate_movement_balances(investimento_id=investimento_id)
        db.session.commit()
        LedgerService.rebuild_account_balances(conta_id=conta_id)

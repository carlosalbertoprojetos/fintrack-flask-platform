from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import MovimentacaoInvestimentoForm
from app.models import Conta, Investimento, MovimentacaoInvestimento, TipoInvestimento
from services.investment_service import InvestmentService


investimento_bp = Blueprint("investimento", __name__)


def get_current_conta():
    """Retorna a conta selecionada em sessao, com fallback para a primeira conta do usuario."""
    contas = Conta.query.filter_by(user_id=current_user.id).all()
    if not contas:
        return None

    conta_id = session.get("last_conta_id")
    if not conta_id:
        conta_id = contas[0].id
        session["last_conta_id"] = conta_id

    conta = Conta.query.filter_by(id=conta_id, user_id=current_user.id).first()
    if conta:
        return conta

    session["last_conta_id"] = contas[0].id
    return contas[0]


def _user_investment_or_404(investimento_id: int):
    investimento = (
        Investimento.query.join(MovimentacaoInvestimento)
        .filter(
            Investimento.id == investimento_id,
            MovimentacaoInvestimento.user_id == current_user.id,
        )
        .first_or_404()
    )
    return investimento


@investimento_bp.route("/investimentos", methods=["GET"])
@login_required
def investimentos():
    conta_filter = request.args.get("conta_id", type=int)
    if not conta_filter:
        conta_atual = get_current_conta()
        if conta_atual:
            conta_filter = conta_atual.id

    investimentos_query = (
        Investimento.query.join(MovimentacaoInvestimento)
        .filter(MovimentacaoInvestimento.user_id == current_user.id)
        .distinct()
    )
    if conta_filter:
        investimentos_query = investimentos_query.filter(MovimentacaoInvestimento.conta_id == conta_filter)

    investimentos = investimentos_query.all()
    tipos_investimento = TipoInvestimento.query.filter_by(user_id=current_user.id, ativo=True).all()

    conta_info = None
    if conta_filter:
        conta = Conta.query.filter_by(id=conta_filter, user_id=current_user.id).first()
        if conta:
            conta_info = {"id": conta.id, "nome": conta.nome, "saldo_atual": conta.saldo_atual or 0.0}

    return render_template(
        "list_investments.html",
        investimentos=investimentos,
        tipos_investimento=tipos_investimento,
        conta_filter=conta_filter,
        conta_info=conta_info,
    )


@investimento_bp.route("/investimentos/novo", methods=["POST"])
@login_required
def novo_investimento():
    tipo_investimento_id = request.form.get("tipo_investimento_id", type=int)
    conta_atual = get_current_conta()
    if not conta_atual:
        flash("Voce precisa ter pelo menos uma conta cadastrada.", "warning")
        return redirect(url_for("investimento.investimentos"))

    try:
        InvestmentService.create_investment(
            user_id=current_user.id,
            tipo_investimento_id=tipo_investimento_id,
            conta_id=conta_atual.id,
        )
        flash("Investimento criado com sucesso!", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(url_for("investimento.investimentos"))


@investimento_bp.route("/investimento/<int:investimento_id>/movimentacoes", methods=["GET", "POST"])
@login_required
def listar_movimentacoes(investimento_id):
    investimento = _user_investment_or_404(investimento_id)
    form = MovimentacaoInvestimentoForm()
    InvestmentService.recalculate_movement_balances(investimento_id=investimento_id)

    movimentacoes = (
        MovimentacaoInvestimento.query.filter_by(
            investimento_id=investimento_id,
            user_id=current_user.id,
        )
        .order_by(MovimentacaoInvestimento.id.desc())
        .all()
    )

    conta_atual = get_current_conta()
    conta_info = {
        "nome": conta_atual.nome if conta_atual else "Nenhuma conta encontrada",
        "saldo_atual": (conta_atual.saldo_atual or 0.0) if conta_atual else 0.0,
    }

    if form.validate_on_submit():
        if not conta_atual:
            flash("Nenhuma conta disponivel para movimentacoes.", "warning")
            return redirect(url_for("investimento.listar_movimentacoes", investimento_id=investimento.id))

        if form.tipo_movimentacao.data == "aplicacao" and float(form.valor.data or 0) > float(conta_info["saldo_atual"]):
            flash(
                f"O valor da aplicacao (R$ {form.valor.data:.2f}) nao pode ser maior que o saldo da conta (R$ {conta_info['saldo_atual']:.2f}).",
                "danger",
            )
            return redirect(url_for("investimento.listar_movimentacoes", investimento_id=investimento.id))

        try:
            InvestmentService.create_movement(
                user_id=current_user.id,
                investimento=investimento,
                conta_id=conta_atual.id,
                data_movimentacao=form.data_movimentacao.data,
                tipo_movimentacao=form.tipo_movimentacao.data,
                valor=form.valor.data,
                observacoes=form.observacoes.data,
            )
            flash(f"Movimentacao de {form.tipo_movimentacao.data} registrada com sucesso!", "success")
            return redirect(url_for("investimento.listar_movimentacoes", investimento_id=investimento.id))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    today = date.today()
    saldo_investimento = investimento.saldo_atual
    primeiro_resgate_zero = None
    for mov in movimentacoes:
        if mov.tipo_movimentacao == "resgate" and mov.saldo_atual == 0.0:
            primeiro_resgate_zero = mov.id
            break

    return render_template(
        "list_movimentacoes_investimento.html",
        investimento=investimento,
        movimentacoes=movimentacoes,
        form=form,
        conta_info=conta_info,
        saldo_investimento=saldo_investimento,
        primeiro_resgate_zero=primeiro_resgate_zero,
        today=today,
    )


@investimento_bp.route("/investimento/<int:investimento_id>/recalcular-saldos", methods=["POST"])
@login_required
def recalcular_saldos_investimento(investimento_id):
    investimento = _user_investment_or_404(investimento_id)
    if InvestmentService.recalculate_movement_balances(investimento_id=investimento.id):
        db.session.commit()
        flash("Saldos das movimentacoes recalculados com sucesso!", "success")
    else:
        flash("Erro ao recalcular saldos das movimentacoes.", "danger")

    return redirect(url_for("investimento.listar_movimentacoes", investimento_id=investimento.id))


@investimento_bp.route("/investimento/<int:investimento_id>/excluir", methods=["POST"])
@login_required
def excluir_investimento(investimento_id):
    investimento = _user_investment_or_404(investimento_id)
    db.session.delete(investimento)
    db.session.commit()
    flash("Investimento excluido com sucesso!", "success")
    return redirect(url_for("investimento.investimentos"))


@investimento_bp.route("/movimentacao/<int:movimentacao_id>/editar", methods=["GET", "POST"])
@login_required
def editar_movimentacao(movimentacao_id):
    movimentacao = MovimentacaoInvestimento.query.filter_by(id=movimentacao_id, user_id=current_user.id).first_or_404()
    investimento = _user_investment_or_404(movimentacao.investimento_id)
    form = MovimentacaoInvestimentoForm(obj=movimentacao)

    conta_info = None
    conta_atual = get_current_conta()
    if conta_atual:
        max_edit_value = conta_atual.saldo_atual or 0.0
        if movimentacao.tipo_movimentacao == "aplicacao" and movimentacao.conta_id == conta_atual.id:
            max_edit_value += movimentacao.valor or 0.0
        conta_info = {
            "nome": conta_atual.nome,
            "saldo_atual": conta_atual.saldo_atual or 0.0,
            "max_edit_value": max_edit_value,
        }

    if form.validate_on_submit():
        try:
            InvestmentService.update_movement(
                user_id=current_user.id,
                mov=movimentacao,
                data_movimentacao=form.data_movimentacao.data,
                valor=form.valor.data,
                observacoes=form.observacoes.data,
            )
            flash("Movimentacao editada com sucesso!", "success")
            return redirect(url_for("investimento.listar_movimentacoes", investimento_id=movimentacao.investimento_id))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    return render_template(
        "edit_movimentacao_investimento.html",
        form=form,
        movimentacao=movimentacao,
        investimento=investimento,
        conta_info=conta_info,
    )


@investimento_bp.route("/movimentacao/<int:movimentacao_id>/excluir", methods=["POST"])
@login_required
def excluir_movimentacao(movimentacao_id):
    movimentacao = MovimentacaoInvestimento.query.filter_by(id=movimentacao_id, user_id=current_user.id).first_or_404()
    investimento_id = movimentacao.investimento_id

    try:
        InvestmentService.delete_movement(user_id=current_user.id, mov=movimentacao)
        flash("Movimentacao excluida com sucesso!", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(url_for("investimento.listar_movimentacoes", investimento_id=investimento_id))

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.forms import ContaForm
from app.models import Conta, TipoConta
from services.initial_balance_service import InitialBalanceService
from services.ledger_service import LedgerService


conta_bp = Blueprint('conta', __name__)


def _user_conta_or_404(conta_id: int):
    return Conta.query.filter_by(id=conta_id, user_id=current_user.id).first_or_404()


@conta_bp.route('/contas', methods=['GET'])
@login_required
def listar_contas():
    contas = Conta.query.filter_by(user_id=current_user.id).all()

    for conta in contas:
        conta.tem_transacoes = bool(conta.transactions)
        conta.tem_movimentacoes_investimento = bool(conta.movimentacoes_investimento)
        conta.tem_lancamentos = conta.tem_transacoes or conta.tem_movimentacoes_investimento

    return render_template('list_accounts.html', contas=contas)


@conta_bp.route('/contas/add', methods=['GET', 'POST'])
@login_required
def add_conta():
    form = ContaForm()
    tipos_conta = TipoConta.query.filter_by(user_id=current_user.id, ativo=True).all()
    form.tipo_id.choices = [(t.id, t.nome) for t in tipos_conta]

    if not form.saldo_inicial.data:
        form.saldo_inicial.data = 0.0

    if form.validate_on_submit():
        conta = Conta(
            nome=form.nome.data,
            tipo_id=form.tipo_id.data,
            saldo_inicial=form.saldo_inicial.data or 0.0,
            saldo_atual=0.0,
            user_id=current_user.id,
        )
        db.session.add(conta)
        db.session.commit()
        InitialBalanceService.sync_for_account(user_id=current_user.id, conta=conta)
        LedgerService.rebuild_account_balances(conta_id=conta.id)
        flash('Conta criada com sucesso!', 'success')
        return redirect(url_for('conta.listar_contas'))

    return render_template('add_edit_conta.html', form=form, title='Adicionar Conta')


@conta_bp.route('/conta/editar/<int:conta_id>', methods=['GET', 'POST'])
@login_required
def editar_conta(conta_id):
    conta = _user_conta_or_404(conta_id)

    form = ContaForm(obj=conta)
    tipos_conta = TipoConta.query.filter_by(user_id=current_user.id, ativo=True).all()
    form.tipo_id.choices = [(t.id, t.nome) for t in tipos_conta]

    if form.validate_on_submit():
        conta.nome = form.nome.data
        conta.tipo_id = form.tipo_id.data
        conta.saldo_inicial = form.saldo_inicial.data or 0.0
        db.session.commit()
        InitialBalanceService.sync_for_account(user_id=current_user.id, conta=conta)
        LedgerService.rebuild_account_balances(conta_id=conta.id)
        flash('Conta atualizada com sucesso!', 'success')
        return redirect(url_for('conta.listar_contas'))

    if conta.tipo:
        form.tipo_id.data = conta.tipo_id

    return render_template('add_edit_conta.html', form=form, title=f'Editar Conta: {conta.nome}', conta=conta)


@conta_bp.route('/conta/editar-nome/<int:conta_id>', methods=['POST'])
@login_required
def editar_nome_inline(conta_id):
    conta = _user_conta_or_404(conta_id)


    novo_nome = request.json.get('nome')
    if not novo_nome or len(novo_nome.strip()) == 0:
        return jsonify({'success': False, 'message': 'Nome nao pode estar vazio.'}), 400

    if len(novo_nome) > 100:
        return jsonify({'success': False, 'message': 'Nome deve ter no maximo 100 caracteres.'}), 400

    try:
        conta.nome = novo_nome.strip()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Nome atualizado com sucesso!'})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao atualizar nome.'}), 500


@conta_bp.route('/conta/excluir/<int:conta_id>', methods=['POST'])
@login_required
def excluir_conta(conta_id):
    conta = _user_conta_or_404(conta_id)

    total_contas = Conta.query.filter_by(user_id=current_user.id).count()
    if total_contas <= 1:
        flash('Nao e possivel excluir a ultima conta. Voce deve ter pelo menos uma conta.', 'warning')
        return redirect(url_for('conta.listar_contas'))

    if conta.movimentacoes_investimento:
        flash('Nao e possivel excluir conta com movimentacoes de investimento vinculadas.', 'warning')
        return redirect(url_for('conta.listar_contas'))

    # A receita automatica de saldo inicial nao deve impedir a exclusao da conta.
    transacoes_relevantes = [t for t in conta.transactions if not t.is_saldo_inicial]
    if transacoes_relevantes:
        flash('Nao e possivel excluir conta com transacoes vinculadas.', 'warning')
        return redirect(url_for('conta.listar_contas'))

    saldo_inicial_tx = InitialBalanceService.find_existing(user_id=current_user.id, conta_id=conta.id)
    if saldo_inicial_tx is not None:
        db.session.delete(saldo_inicial_tx)

    db.session.delete(conta)
    db.session.commit()
    flash('Conta excluida com sucesso!', 'success')
    return redirect(url_for('conta.listar_contas'))

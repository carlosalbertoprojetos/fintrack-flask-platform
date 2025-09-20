from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Conta, TipoConta
from app.forms import ContaForm

conta_bp = Blueprint('conta', __name__)

@conta_bp.route('/contas', methods=['GET'])
@login_required
def listar_contas():
    contas = Conta.query.filter_by(user_id=current_user.id).all()
    
    # Verificar se cada conta tem lançamentos (transações ou movimentações de investimento)
    for conta in contas:
        # Verificar transações
        conta.tem_transacoes = bool(conta.transactions)
        # Verificar movimentações de investimento
        conta.tem_movimentacoes_investimento = bool(conta.movimentacoes_investimento)
        # Conta tem lançamentos se tiver transações OU movimentações de investimento
        conta.tem_lancamentos = conta.tem_transacoes or conta.tem_movimentacoes_investimento
    
    return render_template('list_accounts.html', contas=contas)


@conta_bp.route('/contas/add', methods=['GET', 'POST'])
@login_required
def add_conta():
    form = ContaForm()
    tipos_conta = TipoConta.query.filter_by(user_id=current_user.id, ativo=True).all()
    form.tipo_id.choices = [(t.id, t.nome) for t in tipos_conta]
    
    if form.validate_on_submit():
        conta = Conta(
            nome=form.nome.data,
            tipo_id=form.tipo_id.data,
            saldo_inicial=form.saldo_inicial.data or 0.0,
            user_id=current_user.id
        )
        db.session.add(conta)
        db.session.commit()
        flash('Conta criada com sucesso!', 'success')
        return redirect(url_for('conta.listar_contas'))
    
    return render_template('add_edit_conta.html', form=form, title='Nova Conta')

@conta_bp.route('/conta/editar/<int:conta_id>', methods=['GET', 'POST'])
@login_required
def editar_conta(conta_id):
    conta = Conta.query.get_or_404(conta_id)
    if conta.user_id != current_user.id:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('conta.listar_contas'))
    
    form = ContaForm(obj=conta)
    tipos_conta = TipoConta.query.filter_by(user_id=current_user.id, ativo=True).all()
    form.tipo_id.choices = [(t.id, t.nome) for t in tipos_conta]
    
    if form.validate_on_submit():
        conta.nome = form.nome.data
        conta.tipo_id = form.tipo_id.data
        conta.saldo_inicial = form.saldo_inicial.data or 0.0
        db.session.commit()
        flash('Conta atualizada com sucesso!', 'success')
        return redirect(url_for('conta.listar_contas'))
    
    # Definir o valor atual do tipo no formulário
    if conta.tipo:
        form.tipo_id.data = conta.tipo_id
    
    return render_template('add_edit_conta.html', form=form, title='Editar Conta', conta=conta)

@conta_bp.route('/conta/editar-nome/<int:conta_id>', methods=['POST'])
@login_required
def editar_nome_inline(conta_id):
    conta = Conta.query.get_or_404(conta_id)
    
    if conta.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Acesso não autorizado.'}), 403
    
    novo_nome = request.json.get('nome')
    if not novo_nome or len(novo_nome.strip()) == 0:
        return jsonify({'success': False, 'message': 'Nome não pode estar vazio.'}), 400
    
    if len(novo_nome) > 100:
        return jsonify({'success': False, 'message': 'Nome deve ter no máximo 100 caracteres.'}), 400
    
    try:
        conta.nome = novo_nome.strip()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Nome atualizado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao atualizar nome.'}), 500

@conta_bp.route('/conta/excluir/<int:conta_id>', methods=['POST'])
@login_required
def excluir_conta(conta_id):
    conta = Conta.query.get_or_404(conta_id)
    if conta.user_id != current_user.id:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('conta.listar_contas'))
    
    # Verificar se é a última conta do usuário
    total_contas = Conta.query.filter_by(user_id=current_user.id).count()
    if total_contas <= 1:
        flash('Não é possível excluir a última conta. Você deve ter pelo menos uma conta.', 'warning')
        return redirect(url_for('conta.listar_contas'))
    
    # Verificar se há movimentações de investimento vinculadas
    if conta.movimentacoes_investimento:
        flash('Não é possível excluir uma conta que possui movimentações de investimento vinculadas. Exclua as movimentações primeiro.', 'warning')
        return redirect(url_for('conta.listar_contas'))
    
    # Verificar se há transações vinculadas
    if conta.transactions:
        flash('Não é possível excluir uma conta que possui transações vinculadas. Exclua as transações primeiro.', 'warning')
        return redirect(url_for('conta.listar_contas'))
    
    db.session.delete(conta)
    db.session.commit()
    flash('Conta excluída com sucesso!', 'success')
    return redirect(url_for('conta.listar_contas')) 
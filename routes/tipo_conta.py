from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import TipoConta
from app.forms import TipoContaForm

tipo_conta_bp = Blueprint('tipo_conta', __name__)

def _user_tipo_conta_or_404(item_id: int):
    return TipoConta.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()

@tipo_conta_bp.route('/tipos-conta', methods=['GET'])
@login_required
def listar_tipos_conta():
    tipos_conta = TipoConta.query.filter_by(user_id=current_user.id).order_by(TipoConta.nome).all()
    return render_template('list_tipos_conta.html', tipos_conta=tipos_conta)

@tipo_conta_bp.route('/tipo-conta/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo_conta():
    form = TipoContaForm()
    
    if form.validate_on_submit():
        tipo_conta = TipoConta(
            nome=form.nome.data,
            descricao=form.descricao.data,
            ativo=form.ativo.data,
            user_id=current_user.id
        )
        db.session.add(tipo_conta)
        db.session.commit()
        flash('Tipo de conta criado com sucesso!', 'success')
        return redirect(url_for('tipo_conta.listar_tipos_conta'))
    
    return render_template('add_edit_tipo_conta.html', form=form, title='Adicionar Tipo de Conta')

@tipo_conta_bp.route('/tipo-conta/editar/<int:tipo_id>', methods=['GET', 'POST'])
@login_required
def editar_tipo_conta(tipo_id):
    tipo_conta = _user_tipo_conta_or_404(tipo_id)
    
    if tipo_conta.user_id != current_user.id:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('tipo_conta.listar_tipos_conta'))
    
    form = TipoContaForm(obj=tipo_conta)
    
    if form.validate_on_submit():
        tipo_conta.nome = form.nome.data
        tipo_conta.descricao = form.descricao.data
        tipo_conta.ativo = form.ativo.data
        db.session.commit()
        flash('Tipo de conta atualizado com sucesso!', 'success')
        return redirect(url_for('tipo_conta.listar_tipos_conta'))
    
    return render_template('add_edit_tipo_conta.html', form=form, title=f'Editar Tipo de Conta: {tipo_conta.nome}')

@tipo_conta_bp.route('/tipo-conta/excluir/<int:tipo_id>', methods=['POST'])
@login_required
def excluir_tipo_conta(tipo_id):
    tipo_conta = _user_tipo_conta_or_404(tipo_id)
    
    if tipo_conta.user_id != current_user.id:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('tipo_conta.listar_tipos_conta'))
    
    db.session.delete(tipo_conta)
    db.session.commit()
    flash('Tipo de conta excluído com sucesso!', 'success')
    return redirect(url_for('tipo_conta.listar_tipos_conta'))


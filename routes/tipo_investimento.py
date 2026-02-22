from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import TipoInvestimento
from app.forms import TipoInvestimentoForm

tipo_investimento_bp = Blueprint('tipo_investimento', __name__)

@tipo_investimento_bp.route('/tipos-investimento', methods=['GET'])
@login_required
def listar_tipos_investimento():
    tipos_investimento = TipoInvestimento.query.filter_by(user_id=current_user.id).order_by(TipoInvestimento.nome).all()
    return render_template('list_tipos_investimento.html', tipos_investimento=tipos_investimento)

@tipo_investimento_bp.route('/tipo-investimento/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo_investimento():
    form = TipoInvestimentoForm()
    
    if form.validate_on_submit():
        tipo_investimento = TipoInvestimento(
            nome=form.nome.data,
            descricao=form.descricao.data,
            ativo=form.ativo.data,
            user_id=current_user.id
        )
        db.session.add(tipo_investimento)
        db.session.commit()
        flash('Tipo de investimento criado com sucesso!', 'success')
        return redirect(url_for('tipo_investimento.listar_tipos_investimento'))
    
    return render_template('add_edit_tipo_investimento.html', form=form, title='Adicionar Tipo de Investimento')

@tipo_investimento_bp.route('/tipo-investimento/editar/<int:tipo_id>', methods=['GET', 'POST'])
@login_required
def editar_tipo_investimento(tipo_id):
    tipo_investimento = TipoInvestimento.query.get_or_404(tipo_id)
    
    if tipo_investimento.user_id != current_user.id:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('tipo_investimento.listar_tipos_investimento'))
    
    form = TipoInvestimentoForm(obj=tipo_investimento)
    
    if form.validate_on_submit():
        tipo_investimento.nome = form.nome.data
        tipo_investimento.descricao = form.descricao.data
        tipo_investimento.ativo = form.ativo.data
        db.session.commit()
        flash('Tipo de investimento atualizado com sucesso!', 'success')
        return redirect(url_for('tipo_investimento.listar_tipos_investimento'))
    
    return render_template('add_edit_tipo_investimento.html', form=form, title=f'Editar Tipo de Investimento: {tipo_investimento.nome}')

@tipo_investimento_bp.route('/tipo-investimento/editar-nome/<int:tipo_id>', methods=['POST'])
@login_required
def editar_nome_inline(tipo_id):
    tipo_investimento = TipoInvestimento.query.get_or_404(tipo_id)
    
    if tipo_investimento.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Acesso não autorizado.'}), 403
    
    novo_nome = request.json.get('nome')
    if not novo_nome or len(novo_nome.strip()) == 0:
        return jsonify({'success': False, 'message': 'Nome não pode estar vazio.'}), 400
    
    if len(novo_nome) > 100:
        return jsonify({'success': False, 'message': 'Nome deve ter no máximo 100 caracteres.'}), 400
    
    try:
        tipo_investimento.nome = novo_nome.strip()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Nome atualizado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao atualizar nome.'}), 500

@tipo_investimento_bp.route('/tipo-investimento/editar-descricao/<int:tipo_id>', methods=['POST'])
@login_required
def editar_descricao_inline(tipo_id):
    tipo_investimento = TipoInvestimento.query.get_or_404(tipo_id)
    
    if tipo_investimento.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Acesso não autorizado.'}), 403
    
    nova_descricao = request.json.get('descricao')
    if nova_descricao is None:
        nova_descricao = ''
    
    if len(nova_descricao) > 200:
        return jsonify({'success': False, 'message': 'Descrição deve ter no máximo 200 caracteres.'}), 400
    
    try:
        tipo_investimento.descricao = nova_descricao.strip() if nova_descricao.strip() else None
        db.session.commit()
        return jsonify({'success': True, 'message': 'Descrição atualizada com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao atualizar descrição.'}), 500

@tipo_investimento_bp.route('/tipo-investimento/excluir/<int:tipo_id>', methods=['POST'])
@login_required
def excluir_tipo_investimento(tipo_id):
    tipo_investimento = TipoInvestimento.query.get_or_404(tipo_id)
    
    if tipo_investimento.user_id != current_user.id:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('tipo_investimento.listar_tipos_investimento'))
    
    db.session.delete(tipo_investimento)
    db.session.commit()
    flash('Tipo de investimento excluído com sucesso!', 'success')
    return redirect(url_for('tipo_investimento.listar_tipos_investimento'))


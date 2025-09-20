from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.forms import InvestimentoForm, MovimentacaoInvestimentoForm
from app.models import Investimento, MovimentacaoInvestimento, Conta, TipoInvestimento
from app import db
from flask_login import current_user

def get_current_conta():
    """Função helper para obter a conta atualmente selecionada"""
    # Verificar se o usuário tem contas
    if Conta.query.filter_by(user_id=current_user.id).count() == 0:
        return None
    
    # Obter todas as contas do usuário
    contas = Conta.query.filter_by(user_id=current_user.id).all()
    
    # Obter a conta da sessão
    conta_id = session.get('last_conta_id')
    
    # Se não há conta na sessão, usar a primeira conta
    if not conta_id and contas:
        conta_id = contas[0].id
        session['last_conta_id'] = conta_id
    
    # Verificar se a conta existe
    if conta_id:
        conta_existe = any(conta.id == conta_id for conta in contas)
        if not conta_existe and contas:
            # Se a conta não existe, usar a primeira conta disponível
            conta_id = contas[0].id
            session['last_conta_id'] = conta_id
    
    # Retornar a conta atual
    if conta_id:
        return Conta.query.get(conta_id)
    return None

def recalcular_saldos_movimentacoes(investimento_id):
    """Recalcula os saldos das movimentações de um investimento específico"""
    investimento = Investimento.query.get(investimento_id)
    if not investimento:
        return False
    
    # Buscar movimentações ordenadas por data (mais antiga primeiro)
    movimentacoes = MovimentacaoInvestimento.query.filter_by(investimento_id=investimento_id).order_by(MovimentacaoInvestimento.data_movimentacao.asc()).all()
    
    # Recalcular saldos
    saldo_atual = 0.0
    for mov in movimentacoes:
        mov.saldo_anterior = saldo_atual
        if mov.tipo_movimentacao == 'aplicacao':
            saldo_atual += mov.valor
        elif mov.tipo_movimentacao == 'resgate':
            saldo_atual -= mov.valor
        else:  # rendimento
            saldo_atual += mov.valor
        mov.saldo_atual = saldo_atual
    
    # Salvar alterações
    db.session.commit()
    return True

investimento_bp = Blueprint('investimento', __name__)

@investimento_bp.route('/investimentos', methods=['GET'])
def investimentos():
    
    # Obter filtro de conta da URL
    conta_filter = request.args.get('conta_id', type=int)
    
    # Se não há filtro específico, usar a conta atualmente selecionada
    if not conta_filter:
        conta_atual = get_current_conta()
        if conta_atual:
            conta_filter = conta_atual.id
    
    # Buscar investimentos baseado no filtro de conta
    if conta_filter:
        from app.models import Conta, MovimentacaoInvestimento
        
        # Verificar se a conta existe e pertence ao usuário
        conta = Conta.query.filter_by(id=conta_filter, user_id=current_user.id).first()
        if conta:
            # Filtrar investimentos que têm movimentações de aplicação do usuário atual
            # E que estão relacionados à conta específica
            investimentos_filtrados = []
            
            # Buscar todos os investimentos
            todos_investimentos = Investimento.query.all()
            
            for investimento in todos_investimentos:
                # Verificar se o investimento tem movimentações de aplicação do usuário atual
                # E se essas movimentações estão relacionadas à conta específica
                movimentacoes_aplicacao = MovimentacaoInvestimento.query.filter_by(
                    investimento_id=investimento.id,
                    tipo_movimentacao='aplicacao',
                    user_id=current_user.id,
                    conta_id=conta_filter  # Filtrar por conta específica
                ).all()
                
                # Se tem movimentações de aplicação na conta específica, incluir no filtro
                if movimentacoes_aplicacao:
                    investimentos_filtrados.append(investimento)
            
            investimentos = investimentos_filtrados
        else:
            # Se a conta não existe, não mostrar nenhum investimento
            investimentos = []
    else:
        # Se não há filtro de conta, não mostrar nenhum investimento
        investimentos = []
    
    # Filtrar tipos de investimento apenas do usuário atual
    tipos_investimento = TipoInvestimento.query.filter_by(user_id=current_user.id, ativo=True).all()
    
    # Buscar informações da conta para exibir no template
    conta_info = None
    if conta_filter:
        try:
            from app.models import Conta
            conta = Conta.query.filter_by(id=conta_filter, user_id=current_user.id).first()
            if conta:
                conta_info = {
                    'id': conta.id,
                    'nome': conta.nome,
                    'saldo_atual': conta.saldo_atual or 0.0
                }
        except Exception as e:
            pass
    else:
        # Se não há filtro específico, usar a conta atualmente selecionada
        conta_atual = get_current_conta()
        if conta_atual:
            conta_info = {
                'id': conta_atual.id,
                'nome': conta_atual.nome,
                'saldo_atual': conta_atual.saldo_atual or 0.0
            }
    
    return render_template('list_investments.html', 
                         investimentos=investimentos, 
                         tipos_investimento=tipos_investimento,
                         conta_filter=conta_filter,
                         conta_info=conta_info)

@investimento_bp.route('/investimentos/novo', methods=['POST'])
def novo_investimento():
    tipo_investimento_id = request.form.get('tipo_investimento_id', type=int)
    
    # Obter a conta atualmente selecionada
    conta_atual = get_current_conta()
    if not conta_atual:
        flash('Você precisa ter pelo menos uma conta cadastrada.', 'warning')
        return redirect(url_for('investimento.investimentos'))
    
    novo_investimento = Investimento(
        tipo_investimento_id=tipo_investimento_id
    )
    db.session.add(novo_investimento)
    db.session.commit()
    
    # Criar movimentação inicial de aplicação com valor zero para vincular à conta
    from datetime import date
    movimentacao_inicial = MovimentacaoInvestimento(
        investimento_id=novo_investimento.id,
        data_movimentacao=date.today(),
        tipo_movimentacao='aplicacao',
        valor=0.0,
        saldo_anterior=0.0,
        saldo_atual=0.0,
        observacoes='Investimento criado - aguardando primeira aplicação',
        user_id=current_user.id,
        conta_id=conta_atual.id
    )
    db.session.add(movimentacao_inicial)
    db.session.commit()
    
    flash('Investimento criado com sucesso!', 'success')
    return redirect(url_for('investimento.investimentos'))

@investimento_bp.route('/investimento/<int:investimento_id>/movimentacoes', methods=['GET', 'POST'])
def listar_movimentacoes(investimento_id):
    investimento = Investimento.query.get_or_404(investimento_id)
    form = MovimentacaoInvestimentoForm()
    # Recalcular saldos antes de exibir para garantir consistência
    recalcular_saldos_movimentacoes(investimento_id)
    
    # Buscar movimentações ordenadas por ID (mais recente primeiro para exibição)
    movimentacoes = MovimentacaoInvestimento.query.filter_by(investimento_id=investimento_id).order_by(MovimentacaoInvestimento.id.desc()).all()
    
    # Buscar informações da conta atualmente selecionada
    conta_atual = get_current_conta()
    conta_info = None
    if conta_atual:
        conta_info = {
            'nome': conta_atual.nome,
            'saldo_atual': conta_atual.saldo_atual or 0.0
        }
        
        # Criar mensagens informativas sobre o saldo da conta
        if conta_info['saldo_atual'] < 0:
            flash(f'Saldo Negativo: O saldo da conta está negativo (R$ {conta_info["saldo_atual"]:.2f}). Novas aplicações não estão disponíveis até que o saldo seja regularizado.', 'danger')
        elif conta_info['saldo_atual'] == 0:
            flash('Saldo Zero: O saldo da conta está zerado (R$ 0,00). Novas aplicações não estão disponíveis até que haja saldo disponível.', 'warning')
    else:
        # Se não houver conta, criar um placeholder
        conta_info = {
            'nome': 'Nenhuma conta encontrada',
            'saldo_atual': 0.0
        }
        flash('Nenhuma conta encontrada. É necessário ter uma conta ativa para realizar movimentações.', 'warning')

    if form.validate_on_submit():
        # Validação para aplicação: valor não pode ser maior que o saldo atual da conta
        if form.tipo_movimentacao.data == 'aplicacao':
            if not conta_info or conta_info['saldo_atual'] <= 0:
                flash('Não é possível fazer aplicação: saldo da conta insuficiente ou conta não encontrada.', 'danger')
                return redirect(url_for('investimento.listar_movimentacoes', investimento_id=investimento.id))
            
            if form.valor.data > conta_info['saldo_atual']:
                flash(f'O valor da aplicação (R$ {form.valor.data:.2f}) não pode ser maior que o saldo atual da conta (R$ {conta_info["saldo_atual"]:.2f}).', 'danger')
                return redirect(url_for('investimento.listar_movimentacoes', investimento_id=investimento.id))
        
        # Calcular novo saldo do investimento
        saldo_anterior = investimento.saldo_atual
        if form.tipo_movimentacao.data == 'aplicacao':
            saldo_novo = saldo_anterior + form.valor.data
        elif form.tipo_movimentacao.data == 'resgate':
            saldo_novo = saldo_anterior - form.valor.data
        else: # rendimento
            saldo_novo = saldo_anterior + form.valor.data
        
        # Criar nova movimentação
        nova_mov = MovimentacaoInvestimento(
            investimento_id=investimento.id,
            data_movimentacao=form.data_movimentacao.data,
            tipo_movimentacao=form.tipo_movimentacao.data,
            valor=form.valor.data,
            saldo_anterior=saldo_anterior,
            saldo_atual=saldo_novo,
            observacoes=form.observacoes.data,
            user_id=current_user.id,
            conta_id=conta_atual.id
        )
        db.session.add(nova_mov)
        
        # Atualizar saldo da conta atualmente selecionada
        if conta_atual:
            # Usar o método da classe Conta para atualizar o saldo
            conta_atual.atualizar_saldo_investimento(
                form.tipo_movimentacao.data, 
                form.valor.data, 
                'adicionar'
            )
            db.session.add(conta_atual)
        
        # Commit das alterações
        db.session.commit()
        
        # Recalcular saldos das contas para garantir consistência
        Conta.recalcular_saldos()
        
        # Mensagem de sucesso
        if form.tipo_movimentacao.data == 'aplicacao':
            flash(f'Aplicação de R$ {form.valor.data:.2f} realizada com sucesso! Saldo da conta atualizado.', 'success')
        else:
            flash(f'Movimentação de {form.tipo_movimentacao.data} registrada com sucesso!', 'success')
        
        return redirect(url_for('investimento.listar_movimentacoes', investimento_id=investimento.id))

    from datetime import date
    today = date.today()
    # Obter o saldo atual do investimento para validação de resgate
    saldo_investimento = investimento.saldo_atual
    
    # Identificar o primeiro resgate com saldo zero para ocultar ícones de edição/exclusão
    primeiro_resgate_zero = None
    for mov in movimentacoes:
        if mov.tipo_movimentacao == 'resgate' and mov.saldo_atual == 0.0:
            primeiro_resgate_zero = mov.id
            break
    
    return render_template('list_movimentacoes_investimento.html', 
                         investimento=investimento, 
                         movimentacoes=movimentacoes, 
                         form=form, 
                         conta_info=conta_info, 
                         saldo_investimento=saldo_investimento,
                         primeiro_resgate_zero=primeiro_resgate_zero,
                         today=today)

@investimento_bp.route('/investimento/<int:investimento_id>/recalcular-saldos', methods=['POST'])
def recalcular_saldos_investimento(investimento_id):
    """Rota para recalcular manualmente os saldos das movimentações"""
    if recalcular_saldos_movimentacoes(investimento_id):
        flash('Saldos das movimentações recalculados com sucesso!', 'success')
    else:
        flash('Erro ao recalcular saldos das movimentações.', 'danger')
    
    return redirect(url_for('investimento.listar_movimentacoes', investimento_id=investimento_id))

@investimento_bp.route('/investimento/<int:investimento_id>/excluir', methods=['POST'])
def excluir_investimento(investimento_id):
    investimento = Investimento.query.get_or_404(investimento_id)
    db.session.delete(investimento)
    db.session.commit()
    flash('Investimento excluído com sucesso!', 'success')
    return redirect(url_for('investimento.investimentos'))

@investimento_bp.route('/movimentacao/<int:movimentacao_id>/editar', methods=['GET', 'POST'])
def editar_movimentacao(movimentacao_id):
    movimentacao = MovimentacaoInvestimento.query.get_or_404(movimentacao_id)
    investimento = Investimento.query.get_or_404(movimentacao.investimento_id)
    form = MovimentacaoInvestimentoForm(obj=movimentacao)
    
    # Buscar informações da conta para validação
    conta_atual = get_current_conta()
    conta_info = None
    if conta_atual:
        conta_info = {
            'nome': conta_atual.nome,
            'saldo_atual': conta_atual.saldo_atual or 0.0
        }
    
    if form.validate_on_submit():
        valor_anterior = movimentacao.valor
        valor_novo = form.valor.data
        
        # Ajustar saldo da conta baseado na diferença do valor
        if conta_atual and movimentacao.tipo_movimentacao == 'aplicacao':
            if valor_novo > valor_anterior:
                # Valor aumentou: subtrair a diferença da conta
                diferenca = valor_novo - valor_anterior
                if diferenca > conta_atual.saldo_atual:
                    flash(f'Saldo insuficiente na conta. Diferença: R$ {diferenca:.2f}, Saldo disponível: R$ {conta_atual.saldo_atual:.2f}', 'danger')
                    return redirect(url_for('investimento.editar_movimentacao', movimentacao_id=movimentacao_id))
                
                # Remover valor anterior e adicionar novo valor
                conta_atual.atualizar_saldo_investimento('aplicacao', valor_anterior, 'remover')
                conta_atual.atualizar_saldo_investimento('aplicacao', valor_novo, 'adicionar')
            elif valor_novo < valor_anterior:
                # Valor diminuiu: adicionar a diferença à conta
                diferenca = valor_anterior - valor_novo
                
                # Remover valor anterior e adicionar novo valor
                conta_atual.atualizar_saldo_investimento('aplicacao', valor_anterior, 'remover')
                conta_atual.atualizar_saldo_investimento('aplicacao', valor_novo, 'adicionar')
            
            db.session.add(conta_atual)
        
        # Atualizar a movimentação
        form.populate_obj(movimentacao)
        
        # Recalcular saldos das movimentações deste investimento
        recalcular_saldos_movimentacoes(investimento.id)
        
        db.session.commit()
        
        # Recalcular saldos das contas para garantir consistência
        Conta.recalcular_saldos()
        
        flash('Movimentação editada com sucesso! Saldo da conta ajustado.', 'success')
        return redirect(url_for('investimento.listar_movimentacoes', investimento_id=movimentacao.investimento_id))
    
    return render_template('edit_movimentacao_investimento.html', form=form, movimentacao=movimentacao, investimento=investimento, conta_info=conta_info)

@investimento_bp.route('/movimentacao/<int:movimentacao_id>/excluir', methods=['POST'])
def excluir_movimentacao(movimentacao_id):
    movimentacao = MovimentacaoInvestimento.query.get_or_404(movimentacao_id)
    investimento_id = movimentacao.investimento_id
    tipo_movimentacao = movimentacao.tipo_movimentacao
    valor_movimentacao = movimentacao.valor
    
    # Atualizar saldo da conta atualmente selecionada se for aplicação ou resgate
    conta_atual = get_current_conta()
    if conta_atual:
        # Usar o método da classe Conta para reverter a movimentação
        conta_atual.atualizar_saldo_investimento(tipo_movimentacao, valor_movimentacao, 'remover')
        db.session.add(conta_atual)
    
    # Excluir a movimentação
    db.session.delete(movimentacao)
    db.session.commit()
    
    # Recalcular saldos das contas para garantir consistência
    Conta.recalcular_saldos()
    
    # Mensagem de sucesso
    if tipo_movimentacao == 'aplicacao':
        flash(f'Aplicação de R$ {valor_movimentacao:.2f} excluída com sucesso! Saldo da conta restaurado.', 'success')
    elif tipo_movimentacao == 'resgate':
        flash(f'Resgate de R$ {valor_movimentacao:.2f} excluído com sucesso! Saldo da conta ajustado.', 'success')
    else:
        flash('Movimentação excluída com sucesso!', 'success')
    
    # Redirecionar de volta para a lista de movimentações
    investimento = Investimento.query.get(investimento_id)
    if investimento:
        return redirect(url_for('investimento.listar_movimentacoes', investimento_id=investimento_id))
    else:
        return redirect(url_for('main.dashboard', mensagem='Investimento não encontrado.'))

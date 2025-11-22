from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    session,
)
from urllib.parse import urlencode
from flask_login import login_user, logout_user, login_required, current_user
from app import db, mail
from app.models import Expense, PaymentMethod, User, Category, Transaction
from app.models import Conta
from app.forms import (
    ExpenseForm,
    LoginForm,
    PaymentMethodForm,
    RegistrationForm,
    TransactionForm,
    CategoryForm,
    RequestResetForm,
    ResetPasswordForm,
    ProfileForm,
)
from sqlalchemy import func, extract, desc, or_, and_, case
from datetime import datetime
from calendar import monthrange
import json
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer as Serializer
from decimal import Decimal

# Blueprints
main_bp = Blueprint("main", __name__)
auth_bp = Blueprint("auth", __name__)
transaction_bp = Blueprint("transaction", __name__)


# Funções helper
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


# Rotas principais
@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("home.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # Inicializar dados padrão para o novo usuário
        from app import initialize_user_default_data
        initialize_user_default_data(user)
        
        flash("Cadastro realizado com sucesso! Categorias, formas de pagamento, despesas, tipos de conta e contas padrão foram criados automaticamente.", "success")
        return redirect(url_for("conta.listar_contas"))

    return render_template("add_register.html", form=form)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    # Verifica se o usuário tem pelo menos uma conta cadastrada
    if Conta.query.filter_by(user_id=current_user.id).count() == 0:
        flash("Cadastre ao menos uma conta para acessar o dashboard.", "warning")
        return redirect(url_for("conta.listar_contas"))
    
    # Obter todas as contas do usuário
    contas = Conta.query.filter_by(user_id=current_user.id).all()
    
    # Obter o filtro de conta da URL
    conta_filter = request.args.get('conta_id', type=int)
    
    # Se não há filtro na URL, usar a última conta acessada ou a primeira conta
    if conta_filter is None:
        # Tentar obter da sessão usando get_current_conta
        conta_atual = get_current_conta()
        if conta_atual:
            conta_filter = conta_atual.id
        elif contas:
            # Se não há última conta na sessão, usar a primeira conta
            conta_filter = contas[0].id
    
    # Verificar se a conta filtrada existe
    if conta_filter:
        conta_existe = any(conta.id == conta_filter for conta in contas)
        if not conta_existe:
            # Se a conta não existe, usar a primeira conta disponível
            conta_filter = contas[0].id if contas else None
            session['last_conta_id'] = conta_filter
    
    # Salvar a conta atual na sessão
    # if conta_filter:
    #     session['last_conta_id'] = conta_filter
        
        # Criar flash message informando qual conta está selecionada
        # conta_selecionada = next((c for c in contas if c.id == conta_filter), None)
        # if conta_selecionada:
        #     flash(f'Vocâ acessou a conta {conta_selecionada.nome}.', 'info')
    
    # Obter o mês e ano atual
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_date = datetime.now().date()

    # Mapeamento dos meses em português
    meses = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }

    # Função auxiliar para calcular o valor final
    def get_final_value(transaction):
        amount = transaction.amount or 0
        discount = transaction.discount or 0
        return amount - discount
    
    # Função para verificar se um investimento deve ser exibido
    def deve_exibir_investimento(investimento, current_date):
        """
        Verifica se um investimento deve ser exibido baseado nos critérios:
        EXIBIR investimentos que NÃO se enquadrem nos critérios:
        - Tipo de movimentação seja igual a 'Resgate' E
        - Saldo atual seja igual a 0 E
        - Data da última movimentação (mês/ano) seja menor ao do mês/ano atual
        """
        from app.models import MovimentacaoInvestimento
        
        # Buscar a última movimentação do investimento
        ultima_movimentacao = MovimentacaoInvestimento.query.filter_by(
            investimento_id=investimento.id,
            user_id=current_user.id
        ).order_by(MovimentacaoInvestimento.data_movimentacao.desc()).first()
        
        if not ultima_movimentacao:
            return True  # Exibir investimentos sem movimentações
        
        # Verificar se o investimento se enquadra nos critérios para NÃO exibir
        # Critério 1: Tipo de movimentação seja igual a 'Resgate'
        # Critério 2: Saldo atual seja igual a 0
        # Critério 3: Data da última movimentação (mês/ano) seja menor ao do mês/ano atual
        
        if (ultima_movimentacao.tipo_movimentacao == 'resgate' and 
            ultima_movimentacao.saldo_atual == 0.0 and
            (ultima_movimentacao.data_movimentacao.year < current_date.year or
             (ultima_movimentacao.data_movimentacao.year == current_date.year and 
              ultima_movimentacao.data_movimentacao.month < current_date.month))):
            return False  # NÃO exibir este investimento
        
        return True  # Exibir este investimento
    


    # Buscar transações recentes de receita do mês atual
    recent_income_query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "receita",
        extract("month", Transaction.payment_date) == current_month,
        extract("year", Transaction.payment_date) == current_year,
    )
    if conta_filter:
        recent_income_query = recent_income_query.filter(Transaction.conta_id == conta_filter)
    recent_income = recent_income_query.order_by(Transaction.payment_date.desc()).limit(5).all()

    # Buscar transações recentes de despesa do mês atual
    recent_expenses_query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "despesa",
        or_(
            # Filtrar por data de vencimento no mês (independente do ano)
            extract("month", Transaction.due_date) == current_month,
            # OU filtrar por data de pagamento no mês atual
            and_(
                extract("month", Transaction.payment_date) == current_month,
                extract("year", Transaction.payment_date) == current_year,
            ),
        ),
    )
    if conta_filter:
        recent_expenses_query = recent_expenses_query.filter(Transaction.conta_id == conta_filter)
    recent_expenses = recent_expenses_query.all()
    # Ordenar manualmente, substituindo None por datetime.min
    recent_expenses = sorted(recent_expenses, key=lambda t: t.due_date or datetime.min)

    # Debug: Imprimir todas as despesas encontradas
    # print("\nDespesas encontradas no dashboard:")
    # for exp in recent_expenses:
    #     print(
    #         f"Vencimento: {exp.due_date}, Descrição: {exp.expense.name if exp.expense else exp.description}, "
    #         f"Valor: {exp.amount}, Desconto: {exp.discount}, Categoria: {exp.category.name}"
    #     )

    # Debug: Procurar especificamente por despesas de água
    agua_expenses = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "despesa",
        or_(
            Transaction.expense.has(name="Água"),
            Transaction.description.ilike("%água%"),
        ),
    ).all()
    # print("\nDespesas de água encontradas:")
    # for exp in agua_expenses:
    #     print(
    #         f"Vencimento: {exp.due_date}, Descrição: {exp.expense.name if exp.expense else exp.description}, "
    #         f"Valor: {exp.amount}, Desconto: {exp.discount}, Categoria: {exp.category.name}"
    #     )

    # Buscar transações do mês atual para estatísticas mensais
    monthly_transactions = (
        Transaction.query.filter(
            Transaction.user_id == current_user.id,
            extract("month", Transaction.date) == current_month,
            extract("year", Transaction.date) == current_year,
        )
        .order_by(Transaction.date.desc())
        .limit(5)
        .all()
    )

    # Calcular o total de receitas do mês atual
    income_query = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "receita",
        Transaction.paid == True,  # Apenas receitas pagas
        extract("month", Transaction.payment_date) == current_month,
        extract("year", Transaction.payment_date) == current_year,
    )
    if conta_filter:
        income_query = income_query.filter(Transaction.conta_id == conta_filter)
    income_total = income_query.scalar() or 0

    # Calcular o total de despesas do mês atual considerando due_date ou payment_date
    expense_transactions_query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "despesa",
        Transaction.paid == True,  # Apenas despesas pagas
        or_(
            and_(
                extract("month", Transaction.due_date) == current_month,
                extract("year", Transaction.due_date) == current_year,
            ),
            and_(
                extract("month", Transaction.payment_date) == current_month,
                extract("year", Transaction.payment_date) == current_year,
            ),
        ),
    )
    if conta_filter:
        expense_transactions_query = expense_transactions_query.filter(Transaction.conta_id == conta_filter)
    expense_transactions = expense_transactions_query.all()
    expense_total = sum(get_final_value(t) for t in expense_transactions)

    # Saldo do mês = Total de receitas - Total de despesas
    monthly_balance = income_total - expense_total

    # Debug: Imprimir os valores para verificação
    # print(f"\nValores do mês:")
    # print(f"Total de receitas: {income_total}")
    # print(f"Total de despesas: {expense_total}")
    # print(f"Saldo do mês: {monthly_balance}")

    # Calcular saldo acumulado (soma de todos os saldos dos meses anteriores)
    accumulated_balance_query = db.session.query(
        func.sum(
            case(
                (Transaction.type == "receita", Transaction.amount),
                (
                    Transaction.type == "despesa",
                    -(Transaction.amount - Transaction.discount),
                ),
                else_=0,
            )
        )
    ).filter(
        Transaction.user_id == current_user.id,
        or_(
            # Meses anteriores ao atual
            extract("year", Transaction.payment_date) < current_year,
            # Meses do ano atual até o mês anterior
            and_(
                extract("year", Transaction.payment_date) == current_year,
                extract("month", Transaction.payment_date) < current_month,
            ),
        ),
    )
    
    # Aplicar filtro de conta se especificado
    if conta_filter:
        accumulated_balance_query = accumulated_balance_query.filter(Transaction.conta_id == conta_filter)
    
    accumulated_balance = accumulated_balance_query.scalar() or 0

    # Calcular saldo total (acumulado + saldo do mês atual)
    balance = accumulated_balance + monthly_balance

    # Obter as categorias de despesas com maiores gastos no mês
    expense_by_category_query = (
        db.session.query(
            Category.name,
            func.sum(Transaction.amount).label("total_amount"),
            func.sum(Transaction.discount).label("total_discount"),
        )
        .join(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "despesa",
            extract("month", Transaction.date) == current_month,
            extract("year", Transaction.date) == current_year,
        )
    )
    
    # Aplicar filtro de conta se especificado
    if conta_filter:
        expense_by_category_query = expense_by_category_query.filter(Transaction.conta_id == conta_filter)
    
    expense_by_category = expense_by_category_query.group_by(Category.name).all()

    # Calcular totais finais por categoria (amount - discount)
    top_expense_categories = [
        (cat, (total_amount or 0) - (total_discount or 0))
        for cat, total_amount, total_discount in expense_by_category
    ]
    top_expense_categories.sort(key=lambda x: x[1], reverse=True)
    top_expense_categories = top_expense_categories[:5]

    # Obter as categorias de receitas com maiores valores no mês
    top_income_categories_query = (
        db.session.query(Category.name, func.sum(Transaction.amount).label("total"))
        .join(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "receita",
            extract("month", Transaction.date) == current_month,
            extract("year", Transaction.date) == current_year,
        )
    )
    
    # Aplicar filtro de conta se especificado
    if conta_filter:
        top_income_categories_query = top_income_categories_query.filter(Transaction.conta_id == conta_filter)
    
    top_income_categories = top_income_categories_query.group_by(Category.name).order_by(func.sum(Transaction.amount).desc()).limit(5).all()

    # Obter dados para o gráfico de evolução mensal (últimos 6 meses)
    monthly_data = []
    for i in range(5, -1, -1):
        month = current_month - i
        year = current_year
        while month <= 0:
            month += 12
            year -= 1

        month_income_query = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "receita",
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        )
        if conta_filter:
            month_income_query = month_income_query.filter(Transaction.conta_id == conta_filter)
        month_income = month_income_query.scalar() or 0

        month_expense_transactions_query = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "despesa",
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        )
        if conta_filter:
            month_expense_transactions_query = month_expense_transactions_query.filter(Transaction.conta_id == conta_filter)
        month_expense_transactions = month_expense_transactions_query.all()
        month_expense = sum(get_final_value(t) for t in month_expense_transactions)

        month_name = datetime(year, month, 1).strftime("%b")
        monthly_data.append(
            {
                "month": month_name,
                "receita": float(month_income),
                "despesa": float(month_expense),
                "balance": float(month_income - month_expense),
            }
        )

    # Preparar dados para os gráficos
    expense_chart_data = [
        {"name": cat, "value": float(total)} for cat, total in top_expense_categories
    ]
    income_chart_data = [
        {"name": cat, "value": float(total)} for cat, total in top_income_categories
    ]

    # Serializar os dados para JSON
    expense_chart_json = json.dumps(expense_chart_data, ensure_ascii=False)
    income_chart_json = json.dumps(income_chart_data, ensure_ascii=False)
    monthly_data_json = json.dumps(monthly_data, ensure_ascii=False)

    # Calcular estatísticas adicionais
    # Total de transações: considerar transações com due_date ou payment_date no mês atual
    total_transactions_query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        or_(
            and_(
                extract("month", Transaction.due_date) == current_month,
                extract("year", Transaction.due_date) == current_year,
            ),
            and_(
                extract("month", Transaction.payment_date) == current_month,
                extract("year", Transaction.payment_date) == current_year,
            ),
        ),
    )
    if conta_filter:
        total_transactions_query = total_transactions_query.filter(Transaction.conta_id == conta_filter)
    total_transactions = total_transactions_query.count()

    # Calcular a média diária de despesas
    # Considerar apenas despesas com due_date ou payment_date no mês atual
    # A média é calculada dividindo o total pelo número de dias do mês
    days_in_month = monthrange(current_year, current_month)[1]
    daily_avg_expense = expense_total / days_in_month if days_in_month > 0 else 0

    # Calcular a projeção para o final do mês
    # Usar o dia atual do mês como base para a projeção
    current_day = datetime.now().day
    # Garantir que estamos no mês atual
    if current_date.month == current_month and current_date.year == current_year:
        projected_expense = (
            (expense_total / current_day) * days_in_month if current_day > 0 else 0
        )
    else:
        # Se não estamos no mês atual, a projeção é igual ao total
        projected_expense = expense_total

    # Verificar transações pendentes
    pending_transactions_query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.paid == False,
    )
    if conta_filter:
        pending_transactions_query = pending_transactions_query.filter(Transaction.conta_id == conta_filter)
    pending_transactions = pending_transactions_query.count()

    # Lista de transações pendentes para a tabela collapsada
    pending_transactions_list_query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.paid == False
    )
    if conta_filter:
        pending_transactions_list_query = pending_transactions_list_query.filter(Transaction.conta_id == conta_filter)
    pending_transactions_list = pending_transactions_list_query.order_by(Transaction.due_date.asc(), Transaction.date.asc()).all()

    # Corrigir o total exibido no card para ser a soma dos valores da tabela
    pending_amount = sum((t.amount or 0) - (t.discount or 0) for t in pending_transactions_list)

    # Calcular saldo_atual para o card do dashboard
    saldo_atual = 0.0
    if conta_filter:
        conta_atual = next((c for c in contas if c.id == conta_filter), None)
        if conta_atual:
            # Recalcular apenas a conta específica
            Conta.recalcular_saldos(conta_id=conta_filter)
            # Recarregar o objeto do banco de dados para obter o valor atualizado
            db.session.refresh(conta_atual)
            saldo_atual = conta_atual.saldo_atual
    else:
        # Se não há conta específica, usar a conta atual da sessão
        conta_atual = get_current_conta()
        if conta_atual:
            # Recalcular apenas a conta específica
            Conta.recalcular_saldos(conta_id=conta_atual.id)
            # Recarregar o objeto do banco de dados para obter o valor atualizado
            db.session.refresh(conta_atual)
            saldo_atual = conta_atual.saldo_atual
        else:
            # Recalcular todas as contas do usuário
            Conta.recalcular_saldos()
            # Recarregar todas as contas
            for conta in contas:
                db.session.refresh(conta)
            saldo_atual = sum(c.saldo_atual for c in contas)

    # Buscar investimentos da conta selecionada
    investimentos = []
    investimentos_conta_atual = []
    
    if conta_filter:
        from app.models import Investimento, MovimentacaoInvestimento
        # Buscar investimentos que têm movimentações relacionadas à conta específica
        movimentacoes_conta = MovimentacaoInvestimento.query.filter_by(
            conta_id=conta_filter,
            user_id=current_user.id
        ).all()
        
        # Obter IDs únicos dos investimentos
        investimento_ids = list(set(mov.investimento_id for mov in movimentacoes_conta))
        
        # Buscar os investimentos e aplicar filtros
        for inv_id in investimento_ids:
            investimento = Investimento.query.get(inv_id)
            if investimento:
                # Adicionar informações da conta ao investimento
                investimento.conta = conta_atual
                
                # Verificar se deve ser exibido (aplicar filtros)
                if deve_exibir_investimento(investimento, current_date):
                    investimentos.append(investimento)
                    investimentos_conta_atual.append(investimento)
    else:
        # Se não há conta específica, buscar todos os investimentos do usuário
        from app.models import Investimento, MovimentacaoInvestimento
        movimentacoes_usuario = MovimentacaoInvestimento.query.filter_by(
            user_id=current_user.id
        ).all()
        
        # Obter IDs únicos dos investimentos
        investimento_ids = list(set(mov.investimento_id for mov in movimentacoes_usuario))
        
        # Buscar os investimentos e aplicar filtros
        for inv_id in investimento_ids:
            investimento = Investimento.query.get(inv_id)
            if investimento:
                # Buscar a conta da primeira movimentação deste investimento
                primeira_mov = MovimentacaoInvestimento.query.filter_by(
                    investimento_id=inv_id,
                    user_id=current_user.id
                ).first()
                if primeira_mov:
                    investimento.conta = Conta.query.get(primeira_mov.conta_id)
                
                # Verificar se deve ser exibido (aplicar filtros)
                if deve_exibir_investimento(investimento, current_date):
                    investimentos.append(investimento)

    return render_template(
        "dashboard.html",
        contas=contas,
        conta_filter=conta_filter,
        monthly_transactions=monthly_transactions,
        recent_income=recent_income,
        recent_expenses=recent_expenses,
        income_total=income_total,
        expense_total=expense_total,
        balance=balance,  # Saldo acumulado
        monthly_balance=monthly_balance,  # Saldo do mês
        top_expense_categories=top_expense_categories,
        top_income_categories=top_income_categories,
        expense_chart_json=expense_chart_json,
        income_chart_json=income_chart_json,
        monthly_data_json=monthly_data_json,
        total_transactions=total_transactions,
        daily_avg_expense=daily_avg_expense,
        projected_expense=projected_expense,
        pending_transactions=pending_transactions,
        pending_amount=pending_amount,  # Adicionando o valor total pendente
        pending_transactions_list=pending_transactions_list,
        current_month=f"{meses[current_month]} {current_year}",
        datetime=datetime,
        monthrange=monthrange,
        saldo_atual=saldo_atual,
        investimentos=investimentos,  # Adicionando os investimentos
        investimentos_conta_atual=investimentos_conta_atual,  # Investimentos da conta atual
    )


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash("Senha atual incorreta.", "danger")
            return render_template("profile.html", form=form)

        # Check if email is being changed and if it's already in use
        if form.email.data != current_user.email:
            if User.query.filter_by(email=form.email.data).first():
                flash("Este email já está em uso.", "danger")
                return render_template("profile.html", form=form)
            current_user.email = form.email.data

        # Update password if a new one was provided
        if form.new_password.data:
            current_user.set_password(form.new_password.data)

        db.session.commit()
        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for("auth.profile"))

    # Pre-fill the email field
    if request.method == "GET":
        form.email.data = current_user.email

    return render_template("profile.html", form=form)


# Rotas de autenticação
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        else:
            flash("Nome de usuário ou senha inválidos", "danger")
            # Garantir que a mensagem seja exibida apenas na página de login
            # Não fazer redirect, renderizar o template diretamente
            return render_template("login.html", form=form)

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    # Verifica se o logout foi chamado como parte do processo de shutdown
    if request.args.get("shutdown") == "true":
        return redirect(url_for("shutdown"))
    return redirect(url_for("main.index"))


@transaction_bp.route("/categories", methods=["GET"])
@login_required
def categories():
    selected_type = request.args.get("type", "")

    # Base query
    query = Category.query

    # Apply type filter if selected
    if selected_type:
        query = query.filter(Category.type == selected_type)

    # Order by id descending
    categories = query.order_by(desc(Category.id)).all()

    context = {
        "categories": categories,
        "edit": False,
        "selected_type": selected_type,
    }

    return render_template("list_categories.html", **context)


@transaction_bp.route("/categories/add", methods=["GET", "POST"])
@login_required
def add_category():
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            type=form.type.data,
            exclusive=form.exclusive.data,
            icon=form.icon.data,
            color=form.color.data,
        )

        db.session.add(category)
        db.session.commit()
        flash("Categoria adicionada com sucesso!", "success")
        return redirect(url_for("transaction.categories"))
    else:
        print(form.errors)  # Isso ajudará a encontrar os erros de validação

        # Se houver erros no formulário, exibe um alerta
        if form.errors:
            flash("Erro ao adicionar categoria. Verifique os campos.", "danger")
            print(form.errors)

    return render_template("add_edit_category.html", form=form, category=None, title="Adicionar Categoria")


@transaction_bp.route("/category/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data
        category.type = form.type.data
        category.exclusive = form.exclusive.data  # Usando o valor booleano diretamente
        # category.icon = form.icon.data
        # category.color = form.color.data
        db.session.commit()
        flash("Categoria atualizada com sucesso!", "success")
        return redirect(url_for("transaction.categories"))

    return render_template("add_edit_category.html", form=form, category=category, title=f"Editar Categoria: {category.name}")


@transaction_bp.route("/category/delete/<int:id>")
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)

    # Verificar se a categoria está sendo usada em alguma transação
    if Transaction.query.filter_by(category_id=category.id).first():
        flash(
            "Não é possível excluir uma categoria que está sendo usada em transações.",
            "danger",
        )
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Categoria excluída com sucesso!", "success")
    return redirect(url_for("transaction.categories"))


@transaction_bp.route("/expenses", methods=["GET"])
@login_required
def expenses():
    # Get category filter from query parameters
    category_id = request.args.get("category_id", type=int)

    # Base query
    query = Expense.query.order_by(desc(Expense.id))

    # Apply category filter if specified
    if category_id:
        query = query.filter(Expense.category_id == category_id)

    expenses = query.all()

    # Preencher as opções de categorias
    categories = Category.query.all()

    context = {
        "expenses": expenses,
        "edit": False,
        "categories": categories,
        "selected_category_id": category_id,
    }

    return render_template("list_expensives.html", **context)


@transaction_bp.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    form = ExpenseForm()
    
    # Preencher as opções de categorias
    categories = Category.query.all()
    form.category_id.choices = [(cat.id, cat.name) for cat in categories]

    if form.validate_on_submit():
        expense = Expense(name=form.name.data, category_id=form.category_id.data)

        db.session.add(expense)
        db.session.commit()
        flash("Descrição adicionada com sucesso!", "success")
        return redirect(url_for("transaction.expenses"))

    else:
        print(form.errors)  # Isso ajudará a encontrar os erros de validação

    return render_template("add_edit_expense.html", form=form, expense=None, title="Adicionar Descrição")


@transaction_bp.route("/expenses/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    form = ExpenseForm(obj=expense)

    # Retorna as opções da categoria ANTES da validação
    categories = Category.query.all()
    form.category_id.choices = [(0, "Selecione uma categoria")] + [
        (c.id, c.name) for c in categories
    ]

    if form.validate_on_submit():
        expense.name = form.name.data

        # Se o usuário selecionou uma categoria válida
        expense.category_id = (
            form.category_id.data if form.category_id.data > 0 else None
        )

        db.session.commit()
        flash("Descrição predefinida atualizada com sucesso!", "success")
        return redirect(url_for("transaction.expenses"))

    return render_template("add_edit_expense.html", form=form, expense=expense, title=f"Editar Descrição: {expense.name}")


@transaction_bp.route("/expenses/delete/<int:id>")
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)

    # Verificar se a descrição está sendo usada em alguma transação
    if Transaction.query.filter_by(expense_id=expense.id).first():
        flash(
            "Não é possível excluir uma descrição que está sendo usada em transações.",
            "danger",
        )
    else:
        db.session.delete(expense)
        db.session.commit()
        flash("Descrição predefinida excluída com sucesso!", "success")
    return redirect(url_for("transaction.expenses"))


@transaction_bp.route("/payment_methods", methods=["GET"])
@login_required
def list_payment_methods():
    methods = PaymentMethod.query.all()
    return render_template("list_payment_method.html", methods=methods)


@transaction_bp.route("/payment_methods/add", methods=["GET", "POST"])
@login_required
def add_payment_method():
    form = PaymentMethodForm()
    if form.validate_on_submit():
        payment_method = PaymentMethod(
            name=form.name.data, is_active=form.is_active.data
        )
        db.session.add(payment_method)
        db.session.commit()
        flash("Forma de pagamento adicionada com sucesso!", "success")
        return redirect(url_for("transaction.list_payment_methods"))
    return render_template("payment_method_form.html", form=form, title="Adicionar Forma de Pagamento")


@transaction_bp.route("/payment_methods/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_payment_method(id):
    method = PaymentMethod.query.get_or_404(id)
    form = PaymentMethodForm(obj=method)
    if form.validate_on_submit():
        method.name = form.name.data
        method.is_active = form.is_active.data
        db.session.commit()
        flash("Método de pagamento atualizado!", "success")
        return redirect(url_for("transaction.list_payment_methods"))
    return render_template("payment_method_form.html", form=form, title=f"Editar Forma de Pagamento: {method.name}")


@transaction_bp.route("/payment_methods/delete/<int:id>", methods=["POST"])
@login_required
def delete_payment_method(id):
    method = PaymentMethod.query.get_or_404(id)
    db.session.delete(method)
    db.session.commit()
    flash("Método de pagamento removido!", "danger")
    return redirect(url_for("transaction.list_payment_methods"))


@transaction_bp.route("/reports")
@login_required
def reports():
    check = require_account()
    if check:
        return check
    
    # Obter todas as contas do usuário
    contas = Conta.query.filter_by(user_id=current_user.id).all()
    
    # Obter o filtro de conta da URL
    conta_filter = request.args.get('conta_id', type=int)
    
    # Se não há filtro na URL, usar a última conta acessada ou a primeira conta
    if conta_filter is None:
        # Tentar obter da sessão
        conta_filter = session.get('last_conta_id')
        if conta_filter is None and contas:
            # Se não há última conta na sessão, usar a primeira conta
            conta_filter = contas[0].id
    
    # Verificar se a conta filtrada existe
    if conta_filter:
        conta_existe = any(conta.id == conta_filter for conta in contas)
        if not conta_existe:
            # Se a conta não existe, usar a primeira conta disponível
            conta_filter = contas[0].id if contas else None
            session['last_conta_id'] = conta_filter
    
    # Salvar a conta atual na sessão
    # if conta_filter:
    #     session['last_conta_id'] = conta_filter
        
    #     # Criar flash message informando qual conta está selecionada
    #     conta_selecionada = next((c for c in contas if c.id == conta_filter), None)
    #     if conta_selecionada:
    #         flash(f'Relatórios filtrados para a conta {conta_selecionada.nome}.', 'info')
    
    report_type = request.args.get("type", "monthly")
    year = request.args.get("year", datetime.now().year, type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    payment_method_id = request.args.get("payment_method_id", type=int)
    show_discount_only = request.args.get("show_discount_only", type=bool)
    years = range(datetime.now().year - 5, datetime.now().year + 1)

    # Debug: imprimir os valores de mês e ano
    # print(f"DEBUG: Mês selecionado: {month}, Ano selecionado: {year}")
    # print(f"DEBUG: Mês atual: {datetime.now().month}, Ano atual: {datetime.now().year}")

    # Função auxiliar para calcular o valor final
    def get_final_value(transaction):
        amount = float(transaction.amount or 0)
        discount = float(transaction.discount or 0)
        return amount - discount

    # Função auxiliar para garantir valor float
    def safe_float(value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    # Obter todas as formas de pagamento para o select
    payment_methods = PaymentMethod.query.filter_by(is_active=True).all()

    # Construir a consulta base
    if report_type != "annual":
        query = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            or_(
                # Para despesas, manter a lógica atual de filtrar por due_date ou payment_date
                and_(
                    Transaction.type == "despesa",
                    or_(
                        and_(
                            extract("month", Transaction.due_date) == month,
                            extract("year", Transaction.due_date) == year,
                        ),
                        and_(
                            extract("month", Transaction.payment_date) == month,
                            extract("year", Transaction.payment_date) == year,
                        ),
                    ),
                ),
                # Para receitas, filtrar apenas por payment_date
                and_(
                    Transaction.type == "receita",
                    extract("month", Transaction.payment_date) == month,
                    extract("year", Transaction.payment_date) == year,
                ),
            ),
        )
    else:
        # Para relatório anual, atualizar a lógica também
        query = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            or_(
                # Para despesas, manter a lógica atual
                and_(
                    Transaction.type == "despesa",
                    or_(
                        extract("year", Transaction.due_date) == year,
                        extract("year", Transaction.payment_date) == year,
                    ),
                ),
                # Para receitas, filtrar apenas por payment_date
                and_(
                    Transaction.type == "receita",
                    extract("year", Transaction.payment_date) == year,
                ),
            ),
        )

    # Aplicar filtro de forma de pagamento se especificado
    if payment_method_id:
        query = query.filter(Transaction.payment_method_id == payment_method_id)

    # Aplicar filtro de descontos se especificado
    if show_discount_only:
        query = query.filter(Transaction.discount > 0)
    
    # Aplicar filtro de conta se especificado
    if conta_filter:
        query = query.filter(Transaction.conta_id == conta_filter)

    # Executar a consulta
    transactions = query.all()

    # Função auxiliar para ordenação segura de datas
    def safe_date_sort(transaction):
        if transaction.type == "despesa":
            # Para despesas, usar due_date ou payment_date como fallback
            return transaction.due_date or transaction.payment_date or datetime.min
        else:
            # Para receitas, usar payment_date ou date como fallback
            return transaction.payment_date or transaction.date or datetime.min

    # Filtrar e ordenar transações
    expense_transactions = [t for t in transactions if t.type == "despesa"]
    expense_transactions.sort(key=safe_date_sort)

    income_transactions = [t for t in transactions if t.type == "receita"]
    income_transactions.sort(key=safe_date_sort)

    # Debug: imprimir as transações filtradas
    # print(f"DEBUG: Total de despesas filtradas: {len(expense_transactions)}")
    # print(f"DEBUG: Total de receitas filtradas: {len(income_transactions)}")

    # Inicializar totais
    income_total = 0.0
    expense_total = 0.0
    total_discount = 0.0

    # Calcular totais por tipo de transação
    for t in transactions:
        amount = safe_float(t.amount)
        discount = safe_float(t.discount)
        if t.type == "receita":
            income_total += amount
        else:  # despesa
            expense_total += amount - discount  # Subtrair o desconto do valor total
            total_discount += discount
    # Calcular saldo (receitas - (despesas - descontos))
    balance = (
        income_total - expense_total
    )  # expense_total já inclui o desconto subtraído

    # Inicializar dados dos gráficos
    expense_chart_data = []
    income_chart_data = []
    monthly_data = []

    if report_type == "monthly":
        # Filtrar transações por tipo para cálculos específicos
        income_transactions = [t for t in transactions if t.type == "receita"]

        # Calcular totais por categoria para receitas
        income_by_category = []
        income_category_totals = {}
        for t in income_transactions:
            if not t.category or not t.category.name:
                continue  # Skip transactions with missing category
            amount = safe_float(t.amount)
            if t.category.name not in income_category_totals:
                income_category_totals[t.category.name] = 0
            income_category_totals[t.category.name] += amount

        for category_name, total in income_category_totals.items():
            income_by_category.append({"category": category_name, "amount": total})

        # Ordenar por valor decrescente
        income_by_category.sort(key=lambda x: x["amount"], reverse=True)

        # Calcular totais por categoria para despesas (usando as despesas filtradas)
        expense_by_category = []
        expense_category_totals = {}
        for t in expense_transactions:
            if not t.category or not t.category.name:
                continue  # Skip transactions with missing category
            amount = safe_float(t.amount)
            discount = safe_float(t.discount)
            final_amount = amount - discount
            if t.category.name not in expense_category_totals:
                expense_category_totals[t.category.name] = 0
            expense_category_totals[t.category.name] += final_amount

        for category_name, total in expense_category_totals.items():
            expense_by_category.append({"category": category_name, "amount": total})

        # Ordenar por valor decrescente
        expense_by_category.sort(key=lambda x: x["amount"], reverse=True)

        # Preparar dados para os gráficos
        expense_chart_data = [
            {"category": item["category"], "amount": item["amount"]}
            for item in expense_by_category[:10]  # Top 10 categorias
        ]
        income_chart_data = [
            {"category": item["category"], "amount": item["amount"]}
            for item in income_by_category[:10]  # Top 10 categorias
        ]

        # Buscar investimentos da conta selecionada
        investimentos = []
        
        # Função para verificar se um investimento deve ser exibido
        def deve_exibir_investimento_reports(investimento, year, month):
            """
            Verifica se um investimento deve ser exibido baseado nos critérios:
            EXIBIR investimentos que NÃO se enquadrem nos critérios:
            - Primeira movimentação seja igual ou posterior ao mês/ano selecionado no filtro
            - Tipo de movimentação seja igual a 'Resgate' E
            - Saldo atual seja igual a 0 E
            - Data da última movimentação (mês/ano) seja menor ao do mês/ano selecionado no filtro
            """
            from app.models import MovimentacaoInvestimento
            
            # Buscar a primeira movimentação do investimento
            primeira_movimentacao = MovimentacaoInvestimento.query.filter_by(
                investimento_id=investimento.id,
                user_id=current_user.id
            ).order_by(MovimentacaoInvestimento.data_movimentacao.asc()).first()
            
            if not primeira_movimentacao:
                return True  # Exibir investimentos sem movimentações
            
            # Critério 0: Verificar se a primeira movimentação é igual ou posterior ao mês/ano selecionado
            # Se a primeira movimentação for posterior ao período selecionado, NÃO exibir
            if (primeira_movimentacao.data_movimentacao.year > year or
                (primeira_movimentacao.data_movimentacao.year == year and 
                 primeira_movimentacao.data_movimentacao.month > month)):
                return False  # NÃO exibir este investimento
            
            # Buscar a última movimentação do investimento
            ultima_movimentacao = MovimentacaoInvestimento.query.filter_by(
                investimento_id=investimento.id,
                user_id=current_user.id
            ).order_by(MovimentacaoInvestimento.data_movimentacao.desc()).first()
            
            # Verificar se o investimento se enquadra nos critérios para NÃO exibir
            # Critério 1: Tipo de movimentação seja igual a 'Resgate'
            # Critério 2: Saldo atual seja igual a 0
            # Critério 3: Data da última movimentação (mês/ano) seja menor ao do mês/ano selecionado no filtro
            
            if (ultima_movimentacao.tipo_movimentacao == 'resgate' and 
                ultima_movimentacao.saldo_atual == 0.0 and
                (ultima_movimentacao.data_movimentacao.year < year or 
                 (ultima_movimentacao.data_movimentacao.year == year and 
                  ultima_movimentacao.data_movimentacao.month < month))):
                return False  # NÃO exibir este investimento
            
            return True  # Exibir este investimento
        
        if conta_filter:
            from app.models import Investimento, MovimentacaoInvestimento
            # Buscar investimentos que têm movimentações relacionadas à conta específica
            movimentacoes_conta = MovimentacaoInvestimento.query.filter_by(
                conta_id=conta_filter,
                user_id=current_user.id
            ).all()
            
            # Obter IDs únicos dos investimentos
            investimento_ids = list(set(mov.investimento_id for mov in movimentacoes_conta))
            
            # Buscar os investimentos e aplicar filtros
            for inv_id in investimento_ids:
                investimento = Investimento.query.get(inv_id)
                if investimento:
                    # Adicionar informações da conta ao investimento
                    conta_atual = next((c for c in contas if c.id == conta_filter), None)
                    investimento.conta = conta_atual
                    
                    # Verificar se deve ser exibido (aplicar filtros)
                    if deve_exibir_investimento_reports(investimento, year, month):
                        investimentos.append(investimento)
        else:
            # Se não há conta específica, buscar todos os investimentos do usuário
            from app.models import Investimento, MovimentacaoInvestimento
            movimentacoes_usuario = MovimentacaoInvestimento.query.filter_by(
                user_id=current_user.id
            ).all()
            
            # Obter IDs únicos dos investimentos
            investimento_ids = list(set(mov.investimento_id for mov in movimentacoes_usuario))
            
            # Buscar os investimentos e aplicar filtros
            for inv_id in investimento_ids:
                investimento = Investimento.query.get(inv_id)
                if investimento:
                    # Buscar a conta da primeira movimentação deste investimento
                    primeira_mov = MovimentacaoInvestimento.query.filter_by(
                        investimento_id=inv_id,
                        user_id=current_user.id
                    ).first()
                    if primeira_mov:
                        investimento.conta = Conta.query.get(primeira_mov.conta_id)
                    
                    # Verificar se deve ser exibido (aplicar filtros)
                    if deve_exibir_investimento_reports(investimento, year, month):
                        investimentos.append(investimento)

        return render_template(
            "reports.html",
            contas=contas,
            conta_filter=conta_filter,
            transactions=transactions,
            expense_transactions=expense_transactions,  # Passar as despesas filtradas e ordenadas
            income_by_category=income_by_category,
            expense_by_category=expense_by_category,
            income_total=income_total,
            expense_total=expense_total,
            total_discount=total_discount,
            balance=balance,
            payment_methods=payment_methods,
            selected_method_id=payment_method_id,
            show_discount_only=show_discount_only,
            years=years,
            selected_year=year,
            selected_month=month,
            report_type=report_type,
            expense_chart_data=json.dumps(expense_chart_data),
            income_chart_data=json.dumps(income_chart_data),
            investimentos=investimentos,  # Adicionando os investimentos
        )
    else:  # annual report
        # Agrupar transações por mês
        for m in range(1, 13):
            month_income = 0.0
            month_expense = 0.0
            month_discount = 0.0

            # Filtrar transações do mês
            month_transactions = [t for t in transactions if t.date.month == m]

            for t in month_transactions:
                amount = safe_float(t.amount)
                discount = safe_float(t.discount)
                if t.type == "receita":
                    month_income += amount
                else:  # despesa
                    month_expense += amount
                    month_discount += discount

            monthly_data.append(
                {
                    "month": datetime(year, m, 1).strftime("%b"),
                    "receita": float(month_income),
                    "despesa": float(month_expense - month_discount),
                    "balance": float(month_income - (month_expense - month_discount)),
                }
            )

    # Buscar investimentos da conta selecionada para relatório anual
    investimentos = []
    
    # Função para verificar se um investimento deve ser exibido (relatório anual)
    def deve_exibir_investimento_reports_anual(investimento, year):
        """
        Verifica se um investimento deve ser exibido baseado nos critérios:
        EXIBIR investimentos que NÃO se enquadrem nos critérios:
        - Primeira movimentação seja igual ou posterior ao ano selecionado no filtro
        - Tipo de movimentação seja igual a 'Resgate' E
        - Saldo atual seja igual a 0 E
        - Data da última movimentação (ano) seja menor ao do ano selecionado no filtro
        """
        from app.models import MovimentacaoInvestimento
        
        # Buscar a primeira movimentação do investimento
        primeira_movimentacao = MovimentacaoInvestimento.query.filter_by(
            investimento_id=investimento.id,
            user_id=current_user.id
        ).order_by(MovimentacaoInvestimento.data_movimentacao.asc()).first()
        
        if not primeira_movimentacao:
            return True  # Exibir investimentos sem movimentações
        
        # Critério 0: Verificar se a primeira movimentação é igual ou posterior ao ano selecionado
        # Se a primeira movimentação for posterior ao ano selecionado, NÃO exibir
        if primeira_movimentacao.data_movimentacao.year > year:
            return False  # NÃO exibir este investimento
        
        # Buscar a última movimentação do investimento
        ultima_movimentacao = MovimentacaoInvestimento.query.filter_by(
            investimento_id=investimento.id,
            user_id=current_user.id
        ).order_by(MovimentacaoInvestimento.data_movimentacao.desc()).first()
        
        # Verificar se o investimento se enquadra nos critérios para NÃO exibir
        # Critério 1: Tipo de movimentação seja igual a 'Resgate'
        # Critério 2: Saldo atual seja igual a 0
        # Critério 3: Data da última movimentação (ano) seja menor ao do ano selecionado no filtro
        
        if (ultima_movimentacao.tipo_movimentacao == 'resgate' and 
            ultima_movimentacao.saldo_atual == 0.0 and
            ultima_movimentacao.data_movimentacao.year < year):
            return False  # NÃO exibir este investimento
        
        return True  # Exibir este investimento
    
    if conta_filter:
        from app.models import Investimento, MovimentacaoInvestimento
        # Buscar investimentos que têm movimentações relacionadas à conta específica
        movimentacoes_conta = MovimentacaoInvestimento.query.filter_by(
            conta_id=conta_filter,
            user_id=current_user.id
        ).all()
        
        # Obter IDs únicos dos investimentos
        investimento_ids = list(set(mov.investimento_id for mov in movimentacoes_conta))
        
        # Buscar os investimentos e aplicar filtros
        for inv_id in investimento_ids:
            investimento = Investimento.query.get(inv_id)
            if investimento:
                # Adicionar informações da conta ao investimento
                conta_atual = next((c for c in contas if c.id == conta_filter), None)
                investimento.conta = conta_atual
                
                # Verificar se deve ser exibido (aplicar filtros)
                if deve_exibir_investimento_reports_anual(investimento, year):
                    investimentos.append(investimento)
    else:
        # Se não há conta específica, buscar todos os investimentos do usuário
        from app.models import Investimento, MovimentacaoInvestimento
        movimentacoes_usuario = MovimentacaoInvestimento.query.filter_by(
            user_id=current_user.id
        ).all()
        
        # Obter IDs únicos dos investimentos
        investimento_ids = list(set(mov.investimento_id for mov in movimentacoes_usuario))
        
        # Buscar os investimentos e aplicar filtros
        for inv_id in investimento_ids:
            investimento = Investimento.query.get(inv_id)
            if investimento:
                # Buscar a conta da primeira movimentação deste investimento
                primeira_mov = MovimentacaoInvestimento.query.filter_by(
                    investimento_id=inv_id,
                    user_id=current_user.id
                ).first()
                if primeira_mov:
                    investimento.conta = Conta.query.get(primeira_mov.conta_id)
                
                # Verificar se deve ser exibido (aplicar filtros)
                if deve_exibir_investimento_reports_anual(investimento, year):
                    investimentos.append(investimento)

    # Return para relatório anual (fora do bloco if conta_filter)
    return render_template(
        "reports.html",
        contas=contas,
        conta_filter=conta_filter,
        transactions=transactions,
        expense_transactions=expense_transactions,  # Adicionar as despesas filtradas
        monthly_data=json.dumps(monthly_data),
        income_total=income_total,
        expense_total=expense_total,
        total_discount=total_discount,
        balance=balance,
        payment_methods=payment_methods,
        selected_method_id=payment_method_id,
        show_discount_only=show_discount_only,
        years=years,
        selected_year=year,
        selected_month=month,
        report_type=report_type,
        investimentos=investimentos,  # Adicionando os investimentos
    )


@transaction_bp.route("/export")
@login_required
def export_data():
    # Implementação futura para exportação de dados
    flash("Funcionalidade de exportação será implementada em breve!", "info")
    return redirect(url_for("transaction.reports"))


def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for("auth.reset_token", token=token, _external=True)

    # print("\n" + "=" * 50)
    # print("EMAIL DE RECUPERAÇÃO DE SENHA (CONSOLE)")
    # print("=" * 50)
    # print(f"De: {current_app.config['MAIL_DEFAULT_SENDER']}")
    # print(f"Para: {user.email}")
    # print(f"Assunto: Recuperação de Senha - Finanças Pessoais")
    # print("-" * 50)
    # print("Conteúdo do email:")
    # print(f"Para redefinir sua senha, visite o seguinte link:")
    # print(f"{reset_url}")
    # print(
    #     "\nSe você não solicitou esta recuperação de senha, simplesmente ignore este email."
    # )
    # print("=" * 50 + "\n")

    msg = Message("Recuperação de Senha - Finanças Pessoais", recipients=[user.email])
    msg.body = f"""Para redefinir sua senha, visite o seguinte link:
{reset_url}

Se você não solicitou esta recuperação de senha, simplesmente ignore este email.
"""
    mail.send(msg)


@auth_bp.route("/reset_request", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash("Um email foi enviado com instruções para redefinir sua senha.", "info")
        return redirect(url_for("auth.login"))
    return render_template("reset_request.html", title="Recuperar Senha", form=form)


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    user = User.verify_reset_token(token)
    if user is None:
        flash("O token de recuperação é inválido ou expirou.", "warning")
        return redirect(url_for("auth.reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Sua senha foi atualizada! Agora você pode fazer login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("reset_password.html", title="Redefinir Senha", form=form)


@transaction_bp.route("/reports/payment_method", methods=["GET"])
@login_required
def payment_method_report():
    check = require_account()
    if check:
        return check
    # Obter parâmetros do filtro
    payment_method_id = request.args.get("payment_method_id", type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    year = request.args.get("year", datetime.now().year, type=int)
    years = range(datetime.now().year - 5, datetime.now().year + 1)

    # Construir a consulta base
    query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract("month", Transaction.date) == month,
        extract("year", Transaction.date) == year,
    )

    # Aplicar filtro de forma de pagamento se especificado
    if payment_method_id:
        query = query.filter(Transaction.payment_method_id == payment_method_id)

    # Executar a consulta
    transactions = query.order_by(Transaction.date.desc()).all()

    # Função auxiliar para calcular o valor final
    def get_final_value(transaction):
        amount = float(transaction.amount or 0)
        discount = float(transaction.discount or 0)
        return amount - discount

    # Calcular totais
    total_amount = sum(float(t.amount or 0) for t in transactions)
    total_discount = sum(float(t.discount or 0) for t in transactions)
    total_final = sum(get_final_value(t) for t in transactions)

    # Obter todas as formas de pagamento para o select
    payment_methods = PaymentMethod.query.all()

    # Função auxiliar para garantir valor float
    def safe_float(value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    # Calcular totais por forma de pagamento
    payment_method_totals = {}
    for method in payment_methods:
        method_transactions = [
            t for t in transactions if t.payment_method_id == method.id
        ]
        method_income = sum(
            safe_float(t.amount) for t in method_transactions if t.type == "receita"
        )
        method_expenses = sum(
            safe_float(t.amount) for t in method_transactions if t.type == "despesa"
        )
        method_discount = sum(safe_float(t.discount) for t in method_transactions)
        payment_method_totals[method.id] = {
            "name": method.name,
            "total_income": method_income,
            "total_expenses": method_expenses,
            "total_discount": method_discount,
            "count": len(method_transactions),
        }

    # Preparar transações para o template
    transactions_for_template = []
    for t in transactions:
        transactions_for_template.append(
            {
                "date": t.date,
                "category": t.category,
                "expense": t.expense,
                "description": t.description,
                "amount": safe_float(t.amount),
                "discount": safe_float(t.discount),
                "due_date": t.due_date,
                "payment_date": t.payment_date,
                "payment_method": t.payment_method,
                "paid": t.paid,
                "type": t.type,
            }
        )

    return render_template(
        "payment_method_report.html",
        transactions=transactions_for_template,
        payment_methods=payment_methods,
        selected_method_id=payment_method_id,
        month=month,
        year=year,
        years=years,
        total_amount=safe_float(total_amount),
        total_discount=safe_float(total_discount),
        total_final=safe_float(total_final),
        payment_method_totals=payment_method_totals,
        total_transactions=len(transactions),
    )


@transaction_bp.route("/reports/discounts", methods=["GET"])
@login_required
def discount_report():
    check = require_account()
    if check:
        return check
    # Obter parâmetros do filtro
    month = request.args.get("month", datetime.now().month, type=int)
    year = request.args.get("year", datetime.now().year, type=int)
    years = range(datetime.now().year - 5, datetime.now().year + 1)

    # Buscar transações com desconto
    transactions = (
        Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.discount > 0,
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        )
        .order_by(Transaction.date.desc())
        .all()
    )

    # Função auxiliar para calcular o valor final
    def get_final_value(transaction):
        amount = float(transaction.amount or 0)
        discount = float(transaction.discount or 0)
        return amount - discount

    # Calcular totais
    total_expenses = sum(float(t.amount or 0) for t in transactions)
    total_discounts = sum(float(t.discount or 0) for t in transactions)
    total_final = sum(get_final_value(t) for t in transactions)

    # Função auxiliar para garantir valor float
    def safe_float(value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    # Preparar transações para o template
    transactions_for_template = []
    for t in transactions:
        transactions_for_template.append(
            {
                "date": t.date,
                "category": t.category,
                "expense": t.expense,
                "description": t.description,
                "amount": safe_float(t.amount),
                "discount": safe_float(t.discount),
                "due_date": t.due_date,
                "payment_date": t.payment_date,
                "payment_method": t.payment_method,
                "paid": t.paid,
            }
        )

    # Calcular totais por categoria
    category_totals = {}
    for transaction in transactions:
        category_id = transaction.category_id
        if category_id not in category_totals:
            category_totals[category_id] = {
                "name": transaction.category.name,
                "total_amount": 0.0,
                "total_discount": 0.0,
            }
        category_totals[category_id]["total_amount"] += safe_float(transaction.amount)
        category_totals[category_id]["total_discount"] += safe_float(
            transaction.discount
        )

    categories = list(category_totals.values())

    return render_template(
        "discount_report.html",
        transactions=transactions_for_template,
        month=month,
        year=year,
        years=years,
        total_amount=safe_float(total_expenses),
        total_discount=safe_float(total_discounts),
        total_final=safe_float(total_final),
        total_transactions=len(transactions),
        categories=categories,
    )


@transaction_bp.route("/reports/payment_method_expenses", methods=["GET"])
@login_required
def payment_method_expense_report():
    check = require_account()
    if check:
        return check
    # Obter parâmetros do filtro
    payment_method_id = request.args.get("payment_method_id", type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    year = request.args.get("year", datetime.now().year, type=int)
    years = range(datetime.now().year - 5, datetime.now().year + 1)

    # Construir a consulta base - apenas despesas
    query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "despesa",  # Apenas despesas
        extract("month", Transaction.date) == month,
        extract("year", Transaction.date) == year,
    )

    # Aplicar filtro de forma de pagamento se especificado
    if payment_method_id:
        query = query.filter(Transaction.payment_method_id == payment_method_id)

    # Executar a consulta
    transactions = query.order_by(Transaction.date.desc()).all()

    # Função auxiliar para calcular o valor final
    def get_final_value(transaction):
        amount = float(transaction.amount or 0)
        discount = float(transaction.discount or 0)
        return amount - discount

    # Função auxiliar para garantir valor float
    def safe_float(value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    # Calcular totais usando valores finais
    total_amount = sum(get_final_value(t) for t in transactions)
    total_discount = sum(float(t.discount or 0) for t in transactions)
    total_original = sum(float(t.amount or 0) for t in transactions)

    # Obter todas as formas de pagamento para o select
    payment_methods = PaymentMethod.query.filter_by(is_active=True).all()

    # Preparar transações para o template
    transactions_for_template = []
    for t in transactions:
        transactions_for_template.append(
            {
                "date": t.date,
                "category": t.category,
                "expense": t.expense,
                "description": t.description,
                "amount": safe_float(t.amount),
                "discount": safe_float(t.discount),
                "due_date": t.due_date,
                "payment_date": t.payment_date,
                "payment_method": t.payment_method,
                "paid": t.paid,
            }
        )

    # Calcular totais por forma de pagamento
    payment_method_totals = {}
    for method in payment_methods:
        method_transactions = [
            t for t in transactions if t.payment_method_id == method.id
        ]
        method_original = sum(safe_float(t.amount) for t in method_transactions)
        method_discount = sum(safe_float(t.discount) for t in method_transactions)
        method_final = sum(
            safe_float(t.amount) - safe_float(t.discount) for t in method_transactions
        )
        payment_method_totals[method.id] = {
            "name": method.name,
            "original": method_original,
            "discount": method_discount,
            "final": method_final,
            "count": len(method_transactions),
        }

    return render_template(
        "payment_method_expense_report.html",
        transactions=transactions_for_template,
        payment_methods=payment_methods,
        selected_method_id=payment_method_id,
        month=month,
        year=year,
        years=years,
        total_original=safe_float(total_original),
        total_discount=safe_float(total_discount),
        total_amount=safe_float(total_amount),
        payment_method_totals=payment_method_totals,
        total_transactions=len(transactions),
    )


@transaction_bp.route("/transactions")
@login_required
def transactions():
    page = request.args.get("page", 1, type=int)
    per_page = 10  # número de itens por página

    # Obter o mês e ano atual
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    # Mapeamento dos meses em português
    meses = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }

    # Construir a consulta base para despesas
    expense_query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "despesa",
        or_(
            # Filtrar por data de vencimento no mês
            and_(
                extract("month", Transaction.due_date) == current_month,
                extract("year", Transaction.due_date) == current_year,
            ),
            # OU filtrar por data de pagamento no mês
            and_(
                extract("month", Transaction.payment_date) == current_month,
                extract("year", Transaction.payment_date) == current_year,
            ),
        ),
    )

    # Construir a consulta base para receitas
    income_query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "receita",
        extract("month", Transaction.payment_date) == current_month,
        extract("year", Transaction.payment_date) == current_year,
    )

    # Combinar as queries
    query = expense_query.union(income_query)

    # Executar a consulta e ordenar por due_date para despesas e payment_date para receitas
    transactions = query.order_by(
        Transaction.type.desc(),  # Despesas primeiro
        Transaction.due_date.asc(),  # Ordenar por due_date
    ).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "list_transactions.html",
        transactions=transactions,
        current_month=f"{meses[current_month]} {current_year}",
    )


@transaction_bp.route("/transactions/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    form = TransactionForm()

    # Obter conta_id da URL se fornecido
    conta_id_from_url = request.args.get('conta_id', type=int)

    # Preencher as opções de categorias
    form.category_id.choices = [(cat.id, cat.name) for cat in Category.query.all()]
    # Preencher as opções de formas de pagamento
    form.payment_method_id.choices = [
        (pm.id, pm.name) for pm in PaymentMethod.query.filter_by(is_active=True).all()
    ]
    # Preencher as opções de descrições predefinidas
    form.expense_id.choices = [(0, "Selecione uma descrição")] + [
        (exp.id, exp.name) for exp in Expense.query.all()
    ]
    # Preencher as opções de contas
    form.conta_id.choices = [(c.id, c.nome) for c in Conta.query.filter_by(user_id=current_user.id).all()]

    # Se conta_id foi fornecido na URL, pré-selecionar essa conta
    if conta_id_from_url:
        form.conta_id.data = conta_id_from_url
    
    # Pré-preencher campos se vier de uma replicação (GET request com parâmetros)
    if request.method == 'GET' and request.args:
        if request.args.get('type'):
            form.type.data = request.args.get('type')
        if request.args.get('category_id'):
            form.category_id.data = int(request.args.get('category_id'))
        if request.args.get('expense_id'):
            expense_id = request.args.get('expense_id')
            if expense_id:
                form.expense_id.data = int(expense_id)
        if request.args.get('description'):
            form.description.data = request.args.get('description')
        if request.args.get('amount'):
            # Converter para formato brasileiro (vírgula como decimal, ponto como milhar)
            amount = float(request.args.get('amount'))
            # Formatar com 2 casas decimais, vírgula como separador decimal
            amount_str = f"{amount:.2f}".replace('.', ',')
            # Adicionar pontos como separadores de milhar
            parts = amount_str.split(',')
            integer_part = parts[0]
            # Adicionar pontos a cada 3 dígitos
            integer_part = '{:,}'.format(int(integer_part)).replace(',', '.')
            form.amount.data = f"{integer_part},{parts[1]}"
        if request.args.get('discount'):
            discount = float(request.args.get('discount'))
            # Formatar com 2 casas decimais, vírgula como separador decimal
            discount_str = f"{discount:.2f}".replace('.', ',')
            # Adicionar pontos como separadores de milhar
            parts = discount_str.split(',')
            integer_part = parts[0]
            # Adicionar pontos a cada 3 dígitos
            integer_part = '{:,}'.format(int(integer_part)).replace(',', '.')
            form.discount.data = f"{integer_part},{parts[1]}"
        if request.args.get('payment_method_id'):
            payment_method_id = request.args.get('payment_method_id')
            if payment_method_id:
                form.payment_method_id.data = int(payment_method_id)
        if request.args.get('paid'):
            form.paid.data = request.args.get('paid') == '1'
        if request.args.get('recurrence'):
            form.recurrence.data = request.args.get('recurrence')
        if request.args.get('details'):
            form.details.data = request.args.get('details')
        if request.args.get('notes'):
            form.notes.data = request.args.get('notes')
        if request.args.get('conta_id'):
            conta_id = request.args.get('conta_id')
            if conta_id:
                form.conta_id.data = int(conta_id)
        if request.args.get('date'):
            form.date.data = datetime.strptime(request.args.get('date'), '%Y-%m-%d').date()
        if request.args.get('due_date'):
            form.due_date.data = datetime.strptime(request.args.get('due_date'), '%Y-%m-%d').date()
        if request.args.get('payment_date'):
            form.payment_date.data = datetime.strptime(request.args.get('payment_date'), '%Y-%m-%d').date()

    if form.validate_on_submit():
        if not form.category_id.data or form.category_id.data == 0:
            flash("Selecione uma categoria válida.", "danger")
            return render_template("add_edit_transaction.html", form=form, edit=False)

        # Usar conta_id da URL ou da conta atualmente selecionada
        if conta_id_from_url:
            conta_id = conta_id_from_url
        else:
            # Obter a conta atualmente selecionada
            conta_atual = get_current_conta()
            if not conta_atual:
                flash("Você precisa ter pelo menos uma conta cadastrada.", "warning")
                return redirect(url_for("conta.listar_contas"))
            conta_id = conta_atual.id

        # Os valores já foram validados e convertidos no form.validate_on_submit()
        amount = float(form.amount.data)
        discount = float(form.discount.data) if form.discount.data else 0.0

        transaction = Transaction(
            type=form.type.data,
            date=form.date.data,
            due_date=form.due_date.data,
            category_id=form.category_id.data,
            expense_id=(
                form.expense_id.data
                if form.expense_id.data and form.expense_id.data > 0
                else None
            ),
            description=form.description.data,
            amount=amount,
            discount=discount,
            payment_method_id=form.payment_method_id.data,
            paid=form.paid.data,
            payment_date=form.payment_date.data,
            recurrence=form.recurrence.data,
            details=form.details.data,  # Adicionar campo details
            notes=form.notes.data,  # Adicionar campo notes
            user_id=current_user.id,
            conta_id=conta_id,  # Vincular à conta selecionada
        )

        db.session.add(transaction)
        db.session.commit()
        Conta.recalcular_saldos()
        flash("Transação adicionada com sucesso!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("add_edit_transaction.html", form=form, edit=False)


@transaction_bp.route("/transactions/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_transaction(id):
    transaction = Transaction.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()
    form = TransactionForm(obj=transaction)

    # Preencher as opções de categorias
    form.category_id.choices = [(cat.id, cat.name) for cat in Category.query.all()]
    # Preencher as opções de formas de pagamento
    form.payment_method_id.choices = [
        (pm.id, pm.name) for pm in PaymentMethod.query.filter_by(is_active=True).all()
    ]
    # Preencher as opções de descrições predefinidas
    form.expense_id.choices = [(0, "Selecione uma descrição")] + [
        (exp.id, exp.name) for exp in Expense.query.all()
    ]
    # Preencher as opções de contas
    form.conta_id.choices = [(c.id, c.nome) for c in Conta.query.filter_by(user_id=current_user.id).all()]

    if form.validate_on_submit():
        # Os valores já foram validados e convertidos no form.validate_on_submit()
        amount = float(form.amount.data)
        discount = float(form.discount.data) if form.discount.data else 0.0

        transaction.type = form.type.data
        transaction.date = form.date.data
        transaction.due_date = form.due_date.data
        transaction.category_id = form.category_id.data
        transaction.expense_id = (
            form.expense_id.data
            if form.expense_id.data and form.expense_id.data > 0
            else None
        )
        transaction.description = form.description.data
        transaction.amount = amount
        transaction.discount = discount
        transaction.payment_method_id = form.payment_method_id.data
        transaction.paid = form.paid.data
        transaction.payment_date = form.payment_date.data
        transaction.recurrence = form.recurrence.data
        transaction.details = form.details.data  # Adicionado para salvar detalhes na edição
        transaction.notes = form.notes.data  # Adicionar campo notes na edição
        transaction.conta_id = form.conta_id.data if form.conta_id.data else None

        db.session.commit()
        Conta.recalcular_saldos()
        flash("Transação atualizada com sucesso!", "success")
        return redirect(url_for("transaction.reports"))

    # Definir o valor atual da conta no formulário
    form.conta_id.data = transaction.conta_id
    
    return render_template(
        "add_edit_transaction.html", form=form, transaction=transaction, edit=True
    )


@transaction_bp.route("/transactions/replicate/<int:id>")
@login_required
def replicate_transaction(id):
    transaction = Transaction.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()
    
    # Redirecionar para a página de adicionar com os dados da transação na query string
    params = {
        'type': transaction.type,
        'category_id': transaction.category_id,
        'expense_id': transaction.expense_id or '',
        'description': transaction.description or '',
        'amount': transaction.amount,
        'discount': transaction.discount or 0,
        'payment_method_id': transaction.payment_method_id or '',
        'paid': '1' if transaction.paid else '0',
        'recurrence': transaction.recurrence or 'nenhuma',
        'details': transaction.details or '',
        'notes': transaction.notes or '',
        'conta_id': transaction.conta_id or '',
    }
    
    # Adicionar datas se existirem
    if transaction.date:
        params['date'] = transaction.date.strftime('%Y-%m-%d')
    if transaction.due_date:
        params['due_date'] = transaction.due_date.strftime('%Y-%m-%d')
    if transaction.payment_date:
        params['payment_date'] = transaction.payment_date.strftime('%Y-%m-%d')
    
    # Construir URL com parâmetros codificados
    base_url = url_for('transaction.add_transaction')
    url = f"{base_url}?{urlencode(params)}"
    return redirect(url)


@transaction_bp.route("/transactions/delete/<int:id>")
@login_required
def delete_transaction(id):
    transaction = Transaction.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    Conta.recalcular_saldos()
    flash("Transação excluída com sucesso!", "success")
    return redirect(url_for("transaction.reports"))


@transaction_bp.route("/expenses/by-category/<int:category_id>")
@login_required
def get_expenses(category_id):
    expenses = Expense.query.filter_by(category_id=category_id).all()
    return jsonify([{"id": exp.id, "name": exp.name} for exp in expenses])


@transaction_bp.route("/categories/by-type/<string:type>")
@login_required
def get_categories_by_type(type):
    try:
        # Buscar categorias do tipo específico
        type_categories = Category.query.filter_by(type=type).all()

        # Buscar categorias não exclusivas (que podem ser usadas em qualquer tipo)
        # Garantir que exclusive seja False (não None)
        non_exclusive_categories = Category.query.filter(
            Category.exclusive.is_(False)  # Usar is_ para comparação com False
        ).all()

        # Combinar as duas listas, evitando duplicatas
        all_categories = list(set(type_categories + non_exclusive_categories))

        # Ordenar por nome
        all_categories.sort(key=lambda x: x.name)

        return jsonify([{"id": cat.id, "name": cat.name} for cat in all_categories])
    except Exception as e:
        print(f"Erro ao buscar categorias: {str(e)}")  # Log do erro
        return jsonify([])  # Retorna lista vazia em caso de erro


def require_account():
    if Conta.query.filter_by(user_id=current_user.id).count() == 0:
        flash("Cadastre ao menos uma conta para acessar esta funcionalidade.", "warning")
        return redirect(url_for("conta.listar_contas"))
    return None

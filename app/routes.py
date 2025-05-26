from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from app import db, mail
from app.models import Expense, PaymentMethod, User, Category, Transaction
from app.forms import (
    ExpenseForm,
    LoginForm,
    PaymentMethodForm,
    RegistrationForm,
    TransactionForm,
    CategoryForm,
    RequestResetForm,
    ResetPasswordForm,
)
from sqlalchemy import func, extract, desc
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


# Rotas principais
@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


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
        flash("Cadastro realizado com sucesso! Agora você pode fazer login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("add_register.html", form=form)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    # Obter o mês e ano atual
    current_month = datetime.now().month
    current_year = datetime.now().year

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

    # Buscar transações recentes de receita do mês atual
    recent_income = (
        Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "receita",
            extract("month", Transaction.date) == current_month,
            extract("year", Transaction.date) == current_year,
        )
        .order_by(Transaction.date.desc())
        .limit(5)
        .all()
    )

    # Buscar transações recentes de despesa do mês atual
    recent_expenses = (
        Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "despesa",
            extract("month", Transaction.date) == current_month,
            extract("year", Transaction.date) == current_year,
        )
        .order_by(Transaction.date.desc())
        .limit(5)
        .all()
    )

    # Buscar transações do mês atual
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

    # Calcular o total de receitas e despesas do mês atual (usando valores finais)
    income_total = (
        db.session.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "receita",
            extract("month", Transaction.date) == current_month,
            extract("year", Transaction.date) == current_year,
        )
        .scalar()
        or 0
    )

    # Para despesas, precisamos calcular o valor final (amount - discount)
    expense_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "despesa",
        extract("month", Transaction.date) == current_month,
        extract("year", Transaction.date) == current_year,
    ).all()
    expense_total = sum(get_final_value(t) for t in expense_transactions)

    # Calcular o saldo do mês
    balance = income_total - expense_total

    # Obter as categorias de despesas com maiores gastos no mês (usando valores finais)
    expense_by_category = (
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
        .group_by(Category.name)
        .all()
    )

    # Calcular totais finais por categoria (amount - discount)
    top_expense_categories = [
        (cat, (total_amount or 0) - (total_discount or 0))
        for cat, total_amount, total_discount in expense_by_category
    ]
    top_expense_categories.sort(key=lambda x: x[1], reverse=True)
    top_expense_categories = top_expense_categories[:5]

    # Obter as categorias de receitas com maiores valores no mês
    top_income_categories = (
        db.session.query(Category.name, func.sum(Transaction.amount).label("total"))
        .join(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "receita",
            extract("month", Transaction.date) == current_month,
            extract("year", Transaction.date) == current_year,
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
        .all()
    )

    # Obter dados para o gráfico de evolução mensal (últimos 6 meses)
    monthly_data = []
    for i in range(5, -1, -1):
        # Calcular o mês e ano para cada um dos últimos 6 meses
        month = current_month - i
        year = current_year

        # Ajustar o ano se o mês for negativo
        while month <= 0:
            month += 12
            year -= 1

        # Obter o total de receitas para este mês
        month_income = (
            db.session.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "receita",
                extract("month", Transaction.date) == month,
                extract("year", Transaction.date) == year,
            )
            .scalar()
            or 0
        )

        # Obter transações de despesa para este mês e calcular valores finais
        month_expense_transactions = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "despesa",
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        ).all()
        month_expense = sum(get_final_value(t) for t in month_expense_transactions)

        # Obter o nome do mês
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

    # Serializar os dados para JSON usando json.dumps
    expense_chart_json = json.dumps(expense_chart_data, ensure_ascii=False)
    income_chart_json = json.dumps(income_chart_data, ensure_ascii=False)
    monthly_data_json = json.dumps(monthly_data, ensure_ascii=False)

    # Debug: Verificar os dados antes de enviar para o template
    print("Monthly Data JSON:", monthly_data_json)
    print("Expense Chart JSON:", expense_chart_json)
    print("Income Chart JSON:", income_chart_json)

    # Calcular estatísticas adicionais
    total_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract("month", Transaction.date) == current_month,
        extract("year", Transaction.date) == current_year,
    ).count()

    # Calcular a média diária de despesas (usando valores finais)
    days_in_month = monthrange(current_year, current_month)[1]
    daily_avg_expense = expense_total / days_in_month if days_in_month > 0 else 0

    # Calcular a projeção para o final do mês (usando valores finais)
    current_day = datetime.now().day
    projected_expense = (
        (expense_total / current_day) * days_in_month if current_day > 0 else 0
    )

    # Verificar transações pendentes
    pending_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id, Transaction.paid == "False"
    ).count()

    return render_template(
        "dashboard.html",
        monthly_transactions=monthly_transactions,
        recent_income=recent_income,
        recent_expenses=recent_expenses,
        income_total=income_total,
        expense_total=expense_total,
        balance=balance,
        top_expense_categories=top_expense_categories,
        top_income_categories=top_income_categories,
        expense_chart_json=expense_chart_json,
        income_chart_json=income_chart_json,
        monthly_data_json=monthly_data_json,
        total_transactions=total_transactions,
        daily_avg_expense=daily_avg_expense,
        projected_expense=projected_expense,
        pending_transactions=pending_transactions,
        current_month=f"{meses[current_month]} {current_year}",
        datetime=datetime,
        monthrange=monthrange,
    )


@main_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


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

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    # Verifica se o logout foi chamado como parte do processo de shutdown
    if request.args.get("shutdown") == "true":
        return redirect(url_for("shutdown"))
    return redirect(url_for("main.index"))


@transaction_bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    categories = Category.query.order_by(desc(Category.id)).all()
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

    context = {"categories": categories, "form": form, "edit": False}

    return render_template("list_categories.html", **context)


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

    return render_template("add_category.html", form=form, edit=True)


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


@transaction_bp.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():
    expenses = Expense.query.order_by(desc(Expense.id)).all()
    form = ExpenseForm()

    # Preencher as opções de categorias
    form.category_id.choices = [(cat.id, cat.name) for cat in Category.query.all()]

    if form.validate_on_submit():
        expense = Expense(name=form.name.data, category_id=form.category_id.data)

        db.session.add(expense)
        db.session.commit()
        flash("Descrição adicionada com sucesso!", "success")
        return redirect(url_for("transaction.expenses"))

    else:
        print(form.errors)  # Isso ajudará a encontrar os erros de validação

    context = {"expenses": expenses, "form": form, "edit": False}

    return render_template("list_expensives.html", **context)


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

    return render_template("add_expense.html", form=form, edit=True)


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


@transaction_bp.route("/payment_methods", methods=["GET", "POST"])
@login_required
def list_payment_methods():
    methods = PaymentMethod.query.all()
    return render_template("list_payment_method.html", methods=methods)


@transaction_bp.route("/payment_method/add", methods=["GET", "POST"])
@login_required
def add_payment_method():
    form = PaymentMethodForm()

    if form.validate_on_submit():
        payment_method = PaymentMethod(
            name=form.name.data, is_active=form.is_active.data
        )
        db.session.add(payment_method)
        db.session.commit()
        flash("Método de pagamento adicionado com sucesso!", "success")
        return redirect(url_for("payment_methods"))

    return render_template("add_payment_method.html", form=form)


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
        return redirect(url_for("list_payment_methods"))
    return render_template("payment_method_form.html", form=form)


@transaction_bp.route("/payment_methods/delete/<int:id>", methods=["POST"])
@login_required
def delete_payment_method(id):
    method = PaymentMethod.query.get_or_404(id)
    db.session.delete(method)
    db.session.commit()
    flash("Método de pagamento removido!", "danger")
    return redirect(url_for("list_payment_methods"))


@transaction_bp.route("/reports")
@login_required
def reports():
    report_type = request.args.get("type", "monthly")
    year = request.args.get("year", datetime.now().year, type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    payment_method_id = request.args.get("payment_method_id", type=int)
    show_discount_only = request.args.get("show_discount_only", type=bool)
    years = range(datetime.now().year - 5, datetime.now().year + 1)

    # Função auxiliar para calcular o valor final
    def get_final_value(transaction):
        amount = float(transaction.amount or 0)
        discount = float(transaction.discount or 0)
        return amount - discount

    # Obter todas as formas de pagamento para o select
    payment_methods = PaymentMethod.query.filter_by(is_active=True).all()

    # Construir a consulta base para transações
    query = Transaction.query.filter(Transaction.user_id == current_user.id)

    # Aplicar filtros comuns
    if report_type != "annual":
        query = query.filter(
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        )
    else:
        query = query.filter(extract("year", Transaction.date) == year)

    # Aplicar filtro de forma de pagamento se especificado
    if payment_method_id:
        query = query.filter(Transaction.payment_method_id == payment_method_id)

    # Aplicar filtro de descontos se especificado
    if show_discount_only:
        query = query.filter(Transaction.discount > 0)

    # Executar a consulta e calcular totais
    transactions = query.order_by(Transaction.date.desc()).all()
    total_original = sum(float(t.amount or 0) for t in transactions)
    total_discount = sum(float(t.discount or 0) for t in transactions)
    total_final = sum(get_final_value(t) for t in transactions)

    if report_type == "monthly":
        # Filtrar transações por tipo para cálculos específicos
        income_transactions = [t for t in transactions if t.type == "receita"]
        expense_transactions = [t for t in transactions if t.type == "despesa"]

        income_by_category = (
            db.session.query(Category.name, func.sum(Transaction.amount))
            .join(Transaction)
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "receita",
                extract("month", Transaction.date) == month,
                extract("year", Transaction.date) == year,
            )
        )
        if payment_method_id:
            income_by_category = income_by_category.filter(
                Transaction.payment_method_id == payment_method_id
            )
        income_by_category = income_by_category.group_by(Category.name).all()

        expense_by_category = (
            db.session.query(
                Category.name,
                func.sum(Transaction.amount).label("total_amount"),
                func.sum(Transaction.discount).label("total_discount"),
            )
            .join(Transaction)
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "despesa",
                extract("month", Transaction.date) == month,
                extract("year", Transaction.date) == year,
            )
        )
        if payment_method_id:
            expense_by_category = expense_by_category.filter(
                Transaction.payment_method_id == payment_method_id
            )
        expense_by_category = expense_by_category.group_by(Category.name).all()

        # Calcular totais finais por categoria
        income_total = sum(float(total or 0) for _, total in income_by_category)
        expense_total = sum(
            float(total_amount or 0) - float(total_discount or 0)
            for _, total_amount, total_discount in expense_by_category
        )
        balance = float(income_total - expense_total)

        # Preparar dados para os gráficos
        income_chart_data = [
            {"name": name, "value": float(total or 0)}
            for name, total in income_by_category
        ]
        expense_chart_data = [
            {
                "name": name,
                "value": float(total_amount or 0) - float(total_discount or 0),
            }
            for name, total_amount, total_discount in expense_by_category
        ]

        # Calcular dados diários
        days_in_month = monthrange(year, month)[1]
        daily_data = []
        receita_acumulada = 0
        despesa_acumulada = 0
        saldo = 0

        for day in range(1, days_in_month + 1):
            current_date = datetime(year, month, day).date()
            if current_date > datetime.now().date():
                break

            # Calcular receitas do dia
            receita_dia = sum(
                float(t.amount or 0)
                for t in income_transactions
                if t.date.date() == current_date
            )

            # Calcular despesas do dia (usando valores finais)
            despesa_dia = sum(
                get_final_value(t)
                for t in expense_transactions
                if t.date.date() == current_date
            )

            receita_acumulada += float(receita_dia)
            despesa_acumulada += float(despesa_dia)
            saldo = receita_acumulada - despesa_acumulada

            daily_data.append(
                {
                    "day": f"{day:02d}",
                    "receita": receita_acumulada,
                    "despesa": despesa_acumulada,
                    "balance": saldo,
                }
            )

        return render_template(
            "reports.html",
            transactions=transactions,
            report_type=report_type,
            year=year,
            month=month,
            years=years,
            payment_methods=payment_methods,
            selected_method_id=payment_method_id,
            show_discount_only=show_discount_only,
            income_total=float(income_total),
            expense_total=float(expense_total),
            balance=balance,
            income_by_category=income_by_category,
            expense_by_category=expense_by_category,
            income_chart_data=json.dumps(income_chart_data),
            expense_chart_data=json.dumps(expense_chart_data),
            daily_data=daily_data,
            month_name=datetime(year, month, 1).strftime("%B"),
            total_original=total_original,
            total_discount=total_discount,
            total_final=total_final,
        )

    elif report_type == "annual":
        # ... rest of the annual report code ...
        return render_template(
            "reports.html",
            report_type=report_type,
            transactions=transactions,
            year=year,
            years=years,
            payment_methods=payment_methods,
            selected_method_id=payment_method_id,
            monthly_data=json.dumps(monthly_data),
            annual_income=annual_income,
            annual_expense=annual_expense,
            annual_balance=annual_balance,
            top_expense_categories=top_expense_categories,
            top_income_categories=top_income_categories,
            top_expense_chart_data=json.dumps(top_expense_chart_data),
            top_income_chart_data=json.dumps(top_income_chart_data),
            total_original=total_original,
            total_discount=total_discount,
            total_final=total_final,
        )

    elif report_type == "category":
        # ... rest of the category report code ...
        return render_template(
            "reports.html",
            report_type=report_type,
            year=year,
            years=years,
            payment_methods=payment_methods,
            selected_method_id=payment_method_id,
            categories=categories,
            selected_category=category,
            transactions=transactions,
            monthly_data=json.dumps(monthly_data),
            annual_total=annual_total,
            total_original=total_original,
            total_discount=total_discount,
            total_final=total_final,
        )

    # Tipo de relatório inválido
    return redirect(url_for("transaction.reports", type="monthly"))


@transaction_bp.route("/export")
@login_required
def export_data():
    # Implementação futura para exportação de dados
    flash("Funcionalidade de exportação será implementada em breve!", "info")
    return redirect(url_for("transaction.reports"))


def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for("auth.reset_token", token=token, _external=True)

    print("\n" + "=" * 50)
    print("EMAIL DE RECUPERAÇÃO DE SENHA (CONSOLE)")
    print("=" * 50)
    print(f"De: {current_app.config['MAIL_DEFAULT_SENDER']}")
    print(f"Para: {user.email}")
    print(f"Assunto: Recuperação de Senha - Finanças Pessoais")
    print("-" * 50)
    print("Conteúdo do email:")
    print(f"Para redefinir sua senha, visite o seguinte link:")
    print(f"{reset_url}")
    print(
        "\nSe você não solicitou esta recuperação de senha, simplesmente ignore este email."
    )
    print("=" * 50 + "\n")

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

    # Buscar transações do usuário atual do mês atual com paginação
    transactions = (
        Transaction.query.filter(
            Transaction.user_id == current_user.id,
            extract("month", Transaction.date) == current_month,
            extract("year", Transaction.date) == current_year,
        )
        .order_by(Transaction.date.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template(
        "list_transactions.html",
        transactions=transactions,
        current_month=f"{meses[current_month]}/{current_year}",
    )


@transaction_bp.route("/transactions/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    form = TransactionForm()

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

    if form.validate_on_submit():
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
            amount=form.amount.data,
            discount=form.discount.data or 0,
            payment_method_id=form.payment_method_id.data,
            paid=form.paid.data,
            user_id=current_user.id,
        )

        db.session.add(transaction)
        db.session.commit()
        flash("Transação adicionada com sucesso!", "success")
        return redirect(url_for("transaction.transactions"))

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

    if form.validate_on_submit():
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
        transaction.amount = form.amount.data
        transaction.discount = form.discount.data or 0
        transaction.payment_method_id = form.payment_method_id.data
        transaction.paid = form.paid.data
        transaction.payment_date = form.payment_date.data

        db.session.commit()
        flash("Transação atualizada com sucesso!", "success")
        return redirect(url_for("transaction.transactions"))

    return render_template(
        "add_edit_transaction.html", form=form, transaction=transaction, edit=True
    )


@transaction_bp.route("/transactions/delete/<int:id>")
@login_required
def delete_transaction(id):
    transaction = Transaction.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    flash("Transação excluída com sucesso!", "success")
    return redirect(url_for("transaction.transactions"))


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

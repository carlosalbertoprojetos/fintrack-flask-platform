from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Expense, PaymentMethod, User, Category, Transaction
from app.forms import (
    ExpenseForm,
    LoginForm,
    PaymentMethodForm,
    RegistrationForm,
    TransactionForm,
    CategoryForm,
)
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from calendar import monthrange
import json

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

    return render_template("register.html", form=form)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    # Obter o mês e ano atual
    current_month = datetime.now().month
    current_year = datetime.now().year

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

    # Calcular o total de receitas e despesas do mês atual
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

    expense_total = (
        db.session.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "despesa",
            extract("month", Transaction.date) == current_month,
            extract("year", Transaction.date) == current_year,
        )
        .scalar()
        or 0
    )

    # Calcular o saldo do mês
    balance = income_total - expense_total

    # Obter as categorias de despesas com maiores gastos no mês
    top_expense_categories = (
        db.session.query(Category.name, func.sum(Transaction.amount).label("total"))
        .join(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "despesa",
            extract("month", Transaction.date) == current_month,
            extract("year", Transaction.date) == current_year,
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
        .all()
    )

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

        # Obter o total de receitas e despesas para este mês
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

        month_expense = (
            db.session.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "despesa",
                extract("month", Transaction.date) == month,
                extract("year", Transaction.date) == year,
            )
            .scalar()
            or 0
        )

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

    # Calcular estatísticas adicionais
    total_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract("month", Transaction.date) == current_month,
        extract("year", Transaction.date) == current_year,
    ).count()

    # Calcular a média diária de despesas
    days_in_month = monthrange(current_year, current_month)[1]
    daily_avg_expense = expense_total / days_in_month if days_in_month > 0 else 0

    # Calcular a projeção para o final do mês
    current_day = datetime.now().day
    projected_expense = (
        (expense_total / current_day) * days_in_month if current_day > 0 else 0
    )

    # Verificar transações pendentes
    pending_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id, Transaction.paid == "False"
    ).count()

    # Converter dados para JSON para uso nos gráficos
    expense_chart_json = json.dumps(expense_chart_data)
    income_chart_json = json.dumps(income_chart_data)
    monthly_data_json = json.dumps(monthly_data)

    return render_template(
        "dashboard.html",
        monthly_transactions=monthly_transactions,
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
        current_month=datetime.now().strftime("%B %Y"),
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
    return redirect(url_for("main.index"))


@transaction_bp.route("/categories")
@login_required
def categories():
    categories = Category.query.all()
    return render_template("add_categories.html", categories=categories)


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

    # Se houver erros no formulário, exibe um alerta
    if form.errors:
        flash("Erro ao adicionar categoria. Verifique os campos.", "danger")
        print(form.errors)  # Depuração no console

    return render_template("add_category.html", form=form, edit=False)


@transaction_bp.route("/categories/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data
        category.type = form.type.data
        category.exclusive = form.exclusive.data  # Usando o valor booleano diretamente
        category.icon = form.icon.data
        category.color = form.color.data
        db.session.commit()
        flash("Categoria atualizada com sucesso!", "success")
        return redirect(url_for("transaction.categories"))

    return render_template("add_category.html", form=form, edit=True)


@transaction_bp.route("/categories/delete/<int:id>")
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


@transaction_bp.route("/expenses")
@login_required
def expenses():
    expenses = Expense.query.all()
    return render_template("list_expensive.html", expenses=expenses)


@transaction_bp.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    form = ExpenseForm()

    if form.validate_on_submit():
        exclusive = (
            form.exclusive.data == "True"
        )  # Isto garante que 'True' se torna um booleano True

        expense = Expense(name=form.name.data, exclusive=exclusive)

        db.session.add(expense)
        db.session.commit()
        flash("Descrição predefinida adicionada com sucesso!", "success")
        return redirect(url_for("transaction_bp.expenses"))
    else:
        print(form.errors)  # Isso ajudará a encontrar os erros de validação

    return render_template("add_expense.html", form=form, edit=False)


@transaction_bp.route("/expenses/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    form = ExpenseForm(obj=expense)

    if form.validate_on_submit():
        expense.name = form.name.data
        expense.exclusive = form.exclusive.data  # Atualizar com o valor do formulário
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


@transaction_bp.route("/payment_methods", methods=["GET"])
@login_required
def list_payment_methods():
    methods = PaymentMethod.query.all()
    return render_template("payment_methods.html", methods=methods)


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


@transaction_bp.route("/")
@login_required
def transactions():
    # Filtros
    type_filter = request.args.get("type", "all")
    category_filter = request.args.get("category", "all")
    month_filter = request.args.get("month", datetime.now().month)
    year_filter = request.args.get("year", datetime.now().year)

    # Converter para inteiros se necessário
    try:
        month_filter = int(month_filter)
        year_filter = int(year_filter)
    except ValueError:
        month_filter = datetime.now().month
        year_filter = datetime.now().year

    # Construir a consulta base
    query = Transaction.query.filter(Transaction.user_id == current_user.id)

    # Aplicar filtros
    if type_filter != "all":
        query = query.filter(Transaction.type == type_filter)

    if category_filter != "all":
        query = query.filter(Transaction.category_id == category_filter)

    # Verificação de tipo de mês e ano
    if month_filter != "all" and year_filter != "all":
        query = query.filter(
            extract("month", Transaction.date) == month_filter,
            extract("year", Transaction.date) == year_filter,
        )

    # Ordenar por data (mais recente primeiro)
    transactions = query.order_by(Transaction.date.desc()).all()

    # Obter todas as categorias para o filtro
    categories = Category.query.all()

    # Calcular totais
    income_total = sum(t.amount for t in transactions if t.type == "receita")
    expense_total = sum(t.amount for t in transactions if t.type == "despesa")
    balance = income_total - expense_total

    # Preparar dados para o gráfico de distribuição por categoria
    category_data = {}
    for transaction in transactions:
        if transaction.category:
            category_name = transaction.category.name
            if category_name not in category_data:
                category_data[category_name] = 0
            category_data[category_name] += transaction.amount

    # Converter para formato adequado para o gráfico
    category_chart_data = [
        {"name": cat, "value": val} for cat, val in category_data.items()
    ]
    category_chart_json = json.dumps(category_chart_data)

    return render_template(
        "transactions.html",
        transactions=transactions,
        categories=categories,
        income_total=income_total,
        expense_total=expense_total,
        balance=balance,
        type_filter=type_filter,
        category_filter=category_filter,
        month_filter=month_filter,
        year_filter=year_filter,
        category_chart_json=category_chart_json,
        current_year=datetime.now().year,
    )


@transaction_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    form = TransactionForm()

    # Preencher as opções de categorias, despesas e métodos de pagamento
    form.category_id.choices = [(cat.id, cat.name) for cat in Category.query.all()]
    form.expense_id.choices = [
        (expense.id, expense.name) for expense in Expense.query.all()
    ]
    form.payment_method_id.choices = [
        (payment_method.id, payment_method.name)
        for payment_method in PaymentMethod.query.all()
    ]

    if form.validate_on_submit():
        transaction = Transaction(
            date=form.date.data,
            description=form.description.data,
            amount=form.amount.data,
            type=form.type.data,
            category_id=form.category_id.data,
            expense_id=form.expense_id.data,
            payment_method_id=form.payment_method_id.data,
            paid=form.paid.data,
            notes=form.notes.data,
        )
        db.session.add(transaction)
        db.session.commit()
        flash("Transação adicionada com sucesso!", "success")
        return redirect(url_for("transactions_list"))

    return render_template("add_transaction.html", form=form)


@transaction_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)

    # Verificar se a transação pertence ao usuário atual
    if transaction.user_id != current_user.id:
        flash("Você não tem permissão para editar esta transação.", "danger")
        return redirect(url_for("transaction.transactions"))

    form = TransactionForm(obj=transaction)

    # Carregar categorias
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    form.category_id.choices.insert(0, (0, "Selecione uma categoria"))

    # Carregar descrições predefinidas
    form.expense_id.choices = [(0, "Selecione uma descrição predefinida")]
    if transaction.category_id:
        category = Category.query.get(transaction.category_id)
        expenses = Expense.query.filter(
            (Expense.exclusive == category.type)
            | (Expense.exclusive.is_(None))
            | (Expense.exclusive == "")
        ).all()
        form.expense_id.choices.extend([(e.id, e.name) for e in expenses])

    if form.validate_on_submit():
        transaction.date = form.date.data
        transaction.description = form.description.data
        transaction.amount = form.amount.data
        transaction.type = form.type.data
        transaction.paid = form.paid.data
        transaction.notes = form.notes.data

        if form.category_id.data and form.category_id.data > 0:
            transaction.category_id = form.category_id.data
        else:
            transaction.category_id = None

        if form.expense_id.data and form.expense_id.data > 0:
            transaction.expense_id = form.expense_id.data
        else:
            transaction.expense_id = None

        db.session.commit()
        flash("Transação atualizada com sucesso!", "success")
        return redirect(url_for("transaction.transactions"))

    return render_template("add_transaction.html", form=form, edit=True)


@transaction_bp.route("/delete/<int:id>")
@login_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)

    # Verificar se a transação pertence ao usuário atual
    if transaction.user_id != current_user.id:
        flash("Você não tem permissão para excluir esta transação.", "danger")
        return redirect(url_for("transaction.transactions"))

    db.session.delete(transaction)
    db.session.commit()
    flash("Transação excluída com sucesso!", "success")
    return redirect(url_for("transaction.transactions"))


@transaction_bp.route("/categories/<type>")
@login_required
def get_categories(type):
    # Busca categorias que são exclusivas para o tipo selecionado ou que não são exclusivas
    categories = Category.query.filter(
        (Category.exclusive == type)
        | (Category.exclusive.is_(None))
        | (Category.exclusive == "")
    ).all()

    return jsonify({"categories": [{"id": c.id, "name": c.name} for c in categories]})


@transaction_bp.route("/reports")
@login_required
def reports():
    # Obter parâmetros de filtro
    report_type = request.args.get("type", "monthly")
    year = request.args.get("year", datetime.now().year, type=int)
    month = request.args.get("month", datetime.now().month, type=int)

    # Dados para os filtros
    years = range(datetime.now().year - 5, datetime.now().year + 1)

    # Preparar dados para o relatório
    if report_type == "monthly":
        # Relatório mensal - detalhamento por categoria no mês selecionado
        income_by_category = (
            db.session.query(Category.name, func.sum(Transaction.amount).label("total"))
            .join(Transaction)
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "receita",
                extract("month", Transaction.date) == month,
                extract("year", Transaction.date) == year,
            )
            .group_by(Category.name)
            .all()
        )

        expense_by_category = (
            db.session.query(Category.name, func.sum(Transaction.amount).label("total"))
            .join(Transaction)
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "despesa",
                extract("month", Transaction.date) == month,
                extract("year", Transaction.date) == year,
            )
            .group_by(Category.name)
            .all()
        )

        # Calcular totais
        income_total = sum(total for _, total in income_by_category)
        expense_total = sum(total for _, total in expense_by_category)
        balance = income_total - expense_total

        # Preparar dados para gráficos
        income_chart_data = [
            {"name": cat, "value": float(total)} for cat, total in income_by_category
        ]
        expense_chart_data = [
            {"name": cat, "value": float(total)} for cat, total in expense_by_category
        ]

        # Dados diários para o mês
        days_in_month = monthrange(year, month)[1]
        daily_data = []

        for day in range(1, days_in_month + 1):
            day_date = datetime(year, month, day)

            # Pular dias futuros
            if day_date > datetime.now():
                break

            day_income = (
                db.session.query(func.sum(Transaction.amount))
                .filter(
                    Transaction.user_id == current_user.id,
                    Transaction.type == "receita",
                    func.date(Transaction.date) == day_date.date(),
                )
                .scalar()
                or 0
            )

            day_expense = (
                db.session.query(func.sum(Transaction.amount))
                .filter(
                    Transaction.user_id == current_user.id,
                    Transaction.type == "despesa",
                    func.date(Transaction.date) == day_date.date(),
                )
                .scalar()
                or 0
            )

            daily_data.append(
                {
                    "day": day,
                    "receita": float(day_income),
                    "despesa": float(day_expense),
                    "balance": float(day_income - day_expense),
                }
            )

        return render_template(
            "reports.html",
            report_type=report_type,
            year=year,
            month=month,
            years=years,
            income_by_category=income_by_category,
            expense_by_category=expense_by_category,
            income_total=income_total,
            expense_total=expense_total,
            balance=balance,
            income_chart_data=json.dumps(income_chart_data),
            expense_chart_data=json.dumps(expense_chart_data),
            daily_data=json.dumps(daily_data),
            month_name=datetime(year, month, 1).strftime("%B"),
        )

    elif report_type == "annual":
        # Relatório anual - evolução mensal no ano selecionado
        monthly_data = []

        for month in range(1, 13):
            # Pular meses futuros no ano atual
            if year == datetime.now().year and month > datetime.now().month:
                break

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

            month_expense = (
                db.session.query(func.sum(Transaction.amount))
                .filter(
                    Transaction.user_id == current_user.id,
                    Transaction.type == "despesa",
                    extract("month", Transaction.date) == month,
                    extract("year", Transaction.date) == year,
                )
                .scalar()
                or 0
            )

            month_name = datetime(year, month, 1).strftime("%b")

            monthly_data.append(
                {
                    "month": month_name,
                    "receita": float(month_income),
                    "despesa": float(month_expense),
                    "balance": float(month_income - month_expense),
                }
            )

        # Calcular totais anuais
        annual_income = sum(item["receita"] for item in monthly_data)
        annual_expense = sum(item["despesa"] for item in monthly_data)
        annual_balance = annual_income - annual_expense

        # Categorias com maiores gastos no ano
        top_expense_categories = (
            db.session.query(Category.name, func.sum(Transaction.amount).label("total"))
            .join(Transaction)
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "despesa",
                extract("year", Transaction.date) == year,
            )
            .group_by(Category.name)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(5)
            .all()
        )

        # Categorias com maiores receitas no ano
        top_income_categories = (
            db.session.query(Category.name, func.sum(Transaction.amount).label("total"))
            .join(Transaction)
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == "receita",
                extract("year", Transaction.date) == year,
            )
            .group_by(Category.name)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(5)
            .all()
        )

        # Preparar dados para gráficos
        top_expense_chart_data = [
            {"name": cat, "value": float(total)}
            for cat, total in top_expense_categories
        ]
        top_income_chart_data = [
            {"name": cat, "value": float(total)} for cat, total in top_income_categories
        ]

        return render_template(
            "reports.html",
            report_type=report_type,
            year=year,
            years=years,
            monthly_data=json.dumps(monthly_data),
            annual_income=annual_income,
            annual_expense=annual_expense,
            annual_balance=annual_balance,
            top_expense_categories=top_expense_categories,
            top_income_categories=top_income_categories,
            top_expense_chart_data=json.dumps(top_expense_chart_data),
            top_income_chart_data=json.dumps(top_income_chart_data),
        )

    elif report_type == "category":
        # Relatório por categoria - análise detalhada de uma categoria específica
        category_id = request.args.get("category_id", type=int)
        categories = Category.query.all()

        if category_id:
            category = Category.query.get_or_404(category_id)

            # Transações da categoria no ano selecionado
            transactions = (
                Transaction.query.filter(
                    Transaction.user_id == current_user.id,
                    Transaction.category_id == category_id,
                    extract("year", Transaction.date) == year,
                )
                .order_by(Transaction.date.desc())
                .all()
            )

            # Evolução mensal da categoria no ano
            monthly_data = []

            for month in range(1, 13):
                # Pular meses futuros no ano atual
                if year == datetime.now().year and month > datetime.now().month:
                    break

                month_total = (
                    db.session.query(func.sum(Transaction.amount))
                    .filter(
                        Transaction.user_id == current_user.id,
                        Transaction.category_id == category_id,
                        extract("month", Transaction.date) == month,
                        extract("year", Transaction.date) == year,
                    )
                    .scalar()
                    or 0
                )

                month_name = datetime(year, month, 1).strftime("%b")

                monthly_data.append({"month": month_name, "total": float(month_total)})

            # Total anual da categoria
            annual_total = sum(item["total"] for item in monthly_data)

            return render_template(
                "reports.html",
                report_type=report_type,
                year=year,
                years=years,
                categories=categories,
                selected_category=category,
                transactions=transactions,
                monthly_data=json.dumps(monthly_data),
                annual_total=annual_total,
            )
        else:
            # Nenhuma categoria selecionada
            return render_template(
                "reports.html",
                report_type=report_type,
                year=year,
                years=years,
                categories=categories,
            )

    # Tipo de relatório inválido
    return redirect(url_for("transaction.reports", type="monthly"))


@transaction_bp.route("/export")
@login_required
def export_data():
    # Implementação futura para exportação de dados
    flash("Funcionalidade de exportação será implementada em breve!", "info")
    return redirect(url_for("transaction.transactions"))

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    session,
    Response,
    abort,
)
from urllib.parse import urlencode
from flask_login import login_user, logout_user, login_required, current_user
from app import db, mail
from app.models import Expense, PaymentMethod, User, Category, Transaction
from app.models import Conta, Investimento, MovimentacaoInvestimento
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
    AdminUserForm,
)
from sqlalchemy import func, extract, desc, or_, and_, case
from datetime import datetime, timedelta
from calendar import monthrange
import json
import time
from collections import defaultdict, deque
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer as Serializer
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from services.transaction_service import TransactionService

# Blueprints
main_bp = Blueprint("main", __name__)
auth_bp = Blueprint("auth", __name__)
transaction_bp = Blueprint("transaction", __name__)

_login_attempts = defaultdict(deque)

MONTH_NAMES_PT = {
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


def _report_years(reference_year=None, years_back=5):
    current_year = reference_year or datetime.now().year
    return range(current_year - years_back, current_year + 1)


def _login_limit_exceeded(identifier: str, max_attempts: int, window_seconds: int):
    now = time.time()
    attempts = _login_attempts[identifier]
    while attempts and (now - attempts[0]) > window_seconds:
        attempts.popleft()
    return len(attempts) >= max_attempts


def _register_failed_login(identifier: str, window_seconds: int):
    now = time.time()
    attempts = _login_attempts[identifier]
    while attempts and (now - attempts[0]) > window_seconds:
        attempts.popleft()
    attempts.append(now)


def _clear_login_attempts(identifier: str):
    _login_attempts.pop(identifier, None)


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
        return db.session.get(Conta, conta_id)
    return None


def _user_categories_query():
    return Category.query.filter_by(user_id=current_user.id)


def _user_expenses_query():
    return Expense.query.filter_by(user_id=current_user.id)


def _user_payment_methods_query():
    return PaymentMethod.query.filter_by(user_id=current_user.id)


def _user_category_or_404(category_id):
    return _user_categories_query().filter_by(id=category_id).first_or_404()


def _user_expense_or_404(expense_id):
    return _user_expenses_query().filter_by(id=expense_id).first_or_404()


def _user_payment_method_or_404(method_id):
    return _user_payment_methods_query().filter_by(id=method_id).first_or_404()


def _resolve_conta_filter(contas, requested_conta_id, *, use_current_conta=False):
    conta_filter = requested_conta_id

    if conta_filter is None:
        if use_current_conta:
            conta_atual = get_current_conta()
            if conta_atual:
                conta_filter = conta_atual.id
        else:
            conta_filter = session.get("last_conta_id")

        if conta_filter is None and contas:
            conta_filter = contas[0].id

    if conta_filter and not any(conta.id == conta_filter for conta in contas):
        conta_filter = contas[0].id if contas else None
        session["last_conta_id"] = conta_filter

    return conta_filter


def _build_category_totals(transactions, amount_getter):
    totals = {}
    for transaction in transactions:
        if not transaction.category or not transaction.category.name:
            continue

        category_name = transaction.category.name
        totals[category_name] = totals.get(category_name, 0.0) + amount_getter(transaction)

    category_rows = [
        {"category": category_name, "amount": total}
        for category_name, total in totals.items()
    ]
    category_rows.sort(key=lambda item: item["amount"], reverse=True)
    return category_rows


def _build_reports_query(*, user_id, report_type, year, month, payment_method_id, show_discount_only, conta_filter):
    if report_type != "annual":
        query = Transaction.query.filter(
            Transaction.user_id == user_id,
            or_(
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
                and_(
                    Transaction.type == "receita",
                    extract("month", Transaction.payment_date) == month,
                    extract("year", Transaction.payment_date) == year,
                ),
            ),
        )
    else:
        query = Transaction.query.filter(
            Transaction.user_id == user_id,
            or_(
                and_(
                    Transaction.type == "despesa",
                    or_(
                        extract("year", Transaction.due_date) == year,
                        extract("year", Transaction.payment_date) == year,
                    ),
                ),
                and_(
                    Transaction.type == "receita",
                    extract("year", Transaction.payment_date) == year,
                ),
            ),
        )

    if payment_method_id:
        query = query.filter(Transaction.payment_method_id == payment_method_id)
    if show_discount_only:
        query = query.filter(Transaction.discount > 0)
    if conta_filter:
        query = query.filter(Transaction.conta_id == conta_filter)
    return query


def _report_sort_date(transaction):
    if transaction.type == "despesa":
        return transaction.due_date or transaction.payment_date or datetime.min
    return transaction.payment_date or transaction.date or datetime.min


def _split_report_transactions(transactions):
    expense_transactions = sorted(
        (transaction for transaction in transactions if transaction.type == "despesa"),
        key=_report_sort_date,
    )
    income_transactions = sorted(
        (transaction for transaction in transactions if transaction.type == "receita"),
        key=_report_sort_date,
    )
    return expense_transactions, income_transactions


def _calculate_report_totals(transactions, safe_float):
    income_total = 0.0
    expense_total = 0.0
    total_discount = 0.0

    for transaction in transactions:
        amount = safe_float(transaction.amount)
        discount = safe_float(transaction.discount)
        if transaction.type == "receita":
            income_total += amount
        else:
            expense_total += amount - discount
            total_discount += discount

    return income_total, expense_total, total_discount, income_total - expense_total


def _build_annual_report_monthly_data(transactions, year, safe_float):
    monthly_data = []
    for month_number in range(1, 13):
        month_income = 0.0
        month_expense = 0.0
        month_discount = 0.0

        month_transactions = [transaction for transaction in transactions if transaction.date.month == month_number]
        for transaction in month_transactions:
            amount = safe_float(transaction.amount)
            discount = safe_float(transaction.discount)
            if transaction.type == "receita":
                month_income += amount
            else:
                month_expense += amount
                month_discount += discount

        monthly_data.append(
            {
                "month": datetime(year, month_number, 1).strftime("%b"),
                "receita": float(month_income),
                "despesa": float(month_expense - month_discount),
                "balance": float(month_income - (month_expense - month_discount)),
            }
        )

    return monthly_data


def _apply_optional_conta_filter(query, conta_filter):
    if conta_filter:
        return query.filter(Transaction.conta_id == conta_filter)
    return query


def _dashboard_recent_income(*, user_id, conta_filter, current_month, current_year):
    query = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.type == "receita",
        extract("month", Transaction.payment_date) == current_month,
        extract("year", Transaction.payment_date) == current_year,
    )
    query = _apply_optional_conta_filter(query, conta_filter)
    return query.order_by(Transaction.payment_date.desc()).limit(5).all()


def _dashboard_recent_expenses(*, user_id, conta_filter, current_month, current_year):
    query = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.type == "despesa",
        or_(
            extract("month", Transaction.due_date) == current_month,
            and_(
                extract("month", Transaction.payment_date) == current_month,
                extract("year", Transaction.payment_date) == current_year,
            ),
        ),
    )
    query = _apply_optional_conta_filter(query, conta_filter)
    return sorted(query.all(), key=lambda transaction: transaction.due_date or datetime.min)


def _dashboard_total_transactions(*, user_id, conta_filter, current_month, current_year):
    query = Transaction.query.filter(
        Transaction.user_id == user_id,
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
    query = _apply_optional_conta_filter(query, conta_filter)
    return query.count()


def _dashboard_pending_transactions(*, user_id, conta_filter):
    query = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.paid == False,
    )
    query = _apply_optional_conta_filter(query, conta_filter)
    pending_list = query.order_by(Transaction.due_date.asc(), Transaction.date.asc()).all()
    pending_count = len(pending_list)
    pending_amount = sum((transaction.amount or 0) - (transaction.discount or 0) for transaction in pending_list)
    return pending_count, pending_list, pending_amount


def _dashboard_saldo_atual(*, contas, conta_filter):
    if conta_filter:
        conta_atual = next((conta for conta in contas if conta.id == conta_filter), None)
        if conta_atual:
            Conta.recalcular_saldos(conta_id=conta_filter)
            db.session.refresh(conta_atual)
            return conta_atual.saldo_atual
        return 0.0

    conta_atual = get_current_conta()
    if conta_atual:
        Conta.recalcular_saldos(conta_id=conta_atual.id)
        db.session.refresh(conta_atual)
        return conta_atual.saldo_atual

    Conta.recalcular_saldos()
    for conta in contas:
        db.session.refresh(conta)
    return sum(conta.saldo_atual for conta in contas)


def _build_dashboard_monthly_series(*, user_id, conta_filter, current_month, current_year, get_final_value):
    monthly_data = []
    for offset in range(-5, 7):
        month_number = current_month + offset
        year_number = current_year
        while month_number <= 0:
            month_number += 12
            year_number -= 1
        while month_number > 12:
            month_number -= 12
            year_number += 1

        month_income_query = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == "receita",
            extract("month", Transaction.date) == month_number,
            extract("year", Transaction.date) == year_number,
        )
        month_income_query = _apply_optional_conta_filter(month_income_query, conta_filter)
        month_income = month_income_query.scalar() or 0

        month_expense_query = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.type == "despesa",
            extract("month", Transaction.date) == month_number,
            extract("year", Transaction.date) == year_number,
        )
        month_expense_query = _apply_optional_conta_filter(month_expense_query, conta_filter)
        month_expense = sum(get_final_value(transaction) for transaction in month_expense_query.all())

        monthly_data.append(
            {
                "month": datetime(year_number, month_number, 1).strftime("%b"),
                "receita": float(month_income),
                "despesa": float(month_expense),
                "balance": float(month_income - month_expense),
            }
        )

    return monthly_data


def _safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _get_final_transaction_value(transaction):
    return _safe_float(transaction.amount) - _safe_float(transaction.discount)


def _serialize_transactions_for_report(transactions, *, include_type=False):
    rows = []
    for transaction in transactions:
        row = {
            "date": transaction.date,
            "category": transaction.category,
            "expense": transaction.expense,
            "description": transaction.description,
            "amount": _safe_float(transaction.amount),
            "discount": _safe_float(transaction.discount),
            "due_date": transaction.due_date,
            "payment_date": transaction.payment_date,
            "payment_method": transaction.payment_method,
            "paid": transaction.paid,
        }
        if include_type:
            row["type"] = transaction.type
        rows.append(row)
    return rows


def _payment_method_totals_report(transactions, payment_methods):
    totals = {}
    for method in payment_methods:
        method_transactions = [
            transaction for transaction in transactions if transaction.payment_method_id == method.id
        ]
        totals[method.id] = {
            "name": method.name,
            "total_income": sum(
                _safe_float(transaction.amount)
                for transaction in method_transactions
                if transaction.type == "receita"
            ),
            "total_expenses": sum(
                _safe_float(transaction.amount)
                for transaction in method_transactions
                if transaction.type == "despesa"
            ),
            "total_discount": sum(
                _safe_float(transaction.discount) for transaction in method_transactions
            ),
            "count": len(method_transactions),
        }
    return totals


def _payment_method_expense_totals(transactions, payment_methods):
    totals = {}
    for method in payment_methods:
        method_transactions = [
            transaction for transaction in transactions if transaction.payment_method_id == method.id
        ]
        totals[method.id] = {
            "name": method.name,
            "original": sum(_safe_float(transaction.amount) for transaction in method_transactions),
            "discount": sum(_safe_float(transaction.discount) for transaction in method_transactions),
            "final": sum(_get_final_transaction_value(transaction) for transaction in method_transactions),
            "count": len(method_transactions),
        }
    return totals


def _discount_categories_totals(transactions):
    category_totals = {}
    for transaction in transactions:
        category_id = transaction.category_id
        if category_id not in category_totals:
            category_totals[category_id] = {
                "name": transaction.category.name,
                "total_amount": 0.0,
                "total_discount": 0.0,
            }
        category_totals[category_id]["total_amount"] += _safe_float(transaction.amount)
        category_totals[category_id]["total_discount"] += _safe_float(transaction.discount)
    return list(category_totals.values())


def _list_investments_for_scope(*, user_id, conta_filter, contas_by_id, should_include):
    movement_query = MovimentacaoInvestimento.query.filter_by(user_id=user_id)
    if conta_filter:
        movement_query = movement_query.filter_by(conta_id=conta_filter)

    investimento_ids = sorted({mov.investimento_id for mov in movement_query.all()})
    investimentos = []

    for inv_id in investimento_ids:
        investimento = db.session.get(Investimento, inv_id)
        if not investimento:
            continue

        if conta_filter:
            investimento.conta = contas_by_id.get(conta_filter)
        else:
            primeira_mov = (
                MovimentacaoInvestimento.query.filter_by(investimento_id=inv_id, user_id=user_id)
                .order_by(MovimentacaoInvestimento.id.asc())
                .first()
            )
            investimento.conta = db.session.get(Conta, primeira_mov.conta_id) if primeira_mov else None

        if should_include(investimento):
            investimentos.append(investimento)

    return investimentos


def _first_investment_movement(*, investimento_id, user_id):
    return (
        MovimentacaoInvestimento.query.filter_by(investimento_id=investimento_id, user_id=user_id)
        .order_by(MovimentacaoInvestimento.data_movimentacao.asc(), MovimentacaoInvestimento.id.asc())
        .first()
    )


def _latest_investment_movement(*, investimento_id, user_id):
    return (
        MovimentacaoInvestimento.query.filter_by(investimento_id=investimento_id, user_id=user_id)
        .order_by(MovimentacaoInvestimento.data_movimentacao.desc(), MovimentacaoInvestimento.id.desc())
        .first()
    )


def _should_show_investment_current_period(*, investimento, user_id, current_date):
    ultima_movimentacao = _latest_investment_movement(investimento_id=investimento.id, user_id=user_id)
    if not ultima_movimentacao:
        return True

    if (
        ultima_movimentacao.tipo_movimentacao == "resgate"
        and ultima_movimentacao.saldo_atual == 0.0
        and (
            ultima_movimentacao.data_movimentacao.year < current_date.year
            or (
                ultima_movimentacao.data_movimentacao.year == current_date.year
                and ultima_movimentacao.data_movimentacao.month < current_date.month
            )
        )
    ):
        return False

    return True


def _should_show_investment_monthly_report(*, investimento, user_id, year, month):
    primeira_movimentacao = _first_investment_movement(investimento_id=investimento.id, user_id=user_id)
    if not primeira_movimentacao:
        return True

    if (
        primeira_movimentacao.data_movimentacao.year > year
        or (
            primeira_movimentacao.data_movimentacao.year == year
            and primeira_movimentacao.data_movimentacao.month > month
        )
    ):
        return False

    ultima_movimentacao = _latest_investment_movement(investimento_id=investimento.id, user_id=user_id)
    if (
        ultima_movimentacao
        and ultima_movimentacao.tipo_movimentacao == "resgate"
        and ultima_movimentacao.saldo_atual == 0.0
        and (
            ultima_movimentacao.data_movimentacao.year < year
            or (
                ultima_movimentacao.data_movimentacao.year == year
                and ultima_movimentacao.data_movimentacao.month < month
            )
        )
    ):
        return False

    return True


def _should_show_investment_annual_report(*, investimento, user_id, year):
    primeira_movimentacao = _first_investment_movement(investimento_id=investimento.id, user_id=user_id)
    if not primeira_movimentacao:
        return True

    if primeira_movimentacao.data_movimentacao.year > year:
        return False

    ultima_movimentacao = _latest_investment_movement(investimento_id=investimento.id, user_id=user_id)
    if (
        ultima_movimentacao
        and ultima_movimentacao.tipo_movimentacao == "resgate"
        and ultima_movimentacao.saldo_atual == 0.0
        and ultima_movimentacao.data_movimentacao.year < year
    ):
        return False

    return True


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
    conta_filter = _resolve_conta_filter(
        contas,
        request.args.get('conta_id', type=int),
        use_current_conta=True,
    )

    # Salvar a conta atual na sessão
    # if conta_filter:
    #     session['last_conta_id'] = conta_filter
        
        # Criar flash message informando qual conta está selecionada
        # conta_selecionada = next((c for c in contas if c.id == conta_filter), None)
        # if conta_selecionada:
        #     flash(f'Você acessou a conta {conta_selecionada.nome}.', 'info')
    
    # Obter o mês e ano atual
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_date = datetime.now().date()


    recent_income = _dashboard_recent_income(
        user_id=current_user.id,
        conta_filter=conta_filter,
        current_month=current_month,
        current_year=current_year,
    )

    # Buscar transaÃ§Ãµes recentes de despesa do mês atual
    recent_expenses = _dashboard_recent_expenses(
        user_id=current_user.id,
        conta_filter=conta_filter,
        current_month=current_month,
        current_year=current_year,
    )

    # Debug: Imprimir todas as despesas encontradas
    # print("\nDespesas encontradas no dashboard:")
    # for exp in recent_expenses:
    #     print(
    #         f"Vencimento: {exp.due_date}, Descrição: {exp.expense.name if exp.expense else exp.description}, "
    #         f"Valor: {exp.amount}, Desconto: {exp.discount}, Categoria: {exp.category.name}"
    #     )

    agua_expenses = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "despesa",
        or_(
            Transaction.expense.has(name="Água"),
            Transaction.description.ilike("%Água%"),
        ),
    ).all()
    # print("\nDespesas de Água encontradas:")
    # for exp in agua_expenses:
    #     print(
    #         f"Vencimento: {exp.due_date}, Descrição: {exp.expense.name if exp.expense else exp.description}, "
    #         f"Valor: {exp.amount}, Desconto: {exp.discount}, Categoria: {exp.category.name}"
    #     )

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

    income_query = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "receita",
        Transaction.paid == True,
        extract("month", Transaction.payment_date) == current_month,
        extract("year", Transaction.payment_date) == current_year,
    )
    if conta_filter:
        income_query = income_query.filter(Transaction.conta_id == conta_filter)
    income_total = income_query.scalar() or 0

    expense_transactions_query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "despesa",
        Transaction.paid == True,
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
    expense_total = sum(_get_final_transaction_value(transaction) for transaction in expense_transactions)

    monthly_balance = income_total - expense_total

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
            extract("year", Transaction.payment_date) < current_year,
            and_(
                extract("year", Transaction.payment_date) == current_year,
                extract("month", Transaction.payment_date) < current_month,
            ),
        ),
    )
    if conta_filter:
        accumulated_balance_query = accumulated_balance_query.filter(Transaction.conta_id == conta_filter)
    accumulated_balance = accumulated_balance_query.scalar() or 0
    balance = accumulated_balance + monthly_balance

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
    if conta_filter:
        expense_by_category_query = expense_by_category_query.filter(Transaction.conta_id == conta_filter)
    expense_by_category = expense_by_category_query.group_by(Category.name).all()
    top_expense_categories = [
        (category, (total_amount or 0) - (total_discount or 0))
        for category, total_amount, total_discount in expense_by_category
    ]
    top_expense_categories.sort(key=lambda item: item[1], reverse=True)
    top_expense_categories = top_expense_categories[:5]

    top_income_categories_query = (
        db.session.query(Category.name, func.sum(Transaction.amount).label("total"))
        .join(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "receita",
            Category.name != "Investimentos",
        )
    )
    if conta_filter:
        top_income_categories_query = top_income_categories_query.filter(Transaction.conta_id == conta_filter)
    top_income_categories = (
        top_income_categories_query.group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    monthly_data = _build_dashboard_monthly_series(
        user_id=current_user.id,
        conta_filter=conta_filter,
        current_month=current_month,
        current_year=current_year,
        get_final_value=_get_final_transaction_value,
    )

    expense_chart_data = [
        {"name": category, "value": float(total)} for category, total in top_expense_categories
    ]
    income_chart_data = [
        {"name": category, "value": float(total)} for category, total in top_income_categories
    ]

    expense_chart_json = json.dumps(expense_chart_data, ensure_ascii=False)
    income_chart_json = json.dumps(income_chart_data, ensure_ascii=False)
    monthly_data_json = json.dumps(monthly_data, ensure_ascii=False)

    total_transactions = _dashboard_total_transactions(
        user_id=current_user.id,
        conta_filter=conta_filter,
        current_month=current_month,
        current_year=current_year,
    )

    days_in_month = monthrange(current_year, current_month)[1]
    daily_avg_expense = expense_total / days_in_month if days_in_month > 0 else 0

    current_day = datetime.now().day
    if current_date.month == current_month and current_date.year == current_year:
        projected_expense = (expense_total / current_day) * days_in_month if current_day > 0 else 0
    else:
        projected_expense = expense_total

    pending_transactions, pending_transactions_list, pending_amount = _dashboard_pending_transactions(
        user_id=current_user.id,
        conta_filter=conta_filter,
    )

    saldo_atual = _dashboard_saldo_atual(
        contas=contas,
        conta_filter=conta_filter,
    )

    # Buscar investimentos da conta selecionada
    contas_by_id = {conta.id: conta for conta in contas}
    investimentos = _list_investments_for_scope(
        user_id=current_user.id,
        conta_filter=conta_filter,
        contas_by_id=contas_by_id,
        should_include=lambda investimento: _should_show_investment_current_period(
            investimento=investimento,
            user_id=current_user.id,
            current_date=current_date,
        ),
    )
    investimentos_conta_atual = list(investimentos) if conta_filter else []

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
        current_month=f"{MONTH_NAMES_PT[current_month]} {current_year}",
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


@auth_bp.route("/admin_users", methods=["GET", "POST"])
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)

    form = AdminUserForm()
    users = User.query.order_by(User.username).all()
    form.user_id.choices = [(u.id, f"{u.username} ({u.email})") for u in users]

    selected_id = request.args.get("user_id", type=int)
    if selected_id:
        form.user_id.data = selected_id
    elif not form.user_id.data and users:
        form.user_id.data = users[0].id

    target_user = db.session.get(User, form.user_id.data) if form.user_id.data else None
    if request.method == "GET" and target_user:
        form.username.data = target_user.username
        form.email.data = target_user.email

    if form.validate_on_submit():
        target_user = db.session.get(User, form.user_id.data)
        if not target_user:
            flash("Usuário não encontrado.", "danger")
            return render_template("admin_users.html", form=form)

        target_user.username = form.username.data
        target_user.email = form.email.data
        if form.password.data:
            target_user.set_password(form.password.data)

        db.session.commit()
        flash("Usuário atualizado com sucesso.", "success")
        return redirect(url_for("auth.admin_users", user_id=target_user.id))

    return render_template("admin_users.html", form=form)


# Rotas de autenticação
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    from flask import current_app

    form = LoginForm()
    limit_attempts = int(current_app.config.get("LOGIN_RATE_LIMIT_ATTEMPTS", 5))
    limit_window = int(current_app.config.get("LOGIN_RATE_LIMIT_WINDOW_SECONDS", 300))

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    login_value = (form.username.data or "").strip()
    login_key = login_value.lower()
    identifier = f"{client_ip}:{login_key or 'unknown'}"

    if form.validate_on_submit():
        if _login_limit_exceeded(identifier=identifier, max_attempts=limit_attempts, window_seconds=limit_window):
            flash("Muitas tentativas de login. Aguarde alguns minutos.", "danger")
            return render_template("login.html", form=form), 429

        user = User.query.filter(
            or_(
                func.lower(User.username) == login_key,
                func.lower(User.email) == login_key,
            )
        ).first()
        if user and user.check_password(form.password.data):
            _clear_login_attempts(identifier)
            _clear_login_attempts(f"{client_ip}:{(user.username or '').strip().lower()}")
            _clear_login_attempts(f"{client_ip}:{(user.email or '').strip().lower()}")
            login_user(user, remember=bool(form.remember_me.data))
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        _register_failed_login(identifier=identifier, window_seconds=limit_window)
        flash("Nome de usuario ou senha invalidos", "danger")
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
    query = _user_categories_query()

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
            user_id=current_user.id,
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
    category = _user_category_or_404(id)
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
    category = _user_category_or_404(id)

    # Verificar se a categoria está sendo usada em alguma transação
    if Transaction.query.filter_by(category_id=category.id, user_id=current_user.id).first():
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
    query = _user_expenses_query().order_by(desc(Expense.id))

    # Apply category filter if specified
    if category_id:
        query = query.filter(Expense.category_id == category_id)

    expenses = query.all()

    # Preencher as opções de categorias
    categories = _user_categories_query().all()

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
    categories = _user_categories_query().all()
    form.category_id.choices = [(cat.id, cat.name) for cat in categories]

    if form.validate_on_submit():
        expense = Expense(name=form.name.data, category_id=form.category_id.data, user_id=current_user.id)

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
    expense = _user_expense_or_404(id)
    form = ExpenseForm(obj=expense)

    # Retorna as opções da categoria ANTES da validação
    categories = _user_categories_query().all()
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
    expense = _user_expense_or_404(id)

    # Verificar se a descrição está sendo usada em alguma transação
    if Transaction.query.filter_by(expense_id=expense.id, user_id=current_user.id).first():
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
    methods = _user_payment_methods_query().all()
    return render_template("list_payment_method.html", methods=methods)


@transaction_bp.route("/payment_methods/add", methods=["GET", "POST"])
@login_required
def add_payment_method():
    form = PaymentMethodForm()
    if form.validate_on_submit():
        payment_method = PaymentMethod(
            name=form.name.data, is_active=form.is_active.data, user_id=current_user.id
        )
        db.session.add(payment_method)
        db.session.commit()
        flash("Forma de pagamento adicionada com sucesso!", "success")
        return redirect(url_for("transaction.list_payment_methods"))
    return render_template("payment_method_form.html", form=form, title="Adicionar Forma de Pagamento")


@transaction_bp.route("/payment_methods/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_payment_method(id):
    method = _user_payment_method_or_404(id)
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
    method = _user_payment_method_or_404(id)
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
    conta_filter = _resolve_conta_filter(
        contas,
        request.args.get('conta_id', type=int),
    )

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
    years = _report_years()

    # Debug: imprimir os valores de mês e ano
    # print(f"DEBUG: mês selecionado: {month}, Ano selecionado: {year}")
    # print(f"DEBUG: mês atual: {datetime.now().month}, Ano atual: {datetime.now().year}")

    # Obter todas as formas de pagamento para o select
    payment_methods = _user_payment_methods_query().filter_by(is_active=True).all()

    query = _build_reports_query(
        user_id=current_user.id,
        report_type=report_type,
        year=year,
        month=month,
        payment_method_id=payment_method_id,
        show_discount_only=show_discount_only,
        conta_filter=conta_filter,
    )
    transactions = query.all()
    expense_transactions, income_transactions = _split_report_transactions(transactions)
    income_total, expense_total, total_discount, balance = _calculate_report_totals(
        transactions,
        _safe_float,
    )

    income_chart_data = []
    monthly_data = []

    if report_type == "monthly":
        income_by_category = _build_category_totals(
            income_transactions,
            lambda transaction: _safe_float(transaction.amount),
        )

        expense_by_category = _build_category_totals(
            expense_transactions,
            lambda transaction: _safe_float(transaction.amount) - _safe_float(transaction.discount),
        )

        expense_chart_data = [
            {"category": item["category"], "amount": item["amount"]}
            for item in expense_by_category[:10]
        ]
        income_chart_data = [
            {"category": item["category"], "amount": item["amount"]}
            for item in income_by_category[:10]
        ]

        investimentos = _list_investments_for_scope(
            user_id=current_user.id,
            conta_filter=conta_filter,
            contas_by_id={conta.id: conta for conta in contas},
            should_include=lambda investimento: _should_show_investment_monthly_report(
                investimento=investimento,
                user_id=current_user.id,
                year=year,
                month=month,
            ),
        )

        return render_template(
            "reports.html",
            contas=contas,
            conta_filter=conta_filter,
            transactions=transactions,
            expense_transactions=expense_transactions,
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
            investimentos=investimentos,
        )

    monthly_data = _build_annual_report_monthly_data(
        transactions,
        year,
        _safe_float,
    )

    investimentos = _list_investments_for_scope(
        user_id=current_user.id,
        conta_filter=conta_filter,
        contas_by_id={conta.id: conta for conta in contas},
        should_include=lambda investimento: _should_show_investment_annual_report(
            investimento=investimento,
            user_id=current_user.id,
            year=year,
        ),
    )

    return render_template(
        "reports.html",
        contas=contas,
        conta_filter=conta_filter,
        transactions=transactions,
        expense_transactions=expense_transactions,
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
        investimentos=investimentos,
    )

def _export_serialize(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


@transaction_bp.route("/export")
@login_required
def export_data():
    from app.models import Investimento, MovimentacaoInvestimento, TipoConta, TipoInvestimento

    user_id = current_user.id

    categories = _user_categories_query().order_by(Category.id.asc()).all()
    expenses = _user_expenses_query().order_by(Expense.id.asc()).all()
    payment_methods = _user_payment_methods_query().order_by(PaymentMethod.id.asc()).all()
    tipos_conta = TipoConta.query.filter_by(user_id=user_id).order_by(TipoConta.id.asc()).all()
    contas = Conta.query.filter_by(user_id=user_id).order_by(Conta.id.asc()).all()
    tipos_investimento = TipoInvestimento.query.filter_by(user_id=user_id).order_by(TipoInvestimento.id.asc()).all()
    movimentacoes = (
        MovimentacaoInvestimento.query.filter_by(user_id=user_id)
        .order_by(MovimentacaoInvestimento.id.asc())
        .all()
    )
    investimento_ids = sorted({mov.investimento_id for mov in movimentacoes})
    investimentos = (
        Investimento.query.filter(Investimento.id.in_(investimento_ids))
        .order_by(Investimento.id.asc())
        .all()
        if investimento_ids
        else []
    )
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.id.asc()).all()

    export_payload = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
        },
        "tipos_conta": [
            {
                "id": item.id,
                "nome": item.nome,
                "descricao": item.descricao,
                "ativo": item.ativo,
            }
            for item in tipos_conta
        ],
        "contas": [
            {
                "id": item.id,
                "nome": item.nome,
                "tipo_id": item.tipo_id,
                "saldo_inicial": _export_serialize(item.saldo_inicial),
                "saldo_atual": _export_serialize(item.saldo_atual),
            }
            for item in contas
        ],
        "categories": [
            {
                "id": item.id,
                "name": item.name,
                "type": item.type,
                "exclusive": item.exclusive,
                "icon": item.icon,
                "color": item.color,
            }
            for item in categories
        ],
        "expenses": [
            {
                "id": item.id,
                "name": item.name,
                "category_id": item.category_id,
            }
            for item in expenses
        ],
        "payment_methods": [
            {
                "id": item.id,
                "name": item.name,
                "is_active": item.is_active,
            }
            for item in payment_methods
        ],
        "tipos_investimento": [
            {
                "id": item.id,
                "nome": item.nome,
                "descricao": item.descricao,
                "ativo": item.ativo,
            }
            for item in tipos_investimento
        ],
        "investimentos": [
            {
                "id": item.id,
                "tipo_investimento_id": item.tipo_investimento_id,
                "data_abertura": _export_serialize(item.data_abertura),
                "saldo_atual": _export_serialize(item.saldo_atual),
            }
            for item in investimentos
        ],
        "movimentacoes_investimento": [
            {
                "id": item.id,
                "investimento_id": item.investimento_id,
                "conta_id": item.conta_id,
                "data_movimentacao": _export_serialize(item.data_movimentacao),
                "tipo_movimentacao": item.tipo_movimentacao,
                "valor": _export_serialize(item.valor),
                "saldo_anterior": _export_serialize(item.saldo_anterior),
                "saldo_atual": _export_serialize(item.saldo_atual),
                "observacoes": item.observacoes,
            }
            for item in movimentacoes
        ],
        "transactions": [
            {
                "id": item.id,
                "type": item.type,
                "date": _export_serialize(item.date),
                "due_date": _export_serialize(item.due_date),
                "payment_date": _export_serialize(item.payment_date),
                "amount": _export_serialize(item.amount),
                "discount": _export_serialize(item.discount),
                "paid": item.paid,
                "description": item.description,
                "details": item.details,
                "notes": item.notes,
                "recurrence": item.recurrence,
                "conta_id": item.conta_id,
                "category_id": item.category_id,
                "expense_id": item.expense_id,
                "payment_method_id": item.payment_method_id,
            }
            for item in transactions
        ],
    }

    filename = f"financas_user_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    payload = json.dumps(export_payload, ensure_ascii=False, indent=2)
    return Response(
        payload,
        mimetype="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for("auth.reset_token", token=token, _external=True)

    print("[INFO] Link de recuperação de senha:", reset_url)

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

    payment_method_id = request.args.get("payment_method_id", type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    year = request.args.get("year", datetime.now().year, type=int)
    years = _report_years()

    query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract("month", Transaction.date) == month,
        extract("year", Transaction.date) == year,
    )
    if payment_method_id:
        query = query.filter(Transaction.payment_method_id == payment_method_id)

    transactions = query.order_by(Transaction.date.desc()).all()
    payment_methods = _user_payment_methods_query().all()

    total_amount = sum(_safe_float(transaction.amount) for transaction in transactions)
    total_discount = sum(_safe_float(transaction.discount) for transaction in transactions)
    total_final = sum(_get_final_transaction_value(transaction) for transaction in transactions)

    return render_template(
        "payment_method_report.html",
        transactions=_serialize_transactions_for_report(transactions, include_type=True),
        payment_methods=payment_methods,
        selected_method_id=payment_method_id,
        month=month,
        year=year,
        years=years,
        total_amount=_safe_float(total_amount),
        total_discount=_safe_float(total_discount),
        total_final=_safe_float(total_final),
        payment_method_totals=_payment_method_totals_report(transactions, payment_methods),
        total_transactions=len(transactions),
    )


@transaction_bp.route("/reports/discounts", methods=["GET"])
@login_required
def discount_report():
    check = require_account()
    if check:
        return check

    month = request.args.get("month", datetime.now().month, type=int)
    year = request.args.get("year", datetime.now().year, type=int)
    years = _report_years()

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

    total_expenses = sum(_safe_float(transaction.amount) for transaction in transactions)
    total_discounts = sum(_safe_float(transaction.discount) for transaction in transactions)
    total_final = sum(_get_final_transaction_value(transaction) for transaction in transactions)

    return render_template(
        "discount_report.html",
        transactions=_serialize_transactions_for_report(transactions),
        month=month,
        year=year,
        years=years,
        total_amount=_safe_float(total_expenses),
        total_discount=_safe_float(total_discounts),
        total_final=_safe_float(total_final),
        total_transactions=len(transactions),
        categories=_discount_categories_totals(transactions),
    )


@transaction_bp.route("/reports/payment_method_expenses", methods=["GET"])
@login_required
def payment_method_expense_report():
    check = require_account()
    if check:
        return check

    payment_method_id = request.args.get("payment_method_id", type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    year = request.args.get("year", datetime.now().year, type=int)
    years = _report_years()

    query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "despesa",
        extract("month", Transaction.date) == month,
        extract("year", Transaction.date) == year,
    )
    if payment_method_id:
        query = query.filter(Transaction.payment_method_id == payment_method_id)

    transactions = query.order_by(Transaction.date.desc()).all()
    payment_methods = _user_payment_methods_query().filter_by(is_active=True).all()

    total_amount = sum(_get_final_transaction_value(transaction) for transaction in transactions)
    total_discount = sum(_safe_float(transaction.discount) for transaction in transactions)
    total_original = sum(_safe_float(transaction.amount) for transaction in transactions)

    return render_template(
        "payment_method_expense_report.html",
        transactions=_serialize_transactions_for_report(transactions),
        payment_methods=payment_methods,
        selected_method_id=payment_method_id,
        month=month,
        year=year,
        years=years,
        total_original=_safe_float(total_original),
        total_discount=_safe_float(total_discount),
        total_amount=_safe_float(total_amount),
        payment_method_totals=_payment_method_expense_totals(transactions, payment_methods),
        total_transactions=len(transactions),
    )


@transaction_bp.route("/transactions")
@login_required
def transactions():
    page = request.args.get("page", 1, type=int)
    per_page = 10

    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    expense_query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "despesa",
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

    income_query = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "receita",
        extract("month", Transaction.payment_date) == current_month,
        extract("year", Transaction.payment_date) == current_year,
    )

    query = expense_query.union(income_query)
    transactions = query.order_by(
        Transaction.type.desc(),
        Transaction.due_date.asc(),
    ).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "list_transactions.html",
        transactions=transactions,
        current_month=f"{MONTH_NAMES_PT[current_month]} {current_year}",
    )

PARCELA_INTERVALO_DIAS = 30


def _split_amount_in_cents(total, parcelas):
    """Divide um valor em ``parcelas`` partes arredondadas em centavos.

    A diferenca de arredondamento e somada a ultima parcela para que a soma
    das parcelas seja exatamente igual ao valor total informado.
    Ex.: 100,00 / 3 -> [33.33, 33.33, 33.34].
    """
    total_dec = Decimal(str(total or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if parcelas <= 1:
        return [total_dec]

    base = (total_dec / Decimal(parcelas)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    valores = [base for _ in range(parcelas)]
    valores[-1] = total_dec - base * (parcelas - 1)
    return valores


def _create_installments(*, user_id, base_payload, parcelas):
    """Cria uma transacao por parcela.

    - A primeira parcela mantem as datas originalmente informadas.
    - Cada parcela seguinte soma 30 dias as datas (data, vencimento e pagamento).
    - O valor total e dividido entre as parcelas (arredondado em centavos).
    - A descricao recebe o sufixo "(n/total)".
    """
    base_description = (base_payload.get("description") or "").strip()
    valores = _split_amount_in_cents(base_payload.get("amount"), parcelas)
    descontos = _split_amount_in_cents(base_payload.get("discount"), parcelas)

    criadas = []
    for indice in range(parcelas):
        payload = dict(base_payload)
        offset = timedelta(days=PARCELA_INTERVALO_DIAS * indice)
        for campo_data in ("date", "due_date", "payment_date"):
            if payload.get(campo_data):
                payload[campo_data] = payload[campo_data] + offset

        payload["amount"] = float(valores[indice])
        payload["discount"] = float(descontos[indice])

        sufixo = f"({indice + 1}/{parcelas})"
        payload["description"] = (f"{base_description} {sufixo}").strip() if base_description else sufixo

        criadas.append(TransactionService.create_transaction(user_id=user_id, payload=payload))
    return criadas


def _build_transaction_payload(form, conta_id):
    return {
        "type": form.type.data,
        "date": form.date.data,
        "due_date": form.due_date.data,
        "payment_date": form.payment_date.data,
        "amount": float(form.amount.data),
        "discount": float(form.discount.data) if form.discount.data else 0.0,
        "paid": bool(form.paid.data),
        "category_id": form.category_id.data,
        "expense_id": form.expense_id.data if form.expense_id.data and form.expense_id.data > 0 else None,
        "description": form.description.data,
        "payment_method_id": form.payment_method_id.data,
        "recurrence": form.recurrence.data,
        "details": form.details.data,
        "notes": form.notes.data,
        "conta_id": conta_id,
    }



@transaction_bp.route("/transactions/add", methods=["GET", "POST"] )
@login_required
def add_transaction():
    form = TransactionForm()
    conta_id_from_url = request.args.get("conta_id", type=int)

    form.category_id.choices = [(cat.id, cat.name) for cat in _user_categories_query().all()]
    form.payment_method_id.choices = [
        (pm.id, pm.name) for pm in _user_payment_methods_query().filter_by(is_active=True).all()
    ]
    form.expense_id.choices = [(0, "Selecione uma descricao")] + [
        (exp.id, exp.name) for exp in _user_expenses_query().all()
    ]
    form.conta_id.choices = [(c.id, c.nome) for c in Conta.query.filter_by(user_id=current_user.id).all()]

    if conta_id_from_url:
        form.conta_id.data = conta_id_from_url

    if request.method == "GET" and request.args:
        if request.args.get("type"):
            form.type.data = request.args.get("type")
        if request.args.get("category_id"):
            form.category_id.data = int(request.args.get("category_id"))
        if request.args.get("expense_id"):
            expense_id = request.args.get("expense_id")
            if expense_id:
                form.expense_id.data = int(expense_id)
        if request.args.get("description"):
            form.description.data = request.args.get("description")
        if request.args.get("amount"):
            amount = float(request.args.get("amount"))
            amount_str = f"{amount:.2f}".replace(".", ",")
            parts = amount_str.split(",")
            integer_part = "{:,}".format(int(parts[0])).replace(",", ".")
            form.amount.data = f"{integer_part},{parts[1]}"
        if request.args.get("discount"):
            discount = float(request.args.get("discount"))
            discount_str = f"{discount:.2f}".replace(".", ",")
            parts = discount_str.split(",")
            integer_part = "{:,}".format(int(parts[0])).replace(",", ".")
            form.discount.data = f"{integer_part},{parts[1]}"
        if request.args.get("payment_method_id"):
            payment_method_id = request.args.get("payment_method_id")
            if payment_method_id:
                form.payment_method_id.data = int(payment_method_id)
        if request.args.get("paid"):
            form.paid.data = request.args.get("paid") == "1"
        if request.args.get("recurrence"):
            form.recurrence.data = request.args.get("recurrence")
        if request.args.get("details"):
            form.details.data = request.args.get("details")
        if request.args.get("notes"):
            form.notes.data = request.args.get("notes")
        if request.args.get("conta_id"):
            conta_id = request.args.get("conta_id")
            if conta_id:
                form.conta_id.data = int(conta_id)
        if request.args.get("date"):
            form.date.data = datetime.strptime(request.args.get("date"), "%Y-%m-%d").date()
        if request.args.get("due_date"):
            form.due_date.data = datetime.strptime(request.args.get("due_date"), "%Y-%m-%d").date()
        if request.args.get("payment_date"):
            form.payment_date.data = datetime.strptime(request.args.get("payment_date"), "%Y-%m-%d").date()

    if form.validate_on_submit():
        if not form.category_id.data or form.category_id.data == 0:
            flash("Selecione uma categoria valida.", "danger")
            return render_template("add_edit_transaction.html", form=form, edit=False)

        if conta_id_from_url:
            conta_id = conta_id_from_url
        else:
            conta_atual = get_current_conta()
            if not conta_atual:
                flash("Voce precisa ter pelo menos uma conta cadastrada.", "warning")
                return redirect(url_for("conta.listar_contas"))
            conta_id = conta_atual.id

        payload = _build_transaction_payload(form, conta_id)

        parcelas = 1
        if form.parcelado.data:
            parcelas = form.numero_parcelas.data or 1
            if parcelas < 1:
                parcelas = 1

        try:
            if parcelas > 1:
                _create_installments(
                    user_id=current_user.id,
                    base_payload=payload,
                    parcelas=parcelas,
                )
                flash(f"{parcelas} parcelas adicionadas com sucesso!", "success")
            else:
                TransactionService.create_transaction(user_id=current_user.id, payload=payload)
                flash("Transacao adicionada com sucesso!", "success")
            return redirect(url_for("main.dashboard"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    return render_template("add_edit_transaction.html", form=form, edit=False)


@transaction_bp.route("/transactions/edit/<int:id>", methods=["GET", "POST"] )
@login_required
def edit_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = TransactionForm(obj=transaction)

    form.category_id.choices = [(cat.id, cat.name) for cat in _user_categories_query().all()]
    form.payment_method_id.choices = [
        (pm.id, pm.name) for pm in _user_payment_methods_query().filter_by(is_active=True).all()
    ]
    form.expense_id.choices = [(0, "Selecione uma descricao")] + [
        (exp.id, exp.name) for exp in _user_expenses_query().all()
    ]
    form.conta_id.choices = [(c.id, c.nome) for c in Conta.query.filter_by(user_id=current_user.id).all()]

    if form.validate_on_submit():
        conta_id = form.conta_id.data if form.conta_id.data else transaction.conta_id
        payload = _build_transaction_payload(form, conta_id)
        try:
            TransactionService.update_transaction(user_id=current_user.id, tx=transaction, payload=payload)
            flash("Transacao atualizada com sucesso!", "success")
            return redirect(url_for("transaction.reports"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    form.conta_id.data = transaction.conta_id
    return render_template("add_edit_transaction.html", form=form, transaction=transaction, edit=True)


@transaction_bp.route("/transactions/delete/<int:id>")
@login_required
def delete_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        TransactionService.delete_transaction(user_id=current_user.id, tx=transaction)
        flash("Transacao excluida com sucesso!", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")
    return redirect(url_for("transaction.reports"))


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
        'paid': '0',  # Sempre desmarcar o campo 'Pago' ao replicar
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




@transaction_bp.route("/expenses/by-category/<int:category_id>")
@login_required
def get_expenses(category_id):
    expenses = _user_expenses_query().filter_by(category_id=category_id).all()
    return jsonify([{"id": exp.id, "name": exp.name} for exp in expenses])


@transaction_bp.route("/categories/by-type/<string:type>")
@login_required
def get_categories_by_type(type):
    try:
        # Buscar categorias do tipo específico
        type_categories = _user_categories_query().filter_by(type=type).all()

        # Buscar categorias não exclusivas (que podem ser usadas em qualquer tipo)
        # Garantir que exclusive seja False (não None)
        non_exclusive_categories = _user_categories_query().filter(
            Category.exclusive.is_(False)
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







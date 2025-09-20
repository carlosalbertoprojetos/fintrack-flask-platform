from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app import db
from datetime import datetime
from functools import wraps
from app.models import Transaction, Category, Expense, PaymentMethod, Conta, Investimento
from app.forms import TransactionForm, ContaForm, InvestimentoForm
from flask_login import login_required, current_user

transactions = Blueprint("transactions", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def get_transaction_form_with_contas(form=None):
    if form is None:
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
    # Preencher as opções de contas
    contas = Conta.query.filter_by(user_id=current_user.id).all()
    form.conta_id.choices = [(c.id, c.nome) for c in contas]
    
    return form


@transactions.route("/")
@login_required
def index():
    user_id = session.get("user_id")
    transactions = (
        Transaction.query.filter_by(user_id=user_id)
        .order_by(Transaction.date.desc())
        .all()
    )
    return render_template("home.html", transactions=transactions)


@transactions.route("/transactions/new", methods=["GET", "POST"])
@login_required
def new():
    user_id = session.get("user_id")
    form = get_transaction_form_with_contas()
    if form.validate_on_submit():
        transaction = Transaction(
            amount=form.amount.data,
            description=form.description.data,
            category_id=form.category_id.data,
            user_id=user_id,
            date=form.date.data or datetime.utcnow(),
            details=form.details.data,
            conta_id=form.conta_id.data if form.conta_id.data else None
        )
        db.session.add(transaction)
        db.session.commit()
        flash("Transaction added successfully")
        return redirect(url_for("transactions.index"))
    return render_template("add_edit_transaction.html", form=form, title="Nova Transação")


@transactions.route("/transactions/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    user_id = session.get("user_id")
    transaction = Transaction.query.filter_by(id=id, user_id=user_id).first_or_404()
    form = get_transaction_form_with_contas(form=TransactionForm(obj=transaction))
    if form.validate_on_submit():
        transaction.amount = form.amount.data
        transaction.description = form.description.data
        transaction.category_id = form.category_id.data
        transaction.details = form.details.data
        transaction.date = form.date.data or transaction.date
        transaction.conta_id = form.conta_id.data if form.conta_id.data else None
        db.session.commit()
        flash("Transaction updated successfully")
        return redirect(url_for("transactions.index"))
    form.conta_id.data = transaction.conta_id
    return render_template("add_edit_transaction.html", form=form, title="Editar Transação", edit=True, transaction=transaction)


@transactions.route("/transactions/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    user_id = session.get("user_id")
    transaction = Transaction.query.filter_by(id=id, user_id=user_id).first_or_404()

    db.session.delete(transaction)
    db.session.commit()

    flash("Transaction deleted successfully")
    return redirect(url_for("transactions.index"))


@transactions.route("/reports", methods=["GET"])
@login_required
def reports():
    user_id = session.get("user_id")
    # ... código já existente para relatórios ...
    investimentos = Investimento.query.join(Investimento.conta).filter_by(user_id=user_id).all()
    total_investido = sum(inv.saldo_atual for inv in investimentos)
    # ... outros contextos ...
    return render_template(
        "reports.html",
        # ... outros contextos ...
        investimentos=investimentos,
        total_investido=total_investido,
    )

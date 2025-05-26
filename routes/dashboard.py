from flask import Blueprint, render_template, session, redirect, url_for
from app.models import Transaction, Category, User
from app import db
from functools import wraps
from sqlalchemy import func
import calendar
from datetime import datetime

dashboard = Blueprint("dashboard", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@dashboard.route("/")
@login_required
def index():
    user_id = session.get("user_id")

    # Get current month's data
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Get income categories
    income_categories = Category.query.filter_by(user_id=user_id, type="receita").all()
    income_cat_ids = [cat.id for cat in income_categories]

    # Get expense categories
    expense_categories = Category.query.filter_by(user_id=user_id, type="despesa").all()
    expense_cat_ids = [cat.id for cat in expense_categories]

    # Calculate total income for current month
    income_transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.category_id.in_(income_cat_ids),
        func.extract("month", Transaction.date) == current_month,
        func.extract("year", Transaction.date) == current_year,
    ).all()

    total_income = sum(t.amount for t in income_transactions)

    # Calculate total expenses for current month
    expense_transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.category_id.in_(expense_cat_ids),
        func.extract("month", Transaction.date) == current_month,
        func.extract("year", Transaction.date) == current_year,
    ).all()

    total_expenses = sum(t.amount for t in expense_transactions)

    # Calculate balance
    balance = total_income - total_expenses

    # Get recent transactions
    recent_transactions = (
        Transaction.query.filter_by(user_id=user_id)
        .order_by(Transaction.date.desc())
        .limit(5)
        .all()
    )

    # Category breakdown for expenses
    category_breakdown = {}
    for cat in expense_categories:
        cat_total = sum(
            t.amount for t in expense_transactions if t.category_id == cat.id
        )
        if cat_total > 0:
            category_breakdown[cat.name] = cat_total

    return render_template(
        "dashboard/home.html",
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        recent_transactions=recent_transactions,
        category_breakdown=category_breakdown,
        current_month=calendar.month_name[current_month],
    )

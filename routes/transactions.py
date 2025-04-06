from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app import db
from datetime import datetime
from functools import wraps

transactions = Blueprint("transactions", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@transactions.route("/transactions")
@login_required
def index():
    user_id = session.get("user_id")
    transactions = (
        Transaction.query.filter_by(user_id=user_id)
        .order_by(Transaction.date.desc())
        .all()
    )
    return render_template("transactions/index.html", transactions=transactions)


@transactions.route("/transactions/new", methods=["GET", "POST"])
@login_required
def new():
    user_id = session.get("user_id")
    categories = Category.query.filter_by(user_id=user_id).all()

    if request.method == "POST":
        amount = request.form.get("amount")
        description = request.form.get("description")
        category_id = request.form.get("category_id")
        date_str = request.form.get("date")

        # Validation
        if not amount or not category_id:
            flash("Amount and category are required")
            return redirect(url_for("transactions.new"))

        try:
            amount = float(amount)
        except ValueError:
            flash("Amount must be a number")
            return redirect(url_for("transactions.new"))

        # Parse date or use current date
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                flash("Invalid date format. Use YYYY-MM-DD")
                return redirect(url_for("transactions.new"))
        else:
            date = datetime.utcnow()

        transaction = Transaction(
            amount=amount,
            description=description,
            category_id=category_id,
            user_id=user_id,
            date=date,
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Transaction added successfully")
        return redirect(url_for("transactions.index"))

    return render_template("transactions/new.html", categories=categories)


@transactions.route("/transactions/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    user_id = session.get("user_id")
    transaction = Transaction.query.filter_by(id=id, user_id=user_id).first_or_404()
    categories = Category.query.filter_by(user_id=user_id).all()

    if request.method == "POST":
        amount = request.form.get("amount")
        description = request.form.get("description")
        category_id = request.form.get("category_id")
        date_str = request.form.get("date")

        # Validation
        if not amount or not category_id:
            flash("Amount and category are required")
            return redirect(url_for("transactions.edit", id=id))

        try:
            amount = float(amount)
        except ValueError:
            flash("Amount must be a number")
            return redirect(url_for("transactions.edit", id=id))

        # Parse date
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                transaction.date = date
            except ValueError:
                flash("Invalid date format. Use YYYY-MM-DD")
                return redirect(url_for("transactions.edit", id=id))

        transaction.amount = amount
        transaction.description = description
        transaction.category_id = category_id

        db.session.commit()

        flash("Transaction updated successfully")
        return redirect(url_for("transactions.index"))

    return render_template(
        "transactions/edit.html", transaction=transaction, categories=categories
    )


@transactions.route("/transactions/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    user_id = session.get("user_id")
    transaction = Transaction.query.filter_by(id=id, user_id=user_id).first_or_404()

    db.session.delete(transaction)
    db.session.commit()

    flash("Transaction deleted successfully")
    return redirect(url_for("transactions.index"))

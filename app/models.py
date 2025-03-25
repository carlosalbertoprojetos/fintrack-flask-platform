from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    transactions = db.relationship("Transaction", backref="user", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    exclusive = db.Column(db.Boolean, default=False)  # Defina como Boolean
    icon = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(20), nullable=True)
    exclusive = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<Category {self.name}>"


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    exclusive = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<Expense {self.name}>"


class PaymentMethod(db.Model):
    __tablename__ = "payment_method"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<PaymentMethod {self.name}>"


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    paid = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
    recurrence = db.Column(db.String(10), default="none", nullable=False)
    details = db.Column(db.String(500), nullable=True)

    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("expenses.id"), nullable=True)
    payment_method_id = db.Column(
        db.Integer, db.ForeignKey("payment_method.id"), nullable=True
    )

    def __repr__(self):
        return f"<Transaction {self.category_id} - {self.amount}>"

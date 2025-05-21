from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from app import db, login_manager
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    salt = db.Column(db.LargeBinary)  # criptografia
    transactions = db.relationship("Transaction", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config["SECRET_KEY"])
        return s.dumps({"user_id": self.id})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token, max_age=1800)["user_id"]
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"<User {self.username}>"


# Criptografar senha do usuário
class SecureData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    encrypted_data = db.Column(db.LargeBinary)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    exclusive = db.Column(db.Boolean, default=False)
    icon = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<Category {self.name}>"


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    # Chave estrangeira
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)

    # Relacionamento para acessar o objeto Category diretamente
    category = db.relationship("Category", backref="expenses")

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
    payment_date = db.Column(db.DateTime)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    paid = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
    recurrence = db.Column(db.String(10), default="none", nullable=False)
    details = db.Column(db.String(500), nullable=True)

    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    expense_id = db.Column(db.Integer, db.ForeignKey("expenses.id"), nullable=True)
    payment_method_id = db.Column(db.Integer, db.ForeignKey("payment_method.id"))
    payment_method = db.relationship("PaymentMethod", backref="transactions")

    # Relacionamentos
    category = relationship("Category", backref="transactions")
    expense = relationship("Expense", backref="transactions")

    def __repr__(self):
        return f"<Transaction {self.category_id} - {self.amount}>"

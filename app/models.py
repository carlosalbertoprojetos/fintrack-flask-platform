import hashlib
from datetime import datetime

from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    salt = db.Column(db.LargeBinary)
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
        except Exception:
            return None
        return db.session.get(User, user_id)

    def __repr__(self):
        return f"<User {self.username}>"


class SecureData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    encrypted_data = db.Column(db.LargeBinary)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    exclusive = db.Column(db.Boolean, default=False)
    icon = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(20), nullable=True)
    user = db.relationship("User", backref="categories")

    def __repr__(self):
        return f"<Category {self.name}>"


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    name = db.Column(db.String(64), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    category = db.relationship("Category", backref="expenses")
    user = db.relationship("User", backref="expenses")

    def __repr__(self):
        return f"<Expense {self.name}>"


class PaymentMethod(db.Model):
    __tablename__ = "payment_method"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    name = db.Column(db.String(64), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    user = db.relationship("User", backref="payment_methods")

    def __repr__(self):
        return f"<PaymentMethod {self.name}>"


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    payment_date = db.Column(db.DateTime)
    amount = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, nullable=True, default=0.0)
    type = db.Column(db.String(20), nullable=False)
    paid = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
    recurrence = db.Column(db.String(10), default="none", nullable=False)
    details = db.Column(db.String(500), nullable=True)
    description = db.Column(db.String(500), nullable=True)

    conta_id = db.Column(db.Integer, db.ForeignKey("conta.id"), nullable=True)
    conta = db.relationship("Conta", backref="transactions")

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    expense_id = db.Column(db.Integer, db.ForeignKey("expenses.id"), nullable=True)
    payment_method_id = db.Column(db.Integer, db.ForeignKey("payment_method.id"))

    payment_method = db.relationship("PaymentMethod", backref="transactions")
    category = relationship("Category", backref="transactions")
    expense = relationship("Expense", backref="transactions")

    def __repr__(self):
        return f"<Transaction {self.category_id} - {self.amount}>"


class TipoConta(db.Model):
    __tablename__ = "tipo_conta"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref="tipos_conta")

    def __repr__(self):
        return f"<TipoConta {self.nome}>"


class Conta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo_id = db.Column(db.Integer, db.ForeignKey("tipo_conta.id"), nullable=False)
    tipo = db.relationship("TipoConta", backref="contas")
    saldo_inicial = db.Column(db.Float, default=0.0)
    saldo_atual = db.Column(db.Float, nullable=False, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref="contas")

    def __repr__(self):
        return f"<Conta {self.nome} - {self.tipo.nome if self.tipo else 'Sem tipo'}>"

    @staticmethod
    def recalcular_saldos(conta_id=None):
        """
        Backward compatibility hook.
        Balance recomputation now comes from immutable ledger entries.
        """
        from services.ledger_service import LedgerService

        LedgerService.rebuild_account_balances(conta_id=conta_id)

    def atualizar_saldo_investimento(self, tipo_movimentacao, valor, operacao="adicionar"):
        """
        Backward compatibility hook used by legacy routes.
        New logic should write ledger entries through InvestmentService.
        """
        from services.ledger_service import LedgerService

        LedgerService.apply_legacy_investment_balance_adjustment(
            conta=self,
            tipo_movimentacao=tipo_movimentacao,
            valor=valor,
            operacao=operacao,
        )


class LedgerEntry(db.Model):
    __tablename__ = "ledger_entry"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("conta.id"), nullable=False, index=True)
    reference_type = db.Column(db.String(50), nullable=False, index=True)
    reference_id = db.Column(db.Integer, nullable=True, index=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    previous_hash = db.Column(db.String(64), nullable=True)
    current_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)

    user = db.relationship("User", backref="ledger_entries")
    account = db.relationship("Conta", backref="ledger_entries")

    @staticmethod
    def build_hash(
        *,
        user_id,
        account_id,
        reference_type,
        reference_id,
        amount,
        created_at,
        previous_hash,
    ):
        payload = "|".join(
            [
                str(user_id),
                str(account_id),
                str(reference_type),
                str(reference_id or ""),
                str(amount),
                created_at.isoformat(),
                str(previous_hash or ""),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def validate_chain(entries):
        previous = None
        for entry in entries:
            expected = LedgerEntry.build_hash(
                user_id=entry.user_id,
                account_id=entry.account_id,
                reference_type=entry.reference_type,
                reference_id=entry.reference_id,
                amount=entry.amount,
                created_at=entry.created_at,
                previous_hash=entry.previous_hash,
            )
            if entry.previous_hash != previous:
                return False, f"Invalid previous hash at ledger_entry.id={entry.id}"
            if entry.current_hash != expected:
                return False, f"Invalid current hash at ledger_entry.id={entry.id}"
            previous = entry.current_hash
        return True, "ok"


class MonthlyClosure(db.Model):
    __tablename__ = "monthly_closure"
    __table_args__ = (
        db.UniqueConstraint("user_id", "account_id", "year", "month", name="uq_monthly_closure_scope"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("conta.id"), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False, index=True)
    closing_balance = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total_receitas = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total_despesas = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    ledger_hash_snapshot = db.Column(db.String(64), nullable=True)
    locked = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref="monthly_closures")
    account = db.relationship("Conta", backref="monthly_closures")


class SimulationSession(db.Model):
    __tablename__ = "simulation_session"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("conta.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, default="Nova Simulacao")
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref="simulation_sessions")
    account = db.relationship("Conta", backref="simulation_sessions")


class SimulationLedgerEntry(db.Model):
    __tablename__ = "simulation_ledger_entry"

    id = db.Column(db.Integer, primary_key=True)
    simulation_session_id = db.Column(db.Integer, db.ForeignKey("simulation_session.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("conta.id"), nullable=False, index=True)
    reference_type = db.Column(db.String(50), nullable=False, index=True)
    reference_id = db.Column(db.Integer, nullable=True, index=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    previous_hash = db.Column(db.String(64), nullable=True)
    current_hash = db.Column(db.String(64), nullable=False, index=True)

    session = db.relationship("SimulationSession", backref="ledger_entries")
    user = db.relationship("User", backref="simulation_ledger_entries")
    account = db.relationship("Conta", backref="simulation_ledger_entries")

    @staticmethod
    def build_hash(
        *,
        user_id,
        account_id,
        reference_type,
        reference_id,
        amount,
        created_at,
        previous_hash,
    ):
        payload = "|".join(
            [
                str(user_id),
                str(account_id),
                str(reference_type),
                str(reference_id or ""),
                str(amount),
                created_at.isoformat(),
                str(previous_hash or ""),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AIModelMetadata(db.Model):
    __tablename__ = "ai_model_metadata"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    model_type = db.Column(db.String(50), nullable=False, index=True)
    model_version = db.Column(db.String(30), nullable=False, default="v1")
    model_path = db.Column(db.String(500), nullable=False)
    metrics_json = db.Column(db.Text, nullable=True)
    trained_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref="ai_models")


class Investimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_investimento_id = db.Column(db.Integer, db.ForeignKey("tipo_investimento.id"), nullable=True)
    tipo_investimento = db.relationship("TipoInvestimento", backref="investimentos")
    data_abertura = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    movimentacoes = db.relationship(
        "MovimentacaoInvestimento",
        backref="investimento",
        lazy=True,
        cascade="all, delete-orphan",
    )

    @property
    def saldo_atual(self):
        if not self.movimentacoes:
            return 0.0
        movimentacoes_validas = [m for m in self.movimentacoes if m.id is not None]
        if not movimentacoes_validas:
            return 0.0
        ultima = max(movimentacoes_validas, key=lambda m: m.id)
        return ultima.saldo_atual or 0.0

    @property
    def ultimo_rendimento(self):
        movs = [m for m in self.movimentacoes if m.tipo_movimentacao == "rendimento"]
        if movs:
            return sorted(movs, key=lambda m: m.data_movimentacao)[-1].valor
        return 0.0

    @property
    def data_ultimo_rendimento(self):
        movs = [m for m in self.movimentacoes if m.tipo_movimentacao == "rendimento"]
        if movs:
            return sorted(movs, key=lambda m: m.data_movimentacao)[-1].data_movimentacao
        return None

    @property
    def ultima_movimentacao(self):
        if not self.movimentacoes:
            return None
        movimentacoes_validas = [m for m in self.movimentacoes if m.id is not None]
        if not movimentacoes_validas:
            return None
        return max(movimentacoes_validas, key=lambda m: m.id)


class MovimentacaoInvestimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    investimento_id = db.Column(db.Integer, db.ForeignKey("investimento.id"), nullable=False)
    data_movimentacao = db.Column(db.Date, nullable=False)
    tipo_movimentacao = db.Column(db.String(20), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    saldo_anterior = db.Column(db.Float, nullable=False)
    saldo_atual = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref="movimentacoes_investimento")
    conta_id = db.Column(db.Integer, db.ForeignKey("conta.id"), nullable=False)
    conta = db.relationship("Conta", backref="movimentacoes_investimento")

    def __repr__(self):
        return f"<MovimentacaoInvestimento {self.tipo_movimentacao} - {self.valor}>"


class TipoInvestimento(db.Model):
    __tablename__ = "tipo_investimento"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref="tipos_investimento")

    def __repr__(self):
        return f"<TipoInvestimento {self.nome}>"

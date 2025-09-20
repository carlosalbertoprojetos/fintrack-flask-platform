from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from app import db, login_manager
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from enum import Enum


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
    due_date = db.Column(db.DateTime, nullable=True)  # Data de vencimento para despesas
    payment_date = db.Column(db.DateTime)
    amount = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, nullable=True, default=0.0)  # Campo para desconto
    type = db.Column(db.String(20), nullable=False)
    paid = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
    recurrence = db.Column(db.String(10), default="none", nullable=False)
    details = db.Column(db.String(500), nullable=True)
    description = db.Column(
        db.String(500), nullable=True
    )  # Campo para descrição manual
    conta_id = db.Column(db.Integer, db.ForeignKey('conta.id'), nullable=True)
    conta = db.relationship('Conta', backref='transactions')

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
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipo_conta.id'), nullable=False)
    tipo = db.relationship('TipoConta', backref='contas')
    saldo_inicial = db.Column(db.Float, default=0.0)  # Renomeado de 'saldo' para 'saldo_inicial'
    saldo_atual = db.Column(db.Float, nullable=False, default=0.0)  # Saldo atual calculado
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref="contas")
    # investimentos = db.relationship('Investimento', backref='conta', lazy=True)  # REMOVIDO

    def __repr__(self):
        return f"<Conta {self.nome} - {self.tipo.nome if self.tipo else 'Sem tipo'}>"

    @staticmethod
    def recalcular_saldos():
        from app.models import Transaction, MovimentacaoInvestimento
        from app import db
        from sqlalchemy import extract
        contas = Conta.query.all()
        for conta in contas:
            saldo = conta.saldo_inicial or 0.0
            # Considerar apenas transações pagas
            transacoes = Transaction.query.filter_by(conta_id=conta.id, paid=True).order_by(Transaction.date.asc()).all()
            for transacao in transacoes:
                if transacao.type == 'receita':
                    saldo += transacao.amount
                elif transacao.type == 'despesa':
                    valor = transacao.amount - (transacao.discount or 0.0)
                    saldo -= valor
            
            # Considerar movimentações de investimento
            movimentacoes_investimento = MovimentacaoInvestimento.query.filter_by(conta_id=conta.id).all()
            for mov in movimentacoes_investimento:
                if mov.tipo_movimentacao == 'aplicacao':
                    saldo -= mov.valor  # Aplicação diminui o saldo da conta
                elif mov.tipo_movimentacao == 'resgate':
                    saldo += mov.valor  # Resgate aumenta o saldo da conta
                # Rendimento não afeta o saldo da conta
            
            conta.saldo_atual = saldo
        db.session.commit()
    
    def atualizar_saldo_investimento(self, tipo_movimentacao, valor, operacao='adicionar'):
        """
        Atualiza o saldo da conta baseado em movimentações de investimento
        
        Args:
            tipo_movimentacao: 'aplicacao', 'resgate' ou 'rendimento'
            valor: valor da movimentação
            operacao: 'adicionar' ou 'remover' (para edição/exclusão)
        """
        if tipo_movimentacao == 'aplicacao':
            if operacao == 'adicionar':
                self.saldo_atual -= valor  # Aplicação diminui saldo
            else:  # remover
                self.saldo_atual += valor  # Remoção de aplicação aumenta saldo
        elif tipo_movimentacao == 'resgate':
            if operacao == 'adicionar':
                self.saldo_atual += valor  # Resgate aumenta saldo
            else:  # remover
                self.saldo_atual -= valor  # Remoção de resgate diminui saldo
        # Rendimento não afeta saldo da conta
        
        # Garantir que o saldo não fique negativo (opcional)
        if self.saldo_atual < 0:
            self.saldo_atual = 0.0


class Investimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_investimento_id = db.Column(db.Integer, db.ForeignKey('tipo_investimento.id'), nullable=True)
    tipo_investimento = db.relationship('TipoInvestimento', backref='investimentos')
    data_abertura = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    movimentacoes = db.relationship('MovimentacaoInvestimento', backref='investimento', lazy=True, cascade='all, delete-orphan')

    @property
    def saldo_atual(self):
        # Retorna o saldo_atual do último movimento deste investimento
        if not self.movimentacoes:
            return 0.0
        # Usar ID para garantir que pegue o registro mais recente
        # Filtrar apenas movimentações válidas
        movimentacoes_validas = [m for m in self.movimentacoes if m.id is not None]
        if not movimentacoes_validas:
            return 0.0
        ultima = max(movimentacoes_validas, key=lambda m: m.id)
        return ultima.saldo_atual or 0.0

    @property
    def ultimo_rendimento(self):
        # Busca a última movimentação do tipo rendimento
        movs = [m for m in self.movimentacoes if m.tipo_movimentacao == 'rendimento']
        if movs:
            return sorted(movs, key=lambda m: m.data_movimentacao)[-1].valor
        return 0.0

    @property
    def data_ultimo_rendimento(self):
        movs = [m for m in self.movimentacoes if m.tipo_movimentacao == 'rendimento']
        if movs:
            return sorted(movs, key=lambda m: m.data_movimentacao)[-1].data_movimentacao
        return None
    
    @property
    def ultima_movimentacao(self):
        """Retorna a última movimentação do investimento"""
        if not self.movimentacoes:
            return None
        # Usar ID para garantir que pegue o registro mais recente
        movimentacoes_validas = [m for m in self.movimentacoes if m.id is not None]
        if not movimentacoes_validas:
            return None
        return max(movimentacoes_validas, key=lambda m: m.id)


class MovimentacaoInvestimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    investimento_id = db.Column(db.Integer, db.ForeignKey('investimento.id'), nullable=False)
    data_movimentacao = db.Column(db.Date, nullable=False)
    tipo_movimentacao = db.Column(db.String(20), nullable=False)  # 'aplicacao', 'resgate', 'rendimento'
    valor = db.Column(db.Float, nullable=False)
    saldo_anterior = db.Column(db.Float, nullable=False)
    saldo_atual = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref="movimentacoes_investimento")
    conta_id = db.Column(db.Integer, db.ForeignKey('conta.id'), nullable=False)
    conta = db.relationship('Conta', backref='movimentacoes_investimento')

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

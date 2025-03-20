from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Grupo(db.Model):
    __tablename__ = "grupo"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    exclusivo = db.Column(db.String(20), nullable=False)  # 'Receita' ou 'Despesa'


class Descricao(db.Model):
    __tablename__ = "descricao"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    exclusivo = db.Column(
        db.String(20), nullable=True
    )  # Pode ser 'Receita', 'Despesa' ou NULL
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupo.id"))
    grupo = db.relationship("Grupo", backref=db.backref("descricoes", lazy=True))


class FPgto(db.Model):
    __tablename__ = "fpagto"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class Transacao(db.Model):
    __tablename__ = "transacao"
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)  # 'Receita' ou 'Despesa'
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupo.id"), nullable=False)
    descricao_id = db.Column(db.Integer, db.ForeignKey("descricao.id"), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_pgto = db.Column(db.Date, nullable=False)
    forma_pgto_id = db.Column(db.Integer, db.ForeignKey("fpagto.id"), nullable=False)
    detalhes = db.Column(db.String(255))

    grupo = db.relationship("Grupo", backref=db.backref("transacoes", lazy=True))
    descricao = db.relationship(
        "Descricao", backref=db.backref("transacoes", lazy=True)
    )
    forma_pgto = db.relationship("FPgto", backref=db.backref("transacoes", lazy=True))


class Reposicao(db.Model):
    __tablename__ = "reposicao"
    id = db.Column(db.Integer, primary_key=True)
    operacao = db.Column(db.String(10), nullable=False)  # 'Dividir' ou 'Repassar'
    percentual = db.Column(db.Integer, default=5)  # Percentual entre 1 e 10

    transacao_id = db.Column(db.Integer, db.ForeignKey("transacao.id"), nullable=False)
    transacao = db.relationship(
        "Transacao", backref=db.backref("reposicoes", lazy=True)
    )

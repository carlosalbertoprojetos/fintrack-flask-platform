from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum


from forms import GrupoForm, DescricaoForm


# Inicializa o Flask e a conexão com o banco de dados
app = Flask(__name__)
app.config["SECRET_KEY"] = "sua_chave_secreta_segura"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///financas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Modelos de Banco de Dados
class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    exclusivo = db.Column(
        Enum("Receita", "Despesa", name="tipo_exclusivo"), nullable=True
    )


class Descricao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupo.id"), nullable=True)  # Relacionamento com Grupo
    grupo = db.relationship("Grupo", backref=db.backref("descricoes", lazy=True))



class FPgto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupo.id"), nullable=False)
    descricao_id = db.Column(db.Integer, db.ForeignKey("descricao.id"), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_pgto = db.Column(db.String(50))
    forma_pgto_id = db.Column(db.Integer, db.ForeignKey("fpgtos.id"), nullable=False)
    detalhes = db.Column(db.String(200))


class Reposicao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    operacao = db.Column(db.String(50), nullable=False)
    percentual = db.Column(db.Integer, default=5)


# Rota para a página principal
@app.route("/")
def index():
    grupos = Grupo.query.all()
    descricoes = Descricao.query.all()
    fpgtos = FPgto.query.all()
    reposicoes = Reposicao.query.all()
    return render_template(
        "index.html",
        grupos=grupos,
        descricoes=descricoes,
        fpgtos=fpgtos,
        reposicoes=reposicoes,
    )


# Cadastro de Forma de Pagamento (FPgto)
@app.route("/cadastrar_fpgtos", methods=["GET", "POST"])
def cadastrar_fpgtos():
    if request.method == "POST":
        nome = request.form["nome"]
        is_active = "is_active" in request.form
        fpgtos = FPgto(nome=nome, is_active=is_active)
        db.session.add(fpgtos)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("form_fpgtos.html")


# Cadastro de Reposição
@app.route("/cadastrar_reposicao", methods=["GET", "POST"])
def cadastrar_reposicao():
    if request.method == "POST":
        operacao = request.form["operacao"]
        percentual = request.form["percentual"]
        reposicao = Reposicao(operacao=operacao, percentual=percentual)
        db.session.add(reposicao)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("form_reposicao.html")

# Outras rotas de edição e deleção para FPgto, Transação e Reposicao podem ser criadas de forma semelhante.

if __name__ == "__main__":
    db.create_all()  # Cria as tabelas no banco de dados
    app.run(debug=True)


# ==================== Grupo ====================

# Listar Grupo
@app.route("/listar_grupos")
def listar_grupos():
    grupos = Grupo.query.all()
    return render_template("grupo_listar.html", grupos=grupos)


# Cadastrar Grupo
@app.route("/cadastrar_grupo", methods=["GET", "POST"])
def cadastrar_grupo():
    form = GrupoForm()
    grupo = None  # No caso de cadastro, grupo será None
    if form.validate_on_submit():
        # Garantir que o valor para "exclusivo" seja uma string válida ou None
        exclusivo = form.exclusivo.data if form.exclusivo.data in ['Receita', 'Despesa'] else None
        novo_grupo = Grupo(nome=form.nome.data, exclusivo=exclusivo)
        db.session.add(novo_grupo)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("grupo_form.html", form=form, grupo=grupo)


# Editar Grupo
@app.route("/editar_grupo/<int:grupo_id>", methods=["GET", "POST"])
def editar_grupo(grupo_id):
    grupo = Grupo.query.get(grupo_id)
    if request.method == "POST":
        grupo.nome = request.form["nome"]
        grupo.exclusivo = "exclusivo" in request.form
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("form_grupo.html", grupo=grupo)


# Deletar Grupo
@app.route("/deletar_grupo/<int:grupo_id>")
def deletar_grupo(grupo_id):
    grupo = Grupo.query.get(grupo_id)
    db.session.delete(grupo)
    db.session.commit()
    return redirect(url_for("index"))


# ==================== Descrição ====================

# Listar Descrição
@app.route("/descricao_listar")
def listar_descricoes():
    descricoes = Descricao.query.all()
    return render_template("descricao_listar.html", descricoes=descricoes)


# Cadastrar Descrição
@app.route("/cadastrar_descricao", methods=["GET", "POST"])
def cadastrar_descricao():
    form = DescricaoForm()
    # Preenche o campo 'grupo_id' com os grupos existentes
    form.grupo_id.choices = [(grupo.id, grupo.nome) for grupo in Grupo.query.all()]

    if form.validate_on_submit():
        # Criação da nova descrição
        nova_descricao = Descricao(nome=form.nome.data, grupo_id=form.grupo_id.data)
        db.session.add(nova_descricao)
        db.session.commit()

        return redirect(url_for('listar_descricoes'))

    return render_template("descricao_form.html", form=form)


# Editar Descrição
@app.route("/editar_descricao/<int:descricao_id>", methods=["GET", "POST"])
def editar_descricao(descricao_id):
    descricao = Descricao.query.get(descricao_id)
    if request.method == "POST":
        descricao.nome = request.form["nome"]
        descricao.exclusivo = "exclusivo" in request.form
        descricao.grupo_id = request.form["grupo_id"]
        db.session.commit()
        return redirect(url_for("index"))
    grupos = Grupo.query.all()
    return render_template("form_descricao.html", descricao=descricao, grupos=grupos)


# Deletar Descrição
@app.route("/deletar_descricao/<int:descricao_id>")
def deletar_descricao(descricao_id):
    descricao = Descricao.query.get(descricao_id)
    db.session.delete(descricao)
    db.session.commit()
    return redirect(url_for("index"))


# ==================== FPagamento ====================

@app.route("/listar_fpgto")
def listar_fpgtos():
    fpgtos = FPgto.query.all()
    return render_template("listar_fpgtos.html", fpgtos=fpgtos)


@app.route("/listar_transacoes")
def listar_transacoes():
    transacoes = Transacao.query.all()
    return render_template("listar_transacoes.html", transacoes=transacoes)


@app.route("/listar_reposicoes")
def listar_reposicoes():
    reposicoes = Reposicao.query.all()
    return render_template("listar_reposicoes.html", reposicoes=reposicoes)

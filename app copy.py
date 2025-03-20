from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///financas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Receita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    tipo = db.Column(
        db.String(20), nullable=False
    )  # Exemplo: 'aluguel', 'salário', etc.


class Despesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    tipo = db.Column(
        db.String(20), nullable=False
    )  # Exemplo: 'produto', 'serviço', etc.


class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'receita' ou 'despesa'
    transacao_id = db.Column(db.Integer, nullable=False)
    tipo_transacao_id = db.Column(db.Integer, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, descricao, valor, tipo):
        self.descricao = descricao
        self.valor = valor
        self.tipo = tipo

        # Lógica para definir transacao_id e tipo_transacao_id
        if self.descricao == "Receita":
            # Pega os dados de 'Receita'
            receitas = Receita.query.all()
            self.transacao_id = [receita.id for receita in receitas]
            self.tipo_transacao_id = [receita.tipo for receita in receitas]
        elif self.descricao == "Despesa":
            # Pega os dados de 'Despesa'
            despesas = Despesa.query.all()
            self.transacao_id = [despesa.id for despesa in despesas]
            self.tipo_transacao_id = [despesa.tipo for despesa in despesas]


@app.route("/api/receitas")
def get_receitas():
    receitas = Receita.query.all()
    return jsonify([{"id": receita.id, "tipo": receita.tipo} for receita in receitas])


@app.route("/api/despesas")
def get_despesas():
    despesas = Despesa.query.all()
    return jsonify([{"id": despesa.id, "tipo": despesa.tipo} for despesa in despesas])


@app.route("/")
def index():
    receitas = Receita.query.all()
    despesas = Despesa.query.all()
    transacoes = Transacao.query.order_by(Transacao.data.desc()).all()
    total_receitas = sum(t.valor for t in transacoes if t.tipo == "receita")
    total_despesas = sum(t.valor for t in transacoes if t.tipo == "despesa")
    saldo = total_receitas - total_despesas
    return render_template(
        "index.html",
        transacoes=transacoes,
        saldo=saldo,
        receitas=receitas,
        despesas=despesas,
    )


@app.route("/add_receita", methods=["GET", "POST"])
def add_receita():
    if request.method == "POST":
        descricao = request.form["descricao"]
        tipo = request.form["tipo"]
        nova_receita = Receita(descricao=descricao, tipo=tipo)
        db.session.add(nova_receita)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("add_receita.html")


@app.route("/edit_receita/<int:id>", methods=["GET", "POST"])
def edit_receita(id):
    receita = Receita.query.get_or_404(id)
    if request.method == "POST":
        receita.descricao = request.form["descricao"]
        receita.tipo = request.form["tipo"]
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("edit_receita.html", receita=receita)


@app.route("/delete_receita/<int:id>", methods=["GET", "POST"])
def delete_receita(id):
    receita = Receita.query.get_or_404(id)
    db.session.delete(receita)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/add_despesa", methods=["GET", "POST"])
def add_despesa():
    if request.method == "POST":
        descricao = request.form["descricao"]
        tipo = request.form["tipo"]
        nova_despesa = Despesa(descricao=descricao, tipo=tipo)
        db.session.add(nova_despesa)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("add_despesa.html")


@app.route("/edit_despesa/<int:id>", methods=["GET", "POST"])
def edit_despesa(id):
    despesa = Despesa.query.get_or_404(id)
    if request.method == "POST":
        despesa.descricao = request.form["descricao"]
        despesa.tipo = request.form["tipo"]
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("edit_despesa.html", despesa=despesa)


@app.route("/delete_despesa/<int:id>", methods=["GET", "POST"])
def delete_despesa(id):
    despesa = Despesa.query.get_or_404(id)
    db.session.delete(despesa)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/adicionar", methods=["GET", "POST"])
def adicionar():
    receitas = Receita.query.all()  # Pega todas as receitas
    despesas = Despesa.query.all()  # Pega todas as despesas

    if request.method == "POST":
        descricao = request.form["descricao"]
        valor = float(request.form["valor"])
        tipo = request.form["tipo"]  # 'receita' ou 'despesa'

        # Verifica se o tipo é receita ou despesa e atribui as IDs e tipos correspondentes
        if tipo == "receita":
            transacao_id = int(request.form["transacao"])  # ID de uma receita
            tipo_transacao_id = int(request.form["tipo_transacao"])  # Tipo da receita
        elif tipo == "despesa":
            transacao_id = int(request.form["transacao"])  # ID de uma despesa
            tipo_transacao_id = int(request.form["tipo_transacao"])  # Tipo da despesa

        # Criação da nova transação
        nova_transacao = Transacao(
            descricao=descricao,
            valor=valor,
            tipo=tipo,
            transacao_id=transacao_id,
            tipo_transacao_id=tipo_transacao_id,
        )

        db.session.add(nova_transacao)
        db.session.commit()
        return redirect(
            url_for("index")
        )  # Redireciona para a página principal após adicionar

    # Renderiza o template com as receitas e despesas
    return render_template("tipos.html", receitas=receitas, despesas=despesas)


@app.route("/deletar/<int:id>")
def deletar(id):
    transacao = Transacao.query.get(id)
    if transacao:
        db.session.delete(transacao)
        db.session.commit()
    return redirect(url_for("index"))


@app.route("/formulario")
def formulario():
    return render_template("formulario.html")


@app.route("/fechar")
def fechar():
    # Obtém a função de encerramento do servidor (Werkzeug)
    shutdown = request.environ.get("werkzeug.server.shutdown")
    if shutdown:
        shutdown()

    # Retorna uma página com JavaScript para fechar a aba do navegador
    return """
        <script>
            window.close();
        </script>
        <h1>Fechando o sistema...</h1>
    """


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

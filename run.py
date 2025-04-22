import os
from app import create_app, db
from app.models import Category, PaymentMethod, Expense
from flask import Flask, request, abort
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

with app.app_context():
    categories = Category.query.all()
    payments = PaymentMethod.query.all()
    expensives = Expense.query.all()


@app.cli.command("init-db")
def init_db():
    """Inicializa o banco de dados."""
    db.create_all()
    print("Banco de dados inicializado.")


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        abort(500, 'Servidor não está rodando com o Werkzeug')
    func()

@app.route('/shutdown')
def shutdown():
    shutdown_server()
    return 'Servidor encerrado com sucesso.'

if __name__ == "__main__":
    app.run(debug=True)

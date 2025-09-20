import os
import signal
import sys
import threading
from app import create_app, db
from app.models import Category, PaymentMethod, Expense
from flask import Flask, request, abort, jsonify
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


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models import Conta
        from app import db
        # Recalcular saldos das contas silenciosamente
        Conta.recalcular_saldos()
    try:
        print("Iniciando servidor Flask em http://127.0.0.1:5000")
        app.run(host='127.0.0.1', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nEncerrando o servidor...")
        sys.exit(0)

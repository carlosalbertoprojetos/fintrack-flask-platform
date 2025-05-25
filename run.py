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


def shutdown_server():
    """Função para encerrar o servidor Flask e o processo Python"""
    print("Encerrando o servidor...")
    # Encerra o processo Python imediatamente
    os._exit(0)


@app.route("/shutdown", methods=["GET"])
def shutdown():
    """Rota para encerrar o servidor"""
    try:
        # Encerra o servidor imediatamente
        shutdown_server()
        return jsonify({"message": "Encerrando o servidor..."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        print("\nEncerrando o servidor...")
        sys.exit(0)

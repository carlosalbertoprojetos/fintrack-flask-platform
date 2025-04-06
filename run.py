import os
from app import create_app, db
from app.models import Category, PaymentMethod, Expense
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
    app.run(debug=True)

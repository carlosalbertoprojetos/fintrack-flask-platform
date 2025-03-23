import os
from app import create_app, db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

@app.cli.command("init-db")
def init_db():
    """Inicializa o banco de dados."""
    db.create_all()
    print("Banco de dados inicializado.")

if __name__ == '__main__':
    app.run(debug=True)

from app import app, db

# Garantir que o contexto da aplicação seja ativado
with app.app_context():
    db.create_all()  # Criação das tabelas no banco de dados

app.run(debug=True)

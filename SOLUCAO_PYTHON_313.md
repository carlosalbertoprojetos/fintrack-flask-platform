# Solução para Erro Python 3.13 + SQLAlchemy

## Problema
O erro `AssertionError: Class <class 'sqlalchemy.sql.elements.SQLCoreOperations'> directly inherits TypingOnly` ocorre devido a incompatibilidade entre Python 3.13 e versões antigas do SQLAlchemy.

## Soluções

### Opção 1: Usar Python 3.11 ou 3.12 (RECOMENDADO)
1. Desinstale o Python 3.13 atual
2. Baixe e instale Python 3.11 ou 3.12 do site oficial:
   - https://www.python.org/downloads/
3. Execute novamente o instalador

### Opção 2: Atualizar SQLAlchemy (ALTERNATIVA)
Se preferir manter o Python 3.13:
1. Execute o instalador atualizado que já contém a correção
2. O sistema tentará instalar SQLAlchemy >= 2.0.25 automaticamente

### Opção 3: Instalação Manual
Se as opções acima não funcionarem:
```bash
# Atualizar pip
python -m pip install --upgrade pip

# Instalar SQLAlchemy mais recente
pip install "SQLAlchemy>=2.0.25"

# Instalar outras dependências
pip install -r requirements.txt
```

## Verificação
Após a correção, teste se o banco foi criado corretamente:
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Banco inicializado com sucesso!')"
```

## Suporte
Se o problema persistir, entre em contato:
- WhatsApp: +55 (31) 98676-6866
- Email: carlos.medeiros@exemplo.com


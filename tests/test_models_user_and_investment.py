from datetime import date

from app import db
from app.models import (
    Conta,
    Investimento,
    MovimentacaoInvestimento,
    TipoConta,
    TipoInvestimento,
    User,
)


def _create_user_with_account():
    user = User(username="alice", email="alice@example.com")
    user.set_password("secret123")
    db.session.add(user)
    db.session.flush()

    tipo_conta = TipoConta(nome="Banco", descricao="Conta corrente", ativo=True, user_id=user.id)
    db.session.add(tipo_conta)
    db.session.flush()

    conta = Conta(nome="Conta Alice", tipo_id=tipo_conta.id, saldo_inicial=100.0, saldo_atual=100.0, user_id=user.id)
    db.session.add(conta)

    tipo_inv = TipoInvestimento(nome="CDB", descricao="CDB", ativo=True, user_id=user.id)
    db.session.add(tipo_inv)
    db.session.flush()

    investimento = Investimento(tipo_investimento_id=tipo_inv.id, data_abertura=date(2025, 1, 1))
    db.session.add(investimento)
    db.session.flush()

    return user, conta, investimento


def test_user_password_and_reset_token(app_ctx):
    user = User(username="bob", email="bob@example.com")
    user.set_password("my-pass")
    db.session.add(user)
    db.session.commit()

    assert user.check_password("my-pass") is True
    assert user.check_password("wrong") is False

    token = user.get_reset_token()
    loaded_user = User.verify_reset_token(token)
    assert loaded_user is not None
    assert loaded_user.id == user.id


def test_investimento_properties(app_ctx):
    user, conta, investimento = _create_user_with_account()
    db.session.flush()

    mov1 = MovimentacaoInvestimento(
        investimento_id=investimento.id,
        data_movimentacao=date(2025, 1, 10),
        tipo_movimentacao="aplicacao",
        valor=1000.0,
        saldo_anterior=0.0,
        saldo_atual=1000.0,
        user_id=user.id,
        conta_id=conta.id,
    )
    mov2 = MovimentacaoInvestimento(
        investimento_id=investimento.id,
        data_movimentacao=date(2025, 2, 10),
        tipo_movimentacao="rendimento",
        valor=25.0,
        saldo_anterior=1000.0,
        saldo_atual=1025.0,
        user_id=user.id,
        conta_id=conta.id,
    )
    db.session.add_all([mov1, mov2])
    db.session.commit()

    assert investimento.saldo_atual == 1025.0
    assert investimento.ultimo_rendimento == 25.0
    assert investimento.data_ultimo_rendimento == date(2025, 2, 10)
    assert investimento.ultima_movimentacao is not None
    assert investimento.ultima_movimentacao.id == mov2.id

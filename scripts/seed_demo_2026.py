from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / 'instance' / 'financas.db'
if not DB_PATH.exists():
    raise SystemExit(f'Banco de dados nao encontrado em {DB_PATH}')

os.environ['DATABASE_URL'] = f"sqlite:///{DB_PATH.as_posix()}"

from app import create_app, db, initialize_user_default_data
from app.models import (
    Category,
    Conta,
    Expense,
    Investimento,
    LedgerEntry,
    MonthlyClosure,
    MovimentacaoInvestimento,
    PaymentMethod,
    SimulationLedgerEntry,
    SimulationSession,
    TipoConta,
    TipoInvestimento,
    Transaction,
    User,
)
from services.investment_service import InvestmentService
from services.ledger_service import LedgerService
from services.transaction_service import TransactionService

YEAR = 2026
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'admin123'
DEFAULT_EMAIL = 'admin@sistema.com'

SALARIO = 'Sal\u00e1rio'
TRANSFERENCIA = 'Transfer\u00eancia'
CARTAO_CREDITO = 'Cart\u00e3o Cr\u00e9dito'
CARTAO_DEBITO = 'Cart\u00e3o D\u00e9bito'
ALIMENTACAO = 'Alimenta\u00e7\u00e3o'
MORADIA = 'Moradia'
TRANSPORTE = 'Transporte'
SAUDE = 'Sa\u00fade'
EDUCACAO = 'Educa\u00e7\u00e3o'
SERVICOS = 'Servi\u00e7os'
AGUA = '\u00c1gua'
GAS = 'G\u00e1s'
CONDOMINIO = 'Condom\u00ednio'
ACOES = 'A\u00e7\u00f5es'
ITAU = 'Ita\u00fa'
DECIMO_TERCEIRO = '13\u00ba sal\u00e1rio'
CONFRATERNIZACAO = 'Confraterniza\u00e7\u00e3o de fim de ano'

INITIAL_BALANCES = {
    ITAU: 1800.00,
    'Inter': 4200.00,
    'Bradesco': 950.00,
    'Banco do Brasil': 2600.00,
}

SALARY_BY_MONTH = {
    1: 7200.00,
    2: 7200.00,
    3: 7200.00,
    4: 7350.00,
    5: 7350.00,
    6: 7350.00,
    7: 7500.00,
    8: 7500.00,
    9: 7500.00,
    10: 7650.00,
    11: 7650.00,
    12: 7650.00,
}

FREELANCE_BY_MONTH = {
    1: 850.00,
    2: 0.00,
    3: 1200.00,
    4: 650.00,
    5: 1500.00,
    6: 0.00,
    7: 980.00,
    8: 1400.00,
    9: 700.00,
    10: 1750.00,
    11: 0.00,
    12: 2200.00,
}

MONTH_NAMES = {
    1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
    7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez',
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Popula uma base demo financeira para um usuario.')
    parser.add_argument('--username', default=DEFAULT_USERNAME)
    parser.add_argument('--password', default=DEFAULT_PASSWORD)
    parser.add_argument('--email', default=DEFAULT_EMAIL)
    return parser.parse_args()


def dt(month: int, day: int, hour: int = 10, minute: int = 0) -> datetime:
    return datetime(YEAR, month, day, hour, minute, 0)


def backup_database() -> Path:
    backup_dir = PROJECT_ROOT / 'instance' / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"financas_demo_admin_2026_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def required(mapping: dict[str, object], key: str):
    value = mapping.get(key)
    if value is None:
        raise RuntimeError(f'Recurso obrigatorio nao encontrado: {key}')
    return value


def get_or_create_user(*, username: str, email: str, password: str) -> User:
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    else:
        user.email = email
        user.set_password(password)
        db.session.commit()
    return user


def ensure_account_setup(user: User) -> None:
    tipo_fisico = TipoConta.query.filter_by(user_id=user.id, nome='Banco Físico').first()
    if tipo_fisico is None:
        tipo_fisico = TipoConta(nome='Banco Físico', descricao='Fisico', ativo=True, user_id=user.id)
        db.session.add(tipo_fisico)

    tipo_virtual = TipoConta.query.filter_by(user_id=user.id, nome='Banco Virtual').first()
    if tipo_virtual is None:
        tipo_virtual = TipoConta(nome='Banco Virtual', descricao='Virtual', ativo=True, user_id=user.id)
        db.session.add(tipo_virtual)

    db.session.flush()

    desired_accounts = {
        ITAU: tipo_fisico.id,
        'Inter': tipo_virtual.id,
        'Bradesco': tipo_fisico.id,
        'Banco do Brasil': tipo_fisico.id,
    }
    for nome, tipo_id in desired_accounts.items():
        conta = Conta.query.filter_by(user_id=user.id, nome=nome).first()
        if conta is None:
            conta = Conta(
                nome=nome,
                tipo_id=tipo_id,
                saldo_inicial=INITIAL_BALANCES[nome],
                saldo_atual=INITIAL_BALANCES[nome],
                user_id=user.id,
            )
        else:
            conta.tipo_id = tipo_id
        db.session.add(conta)

    db.session.commit()


def reset_user_financial_data(user: User) -> dict[str, int]:
    investment_ids = [
        row[0]
        for row in db.session.query(MovimentacaoInvestimento.investimento_id)
        .filter(MovimentacaoInvestimento.user_id == user.id)
        .distinct()
        .all()
    ]
    counts = {
        'transactions_deleted': Transaction.query.filter_by(user_id=user.id).count(),
        'ledger_deleted': LedgerEntry.query.filter_by(user_id=user.id).count(),
        'investment_moves_deleted': MovimentacaoInvestimento.query.filter_by(user_id=user.id).count(),
        'monthly_closures_deleted': MonthlyClosure.query.filter_by(user_id=user.id).count(),
        'simulation_sessions_deleted': SimulationSession.query.filter_by(user_id=user.id).count(),
        'simulation_entries_deleted': SimulationLedgerEntry.query.filter_by(user_id=user.id).count(),
        'investments_deleted': len(investment_ids),
    }

    SimulationLedgerEntry.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    SimulationSession.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    MonthlyClosure.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    LedgerEntry.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    Transaction.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    MovimentacaoInvestimento.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    if investment_ids:
        Investimento.query.filter(Investimento.id.in_(investment_ids)).delete(synchronize_session=False)

    for conta in Conta.query.filter_by(user_id=user.id).all():
        conta.saldo_inicial = INITIAL_BALANCES.get(conta.nome, 0.0)
        conta.saldo_atual = conta.saldo_inicial
        db.session.add(conta)

    db.session.commit()
    return counts


def ensure_accounts(user: User) -> dict[str, Conta]:
    accounts = {conta.nome: conta for conta in Conta.query.filter_by(user_id=user.id).all()}
    missing = [name for name in INITIAL_BALANCES if name not in accounts]
    if missing:
        raise RuntimeError(f'Contas obrigatorias ausentes: {missing}')
    return accounts


def load_resources(user: User) -> dict[str, dict[str, object]]:
    categories = {item.name: item for item in Category.query.all()}
    expenses = {item.name: item for item in Expense.query.all()}
    payment_methods = {item.name: item for item in PaymentMethod.query.all()}
    investment_types = {item.nome: item for item in TipoInvestimento.query.filter_by(user_id=user.id).all()}
    accounts = ensure_accounts(user)

    for name in [
        SALARIO, 'Freelance', 'Investimentos', 'Outros Rendimentos', ALIMENTACAO, MORADIA,
        TRANSPORTE, 'Lazer', SAUDE, EDUCACAO, SERVICOS, 'Compras', 'Diversos'
    ]:
        required(categories, name)
    for name in [
        'Aluguel', CONDOMINIO, 'IPTU', 'Supermercado', 'Restaurante', 'Combustível', 'Manutenção',
        'Farmácia', 'Médico', 'Curso', 'Internet', 'Telefone', 'Energia', AGUA, GAS,
        'Roupas', 'Eletrônicos', 'CDB', ACOES, 'Fundos'
    ]:
        required(expenses, name)
    for name in ['Pix', TRANSFERENCIA, CARTAO_DEBITO, CARTAO_CREDITO, 'Boleto']:
        required(payment_methods, name)
    for name in ['CDB', ACOES, 'Fundos', 'Tesouro Direto']:
        required(investment_types, name)

    return {
        'categories': categories,
        'expenses': expenses,
        'payment_methods': payment_methods,
        'investment_types': investment_types,
        'accounts': accounts,
    }


def create_transaction(user: User, resources: dict[str, dict[str, object]], *, when: datetime, tx_type: str,
                       account: str, category: str, amount: float, payment: str,
                       expense: str | None = None, description: str | None = None,
                       details: str | None = None, notes: str | None = None,
                       discount: float = 0.0, recurrence: str = 'none') -> Transaction:
    payload = {
        'type': tx_type,
        'date': when,
        'due_date': when,
        'payment_date': when,
        'amount': amount,
        'discount': discount,
        'paid': True,
        'category_id': required(resources['categories'], category).id,
        'expense_id': required(resources['expenses'], expense).id if expense else None,
        'description': description,
        'payment_method_id': required(resources['payment_methods'], payment).id,
        'recurrence': recurrence,
        'details': details,
        'notes': notes,
        'conta_id': required(resources['accounts'], account).id,
    }
    return TransactionService.create_transaction(user_id=user.id, payload=payload)


def create_investment(resources: dict[str, dict[str, object]], *, investment_type: str, opening_date: date) -> Investimento:
    inv = Investimento(tipo_investimento_id=required(resources['investment_types'], investment_type).id, data_abertura=opening_date)
    db.session.add(inv)
    db.session.commit()
    return inv


def create_investment_movement(user: User, resources: dict[str, dict[str, object]], *, investimento: Investimento,
                               account: str, movement_date: date, movement_type: str,
                               amount: float, notes: str) -> MovimentacaoInvestimento:
    return InvestmentService.create_movement(
        user_id=user.id,
        investimento=investimento,
        conta_id=required(resources['accounts'], account).id,
        data_movimentacao=movement_date,
        tipo_movimentacao=movement_type,
        valor=amount,
        observacoes=notes,
    )


def seed_transactions(user: User, resources: dict[str, dict[str, object]]) -> None:
    create_transaction(user, resources, when=dt(1, 1, 9), tx_type='receita', account='Inter', category='Outros Rendimentos', amount=500.00, payment='Pix', description='Bonus de abertura de ano', details='Credito inicial para compor a base demo de 2026.')

    for month in range(1, 13):
        month_name = MONTH_NAMES[month]
        salary = SALARY_BY_MONTH[month]
        salary_inter = round(salary * 0.65, 2)
        salary_bb = round(salary - salary_inter, 2)

        create_transaction(user, resources, when=dt(month, 5, 9), tx_type='receita', account='Inter', category=SALARIO, amount=salary_inter, payment=TRANSFERENCIA, description=f'Salario principal {month_name}/2026', details='Parcela principal da receita mensal.', recurrence='monthly')
        create_transaction(user, resources, when=dt(month, 5, 9), tx_type='receita', account='Banco do Brasil', category=SALARIO, amount=salary_bb, payment=TRANSFERENCIA, description=f'Reserva de moradia {month_name}/2026', details='Parcela da receita direcionada para despesas fixas.', recurrence='monthly')

        freelance = FREELANCE_BY_MONTH[month]
        if freelance:
            create_transaction(user, resources, when=dt(month, 18, 14), tx_type='receita', account=ITAU, category='Freelance', amount=freelance, payment='Pix', description=f'Projeto freelance {month_name}/2026', details='Servicos de consultoria e pequenos projetos.')

        create_transaction(user, resources, when=dt(month, 1, 9), tx_type='despesa', account='Banco do Brasil', category=MORADIA, expense='Aluguel', amount=1850 + (20 * (month > 6)), payment=TRANSFERENCIA, description=f'Aluguel {month_name}/2026', details='Pagamento mensal da moradia.', recurrence='monthly')
        create_transaction(user, resources, when=dt(month, 10, 9), tx_type='despesa', account='Banco do Brasil', category=MORADIA, expense=CONDOMINIO, amount=420 + month, payment='Boleto', description=f'Condominio {month_name}/2026', recurrence='monthly')
        create_transaction(user, resources, when=dt(month, 12, 10), tx_type='despesa', account='Banco do Brasil', category=SERVICOS, expense='Energia', amount=150 + (month * 4), payment='Boleto', description=f'Conta de energia {month_name}/2026', recurrence='monthly')
        create_transaction(user, resources, when=dt(month, 14, 10), tx_type='despesa', account='Banco do Brasil', category=SERVICOS, expense=AGUA, amount=78 + (month * 2.5), payment='Boleto', description=f'Conta de agua {month_name}/2026', recurrence='monthly')
        create_transaction(user, resources, when=dt(month, 8, 11), tx_type='despesa', account='Inter', category=SERVICOS, expense='Internet', amount=119.90, payment='Pix', description='Internet fibra', recurrence='monthly')
        create_transaction(user, resources, when=dt(month, 8, 12), tx_type='despesa', account='Inter', category=SERVICOS, expense='Telefone', amount=64.90, payment='Pix', description='Plano movel', recurrence='monthly')
        create_transaction(user, resources, when=dt(month, 6, 18), tx_type='despesa', account='Inter', category=ALIMENTACAO, expense='Supermercado', amount=690 + (month * 5), payment=CARTAO_DEBITO, description=f'Supermercado quinzenal A {month_name}/2026', recurrence='monthly')
        create_transaction(user, resources, when=dt(month, 21, 18), tx_type='despesa', account='Inter', category=ALIMENTACAO, expense='Supermercado', amount=520 + (month * 4), payment=CARTAO_DEBITO, description=f'Supermercado quinzenal B {month_name}/2026', recurrence='monthly')
        create_transaction(user, resources, when=dt(month, 9, 8), tx_type='despesa', account='Inter', category=TRANSPORTE, expense='Combustível', amount=250 + (month * 6), payment=CARTAO_CREDITO, description=f'Combustivel {month_name}/2026', recurrence='monthly')
        create_transaction(user, resources, when=dt(month, 16, 20), tx_type='despesa', account='Inter', category=ALIMENTACAO, expense='Restaurante', amount=95 + (month * 7), payment=CARTAO_CREDITO, description=f'Refeicoes fora {month_name}/2026')

        if month % 2 == 0:
            create_transaction(user, resources, when=dt(month, 24, 20), tx_type='despesa', account='Inter', category='Lazer', amount=180 + (month * 10), payment=CARTAO_CREDITO, description=f'Lazer {month_name}/2026', details='Cinema, streaming e saidas ocasionais.')
        if month in {1, 2, 3, 4, 5, 6}:
            create_transaction(user, resources, when=dt(month, 11, 13), tx_type='despesa', account='Inter', category=EDUCACAO, expense='Curso', amount=219.90, payment='Pix', description=f'Curso de capacitacao {month_name}/2026', recurrence='monthly')
        if month in {1, 4, 7, 10}:
            create_transaction(user, resources, when=dt(month, 25, 15), tx_type='despesa', account=ITAU, category=SAUDE, expense='Médico', amount=320 + (month * 3), payment='Pix', description=f'Consulta medica {month_name}/2026')
        elif month in {2, 5, 8, 11}:
            create_transaction(user, resources, when=dt(month, 25, 15), tx_type='despesa', account=ITAU, category=SAUDE, expense='Farmácia', amount=88 + (month * 4), payment='Pix', description=f'Farmacia {month_name}/2026')
        if month in {2, 4, 6, 8, 10, 12}:
            create_transaction(user, resources, when=dt(month, 27, 10), tx_type='despesa', account='Banco do Brasil', category=SERVICOS, expense=GAS, amount=108 + month, payment='Boleto', description=f'Reposicao de gas {month_name}/2026')

    create_transaction(user, resources, when=dt(1, 7, 9), tx_type='despesa', account='Banco do Brasil', category=MORADIA, expense='IPTU', amount=620.00, payment='Boleto', description='IPTU 2026', details='Pagamento anual do IPTU.')
    create_transaction(user, resources, when=dt(3, 22, 11), tx_type='despesa', account='Inter', category=TRANSPORTE, expense='Manutenção', amount=540.00, payment=CARTAO_CREDITO, description='Revisao preventiva do veiculo')
    create_transaction(user, resources, when=dt(9, 18, 11), tx_type='despesa', account='Inter', category=TRANSPORTE, expense='Manutenção', amount=680.00, payment=CARTAO_CREDITO, description='Troca de pneus e alinhamento')
    create_transaction(user, resources, when=dt(4, 20, 16), tx_type='despesa', account=ITAU, category='Compras', expense='Roupas', amount=420.00, payment=CARTAO_CREDITO, description='Renovacao do guarda-roupa')
    create_transaction(user, resources, when=dt(8, 17, 16), tx_type='despesa', account=ITAU, category='Compras', expense='Eletrônicos', amount=1350.00, payment=CARTAO_CREDITO, description='Monitor para home office')
    create_transaction(user, resources, when=dt(11, 24, 16), tx_type='despesa', account=ITAU, category='Compras', expense='Roupas', amount=680.00, payment=CARTAO_CREDITO, description='Compras de fim de ano')
    create_transaction(user, resources, when=dt(5, 28, 15), tx_type='receita', account='Banco do Brasil', category='Outros Rendimentos', amount=1450.00, payment=TRANSFERENCIA, description='Restituicao do IRPF')
    create_transaction(user, resources, when=dt(7, 10, 10), tx_type='despesa', account='Inter', category='Lazer', amount=1850.00, payment=CARTAO_CREDITO, description='Viagem curta de ferias', details='Hospedagem, alimentacao e passeios.')
    create_transaction(user, resources, when=dt(12, 20, 9), tx_type='receita', account='Inter', category=SALARIO, amount=4700.00, payment=TRANSFERENCIA, description=f'{DECIMO_TERCEIRO} principal 2026', details='Parcela principal do decimo terceiro.')
    create_transaction(user, resources, when=dt(12, 20, 9), tx_type='receita', account='Banco do Brasil', category=SALARIO, amount=2950.00, payment=TRANSFERENCIA, description=f'{DECIMO_TERCEIRO} para despesas fixas 2026', details='Parcela do decimo terceiro reservada para compromissos anuais.')
    create_transaction(user, resources, when=dt(6, 14, 20), tx_type='despesa', account='Bradesco', category=TRANSPORTE, expense='Combustível', amount=190.00, payment=CARTAO_CREDITO, description='Combustivel eventual conta Bradesco')
    create_transaction(user, resources, when=dt(12, 31, 21), tx_type='despesa', account='Bradesco', category='Lazer', amount=280.00, payment=CARTAO_CREDITO, description=CONFRATERNIZACAO)


def seed_investments(user: User, resources: dict[str, dict[str, object]]) -> None:
    cdb = create_investment(resources, investment_type='CDB', opening_date=date(YEAR, 1, 10))
    tesouro = create_investment(resources, investment_type='Tesouro Direto', opening_date=date(YEAR, 2, 15))
    acoes = create_investment(resources, investment_type=ACOES, opening_date=date(YEAR, 3, 12))

    for movement_date, movement_type, amount, notes in [
        (date(YEAR, 1, 10), 'aplicacao', 1000.00, 'Aporte inicial no CDB'),
        (date(YEAR, 2, 28), 'rendimento', 38.00, 'Rendimento mensal CDB fevereiro'),
        (date(YEAR, 3, 10), 'aplicacao', 600.00, 'Aporte programado CDB marco'),
        (date(YEAR, 3, 31), 'rendimento', 42.00, 'Rendimento mensal CDB marco'),
        (date(YEAR, 4, 10), 'aplicacao', 600.00, 'Aporte programado CDB abril'),
        (date(YEAR, 4, 30), 'rendimento', 46.00, 'Rendimento mensal CDB abril'),
        (date(YEAR, 5, 10), 'aplicacao', 600.00, 'Aporte programado CDB maio'),
        (date(YEAR, 5, 31), 'rendimento', 49.00, 'Rendimento mensal CDB maio'),
        (date(YEAR, 6, 10), 'aplicacao', 600.00, 'Aporte programado CDB junho'),
        (date(YEAR, 6, 30), 'rendimento', 53.00, 'Rendimento mensal CDB junho'),
        (date(YEAR, 7, 10), 'aplicacao', 600.00, 'Aporte programado CDB julho'),
        (date(YEAR, 7, 31), 'rendimento', 57.00, 'Rendimento mensal CDB julho'),
        (date(YEAR, 8, 10), 'aplicacao', 600.00, 'Aporte programado CDB agosto'),
        (date(YEAR, 8, 31), 'rendimento', 60.00, 'Rendimento mensal CDB agosto'),
        (date(YEAR, 9, 10), 'aplicacao', 600.00, 'Aporte programado CDB setembro'),
        (date(YEAR, 9, 30), 'rendimento', 63.00, 'Rendimento mensal CDB setembro'),
        (date(YEAR, 10, 10), 'aplicacao', 600.00, 'Aporte programado CDB outubro'),
        (date(YEAR, 10, 31), 'rendimento', 67.00, 'Rendimento mensal CDB outubro'),
        (date(YEAR, 11, 20), 'resgate', 2200.00, 'Resgate parcial para caixa de fim de ano'),
        (date(YEAR, 11, 30), 'rendimento', 69.00, 'Rendimento mensal CDB novembro'),
        (date(YEAR, 12, 31), 'rendimento', 72.00, 'Rendimento mensal CDB dezembro'),
    ]:
        create_investment_movement(user, resources, investimento=cdb, account='Inter', movement_date=movement_date, movement_type=movement_type, amount=amount, notes=notes)

    for movement_date, movement_type, amount, notes in [
        (date(YEAR, 2, 15), 'aplicacao', 800.00, 'Aporte inicial Tesouro Direto'),
        (date(YEAR, 4, 15), 'aplicacao', 800.00, 'Aporte programado Tesouro abril'),
        (date(YEAR, 6, 30), 'rendimento', 55.00, 'Rendimento semestral Tesouro'),
        (date(YEAR, 7, 15), 'aplicacao', 900.00, 'Aporte programado Tesouro julho'),
        (date(YEAR, 10, 15), 'aplicacao', 900.00, 'Aporte programado Tesouro outubro'),
        (date(YEAR, 12, 31), 'rendimento', 140.00, 'Rendimento acumulado Tesouro dezembro'),
    ]:
        create_investment_movement(user, resources, investimento=tesouro, account='Banco do Brasil', movement_date=movement_date, movement_type=movement_type, amount=amount, notes=notes)

    for movement_date, movement_type, amount, notes in [
        (date(YEAR, 3, 12), 'aplicacao', 500.00, 'Compra inicial de acoes'),
        (date(YEAR, 4, 12), 'aplicacao', 350.00, 'Aporte mensal acoes abril'),
        (date(YEAR, 5, 20), 'rendimento', 25.00, 'Dividendos maio'),
        (date(YEAR, 6, 12), 'aplicacao', 350.00, 'Aporte mensal acoes junho'),
        (date(YEAR, 8, 20), 'rendimento', 28.00, 'Dividendos agosto'),
        (date(YEAR, 9, 12), 'aplicacao', 450.00, 'Aporte mensal acoes setembro'),
        (date(YEAR, 11, 25), 'rendimento', 35.00, 'Dividendos novembro'),
        (date(YEAR, 12, 20), 'resgate', 900.00, 'Venda parcial para realizacao de lucro'),
        (date(YEAR, 12, 31), 'rendimento', 30.00, 'Dividendos dezembro'),
    ]:
        create_investment_movement(user, resources, investimento=acoes, account=ITAU, movement_date=movement_date, movement_type=movement_type, amount=amount, notes=notes)


def summarize(user: User) -> None:
    tx_count = Transaction.query.filter_by(user_id=user.id).count()
    receita_count = Transaction.query.filter_by(user_id=user.id, type='receita').count()
    despesa_count = Transaction.query.filter_by(user_id=user.id, type='despesa').count()
    investment_move_count = MovimentacaoInvestimento.query.filter_by(user_id=user.id).count()
    ledger_count = LedgerEntry.query.filter_by(user_id=user.id).count()
    date_range = db.session.query(db.func.min(Transaction.date), db.func.max(Transaction.date)).filter_by(user_id=user.id).first()

    print('Resumo da demo 2026')
    print('-------------------')
    print(f'Usuario: {user.username}')
    print(f'Transacoes: {tx_count} (receitas={receita_count}, despesas={despesa_count})')
    print(f'Movimentacoes de investimento: {investment_move_count}')
    print(f'Lancamentos no ledger: {ledger_count}')
    print(f'Periodo das transacoes: {date_range[0]} ate {date_range[1]}')
    print('Saldos por conta:')
    for conta in Conta.query.filter_by(user_id=user.id).order_by(Conta.id.asc()).all():
        ok, message = LedgerService.validate_integrity(user_id=user.id, account_id=conta.id)
        if not ok:
            raise RuntimeError(f'Falha de integridade na conta {conta.nome}: {message}')
        print(f'  - {conta.nome}: inicial={conta.saldo_inicial:.2f} atual={conta.saldo_atual:.2f}')


def main() -> None:
    args = parse_args()
    backup_path = backup_database()
    print(f'Backup criado em: {backup_path}')

    app = create_app()
    with app.app_context():
        db.create_all()
        user = get_or_create_user(username=args.username, email=args.email, password=args.password)
        initialize_user_default_data(user)
        ensure_account_setup(user)
        deleted = reset_user_financial_data(user)
        resources = load_resources(user)
        seed_transactions(user, resources)
        seed_investments(user, resources)
        LedgerService.rebuild_account_balances(user_id=user.id)
        summarize(user)
        print('Registros removidos antes do seed:')
        for key, value in deleted.items():
            print(f'  - {key}: {value}')
        print(f'Usuario seedado: {args.username}')
        print(f'Senha garantida como: {args.password}')


if __name__ == '__main__':
    main()

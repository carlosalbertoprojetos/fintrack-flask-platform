# SFP V3 - Estrategia de Migracao e Backfill

## Objetivo
Migrar de saldo mutavel para ledger imutavel, preservando dados historicos e sem perda de saldo por conta.

## Etapas
1. Aplicar migracao Alembic `d2f6e9b1c4a0_sfp_v3_ledger_and_ai_models.py`.
2. Congelar escrita em janela de manutencao (opcional em producao).
3. Executar backfill por conta/usuario usando `LedgerService.backfill_account_ledger(...)`.
4. Recalcular saldos com `LedgerService.rebuild_account_balances(...)`.
5. Validar integridade de cadeia com `LedgerService.validate_integrity(...)`.
6. Habilitar bloqueio mensal com `ClosureService.close_month(...)` para periodos ja encerrados.

## Script de Backfill (exemplo)
```python
from app import create_app
from app.models import Conta
from services.ledger_service import LedgerService

app = create_app()
with app.app_context():
    contas = Conta.query.all()
    for conta in contas:
        LedgerService.backfill_account_ledger(
            user_id=conta.user_id,
            account_id=conta.id,
            clear_existing=True,
        )
```

## Validacoes Pos-Migracao
- Saldo por conta (antes/depois) deve bater.
- Nenhuma cadeia de hash invalida.
- Relatorio mensal por ledger coerente com historico.

## Rollback
- Reverter migracao Alembic.
- Restaurar backup SQLite/DB anterior.
- Reativar fluxo legado temporariamente.

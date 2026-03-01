# SFP V3 - Breaking Changes

## 1. Mutacao de saldo
- Saldo de conta agora e derivado do ledger (nao deve ser alterado manualmente em rotas).

## 2. Fechamento mensal
- Periodos bloqueados rejeitam alteracao de transacoes/movimentacoes.

## 3. Servicos obrigatorios para escrita
- Fluxos de escrita devem usar `TransactionService` e `InvestmentService`.

## 4. Configuracao
- `SECRET_KEY` deve vir de variavel de ambiente em producao.
- Path de backup e configuravel por `SFP_BACKUP_DIR`.

## 5. Migracao de schema
- Novas tabelas: `ledger_entry`, `monthly_closure`, `simulation_session`, `simulation_ledger_entry`, `ai_model_metadata`.

## Compatibilidade
- Hooks legados em `Conta` foram mantidos para transicao controlada.

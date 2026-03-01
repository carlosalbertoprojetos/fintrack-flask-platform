# PRD - SFP V3 Enterprise

Status: consolidado apos refactor arquitetural para ledger imutavel, service layer e preparacao AI local.

## 1. Visao de Produto
SFP V3 Enterprise e um sistema financeiro pessoal com trilha auditavel por hash chain, fechamento mensal bloqueavel, simulacao isolada e modulos de inteligencia local por usuario.

## 2. Objetivo do Refactor
- Eliminar mutacao financeira sem rastreabilidade.
- Centralizar regra de negocio em servicos.
- Habilitar evolucao segura para SaaS (PostgreSQL-ready, observabilidade e governanca de dados).

## 3. Diagnostico Tecnico (Antes)
Resumo detalhado em [docs/sfp_v3/01_diagnostico_tecnico.md](docs/sfp_v3/01_diagnostico_tecnico.md).

Principais riscos anteriores:
1. Regras de negocio em rotas.
2. Mutacao direta de saldo.
3. Seguranca insuficiente (secret/key path/login guard).
4. Ausencia de fechamento mensal e simulacao isolada.

## 4. Estrutura Alvo
Detalhe em [docs/sfp_v3/02_estrutura_proposta.md](docs/sfp_v3/02_estrutura_proposta.md).

## 5. Modelagem SFP V3
Novas entidades em `app/models.py`:
1. `LedgerEntry` (hash chain, trilha imutavel).
2. `MonthlyClosure` (fechamento por mes/conta/usuario).
3. `SimulationSession` e `SimulationLedgerEntry` (isolamento de cenario).
4. `AIModelMetadata` (governanca de modelos locais).

## 6. Camada de Servicos
Implementado em `services/`:
1. `ledger_service.py`
2. `transaction_service.py`
3. `investment_service.py`
4. `closure_service.py`
5. `report_service.py`
6. `ai_classification_service.py`
7. `anomaly_detection_service.py`
8. `projection_service.py`
9. `data_quality_service.py`

## 7. Exemplo de Criacao de Transacao via Ledger
```python
payload = {
    "type": "despesa",
    "date": datetime(2025, 1, 15),
    "due_date": datetime(2025, 1, 15),
    "payment_date": datetime(2025, 1, 15),
    "amount": 120.0,
    "discount": 20.0,
    "paid": True,
    "category_id": 10,
    "payment_method_id": 3,
    "conta_id": 2,
}

TransactionService.create_transaction(user_id=current_user.id, payload=payload)
# efeito financeiro gera LedgerEntry automaticamente
```

## 8. Seguranca e Infra
Aplicado:
1. `SECRET_KEY` por ambiente (`config.py`).
2. Rate limiting de login (`app/routes.py`).
3. `login_required` em rotas de investimento.
4. Logging estruturado JSON (`app/__init__.py`).
5. Backup sem path hardcoded (`SFP_BACKUP_DIR`).
6. `DATABASE_URL` normalizado para PostgreSQL.

## 9. Migracao e Backfill
Estrategia completa em [docs/sfp_v3/03_estrategia_migracao_backfill.md](docs/sfp_v3/03_estrategia_migracao_backfill.md).

Inclui:
1. Migracao Alembic das novas tabelas.
2. Script de backfill por conta.
3. Validacao de integridade da cadeia e reconciliacao de saldo.

## 10. Breaking Changes
Lista em [docs/sfp_v3/04_breaking_changes.md](docs/sfp_v3/04_breaking_changes.md).

## 11. Criterios de Aceite V3
1. Toda mutacao financeira de transacao/investimento passa por service + ledger.
2. Integridade de hash chain validavel por conta/usuario.
3. Fechamento mensal bloqueia edicao no periodo.
4. Simulacao nao altera ledger real.
5. Projecao e score financeiro disponiveis sem API externa.

## 12. Testes
Novos testes de servicos em `tests/test_services_layer.py` cobrindo:
1. Integridade de ledger.
2. Lock de fechamento mensal.
3. Ciclo completo de transacao e investimento via services.
4. Projecao, simulacao e qualidade de dados.
5. Treino/classificacao e deteccao de anomalias locais.

## 13. Proximos Passos Recomendados
1. Reduzir logica remanescente em rotas de dashboard para `ReportService`.
2. Completar migracao de telas legadas para service layer estrita.
3. Introduzir pipeline CI com gates de cobertura por modulo.

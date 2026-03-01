# SFP V3 - Estrutura de Pastas Proposta

```text
app/
  __init__.py
  models.py
  routes.py
  forms.py
  templates/
  static/
routes/
  conta.py
  investimento.py
  tipo_conta.py
  tipo_investimento.py
services/
  ledger_service.py
  transaction_service.py
  investment_service.py
  closure_service.py
  report_service.py
  ai_classification_service.py
  anomaly_detection_service.py
  projection_service.py
  data_quality_service.py
migrations/
  versions/
    d2f6e9b1c4a0_sfp_v3_ledger_and_ai_models.py
tests/
  test_services_layer.py
  ... (demais testes)
docs/
  sfp_v3/
    01_diagnostico_tecnico.md
    02_estrutura_proposta.md
    03_estrategia_migracao_backfill.md
    04_breaking_changes.md
```

## Diretriz de Organizacao
- Rotas: apenas orquestracao HTTP e serializacao.
- Services: validacoes, regras de estado e transacoes de negocio.
- Models: entidades e constraints.
- Ledger: fonte unica para mutacoes financeiras auditaveis.

# SFP V3 - Diagnostico Tecnico (Pre-Refactor)

## 1. Acoplamento Arquitetural
- Regras de negocio distribuidas em `app/routes.py` e `routes/investimento.py`, com baixa separacao entre camada HTTP e dominio.
- Recalculo de saldo dependente de mutacao direta em `Conta.saldo_atual`, com risco de divergencia historica.
- Relatorios calculados em rotas com logica duplicada e sem fachada de servico.

## 2. Padrao de Mutacao de Saldo (Antes)
- Atualizacao de saldo em fluxo de transacao e investimento sem livro imutavel.
- Recalculo global de contas acionado por rotas, sem trilha auditavel por evento financeiro.
- Ausencia de hash chain para detectar adulteracao de historico.

## 3. Seguranca (Antes)
- Fallback de `SECRET_KEY` fraco/hardcoded.
- Rotas de investimento sem `login_required` em alguns endpoints.
- Path de backup hardcoded no Windows (`C:\backup`).
- Sem rate limiting de login.

## 4. Dados e Evolucao
- Sem entidades para fechamento mensal bloqueado.
- Sem isolamento de simulacao (cenario vs real).
- Sem metadados de modelos locais de IA por usuario.
- Migracoes existentes sem objetos do novo ledger enterprise.

## 5. Testes (Antes)
- Cobertura focal em rotas e modelos legados.
- Ausencia de testes obrigatorios: integridade de ledger, lock de fechamento mensal e acuracia de projecao.

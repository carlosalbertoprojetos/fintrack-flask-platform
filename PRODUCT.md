# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Usuários individuais que querem organizar e acompanhar a própria vida financeira. Cada usuário mantém seus próprios dados.

## Product Purpose

O SFP Flask é uma aplicação web local de finanças pessoais. Ajuda o usuário a acompanhar e organizar suas finanças em um só lugar, incluindo contas, receitas e despesas, vencimentos, pagamentos, saldos, investimentos e relatórios.

## Positioning

O mecanismo ou posicionamento que diferencia o produto de alternativas próximas ainda não foi definido.

## Operating Context

- Aplicação executada localmente e acessada pelo navegador.
- O fluxo financeiro abrange registros, vencimentos e pagamentos, contas e investimentos.
- A interface principal é em português.
- Este registro cobre o SFP Flask; o diretório `sa-saas/` é um subprojeto separado no mesmo repositório.

## Capabilities and Constraints

- Gerencia categorias, descrições de despesas, formas de pagamento, contas, transações e investimentos.
- Oferece dashboard, relatórios mensais e anuais, filtros e exportação JSON dos dados do usuário autenticado.
- Usa Flask, Jinja2, SQLAlchemy e Bootstrap local; SQLite é a configuração padrão, com outros bancos suportados pelo SQLAlchemy via `DATABASE_URL`.
- Isola os dados por usuário e associa transações e investimentos a contas.
- O SFP Flask é um monólito modular server-side; `app/routes.py` ainda concentra parte da lógica de apresentação e relatórios.

## Evidence on Hand

- O repositório contém capturas da interface em `Exibição/dashboard.png`, `Exibição/conta.png` e `Exibição/relatorio.png`.
- O README e os testes do projeto documentam funcionalidades e fluxos existentes; não há depoimentos ou métricas de resultado registrados.

## Product Principles

- Manter os registros financeiros de cada usuário separados.
- Ajudar o usuário a acompanhar contas, vencimentos, pagamentos, saldos e investimentos em um único fluxo.
- Preservar a consistência dos dados financeiros ao registrar e recalcular movimentações.
- Dar acesso a resumos e relatórios baseados nos registros do próprio usuário.

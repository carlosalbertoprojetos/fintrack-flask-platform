# SFP | Sistema de Finanças Pessoais



Sistema web de finanças pessoais construído em Flask, com foco em rastreabilidade financeira, isolamento de dados por usuário, operação local/offline e evolução arquitetural orientada a serviços.



Este repositório funciona como produto funcional e como portfólio técnico. Ele demonstra capacidade de transformar um problema real de domínio financeiro em uma aplicação utilizável, evoluir código legado com mais rigor arquitetural e aplicar estudos modernos em backend, qualidade de dados, IA aplicada e extensibilidade.



## Visão para recrutadores



O SFP foi estruturado para comunicar competência prática em frentes que costumam importar em times de produto e engenharia:



- modelagem de domínio além de um CRUD simples

- backend Python com Flask e SQLAlchemy

- refatoração de legado para uma arquitetura mais sustentável

- isolamento de dados por usuário e validação de ownership

- trilha auditável de eventos financeiros com ledger imutável

- operação local/offline com UX adaptada para ambiente Windows

- suíte de testes versionada e documentação de evolução arquitetural



O valor do projeto não está apenas na interface final, mas nas decisões técnicas que sustentam consistência, segurança, manutenção e possibilidade real de expansão.



## Leitura rápida



Para uma leitura de 30 segundos, este projeto evidencia:



- capacidade de construir um produto funcional em Flask sobre um domínio real

- capacidade de evoluir uma base legada para um desenho mais sustentável

- capacidade de modelar regras financeiras com rastreabilidade e consistência

- capacidade de isolar dados por usuário e endurecer fluxos críticos

- capacidade de aplicar estudos em IA, qualidade de dados e arquitetura de forma pragmática



## Resumo executivo



O sistema entrega hoje:



- autenticação com login, logout, cadastro, perfil e recuperação de senha

- dashboard financeiro com indicadores, gráficos e visão consolidada de receitas, despesas e saldo

- relatórios mensais, anuais e por forma de pagamento

- gestão de contas, categorias, despesas, formas de pagamento e tipos financeiros

- módulo de investimentos com aplicações, resgates, rendimentos e recálculo de saldo

- exportação lógica de dados por usuário

- inicialização local com launcher próprio e execução offline sem dependência obrigatória de CDN

- dados de demonstração para navegação do sistema



Na camada técnica, o projeto evoluiu para incorporar:



- ledger imutável por conta

- fechamento mensal com possibilidade de bloqueio de período

- simulação paralela de cenários

- camada de serviços para regras de negócio críticas

- rotas separadas por contexto funcional

- preparação para recursos de IA local e evolução para arquiteturas mais contextuais



## Casos de uso cobertos



- acompanhar receitas, despesas e saldo por conta

- analisar comportamento financeiro no dashboard e em relatórios

- controlar despesas por categoria, descrição e forma de pagamento

- registrar e reconciliar aplicações, resgates e rendimentos em investimentos

- exportar os dados do usuário autenticado para uso externo

- operar localmente, inclusive em ambientes sem internet



## Principais funcionalidades



### 1. Gestão financeira do dia a dia



- cadastro de contas com saldo inicial e saldo recalculável

- lançamentos de receitas e despesas

- categorização das transações

- vínculo com formas de pagamento e descrição da despesa

- controle de vencimento, pagamento, desconto e recorrência

- replicação de lançamentos para acelerar uso operacional



### 2. Dashboard gerencial



O dashboard foi pensado para leitura rápida do estado financeiro do usuário.



Ele reúne:



- totais consolidados do mês

- saldo mensal e saldo acumulado

- evolução financeira em janela de 12 meses

- receitas por categoria

- despesas por categoria

- visão resumida de investimentos

- lançamentos recentes e indicadores por conta



### 3. Relatórios financeiros



O sistema oferece relatórios úteis para análise e acompanhamento:



- relatório mensal

- relatório anual

- relatório por forma de pagamento

- relatório de descontos

- relatório consolidado de despesas por forma de pagamento

- exportação de dados em JSON por usuário autenticado



### 4. Módulo de investimentos



O módulo de investimentos vai além do cadastro básico.



Ele contempla:



- tipos de investimento por usuário

- criação de investimentos vinculados a contas

- aplicações, resgates e rendimentos

- histórico completo de movimentações

- edição e exclusão de movimentações

- recálculo de saldos do investimento

- consistência entre movimentação do investimento e impacto na conta de origem



### 5. Segurança funcional e isolamento de dados



O sistema foi endurecido para que cada usuário visualize e manipule apenas seu próprio escopo.



Isso inclui:



- categorias por usuário

- despesas por usuário

- formas de pagamento por usuário

- contas por usuário

- tipos de conta por usuário

- tipos de investimento por usuário

- transações e investimentos sempre filtrados pelo usuário autenticado

- validação de ownership antes de gravar ou editar relacionamentos



### 6. Operação local e offline



O projeto foi adaptado para funcionar bem em ambiente local, inclusive sem internet.



Foram implementados:



- assets críticos locais para CSS e JavaScript

- fallbacks para recursos antes dependentes de CDN

- launcher com `run.py` e `run.bat`

- abertura de navegador em janela gerenciada

- fechamento automático da janela do navegador ao desligar o sistema

- backup automático do banco no encerramento



## Diferenciais técnicos



### Ledger imutável como trilha auditável



Uma das evoluções mais relevantes do sistema foi a migração de uma lógica baseada apenas em mutação de saldo para uma abordagem com livro de eventos financeiros.



Isso trouxe ganhos concretos:



- rastreabilidade das alterações financeiras

- reconstrução de saldo por conta

- base para validação de integridade com hash chain

- menor risco de divergência silenciosa entre histórico e saldo atual



Componentes centrais:



- `services/ledger_service.py`

- `services/transaction_service.py`

- `services/investment_service.py`

- `app/models.py`

- `migrations/versions/d2f6e9b1c4a0_sfp_v3_ledger_and_ai_models.py`



### Fechamento mensal e consistência de período



O projeto passou a suportar fechamento mensal por conta e por usuário, com possibilidade de bloqueio do período.



Na prática isso permite:



- preservar períodos já consolidados

- impedir alterações em meses fechados

- gerar snapshots de saldo e totais do mês

- validar consistência entre ledger, saldo e fechamento



### Arquitetura orientada a serviços



As regras de negócio mais críticas foram desacopladas das rotas HTTP.



Hoje a base usa uma divisão mais clara:



- `app/` para app factory, modelos, formulários, rotas principais e templates

- `routes/` para blueprints especializados

- `services/` para regras de negócio, consistência, projeção e auditoria

- `migrations/` para evolução controlada de schema

- `tests/` para cobertura funcional e de serviços



Essa separação melhora manutenção, legibilidade e testabilidade.



### Observabilidade, segurança e operação



O projeto também incorpora cuidados normalmente ausentes em projetos acadêmicos simples:



- logs estruturados em JSON

- rate limiting básico de login em memória de processo

- suporte a `DATABASE_URL`

- configuração de cookies de sessão e remember-me

- backup automático com versionamento por trimestre

- reparo/migração de dados legados com problemas de encoding e escopo



## Tecnologias aplicadas



A lista abaixo foi mapeada diretamente do código e da configuração do projeto.



### Backend principal



- Python 3.10+

- Flask

- Flask-Login

- Flask-SQLAlchemy

- Flask-Migrate

- Flask-WTF

- Flask-Mail

- SQLAlchemy 2.x

- Alembic

- Jinja2

- itsdangerous

- Werkzeug



### Persistência e dados



- SQLite como banco local padrão

- suporte por variável de ambiente para `DATABASE_URL`

- compatibilidade de arquitetura para migração futura a PostgreSQL

- migrations versionadas em `migrations/`



### Frontend do sistema Flask



- Jinja2 Templates

- Bootstrap local

- JavaScript vanilla

- runtime local para gráficos offline em `app/static/js/chart-lite.js`

- CSS local de ícones e fallbacks para operação sem CDN



### Ferramentas de runtime e utilidades



- `python-dotenv` para configuração via ambiente

- `psutil` para apoio a shutdown/gerenciamento no Windows

- launcher em `run.py`, `run.bat` e scripts auxiliares em `sistema/`



### Qualidade e testes



- pytest

- suíte de testes versionada em `tests/`

- 50 casos de teste identificáveis no repositório

- cobertura de rotas, serviços, modelos, helpers e fluxo de execução



## IA aplicada no projeto



O SFP inclui uma camada local de inteligência aplicada ao domínio financeiro. O foco aqui não foi adicionar IA como vitrine, mas usar técnicas úteis para classificação, previsão e auditoria.



Serviços implementados:



- classificação local de transações por texto

  - `services/ai_classification_service.py`

- detecção de anomalias estatísticas

  - `services/anomaly_detection_service.py`

- projeção de fluxo de caixa e score de saúde financeira

  - `services/projection_service.py`

- verificação de integridade e qualidade dos dados financeiros

  - `services/data_quality_service.py`



Esse conjunto mostra dois resultados importantes dos estudos realizados:



- capacidade de traduzir conceitos de IA em serviços aplicáveis ao domínio

- preocupação com dados, contexto do usuário e extensibilidade antes de qualquer acoplamento com provedor externo



## Resultado dos estudos e evolução arquitetural



O projeto também materializa um ciclo de estudo técnico bem-sucedido, porque os aprendizados geraram artefatos concretos no código.



### O que os estudos produziram na prática



- evolução de uma base mais acoplada para uma estrutura orientada a serviços

- introdução de ledger imutável e fechamento mensal

- criação de entidades de simulação para cenários paralelos

- metadados de modelos locais por usuário

- melhoria de segurança funcional com isolamento por escopo

- documentação técnica de diagnóstico, proposta de estrutura, estratégia de migração e breaking changes



### Evidências no repositório



- `docs/sfp_v3/01_diagnostico_tecnico.md`

- `docs/sfp_v3/02_estrutura_proposta.md`

- `docs/sfp_v3/03_estrategia_migracao_backfill.md`

- `docs/sfp_v3/04_breaking_changes.md`

- `services/`

- `migrations/versions/d2f6e9b1c4a0_sfp_v3_ledger_and_ai_models.py`



### Leitura correta para recrutadores



O sucesso dos estudos não está em dizer que todo o projeto já virou uma plataforma enterprise pronta para escala global.



O sucesso está em mostrar que o estudo:



- alterou a arquitetura

- melhorou a qualidade do domínio

- gerou serviços executáveis

- reduziu acoplamento

- aumentou testabilidade

- deixou o produto mais preparado para crescer



## Desafios técnicos resolvidos



### 1. Evolução de um legado acoplado



O projeto partiu de uma base em que parte relevante das regras de negócio ainda estava concentrada em rotas e mutações diretas de saldo.



O trabalho realizado trouxe:



- extração de regras críticas para `services/`

- redução do acoplamento entre HTTP, persistência e domínio

- melhoria da clareza para manutenção e testes



### 2. Consistência financeira e trilha auditável



Em vez de depender apenas de saldo mutável em conta, o sistema passou a contar com ledger imutável e hash chain.



Isso permitiu:



- reconstrução de saldo por eventos

- validação de integridade

- menor risco de divergência histórica silenciosa



### 3. Isolamento real por usuário



Parte importante da evolução do sistema foi deixar de tratar cadastros auxiliares como globais e passar a escopá-los por usuário.



O resultado foi:



- consultas filtradas por `current_user`

- validação de ownership em serviços e rotas

- exportação lógica limitada ao usuário autenticado



### 4. Operação local/offline com experiência controlada



O sistema foi adaptado para um cenário de uso local em Windows, inclusive com execução sem internet.



Foram resolvidos pontos como:



- dependência anterior de CDN para frontend

- inicialização frágil via `python` no Windows

- fechamento coordenado do app com navegador gerenciado



### 5. Base preparada para evolução



Os estudos sobre IA aplicada, qualidade de dados e arquiteturas mais modernas não ficaram apenas na teoria.



Eles resultaram em:



- serviços locais de classificação, anomalia e projeção

- documentação de diagnóstico, estratégia e breaking changes

- workspace complementar `sa-saas/` para estudos de arquitetura moderna com TypeScript, Prisma e orquestração de IA



## Estrutura do repositório



```text

app/

  __init__.py

  forms.py

  middleware.py

  models.py

  routes.py

  static/

  templates/

routes/

  conta.py

  investimento.py

  tipo_conta.py

  tipo_investimento.py

  transactions.py

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

docs/

  sfp_v3/

scripts/

  seed_demo_2026.py

tests/

sistema/

run.py

run.bat

README.md

```



## Principais entidades de domínio



- `User`: autenticação, recuperação de senha e escopo de dados

- `Conta`: conta financeira com saldo inicial e saldo recalculável

- `Transaction`: receita ou despesa com datas, desconto e pagamento

- `Category`: categoria financeira escopada por usuário

- `Expense`: descrição de despesa vinculada a categoria

- `PaymentMethod`: forma de pagamento por usuário

- `Investimento`: ativo financeiro vinculado a tipo de investimento

- `MovimentacaoInvestimento`: aplicação, resgate ou rendimento

- `LedgerEntry`: evento financeiro auditável por conta

- `MonthlyClosure`: fechamento mensal com snapshot de saldos e totais

- `SimulationSession` e `SimulationLedgerEntry`: cenários paralelos de simulação

- `AIModelMetadata`: metadados de modelos locais por usuário



## Execução local



### Requisitos



- Python 3.10 ou superior

- Windows é o cenário mais preparado no estado atual do launcher

- acesso opcional à internet apenas para instalação inicial de dependências



### Instalação rápida no Windows



```powershell

py -3.10 -m venv venv

.\venv\Scripts\python.exe -m pip install -r requirements.txt

run.bat

```



### Execução direta



```powershell

.\venv\Scripts\python.exe run.py

<<<<<<< HEAD
=======
### **Transaction (Transação)**

- ID, data, valor, tipo, categoria, descrição
- Campos: due_date, payment_date, discount, paid
- Relacionamentos com usuário, conta, categoria, forma de pagamento

### **Category (Categoria)**

- ID, nome, tipo (receita/despesa), exclusive
- Ícones e cores personalizáveis

### **PaymentMethod (Forma de Pagamento)**

- ID, nome, is_active
- Dinheiro, PIX, cartões, etc.

### **Investimento (Investimento)**

- ID, tipo_investimento_id, data_abertura
- Relacionamento com movimentações

### **MovimentacaoInvestimento (Movimentação)**

- ID, investimento_id, data_movimentacao
- Campos: tipo_movimentacao, valor, saldo_anterior, saldo_atual
- Relacionamento com conta e usuário

### **TipoInvestimento (Tipo de Investimento)**

- ID, nome, descrição, ativo
- Relacionamento com investimentos

## Instalação e Configuração

### **Pré-requisitos**

- **Windows 10/11** ou **Linux** (Ubuntu, Debian, CentOS, etc.)
- **Python 3.10 ou superior** (será instalado automaticamente se necessário)
- **Conexão com internet** (para download de dependências)
- **Privilégios de administrador** (para instalação)

### **Instalação Automática (Recomendada)**

#### **Método 1: Instalador Corrigido (Windows)**

1. **Execute o Instalador:**
   ```bash
   # Duplo clique em:
   INSTALAR_SISTEMA_CORRIGIDO.bat
   ```

2. **O instalador fará automaticamente:**
   -  Verificar/instalar Python 3.10+ se necessário
   -  Criar diretório `C:\Financas_Pessoais`
   -  Copiar todos os arquivos do sistema (app, routes, migrations, etc.)
   -  Criar ambiente virtual Python
   -  Instalar todas as dependências (Flask, SQLAlchemy, etc.)
   -  Criar scripts de inicialização
   -  Criar atalho na área de trabalho
   -  Testar o sistema
   -  Iniciar o sistema automaticamente

#### **Método 2: Instalador Python (Windows/Linux)**

1. **Execute o Instalador Python:**
   ```bash
   python instalar_sistema.py
   ```

2. **Siga as instruções na tela:**
   - O sistema detectará automaticamente Windows ou Linux
   - Instalará Python se necessário
   - Criará ambiente virtual
   - Instalará todas as dependências
   - Criará atalho na área de trabalho

### **Instalação Manual (Desenvolvedores)**

1. **Clone o Repositório**
   ```bash
   git clone https://github.com/seu-usuario/financas_pessoais_flask.git
   cd financas_pessoais_flask
   ```

2. **Crie Ambiente Virtual**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale Dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute a Aplicação**
   ```bash
   python run.py
   ```

5. **Acesse o Sistema**
   - Abra o navegador em: `http://127.0.0.1:5000`
   - **Usuário:** admin
   - **Senha:** admin123

### **Primeiro Acesso**

Após a instalação:

1. **Acesse:** `http://127.0.0.1:5000`
2. **Login inicial:**
   - **Usuário:** admin
   - **Senha:** admin123
3. **Altere a senha** nas configurações do perfil
4. **Crie sua primeira conta bancária**
5. **Configure tipos de conta e investimento**

## Como Usar o Sistema

### **1. Primeiro Acesso**

1. Acesse `http://127.0.0.1:5000`
2. Clique em "Registrar" para criar sua conta
3. Preencha os dados (username, email, senha)
4. Após o registro, crie sua primeira conta bancária

### **2. Configuração Inicial**

1. **Criar Conta Bancária:**

   - Vá em "Contas" → "Nova Conta"
   - Defina nome, tipo e saldo inicial
   - Salve a conta

2. **Configurar Tipos de Conta:**

   - Vá em "Tipos de Conta" → "Novo Tipo"
   - Crie tipos como "Conta Corrente", "Poupança", etc.

3. **Configurar Tipos de Investimento:**
   - Vá em "Tipos de Investimento" → "Novo Tipo"
   - Crie tipos como "CDB", "Ações", "Fundos", etc.

### **3. Gestão Financeira Diária**

#### **Registrar Receitas:**

1. Clique em "Nova Transação"
2. Selecione tipo "Receita"
3. Escolha categoria (Salário, Freelance, etc.)
4. Informe valor e data de pagamento
5. Selecione forma de pagamento
6. Salve a transação

#### **Registrar Despesas:**

1. Clique em "Nova Transação"
2. Selecione tipo "Despesa"
3. Escolha categoria (Alimentação, Moradia, etc.)
4. Informe valor e data de vencimento
5. Adicione desconto se houver
6. Selecione forma de pagamento
7. Salve a transação

#### **Gerenciar Investimentos:**

1. Vá em "Investimentos"
2. Clique em "Novo Investimento"
3. Selecione o tipo de investimento
4. Registre movimentações:
   - **Aplicação**: Novo investimento
   - **Resgate**: Saque do investimento
   - **Rendimento**: Ganhos recebidos

### **4. Acompanhamento e Relatórios**

1. **Dashboard:** Visão geral do mês atual
2. **Relatórios:** Análises detalhadas por período
3. **Gráficos:** Visualização de dados financeiros
4. **Filtros:** Análise por conta, categoria, período

## Configurações Avançadas

### **Configuração de Email**

Edite o arquivo `config.py`:

```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'seu-email@gmail.com'
MAIL_PASSWORD = 'sua-senha'
>>>>>>> cbbf2a05602df940c745b4cf1d7c469ac041e8c4
```



### Execução sem abrir navegador



Útil para validação automatizada, CI ou execução em segundo plano:



```powershell

$env:SFP_NO_BROWSER = "1"

<<<<<<< HEAD
.\venv\Scripts\python.exe run.py
=======
4. **Banco de Dados Corrompido:**
   - Restaure do backup em `diretorio configurado por SFP_BACKUP_DIR (padrao: ~/Financas_Pessoais/backup)`
   - Ou delete `instance/financas.db` para recriar

5. **Porta 5000 Ocupada:**
   - Feche outros programas usando a porta

### **Erros Específicos Corrigidos**

6. **"No module named 'routes'"**
   - **Causa:** Diretório `routes` não foi copiado durante instalação
   - **Solução:** Use `INSTALAR_SISTEMA_CORRIGIDO.bat` (versão corrigida)
   - **Verificação:** Confirme que existe `C:\Financas_Pessoais\routes\`

7. **"log_message() got an unexpected keyword argument 'end'"**
   - **Causa:** Versão antiga do instalador com erro de função
   - **Solução:** Use a versão corrigida do `instalar_sistema.py`
   - **Status:**  **CORRIGIDO** na versão atual

8. **"Não é possível acessar esse site"**
   - **Causa:** Servidor Flask não iniciou corretamente
   - **Solução:** Verifique se o ambiente virtual está ativado
   - **Comando:** `call venv\Scripts\activate.bat && python run.py`

9. **"Ambiente virtual não está sendo ativado"**
   - **Causa:** Script de inicialização com problema
   - **Solução:** Use os scripts corrigidos com verificações robustas
   - **Verificação:** Script mostra "Ambiente virtual ativado com sucesso!"

### **Verificação de Instalação**

Para verificar se a instalação está correta:

```bash
# Verifique se todos os diretórios existem
dir C:\Financas_Pessoais
# Deve conter: app, routes, migrations, venv, run.py

# Teste o sistema
cd C:\Financas_Pessoais
call venv\Scripts\activate.bat
python -c "from app import create_app; print(' Sistema OK!')"
```

##  Distribuição do Sistema

### **Arquivos Necessários para Instalação**

Para distribuir o sistema, inclua os seguintes arquivos:
>>>>>>> cbbf2a05602df940c745b4cf1d7c469ac041e8c4

```



### Acesso local



- URL: `http://127.0.0.1:5000`

- login administrativo padrão: `admin`

- senha padrão: `admin123`

- usuário demo: `demo`

- senha demo: `demo123`



### Dados de demonstração



O repositório inclui um gerador de dados para navegação demonstrativa no período de 2026:



- `scripts/seed_demo_2026.py`



Exemplo:



```powershell

.\venv\Scripts\python.exe scripts\seed_demo_2026.py --username demo --email demo@sistema.com --password demo123

```



## Testes



A suíte de testes cobre fluxos relevantes do sistema:



- autenticação

- rotas principais e relatórios

- isolamento de dados por usuário

- ledger e detecção de adulteração

- fechamento mensal

- ciclo de vida de transações

- ciclo de vida de investimentos

- projeção, anomalias e qualidade de dados

- helpers de execução do launcher



Instale primeiro as dependências de desenvolvimento:



```powershell

.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt

```



Depois execute a suíte:



```powershell

.\venv\Scripts\python.exe -m pytest -q

```



## Material visual



Capturas do sistema disponíveis no repositório:



- `Exibição/dashboard.png`

- `Exibição/relatorio.png`

- `Exibição/relatorio2.png`

- `Exibição/conta.png`

- `Exibição/tiposconta.png`



## Workspace complementar de estudos modernos



O repositório também contém um workspace complementar em `sa-saas/`, separado do núcleo Flask, com foco em arquitetura moderna para produtos SaaS e IA:



- Next.js

- Node.js + TypeScript

- PostgreSQL

- Prisma

- abstração de provedores de IA

- versionamento e orquestração de prompts



Esse workspace não substitui o sistema Flask principal. Ele funciona como evidência adicional de estudo e experimentação em uma direção mais moderna de plataforma, mantendo o núcleo financeiro do SFP estável e utilizável.



## O que este projeto evidencia profissionalmente



### Capacidade de produto



- entendimento de um domínio financeiro real

- entrega de aplicação navegável e demonstrável

- preocupação com experiência operacional local



### Capacidade de engenharia



- refatoração progressiva de código legado

- modelagem financeira com mais rastreabilidade

- organização por camadas e serviços

- testes automatizados e migrações versionadas



### Capacidade de estudo aplicado



- uso disciplinado de Flask e extensões do ecossistema

- adoção de SQLAlchemy e Alembic para manter a base evolutiva

- aplicação pragmática de IA no contexto do produto

- documentação técnica que mostra diagnóstico, proposta e execução



## Status atual



O SFP está em um estágio sólido como portfólio técnico e base funcional de produto.



Hoje ele já demonstra:



- aplicação Flask funcional com domínio real

- operação local/offline

- rastreabilidade com ledger

- relatórios e dashboard

- investimentos com regras de consistência

- isolamento por usuário

- base preparada para novos ciclos de evolução



## Autor



**Carlos Alberto Medeiros**

<<<<<<< HEAD
=======
- Email: [carlosalbertoprojetos2020@gmail.com]
- WhatsApp: +55 (31) 98676-6866
- LinkedIn: [https://www.linkedin.com/in/carlos-alberto-medeiros-29aa6258/]

## Agradecimentos

- Comunidade Flask
- Desenvolvedores do Bootstrap
- Equipe do Chart.js
- Todos os contribuidores do projeto

---

## Suporte

Para suporte técnico ou dúvidas:

- Email: carlosalbertoprojetos2020@gmail.com
- WhatsApp: +55 (31) 98676-6866
- Issues: [GitHub Issues](https://github.com/seu-usuario/financas_pessoais_flask/issues)

**Versão:** 2.0.0  
**Última Atualização:** Janeiro 2025

##  Problema com Python 3.13?

Se você encontrar o erro:
```
AssertionError: Class <class 'sqlalchemy.sql.elements.SQLCoreOperations'> directly inherits TypingOnly
```

**Soluções:**

1. **Correção Automática**:
   ```bash
   python corrigir_sqlalchemy.py
   ```

2. **Solução Recomendada**: Instale Python 3.10.x:
   - Baixe em: https://www.python.org/downloads/
   - Desinstale Python 3.13
   - Instale Python 3.10.x

3. **Ver instruções detalhadas**: Leia o arquivo `SOLUCAO_PYTHON_313.md`
>>>>>>> cbbf2a05602df940c745b4cf1d7c469ac041e8c4


- LinkedIn: `https://www.linkedin.com/in/carlos-alberto-medeiros-29aa6258/`

- Email: `carlosalbertoprojetos2020@gmail.com`



## Fechamento



Se este repositório for lido como material de recrutamento técnico, a melhor síntese é esta:



- um sistema funcional de domínio real

- com decisões de engenharia coerentes

- sustentado por estudo aplicado e melhoria contínua

- e com sinais concretos de maturidade para evoluir além do escopo inicial

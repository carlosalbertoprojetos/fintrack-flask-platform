# Sistema de Finanças Pessoais Flask

## Visão Geral

O **Sistema de Finanças Pessoais Flask** é uma aplicação web completa desenvolvida em Python/Flask para gerenciamento financeiro pessoal. O sistema oferece uma interface moderna e intuitiva para controle de receitas, despesas, investimentos e relatórios financeiros detalhados.

## Funcionalidades Principais

### Gestão de Usuários

- **Registro e Login**: Sistema completo de autenticação com Flask-Login
- **Recuperação de Senha**: Sistema de reset de senha via email
- **Perfil do Usuário**: Edição de dados pessoais e alteração de senha
- **Sessões Seguras**: Configurações avançadas de cookies e sessões

### Gestão Financeira

#### **Contas Bancárias**

- Criação e gerenciamento de múltiplas contas
- Tipos de conta personalizáveis (Conta Corrente, Poupança, etc.)
- Saldo inicial e saldo atual calculado automaticamente
- Histórico completo de movimentações por conta

#### **Transações**

- **Receitas**: Registro de salários, freelances, investimentos, etc.
- **Despesas**: Controle de gastos com categorização automática
- **Descontos**: Sistema de desconto em despesas
- **Formas de Pagamento**: Dinheiro, PIX, cartões, boleto, etc.
- **Recorrência**: Transações recorrentes (diária, semanal, mensal)
- **Status de Pagamento**: Controle de transações pagas/pendentes
- **Datas**: Data de vencimento e data de pagamento separadas

#### **Categorias e Descrições**

- Categorias predefinidas (Salário, Alimentação, Moradia, etc.)
- Categorias personalizáveis com ícones e cores
- Descrições predefinidas para agilizar o cadastro
- Sistema de categorias exclusivas ou compartilhadas

### Sistema de Investimentos

#### **Tipos de Investimento**

- CDB, Ações, Fundos, Tesouro Direto, Poupança
- Tipos personalizáveis pelo usuário
- Descrições detalhadas para cada tipo

#### **Movimentações de Investimento**

- **Aplicações**: Registro de novos investimentos
- **Resgates**: Saques parciais ou totais
- **Rendimentos**: Registro de ganhos e dividendos
- **Saldo Atual**: Cálculo automático do saldo por investimento
- **Histórico Completo**: Todas as movimentações com datas e valores

#### **Controle de Saldo**

- Integração automática com contas bancárias
- Aplicações diminuem saldo da conta
- Resgates aumentam saldo da conta
- Rendimentos não afetam saldo da conta

### Dashboard e Relatórios

#### **Dashboard Principal**

- **Visão Geral**: Resumo financeiro do mês atual
- **Cards de Resumo**: Receitas, despesas, saldo do mês, saldo atual
- **Transações Pendentes**: Lista de transações não pagas
- **Investimentos Ativos**: Resumo dos investimentos por conta
- **Estatísticas**: Média diária, projeções, total de transações

#### **Gráficos Interativos**

- **Evolução Mensal**: Gráfico de linha dos últimos 6 meses
- **Receitas por Categoria**: Gráfico de pizza
- **Despesas por Categoria**: Gráfico de pizza
- **Comparativo**: Receitas vs Despesas vs Saldo

#### **Relatórios Detalhados**

- **Relatório Mensal**: Transações do mês com filtros
- **Relatório Anual**: Visão anual com evolução mensal
- **Relatório por Forma de Pagamento**: Análise por método de pagamento
- **Relatório de Descontos**: Transações com desconto aplicado
- **Filtros Avançados**: Por conta, categoria, período, status

### Funcionalidades Técnicas

#### **Sistema de Contas Múltiplas**

- Abas para alternar entre contas
- Filtros automáticos por conta selecionada
- Saldos independentes por conta
- Histórico separado por conta

#### **Backup Automático**

- Backup automático do banco de dados
- Localização: `C:\backup\bk_flask.db`
- Atualização automática após cada operação

#### **Compatibilidade de Navegadores**

- Middleware de compatibilidade
- Suporte a Chrome, Firefox, Edge
- Configurações otimizadas de cookies e sessões

#### **Sistema de Shutdown**

- Encerramento automático do servidor
- Fechamento de navegadores
- Limpeza de processos Python e CMD

## Tecnologias Utilizadas

### **Backend**

- **Python 3.8+**: Linguagem principal
- **Flask 2.3.3**: Framework web
- **SQLAlchemy 2.0.23**: ORM para banco de dados
- **Flask-Login 0.6.2**: Autenticação de usuários
- **Flask-Migrate 4.0.5**: Migrações de banco de dados
- **Flask-Mail 0.9.1**: Envio de emails
- **Flask-WTF 1.2.1**: Formulários web
- **WTForms 3.1.1**: Validação de formulários

### **Frontend**

- **Bootstrap 5.2.3**: Framework CSS
- **Chart.js 4.4.1**: Gráficos interativos
- **Font Awesome 6.5.0**: Ícones
- **Boxicons**: Ícones adicionais
- **Google Fonts**: Tipografia

### **Banco de Dados**

- **SQLite**: Banco de dados principal
- **Alembic**: Sistema de migrações

### **Ferramentas de Desenvolvimento**

- **PyInstaller**: Criação de executáveis
- **psutil**: Monitoramento de processos
- **email-validator**: Validação de emails

## Estrutura do Projeto

```
financas_pessoais_flask/
├── app/                         # Aplicação principal
│   ├── __init__.py              # Configuração da aplicação
│   ├── models.py                # Modelos de dados
│   ├── routes.py                # Rotas principais
│   ├── forms.py                 # Formulários
│   ├── middleware.py            # Middleware de compatibilidade
│   ├── static/                  # Arquivos estáticos
│   │   ├── css/                 # Estilos CSS
│   │   ├── js/                  # Scripts JavaScript
│   │   ├── img/                 # Imagens e favicon
│   │   └── vendor/              # Bibliotecas externas
│   └── templates/               # Templates HTML
│       ├── base.html            # Template base
│       ├── dashboard.html       # Dashboard principal
│       ├── login.html           # Página de login
│       ├── add_edit_transaction.html # Formulário de transações
│       └── ...                  # Outros templates
├── routes/                      # Módulos de rotas
│   ├── conta.py                 # Gestão de contas
│   ├── investimento.py          # Gestão de investimentos
│   ├── transactions.py          # Transações
│   ├── tipo_conta.py            # Tipos de conta
│   └── tipo_investimento.py     # Tipos de investimento
├── migrations/                  # Migrações do banco
├── instance/                    # Instância da aplicação
├── build/                       # Arquivos de build
├── dist/                        # Distribuição
├── venv/                        # Ambiente virtual
├── config.py                    # Configurações
├── run.py                       # Arquivo principal
├── requirements.txt             # Dependências
├── installer.py                 # Instalador automático
├── build_installer.bat          # Script de build
└── README.md                    # Este arquivo
```

## Modelos de Dados

### **User (Usuário)**

- ID, username, email, password_hash
- Relacionamento com transações e contas

### **Conta (Conta Bancária)**

- ID, nome, tipo_id, saldo_inicial, saldo_atual
- Relacionamento com usuário e transações

### **TipoConta (Tipo de Conta)**

- ID, nome, descrição, ativo
- Relacionamento com contas

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
- **Python 3.8 ou superior** (será instalado automaticamente se necessário)
- **Conexão com internet** (para download de dependências)
- **Privilégios de administrador** (para instalação)

### **🚀 Instalação Automática (Recomendada)**

#### **Método 1: Instalador Corrigido (Windows)**

1. **Execute o Instalador:**
   ```bash
   # Duplo clique em:
   INSTALAR_SISTEMA_CORRIGIDO.bat
   ```

2. **O instalador fará automaticamente:**
   - ✅ Verificar/instalar Python 3.8+ se necessário
   - ✅ Criar diretório `C:\Financas_Pessoais`
   - ✅ Copiar todos os arquivos do sistema (app, routes, migrations, etc.)
   - ✅ Criar ambiente virtual Python
   - ✅ Instalar todas as dependências (Flask, SQLAlchemy, etc.)
   - ✅ Criar scripts de inicialização
   - ✅ Criar atalho na área de trabalho
   - ✅ Testar o sistema
   - ✅ Iniciar o sistema automaticamente

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

### **📋 Instalação Manual (Desenvolvedores)**

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

### **🎯 Primeiro Acesso**

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
```

### **Configuração de Banco de Dados**

Para usar PostgreSQL ou MySQL:

```python
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/financas'
```

### **Configurações de Segurança**

```python
SECRET_KEY = 'sua-chave-secreta-muito-forte'
SESSION_COOKIE_SECURE = True  # Para HTTPS
```

## Solução de Problemas

### **Problemas Comuns**

1. **Erro de Permissão:**
   - Execute como administrador
   - Verifique permissões da pasta de instalação

2. **Python não Encontrado:**
   - Instale Python 3.8+ do site oficial
   - Adicione Python ao PATH do sistema

3. **Dependências não Instalam:**
   - Verifique conexão com internet
   - Execute: `pip install --upgrade pip`
   - Tente: `pip install -r requirements.txt --no-cache-dir`

4. **Banco de Dados Corrompido:**
   - Restaure do backup em `C:\backup\bk_flask.db`
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
   - **Status:** ✅ **CORRIGIDO** na versão atual

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
python -c "from app import create_app; print('✅ Sistema OK!')"
```

## 📦 Distribuição do Sistema

### **Arquivos Necessários para Instalação**

Para distribuir o sistema, inclua os seguintes arquivos:

```
financas_pessoais_flask/
├── 📁 app/                    # Aplicação Flask principal
├── 📁 routes/                 # Módulos de rotas (CORRIGIDO)
├── 📁 migrations/             # Migrações do banco de dados
├── 📄 instalar_sistema.py     # Instalador Python (CORRIGIDO)
├── 📄 INSTALAR_SISTEMA_CORRIGIDO.bat  # Instalador Windows (RECOMENDADO)
├── 📄 run.py                  # Servidor Flask
├── 📄 config.py               # Configurações
├── 📄 requirements.txt        # Dependências Python
├── 📄 iconFP.png             # Ícone do sistema
└── 📄 README.md              # Este arquivo
```

### **Instruções para o Usuário Final**

1. **Copie todos os arquivos** para uma pasta no computador
2. **Execute:** `INSTALAR_SISTEMA_CORRIGIDO.bat` (Windows)
3. **Ou execute:** `python instalar_sistema.py` (Windows/Linux)
4. **Aguarde** a instalação automática
5. **Acesse:** http://127.0.0.1:5000
6. **Login:** admin / admin123

### **Logs e Debug**

- Logs de instalação: `%USERPROFILE%\financas_pessoais_install.log`
- Logs da aplicação: Console do terminal
- Modo debug: `app.config['DEBUG'] = True`

## Backup e Restauração

### **Backup Automático**

- Localização: `C:\backup\bk_flask.db`
- Atualização: Automática após cada operação
- Frequência: A cada transação salva

### **Backup Manual**

```bash
# Copie o arquivo
copy instance\financas.db backup\financas_backup_YYYYMMDD.db
```

### **Restauração**

```bash
# Restaure do backup
copy backup\bk_flask.db instance\financas.db
```

## Desenvolvimento

### **Estrutura de Desenvolvimento**

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/financas_pessoais_flask.git

# Crie ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instale dependências de desenvolvimento
pip install -r requirements.txt
pip install pytest flask-testing

# Execute em modo desenvolvimento
python run.py
```

### **Adicionando Novas Funcionalidades**

1. Crie novos modelos em `app/models.py`
2. Adicione formulários em `app/forms.py`
3. Crie rotas em `routes/` ou `app/routes.py`
4. Adicione templates em `app/templates/`
5. Execute migrações: `flask db migrate -m "Descrição"`
6. Aplique migrações: `flask db upgrade`

### **Testes**

```bash
# Execute testes
python -m pytest tests/

# Teste específico
python -m pytest tests/test_models.py
```

## Build e Distribuição

### **Criar Executável**

```bash
# Execute o script de build
build_installer.bat

# Ou manualmente
pyinstaller installer_advanced.spec
```

### **Distribuição**

- O executável será criado em `dist/Instalar_Financas_Pessoais_Avancado/`
- Inclui todas as dependências
- Instalação automática em `C:\Financas_Pessoais`

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## Desenvolvedor

**Carlos Alberto Medeiros**

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

## ⚠️ Problema com Python 3.13?

Se você encontrar o erro:
```
AssertionError: Class <class 'sqlalchemy.sql.elements.SQLCoreOperations'> directly inherits TypingOnly
```

**Soluções:**

1. **Correção Automática**:
   ```bash
   python corrigir_sqlalchemy.py
   ```

2. **Solução Recomendada**: Instale Python 3.11 ou 3.12:
   - Baixe em: https://www.python.org/downloads/
   - Desinstale Python 3.13
   - Instale Python 3.11 ou 3.12

3. **Ver instruções detalhadas**: Leia o arquivo `SOLUCAO_PYTHON_313.md`

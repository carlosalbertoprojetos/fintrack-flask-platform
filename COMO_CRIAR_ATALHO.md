# Como Criar Atalho na Área de Trabalho

## Método 1: Usando o Script Batch (Recomendado)

### Passo 1: Copiar o Script para a Área de Trabalho

1. Copie o arquivo `Iniciar_Sistema.bat` para sua área de trabalho
2. Ou crie um atalho do arquivo na área de trabalho

### Passo 2: Configurar o Atalho (Opcional)

1. Clique com o botão direito no arquivo `Iniciar_Sistema.bat` na área de trabalho
2. Selecione "Propriedades"
3. Na aba "Atalho", você pode:
   - Alterar o ícone (clique em "Alterar ícone...")
   - Definir uma tecla de atalho (ex: Ctrl+Alt+S)
   - Executar como administrador (se necessário)

### Passo 3: Usar o Atalho

1. Dê um duplo clique no arquivo `Iniciar_Sistema.bat`
2. O sistema irá:
   - Ativar o ambiente virtual automaticamente
   - Iniciar o servidor Flask
   - Abrir o navegador na tela de login

## Método 2: Criar Atalho Direto do Python

### Passo 1: Criar Novo Atalho

1. Clique com o botão direito na área de trabalho
2. Selecione "Novo" → "Atalho"

### Passo 2: Configurar o Comando

Cole o seguinte comando (ajuste o caminho se necessário):

```
cmd /c "cd /d C:\PROJETOS\Flask\SFP_alfa && call venv\Scripts\activate.bat && python run.py"
```

Ou para manter a janela aberta após encerrar:

```
cmd /k "cd /d C:\PROJETOS\Flask\SFP_alfa && call venv\Scripts\activate.bat && python run.py"
```

### Passo 3: Nomear o Atalho

Dê um nome como "Sistema de Finanças Pessoais"

### Passo 4: Alterar Ícone (Opcional)

1. Clique com o botão direito no atalho criado
2. Selecione "Propriedades"
3. Clique em "Alterar ícone..."
4. Escolha um ícone ou navegue até um arquivo .ico

## Método 3: Usando PowerShell (Avançado)

Se preferir usar PowerShell:

1. Copie o arquivo `Iniciar_Sistema.ps1` para a área de trabalho
2. Clique com o botão direito → "Executar com PowerShell"
3. Se aparecer erro de política de execução, execute no PowerShell como administrador:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## Solução de Problemas

### Erro: "Diretório do projeto não encontrado"

- Verifique se o caminho no script está correto
- Edite o arquivo `.bat` e ajuste o caminho `C:\PROJETOS\Flask\SFP_alfa` para o caminho real do seu projeto

### Erro: "Virtualenv não encontrado"

- Certifique-se de que o ambiente virtual está criado na pasta `venv`
- Se necessário, crie novamente: `python -m venv venv`

### O navegador não abre automaticamente

- O sistema tentará abrir automaticamente após 2 segundos
- Se não abrir, acesse manualmente: `http://127.0.0.1:5000/auth/login`

### Janela fecha imediatamente

- Use `cmd /k` ao invés de `cmd /c` para manter a janela aberta
- Ou edite o script e adicione `pause` no final

## Personalização

### Alterar Porta do Servidor

Edite o arquivo `run.py` e altere a linha:
```python
app.run(host='127.0.0.1', port=5000, ...)
```

### Alterar URL de Abertura

Edite o arquivo `run.py` na função `open_browser()` e altere:
```python
webbrowser.open('http://127.0.0.1:5000/auth/login')
```

## Dicas

- Mantenha a janela do terminal aberta enquanto usar o sistema
- Para encerrar o sistema, pressione `Ctrl+C` na janela do terminal
- Ou use o botão "Encerrar Sistema" na interface web


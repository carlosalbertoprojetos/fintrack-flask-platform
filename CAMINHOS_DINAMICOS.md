# Sistema de Finanças Pessoais - Caminhos Dinâmicos

## Resumo das Mudanças

Todos os caminhos do sistema foram atualizados para serem **dinâmicos** e apontarem para o diretório do **usuário LOCAL** do sistema onde está sendo instalado, em vez de usar caminhos fixos como `C:\Financas_Pessoais` ou procurar usuários de outros sistemas operacionais.

## Principais Alterações

### 1. Diretório de Instalação
- **Antes**: `C:\Financas_Pessoais` (fixo)
- **Agora**: `%USERPROFILE%\Financas_Pessoais` (dinâmico)
- **Detecção**: Usa `getpass.getuser()` e `os.environ.get('USERPROFILE')` para detectar o usuário LOCAL

### 2. Arquivos Modificados

#### `instalar_sistema.py`
- Diretório de instalação agora usa `Path.home() / "Financas_Pessoais"`
- Detecta automaticamente o usuário LOCAL do sistema usando `getpass.getuser()`
- Usa `os.environ.get('USERPROFILE')` para garantir compatibilidade Windows

#### `INSTALAR.bat`
- Variável `INSTALL_DIR` definida como `%USERPROFILE%\Financas_Pessoais`
- Todos os caminhos hardcoded substituídos pela variável

#### `criar_atalho_admin.bat`
- Caminhos atualizados para usar `%USERPROFILE%\Financas_Pessoais`
- Detecta automaticamente a área de trabalho do usuário

#### `criar_atalho_desktop_final.bat`
- Caminhos atualizados para usar `%USERPROFILE%\Financas_Pessoais`

#### `criar_atalho_desktop.py`
- Função `create_desktop_shortcut()` atualizada para usar caminhos dinâmicos
- Detecta automaticamente o diretório do usuário e área de trabalho

#### `start_flask.bat`
- Verifica primeiro o diretório do usuário antes de usar o diretório atual
- Fallback para o diretório atual se não encontrar no diretório do usuário

#### `config.py`
- Função `get_user_install_dir()` para obter diretório dinâmico
- Base de dados e outros arquivos agora apontam para o diretório do usuário

### 3. Novos Arquivos

#### `path_config.py`
- Configuração centralizada de todos os caminhos
- Funções para obter caminhos dinâmicos baseados no usuário LOCAL
- Detecção automática de área de trabalho usando PowerShell
- Suporte a Windows, Linux e macOS
- Usa `getpass.getuser()` para detectar usuário atual

#### `exemplo_caminhos_dinamicos.py`
- Script de demonstração das funcionalidades
- Exemplos de uso dos caminhos dinâmicos
- Mostra informações do usuário atual do sistema

#### `testar_usuario_local.py`
- Script de teste para verificar detecção de usuário local
- Testa compatibilidade em diferentes computadores
- Verifica se todas as funções estão funcionando corretamente

## Vantagens das Mudanças

### ✅ Compatibilidade Universal
- Funciona em QUALQUER computador Windows automaticamente
- Detecta o usuário LOCAL do sistema onde está instalando
- Não requer privilégios de administrador
- Compatível com diferentes configurações de usuário

### ✅ Detecção Automática de Usuário Local
- Usa `getpass.getuser()` para detectar o usuário atual do sistema
- Usa `os.environ.get('USERPROFILE')` para compatibilidade Windows
- Detecta automaticamente o diretório do usuário LOCAL
- Identifica a área de trabalho (OneDrive, Desktop tradicional, etc.)
- Suporte a múltiplos idiomas e configurações

### ✅ Segurança
- Instala no diretório do usuário logado
- Não interfere com outros usuários do sistema
- Permissões adequadas para cada usuário

### ✅ Flexibilidade
- Fácil de manter e atualizar
- Configuração centralizada
- Fallbacks para diferentes cenários

## Como Usar

### Testar Detecção de Usuário
```bash
python testar_usuario_local.py
```

### Verificar Caminhos
```bash
python exemplo_caminhos_dinamicos.py
```

### Instalação Normal
```bash
python instalar_sistema.py
```

### Usar Programaticamente
```python
from path_config import get_user_install_directory
import getpass

# Detecta automaticamente o usuário atual do sistema
current_user = getpass.getuser()
install_dir = get_user_install_directory()
print(f"Usuário: {current_user}")
print(f"Sistema instalado em: {install_dir}")
```

## Estrutura de Diretórios

```
%USERPROFILE%\Financas_Pessoais\
├── app\
├── routes\
├── migrations\
├── instance\
├── run.py
├── config.py
├── path_config.py
├── requirements.txt
├── iconFP.ico
├── iconFP.png
├── start_flask.bat
├── executar_sistema.bat
└── criar_atalho_desktop.py
```

## Detecção de Área de Trabalho

O sistema detecta automaticamente a área de trabalho em diferentes cenários:

1. **OneDrive** (mais comum no Windows 10/11)
   - `%USERPROFILE%\OneDrive\Área de Trabalho`
   - `%USERPROFILE%\OneDrive\Desktop`

2. **Área de Trabalho Tradicional**
   - `%USERPROFILE%\Área de Trabalho`
   - `%USERPROFILE%\Desktop`

3. **PowerShell Detection**
   - Usa `[Environment]::GetFolderPath('Desktop')`

4. **Fallback**
   - `%USERPROFILE%\Desktop` como último recurso

## Compatibilidade

- ✅ Windows 10/11
- ✅ Diferentes idiomas do sistema
- ✅ OneDrive configurado ou não
- ✅ Usuários com privilégios limitados
- ✅ Múltiplos usuários no mesmo computador

## Troubleshooting

### Problema: Atalho não é criado
**Solução**: Execute `criar_atalho_desktop.py` manualmente
```bash
cd %USERPROFILE%\Financas_Pessoais
python criar_atalho_desktop.py
```

### Problema: Sistema não inicia
**Solução**: Verifique se está no diretório correto
```bash
cd %USERPROFILE%\Financas_Pessoais
python run.py
```

### Problema: Banco de dados não encontrado
**Solução**: Reinstale o sistema ou inicialize o banco
```bash
cd %USERPROFILE%\Financas_Pessoais
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

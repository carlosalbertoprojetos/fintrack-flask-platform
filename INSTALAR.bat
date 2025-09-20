@echo off
title Finanças Pessoais - Instalador Corrigido
color 0A
echo.
echo ===============================================
echo    Finanças Pessoais v2.0.0
echo    Instalador Corrigido
echo ===============================================
echo.

REM Define o diretório do script
cd /d "%~dp0"

REM Verifica se Python está instalado
echo [1/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python não encontrado!
    echo.
    echo 📥 Por favor, instale Python 3.8 ou superior:
    echo    https://www.python.org/downloads/
    echo.
    echo ⚠️  Após instalar Python, execute este arquivo novamente.
    pause
    exit /b 1
)
echo ✅ Python encontrado!

REM Verifica se os arquivos necessários existem
echo [2/5] Verificando arquivos...
if not exist "instalar_sistema.py" (
    echo ❌ ERRO: Arquivo instalar_sistema.py não encontrado!
    pause
    exit /b 1
)
if not exist "routes" (
    echo ❌ ERRO: Diretório routes não encontrado!
    pause
    exit /b 1
)
if not exist "app" (
    echo ❌ ERRO: Diretório app não encontrado!
    pause
    exit /b 1
)
echo ✅ Todos os arquivos encontrados!

REM Executa a instalação
echo [3/5] Executando instalação...
echo.
echo ===============================================
echo    INSTALAÇÃO AUTOMÁTICA
echo ===============================================
echo.
python instalar_sistema.py

if errorlevel 1 (
    echo.
    echo ❌ ERRO na instalação!
    echo 🔧 Verifique as mensagens acima para mais detalhes.
    pause
    exit /b 1
)

echo.
echo ✅ Instalação concluída com sucesso!
echo.

REM Verifica se o diretório de instalação existe
echo [4/5] Verificando instalação...
set "INSTALL_DIR=%USERPROFILE%\Financas_Pessoais"
if not exist "%INSTALL_DIR%" (
    echo ❌ ERRO: Sistema não foi instalado corretamente!
    echo 🔄 Execute a instalação novamente.
    pause
    exit /b 1
)

REM Verifica se o diretório routes foi copiado
if not exist "%INSTALL_DIR%\routes" (
    echo ❌ ERRO: Diretório routes não foi copiado!
    echo 🔄 Execute a instalação novamente.
    pause
    exit /b 1
)

echo ✅ Sistema instalado com sucesso!
echo.

REM Testa o sistema
echo [5/6] Testando sistema...
cd /d "%INSTALL_DIR%"
python -c "import sys; sys.path.append('.'); from app import create_app; print('✅ Sistema funcionando!')" 2>nul
if errorlevel 1 (
    echo ⚠️  AVISO: Sistema instalado mas pode ter problemas de importação
    echo 🔧 Execute manualmente para verificar
) else (
    echo ✅ Sistema testado e funcionando!
)

echo.
echo [6/6] Criando atalho na área de trabalho...

REM Verificar se está executando como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo 🔧 Executando como administrador - usando script especial...
    cd /d "%~dp0"
    call criar_atalho_admin.bat
) else (
    echo 👤 Executando como usuário normal...
    cd /d "%INSTALL_DIR%"
    python criar_atalho_desktop.py
    if errorlevel 1 (
        echo ⚠️  AVISO: Erro ao criar atalho automaticamente
        echo 🔧 Criando atalho manual...
        powershell -Command "& { $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\OneDrive\Área de Trabalho\Financas Pessoais.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\executar_sistema.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Sistema de Financas Pessoais v2.0.0'; $Shortcut.IconLocation = '%INSTALL_DIR%\iconFP.ico'; $Shortcut.Save(); Write-Host 'Atalho criado com sucesso!' }"
    ) else (
        echo ✅ Atalho criado com sucesso!
    )
)

echo.
echo ===============================================
echo    INSTALAÇÃO CONCLUÍDA!
echo ===============================================
echo.
echo 🎉 O sistema foi instalado com sucesso!
echo.
echo 📍 Localização: %INSTALL_DIR%
echo 🌐 Acesse: http://127.0.0.1:5000
echo 👤 Usuário: admin
echo 🔑 Senha: admin123
echo.
echo 📋 Para usar o sistema:
echo    1. Use o atalho na área de trabalho
echo    2. Ou execute: python run.py
echo.
pause

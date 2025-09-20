@echo off
title Criando Atalho na Area de Trabalho
color 0A
echo.
echo ================================================
echo    CRIANDO ATALHO NA AREA DE TRABALHO
echo ================================================
echo.

REM Definir caminhos no diretório do usuário logado
set "INSTALL_DIR=%USERPROFILE%\Financas_Pessoais"
set "ICON_PATH=%USERPROFILE%\Financas_Pessoais\iconFP.ico"

echo [1/3] Verificando diretorios...
if not exist "%INSTALL_DIR%" (
    echo ERRO: Diretorio de instalacao nao encontrado!
    echo Execute a instalacao primeiro.
    pause
    exit /b 1
)

echo OK: Diretorio de instalacao encontrado

echo.
echo [2/3] Criando script de execucao...

REM Criar script batch de execucao
set "BATCH_PATH=%INSTALL_DIR%\executar_sistema.bat"
(
echo @echo off
echo title Financas Pessoais v2.0.0
echo color 0A
echo echo.
echo echo ================================================
echo echo    FINANCAS PESSOAIS v2.0.0
echo echo ================================================
echo echo.
echo echo Iniciando sistema...
echo echo.
echo.
echo cd /d "%INSTALL_DIR%"
echo.
echo REM Verificar se o Python esta funcionando
echo python --version ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo [ERRO] Python nao encontrado!
echo     echo Instale Python 3.8 ou superior.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Iniciar o sistema
echo echo Iniciando servidor Flask...
echo echo.
echo echo Acesse: http://127.0.0.1:5000
echo echo Usuario: admin
echo echo Senha: admin123
echo echo.
echo echo Pressione Ctrl+C para parar o servidor
echo echo.
echo.
echo python run.py
echo.
echo echo.
echo echo Sistema encerrado.
echo pause
) > "%BATCH_PATH%"

if exist "%BATCH_PATH%" (
    echo OK: Script de execucao criado
) else (
    echo ERRO: Nao foi possivel criar script de execucao
    pause
    exit /b 1
)

echo.
echo [3/3] Criando atalho na area de trabalho...

REM Obter caminho da area de trabalho usando PowerShell
for /f "tokens=*" %%i in ('powershell -Command "[Environment]::GetFolderPath('Desktop')"') do set "DESKTOP=%%i"

echo Area de trabalho: %DESKTOP%

REM Criar atalho usando PowerShell
set "SHORTCUT_PATH=%DESKTOP%\Financas Pessoais.lnk"

echo Criando atalho: %SHORTCUT_PATH%

powershell -Command "& { $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%BATCH_PATH%'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Sistema de Financas Pessoais v2.0.0'; if (Test-Path '%ICON_PATH%') { $Shortcut.IconLocation = '%ICON_PATH%' }; $Shortcut.Save(); Write-Host 'Atalho criado com sucesso!' }"

echo.
echo Verificando se o atalho foi criado...

if exist "%SHORTCUT_PATH%" (
    echo OK: Atalho criado com sucesso!
    echo    Localizacao: %SHORTCUT_PATH%
    if exist "%ICON_PATH%" (
        echo    Icone: %ICON_PATH%
    )
) else (
    echo AVISO: Atalho .lnk nao foi criado, criando arquivo .bat...
    
    REM Método alternativo: criar arquivo .bat na área de trabalho
    set "ALT_SHORTCUT=%DESKTOP%\Financas Pessoais.bat"
    (
        echo @echo off
        echo cd /d "%INSTALL_DIR%"
        echo python run.py
        echo pause
    ) > "%ALT_SHORTCUT%"
    
    if exist "%ALT_SHORTCUT%" (
        echo OK: Atalho alternativo criado: %ALT_SHORTCUT%
    ) else (
        echo ERRO: Nao foi possivel criar atalho alternativo
        echo.
        echo Solucao manual:
        echo 1. Navegue ate: %INSTALL_DIR%
        echo 2. Execute: executar_sistema.bat
    )
)

echo.
echo ================================================
echo    ATALHO CRIADO COM SUCESSO!
echo ================================================
echo.
echo O atalho foi criado na sua area de trabalho!
echo.
echo Para usar o sistema:
echo    1. Clique duas vezes no atalho "Financas Pessoais"
echo    2. Ou execute: %BATCH_PATH%
echo.
echo Apos iniciar, acesse: http://127.0.0.1:5000
echo Usuario: admin
echo Senha: admin123
echo.
pause



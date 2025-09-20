@echo off
title Criando Atalho - Modo Administrador
color 0A
echo.
echo ================================================
echo    CRIANDO ATALHO NA AREA DE TRABALHO
echo    Modo Administrador
echo ================================================
echo.

REM Definir caminhos no diretório do usuário logado
set "INSTALL_DIR=%USERPROFILE%\Financas_Pessoais"
set "ICON_PATH=%USERPROFILE%\Financas_Pessoais\iconFP.ico"

echo [1/4] Verificando diretorios...
if not exist "%INSTALL_DIR%" (
    echo ERRO: Diretorio de instalacao nao encontrado!
    echo Execute a instalacao primeiro.
    pause
    exit /b 1
)

echo OK: Diretorio de instalacao encontrado

echo.
echo [2/4] Criando script de execucao...

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
echo cd /d "%INSTALL_DIR%"
echo echo.
echo echo Iniciando servidor Flask...
echo echo.
echo echo Acesse: http://127.0.0.1:5000
echo echo Usuario: admin
echo echo Senha: admin123
echo echo.
echo echo Abrindo navegador automaticamente...
echo start http://127.0.0.1:5000
echo echo.
echo echo Pressione Ctrl+C para parar o servidor
echo echo.
echo python run.py
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
echo [3/4] Detectando area de trabalho do usuario atual...

REM Usar PowerShell para obter o caminho correto da area de trabalho
for /f "tokens=*" %%i in ('powershell -Command "[Environment]::GetFolderPath('Desktop')"') do set "DESKTOP_PATH=%%i"
echo Area de trabalho detectada: %DESKTOP_PATH%

REM Verificar se o caminho existe
if not exist "%DESKTOP_PATH%" (
    echo AVISO: Caminho nao existe, tentando alternativas...
    
    REM Tentar OneDrive
    set "ONEDRIVE_PATH=%USERPROFILE%\OneDrive\Área de Trabalho"
    if exist "%ONEDRIVE_PATH%" (
        set "DESKTOP_PATH=%ONEDRIVE_PATH%"
        echo Usando OneDrive: %DESKTOP_PATH%
    ) else (
        REM Fallback para Desktop tradicional
        set "DESKTOP_PATH=%USERPROFILE%\Desktop"
        echo Usando fallback: %DESKTOP_PATH%
    )
)

:create_shortcut
echo.
echo [4/4] Criando atalho na area de trabalho...
echo Caminho: %DESKTOP_PATH%

set "SHORTCUT_PATH=%DESKTOP_PATH%\Financas Pessoais.lnk"

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
    set "ALT_SHORTCUT=%DESKTOP_PATH%\Financas Pessoais.bat"
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
echo O atalho foi criado na area de trabalho!
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

@echo off
REM ============================================================
REM Script para iniciar o Sistema de Finanças Pessoais
REM ============================================================

title Sistema de Finanças Pessoais

REM Obter o diretório onde o script está localizado
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%"

REM Se o script estiver na área de trabalho, tentar encontrar o projeto
if "%SCRIPT_DIR:~-1%"=="\" set "PROJECT_DIR=%SCRIPT_DIR:~0,-1%"
if not exist "%PROJECT_DIR%\venv\Scripts\activate.bat" (
    REM Tentar caminho padrão
    set "PROJECT_DIR=C:\PROJETOS\Flask\SFP_alfa"
)

REM Mudar para o diretório do projeto
cd /d "%PROJECT_DIR%"

REM Verificar se o diretório existe
if not exist "%PROJECT_DIR%" (
    echo [ERRO] Diretório do projeto não encontrado!
    echo [INFO] Caminho tentado: %PROJECT_DIR%
    echo [INFO] Por favor, edite o script e ajuste o caminho do projeto
    pause
    exit /b 1
)

REM Verificar se o virtualenv existe
if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] Virtualenv não encontrado!
    echo [INFO] Execute: python -m venv venv
    pause
    exit /b 1
)

echo ============================================================
echo   INICIANDO SISTEMA DE FINANÇAS PESSOAIS
echo ============================================================
echo.

REM Ativar virtualenv
echo [INFO] Ativando ambiente virtual...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo [ERRO] Falha ao ativar o ambiente virtual!
    pause
    exit /b 1
)

echo [OK] Ambiente virtual ativado
echo.

REM Verificar se Python está disponível
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não encontrado no ambiente virtual!
    pause
    exit /b 1
)

echo [INFO] Iniciando servidor Flask...
echo [INFO] O navegador será aberto automaticamente em alguns segundos...
echo [INFO] A janela será minimizada após o navegador abrir...
echo.
echo ============================================================
echo   Para encerrar o sistema, pressione Ctrl+C
echo ============================================================
echo.

REM Iniciar script VBScript para minimizar janela após 7 segundos
if exist "minimize_window.vbs" (
    start /min wscript.exe minimize_window.vbs
)

REM Executar o script Python
python run.py

REM Se o script terminar, manter a janela aberta para ver erros
if errorlevel 1 (
    echo.
    echo [ERRO] O sistema foi encerrado com erros!
    echo.
    pause
)


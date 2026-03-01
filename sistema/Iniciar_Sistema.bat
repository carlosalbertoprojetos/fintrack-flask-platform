@echo off
setlocal EnableExtensions
REM ============================================================
REM Script para iniciar o Sistema de Financas Pessoais
REM ============================================================

title Sistema de Financas Pessoais

REM Diretorio do projeto (pai de sistema\)
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_DIR=%%~fI"

cd /d "%PROJECT_DIR%" 2>nul
if errorlevel 1 (
    echo [ERRO] Diretorio do projeto nao encontrado!
    echo [INFO] Caminho tentado: %PROJECT_DIR%
    pause
    exit /b 1
)

if not exist "%PROJECT_DIR%\run.py" (
    echo [ERRO] Arquivo run.py nao encontrado no projeto!
    echo [INFO] Caminho: %PROJECT_DIR%
    pause
    exit /b 1
)

REM Detectar base de dados legada do projeto (prioridade para usuarios existentes)
set "DB_FILE="
if exist "%PROJECT_DIR%\instance\financas.db" set "DB_FILE=%PROJECT_DIR%\instance\financas.db"
if not defined DB_FILE if exist "%PROJECT_DIR%\app.db" set "DB_FILE=%PROJECT_DIR%\app.db"
if defined DB_FILE (
    set "DATABASE_URL=sqlite:///%DB_FILE%"
    echo [INFO] Banco de dados definido para: %DB_FILE%
)

REM Detectar venv (.venv ou venv)
set "VENV_DIR="
if exist "%PROJECT_DIR%\venv\Scripts\python.exe" set "VENV_DIR=%PROJECT_DIR%\venv"
if not defined VENV_DIR if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" set "VENV_DIR=%PROJECT_DIR%\.venv"

if not defined VENV_DIR (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo [INFO] Esperado: venv\Scripts\python.exe ou .venv\Scripts\python.exe
    echo [INFO] Execute com Python 3.10+: py -3 -m venv venv
    pause
    exit /b 1
)

set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "ACTIVATE_BAT=%VENV_DIR%\Scripts\activate.bat"

echo ============================================================
echo   INICIANDO SISTEMA DE FINANCAS PESSOAIS
echo ============================================================
echo.

echo [INFO] Ativando ambiente virtual...
if exist "%ACTIVATE_BAT%" (
    call "%ACTIVATE_BAT%"
    if errorlevel 1 (
        echo [ERRO] Falha ao ativar o ambiente virtual!
        pause
        exit /b 1
    )
)
echo [OK] Ambiente virtual ativado
echo.

REM Validar python do venv sem depender de PATH
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no ambiente virtual!
    echo [INFO] Caminho esperado: %PYTHON_EXE%
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('"%PYTHON_EXE%" --version 2^>^&1') do set "PYVER=%%v"
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set "PYMAJOR=%%a"
    set "PYMINOR=%%b"
)

if not defined PYMAJOR (
    echo [ERRO] Nao foi possivel identificar a versao do Python.
    pause
    exit /b 1
)
if not "%PYMAJOR%"=="3" (
    echo [ERRO] Python 3.10+ obrigatorio. Versao atual: %PYVER%
    pause
    exit /b 1
)
if not defined PYMINOR (
    echo [ERRO] Nao foi possivel identificar a versao do Python.
    pause
    exit /b 1
)
if %PYMINOR% LSS 10 (
    echo [ERRO] Python 3.10+ obrigatorio. Versao atual: %PYVER%
    pause
    exit /b 1
)
echo [INFO] Python detectado: %PYVER%
echo.

echo [INFO] Iniciando servidor Flask...
echo [INFO] O navegador sera aberto automaticamente em alguns segundos...
echo.
echo ============================================================
echo   Para encerrar o sistema, pressione Ctrl+C
echo ============================================================
echo.

"%PYTHON_EXE%" run.py

if errorlevel 1 (
    echo.
    echo [ERRO] O sistema foi encerrado com erros!
    echo.
    pause
)

@echo off
REM ============================================================
REM Script para iniciar o Sistema de Finanças Pessoais
REM Este script será executado de forma oculta via VBScript
REM ============================================================

title Sistema de Finanças Pessoais

REM Obter o diretório onde o script está localizado
set "SCRIPT_DIR=%~dp0"
REM O script está em sistema/, então o projeto está um nível acima
set "PROJECT_DIR=%SCRIPT_DIR%.."

REM Normalizar o caminho (remover ..)
cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    REM Se falhar, tentar caminho padrão
    set "PROJECT_DIR=C:\PROJETOS\Flask\SFP_alfa"
) else (
    set "PROJECT_DIR=%CD%"
)

REM Se o diretório do projeto não existir, tentar caminho padrão
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
    echo [INFO] Execute com Python 3.10+: python -m venv venv
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

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set "PYMAJOR=%%a"
    set "PYMINOR=%%b"
)
if not "%PYMAJOR%"=="3" (
    echo [ERRO] Python 3.10+ obrigatorio. Versao atual: %PYVER%
    pause
    exit /b 1
)
if %PYMINOR% LSS 10 (
    echo [ERRO] Python 3.10+ obrigatorio. Versao atual: %PYVER%
    pause
    exit /b 1
)
echo [INFO] Python detectado: %PYVER%

echo [INFO] Iniciando servidor Flask...
echo [INFO] O navegador será aberto automaticamente em alguns segundos...
echo.
echo ============================================================
echo   Para encerrar o sistema, pressione Ctrl+C
echo ============================================================
echo.

REM Executar o script Python
python run.py

REM Se o script terminar, manter a janela aberta para ver erros
if errorlevel 1 (
    echo.
    echo [ERRO] O sistema foi encerrado com erros!
    echo.
    pause
)


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
    call :pause_if_needed
    exit /b 1
)

if not exist "%PROJECT_DIR%\run.py" (
    echo [ERRO] Arquivo run.py nao encontrado no projeto!
    echo [INFO] Caminho: %PROJECT_DIR%
    call :pause_if_needed
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

call :find_venv
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

echo ============================================================
echo   INICIANDO SISTEMA DE FINANCAS PESSOAIS
echo ============================================================
echo.

echo [INFO] Validando ambiente virtual...
call :ensure_working_python
if errorlevel 1 (
    call :pause_if_needed
    exit /b 1
)
echo [OK] Ambiente virtual pronto
echo.

for /f "tokens=2 delims= " %%v in ('"%PYTHON_EXE%" --version 2^>^&1') do set "PYVER=%%v"
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set "PYMAJOR=%%a"
    set "PYMINOR=%%b"
)

if not defined PYMAJOR (
    echo [ERRO] Nao foi possivel identificar a versao do Python.
    call :pause_if_needed
    exit /b 1
)
if not "%PYMAJOR%"=="3" (
    echo [ERRO] Python 3.10+ obrigatorio. Versao atual: %PYVER%
    call :pause_if_needed
    exit /b 1
)
if not defined PYMINOR (
    echo [ERRO] Nao foi possivel identificar a versao do Python.
    call :pause_if_needed
    exit /b 1
)
if %PYMINOR% LSS 10 (
    echo [ERRO] Python 3.10+ obrigatorio. Versao atual: %PYVER%
    call :pause_if_needed
    exit /b 1
)
echo [INFO] Python detectado: %PYVER%

"%PYTHON_EXE%" -c "import flask" >nul 2>&1
if errorlevel 1 (
    if not exist "%PROJECT_DIR%\requirements.txt" (
        echo [ERRO] requirements.txt nao encontrado no projeto.
        call :pause_if_needed
        exit /b 1
    )
    echo [AVISO] Dependencias do projeto nao estao disponiveis neste ambiente virtual.
    echo [INFO] Instalando dependencias automaticamente...
    "%PYTHON_EXE%" -m pip install -r "%PROJECT_DIR%\requirements.txt"
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias do projeto.
        echo [INFO] Execute manualmente: "%PYTHON_EXE%" -m pip install -r requirements.txt
        call :pause_if_needed
        exit /b 1
    )
    "%PYTHON_EXE%" -c "import flask" >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] Dependencias instaladas, mas Flask ainda nao esta disponivel.
        call :pause_if_needed
        exit /b 1
    )
)

echo.
if /I "%SFP_VALIDATE_ONLY%"=="1" (
    echo [OK] Validacao concluida. Encerrando por SFP_VALIDATE_ONLY.
    exit /b 0
)

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
    call :pause_if_needed
)
exit /b %errorlevel%

:find_venv
set "VENV_DIR="
if exist "%PROJECT_DIR%\venv\Scripts\python.exe" set "VENV_DIR=%PROJECT_DIR%\venv"
if not defined VENV_DIR if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" set "VENV_DIR=%PROJECT_DIR%\.venv"
if not defined VENV_DIR if exist "%PROJECT_DIR%\venv" set "VENV_DIR=%PROJECT_DIR%\venv"
if not defined VENV_DIR if exist "%PROJECT_DIR%\.venv" set "VENV_DIR=%PROJECT_DIR%\.venv"
if not defined VENV_DIR set "VENV_DIR=%PROJECT_DIR%\venv"
exit /b 0

:ensure_working_python
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" --version >nul 2>&1
    if not errorlevel 1 exit /b 0
    echo [AVISO] Ambiente virtual inconsistente. Tentando reparar com Python 3.10...
) else (
    if exist "%VENV_DIR%" (
        echo [AVISO] Ambiente virtual incompleto detectado em: %VENV_DIR%
        echo [INFO] Recriando o bootstrap do ambiente virtual...
    ) else (
        echo [INFO] Ambiente virtual nao encontrado. Criando em: %VENV_DIR%
    )
)

call :bootstrap_venv
if errorlevel 1 (
    echo [ERRO] Nao foi possivel criar ou reparar o ambiente virtual.
    echo [INFO] Tente manualmente: py -3.10 -m venv "%VENV_DIR%"
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo [ERRO] Python nao encontrado no ambiente virtual apos bootstrap!
    echo [INFO] Caminho esperado: %PYTHON_EXE%
    exit /b 1
)

"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no ambiente virtual apos tentativa de reparo!
    echo [INFO] Caminho esperado: %PYTHON_EXE%
    exit /b 1
)
exit /b 0

:bootstrap_venv
py -3.10 -m venv "%VENV_DIR%" >nul 2>&1
if not errorlevel 1 exit /b 0

echo [AVISO] Falha ao criar/reparar com py -3.10. Tentando py -3...
py -3 -m venv "%VENV_DIR%" >nul 2>&1
if not errorlevel 1 exit /b 0

echo [AVISO] Falha ao criar/reparar com py -3. Tentando python -m venv...
python -m venv "%VENV_DIR%" >nul 2>&1
if not errorlevel 1 exit /b 0

exit /b 1



:pause_if_needed
if /I "%SFP_VALIDATE_ONLY%"=="1" exit /b 0
if /I "%CI%"=="1" exit /b 0
pause
exit /b 0

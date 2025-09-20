@echo off
REM Define o diretório base como o diretório do usuário logado
set "USER_INSTALL_DIR=%USERPROFILE%\Financas_Pessoais"

REM Verifica se existe no diretório do usuário, senão usa o diretório atual
if exist "%USER_INSTALL_DIR%" (
    cd /d "%USER_INSTALL_DIR%"
) else (
    cd /d "%~dp0"
)

REM Verifica se a venv existe
if not exist "venv\Scripts\activate.bat" (
    echo Criando ambiente virtual...
    py -m venv venv
)

REM Ativa o ambiente virtual
call venv\Scripts\activate.bat

REM Instala as dependências
if exist "requirements.txt" (
    echo Instalando dependências do requirements.txt...
    pip install -r requirements.txt
) else (
    echo Arquivo requirements.txt não encontrado!
)

REM Inicia o Flask usando o Python do ambiente virtual diretamente
start "" venv\Scripts\python.exe run.py

REM Aguarda o servidor iniciar (ajuste se precisar de mais tempo)
timeout /t 5 >nul

REM Abre o navegador
start "" http://127.0.0.1:5000

exit

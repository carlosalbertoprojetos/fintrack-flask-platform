@echo off
cd /d "%~dp0"

REM Verifica se a venv existe
if not exist "venv\Scripts\activate.bat" (
    echo Criando ambiente virtual...
    python -m venv venv
)

REM Ativa o ambiente virtual
call venv\Scripts\activate

REM Instala as dependências
if exist "requirements.txt" (
    echo Instalando dependências do requirements.txt...
    pip install -r requirements.txt
) else (
    echo Arquivo requirements.txt não encontrado!
)

REM Inicia o Flask em uma janela separada
start "" python run.py

REM Aguarda o servidor iniciar (ajuste se precisar de mais tempo)
timeout /t 3 >nul

REM Abre o navegador
start "" http://127.0.0.1:5000

exit

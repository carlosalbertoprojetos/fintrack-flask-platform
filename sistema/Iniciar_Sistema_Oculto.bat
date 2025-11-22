@echo off
REM ============================================================
REM Wrapper para executar o sistema de forma oculta
REM Este arquivo chama o script VBScript que executa sem janela
REM ============================================================

REM Obter o diretório onde o script está localizado
set "SCRIPT_DIR=%~dp0"

REM Executar o script VBScript que inicia o sistema de forma oculta
if exist "%SCRIPT_DIR%Iniciar_Sistema.vbs" (
    wscript.exe "%SCRIPT_DIR%Iniciar_Sistema.vbs"
) else (
    echo [ERRO] Arquivo Iniciar_Sistema.vbs nao encontrado!
    echo [INFO] Caminho tentado: %SCRIPT_DIR%Iniciar_Sistema.vbs
    echo [INFO] Usando metodo alternativo...
    pause
)


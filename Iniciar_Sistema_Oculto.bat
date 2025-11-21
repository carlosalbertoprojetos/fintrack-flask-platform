@echo off
REM ============================================================
REM Wrapper para executar o sistema de forma oculta
REM Este arquivo chama o script VBScript que executa sem janela
REM ============================================================

REM Executar o script VBScript que inicia o sistema de forma oculta
if exist "Iniciar_Sistema.vbs" (
    wscript.exe "Iniciar_Sistema.vbs"
) else (
    echo [ERRO] Arquivo Iniciar_Sistema.vbs nao encontrado!
    echo [INFO] Usando metodo alternativo...
    pause
)


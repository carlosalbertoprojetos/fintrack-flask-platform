@echo off
setlocal EnableExtensions
set "ROOT_DIR=%~dp0"
if exist "%ROOT_DIR%sistema\Iniciar_Sistema.bat" (
    call "%ROOT_DIR%sistema\Iniciar_Sistema.bat"
    exit /b %errorlevel%
)

echo [ERRO] Inicializador nao encontrado.
echo [INFO] Caminho esperado: %ROOT_DIR%sistema\Iniciar_Sistema.bat
pause
exit /b 1
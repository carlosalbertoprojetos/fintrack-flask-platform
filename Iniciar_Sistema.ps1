# ============================================================
# Script PowerShell para iniciar o Sistema de Finanças Pessoais
# ============================================================

$ErrorActionPreference = "Stop"

# Configurações
$ProjectPath = "C:\PROJETOS\Flask\SFP_alfa"
$VenvPath = Join-Path $ProjectPath "venv"
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
$RunScript = Join-Path $ProjectPath "run.py"

# Verificar se o diretório existe
if (-not (Test-Path $ProjectPath)) {
    Write-Host "[ERRO] Diretório do projeto não encontrado!" -ForegroundColor Red
    Write-Host "[INFO] Verifique o caminho: $ProjectPath" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Verificar se o virtualenv existe
if (-not (Test-Path $ActivateScript)) {
    Write-Host "[ERRO] Virtualenv não encontrado!" -ForegroundColor Red
    Write-Host "[INFO] Execute: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  INICIANDO SISTEMA DE FINANÇAS PESSOAIS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Mudar para o diretório do projeto
Set-Location $ProjectPath

# Ativar virtualenv
Write-Host "[INFO] Ativando ambiente virtual..." -ForegroundColor Yellow
try {
    & $ActivateScript
    Write-Host "[OK] Ambiente virtual ativado" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] Falha ao ativar o ambiente virtual!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host ""

# Verificar se Python está disponível
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Host "[ERRO] Python não encontrado no ambiente virtual!" -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host ""
Write-Host "[INFO] Iniciando servidor Flask..." -ForegroundColor Yellow
Write-Host "[INFO] O navegador será aberto automaticamente em alguns segundos..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Para encerrar o sistema, pressione Ctrl+C" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Executar o script Python
try {
    python $RunScript
} catch {
    Write-Host ""
    Write-Host "[ERRO] O sistema foi encerrado com erros!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "Pressione Enter para sair"
    exit 1
}


$ErrorActionPreference = "Stop"

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectPath = (Resolve-Path (Join-Path $ScriptPath ".." )).Path
$RunScript = Join-Path $ProjectPath "run.py"

function Get-VenvPath {
    param([string]$BasePath)

    $candidates = @(
        (Join-Path $BasePath "venv"),
        (Join-Path $BasePath ".venv")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path (Join-Path $candidate "Scripts\python.exe")) {
            return $candidate
        }
    }

    return $null
}

function Repair-Venv {
    param([string]$VenvPath)

    Write-Host "[AVISO] Ambiente virtual inconsistente. Tentando reparar com Python 3.10..." -ForegroundColor Yellow
    & py -3.10 -m venv --upgrade $VenvPath *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[AVISO] Falha ao reparar com py -3.10. Tentando py -3..." -ForegroundColor Yellow
        & py -3 -m venv --upgrade $VenvPath *> $null
    }
}

if (-not (Test-Path $ProjectPath)) {
    Write-Host "[ERRO] Diretorio do projeto nao encontrado!" -ForegroundColor Red
    Write-Host "[INFO] Caminho tentado: $ProjectPath" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

if (-not (Test-Path $RunScript)) {
    Write-Host "[ERRO] Arquivo run.py nao encontrado no projeto!" -ForegroundColor Red
    Write-Host "[INFO] Caminho: $ProjectPath" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

$DbFile = $null
$InstanceDb = Join-Path $ProjectPath "instance\financas.db"
$LegacyDb = Join-Path $ProjectPath "app.db"
if (Test-Path $InstanceDb) {
    $DbFile = $InstanceDb
} elseif (Test-Path $LegacyDb) {
    $DbFile = $LegacyDb
}

if ($DbFile) {
    $env:DATABASE_URL = "sqlite:///$DbFile"
    Write-Host "[INFO] Banco de dados definido para: $DbFile" -ForegroundColor Gray
}

$VenvPath = Get-VenvPath -BasePath $ProjectPath
if (-not $VenvPath) {
    Write-Host "[ERRO] Ambiente virtual nao encontrado!" -ForegroundColor Red
    Write-Host "[INFO] Esperado: venv\Scripts\python.exe ou .venv\Scripts\python.exe" -ForegroundColor Yellow
    Write-Host "[INFO] Execute com Python 3.10+: py -3.10 -m venv venv" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  INICIANDO SISTEMA DE FINANCAS PESSOAIS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Validando ambiente virtual..." -ForegroundColor Yellow

if (-not (Test-Path $PythonExe)) {
    Write-Host "[ERRO] Python nao encontrado no ambiente virtual!" -ForegroundColor Red
    Write-Host "[INFO] Caminho esperado: $PythonExe" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

& $PythonExe --version *> $null
if ($LASTEXITCODE -ne 0) {
    Repair-Venv -VenvPath $VenvPath
    & $PythonExe --version *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERRO] Python nao encontrado no ambiente virtual apos tentativa de reparo!" -ForegroundColor Red
        Write-Host "[INFO] Caminho esperado: $PythonExe" -ForegroundColor Yellow
        Read-Host "Pressione Enter para sair"
        exit 1
    }
}

$pythonVersion = & $PythonExe --version 2>&1
Write-Host "[OK] Ambiente virtual pronto" -ForegroundColor Green
Write-Host "[INFO] $pythonVersion" -ForegroundColor Gray

if ($pythonVersion -notmatch "Python\s+(\d+)\.(\d+)") {
    Write-Host "[ERRO] Nao foi possivel identificar a versao do Python." -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

$major = [int]$Matches[1]
$minor = [int]$Matches[2]
if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
    Write-Host "[ERRO] Python 3.10+ obrigatorio. Versao atual: $pythonVersion" -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

& $PythonExe -c "import flask" *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Dependencias do projeto nao estao disponiveis neste ambiente virtual." -ForegroundColor Red
    Write-Host "[INFO] Execute: `"$PythonExe`" -m pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host ""
if ($env:SFP_VALIDATE_ONLY -eq "1") {
    Write-Host "[OK] Validacao concluida. Encerrando por SFP_VALIDATE_ONLY." -ForegroundColor Green
    exit 0
}

Write-Host "[INFO] Iniciando servidor Flask..." -ForegroundColor Yellow
Write-Host "[INFO] O navegador sera aberto automaticamente em alguns segundos..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Para encerrar o sistema, pressione Ctrl+C" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

& $PythonExe $RunScript
exit $LASTEXITCODE
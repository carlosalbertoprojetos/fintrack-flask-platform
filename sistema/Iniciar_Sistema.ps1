$ErrorActionPreference = "Stop"

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectPath = (Resolve-Path (Join-Path $ScriptPath ".." )).Path
$RunScript = Join-Path $ProjectPath "run.py"

function Wait-IfInteractive {
    if ($env:SFP_VALIDATE_ONLY -eq "1" -or $env:CI -eq "1") {
        return
    }
    Read-Host "Pressione Enter para sair" | Out-Null
}

function Get-VenvPath {
    param([string]$BasePath)

    $venvCandidate = Join-Path $BasePath "venv"
    $dotVenvCandidate = Join-Path $BasePath ".venv"
    $pythonCandidates = @(
        (Join-Path $venvCandidate "Scripts\python.exe"),
        (Join-Path $dotVenvCandidate "Scripts\python.exe")
    )

    foreach ($candidate in $pythonCandidates) {
        if (Test-Path $candidate) {
            return (Split-Path (Split-Path $candidate -Parent) -Parent)
        }
    }

    if (Test-Path $venvCandidate) { return $venvCandidate }
    if (Test-Path $dotVenvCandidate) { return $dotVenvCandidate }
    return $venvCandidate
}

function Bootstrap-Venv {
    param([string]$VenvPath)

    & py -3.10 -m venv $VenvPath *> $null
    if ($LASTEXITCODE -eq 0) { return $true }

    Write-Host "[AVISO] Falha ao criar/reparar com py -3.10. Tentando py -3..." -ForegroundColor Yellow
    & py -3 -m venv $VenvPath *> $null
    if ($LASTEXITCODE -eq 0) { return $true }

    Write-Host "[AVISO] Falha ao criar/reparar com py -3. Tentando python -m venv..." -ForegroundColor Yellow
    & python -m venv $VenvPath *> $null
    return ($LASTEXITCODE -eq 0)
}

function Ensure-WorkingPython {
    param([string]$VenvPath, [string]$PythonExe)

    if ((Test-Path $PythonExe)) {
        & $PythonExe --version *> $null
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        Write-Host "[AVISO] Ambiente virtual inconsistente. Tentando reparar com Python 3.10..." -ForegroundColor Yellow
    } elseif (Test-Path $VenvPath) {
        Write-Host "[AVISO] Ambiente virtual incompleto detectado em: $VenvPath" -ForegroundColor Yellow
        Write-Host "[INFO] Recriando o bootstrap do ambiente virtual..." -ForegroundColor Yellow
    } else {
        Write-Host "[INFO] Ambiente virtual nao encontrado. Criando em: $VenvPath" -ForegroundColor Yellow
    }

    if (-not (Bootstrap-Venv -VenvPath $VenvPath)) {
        return $false
    }

    if (-not (Test-Path $PythonExe)) {
        return $false
    }

    & $PythonExe --version *> $null
    return ($LASTEXITCODE -eq 0)
}

function Ensure-Requirements {
    param([string]$PythonExe, [string]$ProjectPath)

    & $PythonExe -c "import flask" *> $null
    if ($LASTEXITCODE -eq 0) {
        return $true
    }

    $requirementsFile = Join-Path $ProjectPath "requirements.txt"
    if (-not (Test-Path $requirementsFile)) {
        Write-Host "[ERRO] requirements.txt nao encontrado no projeto." -ForegroundColor Red
        return $false
    }

    Write-Host "[AVISO] Dependencias do projeto nao estao disponiveis neste ambiente virtual." -ForegroundColor Yellow
    Write-Host "[INFO] Instalando dependencias automaticamente..." -ForegroundColor Yellow
    & $PythonExe -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    & $PythonExe -c "import flask" *> $null
    return ($LASTEXITCODE -eq 0)
}

if (-not (Test-Path $ProjectPath)) {
    Write-Host "[ERRO] Diretorio do projeto nao encontrado!" -ForegroundColor Red
    Write-Host "[INFO] Caminho tentado: $ProjectPath" -ForegroundColor Yellow
    Wait-IfInteractive
    exit 1
}

if (-not (Test-Path $RunScript)) {
    Write-Host "[ERRO] Arquivo run.py nao encontrado no projeto!" -ForegroundColor Red
    Write-Host "[INFO] Caminho: $ProjectPath" -ForegroundColor Yellow
    Wait-IfInteractive
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
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  INICIANDO SISTEMA DE FINANCAS PESSOAIS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Validando ambiente virtual..." -ForegroundColor Yellow

if (-not (Ensure-WorkingPython -VenvPath $VenvPath -PythonExe $PythonExe)) {
    Write-Host "[ERRO] Nao foi possivel criar ou reparar o ambiente virtual." -ForegroundColor Red
    Write-Host "[INFO] Tente manualmente: py -3.10 -m venv $VenvPath" -ForegroundColor Yellow
    Wait-IfInteractive
    exit 1
}

$pythonVersion = & $PythonExe --version 2>&1
Write-Host "[OK] Ambiente virtual pronto" -ForegroundColor Green
Write-Host "[INFO] $pythonVersion" -ForegroundColor Gray

if ($pythonVersion -notmatch "Python\s+(\d+)\.(\d+)") {
    Write-Host "[ERRO] Nao foi possivel identificar a versao do Python." -ForegroundColor Red
    Wait-IfInteractive
    exit 1
}

$major = [int]$Matches[1]
$minor = [int]$Matches[2]
if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
    Write-Host "[ERRO] Python 3.10+ obrigatorio. Versao atual: $pythonVersion" -ForegroundColor Red
    Wait-IfInteractive
    exit 1
}

if (-not (Ensure-Requirements -PythonExe $PythonExe -ProjectPath $ProjectPath)) {
    Write-Host "[ERRO] Falha ao instalar dependencias do projeto." -ForegroundColor Red
    Write-Host "[INFO] Execute: `"$PythonExe`" -m pip install -r requirements.txt" -ForegroundColor Yellow
    Wait-IfInteractive
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

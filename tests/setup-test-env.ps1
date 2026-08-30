param(
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = $scriptDirectory
$rootRequirementsPath = Join-Path $projectRoot "homelab-mcp\requirements.txt"

if (-not (Test-Path $rootRequirementsPath)) {
    $projectRoot = Split-Path -Parent $scriptDirectory
}

$venvPath = Join-Path $projectRoot ".venv"
$pythonPath = Join-Path $venvPath "Scripts\python.exe"
$requirementsPath = Join-Path $projectRoot "homelab-mcp\requirements.txt"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher (py.exe) nao foi encontrado. Instale o Python e habilite o launcher."
}

if (-not (Test-Path $pythonPath)) {
    & py -m venv $venvPath
}

& $pythonPath -m pip install --upgrade pip
& $pythonPath -m pip install -r $requirementsPath
& $pythonPath -m pip install pytest

if ($RunTests) {
    $env:PYTHONPATH = Join-Path $projectRoot "homelab-mcp"
    & $pythonPath -m pytest (Join-Path $projectRoot "tests") -q

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "Ambiente de testes pronto em $venvPath"
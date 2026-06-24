$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EngineRoot = Join-Path $ProjectRoot "python-engine"
$Venv = Join-Path $EngineRoot ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$OutputDir = Join-Path $ProjectRoot "src-tauri\binaries"
$Target = "x86_64-pc-windows-msvc"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher not found. Install 64-bit Python 3.12."
}

& py -3.12 -c "import sys; assert sys.version_info[:2] == (3, 12)"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.12 is required to package the DJ Agent analysis sidecar."
}

if (-not (Test-Path $Python)) {
    py -3.12 -m venv $Venv
}

& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $EngineRoot "requirements.txt")

Push-Location $EngineRoot
try {
    & $Python -m PyInstaller --noconfirm --clean --onefile --name "dj-agent-engine" `
        --collect-all librosa --collect-all soundfile --collect-all sklearn `
        --hidden-import uvicorn.logging --hidden-import uvicorn.loops.auto `
        --hidden-import uvicorn.protocols.http.auto --hidden-import uvicorn.protocols.websockets.auto `
        --hidden-import uvicorn.lifespan.on "run.py"
} finally {
    Pop-Location
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Copy-Item -Force (Join-Path $EngineRoot "dist\dj-agent-engine.exe") `
    (Join-Path $OutputDir "dj-agent-engine-$Target.exe")
Write-Host "Sidecar ready: src-tauri\binaries\dj-agent-engine-$Target.exe"

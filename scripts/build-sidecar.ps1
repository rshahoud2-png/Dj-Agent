$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EngineRoot = Join-Path $ProjectRoot "python-engine"
$Venv = Join-Path $EngineRoot ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$OutputDir = Join-Path $ProjectRoot "src-tauri\binaries"
$Target = "x86_64-pc-windows-msvc"

function Assert-NativeCommand([string]$Description) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher not found. Install 64-bit Python 3.12."
}

& py -3.12 -c "import sys; assert sys.version_info[:2] == (3, 12)"
Assert-NativeCommand "Python 3.12 validation"

if (Test-Path $Python) {
    & $Python --version
    if ($LASTEXITCODE -ne 0) {
        $ResolvedVenv = [IO.Path]::GetFullPath($Venv)
        $ResolvedEngineRoot = [IO.Path]::GetFullPath($EngineRoot)
        if (-not $ResolvedVenv.StartsWith($ResolvedEngineRoot, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove unexpected virtual environment path: $ResolvedVenv"
        }
        Remove-Item -LiteralPath $ResolvedVenv -Recurse -Force
    }
}

if (-not (Test-Path $Python)) {
    py -3.12 -m venv $Venv
    Assert-NativeCommand "Python virtual environment creation"
}

& $Python -m pip install --upgrade pip
Assert-NativeCommand "pip upgrade"
& $Python -m pip install -r (Join-Path $EngineRoot "requirements.txt")
Assert-NativeCommand "Python dependency installation"

Push-Location $EngineRoot
try {
    & $Python -m PyInstaller --noconfirm --clean --onefile --name "dj-agent-engine" `
        --collect-all librosa --collect-all soundfile --collect-all sklearn `
        --collect-all numpy --collect-all scipy --collect-all numba --collect-all imageio_ffmpeg `
        --hidden-import uvicorn.logging --hidden-import uvicorn.loops.auto `
        --hidden-import uvicorn.protocols.http.auto --hidden-import uvicorn.protocols.websockets.auto `
        --hidden-import uvicorn.lifespan.on "run.py"
    Assert-NativeCommand "PyInstaller packaging"
} finally {
    Pop-Location
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Copy-Item -Force (Join-Path $EngineRoot "dist\dj-agent-engine.exe") `
    (Join-Path $OutputDir "dj-agent-engine-$Target.exe")
Write-Host "Sidecar ready: src-tauri\binaries\dj-agent-engine-$Target.exe"

& (Join-Path $PSScriptRoot "validate-sidecar-bundle.ps1")
& (Join-Path $PSScriptRoot "test-sidecar.ps1")

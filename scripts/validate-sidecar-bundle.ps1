param([string]$Executable = "src-tauri\binaries\dj-agent-engine-x86_64-pc-windows-msvc.exe")

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EngineRoot = Join-Path $ProjectRoot "python-engine"
$Python = Join-Path $EngineRoot ".venv\Scripts\python.exe"
$ExecutablePath = [IO.Path]::GetFullPath((Join-Path $ProjectRoot $Executable))

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python packaging environment is missing: $Python"
}
if (-not (Test-Path -LiteralPath $ExecutablePath)) {
    throw "Packaged sidecar is missing: $ExecutablePath"
}

$contents = (& $Python -m PyInstaller.utils.cliutils.archive_viewer -r $ExecutablePath | Out-String)
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller archive inspection failed with exit code $LASTEXITCODE."
}
foreach ($pattern in @("python3", "numpy", "scipy", "soundfile", "libsndfile", "imageio_ffmpeg", "ffmpeg")) {
    if ($contents -notmatch [regex]::Escape($pattern)) {
        throw "Packaged sidecar validation failed: '$pattern' was not found in the PyInstaller archive."
    }
}

Write-Host "PyInstaller archive contains Python, FFmpeg, NumPy, SciPy, and SoundFile native runtime files."

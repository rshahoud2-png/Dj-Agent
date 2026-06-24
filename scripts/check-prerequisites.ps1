$ErrorActionPreference = "Stop"

function Require-Command([string]$Name, [string]$InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command '$Name'. $InstallHint"
    }
}

Require-Command "node" "Install Node.js 20 or newer."
Require-Command "npm" "Install Node.js 20 or newer."
Require-Command "py" "Install 64-bit Python 3.12 with the Python launcher."
Require-Command "rustc" "Install Rust stable from https://rustup.rs."
Require-Command "cargo" "Install Rust stable from https://rustup.rs."

& py -3.12 -c "import sys; assert sys.version_info[:2] == (3, 12)"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.12 is required for the packaged audio sidecar. Run 'py -0p' to inspect installed versions."
}

$rustHost = (& rustc -Vv | Select-String "^host:").ToString()
if ($rustHost -notmatch "x86_64-pc-windows-msvc") {
    throw "Rust must target x86_64-pc-windows-msvc. Current $rustHost"
}

Write-Host "Windows build prerequisites detected."

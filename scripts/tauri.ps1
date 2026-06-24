param(
    [Parameter(Position = 0)]
    [ValidateSet("dev", "build")]
    [string]$Command = "dev"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot
try {
    if ($Command -eq "build") {
        & (Join-Path $PSScriptRoot "build-windows.ps1")
    } else {
        npm run sidecar:build
        npx tauri dev
    }
} finally {
    Pop-Location
}

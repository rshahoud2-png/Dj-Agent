param([switch]$Unsigned)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot
try {
    & (Join-Path $PSScriptRoot "check-prerequisites.ps1")
    if (-not (Test-Path "src-tauri\icons\icon.ico")) {
        npx tauri icon "assets\app-icon.svg"
    }
    npm run sidecar:build
    if ($Unsigned) {
        npx tauri build --config "src-tauri\tauri.unsigned.conf.json"
    } else {
        npx tauri build
    }
    $Installer = Get-ChildItem "src-tauri\target\release\bundle\nsis\*.exe" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $Installer) {
        throw "Tauri completed but no NSIS installer was found."
    }
    New-Item -ItemType Directory -Force -Path "release" | Out-Null
    Copy-Item -Force $Installer.FullName "release\DJAgentSetup.exe"
    Write-Host "Installer ready: release\DJAgentSetup.exe"
} finally {
    Pop-Location
}

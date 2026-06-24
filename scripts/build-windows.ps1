$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot
try {
    npm run sidecar:build
    npx tauri build
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

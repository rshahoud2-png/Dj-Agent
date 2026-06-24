param([string]$Installer = "release\DJAgentSetup.exe")

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$InstallerPath = [IO.Path]::GetFullPath((Join-Path $ProjectRoot $Installer))
$InstallRoot = Join-Path $env:RUNNER_TEMP "DJAgentDesktopInstallSmoke"

if (-not (Test-Path -LiteralPath $InstallerPath)) {
    throw "Windows installer was not found: $InstallerPath"
}
if (Test-Path -LiteralPath $InstallRoot) {
    throw "Installer smoke-test location already exists: $InstallRoot"
}

$InstallerProcess = Start-Process -FilePath $InstallerPath -ArgumentList @("/S", "/D=$InstallRoot") -PassThru -Wait -WindowStyle Hidden
if ($InstallerProcess.ExitCode -ne 0) {
    throw "DJAgentSetup.exe silent installation failed with exit code $($InstallerProcess.ExitCode)."
}

$deadline = (Get-Date).AddSeconds(60)
do {
    $AppExecutable = Get-ChildItem -LiteralPath $InstallRoot -Filter "DJ Agent Desktop.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    $SidecarExecutable = Get-ChildItem -LiteralPath $InstallRoot -Filter "dj-agent-engine.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($AppExecutable -and $SidecarExecutable) {
        break
    }
    Start-Sleep -Milliseconds 750
} while ((Get-Date) -lt $deadline)

if (-not $AppExecutable) {
    throw "The installed Tauri application executable was not found under $InstallRoot."
}
if (-not $SidecarExecutable) {
    throw "The installed Python sidecar executable was not found under $InstallRoot."
}

& (Join-Path $PSScriptRoot "test-sidecar.ps1") -Executable $SidecarExecutable.FullName -Port 17831
Write-Host "Installed DJAgentSetup.exe contents and sidecar runtime checks passed."

$Uninstaller = Get-ChildItem -LiteralPath $InstallRoot -Filter "*uninstall*.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($Uninstaller) {
    $UninstallProcess = Start-Process -FilePath $Uninstaller.FullName -ArgumentList "/S" -PassThru -Wait -WindowStyle Hidden
    if ($UninstallProcess.ExitCode -ne 0) {
        Write-Warning "Smoke-test uninstall returned exit code $($UninstallProcess.ExitCode)."
    }
}

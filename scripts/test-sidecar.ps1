param(
    [string]$Executable = "src-tauri\binaries\dj-agent-engine-x86_64-pc-windows-msvc.exe",
    [int]$Port = 17829
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ExecutablePath = [IO.Path]::GetFullPath((Join-Path $ProjectRoot $Executable))

if (-not (Test-Path -LiteralPath $ExecutablePath)) {
    throw "Packaged sidecar was not found: $ExecutablePath"
}

$stdout = Join-Path $env:TEMP "dj-agent-sidecar-smoke.stdout.log"
$stderr = Join-Path $env:TEMP "dj-agent-sidecar-smoke.stderr.log"
Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue

$env:DJ_AGENT_ENGINE_PORT = [string]$Port
$process = Start-Process -FilePath $ExecutablePath -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $stdout -RedirectStandardError $stderr

try {
    $passed = $false
    $deadline = (Get-Date).AddSeconds(45)
    do {
        if ($process.HasExited) {
            $details = @(
                "The packaged sidecar exited with code $($process.ExitCode)."
                (Get-Content -LiteralPath $stdout -Raw -ErrorAction SilentlyContinue)
                (Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue)
            ) -join [Environment]::NewLine
            throw $details
        }
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2
            if ($health.status -eq "ok" -and $health.service -eq "dj-agent-desktop-engine") {
                Write-Host "Packaged sidecar health check passed."
                $passed = $true
                break
            }
        } catch {
            Start-Sleep -Milliseconds 750
        }
    } while ((Get-Date) -lt $deadline)

    if (-not $passed) {
        throw "Timed out waiting for packaged sidecar health endpoint."
    }
} finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        $process.WaitForExit()
    }
    Remove-Item Env:DJ_AGENT_ENGINE_PORT -ErrorAction SilentlyContinue
}

param(
    [string]$Executable = "src-tauri\binaries\dj-agent-engine-x86_64-pc-windows-msvc.exe",
    [int]$Port = 17829
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ExecutablePath = if ([IO.Path]::IsPathRooted($Executable)) {
    [IO.Path]::GetFullPath($Executable)
} else {
    [IO.Path]::GetFullPath((Join-Path $ProjectRoot $Executable))
}

if (-not (Test-Path -LiteralPath $ExecutablePath)) {
    throw "Packaged sidecar was not found: $ExecutablePath"
}

$existingProcessIds = @(Get-Process -Name "dj-agent-engine" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
& cmd.exe /d /c start '""' /b "`"$ExecutablePath`"" --port $Port
if ($LASTEXITCODE -ne 0) {
    throw "Windows could not launch the packaged sidecar (exit code $LASTEXITCODE)."
}
Start-Sleep -Milliseconds 500
$process = Get-Process -Name "dj-agent-engine" -ErrorAction SilentlyContinue |
    Where-Object { $_.Id -notin $existingProcessIds } |
    Sort-Object StartTime -Descending |
    Select-Object -First 1

try {
    $passed = $false
    $deadline = (Get-Date).AddSeconds(45)
    do {
        if ($process.HasExited) {
            throw "The packaged sidecar exited with code $($process.ExitCode)."
        }
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2
            if ($health.status -eq "ok" -and $health.service -eq "dj-agent-desktop-engine") {
                $diagnostics = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/diagnostics" -TimeoutSec 30
                $failed = @($diagnostics.checks | Where-Object { -not $_.ok })
                if ($failed.Count -gt 0) {
                    $details = ($failed | ForEach-Object { "$($_.label): $($_.details)" }) -join [Environment]::NewLine
                    throw "Packaged sidecar runtime diagnostics failed:$([Environment]::NewLine)$details"
                }
                Write-Host "Packaged sidecar health, FFmpeg, SQLite, and native dependency checks passed."
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
}

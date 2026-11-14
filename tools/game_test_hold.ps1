# Pauses the in-game test queue while the owner uses the PC.
#
#   powershell -ExecutionPolicy Bypass -File tools\game_test_hold.ps1          # hold until the HOLD file is deleted
#   Remove-Item E:\PandabornDev\build\test\HOLD                                # release: queued runs carry on
#
# It takes the same named mutex every game test takes (after the run in progress, if any, has finished), so no new
# game window opens while it is held. Queued runs simply keep waiting; nothing is cancelled. A run already in the
# game is never interrupted.
param(
    [string]$TestRoot = 'E:\PandabornDev\build\test',
    [string]$Reason = 'the owner is using the PC'
)
$ErrorActionPreference = 'Stop'
$holdPath = Join-Path $TestRoot 'HOLD'
$lockInfoPath = Join-Path $TestRoot 'gametest.lock.json'
$utf8 = New-Object System.Text.UTF8Encoding($false)
New-Item -ItemType Directory -Force $TestRoot | Out-Null
[IO.File]::WriteAllText($holdPath, "Game tests are held: $Reason. Delete this file to release.`r`n", $utf8)

$mutex = New-Object System.Threading.Mutex($false, 'Global\PandabornGameTest')
$owned = $false
try {
    Write-Host "Waiting for the run in progress (if any) to finish..."
    while (-not $owned) {
        if (-not (Test-Path $holdPath)) { Write-Host 'Hold released before it started.'; return }
        try { $owned = $mutex.WaitOne(2000) }
        catch [System.Threading.AbandonedMutexException] { $owned = $true }
    }
    $info = [ordered]@{ pid = $PID; what = "HOLD ($Reason); delete $holdPath to release"; user = $env:USERNAME
                        startedUtc = (Get-Date).ToUniversalTime().ToString('o'); command = [Environment]::CommandLine }
    [IO.File]::WriteAllText($lockInfoPath, ($info | ConvertTo-Json), $utf8)
    Write-Host "Holding the game-test lock. Delete $holdPath to release."
    while (Test-Path $holdPath) { Start-Sleep -Seconds 3 }
    Write-Host 'Released.'
}
finally {
    if ($owned) {
        try { if (Test-Path $lockInfoPath) { $h = Get-Content $lockInfoPath -Raw | ConvertFrom-Json; if ($h.pid -eq $PID) { Remove-Item $lockInfoPath -Force } } } catch { }
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
}

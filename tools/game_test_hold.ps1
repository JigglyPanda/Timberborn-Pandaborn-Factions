# Pauses the in-game test queue while the owner uses the PC.
#
#   powershell -ExecutionPolicy Bypass -File tools\game_test_hold.ps1          # hold until released
#   powershell -ExecutionPolicy Bypass -File tools\game_test_hold.ps1 -Release # release: queued runs carry on
#
# It takes the same named mutex every game test takes (after the run in progress, if any, has finished), so no new
# game window opens while it is held. Queued runs simply keep waiting; nothing is cancelled. A run already in the
# game is never interrupted.
#
# The hold is this process plus its own file, E:\PandabornDev\build\test\HOLD.<pid>.json (pid and start time inside).
# Deleting that file releases it (-Release deletes the file of every hold started with this script). Ending this
# process releases it too: a hold file whose process is gone is stale, and whoever sees it ignores and removes it.
# Several holds can be in force at once (another session's, the owner's tools\play_timberborn.ps1); each has its own
# file and none ends another. While any is in force, queued runs do not try for the lock.
param(
    [string]$TestRoot = 'E:\PandabornDev\build\test',
    [string]$Reason = 'the owner is using the PC',
    [switch]$Release,
    [string]$MutexName = 'Global\PandabornGameTest'   # for trials of this script on a scratch lock
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'game_lock.ps1')

if ($Release) {
    # only holds started by this script: the owner's play session (kind 'play') ends when their game closes
    $mine = @(Get-LiveHolds $TestRoot | Where-Object { $_.kind -eq 'hold' })
    foreach ($h in $mine) { Remove-Item -LiteralPath $h.path -Force; Write-Host "Released the hold of pid $($h.pid) ($($h.reason))." }
    if ($mine.Count -eq 0) { Write-Host 'No hold to release.' }
    return
}

$holdPath = New-HoldFile $TestRoot 'hold' $Reason
$mutex = New-Object System.Threading.Mutex($false, $MutexName)
$owned = $false
try {
    Write-Host "Waiting for the run in progress (if any) to finish..."
    while (-not $owned) {
        if (-not (Test-Path -LiteralPath $holdPath)) { Write-Host 'Hold released before it started.'; return }
        $owned = Enter-MutexNoWait $mutex 2000
    }
    Write-LockInfo $TestRoot "HOLD ($Reason); delete $holdPath to release"
    Write-Host "Holding the game-test lock. Delete $holdPath (or run this script with -Release) to release."
    while (Test-Path -LiteralPath $holdPath) { Start-Sleep -Seconds 3 }
    Write-Host 'Released.'
}
finally {
    # however this ends (released, Ctrl-C, an error), the hold is over: its file must not outlive it
    try { Remove-Item -LiteralPath $holdPath -Force -ErrorAction SilentlyContinue } catch { }
    if ($owned) {
        Remove-LockInfo $TestRoot
        try { $mutex.ReleaseMutex() } catch { }
    }
    $mutex.Dispose()
}

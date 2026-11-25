# For the owner: play Timberborn while the mod's automated tests are in use on this PC.
#
#   powershell -ExecutionPolicy Bypass -File tools\play_timberborn.ps1
#
# What it does, in order:
#   1. pauses the test queue (the same lock every test takes) and waits for the test that is in the game, if any, to
#      finish and put the mod on/off settings back (press S to stop that test and play at once);
#   2. checks that no test left mod settings changed, and removes the test harness from the Mods folder;
#   3. starts Timberborn through Steam, as usual;
#   4. when the game is closed, lets the tests carry on.
# Closing this window early is safe: tests never start while a Timberborn process is open.
param(
    [string]$TestRoot = 'E:\PandabornDev\build\test',
    [switch]$NoLaunch,   # only pause, check and wait: start the game yourself
    [double]$WaitMinutes = 10,
    [string]$MutexName = 'Global\PandabornGameTest'   # for testing this script
)
$ErrorActionPreference = 'Stop'
$holdPath = Join-Path $TestRoot 'HOLD'
$lockInfoPath = Join-Path $TestRoot 'gametest.lock.json'
$pendingPath = Join-Path $TestRoot 'modstate.pending.json'
$modsDir = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Timberborn\Mods'
$utf8 = New-Object System.Text.UTF8Encoding($false)
function Say([string]$text, [string]$color = 'Gray') { Write-Host $text -ForegroundColor $color }
# Test games run on a hidden desktop, so from here they have no window. A game with a window is the owner's: never touched.
function Get-HiddenGames { @(Get-Process Timberborn -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -eq [IntPtr]::Zero }) }

New-Item -ItemType Directory -Force $TestRoot | Out-Null
[IO.File]::WriteAllText($holdPath, "Game tests are held: the owner is playing Timberborn. Delete this file to release.`r`n", $utf8)
$mutex = New-Object System.Threading.Mutex($false, $MutexName)
$owned = $false
try {
    $told = $false
    while (-not $owned) {
        try { $owned = $mutex.WaitOne(1000) } catch [System.Threading.AbandonedMutexException] { $owned = $true }
        if ($owned) { break }
        if (-not $told) {
            $what = '(a test)'
            try { $what = (Get-Content $lockInfoPath -Raw | ConvertFrom-Json).what } catch { }
            Say "A test is using the game right now: $what" 'Yellow'
            Say 'Waiting for it to finish (it runs out of sight). Press S to stop that test and play now.' 'Yellow'
            $told = $true
        }
        $key = $null
        try { if ([Console]::KeyAvailable) { $key = [Console]::ReadKey($true) } } catch { }
        if ($key -and $key.Key -eq 'S') {
            Say 'Stopping the test game; the test will put the mod settings back...' 'Yellow'
            if ($MutexName -eq 'Global\PandabornGameTest') { Get-HiddenGames | Stop-Process -Force -ErrorAction SilentlyContinue }
        }
    }
    $info = [ordered]@{ pid = $PID; what = "HOLD (the owner is playing Timberborn)"; user = $env:USERNAME
                        startedUtc = (Get-Date).ToUniversalTime().ToString('o'); command = [Environment]::CommandLine }
    [IO.File]::WriteAllText($lockInfoPath, ($info | ConvertTo-Json), $utf8)

    # a test game that somehow outlived its run must not be mistaken for the owner's
    # (only with the real lock in hand: under a scratch lock a hidden game is a test in progress, not a leftover)
    $left = @(); if ($MutexName -eq 'Global\PandabornGameTest') { $left = @(Get-HiddenGames) }
    if ($left.Count -gt 0) { $left | Stop-Process -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 3 }

    if (Test-Path $pendingPath) {
        Say 'A test did not confirm that it put the mod settings back. Restoring them now...' 'Yellow'
        & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'run_game_test.ps1') -RestoreModState $pendingPath -DuringHold
        if (Test-Path $pendingPath) {
            # not "your mod settings are as you left them", and no game: it would start with the test's mod settings
            Say "Could not confirm the restore. Timberborn was not started. Do not change mods yet; ask Claude. ($pendingPath)" 'Red'
            return
        }
    }
    $harness = Join-Path $modsDir 'PandabornDevHarness'
    if (Test-Path $harness) {
        $item = Get-Item -LiteralPath $harness -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { cmd /c rmdir "`"$harness`"" | Out-Null }   # the link only, not its target
    }
    Say 'Tests are paused and your mod settings are as you left them.' 'Green'

    if ($NoLaunch) { Say 'Start Timberborn now. Tests stay paused until the game has been opened and closed.' 'Cyan' }
    else { Say 'Starting Timberborn through Steam...' 'Cyan'; Start-Process 'steam://rungameid/1062090' }

    $seen = $false
    $waitUntil = (Get-Date).AddMinutes($WaitMinutes)
    while ($true) {
        $running = @(Get-Process Timberborn -ErrorAction SilentlyContinue).Count -gt 0
        if ($running) { if (-not $seen) { Say 'Timberborn is running. Have fun; tests carry on when you close it.' 'Green' }; $seen = $true }
        elseif ($seen) {
            Start-Sleep -Seconds 8   # Steam may restart the game once at launch
            if (@(Get-Process Timberborn -ErrorAction SilentlyContinue).Count -eq 0) { break }
        }
        elseif ((Get-Date) -gt $waitUntil) { Say "Timberborn did not start within $WaitMinutes minutes." 'Yellow'; break }
        Start-Sleep -Seconds 3
    }
}
finally {
    try { Remove-Item -LiteralPath $holdPath -Force -ErrorAction SilentlyContinue } catch { }
    if ($owned) {
        try { if (Test-Path $lockInfoPath) { $h = Get-Content $lockInfoPath -Raw | ConvertFrom-Json; if ($h.pid -eq $PID) { Remove-Item $lockInfoPath -Force } } } catch { }
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
    Say 'Tests can carry on now. You can close this window.' 'Green'
}

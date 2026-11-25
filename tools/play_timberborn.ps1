# For the owner: play Timberborn while the mod's automated tests are in use on this PC.
#
#   powershell -ExecutionPolicy Bypass -File tools\play_timberborn.ps1
#
# What it does, in order:
#   1. pauses the test queue (the same lock every test takes) and waits for the test that is in the game, if any, to
#      finish and put the mod on/off settings back (press S to stop that test's game and play at once);
#   2. cleans up after a test that died (its game, its mod settings, its links in the Mods folder, its save), checks
#      that no test left mod settings changed, and removes the test harness from the Mods folder;
#   3. starts Timberborn through Steam, as usual;
#   4. when the game is closed, lets the tests carry on.
#
# The only game this script ever stops is the test game written down by the test itself (process id and start time
# in <TestRoot>\run.pending.json). A game you started is never touched, with or without a window.
#
# Closing this window early ends the pause; it does not harm anything. The pause is this window: its file
# (<TestRoot>\HOLD.<pid>.json) is ignored and removed by the tests once the window is gone. Tests do not start while a
# Timberborn process is open, and a test that was starting stops its own game as soon as yours appears. If you close
# the window before your game is up (Steam still launching), a test may start in that gap and end itself a few
# seconds later with "could not test"; keep the window open until the game has closed to avoid that.
param(
    [string]$TestRoot = 'E:\PandabornDev\build\test',
    [switch]$NoLaunch,   # only pause, check and wait: start the game yourself
    [double]$WaitMinutes = 10,
    [string]$MutexName = 'Global\PandabornGameTest'   # for trials of this script on a scratch lock (with a scratch -TestRoot)
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'game_lock.ps1')
$recordPath = Join-Path $TestRoot 'run.pending.json'
$pendingPath = Join-Path $TestRoot 'modstate.pending.json'
$modsDir = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Timberborn\Mods'
# a trial on a scratch lock must not act on the real test folder or the real Mods folder
$scratch = ($MutexName -ne 'Global\PandabornGameTest')
$realRoot = ([IO.Path]::GetFullPath($TestRoot).TrimEnd('\') -eq 'E:\PandabornDev\build\test')
$mayAct = -not ($scratch -and $realRoot)
function Say([string]$text, [string]$color = 'Gray') { Write-Host $text -ForegroundColor $color }

$holdPath = New-HoldFile $TestRoot 'play' 'the owner is playing Timberborn'
$mutex = New-Object System.Threading.Mutex($false, $MutexName)
$owned = $false
try {
    $told = $false
    while (-not $owned) {
        $owned = Enter-MutexNoWait $mutex 1000
        if ($owned) { break }
        if (-not $told) {
            $what = '(a test)'
            try { $what = (Read-JsonFile (Join-Path $TestRoot 'gametest.lock.json')).what } catch { }
            Say "A test is using the game right now: $what" 'Yellow'
            Say 'Waiting for it to finish (it runs out of sight). Press S to stop that test and play now.' 'Yellow'
            $told = $true
        }
        $key = $null
        try { if ([Console]::KeyAvailable) { $key = [Console]::ReadKey($true) } } catch { }
        if ($key -and $key.Key -eq 'S' -and $mayAct) {
            # the test wrote down its own game (pid and start time): that process and no other
            $stopped = Stop-RecordedGames (Read-RunRecord $recordPath) 'Timberborn' 5
            if ($stopped.killed.Count -gt 0) { Say "Stopped the test game (pid $($stopped.killed -join ', ')); the test will put the mod settings back..." 'Yellow' }
            else { Say 'That test has no game open right now (it is starting or finishing); still waiting for it.' 'Yellow' }
        }
    }
    Write-LockInfo $TestRoot 'HOLD (the owner is playing Timberborn)'

    # a test that died (closed window, timeout, reboot) left a record: its game, flags, junctions and save are cleaned
    # from it, by the test runner itself, under this hold
    if ($mayAct -and ((Test-Path -LiteralPath $recordPath) -or (Test-Path -LiteralPath $pendingPath))) {
        Say 'A test did not finish cleanly. Putting things back...' 'Yellow'
        & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'run_game_test.ps1') -Recover -DuringHold -TestRoot $TestRoot -MutexName $MutexName
        if ((Test-Path -LiteralPath $recordPath) -or (Test-Path -LiteralPath $pendingPath)) {
            # not "your mod settings are as you left them", and no game: it would start with the test's mod settings
            Say "Could not put everything back. Timberborn was not started. Do not change mods yet; ask Claude. ($recordPath, $pendingPath)" 'Red'
            return
        }
    }
    if (-not $scratch) {
        $harness = Join-Path $modsDir 'PandabornDevHarness'
        $item = Get-Item -LiteralPath $harness -Force -ErrorAction SilentlyContinue
        if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { cmd /c rmdir "`"$harness`"" | Out-Null }   # the link only, not its target
    }
    Say 'Tests are paused and your mod settings are as you left them.' 'Green'
    $already = @(Get-Process Timberborn -ErrorAction SilentlyContinue)
    if ($already.Count -gt 0) {
        Say "A Timberborn is already open (pid $($already.Id -join ', ')). If you did not start it, end it in Task Manager: tests stay paused while it runs." 'Yellow'
    }

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
        Remove-LockInfo $TestRoot
        try { $mutex.ReleaseMutex() } catch { }
    }
    $mutex.Dispose()
    Say 'Tests can carry on now. You can close this window.' 'Green'
}

# Trials of the lock, hold, pending-run and gate helpers, in a scratch folder with a scratch mutex.
#
#   powershell -ExecutionPolicy Bypass -File tools\tests\game_lock.trial.ps1 -Scratch <an empty folder outside the build tree>
#
# It never starts Timberborn, never takes Global\PandabornGameTest, never touches the Mods folder, the registry or
# E:\PandabornDev\build\test. The processes it starts and stops are its own PowerShell sleepers. The junctions it makes
# and removes are inside -Scratch. Functions of run_game_test.ps1 and pandaborn.ps1 are pulled out of the files by the
# parser and run alone (those scripts are never executed); proto\foundation\build.ps1 is run for real, with
# -ProtoRoot inside -Scratch. Exit code 0 when every trial passed.
param([Parameter(Mandatory = $true)][string]$Scratch)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Scratch = [IO.Path]::GetFullPath($Scratch).TrimEnd('\')
if ($Scratch -like 'E:\PandabornDev\build*' -or $Scratch -like '*\Timberborn\Mods*') { throw 'pick a scratch folder outside the build tree and the Mods folder' }
$work = Join-Path $Scratch ("trial-" + $PID)
New-Item -ItemType Directory -Force $work | Out-Null
. (Join-Path $repo 'tools\game_lock.ps1')
$mutexName = "Local\PandabornTrial$PID"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$script:fails = 0; $script:passes = 0
function Check([string]$what, [bool]$ok, [string]$detail = '') {
    if ($ok) { $script:passes++; Write-Host "  ok    $what" } else { $script:fails++; Write-Host "  FAIL  $what  $detail" -ForegroundColor Red }
}
function Get-Fn([string]$file, [string]$name) {
    $t = $null; $e = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $repo $file), [ref]$t, [ref]$e)
    if ($e.Count) { throw "$file does not parse: $($e[0])" }
    $fn = $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true) | Select-Object -First 1
    if (-not $fn) { throw "no function $name in $file" }
    return $fn.Extent.Text
}
# a PowerShell child that does something with the shared helpers and then sleeps; returns the process
function Start-Helper([string]$body, [int]$seconds = 60) {
    $lib = Join-Path $repo 'tools\game_lock.ps1'
    $script = Join-Path $work ("helper-" + [guid]::NewGuid().ToString('N') + '.ps1')
    [IO.File]::WriteAllText($script, ". '$lib'`r`n$body`r`nStart-Sleep -Seconds $seconds`r`n", $utf8)
    return (Start-Process powershell -PassThru -WindowStyle Hidden -RedirectStandardError "$script.err" -RedirectStandardOutput "$script.out" `
            -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$script`"")   # Start-Process does not quote a path with a space
}
function Wait-For([scriptblock]$test, [int]$seconds = 20) {
    for ($i = 0; $i -lt $seconds * 5; $i++) { if (& $test) { return $true }; Start-Sleep -Milliseconds 200 }
    return $false
}
$helpers = @()
try {
    # ------------------------------------------------------------ parse
    Write-Host 'parse'
    foreach ($f in 'tools\game_lock.ps1', 'tools\run_game_test.ps1', 'tools\game_test_hold.ps1', 'tools\play_timberborn.ps1', 'tools\pandaborn.ps1', 'proto\foundation\build.ps1') {
        $t = $null; $e = $null
        $null = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $repo $f), [ref]$t, [ref]$e)
        Check "$f parses" ($e.Count -eq 0) ($e | Select-Object -First 1)
    }

    # ------------------------------------------------------------ pid + start time, paths, json
    Write-Host 'pid and start time'
    $me = Get-ProcessStartUtc $PID
    Check 'own process matches its pid and start time' (Test-SameProcess $PID $me)
    Check 'same pid, another start time: not the same process' (-not (Test-SameProcess $PID ((Get-Date).AddDays(-1).ToUniversalTime().ToString('o'))))
    Check 'same pid, no start time: not the same process' (-not (Test-SameProcess $PID $null))
    Check 'a pid nobody has: not the same process' (-not (Test-SameProcess 999999 $me))
    Check 'right pid and time, wrong process name: no' (-not (Test-SameProcess $PID $me 'Timberborn'))
    Check 'start time survives as a DateTime too' (Test-SameProcess $PID ([datetime]::Parse($me, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind)))
    Write-Host 'paths'
    Check 'a folder inside the root is under it' (Test-PathUnder (Join-Path $work 'a\b') $work)
    Check 'the root itself is not under it' (-not (Test-PathUnder $work $work))
    Check 'a sibling with the same prefix is not under it' (-not (Test-PathUnder ($work + 'x\a') $work))
    Check '..\ out of the root is not under it' (-not (Test-PathUnder (Join-Path $work 'a\..\..\b') $work))
    Check 'an empty path is not under it' (-not (Test-PathUnder '' $work))
    $jf = Join-Path $work 'roundtrip.json'
    $word = 'M' + [char]0xE9 + 'x ' + [char]0x2013 + ' ' + [char]0x718A
    Write-JsonFile $jf ([ordered]@{ name = $word; list = @(1) })
    $back = Read-JsonFile $jf
    Check 'json written and read back as UTF-8 (non-ASCII kept)' ($back.name -eq $word)
    Check 'an unreadable json file reads as nothing' ($null -eq (Read-JsonFile (Join-Path $work 'missing.json')))

    # ------------------------------------------------------------ holds
    Write-Host 'holds'
    $root = Join-Path $work 'test'; New-Item -ItemType Directory -Force $root | Out-Null
    Check 'no hold file: no hold' (@(Get-LiveHolds $root).Count -eq 0)
    [IO.File]::WriteAllText((Join-Path $root 'HOLD'), 'old format', $utf8)
    Check 'a file plainly named HOLD (old format) is not a hold' (@(Get-LiveHolds $root).Count -eq 0)
    $dead = Join-Path $root 'HOLD.999999.json'
    Write-JsonFile $dead ([ordered]@{ pid = 999999; processStartedUtc = $me; kind = 'hold'; reason = 'dead' })
    Check 'a hold whose process is gone is not a hold' (@(Get-LiveHolds $root).Count -eq 0)
    Check '... and its file is removed on sight' (-not (Test-Path $dead))
    $reused = Join-Path $root 'HOLD.777.json'
    Write-JsonFile $reused ([ordered]@{ pid = $PID; processStartedUtc = (Get-Date).AddDays(-2).ToUniversalTime().ToString('o'); kind = 'hold'; reason = 'pid reused' })
    Check 'a hold with a live pid but another start time is stale' ((@(Get-LiveHolds $root).Count -eq 0) -and -not (Test-Path $reused))
    $young = Join-Path $root 'HOLD.5.json'; [IO.File]::WriteAllText($young, '', $utf8)
    $null = Get-LiveHolds $root
    Check 'an unreadable hold file just written is left alone' (Test-Path $young)
    (Get-Item $young).LastWriteTime = (Get-Date).AddMinutes(-5); $null = Get-LiveHolds $root
    Check '... and removed once it is old' (-not (Test-Path $young))
    $mine = New-HoldFile $root 'play' 'trial: the owner'
    Check 'own hold is in force' (@(Get-LiveHolds $root).Count -eq 1)
    # a second holder, in its own process, that takes the scratch lock like game_test_hold.ps1 does
    $holder = Start-Helper @"
`$h = New-HoldFile '$root' 'hold' 'trial: an agent'
`$m = New-Object System.Threading.Mutex(`$false, '$mutexName')
`$null = Enter-MutexNoWait `$m 5000
Write-LockInfo '$root' 'HOLD (trial)'
[IO.File]::WriteAllText('$work\holder.ready', 'x')
"@
    $helpers += $holder
    Check 'the second holder came up' (Wait-For { Test-Path "$work\holder.ready" }) ((Get-ChildItem $work -Filter 'helper-*.err' | Get-Content -ErrorAction SilentlyContinue | Select-Object -First 6) -join ' | ')
    Check 'two holders: two holds in force, one file each' (@(Get-LiveHolds $root).Count -eq 2)
    $owns = Test-HoldOwnsLock $root $mutexName
    Check 'a live hold that owns the lock is recognised' ($owns.ok) $owns.why
    Remove-Item -LiteralPath $mine -Force
    Check 'one holder leaves: the other hold stays in force' (@(Get-LiveHolds $root).Count -eq 1 -and (Test-HoldOwnsLock $root $mutexName).ok)
    $il = Enter-InstallLock $root $mutexName $false 'install trial'
    Check 'install without the lock: refused, and it names the holder' ((-not $il.ok) -and $il.why -match 'HOLD \(trial\)') $il.why
    $il = Enter-InstallLock $root $mutexName $true 'install trial'
    Check 'install with -CallerHoldsLock under a live hold: accepted, takes nothing' ($il.ok -and $null -eq $il.mutex) $il.why
    # the lock is taken, but by something that is not a hold (a test): -DuringHold and -CallerHoldsLock must refuse
    $mine = New-HoldFile $root 'hold' 'trial: waiting behind a test'
    $info = Read-JsonFile (Join-Path $root 'gametest.lock.json')
    Write-JsonFile (Join-Path $root 'gametest.lock.json') ([ordered]@{ pid = 4; processStartedUtc = $me; what = 'Inkpaws test' })
    $owns = Test-HoldOwnsLock $root $mutexName
    Check 'a hold file while a test owns the lock: the hold is not in effect yet' (-not $owns.ok) $owns.why
    Write-JsonFile (Join-Path $root 'gametest.lock.json') $info
    Remove-Item -LiteralPath $mine -Force
    # the holder is killed: its file and the holder file stay behind, the lock is abandoned
    Stop-Process -Id $holder.Id -Force; $null = $holder.WaitForExit(5000)
    Check 'holder killed: its hold file is stale and nothing is held' (@(Get-LiveHolds $root).Count -eq 0)
    Check '... the stale file was removed' (@(Get-ChildItem $root -Filter 'HOLD.*.json').Count -eq 0)
    $mine = New-HoldFile $root 'hold' 'trial: file only'
    $owns = Test-HoldOwnsLock $root $mutexName
    Check 'a hold file with nobody on the lock is not a hold in effect' (-not $owns.ok) $owns.why
    Remove-Item -LiteralPath $mine -Force
    $il = Enter-InstallLock $root $mutexName $true 'install trial'
    Check 'install with -CallerHoldsLock and no hold: refused' (-not $il.ok) $il.why
    $il = Enter-InstallLock $root $mutexName $false 'install trial'
    Check 'install takes a free (abandoned) lock and writes the holder file' ($il.ok -and (Read-JsonFile (Join-Path $root 'gametest.lock.json')).what -eq 'install trial') $il.why
    $probe = New-Object System.Threading.Mutex($false, $mutexName)
    $again = Enter-MutexNoWait $probe
    Check 'while install holds it, the lock is ours (same thread re-enters)' $again
    if ($again) { $probe.ReleaseMutex() }; $probe.Dispose()
    Exit-InstallLock $il $root
    Check 'install releases the lock and removes its holder file' (-not (Test-Path (Join-Path $root 'gametest.lock.json')))

    # ------------------------------------------------------------ the pending-run record
    Write-Host 'pending-run record'
    $recPath = Join-Path $root 'run.pending.json'
    $game = Start-Helper '' 120; $helpers += $game
    $other = Start-Helper '' 120; $helpers += $other
    $null = Wait-For { (Get-ProcessStartUtc $game.Id) -and (Get-ProcessStartUtc $other.Id) }
    $mods = Join-Path $work 'Mods'; $saves = Join-Path $work 'Saves'; $targets = Join-Path $work 'targets'
    foreach ($d in $mods, $saves, "$targets\harness", "$targets\extra", "$targets\elsewhere", "$targets\gone", "$mods\RealMod", "$saves\PB_AutoTest_trial", "$saves\MySettlement", "$root\run1") { New-Item -ItemType Directory -Force $d | Out-Null }
    [IO.File]::WriteAllText("$targets\harness\keep.txt", 'x', $utf8); [IO.File]::WriteAllText("$mods\RealMod\keep.txt", 'x', $utf8)
    [IO.File]::WriteAllText("$saves\PB_AutoTest_trial\a.timber", 'x', $utf8); [IO.File]::WriteAllText("$saves\MySettlement\a.timber", 'x', $utf8)
    New-Item -ItemType Junction -Path "$mods\PandabornDevHarness" -Target "$targets\harness" | Out-Null
    New-Item -ItemType Junction -Path "$mods\pbgate-trial" -Target "$targets\extra" | Out-Null
    New-Item -ItemType Junction -Path "$mods\Repointed" -Target "$targets\elsewhere" | Out-Null
    New-Item -ItemType Junction -Path "$mods\Dangling" -Target "$targets\gone" | Out-Null
    Remove-Item "$targets\gone" -Force
    New-Item -ItemType Junction -Path "$work\OutsideMods" -Target "$targets\extra" | Out-Null
    [IO.File]::WriteAllText("$root\run1\request.in.json", '{}', $utf8); [IO.File]::WriteAllText("$root\request.json", '{}', $utf8)
    [IO.File]::WriteAllText("$work\request.json", '{}', $utf8); [IO.File]::WriteAllText("$root\run1\result.json", '{}', $utf8)
    $record = [ordered]@{
        runId = 'run1'; runDir = "$root\run1"
        runner = [ordered]@{ pid = 999999; processStartedUtc = $me }
        games = @([ordered]@{ pid = $game.Id; processStartedUtc = (Get-ProcessStartUtc $game.Id) },
                  [ordered]@{ pid = $other.Id; processStartedUtc = (Get-Date).AddHours(-3).ToUniversalTime().ToString('o') },   # pid reused by somebody else
                  [ordered]@{ pid = $PID; processStartedUtc = $null })                                                        # start time never read
        junctions = @([ordered]@{ path = "$mods\PandabornDevHarness"; target = "$targets\harness" }, [ordered]@{ path = "$mods\pbgate-trial"; target = "$targets\extra" },
                      [ordered]@{ path = "$mods\Repointed"; target = "$targets\extra" }, [ordered]@{ path = "$mods\RealMod"; target = "$targets\extra" },
                      [ordered]@{ path = "$mods\Dangling"; target = "$targets\gone" }, [ordered]@{ path = "$work\OutsideMods"; target = "$targets\extra" },
                      [ordered]@{ path = "$mods\NeverMade"; target = "$targets\extra" })
        save = "$saves\PB_AutoTest_trial"
        requests = @("$root\run1\request.in.json", "$root\request.json", "$work\request.json", "$root\run1\result.json")
    }
    Write-JsonFile $recPath $record
    $rec = Read-RunRecord $recPath
    Check 'record written and read back' ($rec.runId -eq 'run1' -and @($rec.junctions).Count -eq 7)
    Check 'a record whose runner is gone: runner not alive' (-not (Test-RunnerAlive $rec))
    Check 'a record of this very process: runner alive' (Test-RunnerAlive ([pscustomobject]@{ runner = [pscustomobject]@{ pid = $PID; processStartedUtc = $me } }))
    $stopped = Stop-RecordedGames $rec 'powershell' 15
    Check 'the recorded game (pid and start time) is stopped' ($stopped.killed -contains $game.Id -and $game.HasExited)
    Check 'a recorded pid with another start time is NOT stopped' ((-not $other.HasExited) -and $stopped.killed -notcontains $other.Id)
    Check 'a recorded pid without a start time is NOT stopped (this process is still here)' ($stopped.killed -notcontains $PID)
    Check 'nothing recorded is still alive afterwards' ($stopped.alive.Count -eq 0)
    $none = Stop-RecordedGames $rec 'Timberborn' 0
    Check 'with the real process name, nothing of ours matches (name is part of the check)' ($none.killed.Count -eq 0)
    Check 'no record: nothing to stop' ((Stop-RecordedGames $null 'powershell' 0).killed.Count -eq 0)
    $j = Remove-RecordedJunctions $rec $mods
    Check 'recorded junctions with the recorded target are removed' ((-not (Get-Item "$mods\PandabornDevHarness" -Force -ErrorAction SilentlyContinue)) -and -not (Get-Item "$mods\pbgate-trial" -Force -ErrorAction SilentlyContinue)) ($j.skipped -join '; ')
    Check '... the link only: the target and its files are untouched' (Test-Path "$targets\harness\keep.txt")
    Check 'a junction that now points elsewhere is left alone' ([bool](Get-Item "$mods\Repointed" -Force -ErrorAction SilentlyContinue))
    Check 'a real folder with a recorded name is left alone' (Test-Path "$mods\RealMod\keep.txt")
    Check 'a junction outside the Mods folder is left alone' ([bool](Get-Item "$work\OutsideMods" -Force -ErrorAction SilentlyContinue))
    Check 'a recorded junction whose target is gone is removed too' (-not (Get-Item "$mods\Dangling" -Force -ErrorAction SilentlyContinue)) ($j.skipped -join '; ')
    Check 'three removed, three skipped with a reason, one never made' ($j.removed.Count -eq 3 -and $j.skipped.Count -eq 3) "removed $($j.removed.Count), skipped $($j.skipped.Count)"
    $s = Remove-RecordedSave $rec $saves
    Check 'the recorded test save is deleted' ($s -and -not (Test-Path "$saves\PB_AutoTest_trial"))
    Check 'another settlement is untouched' (Test-Path "$saves\MySettlement\a.timber")
    Check 'a recorded save that is not PB_AutoTest_* is refused' ($null -eq (Remove-RecordedSave ([pscustomobject]@{ save = "$saves\MySettlement" }) $saves) -and (Test-Path "$saves\MySettlement"))
    Check 'a recorded save outside the Saves folder is refused' ($null -eq (Remove-RecordedSave ([pscustomobject]@{ save = "$work\PB_AutoTest_x" }) $saves))
    $r = @(Remove-RecordedRequests $rec $root)
    Check 'recorded request files inside the test root are deleted' ($r.Count -eq 2 -and -not (Test-Path "$root\run1\request.in.json") -and -not (Test-Path "$root\request.json"))
    Check 'a request path outside the test root, and a file that is not a request, stay' ((Test-Path "$work\request.json") -and (Test-Path "$root\run1\result.json"))

    # ------------------------------------------------------------ run_game_test.ps1 (functions pulled out)
    Write-Host 'run_game_test.ps1 functions'
    function Say([string]$text, [string]$color = 'Gray') { $script:said += $text }
    $restorePattern = '^(Screenmanager |UnitySelectMonitor)'
    foreach ($fn in 'Test-IsTestGame', 'Get-TestProcesses', 'Get-OwnerGames', 'Format-PrefValue', 'ConvertTo-PrefRecord', 'ConvertFrom-PrefRecord', 'Get-WindowPrefPlan', 'Save-RunRecord', 'Clear-DeadRun') {
        . ([scriptblock]::Create((Get-Fn 'tools\run_game_test.ps1' $fn)))
    }
    $self = Get-Process -Id $PID
    $script:testGames = @(@{ pid = $PID; processStartedUtc = $me })
    Check 'a game with our pid and start time is ours' (Test-IsTestGame $self)
    $script:testGames = @(@{ pid = $PID; processStartedUtc = (Get-Date).AddDays(-1).ToUniversalTime().ToString('o') })
    Check 'a game with our pid and another start time is not ours' (-not (Test-IsTestGame $self))
    $script:testGames = @()
    Check 'before any launch nothing is ours' (-not (Test-IsTestGame $self))
    $Visible = $false
    $real = @(Get-Process Timberborn -ErrorAction SilentlyContinue).Count
    Check "hidden run, no launch: no test process; every Timberborn open ($real) is somebody else's" (@(Get-TestProcesses (Get-Date).AddDays(-30)).Count -eq 0 -and @(Get-OwnerGames).Count -eq $real)
    # window prefs: record rows and the plan, on made-up snapshots (no registry)
    $DWord = [Microsoft.Win32.RegistryValueKind]::DWord; $Binary = [Microsoft.Win32.RegistryValueKind]::Binary
    $before = @{
        'Screenmanager Resolution Width_h1'  = @{ Kind = $DWord; Value = 2560 }
        'Screenmanager Resolution Height_h2' = @{ Kind = $DWord; Value = 1440 }
        'Screenmanager Fullscreen mode_h3'   = @{ Kind = $DWord; Value = 1 }
        'UnitySelectMonitor_h4'              = @{ Kind = $Binary; Value = [byte[]](1, 2, 3) }
        'ModEnabled.Local.X.Y_h5'            = @{ Kind = $DWord; Value = 1 }
    }
    $rows = @(ConvertTo-PrefRecord $before)
    $rowsBack = @(($rows | ConvertTo-Json -Depth 4 | ConvertFrom-Json))
    Check 'window prefs recorded: the four window values, no mod flag' ($rows.Count -eq 4 -and -not ($rows | Where-Object { $_.name -like 'ModEnabled*' }))
    $bin = ConvertFrom-PrefRecord ($rowsBack | Where-Object { $_.name -eq 'UnitySelectMonitor_h4' })
    Check 'a binary value survives the record' (($bin.Value -join ',') -eq '1,2,3' -and $bin.Kind -eq $Binary)
    $after = @{
        'Screenmanager Resolution Width_h1'  = @{ Kind = $DWord; Value = 1280 }
        'Screenmanager Resolution Height_h2' = @{ Kind = $DWord; Value = 720 }
        'Screenmanager Fullscreen mode_h3'   = @{ Kind = $DWord; Value = 3 }
        'UnitySelectMonitor_h4'              = @{ Kind = $Binary; Value = [byte[]](1, 2, 3) }
        'Screenmanager New_h9'               = @{ Kind = $DWord; Value = 7 }
        'ModEnabled.Local.X.Y_h5'            = @{ Kind = $DWord; Value = 0 }
    }
    $plan = @(Get-WindowPrefPlan $rowsBack $after 1280 720)
    Check 'registry still at the test size: three values set back, the new one deleted, the unchanged and the mod flag left' (
        @($plan | Where-Object { $_.action -eq 'set' }).Count -eq 3 -and @($plan | Where-Object { $_.action -eq 'delete' }).name -eq 'Screenmanager New_h9' -and -not ($plan | Where-Object { $_.name -like 'ModEnabled*' -or $_.name -like 'UnitySelect*' })) (($plan | ForEach-Object { "$($_.action) $($_.name)" }) -join '; ')
    $w = $plan | Where-Object { $_.name -like '*Width*' }
    Check '... the width goes back to the owner''s 2560' ($w.entry.Value -eq 2560 -and $w.entry.Kind -eq $DWord)
    $after['Screenmanager Resolution Width_h1'].Value = 1920
    Check 'the owner changed the size since: nothing is planned' (@(Get-WindowPrefPlan $rowsBack $after 1280 720).Count -eq 0)
    Check 'a fullscreen run recorded no size: nothing is planned' (@(Get-WindowPrefPlan $rowsBack $after $null $null).Count -eq 0)
    # Clear-DeadRun, with the registry steps replaced by stand-ins
    if ($real -gt 0) { Write-Host '  (skipped: Clear-DeadRun refuses while a Timberborn process is open, and one is; that refusal is what it should do)' }
    else {
        $script:restoreCalls = 0; $script:prefCalls = 0; $script:said = @()
        function Restore-ModState($state) { $script:restoreCalls++; return [ordered]@{ ok = $script:restoreOk; entries = @([ordered]@{ name = 'n'; match = $script:restoreOk; before = 'DWord 1'; afterRestore = 'DWord 1' }) } }
        function Restore-WindowPrefs($rows, $width, $height) { $script:prefCalls++; return @('Screenmanager Resolution Width_h1') }
        $TestRoot = $root; $modsDir = $mods; $savesDir = $saves; $runRecordPath = $recPath; $pendingStatePath = Join-Path $root 'modstate.pending.json'
        New-Item -ItemType Directory -Force "$saves\PB_AutoTest_trial2", "$root\run2" | Out-Null
        New-Item -ItemType Junction -Path "$mods\PandabornDevHarness" -Target "$targets\harness" | Out-Null
        [IO.File]::WriteAllText("$root\run2\request.in.json", '{}', $utf8)
        $rec2 = [ordered]@{ runId = 'run2'; runner = [ordered]@{ pid = 999999; processStartedUtc = $me }; games = @()
                            junctions = @([ordered]@{ path = "$mods\PandabornDevHarness"; target = "$targets\harness" }); save = "$saves\PB_AutoTest_trial2"
                            requests = @("$root\run2\request.in.json"); windowPrefs = $rows; window = [ordered]@{ width = 1280; height = 720 } }
        Write-JsonFile $recPath $rec2
        Write-JsonFile $pendingStatePath ([ordered]@{ runId = 'run2'; entries = @() })
        $script:restoreOk = $false
        $ok = Clear-DeadRun (Read-RunRecord $recPath)
        Check 'flags not verified: clean-up reports failure, record and pending file stay' ((-not $ok) -and (Test-Path $recPath) -and (Test-Path $pendingStatePath))
        Check '... the junction, save and request went all the same' ((-not (Get-Item "$mods\PandabornDevHarness" -Force -ErrorAction SilentlyContinue)) -and -not (Test-Path "$saves\PB_AutoTest_trial2") -and -not (Test-Path "$root\run2\request.in.json"))
        $script:restoreOk = $true
        $ok = Clear-DeadRun (Read-RunRecord $recPath)
        Check 'second pass, flags verified: done; record and pending file removed' ($ok -and -not (Test-Path $recPath) -and -not (Test-Path $pendingStatePath))
        Check 'flags went through the restore path both times, window prefs too' ($script:restoreCalls -eq 2 -and $script:prefCalls -eq 2)
        Write-JsonFile $recPath $rec2
        Write-JsonFile $pendingStatePath ([ordered]@{ runId = 'another-run'; entries = @() })
        $ok = Clear-DeadRun (Read-RunRecord $recPath)
        Check 'a pending flag file of another run is not restored by this record, and stays' ($ok -and $script:restoreCalls -eq 2 -and (Test-Path $pendingStatePath))
        Remove-Item $pendingStatePath -Force
    }

    # ------------------------------------------------------------ pandaborn.ps1 (functions pulled out)
    Write-Host 'pandaborn.ps1 functions'
    foreach ($fn in 'Copy-IfChanged', 'Sync-Tree', 'Get-TreeHash', 'Get-GameVersion', 'Get-PrunableGateCopies', 'Remove-GateCopies') {
        . ([scriptblock]::Create((Get-Fn 'tools\pandaborn.ps1' $fn)))
    }
    $buildRoot = Join-Path $work 'build'
    $src = Join-Path $work 'src'; New-Item -ItemType Directory -Force "$src\Scripts", "$src\Modules", "$src\AssetBundles", "$src\Buildings", "$buildRoot\stage\Mod" | Out-Null
    [IO.File]::WriteAllText("$src\manifest.json", '{ "Id": "JigglyPanda.PandabornFactions", "Name": "Pandaborn - Factions" }', $utf8)
    [IO.File]::WriteAllText("$src\Scripts\Pandaborn.Bootstrap.dll", 'dll', $utf8); [IO.File]::WriteAllText("$src\Modules\modules.txt", "Bell  Pandaborn.Bell.bin`n", $utf8)
    [IO.File]::WriteAllText("$src\Modules\Pandaborn.Bell.bin", 'bell', $utf8); [IO.File]::WriteAllText("$src\AssetBundles\pandabornlook_win", 'look', $utf8)
    [IO.File]::WriteAllText("$src\Buildings\Den.blueprint.json", '{}', $utf8)
    $map = [ordered]@{}; foreach ($f in Get-ChildItem $src -Recurse -File) { $map[$f.FullName.Substring($src.Length + 1)] = $f.FullName }
    [IO.File]::WriteAllText("$buildRoot\stage\Mod\stale.txt", 'x', $utf8)
    $outside = Join-Path $work 'OwnersMods'; New-Item -ItemType Directory -Force $outside | Out-Null; [IO.File]::WriteAllText("$outside\precious.txt", 'x', $utf8)
    $threw = $false; try { $null = Sync-Tree $outside $map } catch { $threw = $true }
    Check 'Sync-Tree refuses a target outside the build root, and deletes nothing there' ($threw -and (Test-Path "$outside\precious.txt") -and @(Get-ChildItem $outside).Count -eq 1)
    $threw = $false; try { $null = Sync-Tree $buildRoot $map } catch { $threw = $true }
    Check 'Sync-Tree refuses the build root itself' $threw
    $r = Sync-Tree "$buildRoot\stage\Mod" $map
    Check 'Sync-Tree mirrors into a folder inside the build root (stale file removed)' ($r.files -eq 6 -and -not (Test-Path "$buildRoot\stage\Mod\stale.txt") -and (Test-Path "$buildRoot\stage\Mod\Scripts\Pandaborn.Bootstrap.dll"))
    $stage = "$buildRoot\stage\Mod"
    Check 'two copies of a tree in different folders hash alike' ((Get-TreeHash $src) -eq (Get-TreeHash $stage))
    $parts = @('scripts\', 'modules\', 'assetbundles\')
    $codeBefore = Get-TreeHash $stage $parts
    [IO.File]::WriteAllText("$stage\Buildings\Den.blueprint.json", '{ "x": 1 }', $utf8)
    Check 'the code hash ignores a data file' ((Get-TreeHash $stage $parts) -eq $codeBefore)
    Check '... which the whole-tree hash sees' ((Get-TreeHash $src) -ne (Get-TreeHash $stage))
    [IO.File]::WriteAllText("$stage\Buildings\Den.blueprint.json", '{}', $utf8)
    [IO.File]::WriteAllText("$stage\Modules\modules.txt", "Bell  Pandaborn.Bell.bin`nWater  Pandaborn.Water.bin`n", $utf8)
    Check 'the code hash sees a changed modules.txt' ((Get-TreeHash $stage $parts) -ne $codeBefore)
    [IO.File]::WriteAllText("$stage\Modules\modules.txt", "Bell  Pandaborn.Bell.bin`n", $utf8)
    [IO.File]::WriteAllText("$stage\manifest.json", '{ "Id": "Other" }', $utf8)
    Check 'a skipped file does not count' ((Get-TreeHash $src @() @('manifest.json')) -eq (Get-TreeHash $stage @() @('manifest.json')) -and (Get-TreeHash $src) -ne (Get-TreeHash $stage))
    Copy-Item "$src\manifest.json" "$stage\manifest.json" -Force
    $fakeGame = Join-Path $work 'steamapps\common\Timberborn'; New-Item -ItemType Directory -Force "$fakeGame\Timberborn_Data\StreamingAssets" | Out-Null
    [IO.File]::WriteAllText("$fakeGame\Timberborn_Data\StreamingAssets\VersionNumbers.json", '{ "CurrentVersion": "9.8.7.6" }', $utf8)
    [IO.File]::WriteAllText("$work\steamapps\appmanifest_1062090.acf", "`"AppState`"`n{`n`t`"appid`"`t`t`"1062090`"`n`t`"buildid`"`t`t`"4242`"`n}", $utf8)
    $gv = Get-GameVersion $fakeGame
    Check 'game version and Steam build are read from the game''s own files' ($gv.version -eq '9.8.7.6' -and $gv.steamBuild -eq '4242') "$($gv.version) / $($gv.steamBuild)"
    $gv = Get-GameVersion (Join-Path $work 'nowhere')
    Check 'no game there: no version (install then refuses any gate)' ($null -eq $gv.version)
    # gate copies
    $proto = Join-Path $buildRoot 'proto'; $fakeMods = Join-Path $work 'Mods2'
    foreach ($n in 'pbgate-AAAA0001', 'pbgate-BBBB0002', 'pbgate-CCCC0003', 'pbgate-DDDD0004', 'pbgate-EEEE0005', 'pbgate', 'pbfoundation', 'pbgate-notahash') { New-Item -ItemType Directory -Force "$proto\$n" | Out-Null; [IO.File]::WriteAllText("$proto\$n\f.bin", ('x' * 2000), $utf8) }
    New-Item -ItemType Directory -Force $fakeMods | Out-Null
    New-Item -ItemType Junction -Path "$fakeMods\pbgate-CCCC0003" -Target "$proto\pbgate-CCCC0003" | Out-Null     # a run has it loaded
    foreach ($n in 'pbgate-AAAA0001', 'pbgate-BBBB0002', 'pbgate-CCCC0003', 'pbgate-EEEE0005') { (Get-Item "$proto\$n").LastWriteTime = (Get-Date).AddDays(-2) }
    [IO.File]::WriteAllText("$proto\pbgate-BBBB0002.devcopy.json", '{}', $utf8)
    $old = @(Get-PrunableGateCopies $proto 'pbgate-AAAA0001' $fakeMods)
    Check 'prunable: old pbgate-<hash> copies only; not the current one, not one in Mods, not a young one, not other folders' ((($old.Name | Sort-Object) -join ',') -eq 'pbgate-BBBB0002,pbgate-EEEE0005') ($old.Name -join ',')
    $gone = @(Remove-GateCopies ($old + [pscustomobject]@{ Path = "$proto\pbfoundation" } + [pscustomobject]@{ Path = $outside }) $proto)
    Check 'prune removes those two and their .devcopy.json, nothing else' ($gone.Count -eq 2 -and -not (Test-Path "$proto\pbgate-BBBB0002") -and -not (Test-Path "$proto\pbgate-BBBB0002.devcopy.json") -and (Test-Path "$proto\pbfoundation\f.bin") -and (Test-Path "$outside\precious.txt") -and @(Get-ChildItem $proto -Directory).Count -eq 6)
    [IO.Directory]::Delete("$fakeMods\pbgate-CCCC0003", $false)

    # ------------------------------------------------------------ proto\foundation\build.ps1, run for real in the scratch folder
    Write-Host 'proto\foundation\build.ps1'
    $build = Join-Path $repo 'proto\foundation\build.ps1'
    # stderr of a child that refuses must not stop this script: run it with errors as output
    function Invoke-Build([string[]]$buildArgs) {
        $ErrorActionPreference = 'Continue'
        $o = & powershell -NoProfile -ExecutionPolicy Bypass -File $build @buildArgs 2>&1
        $script:buildExit = $LASTEXITCODE
        return $o
    }
    $sproto = Join-Path $work 'proto'; New-Item -ItemType Directory -Force $sproto, "$work\victim" | Out-Null
    [IO.File]::WriteAllText("$work\victim\precious.txt", 'x', $utf8); [IO.File]::WriteAllText("$sproto\other-lane.txt", 'x', $utf8)
    foreach ($bad in '', ' ', '..\victim', '..', '.', 'a\b', "$work\victim", 'C:', 'name.') {
        $out = Invoke-Build @('-Name', "`"$bad`"", '-Source', $src, '-Staged', '-ProtoRoot', $sproto)
        Check "-Name '$bad' is refused" ($script:buildExit -ne 0 -and (Test-Path "$work\victim\precious.txt") -and (Test-Path "$sproto\other-lane.txt")) ($out | Select-Object -Last 1)
    }
    New-Item -ItemType Directory -Force "$src\AssetBundles.parked" | Out-Null; [IO.File]::WriteAllText("$src\AssetBundles.parked\pandabornlook_win", 'parked', $utf8)
    $out = Invoke-Build @('-Name', 'pbgate-0BADF00D', '-Source', $src, '-Staged', '-ProtoRoot', $sproto)
    $copy = "$sproto\pbgate-0BADF00D"
    Check '-Staged builds the copy' ($script:buildExit -eq 0 -and (Test-Path "$copy\manifest.json")) ($out | Select-Object -Last 2)
    $info = Read-JsonFile "$copy.devcopy.json"
    Check 'the copy''s code is the source''s code, byte for byte (Scripts, Modules with modules.txt, AssetBundles)' ((Get-TreeHash $copy $parts) -eq (Get-TreeHash $src $parts) -and $info.codeHash -eq (Get-TreeHash $src $parts))
    Check 'nothing was added: no DevCarrier line, no probe, no fragment' ((Get-Content "$copy\Modules\modules.txt" -Raw) -eq (Get-Content "$src\Modules\modules.txt" -Raw) -and @(Get-ChildItem $copy -Recurse -File).Count -eq 6)
    Check 'only manifest.json differs, and the list of substitutions says so' ((Get-TreeHash $copy @() @('manifest.json')) -eq (Get-TreeHash $src @() @('manifest.json')) -and @($info.substitutions).Count -eq 1 -and $info.substitutions[0].file -eq 'manifest.json')
    Check 'the copy has the dev Id, the source keeps its own' ((Read-JsonFile "$copy\manifest.json").Id -eq 'JigglyPanda.PandabornFactionsDev' -and (Read-JsonFile "$src\manifest.json").Id -eq 'JigglyPanda.PandabornFactions')
    Check 'parked bundles are not copied' (-not (Test-Path "$copy\AssetBundles.parked"))
    Check 'the record lists the code files' ((@($info.codeFiles) -join ',') -eq 'AssetBundles\pandabornlook_win,Modules\modules.txt,Modules\Pandaborn.Bell.bin,Scripts\Pandaborn.Bootstrap.dll') (@($info.codeFiles) -join ',')
    $out = Invoke-Build @('-Name', 'pbgate-0BADF00D', '-Source', $copy, '-Staged', '-ProtoRoot', $sproto)
    Check 'a copy cannot be its own source' ($script:buildExit -ne 0 -and (Test-Path "$copy\manifest.json"))
}
finally {
    foreach ($h in $helpers) { try { if (-not $h.HasExited) { Stop-Process -Id $h.Id -Force } } catch { } }
    # the junctions made here go first (the link only), then the scratch tree
    foreach ($j in @(Get-ChildItem -LiteralPath $work -Recurse -Directory -Force -ErrorAction SilentlyContinue | Where-Object { $_.LinkType })) { try { [IO.Directory]::Delete($j.FullName, $false) } catch { } }
    Start-Sleep -Milliseconds 300
    Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host ''
Write-Host ("{0} passed, {1} failed" -f $script:passes, $script:fails) -ForegroundColor $(if ($script:fails) { 'Red' } else { 'Green' })
exit $(if ($script:fails) { 1 } else { 0 })

<#
.SYNOPSIS
  Automated in-game test. Launches Timberborn, lets the PandabornDevHarness mod start a new game as the given faction,
  run it, take screenshots and write result.json, then quits, scans the log and prints a verdict.

.DESCRIPTION
  Exit codes: 0 = pass, 1 = fail (a check failed, our mods logged errors, or the game crashed),
              2 = could not test (game already running, build/launch failure, timeout, harness never loaded).
  Output: E:\PandabornDev\build\test\<RunId>\ with request.json, result.json, summary.json, harness.log, Player.log, *.png.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -RunSeconds 60
.EXAMPLE
  tools\run_game_test.ps1 -Faction Inkpaws -InGameDays 2 -Speed 3 -Buildings 'LumberjackFlag.Folktails' -Checks @{ minChildren = 1 }
#>
[CmdletBinding()]
param(
    [string]$Faction = 'Folktails',
    [string]$Map = 'Diorama',
    [string]$GameMode = '',
    [double]$RunSeconds = 60,
    [double]$InGameDays = 0,
    [double]$InGameHours = 0,
    [double]$Speed = 3,
    # kind@at; kind = overview | screen | adult | child | bot; at = start | end | <real seconds after the run began>
    [string[]]$Screenshots = @('overview@start', 'adult@start', 'child@start', 'overview@end', 'screen@end'),
    # template names placed (finished) near the district center; use -RequestJson for offsets/unfinished
    [string[]]$Buildings = @(),
    # merged into request.checks, e.g. @{ minChildren = 1; adultTemplate = 'BeaverAdult.Folktails' }
    [hashtable]$Checks = @{},
    # a JSON file whose top-level keys override the generated request
    [string]$RequestJson = '',
    [switch]$NoDevMode,
    [switch]$Fullscreen,
    [int]$Width = 1280,
    [int]$Height = 720,
    [switch]$Sound,
    [int]$TimeoutSeconds = 600,
    [switch]$KeepSave,
    [switch]$NoBuild,
    # leave the Mods\PandabornDevHarness junction in place after the run (it is inert without a request)
    [switch]$KeepInstalled,
    # also fail on errors from other mods / the base game
    [switch]$StrictLog,
    [string[]]$OwnPatterns = @('PandabornFactions', 'PandabornDevHarness', 'Inkpaws'),
    [string]$RunId = '',
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Timberborn',
    [string]$TestRoot = 'E:\PandabornDev\build\test',
    [string]$HarnessDir = 'E:\PandabornDev\build\PandabornDevHarness'
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$documents = [Environment]::GetFolderPath('MyDocuments')
$modsDir = Join-Path $documents 'Timberborn\Mods'
$savesDir = Join-Path $documents 'Timberborn\Saves'
$requestPath = Join-Path $TestRoot 'request.json'
$prefsKey = 'Software\Mechanistry\Timberborn'
$restorePattern = '^(Screenmanager |UnitySelectMonitor)'   # window state Unity saves on exit

function Say([string]$text, [string]$color = 'Gray') { Write-Host $text -ForegroundColor $color }

function Get-TestProcesses([datetime]$since) {
    @(Get-Process Timberborn -ErrorAction SilentlyContinue | Where-Object {
        try { $_.StartTime -ge $since.AddSeconds(-3) } catch { $false } })
}

function Get-PrefsSnapshot {
    $snapshot = @{}
    $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($prefsKey)
    if ($null -eq $key) { return $snapshot }
    try {
        foreach ($name in $key.GetValueNames()) {
            $snapshot[$name] = @{ Kind = $key.GetValueKind($name); Value = $key.GetValue($name, $null, 'DoNotExpandEnvironmentNames') }
        }
    } finally { $key.Close() }
    return $snapshot
}

function Format-PrefValue($entry) {
    if ($null -eq $entry) { return '<none>' }
    if ($entry.Value -is [byte[]]) { return ($entry.Value -join ',') }
    return [string]$entry.Value
}

# ------------------------------------------------------------------ preflight
$running = @(Get-Process Timberborn -ErrorAction SilentlyContinue)
if ($running.Count -gt 0) {
    Say "Timberborn is already running (pid $($running.Id -join ', ')). Not touching it; close it and retry." 'Yellow'
    exit 2
}
if (-not (Get-Process steam -ErrorAction SilentlyContinue)) {
    Say 'Steam is not running: the game may refuse to start or Workshop mods will be missing.' 'Yellow'
}
if (-not $RunId) { $RunId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + ($Faction.ToLowerInvariant() -replace '[^a-z0-9]', '') }
$runDir = Join-Path $TestRoot $RunId
New-Item -ItemType Directory -Force $runDir | Out-Null
$settlement = 'PB_AutoTest_' + ($RunId -replace '[^A-Za-z0-9_-]', '_')

# ------------------------------------------------------------------ build + install (junction)
if (-not $NoBuild) {
    $project = Join-Path $repo 'src\devharness\PandabornDevHarness.csproj'
    $buildLog = & dotnet build $project -c Release -v q --nologo "-p:ModOut=$HarnessDir" 2>&1
    if ($LASTEXITCODE -ne 0) { $buildLog | ForEach-Object { Say "  $_" 'Red' }; Say 'Harness build failed.' 'Red'; exit 2 }
}
if (-not (Test-Path (Join-Path $HarnessDir 'Scripts\PandabornDevHarness.dll'))) { Say "Harness DLL missing in $HarnessDir" 'Red'; exit 2 }
$link = Join-Path $modsDir 'PandabornDevHarness'
if (Test-Path $link) {
    $item = Get-Item $link -Force
    $target = @($item.Target) | Select-Object -First 1
    if ($item.LinkType -ne 'Junction' -or ($target.TrimEnd('\') -ne $HarnessDir.TrimEnd('\'))) {
        Say "$link exists but is not a junction to $HarnessDir; leaving it alone." 'Red'; exit 2
    }
} else {
    New-Item -ItemType Junction -Path $link -Target $HarnessDir | Out-Null
    Say "Installed harness: $link -> $HarnessDir"
}

# ------------------------------------------------------------------ request
$shots = @()
foreach ($s in $Screenshots) {
    $parts = $s.Split('@')
    $kind = $parts[0].Trim().ToLowerInvariant()
    $at = if ($parts.Count -gt 1) { $parts[1].Trim().ToLowerInvariant() } else { 'start' }
    $shots += [ordered]@{ name = "$($kind)_$at"; kind = $kind; at = $at }
}
$run = [ordered]@{ realSeconds = $RunSeconds }
if ($InGameDays -gt 0 -or $InGameHours -gt 0) {
    $run = [ordered]@{ inGameDays = $InGameDays; inGameHours = $InGameHours }
    if ($PSBoundParameters.ContainsKey('RunSeconds')) { $run.realSeconds = $RunSeconds }
}
$request = [ordered]@{
    runId          = $RunId
    outputDir      = $runDir
    expiresUtc     = (Get-Date).ToUniversalTime().AddSeconds($TimeoutSeconds + 120).ToString('o')
    faction        = $Faction
    map            = $Map
    gameMode       = $GameMode
    settlementName = $settlement
    speed          = $Speed
    devMode        = (-not $NoDevMode)
    mute           = (-not $Sound)
    window         = [ordered]@{ windowed = (-not $Fullscreen); width = $Width; height = $Height }
    run            = $run
    buildings      = @($Buildings)
    screenshots    = $shots
    ownPatterns    = @($OwnPatterns)
    checks         = $Checks
}
if ($RequestJson) {
    $override = Get-Content $RequestJson -Raw | ConvertFrom-Json
    foreach ($p in $override.PSObject.Properties) { $request[$p.Name] = $p.Value }
    $request.outputDir = $runDir; $request.runId = $RunId
}
$requestText = $request | ConvertTo-Json -Depth 10
[IO.File]::WriteAllText($requestPath, $requestText, (New-Object Text.UTF8Encoding($false)))

# ------------------------------------------------------------------ launch
$prefsBefore = Get-PrefsSnapshot
$logFile = Join-Path $runDir 'Player.log'
$arguments = @('-skipModManager', '-logFile', "`"$logFile`"", '-pbTestRequest', "`"$requestPath`"")
if (-not $Fullscreen) { $arguments += @('-screen-fullscreen', '0', '-screen-width', "$Width", '-screen-height', "$Height") }
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = Join-Path $GameDir 'Timberborn.exe'
$psi.WorkingDirectory = $GameDir
$psi.Arguments = $arguments -join ' '
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true   # Unity echoes its memory setup to stdout; drained and dropped below
$psi.RedirectStandardError = $true
# launched by Steam, the game gets these; with them set it does not bounce through Steam (which would drop our arguments)
$psi.EnvironmentVariables['SteamAppId'] = '1062090'
$psi.EnvironmentVariables['SteamGameId'] = '1062090'
$psi.EnvironmentVariables['PANDABORN_TEST_REQUEST'] = $requestPath
$launchTime = Get-Date
Say "Run $RunId : $Faction on $Map; output $runDir" 'Cyan'
$game = [Diagnostics.Process]::Start($psi)
$game.BeginOutputReadLine()
$game.BeginErrorReadLine()

# ------------------------------------------------------------------ wait
$deadline = $launchTime.AddSeconds($TimeoutSeconds)
$resultPath = Join-Path $runDir 'result.json'
$harnessLog = Join-Path $runDir 'harness.log'
$shownLines = 0
$timedOut = $false
$killedAfterResult = $false
$resultSeenAt = $null
$sawProcess = $false
while ($true) {
    Start-Sleep -Seconds 2
    if (Test-Path $harnessLog) {
        $lines = @(Get-Content $harnessLog -ErrorAction SilentlyContinue)
        for ($i = $shownLines; $i -lt $lines.Count; $i++) { Say "  $($lines[$i])" 'DarkGray' }
        $shownLines = $lines.Count
    }
    $procs = Get-TestProcesses $launchTime
    if ($procs.Count -gt 0) { $sawProcess = $true }
    if ((Test-Path $resultPath) -and -not $resultSeenAt) { $resultSeenAt = Get-Date }
    if ($procs.Count -eq 0) {
        # a Steam bounce briefly leaves no process; give it a moment before calling it over
        if (-not $resultSeenAt -and ((Get-Date) - $launchTime).TotalSeconds -lt 30) { continue }
        break
    }
    if ((Get-Date) -gt $deadline) {
        Say "Timeout after $TimeoutSeconds s: killing the game." 'Red'
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        $timedOut = $true
        break
    }
    if ($resultSeenAt -and ((Get-Date) - $resultSeenAt).TotalSeconds -gt 90) {
        Say 'Result written but the game did not quit within 90 s: killing it.' 'Yellow'
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        $killedAfterResult = $true
        break
    }
}
for ($i = 0; $i -lt 15 -and (Get-TestProcesses $launchTime).Count -gt 0; $i++) { Start-Sleep -Seconds 1 }
Get-TestProcesses $launchTime | Stop-Process -Force -ErrorAction SilentlyContinue
$gameSeconds = [math]::Round(((Get-Date) - $launchTime).TotalSeconds)

# ------------------------------------------------------------------ cleanup: request, window prefs, saves
$requestConsumed = -not (Test-Path $requestPath)
if (-not $requestConsumed) { Remove-Item $requestPath -Force }

$prefsAfter = Get-PrefsSnapshot
$restored = @(); $changed = @()
$names = @($prefsBefore.Keys) + @($prefsAfter.Keys) | Sort-Object -Unique
$writable = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($prefsKey, $true)
foreach ($name in $names) {
    $before = $prefsBefore[$name]; $after = $prefsAfter[$name]
    if ((Format-PrefValue $before) -eq (Format-PrefValue $after)) { continue }
    if ($name -match $restorePattern -and $null -ne $writable) {
        if ($null -eq $before) { $writable.DeleteValue($name, $false) }
        else { $writable.SetValue($name, $before.Value, $before.Kind) }
        $restored += $name
    } else { $changed += $name }
}
if ($null -ne $writable) { $writable.Close() }

if (-not $KeepInstalled -and (Test-Path $link)) {
    [IO.Directory]::Delete($link, $false)   # removes the junction only, never the target
}

$savesDeleted = @()
if (-not $KeepSave -and (Test-Path $savesDir)) {
    Get-ChildItem $savesDir -Directory | Where-Object { $_.Name -like 'PB_AutoTest*' -and $_.Name -eq $settlement } | ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force
        $savesDeleted += $_.Name
    }
}

# ------------------------------------------------------------------ log
if (-not (Test-Path $logFile)) {
    $fallback = Join-Path $env:USERPROFILE 'AppData\LocalLow\Mechanistry\Timberborn\Player.log'
    if ((Test-Path $fallback) -and (Get-Item $fallback).LastWriteTime -ge $launchTime) { Copy-Item $fallback $logFile }
}
$ownRegex = ($OwnPatterns | ForEach-Object { [regex]::Escape($_) }) -join '|'
$groups = @{}
function Add-Issue([string]$source, [string]$type, [string]$first, [string]$context) {
    $ours = $context -match $ownRegex
    $keyText = ($first -replace '\d+', '#')
    if ($keyText.Length -gt 200) { $keyText = $keyText.Substring(0, 200) }
    $key = "$type|$ours|$keyText"
    if (-not $groups.ContainsKey($key)) {
        $groups[$key] = [ordered]@{ type = $type; ours = $ours; count = 0; source = $source; first = $first
                                    sample = $context.Substring(0, [math]::Min(1500, $context.Length)) }
    }
    $groups[$key].count++
}
# 1) Player.log. A release build writes errors without a type marker or stack trace, so this catches exceptions,
#    assertion failures and lines that call themselves errors; everything before the harness started is covered too.
$issueRegex = '\b[A-Z]\w*Exception\b|^Assertion failed|^\[?(Error|ERROR)\]?[:\] ]|\bERROR\b|^First uncaught exception'
if (Test-Path $logFile) {
    $lines = @(Get-Content $logFile)
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match '^\s+at ' -or $line -notmatch $issueRegex) { continue }
        if ($line -match '^\[PandabornDevHarness\] (active|starting|game|phase|placed|screenshot|running|window|finished|quitting)') { continue }
        $context = $line
        for ($j = $i + 1; $j -lt [math]::Min($lines.Count, $i + 40) -and $lines[$j] -match '^\s+(at |---)|^\S+:\S+ \(|^\(Filename:|^Rethrow as'; $j++) { $context += "`n" + $lines[$j] }
        $type = if ($line -match '^First uncaught') { 'crash' } elseif ($line -match 'Exception') { 'exception' } elseif ($line -match '^Assertion') { 'assert' } else { 'error' }
        Add-Issue 'Player.log' $type $line $context
    }
}
# 2) What the harness saw through Unity's log callback, with real types and stack traces (from mod load onwards).
$harnessIssues = @()
if (Test-Path $resultPath) {
    $tmp = Get-Content $resultPath -Raw | ConvertFrom-Json
    foreach ($e in @($tmp.log.entries)) {
        if (-not $e) { continue }
        $first = ($e.message -split "`n")[0]
        $harnessIssues += [ordered]@{ type = $e.type; ours = [bool]$e.ours; first = $first }
    }
}
$hGroups = $harnessIssues | Group-Object { "$($_.type)|$($_.ours)|$($_.first)" } | ForEach-Object {
    [ordered]@{ type = $_.Group[0].type; ours = $_.Group[0].ours; count = $_.Count; source = 'harness'; first = $_.Group[0].first } }
$ourGroups = @(@($groups.Values) + @($hGroups) | Where-Object { $_ -and $_.ours } | Sort-Object { -$_.count })
$otherGroups = @(@($groups.Values) + @($hGroups) | Where-Object { $_ -and -not $_.ours } | Sort-Object { -$_.count })

# ------------------------------------------------------------------ verdict
$result = $null
if (Test-Path $resultPath) { $result = Get-Content $resultPath -Raw | ConvertFrom-Json }
$problems = @()
$exitCode = 0
if (-not $sawProcess) { $problems += 'the game process never started'; $exitCode = 2 }
elseif (-not $requestConsumed) { $problems += 'the harness never picked up the request (mod not loaded?)'; $exitCode = 2 }
elseif ($null -eq $result) { $problems += 'no result.json'; $exitCode = 2 }
if ($timedOut) { $problems += "timeout after $TimeoutSeconds s"; if ($exitCode -eq 0) { $exitCode = 2 } }
if ($null -ne $result) {
    if ($result.status -ne 'completed') { $problems += "harness status: $($result.status)"; if ($exitCode -eq 0) { $exitCode = 1 } }
    foreach ($c in @($result.checks)) { if ($c -and -not $c.pass) { $problems += "check $($c.name) failed: $($c.detail)"; if ($exitCode -eq 0) { $exitCode = 1 } } }
}
if ($ourGroups.Count -gt 0) { $problems += "$($ourGroups.Count) kind(s) of log errors from our mods"; if ($exitCode -eq 0) { $exitCode = 1 } }
if ($StrictLog -and $otherGroups.Count -gt 0) { $problems += "$($otherGroups.Count) kind(s) of log errors from other mods/the game (-StrictLog)"; if ($exitCode -eq 0) { $exitCode = 1 } }
if ($killedAfterResult) { $problems += 'the game had to be killed after writing its result' }
$verdict = if ($exitCode -eq 0) { 'PASS' } elseif ($exitCode -eq 1) { 'FAIL' } else { 'ERROR' }

$summary = [ordered]@{
    verdict = $verdict; exitCode = $exitCode; runId = $RunId; runDir = $runDir; gameSeconds = $gameSeconds
    harnessStatus = $(if ($result) { $result.status } else { $null }); harnessVerdict = $(if ($result) { $result.verdict } else { $null })
    problems = $problems; timedOut = $timedOut; requestConsumed = $requestConsumed
    logErrorsOurs = $ourGroups; logErrorsOthers = $otherGroups
    prefsRestored = $restored; prefsChangedNotRestored = $changed; savesDeleted = $savesDeleted
}
[IO.File]::WriteAllText((Join-Path $runDir 'summary.json'), ($summary | ConvertTo-Json -Depth 6), (New-Object Text.UTF8Encoding($false)))

# ------------------------------------------------------------------ report
$color = @{ PASS = 'Green'; FAIL = 'Red'; ERROR = 'Red' }[$verdict]
Say ''
Say "=== $verdict  ($RunId, $gameSeconds s)  $runDir" $color
if ($null -ne $result) {
    Say ("game {0}; faction {1}; map {2}; status {3}" -f $result.gameVersion, $result.activeFaction.id, $result.newGame.map, $result.status)
    if ($result.population) { Say ("population: {0} adults, {1} children, {2} bots; day {3}" -f $result.population.adults, $result.population.children, $result.population.bots, $result.time.day) }
    foreach ($c in @($result.checks)) { if ($c) { Say ("  [{0}] {1}: {2}" -f $(if ($c.pass) { 'ok' } else { 'XX' }), $c.name, $c.detail) $(if ($c.pass) { 'Gray' } else { 'Red' }) } }
    foreach ($s in @($result.characterSamples) | Select-Object -First 6) { if ($s) { Say ("  {0,-6} {1,-28} mesh {2}; coat {3}" -f $s.kind, $s.template, $s.body.mesh, $s.body.baseMap) } }
    foreach ($s in @($result.screenshots)) { if ($s) { Say ("  shot {0}: {1}" -f $s.name, $(if ($s.file) { $s.file } else { 'MISSING ' + $s.error })) } }
    Say ("harness log counts: {0} errors, {1} exceptions ({2} ours)" -f $result.log.errors, $result.log.exceptions, ($result.log.ownErrors + $result.log.ownExceptions))
}
Say ("log issues: {0} kind(s) from our mods, {1} from other mods / the game" -f $ourGroups.Count, $otherGroups.Count)
foreach ($g in $ourGroups | Select-Object -First 8) { Say ("  OURS  x{0} {1} [{2}]: {3}" -f $g.count, $g.type, $g.source, $g.first) 'Red' }
foreach ($g in $otherGroups | Select-Object -First 8) { Say ("  other x{0} {1} [{2}]: {3}" -f $g.count, $g.type, $g.source, $g.first) 'DarkYellow' }
if (-not $KeepInstalled) { Say "harness junction removed (use -KeepInstalled to keep it)" 'DarkGray' }
if ($restored.Count) { Say "restored window prefs: $($restored -join ', ')" }
if ($changed.Count) { Say "other prefs the game changed (not restored): $($changed -join ', ')" 'DarkGray' }
if ($savesDeleted.Count) { Say "deleted test save(s): $($savesDeleted -join ', ')" }
foreach ($p in $problems) { Say "  problem: $p" $color }
exit $exitCode

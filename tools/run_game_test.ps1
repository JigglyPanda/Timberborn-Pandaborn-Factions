<#
.SYNOPSIS
  Automated in-game test. Launches Timberborn, lets the PandabornDevHarness mod start a new game as the given faction,
  run it, take screenshots and write result.json, then quits, scans the log and prints a verdict.

.DESCRIPTION
  Exit codes: 0 = pass, 1 = fail (a check failed, our mods logged errors, or the game crashed),
              2 = could not test (game already running, build/launch failure, timeout, harness never loaded,
                  mod state could not be changed or restored).
  Output: E:\PandabornDev\build\test\<RunId>\ with request.json, result.json, summary.json, harness.log, Player.log, *.png.
  With -SaveAndReload the second launch (into the saved game) writes to <RunId>\reload\.

  Mod isolation (-DisableMods / -OnlyMods) changes the game's own per-mod enable flags (Unity PlayerPrefs in
  HKCU\Software\Mechanistry\Timberborn, value "ModEnabled.<Local|Steam Workshop>.<folder>.<manifest Id>_h<hash>",
  REG_DWORD 1/0, absent = enabled). Before anything is changed the exact prior values are written to
  <run>\modstate.json and E:\PandabornDev\build\test\modstate.pending.json. They are restored in a finally block (also on
  timeout, crash and Ctrl-C) after the game has exited, then re-read and compared. If the script is killed outright,
  run it with -RestoreModState <file>; while modstate.pending.json exists the script refuses to start a test.

  A killed runner (closed console, a tool timeout, a reboot) runs no finally block. So before its first change a run
  writes <TestRoot>\run.pending.json: its own pid and start time, each test game's pid and start time, the junctions
  it makes in Mods (with their targets), its save folder, its request files, the window prefs. A clean exit removes
  the record. The next run that gets the lock (and tools\play_timberborn.ps1, and -Recover) finds a record whose
  runner is dead and cleans from it: stops the recorded game only if pid AND start time still match, restores the flags
  through the normal restore, removes the recorded junctions (the link, never the target), deletes the recorded save
  and requests. Shared helpers: tools\game_lock.ps1; their trials: tools\tests\game_lock.trial.ps1.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -RunSeconds 60
.EXAMPLE
  tools\run_game_test.ps1 -Faction Inkpaws -DisableMods JigglyPanda.Pandaborn -InGameDays 2 -Buildings 'Lodge.Folktails'
.EXAMPLE
  tools\run_game_test.ps1 -Faction Inkpaws -OnlyMods JigglyPanda.PandabornFactions -SaveAndReload
.EXAMPLE
  tools\run_game_test.ps1 -RestoreModState E:\PandabornDev\build\test\modstate.pending.json
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
    # merged into request.checks, e.g. @{ minChildren = 1; adultTemplate = 'BeaverAdult' }
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
    # mods (manifest Id, folder name or display name) to switch off for this run only
    [string[]]$DisableMods = @(),
    # switch off every enabled mod except these (plus the harness and their required mods) for this run only
    [string[]]$OnlyMods = @(),
    # restore mod enable flags from a modstate.json written by an earlier run, then exit
    [string]$RestoreModState = '',
    # screen captures of the main menu's new-game faction panel, one per faction, before the game starts
    [switch]$FactionPanelShots,
    # save the test game at the end, relaunch the game straight into the save (-saveName/-settlementName) and check it
    [switch]$SaveAndReload,
    [double]$ReloadSeconds = 20,
    # skip opening every batch-control tab at the end of the run
    [switch]$NoBatchControl,
    # extra mod folders (e.g. E:\PandabornDev\build\proto\<name>) junctioned into Mods and enabled for this run only
    [string[]]$ExtraMods = @(),
    # wait this long for another test run (named mutex) or an open Timberborn before giving up with exit code 2
    [int]$WaitForGameSeconds = 1800,
    # print the mod flag plan (what -DisableMods/-OnlyMods/-ExtraMods would change) and exit without launching
    [switch]$DryRun,
    # show the game window on the real desktop (default: the game runs on a hidden desktop and never takes the focus)
    [switch]$Visible,
    # run although the queue is held (tools\game_test_hold.ps1): only for the session that started the hold
    [switch]$DuringHold,
    # clean up after a run that died (its record is <TestRoot>\run.pending.json), then exit. A normal run does the same
    # before it starts; this is for tools\play_timberborn.ps1 and for doing it by hand.
    [switch]$Recover,
    # only for trials of the hold scripts on a scratch lock; a real run always uses the default
    [string]$MutexName = 'Global\PandabornGameTest',
    [string]$RunId = '',
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Timberborn',
    [string]$WorkshopDir = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\1062090',
    [string]$TestRoot = 'E:\PandabornDev\build\test',
    [string]$HarnessDir = 'E:\PandabornDev\build\PandabornDevHarness'
)

$ErrorActionPreference = 'Stop'
# powershell -File passes "a,b" as one string: split list parameters on commas
function Split-List([string[]]$items) { @($items | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
$DisableMods = @(Split-List $DisableMods)
$OnlyMods = @(Split-List $OnlyMods)
$ExtraMods = @(Split-List $ExtraMods)
$Buildings = @(Split-List $Buildings)
$Screenshots = @(Split-List $Screenshots)
$OwnPatterns = @(Split-List $OwnPatterns)
$repo = Split-Path -Parent $PSScriptRoot
$documents = [Environment]::GetFolderPath('MyDocuments')
$modsDir = Join-Path $documents 'Timberborn\Mods'
$savesDir = Join-Path $documents 'Timberborn\Saves'
$requestPath = Join-Path $TestRoot 'request.json'
$pendingStatePath = Join-Path $TestRoot 'modstate.pending.json'
$prefsKey = 'Software\Mechanistry\Timberborn'
$restorePattern = '^(Screenmanager |UnitySelectMonitor)'   # window state Unity saves on exit
$lockInfoPath = Join-Path $TestRoot 'gametest.lock.json'
$mutexName = $MutexName
$runRecordPath = Join-Path $TestRoot 'run.pending.json'
. (Join-Path $PSScriptRoot 'game_lock.ps1')   # holds, the holder file, the pending-run record, pid + start time checks
$harnessId = 'JigglyPanda.PandabornDevHarness'
$saveName = 'PB_AutoTest'
$utf8 = New-Object Text.UTF8Encoding($false)

function Say([string]$text, [string]$color = 'Gray') { Write-Host $text -ForegroundColor $color }

# Runs the game on a separate Windows desktop (same session, so the GPU, the registry and the files are the same), where
# its window is never on the owner's screen and gets none of the owner's input. The desktop goes away with its last
# process and handle.
$hiddenDesktopName = 'PandabornTest'
if (-not $Visible -and -not ('PandabornTest.HiddenDesktop' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
namespace PandabornTest {
    public static class HiddenDesktop {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        struct STARTUPINFO {
            public int cb; public string lpReserved; public string lpDesktop; public string lpTitle;
            public int dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute, dwFlags;
            public short wShowWindow, cbReserved2; public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
        }
        [StructLayout(LayoutKind.Sequential)]
        struct PROCESS_INFORMATION { public IntPtr hProcess, hThread; public int dwProcessId, dwThreadId; }
        [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        static extern IntPtr CreateDesktop(string name, IntPtr device, IntPtr devmode, int flags, uint access, IntPtr security);
        [DllImport("user32.dll", SetLastError = true)] static extern bool CloseDesktop(IntPtr desktop);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        static extern bool CreateProcess(string app, System.Text.StringBuilder commandLine, IntPtr processAttributes, IntPtr threadAttributes,
            bool inheritHandles, uint flags, IntPtr environment, string currentDirectory, ref STARTUPINFO startupInfo, out PROCESS_INFORMATION info);
        [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
        static IntPtr _desktop = IntPtr.Zero;
        public static int Start(string desktopName, string commandLine, string workingDirectory) {
            if (_desktop == IntPtr.Zero) {
                _desktop = CreateDesktop(desktopName, IntPtr.Zero, IntPtr.Zero, 0, 0x10000000 /* GENERIC_ALL */, IntPtr.Zero);
                if (_desktop == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateDesktop failed");
            }
            var si = new STARTUPINFO(); si.cb = Marshal.SizeOf(typeof(STARTUPINFO)); si.lpDesktop = "WinSta0\\" + desktopName;
            PROCESS_INFORMATION pi;
            if (!CreateProcess(null, new System.Text.StringBuilder(commandLine), IntPtr.Zero, IntPtr.Zero, false, 0, IntPtr.Zero, workingDirectory, ref si, out pi))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateProcess failed");
            CloseHandle(pi.hThread); CloseHandle(pi.hProcess);
            return pi.dwProcessId;
        }
        public static void Close() { if (_desktop != IntPtr.Zero) { CloseDesktop(_desktop); _desktop = IntPtr.Zero; } }
    }
}
'@
}

# The game processes this run started. On the hidden desktop the pid is known, so a game the owner starts meanwhile is
# never counted, waited for or killed. (-Visible launches may bounce through Steam, so they go by start time.)
$script:testGames = @()   # @{ pid; processStartedUtc } of every game this run started on the hidden desktop
# Is this process one of ours? By pid AND start time (a pid can come back as somebody else's game). An entry whose
# start time could not be read at launch goes by pid alone, in this run only; the record never kills on a pid alone.
function Test-IsTestGame($process) {
    foreach ($g in $script:testGames) {
        if ($g.pid -ne $process.Id) { continue }
        if (-not $g.processStartedUtc) { return $true }
        try { if ($process.StartTime.ToUniversalTime().Ticks -eq (Get-UtcTicks $g.processStartedUtc)) { return $true } } catch { }
    }
    return $false
}
function Get-TestProcesses([datetime]$since) {
    # hidden desktop: only the games this run started. Before the first launch (or when the launch failed) that is
    # nothing; going by start time there would count, and kill, a game the owner started in those seconds.
    if (-not $Visible) {
        return @(Get-Process Timberborn -ErrorAction SilentlyContinue | Where-Object { Test-IsTestGame $_ })
    }
    @(Get-Process Timberborn -ErrorAction SilentlyContinue | Where-Object {
        try { $_.StartTime -ge $since.AddSeconds(-3) } catch { $false } })
}
# Timberborn processes that are not this run's: the owner playing. (-Visible cannot tell them apart.)
function Get-OwnerGames {
    if ($Visible) { return @() }
    @(Get-Process Timberborn -ErrorAction SilentlyContinue | Where-Object { -not (Test-IsTestGame $_) })
}

# ------------------------------------------------------------------ the pending-run record (tools\game_lock.ps1)
# What this run has changed on the machine, on disk before each change: if the runner is killed (closed console, tool
# timeout, reboot), the next lock holder and tools\play_timberborn.ps1 clean from it.
$script:runRecord = $null
$script:leftBehind = $false   # true while something of this run may still be on the machine
function Save-RunRecord {
    if ($null -eq $script:runRecord) { return }
    try { Write-JsonFile $runRecordPath $script:runRecord } catch { Say "could not write $($runRecordPath): $_" 'Yellow' }
}

# Window prefs (the values Unity saves on exit) as record rows, and back.
function ConvertTo-PrefRecord($snapshot) {
    $rows = @()
    foreach ($name in @($snapshot.Keys | Sort-Object)) {
        if ($name -notmatch $restorePattern) { continue }
        $e = $snapshot[$name]; $bytes = $e.Value -is [byte[]]
        $rows += [ordered]@{ name = $name; kind = [string]$e.Kind; base64 = $bytes
                             value = $(if ($bytes) { [Convert]::ToBase64String($e.Value) } else { $e.Value }) }
    }
    return $rows
}
function ConvertFrom-PrefRecord($row) {
    $kind = [Microsoft.Win32.RegistryValueKind]([string]$row.kind)
    $value = if ($row.base64) { , [Convert]::FromBase64String([string]$row.value) }
             elseif ($kind -eq 'DWord') { [int]$row.value } elseif ($kind -eq 'QWord') { [long]$row.value } else { [string]$row.value }
    return @{ Kind = $kind; Value = $value }
}
# What to write so the window prefs are again what the dead run recorded. Nothing unless the registry still holds the
# test's own window size: otherwise the owner, or a later run, has set theirs since, and those stay.
# $now is a Get-PrefsSnapshot. Returns rows @{ name; action = 'set' | 'delete'; entry }.
function Get-WindowPrefPlan($rows, $now, $width, $height) {
    $plan = @()
    if (-not $width -or -not $height) { return $plan }
    $w = @($now.Keys | Where-Object { $_ -match '^Screenmanager Resolution Width' }) | Select-Object -First 1
    $h = @($now.Keys | Where-Object { $_ -match '^Screenmanager Resolution Height' }) | Select-Object -First 1
    if (-not $w -or -not $h) { return $plan }
    if ([string]$now[$w].Value -ne [string]$width -or [string]$now[$h].Value -ne [string]$height) { return $plan }
    $byName = @{}; foreach ($r in @($rows | Where-Object { $_ })) { $byName[[string]$r.name] = $r }
    foreach ($name in @($now.Keys | Sort-Object)) {
        if ($name -notmatch $restorePattern) { continue }
        if (-not $byName.ContainsKey($name)) { $plan += @{ name = $name; action = 'delete'; entry = $null }; continue }
        $entry = ConvertFrom-PrefRecord $byName[$name]
        if ((Format-PrefValue $entry) -ne (Format-PrefValue $now[$name])) { $plan += @{ name = $name; action = 'set'; entry = $entry } }
    }
    return $plan
}
function Restore-WindowPrefs($rows, $width, $height) {
    $plan = @(Get-WindowPrefPlan $rows (Get-PrefsSnapshot) $width $height)
    if ($plan.Count -eq 0) { return @() }
    $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($prefsKey, $true)
    if ($null -eq $key) { return @() }
    try {
        foreach ($p in $plan) {
            if ($p.action -eq 'delete') { $key.DeleteValue($p.name, $false) } else { $key.SetValue($p.name, $p.entry.Value, $p.entry.Kind) }
        }
    } finally { $key.Close() }
    return @($plan | ForEach-Object { $_.name })
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

# ------------------------------------------------------------------ mod enable flags (Unity PlayerPrefs)

# Unity's PlayerPrefs registry value name: key + "_h" + djb2-xor hash of the UTF-8 key (verified against existing values)
function Get-PrefValueName([string]$prefKey) {
    [long]$h = 5381
    foreach ($b in [Text.Encoding]::UTF8.GetBytes($prefKey)) { $h = ((($h * 33) -band 0xFFFFFFFFL) -bxor [long]$b) }
    return "$($prefKey)_h$h"
}

# The game reads manifests with a lenient JSON reader (trailing commas are common); ConvertFrom-Json is strict, so
# trailing commas and // comments are stripped first. Returns $null if it still cannot be read.
function Read-Manifest([string]$path) {
    try {
        $text = [IO.File]::ReadAllText($path)
        $text = [regex]::Replace($text, '(?m)^\s*//.*$', '')
        $text = [regex]::Replace($text, ',(\s*[}\]])', '$1')
        return ($text | ConvertFrom-Json)
    } catch { return $null }
}
$script:manifestProblems = @()

# Every mod folder the game can see, as Timberborn.Modding builds its key: "ModEnabled.<DisplaySource>.<OriginName>.<Id>".
# OriginName is the top folder even when a version-* subfolder is loaded; all Ids found in the folder are listed.
function Get-InstalledMods {
    $mods = @()
    $sources = @(@{ Source = 'Local'; Dir = $modsDir; Deep = $false }, @{ Source = 'Steam Workshop'; Dir = $WorkshopDir; Deep = $true })
    foreach ($src in $sources) {
        if (-not (Test-Path $src.Dir)) { continue }
        foreach ($dir in Get-ChildItem -LiteralPath $src.Dir -Directory -Force) {
            $manifestFiles = @()
            $root = Join-Path $dir.FullName 'manifest.json'
            if (Test-Path -LiteralPath $root) { $manifestFiles += $root }
            foreach ($v in @(Get-ChildItem -LiteralPath $dir.FullName -Directory -Filter 'version-*' -ErrorAction SilentlyContinue)) {
                $m = Join-Path $v.FullName 'manifest.json'
                if (Test-Path -LiteralPath $m) { $manifestFiles += $m }
            }
            if ($src.Deep -and $manifestFiles.Count -eq 0) {
                $manifestFiles = @(Get-ChildItem -LiteralPath $dir.FullName -Recurse -Filter 'manifest.json' -File -ErrorAction SilentlyContinue | ForEach-Object FullName)
            }
            $ids = @(); $names = @(); $required = @()
            foreach ($mf in $manifestFiles) {
                $m = Read-Manifest $mf
                if ($null -eq $m -or -not $m.Id) { $script:manifestProblems += $mf; continue }
                if ($ids -cnotcontains $m.Id) { $ids += [string]$m.Id }   # the pref key is case-sensitive
                if ($m.Name -and $names -notcontains $m.Name) { $names += [string]$m.Name }
                foreach ($r in @($m.RequiredMods)) { if ($r -and $r.Id -and $required -notcontains $r.Id) { $required += [string]$r.Id } }
            }
            if ($ids.Count -eq 0) { continue }   # the game skips folders without a manifest too
            $mods += [pscustomobject]@{
                Source = $src.Source; Origin = $dir.Name; Ids = $ids; Names = $names; Required = $required
                Keys = @($ids | ForEach-Object { Get-PrefValueName "ModEnabled.$($src.Source).$($dir.Name).$_" })
            }
        }
    }
    return $mods
}

function Read-PrefEntry($key, [string]$name) {
    if ($key.GetValueNames() -notcontains $name) { return [ordered]@{ name = $name; existed = $false; kind = $null; value = $null } }
    $kind = $key.GetValueKind($name)
    return [ordered]@{ name = $name; existed = $true; kind = [string]$kind; value = $key.GetValue($name) }
}

# true when a mod with this key layout is enabled (no value or DWORD 1)
function Test-ModEnabled($key, $mod) {
    foreach ($n in $mod.Keys) {
        $e = Read-PrefEntry $key $n
        if ($e.existed -and [int]$e.value -ne 1) { return $false }
    }
    return $true
}

function Find-Mods($mods, [string[]]$tokens) {
    $found = @(); $missing = @()
    foreach ($t in $tokens) {
        $hits = @($mods | Where-Object { $_.Ids -contains $t -or $_.Origin -eq $t -or $_.Names -contains $t })
        if ($hits.Count -eq 0) { $missing += $t } else { $found += $hits }
    }
    return @{ Found = @($found | Sort-Object Source, Origin -Unique); Missing = $missing }
}

# Restores every recorded value exactly (DWORD value back, or deletes a value that did not exist), then re-reads
# them. Returns the per-value comparison; .ok is false if any value differs from what was recorded.
function Restore-ModState($state) {
    $rows = @(); $ok = $true
    $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($prefsKey, $true)
    if ($null -eq $key) { throw "registry key HKCU\$prefsKey not found" }
    try {
        foreach ($e in @($state.entries)) {
            try {
                if ($e.existed) { $key.SetValue($e.name, [int]$e.value, [Microsoft.Win32.RegistryValueKind]::DWord) }
                else { $key.DeleteValue($e.name, $false) }
            } catch { Say "  could not restore $($e.name): $_" 'Red' }
        }
        $key.Flush()
        foreach ($e in @($state.entries)) {
            $after = Read-PrefEntry $key $e.name
            $match = ($after.existed -eq [bool]$e.existed) -and (-not $e.existed -or ($after.kind -eq $e.kind -and [int]$after.value -eq [int]$e.value))
            if (-not $match) { $ok = $false }
            $rows += [ordered]@{ name = $e.name; mod = $e.mod; before = $(if ($e.existed) { "$($e.kind) $($e.value)" } else { '<absent>' })
                                 set = "DWord $($e.set)"; afterRestore = $(if ($after.existed) { "$($after.kind) $($after.value)" } else { '<absent>' }); match = $match }
        }
    } finally { $key.Close() }
    return [ordered]@{ ok = $ok; entries = $rows }
}

# ------------------------------------------------------------------ request + launch helpers
function New-Request([string]$outDir, [hashtable]$extra) {
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
        runId             = $RunId
        outputDir         = $outDir
        expiresUtc        = (Get-Date).ToUniversalTime().AddSeconds($TimeoutSeconds + 120).ToString('o')
        faction           = $Faction
        map               = $Map
        gameMode          = $GameMode
        settlementName    = $settlement
        speed             = $Speed
        devMode           = (-not $NoDevMode)
        mute              = (-not $Sound)
        window            = [ordered]@{ windowed = (-not $Fullscreen); width = $Width; height = $Height }
        run               = $run
        buildings         = @($Buildings)
        screenshots       = $shots
        ownPatterns       = @($OwnPatterns)
        checks            = $Checks
        batchControl      = (-not $NoBatchControl)
        factionPanelShots = [bool]$FactionPanelShots
    }
    if ($SaveAndReload) { $request.save = $saveName }
    if ($RequestJson) {
        $override = Get-Content $RequestJson -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($p in $override.PSObject.Properties) { $request[$p.Name] = $p.Value }
    }
    foreach ($k in $extra.Keys) { $request[$k] = $extra[$k] }
    $request.outputDir = $outDir; $request.runId = $RunId
    return $request
}

# Launches the game with a request, waits for it to finish (or kills it), restores the window prefs. Never returns
# with a test process still alive unless it could not be killed (reported in .stillRunning).
function Invoke-GameRun([string]$outDir, $request, [string[]]$extraArgs) {
    # never start a second game next to the owner's (they may have started theirs between two launches of this run)
    if (@(Get-OwnerGames).Count -gt 0) { throw 'aborted: a Timberborn that is not this run''s is open; the test game was not started' }
    New-Item -ItemType Directory -Force $outDir | Out-Null
    # The request goes into the run folder, not to the harness's default path (<TestRoot>\request.json): a game started
    # without our arguments (the owner's) looks there, and must never find one. The harness takes the path from the
    # command line or the environment (src/devharness/Harness.cs FindRequestPath). Only a -Visible launch, which may
    # bounce through Steam and lose both, still uses the default path.
    $requestPath = if ($Visible) { $requestPath } else { Join-Path $outDir 'request.in.json' }
    $script:requestFile = $requestPath
    $prefsBefore = Get-PrefsSnapshot
    if ($null -ne $script:runRecord) {
        $script:runRecord.requests = @($script:runRecord.requests) + $requestPath
        if ($null -eq $script:runRecord.windowPrefs) {
            # the first launch's values are the owner's; a second launch would record what the first one left
            $script:runRecord.windowPrefs = @(ConvertTo-PrefRecord $prefsBefore)
            $script:runRecord.window = $(if ($Fullscreen) { $null } else { [ordered]@{ width = $Width; height = $Height } })
        }
        Save-RunRecord
    }
    [IO.File]::WriteAllText($requestPath, ($request | ConvertTo-Json -Depth 10), $utf8)
    $logFile = Join-Path $outDir 'Player.log'
    $arguments = @('-skipModManager', '-logFile', "`"$logFile`"", '-pbTestRequest', "`"$requestPath`"") + $extraArgs
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
    $script:launchTime = Get-Date
    $launchTime = $script:launchTime
    Say "Run $RunId : $($request.faction) on $($request.map); output $outDir" 'Cyan'
    if ($Visible) {
        $game = [Diagnostics.Process]::Start($psi)
        $game.BeginOutputReadLine()
        $game.BeginErrorReadLine()
        if ($null -ne $script:runRecord) {
            $script:runRecord.games = @($script:runRecord.games) + [ordered]@{ pid = $game.Id; processStartedUtc = (Get-ProcessStartUtc $game.Id) }
            Save-RunRecord
        }
    } else {
        # Default: the game runs on its own hidden Windows desktop. It has no window on the owner's screen, cannot take
        # the focus, and never sees the real keyboard or mouse, so the PC stays usable during a run. The child inherits
        # this process's environment, so the variables are set here for the moment of the launch.
        $saved = @{}
        foreach ($name in @('SteamAppId', 'SteamGameId', 'PANDABORN_TEST_REQUEST')) { $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
        try {
            $env:SteamAppId = '1062090'; $env:SteamGameId = '1062090'; $env:PANDABORN_TEST_REQUEST = $requestPath
            $hiddenPid = [PandabornTest.HiddenDesktop]::Start($hiddenDesktopName, "`"$($psi.FileName)`" $($psi.Arguments)", $GameDir)
        } finally {
            foreach ($name in $saved.Keys) { [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process') }
        }
        $started = $null
        for ($i = 0; $i -lt 10 -and -not $started; $i++) { $started = Get-ProcessStartUtc $hiddenPid; if (-not $started) { Start-Sleep -Milliseconds 100 } }
        $script:testGames += @{ pid = $hiddenPid; processStartedUtc = $started }
        if ($null -ne $script:runRecord) {
            $script:runRecord.games = @($script:runRecord.games) + [ordered]@{ pid = $hiddenPid; processStartedUtc = $started }
            Save-RunRecord
        }
        Say "  hidden desktop '$hiddenDesktopName', pid $hiddenPid (use -Visible to see the game)" 'DarkGray'
    }

    $deadline = $launchTime.AddSeconds($TimeoutSeconds)
    $resultPath = Join-Path $outDir 'result.json'
    $harnessLog = Join-Path $outDir 'harness.log'
    $shownLines = 0; $timedOut = $false; $killedAfterResult = $false; $resultSeenAt = $null; $sawProcess = $false
    while ($true) {
        Start-Sleep -Seconds 2
        if (Test-Path $harnessLog) {
            $lines = @(Get-Content $harnessLog -ErrorAction SilentlyContinue)
            for ($i = $shownLines; $i -lt $lines.Count; $i++) { Say "  $($lines[$i])" 'DarkGray' }
            $shownLines = $lines.Count
        }
        $procs = Get-TestProcesses $launchTime
        if ($procs.Count -gt 0) { $sawProcess = $true }
        if (@(Get-OwnerGames).Count -gt 0) {
            Say 'The owner started Timberborn during this run: stopping the test game and restoring mod flags.' 'Red'
            $procs | Stop-Process -Force -ErrorAction SilentlyContinue
            throw 'aborted: the owner started Timberborn during the run'
        }
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
    $stillRunning = Stop-TestGame $launchTime
    $gameSeconds = [math]::Round(((Get-Date) - $launchTime).TotalSeconds)

    $requestConsumed = -not (Test-Path $requestPath)
    if (-not $requestConsumed) { Remove-Item $requestPath -Force }

    # window prefs Unity saved on exit go back to what they were
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

    if (-not (Test-Path $logFile)) {
        $fallback = Join-Path $env:USERPROFILE 'AppData\LocalLow\Mechanistry\Timberborn\Player.log'
        if ((Test-Path $fallback) -and (Get-Item $fallback).LastWriteTime -ge $launchTime) { Copy-Item $fallback $logFile }
    }
    return [ordered]@{
        outDir = $outDir; logFile = $logFile; resultPath = $resultPath; timedOut = $timedOut; killedAfterResult = $killedAfterResult
        sawProcess = $sawProcess; requestConsumed = $requestConsumed; gameSeconds = $gameSeconds; stillRunning = $stillRunning
        prefsRestored = $restored; prefsChanged = $changed
    }
}

# Kills test processes started since $since and waits for them to be gone. Returns true if one is still alive.
function Stop-TestGame([datetime]$since) {
    for ($i = 0; $i -lt 15 -and (Get-TestProcesses $since).Count -gt 0; $i++) { Start-Sleep -Seconds 1 }
    for ($i = 0; $i -lt 30 -and (Get-TestProcesses $since).Count -gt 0; $i++) {
        Get-TestProcesses $since | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
    return ((Get-TestProcesses $since).Count -gt 0)
}

# Scans the log and the result of one launch and prints its verdict. Returns the summary.
function Get-RunVerdict($run, [string]$label) {
    $logFile = $run.logFile; $resultPath = $run.resultPath
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
    $ownWarnings = @()
    if (Test-Path $logFile) {
        $lines = @(Get-Content $logFile)
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $line = $lines[$i]
            if ($line -match '^\s+at ') { continue }
            if ($line -notmatch $issueRegex) {
                # anything else that names our mods and sounds like a problem (missing loc key, asset, warning)
                if ($line -match $ownRegex -and $line -match '(?i)warn|missing|not found|failed|invalid|unknown' -and $line -notmatch '^\[PandabornDevHarness\] (INFO|active|starting|game|phase|placed|screenshot|running|window|finished|quitting|saving|saved)') {
                    $ownWarnings += $line
                }
                continue
            }
            if ($line -match '^\[PandabornDevHarness\] (active|starting|game|phase|placed|screenshot|running|window|finished|quitting|saving|saved)') { continue }
            $context = $line
            for ($j = $i + 1; $j -lt [math]::Min($lines.Count, $i + 40) -and $lines[$j] -match '^\s+(at |---)|^\S+:\S+ \(|^\(Filename:|^Rethrow as'; $j++) { $context += "`n" + $lines[$j] }
            $type = if ($line -match '^First uncaught') { 'crash' } elseif ($line -match 'Exception') { 'exception' } elseif ($line -match '^Assertion') { 'assert' } else { 'error' }
            Add-Issue 'Player.log' $type $line $context
        }
    }
    # 2) What the harness saw through Unity's log callback, with real types and stack traces (from mod load onwards).
    $harnessIssues = @()
    $result = $null
    if (Test-Path $resultPath) {
        $result = Get-Content $resultPath -Raw | ConvertFrom-Json
        foreach ($e in @($result.log.entries)) {
            if (-not $e) { continue }
            $first = ($e.message -split "`n")[0]
            $harnessIssues += [ordered]@{ type = $e.type; ours = [bool]$e.ours; first = $first }
        }
    }
    $hGroups = $harnessIssues | Group-Object { "$($_.type)|$($_.ours)|$($_.first)" } | ForEach-Object {
        [ordered]@{ type = $_.Group[0].type; ours = $_.Group[0].ours; count = $_.Count; source = 'harness'; first = $_.Group[0].first } }
    $ourGroups = @(@($groups.Values) + @($hGroups) | Where-Object { $_ -and $_.ours } | Sort-Object { -$_.count })
    $otherGroups = @(@($groups.Values) + @($hGroups) | Where-Object { $_ -and -not $_.ours } | Sort-Object { -$_.count })

    $problems = @(); $exitCode = 0
    if (-not $run.sawProcess) { $problems += 'the game process never started'; $exitCode = 2 }
    elseif (-not $run.requestConsumed) { $problems += 'the harness never picked up the request (mod not loaded?)'; $exitCode = 2 }
    elseif ($null -eq $result) { $problems += 'no result.json'; $exitCode = 2 }
    if ($run.timedOut) { $problems += "timeout after $TimeoutSeconds s"; if ($exitCode -eq 0) { $exitCode = 2 } }
    if ($run.stillRunning) { $problems += 'a test game process could not be killed'; $exitCode = 2 }
    if ($null -ne $result) {
        if ($result.status -ne 'completed') { $problems += "harness status: $($result.status)"; if ($exitCode -eq 0) { $exitCode = 1 } }
        foreach ($c in @($result.checks)) { if ($c -and -not $c.pass) { $problems += "check $($c.name) failed: $($c.detail)"; if ($exitCode -eq 0) { $exitCode = 1 } } }
    }
    if ($ourGroups.Count -gt 0) { $problems += "$($ourGroups.Count) kind(s) of log errors from our mods"; if ($exitCode -eq 0) { $exitCode = 1 } }
    if ($StrictLog -and $otherGroups.Count -gt 0) { $problems += "$($otherGroups.Count) kind(s) of log errors from other mods/the game (-StrictLog)"; if ($exitCode -eq 0) { $exitCode = 1 } }
    if ($run.killedAfterResult) { $problems += 'the game had to be killed after writing its result' }

    # mods that were supposed to be off must not be in the loaded list
    $loadedMods = @(); $disabledButLoaded = @()
    if ($null -ne $result) { $loadedMods = @($result.mods | ForEach-Object { $_.id }) }
    if ($null -ne $modPlan -and $null -ne $result) {
        $offIds = @($modPlan.entries | ForEach-Object { if ($_.mod -match '\((.*)\)$') { $Matches[1] -split ', ' } }) | Select-Object -Unique
        $disabledButLoaded = @($offIds | Where-Object { $loadedMods -contains $_ })
        if ($modPlan.mode -eq 'OnlyMods') {
            $disabledButLoaded += @($loadedMods | Where-Object { $modPlan.keptIds -notcontains $_ })
        }
        if ($disabledButLoaded.Count) { $problems += "mods that should be off were loaded: $($disabledButLoaded -join ', ')"; if ($exitCode -eq 0) { $exitCode = 2 } }
    }
    $verdict = if ($exitCode -eq 0) { 'PASS' } elseif ($exitCode -eq 1) { 'FAIL' } else { 'ERROR' }

    $summary = [ordered]@{
        verdict = $verdict; exitCode = $exitCode; label = $label; runId = $RunId; runDir = $run.outDir; gameSeconds = $run.gameSeconds
        harnessStatus = $(if ($result) { $result.status } else { $null }); harnessVerdict = $(if ($result) { $result.verdict } else { $null })
        problems = $problems; timedOut = $run.timedOut; requestConsumed = $run.requestConsumed
        modsLoaded = $loadedMods; disabledButLoaded = $disabledButLoaded
        logErrorsOurs = $ourGroups; logErrorsOthers = $otherGroups; logLinesOursSuspicious = @($ownWarnings | Select-Object -Unique -First 50)
        prefsRestored = $run.prefsRestored; prefsChangedNotRestored = $run.prefsChanged
    }

    $color = @{ PASS = 'Green'; FAIL = 'Red'; ERROR = 'Red' }[$verdict]
    Say ''
    Say "=== $verdict  $label ($RunId, $($run.gameSeconds) s)  $($run.outDir)" $color
    if ($null -ne $result) {
        Say ("game {0}; faction {1}; map {2}; status {3}; {4} mods loaded" -f $result.gameVersion, $result.activeFaction.id, $result.newGame.map, $result.status, $loadedMods.Count)
        if ($result.population) { Say ("population: {0} adults, {1} children, {2} bots; day {3}" -f $result.population.adults, $result.population.children, $result.population.bots, $result.time.day) }
        foreach ($c in @($result.checks)) { if ($c) { Say ("  [{0}] {1}: {2}" -f $(if ($c.pass) { 'ok' } else { 'XX' }), $c.name, $c.detail) $(if ($c.pass) { 'Gray' } else { 'Red' }) } }
        foreach ($s in @($result.characterSamples) | Select-Object -First 6) { if ($s) { Say ("  {0,-6} {1,-22} model {2} ({3} v); coat {4}" -f $s.kind, $s.template, $s.body.modelAsset, $s.body.vertices, $(if ($s.body.baseMapAsset) { $s.body.baseMapAsset } else { $s.body.baseMap })) } }
        foreach ($s in @($result.screenshots)) { if ($s) { Say ("  shot {0}: {1}" -f $s.name, $(if ($s.file) { $s.file } else { 'MISSING ' + $s.error })) } }
        Say ("harness log counts: {0} errors, {1} exceptions ({2} ours)" -f $result.log.errors, $result.log.exceptions, ($result.log.ownErrors + $result.log.ownExceptions))
    }
    Say ("log issues: {0} kind(s) from our mods, {1} from other mods / the game" -f $ourGroups.Count, $otherGroups.Count)
    foreach ($g in $ourGroups | Select-Object -First 8) { Say ("  OURS  x{0} {1} [{2}]: {3}" -f $g.count, $g.type, $g.source, $g.first) 'Red' }
    foreach ($g in $otherGroups | Select-Object -First 8) { Say ("  other x{0} {1} [{2}]: {3}" -f $g.count, $g.type, $g.source, $g.first) 'DarkYellow' }
    foreach ($w in $summary.logLinesOursSuspicious | Select-Object -First 8) { Say "  ours? $w" 'Yellow' }
    if ($run.prefsRestored.Count) { Say "restored window prefs: $($run.prefsRestored -join ', ')" }
    if ($run.prefsChanged.Count) { Say "other prefs the game changed (not restored): $($run.prefsChanged -join ', ')" 'DarkGray' }
    foreach ($p in $problems) { Say "  problem: $p" $color }
    return $summary
}

# ------------------------------------------------------------------ cross-process game lock
# One test at a time per machine: a named mutex held for the whole run, plus no other Timberborn process.
# Waiters are served first come, first served: each writes a ticket file (name sorts by arrival time) into
# <TestRoot>\queue and only the oldest ticket whose process is still alive may try for the mutex. Without this,
# whoever happened to poll first after a release won, and a run could wait hours behind later arrivals.
function Get-QueueAhead([string]$queueDir, [string]$myTicket) {
    $ahead = @()
    foreach ($f in @(Get-ChildItem -LiteralPath $queueDir -Filter '*.json' -ErrorAction SilentlyContinue | Sort-Object Name)) {
        if ($f.Name -eq $myTicket) { break }
        $alive = $false; $t = $null
        try {
            $t = Get-Content -LiteralPath $f.FullName -Raw | ConvertFrom-Json
            $p = Get-Process -Id ([int]$t.pid) -ErrorAction SilentlyContinue
            # same pid and same start time = the same process (pids are reused)
            if ($p -and ($p.StartTime.ToUniversalTime().ToString('o') -eq $t.processStartedUtc)) { $alive = $true }
        } catch { }
        if ($alive) { $ahead += $t }
        # a ticket that cannot be read yet may be one another waiter is writing right now: leave young ones alone
        elseif ($null -ne $t -or ((Get-Date) - $f.LastWriteTime).TotalSeconds -gt 30) { try { Remove-Item -LiteralPath $f.FullName -Force } catch { } }
    }
    return $ahead
}

function Enter-GameLock([int]$timeoutSeconds, [string]$what) {
    $mutex = New-Object System.Threading.Mutex($false, $mutexName)
    $deadline = (Get-Date).AddSeconds($timeoutSeconds)
    $owned = $false; $lastMessage = ''
    $queueDir = Join-Path $TestRoot 'queue'
    $myTicket = '{0}-{1:D6}.json' -f (Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmssfff'), $PID
    $myTicketPath = Join-Path $queueDir $myTicket
    try {
        New-Item -ItemType Directory -Force $queueDir | Out-Null
        $ticket = [ordered]@{ pid = $PID; what = $what; queuedUtc = (Get-Date).ToUniversalTime().ToString('o')
                              processStartedUtc = (Get-Process -Id $PID).StartTime.ToUniversalTime().ToString('o') }
        [IO.File]::WriteAllText($myTicketPath, ($ticket | ConvertTo-Json), $utf8)
    } catch { $myTicketPath = $null }   # no ticket: fall back to plain polling
    $script:queueTicketPath = $myTicketPath   # also removed on every exit path of the script (main finally)
    $lastTick = Get-Date; $orphanTried = $false
    while ($true) {
        $ahead = @()
        if (-not $owned -and $myTicketPath) { $ahead = @(Get-QueueAhead $queueDir $myTicket) }
        # A hold in force (tools\game_test_hold.ps1, tools\play_timberborn.ps1: a HOLD.<pid>.json of a live process) goes
        # first: while there is one, a queued run does not even try for the lock, so it cannot slip in between the run
        # in progress and the hold. A hold file whose process is gone is not a hold (Get-LiveHolds removes it).
        $holds = @(); if (-not $owned) { $holds = @(Get-LiveHolds $TestRoot) }
        if (-not $owned -and $ahead.Count -eq 0 -and $holds.Count -eq 0) {
            try { $owned = $mutex.WaitOne(0) }
            catch {
                $inner = $_.Exception; while ($inner.InnerException) { $inner = $inner.InnerException }
                if ($inner -is [System.Threading.AbandonedMutexException] -or $_.Exception -is [System.Threading.AbandonedMutexException]) {
                    $owned = $true; Say 'The previous lock holder exited without releasing the lock; taking it over.' 'Yellow'
                } else { throw }
            }
        }
        if ($owned) {
            $procs = @(Get-Process Timberborn -ErrorAction SilentlyContinue)
            if ($procs.Count -gt 0 -and -not $orphanTried) {
                # a test game whose runner died would keep every run waiting here, unseen on the hidden desktop: stop it
                # (only the recorded pid with the recorded start time; anything else open is the owner's and is waited for)
                $orphanTried = $true
                $dead = Read-RunRecord $runRecordPath
                if ($dead -and -not (Test-RunnerAlive $dead)) {
                    $stopped = Stop-RecordedGames $dead
                    if ($stopped.killed.Count -gt 0) { Say "Stopped the test game a dead run left behind (pid $($stopped.killed -join ', '), run $($dead.runId))." 'Yellow' }
                    $procs = @(Get-Process Timberborn -ErrorAction SilentlyContinue)
                }
            }
            if ($procs.Count -eq 0) {
                Write-LockInfo $TestRoot $what
                if ($myTicketPath) { try { Remove-Item -LiteralPath $myTicketPath -Force } catch { } }
                return $mutex
            }
            $message = "Waiting for Timberborn to close (pid $($procs.Id -join ', '); not started by a test run holding the lock)."
        } else {
            $holder = '(unknown)'
            if (Test-Path $lockInfoPath) { try { $h = Get-Content $lockInfoPath -Raw | ConvertFrom-Json; $holder = "pid $($h.pid), $($h.what), since $($h.startedUtc)" } catch { } }
            $message = "Waiting for another game test to finish: $holder"
            if ($ahead.Count -gt 0) { $message = "Queued behind $($ahead.Count) earlier run(s); next: pid $($ahead[0].pid), $($ahead[0].what). Running now: $holder" }
            if ($holds.Count -gt 0) { $message = "The queue is held ($(@($holds | ForEach-Object { "pid $($_.pid): $($_.reason)" }) -join '; ')). Lock: $holder" }
        }
        # A hold pauses the queue while the owner uses the PC: held time does not count as waiting (the real time that
        # passed since the last look, not a fixed 5 s: a loop takes a little longer than its sleep).
        $now = Get-Date
        if (-not $owned -and $holds.Count -gt 0) { $deadline = $deadline + ($now - $lastTick) }
        $lastTick = $now
        if ((Get-Date) -gt $deadline) {
            Say "Gave up after $timeoutSeconds s. $message" 'Red'
            if ($myTicketPath) { try { Remove-Item -LiteralPath $myTicketPath -Force } catch { } }
            if ($owned) { $mutex.ReleaseMutex() }
            $mutex.Dispose()
            return $null
        }
        if ($message -ne $lastMessage) { Say $message 'Yellow'; $lastMessage = $message }
        Start-Sleep -Seconds 5
    }
}

function Exit-GameLock($mutex) {
    if ($null -eq $mutex) { return }
    Remove-LockInfo $TestRoot
    try { $mutex.ReleaseMutex() } catch { }
    $mutex.Dispose()
}

# Junctions $target into Mods\<name>. Returns 'created', 'existing' (already a junction to the same target) or throws.
function Install-ModJunction([string]$target, [string]$name) {
    $path = Join-Path $modsDir $name
    if (Test-Path -LiteralPath $path) {
        $item = Get-Item -LiteralPath $path -Force
        $current = @($item.Target) | Select-Object -First 1
        if ($item.LinkType -ne 'Junction' -or ($current.TrimEnd('\') -ne $target.TrimEnd('\'))) {
            throw "$path exists but is not a junction to $target; leaving it alone."
        }
        return 'existing'
    }
    New-Item -ItemType Junction -Path $path -Target $target | Out-Null
    Say "Installed: $path -> $target"
    return 'created'
}

# Cleans up after a run whose runner died (closed console, tool timeout, reboot), from its record. Called with the
# test lock in hand (or under a verified hold). Touches only what the record names: the recorded game (pid and start
# time), the recorded junctions (the link, never the target), the flags through the normal restore, the recorded
# save and request, the window prefs. Returns true when nothing of that run is left; then the record is removed.
function Clear-DeadRun($rec) {
    Say "A run that died left changes behind (run $($rec.runId), runner pid $($rec.runner.pid)): cleaning from $runRecordPath" 'Yellow'
    $stopped = Stop-RecordedGames $rec
    if ($stopped.killed.Count -gt 0) { Say "  stopped its test game (pid $($stopped.killed -join ', '))" }
    if ($stopped.alive.Count -gt 0) { Say "  its test game (pid $($stopped.alive -join ', ')) could not be stopped; nothing else was touched" 'Red'; return $false }
    $open = @(Get-Process Timberborn -ErrorAction SilentlyContinue)
    if ($open.Count -gt 0) { Say "  a Timberborn that is not that run's is open (pid $($open.Id -join ', ')): mod flags cannot be put back while it runs; nothing else was touched" 'Red'; return $false }
    $ok = $true
    if (Test-Path $pendingStatePath) {
        $state = Read-JsonFile $pendingStatePath
        if ($null -eq $state) { Say "  cannot read $pendingStatePath" 'Red'; $ok = $false }
        elseif ($state.runId -eq $rec.runId) {
            $res = Restore-ModState $state
            foreach ($r in $res.entries) { Say ("  {0,-5} {1}: before {2}, now {3}" -f $(if ($r.match) { 'ok' } else { 'DIFF' }), $r.name, $r.before, $r.afterRestore) $(if ($r.match) { 'Gray' } else { 'Red' }) }
            if ($res.ok) { Remove-Item $pendingStatePath -Force; Say "  mod flags restored and verified ($(@($res.entries).Count) value(s))" }
            else { Say '  mod flags could not be verified (see DIFF lines)' 'Red'; $ok = $false }
        }
        # a pending file of another run is not this record's business: the preflight below still refuses to start
    }
    $j = Remove-RecordedJunctions $rec $modsDir
    foreach ($x in $j.removed) { Say "  removed junction $x" }
    foreach ($x in $j.skipped) { Say "  junction left alone: $x" 'Yellow' }
    $save = Remove-RecordedSave $rec $savesDir
    if ($save) { Say "  deleted test save $save" }
    foreach ($x in @(Remove-RecordedRequests $rec $TestRoot)) { Say "  deleted request $x" }
    try {
        if ($rec.windowPrefs -and $rec.window) {
            $names = @(Restore-WindowPrefs $rec.windowPrefs $rec.window.width $rec.window.height)
            if ($names.Count -gt 0) { Say "  window prefs put back: $($names -join ', ')" }
        }
    } catch { Say "  window prefs not restored: $_" 'Yellow' }
    if ($ok) { Remove-Item -LiteralPath $runRecordPath -Force -ErrorAction SilentlyContinue; Say '  done; record removed.' 'Green' }
    return $ok
}

# ------------------------------------------------------------------ main
$lock = $null
$script:requestFile = $requestPath   # the request file of the launch in progress (set by Invoke-GameRun)
$script:launchTime = $null
$links = @()        # junctions to remove at the end: @{ path; target }
$exitCode = 2
try {
    $what = if ($RestoreModState) { "restore $RestoreModState" } elseif ($Recover) { 'recover after a dead run' } else { "$Faction test $RunId".Trim() }
    if ($DuringHold) {
        # the queue is held by tools\game_test_hold.ps1, which owns the lock for us: nobody else can start a game
        # A hold file alone proves nothing: it is written before the hold has the lock (a test may still be between two
        # launches). The hold is real only while a live hold process (pid and start time) owns the lock.
        $held = Test-HoldOwnsLock $TestRoot $mutexName
        if (-not $held.ok) { Say "-DuringHold needs the queue to be held (tools\game_test_hold.ps1): $($held.why). Not starting." 'Red'; exit 2 }
        # the test game of a run that died is ours to stop (recorded pid and start time only); any other is the owner's
        $dead = Read-RunRecord $runRecordPath
        if ($dead -and -not (Test-RunnerAlive $dead)) {
            $stopped = Stop-RecordedGames $dead
            if ($stopped.killed.Count -gt 0) { Say "Stopped the test game a dead run left behind (pid $($stopped.killed -join ', '), run $($dead.runId))." 'Yellow' }
        }
        if (@(Get-Process Timberborn -ErrorAction SilentlyContinue).Count -gt 0) { Say 'A Timberborn process is open; not starting.' 'Red'; exit 2 }
    } else {
        $lock = Enter-GameLock $WaitForGameSeconds $what
        if ($null -eq $lock) { exit 2 }
    }

    # -------------------------------------------------------------- -RestoreModState mode
    if ($RestoreModState) {
        # written as UTF-8 without a BOM; Windows PowerShell would read that as ANSI and mangle a non-ASCII mod folder
        # or Id inside a value name (the wrong value restored, and "verified" against itself)
        $state = Get-Content -LiteralPath $RestoreModState -Raw -Encoding UTF8 | ConvertFrom-Json
        $res = Restore-ModState $state
        foreach ($r in $res.entries) { Say ("  {0,-5} {1}: before {2}, now {3}" -f $(if ($r.match) { 'ok' } else { 'DIFF' }), $r.name, $r.before, $r.afterRestore) $(if ($r.match) { 'Gray' } else { 'Red' }) }
        if ($res.ok) {
            if (Test-Path $pendingStatePath) {
                $pending = Get-Content $pendingStatePath -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($pending.runId -eq $state.runId) { Remove-Item $pendingStatePath -Force; Say "removed $pendingStatePath" }
            }
            Say "Mod state restored and verified ($(@($res.entries).Count) value(s))." 'Green'; exit 0
        }
        Say 'Restore could not be verified for every value (see DIFF lines).' 'Red'; exit 2
    }

    # -------------------------------------------------------------- a run that died, or one still going
    if (Test-Path -LiteralPath $runRecordPath) {
        $rec = Read-RunRecord $runRecordPath
        if ($null -eq $rec) { Say "Cannot read $runRecordPath (the record of a run in progress or of one that died). Look at it before deleting it." 'Red'; exit 2 }
        if (Test-RunnerAlive $rec) {
            # only possible outside the queue (-DuringHold): two runs at once would change flags and junctions twice
            Say "Run $($rec.runId) (pid $($rec.runner.pid)) is still in progress; not starting next to it." 'Red'; exit 2
        }
        if (-not (Clear-DeadRun $rec)) { Say "The dead run could not be cleaned up completely; $runRecordPath stays. Not starting." 'Red'; exit 2 }
    }
    if ($Recover) {
        if (Test-Path $pendingStatePath) {
            # flags left by a run that had no record (an older runner): the plain restore
            $state = Read-JsonFile $pendingStatePath
            if ($null -eq $state) { Say "Cannot read $pendingStatePath" 'Red'; exit 2 }
            $res = Restore-ModState $state
            foreach ($r in $res.entries) { Say ("  {0,-5} {1}: before {2}, now {3}" -f $(if ($r.match) { 'ok' } else { 'DIFF' }), $r.name, $r.before, $r.afterRestore) $(if ($r.match) { 'Gray' } else { 'Red' }) }
            if (-not $res.ok) { Say 'Restore could not be verified for every value (see DIFF lines).' 'Red'; exit 2 }
            Remove-Item $pendingStatePath -Force
            Say "Mod state restored and verified ($(@($res.entries).Count) value(s))." 'Green'
        }
        Say 'Nothing of a dead run is left.' 'Green'
        $exitCode = 0
        exit 0
    }

    # -------------------------------------------------------------- preflight
    if (Test-Path $pendingStatePath) {
        Say "A previous run changed mod enable flags and did not confirm their restore: $pendingStatePath" 'Red'
        Say "Run: tools\run_game_test.ps1 -RestoreModState `"$pendingStatePath`"" 'Red'
        exit 2
    }
    if ($DisableMods.Count -gt 0 -and $OnlyMods.Count -gt 0) { Say 'Use -DisableMods or -OnlyMods, not both.' 'Red'; exit 2 }
    if (-not (Get-Process steam -ErrorAction SilentlyContinue)) {
        Say 'Steam is not running: the game may refuse to start or Workshop mods will be missing.' 'Yellow'
    }
    if (-not $RunId) { $RunId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + ($Faction.ToLowerInvariant() -replace '[^a-z0-9]', '') }
    $runDir = Join-Path $TestRoot $RunId
    New-Item -ItemType Directory -Force $runDir | Out-Null
    $settlement = 'PB_AutoTest_' + ($RunId -replace '[^A-Za-z0-9_-]', '_')

    # extra dev mods: check them before anything is installed
    $extra = @()
    foreach ($p in $ExtraMods) {
        foreach ($one in ($p -split ',')) {
            $one = $one.Trim(); if (-not $one) { continue }
            if (-not (Test-Path -LiteralPath $one -PathType Container)) { Say "Extra mod folder not found: $one" 'Red'; exit 2 }
            $full = (Resolve-Path -LiteralPath $one).Path.TrimEnd('\')
            $manifest = Read-Manifest (Join-Path $full 'manifest.json')
            if ($null -eq $manifest -or -not $manifest.Id) { Say "No manifest.json with an Id in $full" 'Red'; exit 2 }
            $extra += [pscustomobject]@{ Path = $full; Folder = (Split-Path $full -Leaf); Id = [string]$manifest.Id; Name = [string]$manifest.Name }
        }
    }
    foreach ($x in $extra) {
        foreach ($pattern in @($x.Id, $x.Folder, $x.Name)) { if ($pattern -and $OwnPatterns -notcontains $pattern) { $OwnPatterns += $pattern } }
    }

    # the record of what this run changes, on disk before the first change (-KeepSave and -KeepInstalled: what is
    # meant to stay is not recorded, so a clean-up after a death leaves it too)
    $script:runRecord = [ordered]@{
        runId = $RunId; runDir = $runDir; createdUtc = (Get-Date).ToUniversalTime().ToString('o')
        runner = [ordered]@{ pid = $PID; processStartedUtc = (Get-ProcessStartUtc $PID) }
        command = [Environment]::CommandLine
        games = @(); junctions = @(); requests = @()
        save = $(if ($KeepSave) { $null } else { Join-Path $savesDir $settlement })
        modState = $null; windowPrefs = $null; window = $null
    }
    Save-RunRecord

    # -------------------------------------------------------------- build + install (junctions)
    if (-not $NoBuild) {
        $project = Join-Path $repo 'src\devharness\PandabornDevHarness.csproj'
        $buildLog = & dotnet build $project -c Release -v q --nologo "-p:ModOut=$HarnessDir" 2>&1
        if ($LASTEXITCODE -ne 0) { $buildLog | ForEach-Object { Say "  $_" 'Red' }; Say 'Harness build failed.' 'Red'; exit 2 }
    }
    if (-not (Test-Path (Join-Path $HarnessDir 'Scripts\PandabornDevHarness.dll'))) { Say "Harness DLL missing in $HarnessDir" 'Red'; exit 2 }
    try {
        # each junction is in the record before it exists
        $harnessLink = @{ path = (Join-Path $modsDir 'PandabornDevHarness'); target = $HarnessDir }
        if (-not $KeepInstalled) { $script:runRecord.junctions = @($script:runRecord.junctions) + [ordered]@{ path = $harnessLink.path; target = $harnessLink.target }; Save-RunRecord }
        $null = Install-ModJunction $HarnessDir 'PandabornDevHarness'
        # the harness junction is removed at the end even if it was already there (it is inert without a request);
        # -KeepInstalled keeps it, and only it: an -ExtraMods junction is a live mod in the owner's game and always goes
        if (-not $KeepInstalled) { $links += $harnessLink }
        foreach ($x in $extra) {
            $extraLink = @{ path = (Join-Path $modsDir $x.Folder); target = $x.Path }
            $already = [bool](Get-Item -LiteralPath $extraLink.path -Force -ErrorAction SilentlyContinue)
            if (-not $already) { $script:runRecord.junctions = @($script:runRecord.junctions) + [ordered]@{ path = $extraLink.path; target = $extraLink.target }; Save-RunRecord }
            $how = Install-ModJunction $x.Path $x.Folder
            if ($how -eq 'created') { $links += $extraLink }
        }
    } catch { Say "$_" 'Red'; exit 2 }

    # -------------------------------------------------------------- mod flag plan (nothing is changed yet)
    $modPlan = $null
    $extraKeys = @($extra | ForEach-Object { Get-PrefValueName "ModEnabled.Local.$($_.Folder).$($_.Id)" })
    if ($DisableMods.Count -gt 0 -or $OnlyMods.Count -gt 0 -or $extra.Count -gt 0) {
        $installed = @(Get-InstalledMods)
        $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($prefsKey)
        if ($null -eq $key) { Say "HKCU\$prefsKey not found; refusing to guess." 'Red'; exit 2 }
        try {
            $toDisable = @(); $keptForDeps = @(); $notes = @(); $keptIds = @()
            $extraTokens = @($extra | ForEach-Object { $_.Id })
            if ($DisableMods.Count -gt 0) {
                $f = Find-Mods $installed $DisableMods
                if ($f.Missing.Count) { Say "Not installed (by Id, folder or name): $($f.Missing -join ', ')" 'Red'; exit 2 }
                $toDisable = @($f.Found | Where-Object { $_.Ids -notcontains $harnessId -and -not ($_.Source -eq 'Local' -and ($extra.Folder -contains $_.Origin)) })
            } elseif ($OnlyMods.Count -gt 0) {
                if ($script:manifestProblems.Count) {
                    Say "Cannot read these manifests, so -OnlyMods cannot switch every mod off reliably: $($script:manifestProblems -join '; ')" 'Red'; exit 2
                }
                $f = Find-Mods $installed ($OnlyMods + $harnessId + $extraTokens)
                if ($f.Missing.Count) { Say "Not installed (by Id, folder or name): $($f.Missing -join ', ')" 'Red'; exit 2 }
                $keep = @{}
                foreach ($m in $f.Found) { $keep["$($m.Source)|$($m.Origin)"] = $m }
                # keep what the kept mods require, transitively; the game itself does not enforce RequiredMods
                do {
                    $added = $false
                    foreach ($m in @($keep.Values)) {
                        foreach ($rid in $m.Required) {
                            $deps = @($installed | Where-Object { $_.Ids -contains $rid })
                            if ($deps.Count -eq 0) { $notes += "$($m.Ids -join '/') requires $rid, which is not installed"; continue }
                            foreach ($d in $deps) {
                                $k = "$($d.Source)|$($d.Origin)"
                                if (-not $keep.ContainsKey($k)) { $keep[$k] = $d; $keptForDeps += $d; $added = $true }
                            }
                        }
                    }
                } while ($added)
                $toDisable = @($installed | Where-Object { -not $keep.ContainsKey("$($_.Source)|$($_.Origin)") })
                $keptIds = @($keep.Values | ForEach-Object { $_.Ids })
            }
            $entries = @(); $alreadyOff = @()
            foreach ($m in $toDisable) {
                if (-not (Test-ModEnabled $key $m)) { $alreadyOff += $m; continue }
                foreach ($n in $m.Keys) {
                    $e = Read-PrefEntry $key $n
                    if ($e.existed -and $e.kind -ne 'DWord') { Say "$n has kind $($e.kind), not DWord: refusing to change it." 'Red'; exit 2 }
                    $e['mod'] = "$($m.Source)/$($m.Origin) ($($m.Ids -join ', '))"
                    $e['set'] = 0
                    $entries += $e
                }
            }
            # a mod the game has never seen has no flag and loads enabled; one that was switched off before is switched on
            foreach ($x in $extra) {
                $n = Get-PrefValueName "ModEnabled.Local.$($x.Folder).$($x.Id)"
                $e = Read-PrefEntry $key $n
                if (-not $e.existed) { continue }
                if ($e.kind -ne 'DWord') { Say "$n has kind $($e.kind), not DWord: refusing to change it." 'Red'; exit 2 }
                if ([int]$e.value -eq 1) { continue }
                $e['mod'] = "Local/$($x.Folder) ($($x.Id))"
                $e['set'] = 1
                $entries += $e
            }
        } finally { $key.Close() }
        if ($entries.Count -gt 0) {
            $modPlan = [ordered]@{
                runId = $RunId; createdUtc = (Get-Date).ToUniversalTime().ToString('o'); registryKey = "HKCU\$prefsKey"
                mode = $(if ($OnlyMods.Count) { 'OnlyMods' } elseif ($DisableMods.Count) { 'DisableMods' } else { 'ExtraMods' })
                requested = @(@($DisableMods) + @($OnlyMods) + @($extra | ForEach-Object { "+$($_.Id)" }) | Where-Object { $_ })
                keptIds = @($keptIds)
                restoreHint = "powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`" -RestoreModState `"$(Join-Path $runDir 'modstate.json')`""
                entries = $entries
                alreadyDisabled = @($alreadyOff | ForEach-Object { "$($_.Source)/$($_.Origin)" })
                keptAsDependencies = @($keptForDeps | ForEach-Object { "$($_.Source)/$($_.Origin)" })
                notes = $notes
            }
            $off = @($entries | Where-Object { $_.set -eq 0 } | ForEach-Object { $_.mod } | Select-Object -Unique)
            $on = @($entries | Where-Object { $_.set -eq 1 } | ForEach-Object { $_.mod } | Select-Object -Unique)
            Say ("Mod flags for this run ({0}): off {1}: {2}" -f $modPlan.mode, $off.Count, ($off -join '; ')) 'Cyan'
            if ($on.Count) { Say "  switched on: $($on -join '; ')" 'Cyan' }
            if ($keptForDeps.Count) { Say "  kept as required dependencies: $($modPlan.keptAsDependencies -join ', ')" }
            foreach ($n in $notes) { Say "  note: $n" 'Yellow' }
        }
    }

    if ($DryRun) {
        if ($null -eq $modPlan) { Say 'Dry run: no mod flags would change.' }
        else {
            foreach ($e in $modPlan.entries) { Say ("  would set {0} = {1} (now {2}) for {3}" -f $e.name, $e.set, $(if ($e.existed) { "$($e.kind) $($e.value)" } else { 'absent' }), $e.mod) }
            if ($modPlan.alreadyDisabled.Count) { Say "  already off: $($modPlan.alreadyDisabled -join ', ')" }
        }
        $exitCode = 0
        exit 0
    }

    # The lock was taken with no Timberborn open, but the harness build above takes a while and the owner may have
    # started the game since (Steam also restarts it once at launch). Nothing is changed yet: stop here.
    $open = @(Get-Process Timberborn -ErrorAction SilentlyContinue)
    if ($open.Count -gt 0) { Say "Timberborn was started (pid $($open.Id -join ', ')) while this run prepared; not changing mod flags, not starting a test game." 'Red'; exit 2 }

    # -------------------------------------------------------------- run (flags changed only inside try/finally)
    $runs = @()
    $modRestore = $null
    $script:launchTime = Get-Date
    $script:savesDeleted = @()
    $fatal = $null
    $script:leftBehind = $true   # until the clean-up below says otherwise, the record stays for the next lock holder
    try {
        if ($null -ne $modPlan) {
            # the exact prior values go to disk before anything changes
            $stateText = $modPlan | ConvertTo-Json -Depth 6
            [IO.File]::WriteAllText((Join-Path $runDir 'modstate.json'), $stateText, $utf8)
            [IO.File]::WriteAllText($pendingStatePath, $stateText, $utf8)
            $script:runRecord.modState = (Join-Path $runDir 'modstate.json'); Save-RunRecord
            $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($prefsKey, $true)
            try {
                foreach ($e in $modPlan.entries) { $key.SetValue($e.name, [int]$e.set, [Microsoft.Win32.RegistryValueKind]::DWord) }
                $key.Flush()
            } finally { $key.Close() }
            Say "Mod flags set for this run ($(@($modPlan.entries).Count) value(s)); prior state in $(Join-Path $runDir 'modstate.json')" 'Cyan'
        }

        $request = New-Request $runDir @{}
        $first = Invoke-GameRun $runDir $request @()
        $runs += @{ label = 'new game'; run = $first }

        if ($SaveAndReload) {
            $saveFile = Join-Path $savesDir "$settlement\$saveName.timber"
            if (-not $first.stillRunning -and (Test-Path -LiteralPath $saveFile)) {
                $reloadDir = Join-Path $runDir 'reload'
                $reloadShots = @(@('overview@start', 'adult@start', 'child@start') | ForEach-Object {
                    $p = $_.Split('@'); [ordered]@{ name = "$($p[0])_$($p[1])"; kind = $p[0]; at = $p[1] } })
                $reloadRequest = New-Request $reloadDir @{ loadSave = $true; save = $null; buildings = @(); screenshots = $reloadShots
                                                           factionPanelShots = $false; run = [ordered]@{ realSeconds = $ReloadSeconds } }
                $second = Invoke-GameRun $reloadDir $reloadRequest @('-saveName', "`"$saveName`"", '-settlementName', "`"$settlement`"")
                $runs += @{ label = 'reload'; run = $second }
            } else {
                Say "No save at $saveFile; skipping the reload launch." 'Red'
                $runs += @{ label = 'reload'; run = $null }
            }
        }
    } catch {
        $fatal = $_
        Say "Run aborted: $_" 'Red'
    } finally {
        # never leave the game running, and never restore flags while it runs (it rewrites them on exit)
        $alive = Stop-TestGame $script:launchTime
        if ($alive) { Say 'A test game process is still alive and could not be killed.' 'Red' }
        # first of all: an unconsumed request sits at the harness's default path, and the harness junction is still in
        # Mods, so a game the owner starts now (the wait below can last as long as they play) would run the test itself
        try { if (Test-Path -LiteralPath $script:requestFile) { Remove-Item -LiteralPath $script:requestFile -Force } } catch { }
        if ($null -ne $modPlan) {
            $state = Get-Content -LiteralPath (Join-Path $runDir 'modstate.json') -Raw -Encoding UTF8 | ConvertFrom-Json
            $modRestore = Restore-ModState $state
            [IO.File]::WriteAllText((Join-Path $runDir 'modstate.restore.json'), ($modRestore | ConvertTo-Json -Depth 6), $utf8)
            $ownerGames = @(Get-OwnerGames)
            if ($ownerGames.Count -gt 0) {
                Say "The owner's Timberborn (pid $($ownerGames.Id -join ', ')) is open. Flags are restored now and checked again when it closes; the queue waits." 'Yellow'
                while (@(Get-OwnerGames).Count -gt 0) { Start-Sleep -Seconds 5 }
                $modRestore = Restore-ModState $state
                [IO.File]::WriteAllText((Join-Path $runDir 'modstate.restore.json'), ($modRestore | ConvertTo-Json -Depth 6), $utf8)
            }
            if ($modRestore.ok -and -not $alive) {
                Remove-Item $pendingStatePath -Force -ErrorAction SilentlyContinue
                Say "Mod flags restored and verified: $(@($modRestore.entries).Count) value(s) match the recorded prior state." 'Green'
            } else {
                Say "MOD FLAGS NOT VERIFIED. Restore by hand once the game is closed: $($modPlan.restoreHint)" 'Red'
            }
        }
        if (-not $KeepSave -and (Test-Path $savesDir)) {
            Get-ChildItem $savesDir -Directory | Where-Object { $_.Name -like 'PB_AutoTest*' -and $_.Name -eq $settlement } | ForEach-Object {
                Remove-Item $_.FullName -Recurse -Force
                $script:savesDeleted += $_.Name
            }
        }
        # reached only when nothing above threw: the game is gone, the flags are back (or there were none), the save
        # and the request are deleted. Otherwise the record stays and the next lock holder cleans from it.
        $script:leftBehind = [bool]($alive -or ($null -ne $modPlan -and -not ($modRestore -and $modRestore.ok)))
    }

    # -------------------------------------------------------------- verdicts
    $exitCode = 0
    $summaries = @()
    foreach ($r in $runs) {
        if ($null -eq $r.run) {
            $summaries += [ordered]@{ label = $r.label; verdict = 'ERROR'; exitCode = 2; problems = @('no save to reload') }
            $exitCode = 2; continue
        }
        $s = Get-RunVerdict $r.run $r.label
        [IO.File]::WriteAllText((Join-Path $r.run.outDir 'summary.json'), ($s | ConvertTo-Json -Depth 6), $utf8)
        $summaries += $s
        if ($s.exitCode -eq 2) { $exitCode = 2 } elseif ($s.exitCode -eq 1 -and $exitCode -eq 0) { $exitCode = 1 }
    }
    if ($null -ne $fatal -or $runs.Count -eq 0) { $exitCode = 2 }
    if ($null -ne $modPlan -and -not $modRestore.ok) { $exitCode = 2 }
    $overall = [ordered]@{
        exitCode = $exitCode; runId = $RunId; runDir = $runDir; runs = $summaries; savesDeleted = $script:savesDeleted
        extraMods = @($extra | ForEach-Object { [ordered]@{ id = $_.Id; folder = $_.Folder; path = $_.Path } })
        modState = $(if ($null -ne $modPlan) { [ordered]@{ mode = $modPlan.mode; requested = $modPlan.requested; restoredAndVerified = $modRestore.ok; entries = $modRestore.entries; alreadyDisabled = $modPlan.alreadyDisabled; keptAsDependencies = $modPlan.keptAsDependencies } } else { $null })
        error = $(if ($fatal) { [string]$fatal } else { $null })
    }
    [IO.File]::WriteAllText((Join-Path $runDir 'overall.json'), ($overall | ConvertTo-Json -Depth 8), $utf8)
    if ($script:savesDeleted.Count) { Say "deleted test save(s): $($script:savesDeleted -join ', ')" }
    Say ("overall exit code {0}" -f $exitCode) $(if ($exitCode -eq 0) { 'Green' } else { 'Red' })
} finally {
    # junctions this run installed go away on every exit path; a test game must not be running when they do
    if ($links.Count -gt 0) {
        if ($null -ne $script:launchTime) { $null = Stop-TestGame $script:launchTime }
        foreach ($l in $links) {
            if (Test-Path -LiteralPath $l.path) {
                $item = Get-Item -LiteralPath $l.path -Force
                $current = @($item.Target) | Select-Object -First 1
                if ($item.LinkType -eq 'Junction' -and $current.TrimEnd('\') -eq $l.target.TrimEnd('\')) {
                    try {
                        [IO.Directory]::Delete($l.path, $false)   # removes the junction only, never the target
                        Say "removed junction $($l.path)" 'DarkGray'
                    } catch { Say "could not remove junction $($l.path): $_" 'Red'; $script:leftBehind = $true }
                }
            }
        }
    }
    # the pending-run record goes when nothing of this run is left on the machine; otherwise it stays, and the next
    # lock holder (or tools\play_timberborn.ps1) finishes the clean-up from it
    if ($null -ne $script:runRecord) {
        if ($script:leftBehind) { Say "Something of this run may be left on the machine: $runRecordPath stays for the next run to clean from." 'Yellow' }
        else { Remove-Item -LiteralPath $runRecordPath -Force -ErrorAction SilentlyContinue }
    }
    # our handle on the hidden desktop (it would stay open in a session that called this script with &)
    if ('PandabornTest.HiddenDesktop' -as [type]) { try { [PandabornTest.HiddenDesktop]::Close() } catch { } }
    Exit-GameLock $lock
    if ($script:queueTicketPath) { try { Remove-Item -LiteralPath $script:queueTicketPath -Force -ErrorAction SilentlyContinue } catch { } }
}
exit $exitCode

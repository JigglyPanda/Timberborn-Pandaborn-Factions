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
$mutexName = 'Global\PandabornGameTest'
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
        $override = Get-Content $RequestJson -Raw | ConvertFrom-Json
        foreach ($p in $override.PSObject.Properties) { $request[$p.Name] = $p.Value }
    }
    foreach ($k in $extra.Keys) { $request[$k] = $extra[$k] }
    $request.outputDir = $outDir; $request.runId = $RunId
    return $request
}

# Launches the game with a request, waits for it to finish (or kills it), restores the window prefs. Never returns
# with a test process still alive unless it could not be killed (reported in .stillRunning).
function Invoke-GameRun([string]$outDir, $request, [string[]]$extraArgs) {
    New-Item -ItemType Directory -Force $outDir | Out-Null
    [IO.File]::WriteAllText($requestPath, ($request | ConvertTo-Json -Depth 10), $utf8)
    $prefsBefore = Get-PrefsSnapshot
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
        if ($alive) { $ahead += $t } else { try { Remove-Item -LiteralPath $f.FullName -Force } catch { } }
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
    while ($true) {
        $ahead = @()
        if (-not $owned -and $myTicketPath) { $ahead = @(Get-QueueAhead $queueDir $myTicket) }
        if (-not $owned -and $ahead.Count -eq 0) {
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
            if ($procs.Count -eq 0) {
                $info = [ordered]@{ pid = $PID; what = $what; user = $env:USERNAME; startedUtc = (Get-Date).ToUniversalTime().ToString('o')
                                    command = [Environment]::CommandLine }
                try { New-Item -ItemType Directory -Force $TestRoot | Out-Null; [IO.File]::WriteAllText($lockInfoPath, ($info | ConvertTo-Json), $utf8) } catch { }
                if ($myTicketPath) { try { Remove-Item -LiteralPath $myTicketPath -Force } catch { } }
                return $mutex
            }
            $message = "Waiting for Timberborn to close (pid $($procs.Id -join ', '); not started by a test run holding the lock)."
        } else {
            $holder = '(unknown)'
            if (Test-Path $lockInfoPath) { try { $h = Get-Content $lockInfoPath -Raw | ConvertFrom-Json; $holder = "pid $($h.pid), $($h.what), since $($h.startedUtc)" } catch { } }
            $message = "Waiting for another game test to finish: $holder"
            if ($ahead.Count -gt 0) { $message = "Queued behind $($ahead.Count) earlier run(s); next: pid $($ahead[0].pid), $($ahead[0].what). Running now: $holder" }
        }
        # tools\game_test_hold.ps1 pauses the queue while the owner uses the PC: held time does not count as waiting.
        if (-not $owned -and (Test-Path (Join-Path $TestRoot 'HOLD'))) { $deadline = $deadline.AddSeconds(5) }
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
    try {
        if (Test-Path $lockInfoPath) {
            $h = Get-Content $lockInfoPath -Raw | ConvertFrom-Json
            if ($h.pid -eq $PID) { Remove-Item $lockInfoPath -Force }
        }
    } catch { }
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

# ------------------------------------------------------------------ main
$lock = $null
$script:launchTime = $null
$links = @()        # junctions to remove at the end: @{ path; target }
$exitCode = 2
try {
    $what = if ($RestoreModState) { "restore $RestoreModState" } else { "$Faction test $RunId".Trim() }
    if ($DuringHold) {
        # the queue is held by tools\game_test_hold.ps1, which owns the lock for us: nobody else can start a game
        if (-not (Test-Path (Join-Path $TestRoot 'HOLD'))) { Say '-DuringHold needs the queue to be held (tools\game_test_hold.ps1).' 'Red'; exit 2 }
        if (@(Get-Process Timberborn -ErrorAction SilentlyContinue).Count -gt 0) { Say 'A Timberborn process is open; not starting.' 'Red'; exit 2 }
    } else {
        $lock = Enter-GameLock $WaitForGameSeconds $what
        if ($null -eq $lock) { exit 2 }
    }

    # -------------------------------------------------------------- -RestoreModState mode
    if ($RestoreModState) {
        $state = Get-Content -LiteralPath $RestoreModState -Raw | ConvertFrom-Json
        $res = Restore-ModState $state
        foreach ($r in $res.entries) { Say ("  {0,-5} {1}: before {2}, now {3}" -f $(if ($r.match) { 'ok' } else { 'DIFF' }), $r.name, $r.before, $r.afterRestore) $(if ($r.match) { 'Gray' } else { 'Red' }) }
        if ($res.ok) {
            if (Test-Path $pendingStatePath) {
                $pending = Get-Content $pendingStatePath -Raw | ConvertFrom-Json
                if ($pending.runId -eq $state.runId) { Remove-Item $pendingStatePath -Force; Say "removed $pendingStatePath" }
            }
            Say "Mod state restored and verified ($(@($res.entries).Count) value(s))." 'Green'; exit 0
        }
        Say 'Restore could not be verified for every value (see DIFF lines).' 'Red'; exit 2
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

    # -------------------------------------------------------------- build + install (junctions)
    if (-not $NoBuild) {
        $project = Join-Path $repo 'src\devharness\PandabornDevHarness.csproj'
        $buildLog = & dotnet build $project -c Release -v q --nologo "-p:ModOut=$HarnessDir" 2>&1
        if ($LASTEXITCODE -ne 0) { $buildLog | ForEach-Object { Say "  $_" 'Red' }; Say 'Harness build failed.' 'Red'; exit 2 }
    }
    if (-not (Test-Path (Join-Path $HarnessDir 'Scripts\PandabornDevHarness.dll'))) { Say "Harness DLL missing in $HarnessDir" 'Red'; exit 2 }
    try {
        $null = Install-ModJunction $HarnessDir 'PandabornDevHarness'
        # the harness junction is removed at the end even if it was already there (it is inert without a request)
        if (-not $KeepInstalled) { $links += @{ path = (Join-Path $modsDir 'PandabornDevHarness'); target = $HarnessDir } }
        foreach ($x in $extra) {
            $how = Install-ModJunction $x.Path $x.Folder
            if ($how -eq 'created' -and -not $KeepInstalled) { $links += @{ path = (Join-Path $modsDir $x.Folder); target = $x.Path } }
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

    # -------------------------------------------------------------- run (flags changed only inside try/finally)
    $runs = @()
    $modRestore = $null
    $script:launchTime = Get-Date
    $script:savesDeleted = @()
    $fatal = $null
    try {
        if ($null -ne $modPlan) {
            # the exact prior values go to disk before anything changes
            $stateText = $modPlan | ConvertTo-Json -Depth 6
            [IO.File]::WriteAllText((Join-Path $runDir 'modstate.json'), $stateText, $utf8)
            [IO.File]::WriteAllText($pendingStatePath, $stateText, $utf8)
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
        if ($null -ne $modPlan) {
            $state = Get-Content -LiteralPath (Join-Path $runDir 'modstate.json') -Raw | ConvertFrom-Json
            $modRestore = Restore-ModState $state
            [IO.File]::WriteAllText((Join-Path $runDir 'modstate.restore.json'), ($modRestore | ConvertTo-Json -Depth 6), $utf8)
            if ($modRestore.ok -and -not $alive) {
                Remove-Item $pendingStatePath -Force -ErrorAction SilentlyContinue
                Say "Mod flags restored and verified: $(@($modRestore.entries).Count) value(s) match the recorded prior state." 'Green'
            } else {
                Say "MOD FLAGS NOT VERIFIED. Restore by hand once the game is closed: $($modPlan.restoreHint)" 'Red'
            }
        }
        if (Test-Path $requestPath) { Remove-Item $requestPath -Force }
        if (-not $KeepSave -and (Test-Path $savesDir)) {
            Get-ChildItem $savesDir -Directory | Where-Object { $_.Name -like 'PB_AutoTest*' -and $_.Name -eq $settlement } | ForEach-Object {
                Remove-Item $_.FullName -Recurse -Force
                $script:savesDeleted += $_.Name
            }
        }
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
                    [IO.Directory]::Delete($l.path, $false)   # removes the junction only, never the target
                    Say "removed junction $($l.path)" 'DarkGray'
                }
            }
        }
    }
    Exit-GameLock $lock
    if ($script:queueTicketPath) { try { Remove-Item -LiteralPath $script:queueTicketPath -Force -ErrorAction SilentlyContinue } catch { } }
}
exit $exitCode

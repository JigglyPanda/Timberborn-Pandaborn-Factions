# Shared by run_game_test.ps1, game_test_hold.ps1, play_timberborn.ps1 and pandaborn.ps1 (dot-sourced).
#
# Functions only: no state, and every folder and name is a parameter, so each one can be tried in a scratch folder
# with a scratch mutex name (tools\tests\game_lock.trial.ps1 does exactly that). Nothing here reads or writes the
# registry.
#
# Files in <TestRoot> (E:\PandabornDev\build\test):
#   gametest.lock.json   who owns the test lock now (pid, start time, what)
#   HOLD.<pid>.json      one per holder (game_test_hold.ps1, play_timberborn.ps1): pid, start time, kind, reason.
#                        A hold is in force while any of these names a process that is still alive. One whose process
#                        is gone is stale: ignored and removed by whoever sees it. (A file plainly named HOLD is the
#                        old format: ignored.)
#   run.pending.json     what the run in progress has changed on this machine, written before the first change and
#                        removed on a clean exit. If its runner is dead, the next lock holder cleans from it.

$script:GameLockUtf8 = New-Object System.Text.UTF8Encoding($false)

function Get-UtcTicks($Value) {
    if ($null -eq $Value) { return -1 }
    if ($Value -is [datetime]) { return $Value.ToUniversalTime().Ticks }
    try {
        return [datetime]::Parse([string]$Value, [Globalization.CultureInfo]::InvariantCulture,
                                 [Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime().Ticks
    } catch { return -1 }
}

function Get-ProcessStartUtc([int]$ProcessId) {
    try { return (Get-Process -Id $ProcessId -ErrorAction Stop).StartTime.ToUniversalTime().ToString('o') } catch { return $null }
}

# True when the process with this pid is the very process that was recorded. Pids are reused; a pid with its start
# time is not. Everything that kills a process or takes something over from one goes through here.
function Test-SameProcess($ProcessId, $StartedUtc, [string]$Name = '') {
    if ($null -eq $ProcessId -or $null -eq $StartedUtc) { return $false }
    $want = Get-UtcTicks $StartedUtc
    if ($want -lt 0) { return $false }
    try {
        $p = Get-Process -Id ([int]$ProcessId) -ErrorAction Stop
        if ($Name -and $p.ProcessName -ne $Name) { return $false }
        return ($p.StartTime.ToUniversalTime().Ticks -eq $want)
    } catch { return $false }
}

# True when $Path is strictly inside $Root (not $Root itself), by full path, case-insensitive.
function Test-PathUnder([string]$Path, [string]$Root) {
    if (-not $Path -or -not $Root) { return $false }
    try {
        $full = [IO.Path]::GetFullPath($Path).TrimEnd('\')
        $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\')
    } catch { return $false }
    return $full.StartsWith($rootFull + '\', [StringComparison]::OrdinalIgnoreCase)
}

function Read-JsonFile([string]$Path) {
    try { return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json) } catch { return $null }
}

# Whole file or nothing: a reader never sees half a record.
function Write-JsonFile([string]$Path, $Value, [int]$Depth = 8) {
    $tmp = "$Path.$PID.tmp"
    [IO.File]::WriteAllText($tmp, ($Value | ConvertTo-Json -Depth $Depth), $script:GameLockUtf8)
    Move-Item -LiteralPath $tmp -Destination $Path -Force
}

# ------------------------------------------------------------------ the lock and its holder file

# WaitOne(0) that treats a lock abandoned by a dead holder as taken by us. Returns true when we own it now.
function Enter-MutexNoWait($Mutex, [int]$Milliseconds = 0) {
    try { return $Mutex.WaitOne($Milliseconds) }
    catch {
        $inner = $_.Exception; while ($inner.InnerException) { $inner = $inner.InnerException }
        if ($inner -is [System.Threading.AbandonedMutexException] -or $_.Exception -is [System.Threading.AbandonedMutexException]) { return $true }
        throw
    }
}

function Write-LockInfo([string]$TestRoot, [string]$What) {
    $info = [ordered]@{ pid = $PID; processStartedUtc = (Get-ProcessStartUtc $PID); what = $What; user = $env:USERNAME
                        startedUtc = (Get-Date).ToUniversalTime().ToString('o'); command = [Environment]::CommandLine }
    try { New-Item -ItemType Directory -Force $TestRoot | Out-Null; Write-JsonFile (Join-Path $TestRoot 'gametest.lock.json') $info } catch { }
}

# Removes the holder file if it is ours.
function Remove-LockInfo([string]$TestRoot) {
    $path = Join-Path $TestRoot 'gametest.lock.json'
    try { $h = Read-JsonFile $path; if ($h -and $h.pid -eq $PID) { Remove-Item -LiteralPath $path -Force } } catch { }
}

function Get-LockHolderText([string]$TestRoot) {
    $h = Read-JsonFile (Join-Path $TestRoot 'gametest.lock.json')
    if ($null -eq $h) { return '(unknown)' }
    return "pid $($h.pid), $($h.what), since $($h.startedUtc)"
}

# ------------------------------------------------------------------ holds

function New-HoldFile([string]$TestRoot, [string]$Kind, [string]$Reason) {
    New-Item -ItemType Directory -Force $TestRoot | Out-Null
    $path = Join-Path $TestRoot ("HOLD.{0}.json" -f $PID)
    $hold = [ordered]@{ pid = $PID; processStartedUtc = (Get-ProcessStartUtc $PID); kind = $Kind; reason = $Reason
                        createdUtc = (Get-Date).ToUniversalTime().ToString('o') }
    Write-JsonFile $path $hold
    return $path
}

# The holds in force: every HOLD.<pid>.json whose process is alive. Stale ones are removed on sight.
function Get-LiveHolds([string]$TestRoot) {
    $live = @()
    foreach ($f in @(Get-ChildItem -LiteralPath $TestRoot -Filter 'HOLD.*.json' -File -ErrorAction SilentlyContinue)) {
        $h = Read-JsonFile $f.FullName
        if ($null -eq $h) {
            # unreadable: gone already, or being written; an old one is rubbish
            if (((Get-Date) - $f.LastWriteTime).TotalSeconds -gt 30) { try { Remove-Item -LiteralPath $f.FullName -Force } catch { } }
            continue
        }
        if (Test-SameProcess $h.pid $h.processStartedUtc) {
            $live += [pscustomobject]@{ pid = [int]$h.pid; processStartedUtc = $h.processStartedUtc; kind = [string]$h.kind
                                        reason = [string]$h.reason; path = $f.FullName }
        } else { try { Remove-Item -LiteralPath $f.FullName -Force } catch { } }
    }
    return $live
}

# Is the test lock owned, right now, by a live hold? The hold file alone proves nothing (it is written before the hold
# has the lock), and the holder file alone proves nothing either (it stays behind when its writer is killed).
# Returns @{ ok; why; holder }.
function Test-HoldOwnsLock([string]$TestRoot, [string]$MutexName) {
    $holds = @(Get-LiveHolds $TestRoot)
    if ($holds.Count -eq 0) { return @{ ok = $false; why = 'no hold is in force (no HOLD.<pid>.json of a live process)'; holder = $null } }
    $probe = New-Object System.Threading.Mutex($false, $MutexName)
    $free = $false
    try { $free = Enter-MutexNoWait $probe } catch { $free = $false }
    if ($free) { try { $probe.ReleaseMutex() } catch { } }
    $probe.Dispose()
    if ($free) { return @{ ok = $false; why = 'a hold file exists but nobody owns the test lock (the hold script is not holding yet, or is gone)'; holder = $null } }
    $h = Read-JsonFile (Join-Path $TestRoot 'gametest.lock.json')
    $mine = @($holds | Where-Object { $h -and $_.pid -eq [int]$h.pid -and (Test-SameProcess $h.pid $h.processStartedUtc) })
    if ($mine.Count -eq 0) {
        return @{ ok = $false; why = "the test lock is owned by something that is not a live hold: $(Get-LockHolderText $TestRoot)"; holder = $h }
    }
    return @{ ok = $true; why = "held by pid $($h.pid): $($h.what)"; holder = $h }
}

# ------------------------------------------------------------------ install (tools\pandaborn.ps1)

# The install stage takes the test lock for the mirror, without waiting. With -CallerHoldsLock it takes nothing and
# checks instead that a live hold owns the lock. Returns @{ ok; why; mutex }.
function Enter-InstallLock([string]$TestRoot, [string]$MutexName, [bool]$CallerHoldsLock, [string]$What = 'install') {
    if ($CallerHoldsLock) {
        $c = Test-HoldOwnsLock $TestRoot $MutexName
        return @{ ok = [bool]$c.ok; why = $c.why; mutex = $null }
    }
    $mutex = New-Object System.Threading.Mutex($false, $MutexName)
    $got = $false
    try { $got = Enter-MutexNoWait $mutex } catch { $got = $false }
    if (-not $got) {
        $mutex.Dispose()
        return @{ ok = $false; why = "the test lock is taken: $(Get-LockHolderText $TestRoot)"; mutex = $null }
    }
    Write-LockInfo $TestRoot $What
    return @{ ok = $true; why = 'lock taken'; mutex = $mutex }
}

function Exit-InstallLock($Lock, [string]$TestRoot) {
    if ($null -eq $Lock -or $null -eq $Lock.mutex) { return }
    Remove-LockInfo $TestRoot
    try { $Lock.mutex.ReleaseMutex() } catch { }
    $Lock.mutex.Dispose()
    $Lock.mutex = $null
}

# ------------------------------------------------------------------ the pending-run record

function Read-RunRecord([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    return (Read-JsonFile $Path)
}

function Test-RunnerAlive($Record) {
    if ($null -eq $Record -or $null -eq $Record.runner) { return $false }
    return (Test-SameProcess $Record.runner.pid $Record.runner.processStartedUtc)
}

# Stops the recorded test games and nothing else: a process is touched only if its pid AND its start time (and its
# name) are the recorded ones. Returns @{ killed = pids; alive = pids that would not die }.
function Stop-RecordedGames($Record, [string]$ProcessName = 'Timberborn', [int]$WaitSeconds = 30) {
    $killed = @()
    $games = @(); if ($Record) { $games = @($Record.games | Where-Object { $_ }) }
    foreach ($g in $games) {
        if (Test-SameProcess $g.pid $g.processStartedUtc $ProcessName) {
            try { Stop-Process -Id ([int]$g.pid) -Force -ErrorAction Stop } catch { }
            $killed += [int]$g.pid
        }
    }
    $alive = @()
    for ($i = 0; $i -le $WaitSeconds; $i++) {
        $alive = @($games | Where-Object { Test-SameProcess $_.pid $_.processStartedUtc $ProcessName } | ForEach-Object { [int]$_.pid })
        if ($alive.Count -eq 0) { break }
        Start-Sleep -Seconds 1
    }
    return @{ killed = $killed; alive = $alive }
}

# Removes the recorded junctions: only a link directly in $ModsDir that is a junction and still points at the recorded
# target. The link goes, never the target. Returns @{ removed; skipped }.
function Remove-RecordedJunctions($Record, [string]$ModsDir) {
    $removed = @(); $skipped = @()
    $modsFull = [IO.Path]::GetFullPath($ModsDir).TrimEnd('\')
    foreach ($j in @($Record.junctions | Where-Object { $_ })) {
        $path = [string]$j.path
        try {
            if ((Split-Path ([IO.Path]::GetFullPath($path)) -Parent).TrimEnd('\') -ne $modsFull) { $skipped += "$path (not directly in $ModsDir)"; continue }
            $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
            if ($null -eq $item) { continue }   # gone already
            $current = [string](@($item.Target) | Select-Object -First 1)
            if ($item.LinkType -ne 'Junction') { $skipped += "$path (not a junction)"; continue }
            if ($current.TrimEnd('\') -ne ([string]$j.target).TrimEnd('\')) { $skipped += "$path (points at $current now)"; continue }
            [IO.Directory]::Delete($path, $false)
            $removed += $path
        } catch { $skipped += "$path ($_)" }
    }
    return @{ removed = $removed; skipped = $skipped }
}

# Deletes the recorded test save: only a real folder directly in $SavesDir whose name starts with PB_AutoTest_.
function Remove-RecordedSave($Record, [string]$SavesDir) {
    $path = [string]$Record.save
    if (-not $path) { return $null }
    try {
        $full = [IO.Path]::GetFullPath($path)
        if ((Split-Path $full -Parent).TrimEnd('\') -ne [IO.Path]::GetFullPath($SavesDir).TrimEnd('\')) { return $null }
        if ((Split-Path $full -Leaf) -notlike 'PB_AutoTest_*') { return $null }
        $item = Get-Item -LiteralPath $full -Force -ErrorAction SilentlyContinue
        if ($null -eq $item -or -not $item.PSIsContainer -or $item.LinkType) { return $null }
        Remove-Item -LiteralPath $full -Recurse -Force
        return $full
    } catch { return $null }
}

# Deletes the recorded request files: only files inside $TestRoot named request.json or request.in.json.
function Remove-RecordedRequests($Record, [string]$TestRoot) {
    $removed = @()
    foreach ($path in @($Record.requests | Where-Object { $_ })) {
        $path = [string]$path
        if (-not (Test-PathUnder $path $TestRoot)) { continue }
        if (@('request.json', 'request.in.json') -notcontains (Split-Path $path -Leaf)) { continue }
        if (Test-Path -LiteralPath $path -PathType Leaf) { try { Remove-Item -LiteralPath $path -Force; $removed += $path } catch { } }
    }
    return $removed
}

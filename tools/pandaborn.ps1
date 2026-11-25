<#
.SYNOPSIS
  One command for the Pandaborn - Factions build: pin, generate, validate, code, bundles, assemble, install, test,
  package, all.

.DESCRIPTION
  powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 <stage> [options]

  pin       Compare the installed game, its Unity version and the vanilla blueprint dump with catalogue/vanilla.pin.json.
            -Accept rewrites the pin (after reviewing tools/game_diff.py).
  generate  catalogue/ -> E:\PandabornDev\build\gen\PandabornFactions (blueprints, collections, modifiers, loc), with
            .provenance.json, .report.json and .grid.json next to it. -Lock appends new ids to catalogue/ids.lock.json;
            -DryRun prints the diff and writes nothing; -AcceptPin generates against a game that differs from the pin.
  models    Runs every art/models/<Id>/build.py (the building kit; -Plants adds art/plants/<Id>/build.py) with the
            art venv into E:\PandabornDev\build\models\<Id>. The meshes never enter git; assemble copies the
            ones the catalogue adopts (model = "<Id>") into the mod, from <GenDir>.models.json.
  code      Builds src/code (Bootstrap, Specs, Core, every module; the Look module brings the pandabornlook bundle)
            into E:\PandabornDev\build\code, and dumps the mod's own spec classes for the validator. On by default;
            -NoCode builds the data-only fallback (the mod must still be playable, with the Folktails look).
  bundles   Copies every built Pandaborn asset bundle (pandaborn*_win / _mac, never renamed) from -BundleDirs into the
            staging folder: today the plants (E:\PandabornDev\build\plants\AssetBundles, tools/build_plants.ps1).
            The look bundle comes with the code. Fails when an adopted model needs a bundle that is not built.
  assemble  Mirrors mod/PandabornFactions (hand-written files), the generated data, the two panda body meshes (not in
            git) and the code/bundle outputs into the staging folder E:\PandabornDev\build\stage\PandabornFactions.
            A generated file landing on a hand-written one is an error. Nothing installed is touched.
  validate  tools/validate.py on the staging folder (schema, ids, lock, needs, assets...).
  gate      THE INSTALL GATE: builds a dev copy of the staging folder (proto/foundation/build.ps1 -Name pbgate-<hash>
            -Staged: the staged files as they are, code included; only manifest.json is replaced) and runs
            the generated grid request on it with the installed faction switched off (every placeable template placed
            and finished, recipes on, a speed ladder, three in-game hours). On a pass it writes <StageDir>.gate.json
            with the staging folder's content hash, the hash of the code files it ran, every file of the copy that
            differed from the stage, the game version, the hash of the grid request and the mods that were loaded;
            install refuses a staging folder without a matching gate, and a gate from another game version.
            Queues behind other game tests (-WaitForGameSeconds 10800).
            gate -Prune does not run the gate: it removes the pbgate-<hash> copies in E:\PandabornDev\build\proto that
            are not the current stage's (not one a run has junctioned into Mods, not one younger than 12 hours);
            with -DryRun it only lists them with their sizes.
  install   Mirrors the validated staging folder into E:\PandabornDev\build\PandabornFactions (the folder the game's Mods
            junction points at) and makes the junction, exactly as tools/build.ps1 always did. Refuses if validation
            failed in this run. Never touches any other Mods entry and never replaces a real folder.
            Takes the game-test lock for the mirror, without waiting: if a test (or a hold) has it, install refuses and
            names the holder. -CallerHoldsLock: the caller holds the queue (tools\game_test_hold.ps1, still running);
            install then takes nothing and checks that a live hold owns the lock. Refuses while Timberborn runs.
            -GateOverride "<reason>" installs without a passing gate (logged once validation has passed). In a run
            that has the gate stage (all) it never applies: a failed gate stops the run before install.
  test      tools/run_game_test.ps1 -Faction Inkpaws with the generated grid request (every placeable template),
            on Plains with -OnlyMods JigglyPanda.PandabornFactions. -TestArgs passes more arguments.
  package   Copies the staging folder to E:\PandabornDev\build\package\PandabornFactions and zips it (mod.io).
  all       pin, models, generate, code, bundles, assemble, validate, gate, install. (test and package only when named.)

  Exit code 0 when every requested stage passed.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 all
  powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 generate -DryRun
  powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 generate,assemble,validate
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)][string[]]$Stage = @('all'),
    [switch]$Accept,
    [switch]$AcceptPin,
    [switch]$Lock,
    [switch]$DryRun,
    [switch]$NoCode,
    [switch]$WithCode,      # kept for old callers: code is on by default now
    [switch]$WithBundles,   # kept for old callers: bundles are always copied
    [switch]$NoLink,
    [switch]$Plants,
    [switch]$Release,       # validate with the release rules (the package stage always does)
    [string[]]$Combo = @(), # combos: only these combinations (default: all)
    [string]$ArtPython = 'E:\PandabornDev\tools\venv\Scripts\python.exe',
    [string]$Catalogue = '',
    [string]$GenDir = 'E:\PandabornDev\build\gen\PandabornFactions',
    [string]$StageDir = 'E:\PandabornDev\build\stage\PandabornFactions',
    [string]$InstallDir = 'E:\PandabornDev\build\PandabornFactions',
    [string]$PackageDir = 'E:\PandabornDev\build\package',
    # plants (tools/build_plants.ps1) and sounds (tools/build_sound.ps1); the look bundle comes with the code. Planned:
    # E:\PandabornDev\build\characters\attachments (pandabornattachments, hats and baskets) once that lane's real
    # geometry and _mac twin are in (docs/tech/ringtail-body.md 7.3)
    [string[]]$BundleDirs = @('E:\PandabornDev\build\plants\AssetBundles', 'E:\PandabornDev\build\sound\AssetBundles',
                              'E:\PandabornDev\build\characters\attachments'),
    [string]$MeshSource = 'E:\PandabornDev\assets\Pandaborn-Reskin-release\Characters\Beaver',
    [string]$RingtailMeshSource = 'E:\PandabornDev\build\characters\out',
    [string]$ModsDir = 'C:\Users\Israel Gonzalez\Documents\Timberborn\Mods',
    [string]$LinkName = 'PandabornFactions',
    [string[]]$TestArgs = @(),
    # install without a passing gate: only on the coordinator's word, with the reason (written to the gate log)
    [string]$GateOverride = '',
    # install: the caller holds the test queue through a live hold (tools\game_test_hold.ps1); checked, not trusted
    [switch]$CallerHoldsLock,
    # gate: remove old pbgate-<hash> copies instead of running the gate (-DryRun: list them)
    [switch]$Prune,
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Timberborn',
    [string]$TestRoot = 'E:\PandabornDev\build\test',
    [string]$TestMutexName = 'Global\PandabornGameTest'   # only for trials on a scratch lock
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$source = Join-Path $repo 'mod\PandabornFactions'
$env:PYTHONDONTWRITEBYTECODE = '1'
. (Join-Path $PSScriptRoot 'game_lock.ps1')   # the test lock, holds, Test-PathUnder
# every folder this script mirrors into (and so deletes from) must be inside the build root
$buildRoot = 'E:\PandabornDev\build'
$protoRoot = Join-Path $buildRoot 'proto'
$stages = @($Stage | ForEach-Object { $_ -split ',' } | Where-Object { $_ } | ForEach-Object { $_.Trim().ToLowerInvariant() })
if ($stages -contains 'all') { $stages = @('pin', 'models', 'generate', 'code', 'bundles', 'assemble', 'validate', 'gate', 'install') + @($stages | Where-Object { $_ -ne 'all' }) }
$known = 'pin', 'models', 'generate', 'validate', 'code', 'bundles', 'assemble', 'gate', 'install', 'test', 'package', 'combos'
foreach ($s in $stages) { if ($known -notcontains $s) { throw "unknown stage '$s' (stages: $($known -join ', '), all)" } }

# large binaries that live outside git: staging-relative path -> source file
$meshes = [ordered]@{
    'Characters\Pandaborn\InkpawAdult.Model.timbermesh' = Join-Path $MeshSource 'BeaverAdult.Model.timbermesh'
    'Characters\Pandaborn\InkpawChild.Model.timbermesh' = Join-Path $MeshSource 'BeaverChild.Model.timbermesh'
    # the Wooden Ox (character pass 3, docs/tech/ringtail-body.md 8.6), shipped always
    'Characters\Pandaborn\WoodenOx.Model.timbermesh' = Join-Path $RingtailMeshSource 'WoodenOx.Model.timbermesh'
}
# the Ringtail bodies (ringtail-body lane, docs/tech/ringtail-body.md), shipped only when the generated data has the
# Ringtail templates (catalogue/rules.toml [modules] Ringtails)
$ringtailMeshes = [ordered]@{
    'Characters\Pandaborn\RingtailAdult.Model.timbermesh' = Join-Path $RingtailMeshSource 'RingtailAdult.Model.timbermesh'
    'Characters\Pandaborn\RingtailChild.Model.timbermesh' = Join-Path $RingtailMeshSource 'RingtailChild.Model.timbermesh'
}

function Say([string]$text, [string]$color = 'Gray') { Write-Host $text -ForegroundColor $color }

function Get-Python {
    foreach ($name in 'python', 'py') {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        $pre = @(); if ($name -eq 'py') { $pre = @('-3') }
        $v = & $cmd.Source @pre -c "import sys; print(sys.version_info >= (3, 11))" 2>$null
        if ($v -eq 'True') { return , @($cmd.Source) + $pre }
    }
    throw 'Python 3.11 or newer not found (the generator needs tomllib)'
}
$py = Get-Python
function Invoke-Py([string[]]$arguments) {
    $exe = $py[0]; $pre = @($py | Select-Object -Skip 1)
    & $exe @pre -I @arguments | Out-Host
    return $LASTEXITCODE
}

function Copy-IfChanged([string]$from, [string]$to) {
    $src = Get-Item -LiteralPath $from
    if (Test-Path -LiteralPath $to) {
        $dst = Get-Item -LiteralPath $to
        if ($dst.Length -eq $src.Length -and $dst.LastWriteTimeUtc -eq $src.LastWriteTimeUtc) { return $false }
    }
    $dir = Split-Path $to -Parent
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
    Copy-Item -LiteralPath $from -Destination $to -Force
    return $true
}

# Makes $dest an exact mirror of the given (relative path -> source file) map. Returns counts.
function Sync-Tree([string]$dest, $map) {
    # an exact mirror deletes whatever else is in the target: never outside the build root (a mistyped -InstallDir,
    # -StageDir or -PackageDir pointing at the Mods folder would empty it)
    if (-not (Test-PathUnder $dest $buildRoot)) { throw "Sync-Tree: $dest is not inside $buildRoot; refusing to mirror into it" }
    if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Force $dest | Out-Null }
    $dest = (Resolve-Path $dest).Path
    $copied = 0; $removed = 0
    foreach ($rel in $map.Keys) { if (Copy-IfChanged $map[$rel] (Join-Path $dest $rel)) { $copied++ } }
    $want = @{}; foreach ($rel in $map.Keys) { $want[$rel.ToLowerInvariant()] = $true }
    foreach ($f in Get-ChildItem -LiteralPath $dest -Recurse -File -Force) {
        $rel = $f.FullName.Substring($dest.Length + 1)
        if (-not $want.ContainsKey($rel.ToLowerInvariant())) { Remove-Item -LiteralPath $f.FullName -Force; $removed++ }
    }
    Get-ChildItem -LiteralPath $dest -Recurse -Directory | Sort-Object { $_.FullName.Length } -Descending |
        Where-Object { -not (Get-ChildItem -LiteralPath $_.FullName -Force) } |
        ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
    return @{ files = $map.Count; copied = $copied; removed = $removed }
}

function Add-Tree($map, [string]$root, [string]$origin, $origins) {
    if (-not (Test-Path -LiteralPath $root)) { return }
    $root = (Resolve-Path $root).Path
    foreach ($f in Get-ChildItem -LiteralPath $root -Recurse -File) {
        $rel = $f.FullName.Substring($root.Length + 1)
        # a second enabled copy parks its own bundles in AssetBundles.parked (docs/tech/stage0.md): never content
        if ($rel -match '(^|\\)AssetBundles\.parked(\\|$)') { continue }
        $k = $rel.ToLowerInvariant()
        if ($origins.ContainsKey($k)) { throw "assemble: $rel comes from both $($origins[$k]) and $origin. Generated files must not be hand-written too." }
        $origins[$k] = $origin
        $map[$rel] = $f.FullName
    }
}

# Keeps in a code build only the modules the generator's report lists as on (Modules\modules.txt and the files it
# names). Returns the ids it dropped.
function Limit-Modules([string]$codeDir, [string]$reportFile) {
    $dropped = @()
    if (-not (Test-Path -LiteralPath $reportFile)) { return $dropped }
    $on = @((Get-Content -LiteralPath $reportFile -Raw | ConvertFrom-Json).modules.on)
    $mt = Join-Path $codeDir 'Modules\modules.txt'
    if (-not (Test-Path -LiteralPath $mt)) { return $dropped }
    $kept = @()
    foreach ($line in Get-Content -LiteralPath $mt) {
        $id = ($line -split '\s+')[0]
        if ($line.Trim() -eq '' -or $line.TrimStart().StartsWith('#') -or $on -contains $id) { $kept += $line; continue }
        $dropped += $id
        $file = ($line -split '\s+')[1]
        foreach ($f in @($file, ($file -replace '\.bin$', '.api.txt'))) {
            $pth = Join-Path $codeDir ('Modules\' + $f); if (Test-Path -LiteralPath $pth) { Remove-Item -LiteralPath $pth -Force }
        }
    }
    [IO.File]::WriteAllLines($mt, [string[]]$kept)
    return $dropped
}

function Get-StageHash([string]$dir) {
    # content hash of a staging folder: every file's relative path and SHA-256 (the parked-bundle folder is not content)
    $root = (Resolve-Path -LiteralPath $dir).Path
    $lines = foreach ($f in Get-ChildItem -LiteralPath $root -Recurse -File | Sort-Object FullName) {
        $rel = $f.FullName.Substring($root.Length + 1)
        if ($rel -match '(^|\\)AssetBundles\.parked(\\|$)') { continue }
        $rel.ToLowerInvariant() + ':' + (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
    }
    $bytes = [Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))
    $sha = [Security.Cryptography.SHA256]::Create()
    return ([BitConverter]::ToString($sha.ComputeHash($bytes)) -replace '-', '')
}

# Like Get-StageHash, for a part of a tree: only files whose lowercased relative path starts with one of $only (when
# given), without the files in $skip. Sorted by relative path, ordinal, so two copies of one tree in different folders
# hash alike. (The same function is in proto/foundation/build.ps1.)
function Get-TreeHash([string]$root, [string[]]$only = @(), [string[]]$skip = @()) {
    $root = (Resolve-Path -LiteralPath $root).Path.TrimEnd('\')
    $lines = @(foreach ($f in Get-ChildItem -LiteralPath $root -Recurse -File) {
        $rel = $f.FullName.Substring($root.Length + 1)
        if ($rel -match '(^|\\)AssetBundles\.parked(\\|$)') { continue }
        $low = $rel.ToLowerInvariant()
        if ($skip -contains $low) { continue }
        if ($only.Count -gt 0 -and -not @($only | Where-Object { $low.StartsWith($_) })) { continue }
        $low + ':' + (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
    })
    $lines = [string[]]$lines
    [Array]::Sort($lines, [StringComparer]::Ordinal)
    $sha = [Security.Cryptography.SHA256]::Create()
    return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes(($lines -join "`n")))) -replace '-', '')
}
$codeParts = @('scripts\', 'modules\', 'assetbundles\')   # what the code and bundle stages contribute to the mod

# The installed game: version from its own file, build id from Steam's manifest (a hotfix can keep the version).
function Get-GameVersion([string]$gameDir) {
    $version = $null; $build = $null
    try { $version = [string](Get-Content -LiteralPath (Join-Path $gameDir 'Timberborn_Data\StreamingAssets\VersionNumbers.json') -Raw | ConvertFrom-Json).CurrentVersion } catch { }
    try {
        $acf = Join-Path (Split-Path (Split-Path $gameDir -Parent) -Parent) 'appmanifest_1062090.acf'
        if ((Get-Content -LiteralPath $acf -Raw) -match '"buildid"\s+"(\d+)"') { $build = $Matches[1] }
    } catch { }
    return [ordered]@{ version = $version; steamBuild = $build }
}

# Gate copies (pbgate-<8 hex>) in $protoDir that are not $keepName, with their sizes. Never one that may be in use: a
# copy junctioned into Mods (a run has it loaded) or younger than $minAgeHours (a gate may be queued with it).
function Get-PrunableGateCopies([string]$protoDir, [string]$keepName, [string]$modsDir, [double]$minAgeHours = 12) {
    $list = @()
    foreach ($d in @(Get-ChildItem -LiteralPath $protoDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^pbgate-[0-9A-Fa-f]{8}$' })) {
        if ($d.Name -eq $keepName -or $d.LinkType) { continue }
        if ($modsDir -and (Get-Item -LiteralPath (Join-Path $modsDir $d.Name) -Force -ErrorAction SilentlyContinue)) { continue }
        if (((Get-Date) - $d.LastWriteTime).TotalHours -lt $minAgeHours) { continue }
        $bytes = (Get-ChildItem -LiteralPath $d.FullName -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
        $list += [pscustomobject]@{ Name = $d.Name; Path = $d.FullName; SizeMB = [math]::Round([double]$bytes / 1MB); Built = $d.LastWriteTime }
    }
    return $list
}
# Removes them: only a real pbgate-<hash> folder directly in $protoDir, and its .devcopy.json.
function Remove-GateCopies($copies, [string]$protoDir) {
    $removed = @()
    $protoFull = [IO.Path]::GetFullPath($protoDir).TrimEnd('\')
    foreach ($c in @($copies)) {
        $full = [IO.Path]::GetFullPath([string]$c.Path)
        if ((Split-Path $full -Parent).TrimEnd('\') -ne $protoFull -or (Split-Path $full -Leaf) -notmatch '^pbgate-[0-9A-Fa-f]{8}$') { continue }
        $item = Get-Item -LiteralPath $full -Force -ErrorAction SilentlyContinue
        if ($null -eq $item -or $item.LinkType) { continue }
        Remove-Item -LiteralPath $full -Recurse -Force
        Remove-Item -LiteralPath "$full.devcopy.json" -Force -ErrorAction SilentlyContinue
        $removed += $full
    }
    return $removed
}

$failed = @()
$validated = $false
$codeOut = Join-Path (Split-Path $StageDir -Parent) 'code\PandabornFactions'
$bundleOut = Join-Path (Split-Path $StageDir -Parent) 'bundles\PandabornFactions'

foreach ($s in $stages) {
    Say "== $s" 'Cyan'
    switch ($s) {
        'pin' {
            $a = @((Join-Path $repo 'src\gen\generate.py'), 'pin'); if ($Accept) { $a += '--accept' }
            $code = Invoke-Py $a
            if ($code -ne 0) { $failed += $s; if (-not $AcceptPin) { break } }
            # the Words table (src/code/Pandaborn.Words) against the game's current texts: a game update that changes a
            # reviewed text or adds a new beaver line shows here (a hard failure for package)
            $words = @((Join-Path $repo 'src\code\Pandaborn.Words\tools\candidates.py'), '--check',
                       (Join-Path $repo 'src\code\Pandaborn.Words\mod\Pandaborn\Words\words.enUS.txt'))
            if ((Invoke-Py $words) -ne 0) { Say 'pin: the Words table needs a review (candidates.py --check above)' 'DarkYellow' }
        }
        'generate' {
            $a = @((Join-Path $repo 'src\gen\generate.py'), '--out', $GenDir)
            if ($Catalogue) { $a += @('--catalogue', $Catalogue) }
            if ($Lock) { $a += '--lock' }; if ($DryRun) { $a += '--dry-run' }; if ($NoCode) { $a += '--no-code' }; if ($AcceptPin -or $Accept) { $a += '--accept-pin' }
            if ((Invoke-Py $a) -ne 0) { $failed += $s; break }
        }
        'models' {
            if (-not (Test-Path -LiteralPath $ArtPython)) { Say "models: art Python not found: $ArtPython" 'Red'; $failed += $s; break }
            $env:TEMP = 'E:\PandabornDev\tools\tmp'; $env:TMP = $env:TEMP
            $roots = @('art' + [IO.Path]::DirectorySeparatorChar + 'models'); if ($Plants) { $roots += 'art' + [IO.Path]::DirectorySeparatorChar + 'plants' }
            $built = 0; $bad = @()
            foreach ($root in $roots) {
                foreach ($script in Get-ChildItem -Path (Join-Path $repo $root) -Filter build.py -Recurse -Depth 1 -ErrorAction SilentlyContinue) {
                    $out = & $ArtPython $script.FullName 2>&1
                    if ($LASTEXITCODE -ne 0) { $bad += $script.Directory.Name; $out | Select-Object -Last 5 | ForEach-Object { Say "  $_" 'Red' } }
                    else { $built++ }
                }
            }
            Say "models: $built built into E:\PandabornDev\build\models$(if ($bad) { '; FAILED: ' + ($bad -join ', ') })"
            if ($bad) { $failed += $s; break }
        }
        'code' {
            if ($NoCode) { Say 'code: skipped (-NoCode: data-only fallback build)' 'DarkYellow'; continue }
            if (Test-Path $codeOut) { Remove-Item -Recurse -Force $codeOut }
            New-Item -ItemType Directory -Force $codeOut | Out-Null
            $log = & dotnet build (Join-Path $repo 'src\code\Pandaborn.Code.sln') -c Release -v q --nologo "-p:ModOut=$codeOut" 2>&1
            if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Say "  $_" 'Red' }; $failed += $s; break }
            Say "code: built into $codeOut"
            # ship only the modules whose data the catalogue has switched on (rules.toml [modules]); a module without
            # its data would do nothing, and validate --release refuses it
            $dropped = Limit-Modules $codeOut "$GenDir.report.json"
            if ($dropped) { Say "code: modules left out until their data is switched on: $($dropped -join ', ')" 'DarkYellow' }
            # the mod's own spec classes, for the validator (.bin files are assemblies loaded from bytes)
            $dlls = Join-Path (Split-Path $codeOut -Parent) 'code-dlls'
            if (Test-Path $dlls) { Remove-Item -Recurse -Force $dlls }
            New-Item -ItemType Directory -Force $dlls | Out-Null
            foreach ($f in Get-ChildItem -LiteralPath $codeOut -Recurse -File | Where-Object { $_.Extension -in '.bin', '.dll' }) {
                Copy-Item -LiteralPath $f.FullName (Join-Path $dlls ($f.BaseName + '.dll'))
            }
            $modSchema = Join-Path (Split-Path $codeOut -Parent) 'code-schema.json'
            $log = & dotnet run --project (Join-Path $repo 'tools\schema') -c Release -- --include $dlls --out $modSchema 2>&1
            if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Say "  $_" 'Red' }; $failed += $s; break }
            Say "code: spec schema with the mod's own classes in $modSchema"
            # game-update alarm: each module's game-API list (FEATURE.md) against the committed one; a warning here,
            # a hard failure for package (tools/check_api_lists.py)
            if ((Invoke-Py @((Join-Path $repo 'tools\check_api_lists.py'), '--repo', $repo, '--warn-only')) -ne 0) {
                Say 'code: tools/check_api_lists.py could not run' 'DarkYellow'
            }
        }
        'bundles' {
            if (Test-Path $bundleOut) { Remove-Item -Recurse -Force $bundleOut }
            New-Item -ItemType Directory -Force (Join-Path $bundleOut 'AssetBundles') | Out-Null
            $n = 0; $have = @{}
            foreach ($dir in $BundleDirs) {
                foreach ($f in Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^pandaborn.*_(win|mac)$' -and $_.Name -notmatch '^pandabornlook_' }) {
                    Copy-Item -LiteralPath $f.FullName (Join-Path $bundleOut "AssetBundles\$($f.Name)"); $n++
                    $have[($f.Name -replace '_(win|mac)$', '')] = $true
                }
            }
            $manifest = "$GenDir.models.json"
            $needed = @(); if (Test-Path -LiteralPath $manifest) { $needed = @((Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json).bundles) }
            $missingB = @($needed | Where-Object { $_ -and -not $have.ContainsKey($_) })
            Say "bundles: $n file(s) from $($BundleDirs -join ', ')"
            if ($missingB.Count -gt 0) { Say "bundles: adopted models need bundle(s) not built: $($missingB -join ', ') (tools/build_plants.ps1)" 'Red'; $failed += $s; break }
        }
        'assemble' {
            if (-not (Test-Path (Join-Path $GenDir 'Factions'))) { Say "assemble: no generated data in $GenDir (run generate first)" 'Red'; $failed += $s; break }
            $map = [ordered]@{}; $origins = @{}
            Add-Tree $map $source 'mod/PandabornFactions' $origins
            Add-Tree $map $GenDir 'generated' $origins
            if (-not $NoCode) {
                if (-not (Test-Path (Join-Path $codeOut 'Scripts'))) { Say "assemble: no code build in $codeOut (run the code stage, or pass -NoCode)" 'Red'; $failed += $s; break }
                Add-Tree $map $codeOut 'code' $origins
            }
            # meshes of the models the catalogue adopts (built by the models stage, outside git)
            $manifest = "$GenDir.models.json"
            if (Test-Path -LiteralPath $manifest) {
                $mm = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
                $missingMesh = @()
                foreach ($p in $mm.files.PSObject.Properties) {
                    $rel = $p.Name.Replace('/', [string][IO.Path]::DirectorySeparatorChar)
                    if (-not (Test-Path -LiteralPath $p.Value)) { $missingMesh += $p.Value; continue }
                    $k = $rel.ToLowerInvariant()
                    if ($origins.ContainsKey($k)) { throw "assemble: $rel comes from both $($origins[$k]) and models" }
                    $origins[$k] = 'models'; $map[$rel] = $p.Value
                }
                if ($missingMesh) { Say ("assemble: {0} model mesh(es) missing; run the models stage first: {1}" -f $missingMesh.Count, ($missingMesh | Select-Object -First 3) -join ', ') 'Red'; $failed += $s; break }
            }
            if (Test-Path $bundleOut) { Add-Tree $map $bundleOut 'bundles' $origins }
            # PAIRED CHANGE: the models' lantern paper and windows sit on regions of the look sheet
            # (src/pipeline/sheet_regions.json); a pandabornlook bundle older than the last change of that file pairs new
            # meshes with an old sheet (lanterns that never glow). The bundle must be built after it.
            if (-not $NoCode) {
                $regionsAt = & git -C $repo log -1 --format=%ct -- 'src/pipeline/sheet_regions.json' 2>$null
                if ($regionsAt) {
                    $regionsTime = [DateTimeOffset]::FromUnixTimeSeconds([long]$regionsAt).LocalDateTime
                    foreach ($b in 'pandabornlook_win', 'pandabornlook_mac') {
                        $f = Join-Path $codeOut "AssetBundles\$b"
                        if ((Test-Path -LiteralPath $f) -and (Get-Item -LiteralPath $f).LastWriteTime -lt $regionsTime) {
                            Say "assemble: $b ($((Get-Item -LiteralPath $f).LastWriteTime)) is older than the look-sheet regions the meshes use ($regionsTime): rebuild it (tools/build_look.ps1), then the code stage" 'Red'
                            $failed += $s
                        }
                    }
                    if ($failed -contains $s) { break }
                }
            }
            # PAIRED CHANGE: plant meshes and the pandabornplants bundle (material regions such as bamboo_buds_c/_d/_e).
            # Every adopted plant's meshes must be built after the last commit of art/plants/<Id>, and the bundle after
            # the last commit under art/plants: an old mesh with a new bundle (or the reverse) paints the wrong masks.
            $plantsBundle = Join-Path $bundleOut 'AssetBundles\pandabornplants_win'
            $plantsAt = & git -C $repo log -1 --format=%ct -- 'art/plants' 2>$null
            if ($plantsAt -and (Test-Path -LiteralPath $plantsBundle)) {
                # an hour of slack: a lane builds, looks, then commits (the build is a little older than its commit)
                $plantsTime = [DateTimeOffset]::FromUnixTimeSeconds([long]$plantsAt).LocalDateTime.AddHours(-1)
                foreach ($b in 'pandabornplants_win', 'pandabornplants_mac') {
                    $f = Join-Path $bundleOut "AssetBundles\$b"
                    if ((Test-Path -LiteralPath $f) -and (Get-Item -LiteralPath $f).LastWriteTime -lt $plantsTime) {
                        Say "assemble: $b is older than the last plant change in git ($plantsTime): rebuild it (tools/build_plants.ps1)" 'Red'
                        $failed += $s
                    }
                }
            }
            $manifestPlants = "$GenDir.models.json"
            if (Test-Path -LiteralPath $manifestPlants) {
                $adoptedPlants = @(((Get-Content -LiteralPath $manifestPlants -Raw | ConvertFrom-Json).adopted.PSObject.Properties |
                    Where-Object { $_.Name -like 'plant:*' }).Name | ForEach-Object { $_.Substring(6) })
                foreach ($plantId in $adoptedPlants) {
                    $at = & git -C $repo log -1 --format=%ct -- "art/plants/$plantId" 2>$null
                    if (-not $at) { continue }
                    $t = [DateTimeOffset]::FromUnixTimeSeconds([long]$at).LocalDateTime.AddHours(-1)
                    $old = @(Get-ChildItem -LiteralPath (Join-Path 'E:\PandabornDev\build\plants' $plantId) -Filter '*.timbermesh' -File -ErrorAction SilentlyContinue |
                             Where-Object { $_.LastWriteTime -lt $t })
                    if ($old.Count -gt 0) {
                        Say "assemble: plant $plantId has $($old.Count) mesh(es) older than its last change in git ($t): run the models stage with -Plants" 'Red'
                        $failed += $s
                    }
                }
            }
            if ($failed -contains $s) { break }
            $allMeshes = [ordered]@{}; foreach ($k in $meshes.Keys) { $allMeshes[$k] = $meshes[$k] }
            if (Test-Path -LiteralPath (Join-Path $GenDir 'Characters\Pandaborn\RingtailAdult.Inkpaws.blueprint.json')) {
                foreach ($k in $ringtailMeshes.Keys) { $allMeshes[$k] = $ringtailMeshes[$k] }
            }
            foreach ($rel in $allMeshes.Keys) {
                $from = $allMeshes[$rel]
                if (-not (Test-Path -LiteralPath $from)) { throw "large mesh missing: $from" }
                $fs = [IO.File]::OpenRead($from); try { $b0 = $fs.ReadByte(); $b1 = $fs.ReadByte() } finally { $fs.Dispose() }
                if ($b0 -ne 0x78 -or $b1 -ne 0x9C) { throw "$from does not start with zlib header 78 9C" }
                $map[$rel] = $from
            }
            $r = Sync-Tree $StageDir $map
            Say ("assemble: {0} files in {1} ({2} copied, {3} removed)" -f $r.files, $StageDir, $r.copied, $r.removed)
        }
        'validate' {
            $a = @((Join-Path $repo 'tools\validate.py'), '--mod', $StageDir, '--quiet')
            if ($Catalogue) { $a += @('--lock', (Join-Path $Catalogue 'ids.lock.json')) }
            # what this build leaves out on purpose (items waiting for a module it does not ship; everything code-bound
            # in a -NoCode build): the lock check accepts those ids as absent
            if (Test-Path -LiteralPath "$GenDir.report.json") { $a += @('--left-out', "$GenDir.report.json") }
            $modSchema = Join-Path (Split-Path $codeOut -Parent) 'code-schema.json'
            if (-not $NoCode -and (Test-Path $modSchema)) { $a += @('--mod-schema', $modSchema) }
            if ($Release) { $a += '--release' }
            if ((Invoke-Py $a) -ne 0) { $failed += $s; break }
            $validated = $true
            # report only: numbers in the balance model's stat sheet the catalogue has not carried over
            if (-not $Release) { $null = Invoke-Py @((Join-Path $repo 'src\gen\import_statsheet.py'), '--check') }
        }
        'combos' {
            # Every build a player can end up with must generate, assemble and pass the release rules: all modules on,
            # the data-only build, and each module (or family) switched off in rules.toml. A tutorial stage that names
            # a template one of these builds lacks would throw at the start of every game (TutorialService.Load), a
            # good left without a source or a use would lie. Run it before committing a catalogue or generator change.
            # One scratch folder is reused (only changed files are copied); nothing installed or staged is touched.
            if (-not (Test-Path (Join-Path $codeOut 'Scripts'))) { Say "combos: no code build in $codeOut (run the code stage first)" 'Red'; $failed += $s; break }
            $combos = [ordered]@{
                'all-on'            = ''
                'no-code'           = 'NOCODE'
                'water-off'         = 'Water=off'
                'festival-off'      = 'Festival=off'
                'flowering-off'     = 'Flowering=off'
                'water-events-off'  = 'Water=off,Festival=off,Flowering=off'
                'ringtails-off'     = 'Ringtails=off,RingtailsFallback=off'
                'tutorial-off'      = 'Tutorial=off'
                'bell-off'          = 'Bell=off'
            }
            if ($Combo) { $only = [ordered]@{}; foreach ($k in $Combo) { if (-not $combos.Contains($k)) { throw "combos: no combination named $k ($($combos.Keys -join ', '))" }; $only[$k] = $combos[$k] }; $combos = $only }
            $root = Join-Path (Split-Path (Split-Path $StageDir -Parent) -Parent) 'combos'
            $cGen = Join-Path $root 'gen\PandabornFactions'; $cStage = Join-Path $root 'stage\PandabornFactions'
            $cCode = Join-Path $root 'stage\code\PandabornFactions'; $cBundles = Join-Path $root 'stage\bundles\PandabornFactions'
            $bad = @()
            foreach ($name in $combos.Keys) {
                $mods = $combos[$name]; $noCode = ($mods -eq 'NOCODE')
                Say "-- combination $name$(if ($mods -and -not $noCode) { ' (' + $mods + ')' })" 'Cyan'
                $a = @((Join-Path $repo 'src\gen\generate.py'), '--out', $cGen, '--quiet')
                if ($Catalogue) { $a += @('--catalogue', $Catalogue) }
                if ($noCode) { $a += '--no-code' } elseif ($mods) { $a += @('--modules', $mods) }
                if ((Invoke-Py $a) -ne 0) { $bad += "$name (generate)"; continue }
                # the code and bundles of the real build, trimmed to this combination's modules as the code stage would
                $map = [ordered]@{}; $origins = @{}; Add-Tree $map $codeOut 'code' $origins
                $null = Sync-Tree $cCode $map
                $null = Limit-Modules $cCode "$cGen.report.json"
                $schema = Join-Path (Split-Path $codeOut -Parent) 'code-schema.json'
                if (Test-Path -LiteralPath $schema) { Copy-Item -LiteralPath $schema (Join-Path (Split-Path $cCode -Parent) 'code-schema.json') -Force }
                if (Test-Path $bundleOut) { $map = [ordered]@{}; $origins = @{}; Add-Tree $map $bundleOut 'bundles' $origins; $null = Sync-Tree $cBundles $map }
                $sub = @('-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, 'assemble,validate', '-GenDir', $cGen, '-StageDir', $cStage, '-Release')
                if ($noCode) { $sub += '-NoCode' }
                if ($Catalogue) { $sub += @('-Catalogue', $Catalogue) }
                $out = & powershell @sub 2>&1
                if ($LASTEXITCODE -ne 0) {
                    $bad += $name
                    $out | Where-Object { $_ -match '^(ERROR|assemble:|FAILED|validate:)' } | Select-Object -First 25 | ForEach-Object { Say "  $_" 'Red' }
                } else { Say ("  ok: " + (($out | Where-Object { $_ -match '^validate:' }) -join ' ')) }
            }
            if ($bad) { Say "combos: FAILED: $($bad -join ', ')" 'Red'; $failed += $s; break }
            Say "combos: $($combos.Count) combination(s) generate, assemble and pass the release rules"
        }
        'gate' {
            if ($failed.Count -gt 0) { Say "gate: not run, earlier stages failed: $($failed -join ', ')" 'Red'; $failed += $s; break }
            $hash = Get-StageHash $StageDir
            $copy = 'pbgate-' + $hash.Substring(0, 8)   # one copy per staging content: two gates never share a folder
            if ($Prune) {
                # gate -Prune: old copies only, no gate run
                $old = @(Get-PrunableGateCopies $protoRoot $copy $ModsDir)
                foreach ($c in $old) { Say ("gate: old copy {0,-18} {1,6} MB  built {2}" -f $c.Name, $c.SizeMB, $c.Built) }
                if ($old.Count -eq 0) { Say 'gate: no old gate copy to remove (the current one, copies in use and copies younger than 12 hours stay)' }
                elseif ($DryRun) { Say ("gate: -DryRun, nothing removed; {0} copy(ies), {1} MB" -f $old.Count, ($old | Measure-Object SizeMB -Sum).Sum) }
                else { $gone = @(Remove-GateCopies $old $protoRoot); Say "gate: removed $($gone.Count) old copy(ies)" }
                continue
            }
            # the copy is the staging folder as it is (-Staged): the staged Scripts, Modules (with the staged, filtered
            # modules.txt) and bundles, not a fresh build of src/code; the build lists every file it had to replace
            & powershell -ExecutionPolicy Bypass -File (Join-Path $repo 'proto\foundation\build.ps1') -Name $copy -Source $StageDir -Staged | Out-Host
            if ($LASTEXITCODE -ne 0) { Say 'gate: the dev copy did not build' 'Red'; $failed += $s; break }
            $copyDir = Join-Path $protoRoot $copy
            $devcopy = $null
            try { $devcopy = Get-Content -LiteralPath "$copyDir.devcopy.json" -Raw -Encoding UTF8 | ConvertFrom-Json } catch { }
            if ($null -eq $devcopy -or $devcopy.mode -ne 'staged') { Say "gate: $copyDir.devcopy.json missing or not a staged copy" 'Red'; $failed += $s; break }
            $substituted = @($devcopy.substitutions | ForEach-Object { ([string]$_.file).ToLowerInvariant() })
            # the code the gate runs is the code install will copy: same files, same bytes
            $codeHash = Get-TreeHash $StageDir $codeParts
            if ($codeHash -ne (Get-TreeHash $copyDir $codeParts)) { Say 'gate: the copy''s Scripts, Modules or AssetBundles differ from the staged ones' 'Red'; $failed += $s; break }
            $restHash = Get-TreeHash $StageDir @() $substituted
            if ($restHash -ne (Get-TreeHash $copyDir @() $substituted)) { Say "gate: the copy differs from the staging folder in more than $($substituted -join ', ')" 'Red'; $failed += $s; break }
            $grid = "$GenDir.grid.json"
            if (-not (Test-Path -LiteralPath $grid)) { Say "gate: $grid missing (run generate)" 'Red'; $failed += $s; break }
            $gridHash = (Get-FileHash -LiteralPath $grid -Algorithm SHA256).Hash
            $game = Get-GameVersion $GameDir
            # exit 2 = could not test (no verdict, e.g. the game was closed from outside): one more try, then it fails
            foreach ($try in 1, 2) {
                $runId = 'gate-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
                & powershell -ExecutionPolicy Bypass -File (Join-Path $repo 'tools\run_game_test.ps1') -Faction Inkpaws -Map Plains `
                    -DisableMods JigglyPanda.PandabornFactions -ExtraMods "E:\PandabornDev\build\proto\$copy" -RequestJson $grid `
                    -RunSeconds 2400 -TimeoutSeconds 4200 -WaitForGameSeconds 10800 -RunId $runId | Out-Host
                $code = $LASTEXITCODE
                if ($code -ne 2) { break }
                Say "gate: run $runId could not test (exit 2); trying again" 'DarkYellow'
            }
            if ($code -ne 0) { Say "gate: FAILED (run $runId, exit $code): this staging folder must not be installed" 'Red'; $failed += $s; break }
            # with the Water module shipped, the water lane's line (crossing, spout, save and reload) and its scoop-wheel /
            # trip-hammer scenario also run on the catalogue's own templates (docs/tech/water.md, before Water is on)
            $extra = @()
            $mt = Join-Path $StageDir 'Modules\modules.txt'
            if ((Test-Path -LiteralPath $mt) -and (Select-String -LiteralPath $mt -Pattern '^Water\s' -Quiet)) {
                $extra += @(@{ file = 'tests\scenarios\catalogue\water_w4_inkpaws.json'; reload = $true },
                            @{ file = 'tests\scenarios\catalogue\water_scoop_inkpaws.json'; reload = $false })
            }
            $runs = @($runId)
            foreach ($x in $extra) {
                foreach ($try in 1, 2) {
                    $xid = 'gate-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [IO.Path]::GetFileNameWithoutExtension($x.file)
                    $args2 = @('-ExecutionPolicy', 'Bypass', '-File', (Join-Path $repo 'tools\run_game_test.ps1'), '-Faction', 'Inkpaws',
                               '-Map', 'Plains', '-DisableMods', 'JigglyPanda.PandabornFactions', '-ExtraMods', "E:\PandabornDev\build\proto\$copy",
                               '-RequestJson', (Join-Path $repo $x.file), '-RunSeconds', '1500', '-TimeoutSeconds', '3600',
                               '-WaitForGameSeconds', '10800', '-RunId', $xid)
                    if ($x.reload) { $args2 += '-SaveAndReload' }
                    & powershell @args2 | Out-Host
                    $code = $LASTEXITCODE
                    if ($code -ne 2) { break }
                    Say "gate: run $xid could not test (exit 2); trying again" 'DarkYellow'
                }
                $runs += $xid
                if ($code -ne 0) { break }
            }
            if ($code -ne 0) { Say "gate: FAILED (run $xid, exit $code): this staging folder must not be installed" 'Red'; $failed += $s; break }
            if ((Get-StageHash $StageDir) -ne $hash) { Say 'gate: the staging folder changed during the run; run the gate again' 'Red'; $failed += $s; break }
            # what ran must still be what was hashed: the copy (a run may park its bundles, never change a file), the
            # grid request (read by each run when it launches, hours after the hash) and the game
            if ((Get-TreeHash $copyDir @() $substituted) -ne $restHash) { Say 'gate: the dev copy changed during the run; run the gate again' 'Red'; $failed += $s; break }
            if ((Get-FileHash -LiteralPath $grid -Algorithm SHA256).Hash -ne $gridHash) { Say 'gate: the grid request changed during the run; run the gate again' 'Red'; $failed += $s; break }
            $gameAfter = Get-GameVersion $GameDir
            if ($gameAfter.version -ne $game.version -or $gameAfter.steamBuild -ne $game.steamBuild) { Say 'gate: the game was updated during the run; run the gate again' 'Red'; $failed += $s; break }
            # the mods that were loaded, and the version the game reported, from the grid run's own result
            $loaded = @(); $reported = $null
            try {
                $res = Get-Content -LiteralPath (Join-Path (Join-Path $TestRoot $runs[0]) 'result.json') -Raw -Encoding UTF8 | ConvertFrom-Json
                $loaded = @($res.mods | ForEach-Object { [string]$_.id } | Sort-Object); $reported = [string]$res.gameVersion
            } catch { Say "gate: could not read the grid run's result for the mod list: $_" 'DarkYellow' }
            $runId = $runs -join ', '
            $gate = [ordered]@{
                hash = $hash; run = $runId; passedUtc = (Get-Date).ToUniversalTime().ToString('o'); stage = $StageDir
                gameVersion = $game.version; steamBuild = $game.steamBuild; gameVersionReported = $reported
                codeHash = $codeHash; codeFiles = @($devcopy.codeFiles)
                devCopy = [ordered]@{ name = $copy; mode = $devcopy.mode; manifestId = $devcopy.manifestId; substitutions = @($devcopy.substitutions) }
                grid = [ordered]@{ path = $grid; sha256 = $gridHash }
                modsLoaded = $loaded
            }
            [IO.File]::WriteAllText("$StageDir.gate.json", ($gate | ConvertTo-Json -Depth 6))
            Say "gate: passed (run $runId); $StageDir may be installed"
        }
        'install' {
            if ($failed.Count -gt 0) { Say "install: refused, earlier stages failed: $($failed -join ', ')" 'Red'; $failed += $s; break }
            # CLAUDE.md, install discipline: the test lock for the mirror, so no test game starts while the installed folder
            # is being rewritten. No waiting: the lock is free right after the gate; if a test or a hold has it, say who.
            $installLock = Enter-InstallLock $TestRoot $TestMutexName ([bool]$CallerHoldsLock) "install $StageDir"
            if (-not $installLock.ok) {
                Say "install: refused, $($installLock.why). Run the install stage again when the lock is free, or hold the queue (tools\game_test_hold.ps1) and pass -CallerHoldsLock." 'Red'
                $failed += $s; break
            }
            try {   # (the body keeps its old indentation; the finally at the end of the stage releases the lock)
            # never while a Timberborn process runs (a game holds the mod's bundles open, so
            # the mirror would stop half way; a test game loading the folder would read a mix of old and new files)
            $open = @(Get-Process Timberborn -ErrorAction SilentlyContinue)
            if ($open.Count -gt 0) {
                Say "install: refused, Timberborn is running (pid $($open.Id -join ', ')). Run the install stage again when no game is open (hold the test queue for it: tools\game_test_hold.ps1)." 'Red'
                $failed += $s; break
            }
            $gateFile = "$StageDir.gate.json"
            $gateOk = $false
            $stageHash = Get-StageHash $StageDir
            $gateWhy = 'this staging folder has not passed the gate'
            $game = Get-GameVersion $GameDir
            if (Test-Path -LiteralPath $gateFile) {
                $g = Get-Content -LiteralPath $gateFile -Raw | ConvertFrom-Json
                $gateOk = ($g.hash -eq $stageHash)
                # a pass is a pass for one game version: after an update the same files may crash
                if ($gateOk -and (-not $g.gameVersion -or -not $game.version -or [string]$g.gameVersion -ne $game.version)) {
                    $gateOk = $false
                    $gateWhy = "its gate passed on game version '$($g.gameVersion)', the installed game is '$($game.version)'"
                }
                elseif ($gateOk -and $g.steamBuild -and $game.steamBuild -and [string]$g.steamBuild -ne $game.steamBuild) {
                    Say "install: the gate passed on Steam build $($g.steamBuild), the game is now build $($game.steamBuild) (same version $($game.version))" 'Yellow'
                }
            }
            $overridden = $false
            if (-not $gateOk) {
                if (-not $GateOverride) {
                    Say "install: refused, $gateWhy (pandaborn.ps1 gate: a dev copy loaded with every template placed, finished and working)" 'Red'
                    $failed += $s; break
                }
                $overridden = $true   # logged below, once validation has passed: a line in the log is an install that happened
            }
            if (-not $validated) {
                $a = @((Join-Path $repo 'tools\validate.py'), '--mod', $StageDir, '--quiet')
                if (Test-Path -LiteralPath "$GenDir.report.json") { $a += @('--left-out', "$GenDir.report.json") }
                $modSchema = Join-Path (Split-Path $codeOut -Parent) 'code-schema.json'
                if (-not $NoCode -and (Test-Path $modSchema)) { $a += @('--mod-schema', $modSchema) }
                if ((Invoke-Py $a) -ne 0) { Say 'install: refused, the staging folder does not validate' 'Red'; $failed += $s; break }
                $validated = $true
            }
            if ($overridden) {
                $log = "$StageDir.gate-overrides.log"
                Add-Content -LiteralPath $log -Value ("{0} override: {1} [stage hash {2}; game {3}; by {4}; {5}]" -f (Get-Date).ToString('o'), $GateOverride, $stageHash, $game.version, $env:USERNAME, $gateWhy)
                Say "install: GATE OVERRIDDEN ($GateOverride), logged in $log" 'Yellow'
            }
            $map = [ordered]@{}; $origins = @{}
            Add-Tree $map $StageDir 'stage' $origins
            $r = Sync-Tree $InstallDir $map
            Say ("install: {0} files in {1} ({2} copied, {3} removed)" -f $r.files, $InstallDir, $r.copied, $r.removed)
            if ($NoLink) { continue }
            if (-not (Test-Path -LiteralPath $ModsDir -PathType Container)) { throw "Mods folder not found: $ModsDir" }
            $InstallDirFull = (Resolve-Path $InstallDir).Path
            $link = Join-Path $ModsDir $LinkName
            $item = Get-Item -LiteralPath $link -Force -ErrorAction SilentlyContinue
            if ($item) {
                if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                    throw "$link exists and is a real folder, not a junction. Not touching it; move it away by hand if it is stale."
                }
                $target = @($item.Target)[0]
                if ($target -and ($target -eq $InstallDirFull -or (Resolve-Path -LiteralPath $target -ErrorAction SilentlyContinue).Path -eq $InstallDirFull)) {
                    Say "link: $link -> $InstallDirFull (already in place)"; continue
                }
                cmd /c rmdir "$link" | Out-Null
                if (Test-Path -LiteralPath $link) { throw "could not remove the old junction $link" }
            }
            New-Item -ItemType Junction -Path $link -Target $InstallDirFull | Out-Null
            Say "link: $link -> $InstallDirFull (created)"
            } finally { Exit-InstallLock $installLock $TestRoot }
        }
        'test' {
            $grid = "$GenDir.grid.json"
            if (-not (Test-Path $grid)) { Say "test: $grid missing (run generate)" 'Red'; $failed += $s; break }
            $a = @('-ExecutionPolicy', 'Bypass', '-File', (Join-Path $repo 'tools\run_game_test.ps1'), '-Faction', 'Inkpaws',
                   '-Map', 'Plains', '-OnlyMods', 'JigglyPanda.PandabornFactions', '-RequestJson', $grid, '-RunSeconds', '300',
                   '-NoBatchControl', '-Screenshots', 'overview@end', '-TimeoutSeconds', '1200', '-WaitForGameSeconds', '7200') + $TestArgs
            & powershell @a
            if ($LASTEXITCODE -ne 0) { $failed += $s }
        }
        'package' {
            # release rules: a missing _mac bundle twin is an error here (dev stages only warn)
            $a = @((Join-Path $repo 'tools\validate.py'), '--mod', $StageDir, '--quiet', '--release')
            if (Test-Path -LiteralPath "$GenDir.report.json") { $a += @('--left-out', "$GenDir.report.json") }
            $modSchema = Join-Path (Split-Path $codeOut -Parent) 'code-schema.json'
            if (-not $NoCode -and (Test-Path $modSchema)) { $a += @('--mod-schema', $modSchema) }
            if ((Invoke-Py $a) -ne 0) { Say 'package: refused, the staging folder fails the release rules' 'Red'; $failed += $s; break }
            if (-not $NoCode -and (Invoke-Py @((Join-Path $repo 'tools\check_api_lists.py'), '--repo', $repo)) -ne 0) {
                Say 'package: refused, a module''s game-API list changed and is not committed (tools/check_api_lists.py)' 'Red'; $failed += $s; break
            }
            $words = @((Join-Path $repo 'src\code\Pandaborn.Words\tools\candidates.py'), '--check',
                       (Join-Path $repo 'src\code\Pandaborn.Words\mod\Pandaborn\Words\words.enUS.txt'))
            if (-not $NoCode -and (Invoke-Py $words) -ne 0) { Say 'package: refused, the Words table needs a review' 'Red'; $failed += $s; break }
            $out = Join-Path $PackageDir 'PandabornFactions'
            $map = [ordered]@{}; $origins = @{}
            Add-Tree $map $StageDir 'stage' $origins
            $r = Sync-Tree $out $map
            $zip = Join-Path $PackageDir 'PandabornFactions.zip'
            if (Test-Path $zip) { Remove-Item -Force $zip }
            Compress-Archive -Path $out -DestinationPath $zip
            Say ("package: {0} files in {1}; {2}" -f $r.files, $out, $zip)
        }
    }
    if ($failed.Count -gt 0) { break }   # a failed stage stops the run
}
if ($failed.Count -gt 0) { Say "FAILED: $($failed -join ', ')" 'Red'; exit 1 }
Say "OK: $($stages -join ', ')" 'Green'
exit 0

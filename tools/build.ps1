<#
.SYNOPSIS
  Builds the installable Pandaborn - Factions mod on E: and links it into the game's Mods folder.

.DESCRIPTION
  1. Mirrors mod/PandabornFactions (the repo source) into $BuildDir.
  2. Adds the two large panda body meshes, which are not in git, from the Reskin release on E:,
     under their faction-only names (Characters/Pandaborn/InkpawAdult|InkpawChild.Model.timbermesh).
  3. Removes anything in $BuildDir that is no longer part of the build.
  4. Runs tools/validate.py on the result (skip with -SkipValidate).
  5. Makes $ModsDir\PandabornFactions a directory junction to $BuildDir, so the heavy files stay on E:.

  Idempotent: unchanged files are not recopied. It only ever touches $BuildDir and the single
  $ModsDir\PandabornFactions entry; no other folder in Mods is read, changed or removed. If
  $ModsDir\PandabornFactions exists as a real folder (not a junction), the script stops instead of replacing it.
#>
[CmdletBinding()]
param(
    [string]$BuildDir = 'E:\PandabornDev\build\PandabornFactions',
    [string]$MeshSource = 'E:\PandabornDev\assets\Pandaborn-Reskin-release\Characters\Beaver',
    [string]$ModsDir = 'C:\Users\Israel Gonzalez\Documents\Timberborn\Mods',
    [string]$LinkName = 'PandabornFactions',
    [switch]$SkipValidate,
    [switch]$NoLink
)
$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$source = Join-Path $repo 'mod\PandabornFactions'
if (-not (Test-Path $source -PathType Container)) { throw "mod source not found: $source" }

# large binaries that live outside git: build-relative path -> source file
$meshes = [ordered]@{
    'Characters\Pandaborn\InkpawAdult.Model.timbermesh' = Join-Path $MeshSource 'BeaverAdult.Model.timbermesh'
    'Characters\Pandaborn\InkpawChild.Model.timbermesh' = Join-Path $MeshSource 'BeaverChild.Model.timbermesh'
}

function Copy-IfChanged([string]$from, [string]$to) {
    $src = Get-Item -LiteralPath $from
    if (Test-Path -LiteralPath $to) {
        $dst = Get-Item -LiteralPath $to
        if ($dst.Length -eq $src.Length -and $dst.LastWriteTimeUtc -eq $src.LastWriteTimeUtc) { return $false }
    }
    $dir = Split-Path $to -Parent
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
    Copy-Item -LiteralPath $from -Destination $to -Force   # Copy-Item keeps LastWriteTime
    return $true
}

# ---------------------------------------------------------------------------------------------- build
if (-not (Test-Path $BuildDir)) { New-Item -ItemType Directory -Force $BuildDir | Out-Null }
$BuildDir = (Resolve-Path $BuildDir).Path
$expected = @{}
$copied = 0

foreach ($f in Get-ChildItem -LiteralPath $source -Recurse -File) {
    $rel = $f.FullName.Substring($source.Length + 1)
    if ($rel -like '*.timbermesh' -and $meshes.Contains($rel)) { continue }
    $expected[$rel.ToLowerInvariant()] = $true
    if (Copy-IfChanged $f.FullName (Join-Path $BuildDir $rel)) { $copied++ }
}

foreach ($rel in $meshes.Keys) {
    $from = $meshes[$rel]
    if (-not (Test-Path -LiteralPath $from)) { throw "large mesh missing: $from" }
    $fs = [IO.File]::OpenRead($from)
    try { $b0 = $fs.ReadByte(); $b1 = $fs.ReadByte() } finally { $fs.Dispose() }
    if ($b0 -ne 0x78 -or $b1 -ne 0x9C) { throw "$from does not start with zlib header 78 9C" }
    $expected[$rel.ToLowerInvariant()] = $true
    if (Copy-IfChanged $from (Join-Path $BuildDir $rel)) { $copied++ }
}

# remove stale files and empty folders from the build output
$removed = 0
foreach ($f in Get-ChildItem -LiteralPath $BuildDir -Recurse -File) {
    $rel = $f.FullName.Substring($BuildDir.Length + 1)
    if (-not $expected.ContainsKey($rel.ToLowerInvariant())) {
        Remove-Item -LiteralPath $f.FullName -Force
        $removed++
    }
}
Get-ChildItem -LiteralPath $BuildDir -Recurse -Directory |
    Sort-Object { $_.FullName.Length } -Descending |
    Where-Object { -not (Get-ChildItem -LiteralPath $_.FullName -Force) } |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }

Write-Host ("build: {0} files in {1} ({2} copied, {3} removed)" -f $expected.Count, $BuildDir, $copied, $removed)

# ------------------------------------------------------------------------------------------- validate
if (-not $SkipValidate) {
    $py = Get-Command python -ErrorAction SilentlyContinue
    $pyArgs = @()
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue; $pyArgs = @('-3') }
    if (-not $py) { throw 'Python 3 not found; install it or pass -SkipValidate' }
    & $py.Source @pyArgs -I (Join-Path $repo 'tools\validate.py') --mod $BuildDir --quiet
    if ($LASTEXITCODE -ne 0) { throw "validation failed (exit $LASTEXITCODE); the mod was built but not linked" }
}

# ---------------------------------------------------------------------------------------------- link
if ($NoLink) { return }
if (-not (Test-Path -LiteralPath $ModsDir -PathType Container)) { throw "Mods folder not found: $ModsDir" }
$link = Join-Path $ModsDir $LinkName
$item = Get-Item -LiteralPath $link -Force -ErrorAction SilentlyContinue
if ($item) {
    $isLink = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
    if (-not $isLink) {
        throw "$link exists and is a real folder, not a junction. Not touching it; move it away by hand if it is stale."
    }
    $target = @($item.Target)[0]
    if ($target -and ((Resolve-Path -LiteralPath $target -ErrorAction SilentlyContinue).Path -eq $BuildDir -or $target -eq $BuildDir)) {
        Write-Host "link: $link -> $BuildDir (already in place)"
        return
    }
    # a junction pointing somewhere else: remove only the link itself, never its target's contents
    cmd /c rmdir "$link" | Out-Null
    if (Test-Path -LiteralPath $link) { throw "could not remove the old junction $link" }
}
New-Item -ItemType Junction -Path $link -Target $BuildDir | Out-Null
Write-Host "link: $link -> $BuildDir (created)"

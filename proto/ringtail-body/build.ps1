<#
.SYNOPSIS
  Builds the Ringtail body test mod (dev only) into E:\PandabornDev\build\proto\ringtail-body.
.DESCRIPTION
  1. Mirrors proto/ringtail-body/mod (manifest, the template merges) into the build folder.
  2. Copies the two Ringtail meshes from the character build output (not in git; src/pipeline/characters builds them)
     to Characters/Pandaborn/, and the Ringtail coats from mod/PandabornFactions/Materials/Pandaborn/Ringtails.
  3. Builds proto/ringtail-body/src (the picture probe) into <build>\Scripts.
  4. Removes stale files. Never touches the Mods folder: tools/run_game_test.ps1 -ExtraMods junctions it for a run,
     next to the Ringtail prototype (E:\PandabornDev\build\proto\ringtails), which this mod requires and merges onto.
#>
[CmdletBinding()]
param(
    [string]$BuildDir = 'E:\PandabornDev\build\proto\ringtail-body',
    [string]$MeshDir = 'E:\PandabornDev\build\characters\out'
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$repo = Resolve-Path (Join-Path $here '..\..')
$source = Join-Path $here 'mod'
New-Item -ItemType Directory -Force $BuildDir | Out-Null
$expected = @{}
function Put([string]$from, [string]$rel) {
    if (-not (Test-Path -LiteralPath $from)) { throw "missing: $from" }
    $to = Join-Path $BuildDir $rel
    New-Item -ItemType Directory -Force (Split-Path $to -Parent) | Out-Null
    Copy-Item -LiteralPath $from -Destination $to -Force
    $script:expected[$rel.ToLowerInvariant()] = $true
}
foreach ($f in Get-ChildItem -LiteralPath $source -Recurse -File) { Put $f.FullName $f.FullName.Substring($source.Length + 1) }
foreach ($m in 'RingtailAdult.Model.timbermesh', 'RingtailChild.Model.timbermesh', 'WoodenOx.Model.timbermesh') { Put (Join-Path $MeshDir $m) "Characters\Pandaborn\$m" }
# the Ringtail fur masks for the Reskin's factions-compat branch (<model asset>.FurMask), with their meta files
foreach ($f in Get-ChildItem -LiteralPath (Join-Path $repo 'mod\PandabornFactions\Characters\Pandaborn') -File | Where-Object { $_.Name -like '*.FurMask.png*' }) {
    Put $f.FullName "Characters\Pandaborn\$($f.Name)"
}
foreach ($sub in 'Ringtails', 'Outfits\Ringtail') {
    $dir = Join-Path $repo "mod\PandabornFactions\Materials\Pandaborn\$sub"
    if (-not (Test-Path -LiteralPath $dir)) { continue }
    foreach ($f in Get-ChildItem -LiteralPath $dir -Recurse -File | Where-Object { $_.Name -like '*.png' -or $_.Name -like '*.meta.json' }) {
        Put $f.FullName ("Materials\Pandaborn\$sub\" + $f.FullName.Substring($dir.Length + 1))
    }
}
# the attachments bundle (src/unity/PandabornAttachments, built into E:\PandabornDev\build\characters\attachments)
$bundle = 'E:\PandabornDev\build\characters\attachments\pandabornattachments_win'
if (Test-Path -LiteralPath $bundle) { Put $bundle 'AssetBundles\pandabornattachments_win' } else { Write-Warning "no attachments bundle at $bundle" }
$project = Join-Path $here 'src\PandabornProtoRingtailBody.csproj'
$log = & dotnet build $project -c Release -v q --nologo "-p:ModOut=$BuildDir" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'probe build failed' }
$expected['scripts\pandabornprotoringtailbody.dll'] = $true
foreach ($f in Get-ChildItem -LiteralPath $BuildDir -Recurse -File) {
    $rel = $f.FullName.Substring($BuildDir.Length + 1)
    if (-not $expected.ContainsKey($rel.ToLowerInvariant())) { Remove-Item -LiteralPath $f.FullName -Force; Write-Host "removed stale $rel" }
}
Write-Host "Built $BuildDir ($($expected.Count) files)" -ForegroundColor Green

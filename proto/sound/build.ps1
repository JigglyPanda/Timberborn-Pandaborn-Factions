<#
.SYNOPSIS
  Builds the sound prototype mod into E:\PandabornDev\build\proto\sound: a layered dev mod for the installed faction
  (Id JigglyPanda.PandabornProtoSound, requires JigglyPanda.PandabornFactions) that carries the pandabornsounds bundle
  and blueprint fragments pointing the faction's buildings, colonist calls and wonder at those sounds.

.DESCRIPTION
  * mirrors proto/sound/mod (manifest + same-path blueprint fragments) into -Out;
  * copies pandabornsounds_win (and _mac when built) from -Bundles into -Out\AssetBundles, unrenamed; -BuildBundle runs
    tools\build_sound.ps1 first;
  * ships no bundle when the installed faction mod already ships pandabornsounds (it does since commit b24e571): two
    enabled mods with the same bundle crash every game ("another AssetBundle with the same files is already loaded";
    docs/tech/look.md, problem 10). It never ships a DLL or another bundle.
  Test (one game at a time; the runner queues behind other lanes):
    & tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RequestJson proto\sound\tests\sound.request.json `
        -OnlyMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\sound -WaitForGameSeconds 10800 `
        -TimeoutSeconds 1200
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File proto\sound\build.ps1 -BuildBundle
#>
[CmdletBinding()]
param(
    [string]$Out = 'E:\PandabornDev\build\proto\sound',
    [string]$Bundles = 'E:\PandabornDev\build\sound\AssetBundles',
    [string]$BundleName = 'pandabornsounds',
    [string]$InstalledFaction = "$env:USERPROFILE\Documents\Timberborn\Mods\PandabornFactions",
    [switch]$BuildBundle
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

$shipped = @(Get-ChildItem -ErrorAction SilentlyContinue "$InstalledFaction\AssetBundles" -Filter "$BundleName*" |
             Where-Object { $_.Extension -ne '.manifest' })
# Ship the bundle ONLY while the installed faction does not: two enabled mods with the same bundle crash every game
# (run sound-1 did exactly that after the faction adopted pandabornsounds in commit b24e571). Fragments only otherwise.
$shipBundle = $shipped.Count -eq 0
if (-not $shipBundle) {
    Write-Host "the installed faction ships $($shipped.Name -join ', '): the prototype carries blueprint fragments only"
}

if ($BuildBundle) {
    & powershell -ExecutionPolicy Bypass -File "$repo\tools\build_sound.ps1"
    if ($LASTEXITCODE -ne 0) { throw "tools\build_sound.ps1 failed ($LASTEXITCODE)" }
}
$win = Join-Path $Bundles "$($BundleName)_win"
if (-not (Test-Path $win)) { throw "$win not built: run tools\build_sound.ps1 (or this script with -BuildBundle)" }

New-Item -ItemType Directory -Force $Out | Out-Null
robocopy "$repo\proto\sound\mod" $Out /MIR /XD AssetBundles /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
$ab = Join-Path $Out 'AssetBundles'
New-Item -ItemType Directory -Force $ab | Out-Null
Get-ChildItem $ab | Remove-Item -Force
if ($shipBundle) {
    # bundles only: the game would skip a *.manifest, but tools/validate.py reads every file as an asset and reports the
    # bundle and its .manifest as one duplicated path
    Copy-Item -Force $win $ab
    $mac = Join-Path $Bundles "$($BundleName)_mac"
    if (Test-Path $mac) { Copy-Item -Force $mac $ab } else { Write-Warning "$mac not built (Windows-only prototype)" }
} else {
    Remove-Item -Force $ab
}
Get-ChildItem -Recurse -File $Out | Select-Object @{ n = 'File'; e = { $_.FullName.Substring($Out.Length + 1) } }, Length |
    Format-Table -AutoSize | Out-String | Write-Host
"prototype in $Out"

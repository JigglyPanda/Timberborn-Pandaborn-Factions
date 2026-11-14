<#
.SYNOPSIS
  Builds the installable Pandaborn - Factions mod on E: and links it into the game's Mods folder.

.DESCRIPTION
  Kept for existing callers; the build is now tools/pandaborn.ps1. This runs its stages
  generate, assemble, validate, install:
    1. catalogue/ -> E:\PandabornDev\build\gen\PandabornFactions (generated blueprints, collections, loc).
    2. mod/PandabornFactions (hand-written files) + generated data + the two panda body meshes (from the Reskin release
       on E:, not in git) -> staging folder E:\PandabornDev\build\stage\PandabornFactions.
    3. tools/validate.py on the staging folder. -SkipValidate is accepted for old callers but install always
       validates: a broken build is never linked into the game.
    4. Mirror into $BuildDir and make $ModsDir\PandabornFactions a directory junction to it (as before: it never
       touches any other Mods entry and refuses to replace a real folder).
#>
[CmdletBinding()]
param(
    [string]$BuildDir = 'E:\PandabornDev\build\PandabornFactions',
    [string]$ModsDir = 'C:\Users\Israel Gonzalez\Documents\Timberborn\Mods',
    [string]$LinkName = 'PandabornFactions',
    [switch]$SkipValidate,
    [switch]$NoLink
)
$ErrorActionPreference = 'Stop'
$stages = if ($SkipValidate) { 'generate,assemble,install' } else { 'generate,assemble,validate,install' }
$a = @('-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'pandaborn.ps1'), $stages,
       '-InstallDir', $BuildDir, '-ModsDir', $ModsDir, '-LinkName', $LinkName)
if ($NoLink) { $a += '-NoLink' }
& powershell @a
exit $LASTEXITCODE

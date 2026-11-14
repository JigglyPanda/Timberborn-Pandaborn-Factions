<#
.SYNOPSIS
  Builds the runtime code (src/code: bootstrap, Specs, Core and every feature module, with each module's data and the
  look bundle when present) into a dev-only mod folder that rides on the installed faction mod.
.DESCRIPTION
  Until the owner switches the code on in the faction mod itself (src/code/README.md, "Build"), feature tests load the
  code through this folder instead of changing the shared E:\PandabornDev\build\PandabornFactions install:
    tools\run_game_test.ps1 -Faction Inkpaws -ExtraMods E:\PandabornDev\build\PandabornCodeDev ...
  The folder is rebuilt from scratch each time (manifest Id JigglyPanda.PandabornCodeDev, requires
  JigglyPanda.PandabornFactions). Never enable it together with another mod that carries the code (proto/stage0) or with
  the retired look prototypes (JigglyPanda.PandabornProtoLook): the Look data would be loaded twice.
  -DevSwitch writes pandaborn.dev.txt ('force-off: Look', 'simulate-missing-api: Look'; ';' separates lines).
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\build_code_devmod.ps1 -DevSwitch 'force-off: Look'
#>
[CmdletBinding()]
param(
    [string]$Out = 'E:\PandabornDev\build\PandabornCodeDev',
    [string]$DevSwitch = ''
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
if (Test-Path -LiteralPath $Out) {
    $item = Get-Item -LiteralPath $Out -Force
    if ($item.LinkType) { throw "$Out is a link; refusing to clear it" }
    Get-ChildItem -LiteralPath $Out -Force | Remove-Item -Recurse -Force
}
New-Item -ItemType Directory -Force $Out | Out-Null

$sln = Join-Path $repo 'src\code\Pandaborn.Code.sln'
$log = & dotnet build $sln -c Release -v q --nologo "-p:ModOut=$Out" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'code build failed' }
$log | Where-Object { $_ -match 'Pandaborn\.Look' } | ForEach-Object { Write-Host $_ }

$manifest = [ordered]@{
    Name = 'Pandaborn - Factions code (dev only)'
    Version = '0.0.1'
    Id = 'JigglyPanda.PandabornCodeDev'
    MinimumGameVersion = '1.1.0.0'
    Description = 'Development-only: the runtime code of Pandaborn - Factions (bootstrap and feature modules) for in-game tests, until it ships inside the faction mod. Never shipped. Art and code are AI-generated.'
    RequiredMods = @([ordered]@{ Id = 'JigglyPanda.PandabornFactions' })
    OptionalMods = @()
}
[IO.File]::WriteAllText((Join-Path $Out 'manifest.json'), ($manifest | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding($false)))
if ($DevSwitch) {
    [IO.File]::WriteAllText((Join-Path $Out 'pandaborn.dev.txt'), ($DevSwitch -replace ';', "`n"))
    Write-Host "dev switch written: $DevSwitch" -ForegroundColor Yellow
}
$files = @(Get-ChildItem -LiteralPath $Out -Recurse -File)
Write-Host "Built $Out ($($files.Count) files)" -ForegroundColor Green

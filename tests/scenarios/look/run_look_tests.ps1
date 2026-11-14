# Runs the Pandaborn.Look scenarios in order (same-session chain, feature on, relaunch into Folktails, force-off,
# simulate-missing-api). Needs the shipping bundle (tools/build_look.ps1 -BundleName pandabornlook). Log: E:/PandabornDev/build/look/module_runs.txt
param([string[]]$Only = @())
$ErrorActionPreference = 'Continue'
$repo = 'C:\Users\Israel Gonzalez\Desktop\Claude Projects\Claude Porjects\Timberborn-Pandaborn-Factions'
Set-Location $repo
$harness = 'E:\PandabornDev\build\PandabornDevHarness-look'
$own = 'PandabornFactions,PandabornDevHarness,Inkpaws,Pandaborn.Look,Pandaborn.Core,Pandaborn.Bootstrap,Pandaborn.Specs,[Pandaborn]'
$summary = 'E:\PandabornDev\build\look\module_runs.txt'
$b = & dotnet build "$repo\src\devharness\PandabornDevHarness.csproj" -c Release -v q --nologo "-p:ModOut=$harness" 2>&1
if ($LASTEXITCODE -ne 0) { $b; "harness build failed" | Add-Content $summary; exit 2 }
$runs = @(
  @{ id = 'look-module-then-2';      json = 'tests\scenarios\look\inkpaws_then_folktails.json'; sw = '';                          t = 1200 },
  @{ id = 'look-module-on-2';        json = 'tests\scenarios\look\inkpaws_on.json';             sw = '';                          t = 900 },
  @{ id = 'look-module-relaunch-2';  json = 'tests\scenarios\look\folktails.json';              sw = '';                          t = 600 },
  @{ id = 'look-module-forceoff-2';  json = 'tests\scenarios\look\inkpaws_forced_off.json';     sw = 'force-off: Look';           t = 600 },
  @{ id = 'look-module-missingapi-2';json = 'tests\scenarios\look\inkpaws_missing_api.json';    sw = 'simulate-missing-api: Look';t = 600 }
)
foreach ($r in $runs) {
  if ($Only.Count -and $Only -notcontains $r.id) { continue }
  & "$repo\tools\build_code_devmod.ps1" -DevSwitch $r.sw | Out-Host
  $start = Get-Date
  & powershell -ExecutionPolicy Bypass -File "$repo\tools\run_game_test.ps1" -RequestJson $r.json -ExtraMods 'E:\PandabornDev\build\PandabornCodeDev' `
      -RunId $r.id -NoBuild -HarnessDir $harness -WaitForGameSeconds 10800 -TimeoutSeconds $r.t -OwnPatterns $own *> "E:\PandabornDev\build\look\$($r.id).txt"
  $code = $LASTEXITCODE
  "{0} {1} exit {2} started {3} ended {4}" -f (Get-Date -Format s), $r.id, $code, $start.ToString('s'), (Get-Date).ToString('s') | Add-Content $summary
}

<#
.SYNOPSIS
  Shared helpers for the Unity bundle builds (dot-sourced by tools\build_look.ps1 and tools\build_plants.ps1).

.DESCRIPTION
  Resolve-UnityEditor picks the Unity 6000.5.11f1 editor:
    * an explicit -UnityPath (the editor folder or Unity.exe) always wins; with -Mac it must have Mac Build Support;
    * otherwise, for Windows-only builds: the Hub install on C: first, then the private copy on E:;
    * with -Mac: the first candidate that has Editor\Data\PlaybackEngines\MacStandaloneSupport (today only the E: copy,
      which carries the Mac Build Support (Mono) module; see docs/tech/mac.md).
  Get-MacProject returns the Unity project used for the macOS target: a sibling of the Windows project
  (<Project>-mac), so building for StandaloneOSX never reimports or locks the Windows project, and both targets can be
  built at the same time.
#>

$script:UnityCandidates = @(
    'C:\Program Files\Unity\Hub\Editor\6000.5.11f1\Editor\Unity.exe',
    'E:\PandabornDev\tools\unity-6000.5.11f1\Editor\Unity.exe'
)

function Test-UnityMacSupport([string]$Exe) {
    Test-Path (Join-Path (Split-Path -Parent $Exe) 'Data\PlaybackEngines\MacStandaloneSupport\UnityEditor.OSXStandalone.Extensions.dll')
}

function Resolve-UnityEditor([string]$UnityPath, [switch]$Mac) {
    if ($UnityPath) {
        $exe = if ((Test-Path $UnityPath -PathType Container)) {
            @((Join-Path $UnityPath 'Editor\Unity.exe'), (Join-Path $UnityPath 'Unity.exe')) | Where-Object { Test-Path $_ } | Select-Object -First 1
        } else { $UnityPath }
        if (-not $exe -or -not (Test-Path $exe)) { throw "Unity editor not found at $UnityPath" }
        if ($Mac -and -not (Test-UnityMacSupport $exe)) {
            throw "-Mac: $exe has no Mac Build Support (Editor\Data\PlaybackEngines\MacStandaloneSupport); see docs/tech/mac.md"
        }
        return $exe
    }
    $found = $script:UnityCandidates | Where-Object { Test-Path $_ }
    if ($Mac) {
        $exe = $found | Where-Object { Test-UnityMacSupport $_ } | Select-Object -First 1
        if (-not $exe) {
            throw ("-Mac: no Unity 6000.5.11f1 with Mac Build Support found (looked at: " + ($script:UnityCandidates -join ', ') +
                   "). Set up the E: copy as described in docs/tech/mac.md, or pass -UnityPath")
        }
        return $exe
    }
    $exe = $found | Select-Object -First 1
    if (-not $exe) { throw ("no Unity 6000.5.11f1 found (looked at: " + ($script:UnityCandidates -join ', ') + "); pass -UnityPath") }
    return $exe
}

function Get-MacProject([string]$Project, [string]$MacProject) {
    if ($MacProject) { return $MacProject }
    return ($Project.TrimEnd('\', '/') + '-mac')
}

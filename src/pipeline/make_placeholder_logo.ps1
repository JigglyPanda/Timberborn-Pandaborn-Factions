# Draws the PLACEHOLDER Inkpaws faction logo (a flat panda face in an ink ring) until real art exists.
# Output: mod/PandabornFactions/Sprites/Pandaborn/Avatars/InkpawsLogo.png (+ .meta.json marking it a sprite).
param(
    [int]$Size = 256
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$repo = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$outDir = Join-Path $repo 'mod\PandabornFactions\Sprites\Pandaborn\Avatars'
New-Item -ItemType Directory -Force $outDir | Out-Null
$out = Join-Path $outDir 'InkpawsLogo.png'

$s = $Size / 256.0
function New-Rect([double]$x, [double]$y, [double]$w, [double]$h) {
    New-Object System.Drawing.RectangleF ([float]($x * $s)), ([float]($y * $s)), ([float]($w * $s)), ([float]($h * $s))
}

$bmp = New-Object System.Drawing.Bitmap $Size, $Size, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.Clear([System.Drawing.Color]::Transparent)

$ink = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 28, 28, 34))
$paper = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 244, 239, 226))
$jade = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 96, 150, 104))
$blush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(150, 232, 150, 140))

# jade disc with an ink rim
$g.FillEllipse($ink, (New-Rect 4 4 248 248))
$g.FillEllipse($jade, (New-Rect 14 14 228 228))
# ears
$g.FillEllipse($ink, (New-Rect 52 50 58 58))
$g.FillEllipse($ink, (New-Rect 146 50 58 58))
# face
$g.FillEllipse($paper, (New-Rect 58 72 140 124))
# eye patches, tilted like teardrops
foreach ($side in @(@{x = 84; a = -30}, @{x = 136; a = 30})) {
    $st = $g.Save()
    $g.TranslateTransform([float](($side.x + 18) * $s), [float](128 * $s))
    $g.RotateTransform([float]$side.a)
    $g.FillEllipse($ink, (New-Rect -16 -24 32 46))
    $g.FillEllipse($paper, (New-Rect -4 -10 11 11))
    $g.Restore($st)
}
# nose, mouth and cheeks
$g.FillEllipse($ink, (New-Rect 116 150 24 16))
$pen = New-Object System.Drawing.Pen ($ink.Color), ([float](4 * $s))
$pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
$pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
$g.DrawArc($pen, (New-Rect 106 154 24 20), 20, 140)
$g.DrawArc($pen, (New-Rect 126 154 24 20), 20, 140)
$g.FillEllipse($blush, (New-Rect 74 154 22 14))
$g.FillEllipse($blush, (New-Rect 160 154 22 14))

$g.Dispose()
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Set-Content -Path ($out + '.meta.json') -Value '{"isSprite": true}' -Encoding ascii -NoNewline
Write-Host "wrote $out"

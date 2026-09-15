# Bumps the app version (so installed iPads pick up the new service-worker cache),
# commits everything and pushes to GitHub. GitHub Pages redeploys automatically (~1 min).
#
#   .\deploy.ps1 "what changed"
#   .\deploy.ps1 "what changed" -Minor     (1.0.x -> 1.1.0)
param(
    [string]$Message = "Update",
    [switch]$Minor
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$index = Get-Content index.html -Raw -Encoding UTF8
if ($index -notmatch "const APP_VERSION = '(\d+)\.(\d+)\.(\d+)'") { throw "APP_VERSION not found in index.html" }
$maj = [int]$Matches[1]; $min = [int]$Matches[2]; $pat = [int]$Matches[3]
if ($Minor) { $min++; $pat = 0 } else { $pat++ }
$new = "$maj.$min.$pat"

$index = $index -replace "const APP_VERSION = '\d+\.\d+\.\d+'", "const APP_VERSION = '$new'"
[IO.File]::WriteAllText("$PSScriptRoot\index.html", $index, (New-Object Text.UTF8Encoding $false))

$sw = Get-Content sw.js -Raw -Encoding UTF8
$sw = $sw -replace "const VERSION = '\d+\.\d+\.\d+'", "const VERSION = '$new'"
[IO.File]::WriteAllText("$PSScriptRoot\sw.js", $sw, (New-Object Text.UTF8Encoding $false))

git add -A
git commit -m "v$new - $Message"
if (-not (git remote)) { throw "No git remote yet. Create the GitHub repo first (see README.md)." }
git push
Write-Host "Deployed v$new. GitHub Pages updates in about a minute; on the iPad close and reopen the app twice." -ForegroundColor Green

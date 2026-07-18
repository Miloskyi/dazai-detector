# Push script — token is passed via git credential or environment, not hardcoded here.
# Usage: set GH_TOKEN env var before running, or git will prompt for credentials.
param([string]$Token = $env:GH_TOKEN)

$dir = "C:\Users\gomez\Downloads\Dazai-Detector--main"
Set-Location $dir

if ($Token) {
    git remote set-url origin "https://Miloskyi:${Token}@github.com/Miloskyi/dazai-detector.git"
}

git push -u origin main --force
Write-Host "Done: https://github.com/Miloskyi/dazai-detector" -ForegroundColor Green

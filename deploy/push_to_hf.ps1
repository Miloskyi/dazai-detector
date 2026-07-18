# push_to_hf.ps1
# Ejecutar desde: C:\Users\gomez\Downloads\Dazai-Detector--main
# Uso: .\deploy\push_to_hf.ps1
#
# Hace push del backend a HF Space GOMITAA/dazai-detector
# El Space DEBE estar creado con SDK: Docker (cpu-basic, gratis)

$ErrorActionPreference = "Stop"
$HFUser  = "GOMITAA"
$HFSpace = "dazai-detector"
$RemoteURL = "https://huggingface.co/spaces/$HFUser/$HFSpace"

Write-Host ""
Write-Host "===============================" -ForegroundColor Cyan
Write-Host "  Dazai Detector - HF Deploy" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host "  Space: $RemoteURL"
Write-Host ""

# 1. Configurar remote si no existe
$remotes = git remote 2>&1
if ($remotes -notmatch "huggingface") {
    Write-Host "[1/3] Agregando remote 'huggingface'..." -ForegroundColor Yellow
    git remote add huggingface $RemoteURL
} else {
    Write-Host "[1/3] Remote 'huggingface' ya configurado." -ForegroundColor Green
}

# 2. Guardar branch actual y crear branch temporal
$currentBranch = git rev-parse --abbrev-ref HEAD
Write-Host "[2/3] Preparando branch de deploy..." -ForegroundColor Yellow

git branch -D hf-deploy 2>$null
git checkout -b hf-deploy

# Reemplazar README con el del Space (tiene el frontmatter que HF necesita)
Copy-Item "deploy\huggingface-space\README.md" "README.md" -Force
git add README.md
git commit -q -m "Deploy: Hugging Face Space README"

# 3. Push (Git pedira usuario y password — usa tu token HF como password)
Write-Host "[3/3] Haciendo push a Hugging Face..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Git va a pedir credenciales:" -ForegroundColor Magenta
Write-Host "  Username: $HFUser" -ForegroundColor Magenta
Write-Host "  Password: pega tu token HF (hf_...)" -ForegroundColor Magenta
Write-Host ""

git push --force huggingface hf-deploy:main

# Volver al branch original
git checkout $currentBranch
git branch -D hf-deploy

Write-Host ""
Write-Host "===============================" -ForegroundColor Green
Write-Host "  Push completado!" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host ""
Write-Host "  El build esta corriendo en HF. Monitorea en:" -ForegroundColor Yellow
Write-Host "  https://huggingface.co/spaces/$HFUser/$HFSpace" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Cuando este live, configura estas variables en:" -ForegroundColor Yellow
Write-Host "  Settings > Variables and Secrets:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  LLM_PROVIDER  = openai"
Write-Host "  LLM_MODEL     = llama-3.3-70b-versatile"
Write-Host "  LLM_BASE_URL  = https://api.groq.com/openai/v1"
Write-Host "  LLM_API_KEY   = (tu Groq key)"
Write-Host "  BACKEND_CORS_ORIGINS = https://dazai-detector.pages.dev"
Write-Host ""

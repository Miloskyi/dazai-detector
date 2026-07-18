#!/usr/bin/env pwsh
# deploy.ps1 — Deploy Dazai Detector to Hugging Face Spaces (backend) + Cloudflare Pages (frontend)
#
# Prerequisites:
#   1. git installed (already done — repo has initial commit)
#   2. huggingface-cli installed: pip install huggingface_hub[cli]
#   3. A Hugging Face account with a Space created:
#      - Go to https://huggingface.co/new-space
#      - SDK: Docker | Hardware: cpu-basic (free) | Visibility: Public
#      - Name it whatever you want (e.g. "dazai-detector")
#   4. A Cloudflare account (free, no card): https://dash.cloudflare.com/sign-up

param(
    [string]$HFUser    = "",   # Your HF username, e.g. "juanpacol"
    [string]$HFSpace   = "",   # Your HF Space name, e.g. "dazai-detector"
    [string]$CFProject = "dazai-detector"  # Cloudflare Pages project name
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── 0. Collect missing params interactively ──────────────────────────────────
if (-not $HFUser)  { $HFUser  = Read-Host "Enter your Hugging Face username" }
if (-not $HFSpace) { $HFSpace = Read-Host "Enter your Hugging Face Space name (e.g. dazai-detector)" }

$HF_REMOTE_URL = "https://huggingface.co/spaces/$HFUser/$HFSpace"
$HF_API_URL    = "https://$($HFUser.ToLower())-$($HFSpace.ToLower()).hf.space"

Write-Host ""
Write-Host "=== DEPLOY CONFIG ===" -ForegroundColor Cyan
Write-Host "  HF Space URL  : $HF_REMOTE_URL"
Write-Host "  Backend API   : $HF_API_URL"
Write-Host "  CF Project    : $CFProject"
Write-Host ""

# ── 1. Add HF remote if missing ──────────────────────────────────────────────
$remotes = git remote 2>&1
if ($remotes -notmatch "huggingface") {
    Write-Host "[1/4] Adding 'huggingface' remote..." -ForegroundColor Yellow
    git remote add huggingface $HF_REMOTE_URL
} else {
    Write-Host "[1/4] 'huggingface' remote already configured." -ForegroundColor Green
}

# ── 2. Login to HF (if not already) ─────────────────────────────────────────
Write-Host "[2/4] Logging into Hugging Face..." -ForegroundColor Yellow
huggingface-cli login

# ── 3. Push backend to HF Space via hf-deploy branch ────────────────────────
Write-Host "[3/4] Pushing backend to Hugging Face Space..." -ForegroundColor Yellow
Write-Host "      (This triggers a Docker build on HF — takes ~5 min)"
Write-Host ""

$currentBranch = git rev-parse --abbrev-ref HEAD

# Clean up any leftover hf-deploy branch
git branch -D hf-deploy 2>$null

# Create throwaway branch with HF Space README at root
git checkout -b hf-deploy
Copy-Item "deploy\huggingface-space\README.md" "README.md" -Force
git add README.md
git commit -q -m "Deploy: use Hugging Face Space README"

# Push to HF Space main branch
git push --force huggingface "hf-deploy:main"

# Return to original branch
git checkout $currentBranch
git branch -D hf-deploy

Write-Host ""
Write-Host "  Backend pushed! Monitor build at:" -ForegroundColor Green
Write-Host "  https://huggingface.co/spaces/$HFUser/$HFSpace (Logs tab)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Once the Space is live, set these variables in Space Settings > Variables:" -ForegroundColor Yellow
Write-Host "    BACKEND_CORS_ORIGINS = https://$CFProject.pages.dev"
Write-Host "    LLM_PROVIDER         = openai"
Write-Host "    LLM_API_KEY          = <your-groq-key>"
Write-Host "    LLM_MODEL            = llama-3.3-70b-versatile"
Write-Host "    LLM_BASE_URL         = https://api.groq.com/openai/v1"
Write-Host ""

# ── 4. Build & deploy frontend to Cloudflare Pages ───────────────────────────
Write-Host "[4/4] Building frontend and deploying to Cloudflare Pages..." -ForegroundColor Yellow

# Check wrangler
if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: npx not found. Install Node.js from https://nodejs.org/" -ForegroundColor Red
    Write-Host "  Then re-run this script." -ForegroundColor Red
    exit 1
}

Push-Location "platform\frontend"

# Install deps if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "  Installing frontend dependencies..."
    npm ci --silent
}

# Production build pointing at the HF Space
Write-Host "  Building React app with VITE_API_URL=$HF_API_URL..."
$env:VITE_API_URL = $HF_API_URL
npm run build

# Deploy via Wrangler (will prompt for Cloudflare login on first run)
Write-Host "  Deploying dist/ to Cloudflare Pages (will open browser for login if needed)..."
npx wrangler pages deploy dist --project-name=$CFProject --commit-dirty=true

Pop-Location

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  DEPLOY COMPLETE" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend : https://$CFProject.pages.dev" -ForegroundColor Cyan
Write-Host "  Backend  : $HF_API_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT — after both are live:" -ForegroundColor Yellow
Write-Host "  1. Go to HF Space Settings > Variables"
Write-Host "     Set BACKEND_CORS_ORIGINS=https://$CFProject.pages.dev"
Write-Host "  2. Verify: open the Pages URL, check Dashboard loads real stats"
Write-Host "  3. Send one chat message to confirm the anti-hallucination chain"
Write-Host ""

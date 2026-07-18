#!/usr/bin/env bash
# Pushes this project to a Hugging Face Space without touching the project's
# main README.md/branch: it builds a throwaway `hf-deploy` branch where the
# root README.md is swapped for the Space's frontmatter'd README, commits
# only that swap, force-pushes it to the `huggingface` remote, then returns
# you to the branch you started on.
#
# One-time setup before running this:
#   1. Create a Space at huggingface.co/new-space with SDK = Docker.
#   2. git remote add huggingface https://huggingface.co/spaces/<you>/<space-name>
#   3. huggingface-cli login  (or set up an SSH key on your HF account)
#
# Usage: ./deploy/huggingface-space/push.sh

set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository. Run 'git init' and commit your work first." >&2
  exit 1
fi

if ! git remote get-url huggingface >/dev/null 2>&1; then
  echo "No 'huggingface' remote configured. See the setup steps in this script's header." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "You have uncommitted changes. Commit or stash them before deploying." >&2
  exit 1
fi

original_branch=$(git rev-parse --abbrev-ref HEAD)

git branch -D hf-deploy >/dev/null 2>&1 || true
git checkout -b hf-deploy

cp deploy/huggingface-space/README.md README.md
git add README.md
git commit -q -m "Deploy: use Hugging Face Space README"

echo "Pushing to the 'huggingface' remote (this can take a few minutes — the"
echo "pipeline reruns during the image build)..."
git push --force huggingface hf-deploy:main

git checkout "$original_branch"
git branch -D hf-deploy

echo "Done. Check build progress on your Space's page (Logs tab)."

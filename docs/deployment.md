# Deployment — Free Hosting

Backend on Hugging Face Spaces (Docker SDK), frontend on Cloudflare Pages. Both are free with no
credit card, and neither has meaningful cold-start risk for a judge opening a link.

## Why this split

The backend (FastAPI + XGBoost + SHAP + ChromaDB) needs a real Docker container with enough RAM; the
frontend is a static build that any CDN can serve. Hugging Face Spaces' filesystem is ephemeral, so
`deploy/huggingface-space/Dockerfile` bakes the demo dataset, the trained hybrid model, the first
report, and the ChromaDB index into the image at **build time** instead of writing them at runtime —
see that file's comments for why.

## 1. Deploy the backend to Hugging Face Spaces

1. Create a Space at huggingface.co/new-space: SDK = **Docker**, hardware = free `cpu-basic`.
2. Locally, add it as a git remote and log in:
   ```bash
   git remote add huggingface https://huggingface.co/spaces/<you>/<space-name>
   huggingface-cli login
   ```
3. Commit your work on your normal branch (the deploy script never touches it directly):
   ```bash
   git add -A && git commit -m "Initial commit"
   ```
4. Run the deploy script:
   ```bash
   ./deploy/huggingface-space/push.sh
   ```
   This builds a throwaway `hf-deploy` branch with the Space's frontmatter'd README swapped in (see
   the script's comments), pushes it, and returns you to your original branch — your project's real
   `README.md` is never modified on your main branch.
5. Watch the Space's **Logs** tab for the build (a few minutes — the pipeline reruns during the image
   build). Once it's live, your API is at `https://<you>-<space-name>.hf.space`.
6. In the Space's **Settings → Variables**, set `BACKEND_CORS_ORIGINS` to your frontend's URL once you
   have it (step 2 below) — comma-separated if you need more than one origin.

To redeploy after changing backend/pipeline code, just re-run `push.sh`.

## 2. Deploy the frontend to Cloudflare Pages

1. Build locally to confirm it compiles clean:
   ```bash
   cd platform/frontend
   VITE_API_URL=https://<you>-<space-name>.hf.space npm run build
   ```
2. Deploy the `dist/` folder with Wrangler (no Cloudflare account setup beyond `wrangler login`):
   ```bash
   npx wrangler login
   npx wrangler pages deploy dist --project-name=dazai-detector
   ```
   Or connect the GitHub repo in the Cloudflare dashboard instead, with build command `npm run build`,
   output directory `dist`, and the `VITE_API_URL` environment variable set to your Space's URL — this
   gives you auto-deploy on every push instead of a manual `wrangler pages deploy`.
3. Cloudflare gives you a `https://dazai-detector.pages.dev` URL. Set that as `BACKEND_CORS_ORIGINS` on
   the Hugging Face Space (step 6 above) so the browser's CORS check passes.

## 3. Verify end-to-end

- Open the Pages URL, confirm the Dashboard loads real stats (proves the frontend reached the Space).
- Ask the chat one question of each of the 4 types and confirm each answer's `sources` shows a real
  tool name — same anti-hallucination guarantee as local/Docker, now running on free infra.

## Notes

- The MCP server (`platform/mcp_server`) is not deployed publicly by default — the backend already
  reuses its agents directly for chat (`backend/services/chat_service.py`), so nothing is lost. If you
  want the MCP server itself reachable by external MCP clients, deploy it as a second Hugging Face
  Space using the same pattern (copy `deploy/huggingface-space/`, point the `dockerfile`'s CMD at
  `platform/mcp_server/server.py` with `MCP_TRANSPORT=http`, and set `MCP_PORT` to match `app_port`).
- LLM narratives still default to the offline template unless you set `LLM_PROVIDER`/`LLM_API_KEY` in
  the Space's Variables — same fallback behavior as local/Docker.
- To refresh the baked-in demo data (e.g. after tuning the model), just re-run `push.sh` — the pipeline
  reruns during the image build every time.

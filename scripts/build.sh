#!/usr/bin/env bash
# Render build script — installs deps and pre-bakes the pipeline artifacts
# so the server starts with data ready (no cold-start bootstrap needed).
set -e

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Running pipeline bootstrap ==="
# Add project root and platform/ to PYTHONPATH
export PYTHONPATH="$(pwd):$(pwd)/platform:$PYTHONPATH"

echo "--- Step 1/4: generating synthetic dataset ---"
python intelligence/pipeline/make_sample.py

echo "--- Step 2/4: running hybrid model pipeline ---"
python intelligence/pipeline/run_pipeline.py

echo "--- Step 3/4: generating report ---"
python platform/backend/services/report_service.py

echo "--- Step 4/4: ingesting into ChromaDB ---"
python platform/rag/ingest.py

echo "=== Build complete ==="

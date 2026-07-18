# Hugging Face Spaces (Docker SDK) — backend deploy.
#
# Unlike docker/python.Dockerfile (used by docker-compose, where a separate
# `pipeline` service writes to a bind-mounted volume), Spaces' filesystem is
# ephemeral: anything written only at container start vanishes on restart. So
# here the dataset, hybrid model, first report, and RAG index are all baked
# into the image as build-time RUN steps instead.
#
# Build context is the project root (see deploy/README.md for the exact push
# instructions) — this file only gets selected via the Space's `dockerfile:`
# setting in the root README.md frontmatter.

FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY intelligence/ intelligence/
COPY platform/backend/ platform/backend/
COPY platform/mcp_server/ platform/mcp_server/
COPY platform/rag/ platform/rag/

RUN python intelligence/pipeline/make_sample.py \
    && python intelligence/pipeline/run_pipeline.py \
    && python platform/backend/services/report_service.py \
    && python platform/rag/ingest.py

ENV PORT=7860
EXPOSE 7860

CMD ["python", "platform/backend/main.py"]

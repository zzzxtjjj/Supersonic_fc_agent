FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/opt/huggingface \
    SERVE_FRONTEND=true \
    FRONTEND_DIST=/app/frontend/dist

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/
COPY backend/ ./backend/
COPY data/ ./data/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist/

# Production images carry the exact local RAG models and run offline afterward.
RUN python -c "from sentence_transformers import CrossEncoder, SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5'); CrossEncoder('BAAI/bge-reranker-base')"

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

EXPOSE 8000

CMD ["sh", "-c", "python -m backend.prepare_runtime_storage && exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

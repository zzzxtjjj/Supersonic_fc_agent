# Deployment V1

## Local acceptance

Use Python 3.11 from the project root:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

The local URLs are:

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/health`

Run the offline acceptance checks with:

```powershell
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
python -m scripts.validate_chunks
python -m scripts.validate_season_data --season 25-26
python -m scripts.validate_season_data --season 26-27
python -m pytest
cd frontend
npm run build
```

## Production architecture

Deployment V1 uses one Docker service and one persistent volume:

```text
Browser (HTTPS)
  -> FastAPI + compiled React frontend (one origin)
       -> LangGraph Agent
            -> OpenAI-compatible LLM provider (Qwen Flash by default)
            -> local BGE embedding and reranker models
       -> persistent season/media JSON and uploaded images
```

The single-origin layout keeps browser API requests on `/api` and avoids an
unnecessary cross-origin production setup. Run exactly one Uvicorn worker while
JSON files and in-memory administrator sessions are in use.

The Docker build downloads `BAAI/bge-small-zh-v1.5` and
`BAAI/bge-reranker-base` into the image. Runtime sets `HF_HUB_OFFLINE=1` and
`TRANSFORMERS_OFFLINE=1`, so user requests do not download models.

## Required environment variables

Configure these through the platform secret/environment interface. Do not put
their values in Git, the Dockerfile, or frontend `VITE_*` variables.

```text
LLM_API_KEY
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-flash
ADMIN_USERNAME
ADMIN_PASSWORD_HASH
SESSION_SECRET
APP_ENV=production
SERVE_FRONTEND=true
SEASON_DATA_ROOT=/app/persistent/seasons
MEDIA_DATA_ROOT=/app/persistent/media
MEDIA_UPLOAD_ROOT=/app/persistent/uploads
```

`LLM_API_KEY` is a backend-only secret. The default URL uses Alibaba Cloud
Bailian's OpenAI-compatible endpoint; changing `LLM_BASE_URL` and `LLM_MODEL`
switches providers without changing the Agent workflow.

`SESSION_SECRET` must contain at least 32 characters. Generate the administrator
password hash and session secret locally with:

```powershell
python -m backend.auth_cli hash-password
python -m backend.auth_cli generate-secret
```

`APP_ENV=production` makes the admin session cookie `Secure`; it is always
`HttpOnly` and `SameSite=Strict`.

`FRONTEND_ORIGIN` can remain empty for the recommended same-origin deployment.
If the frontend is later hosted separately, set it to the one exact HTTPS
origin. Production never defaults to `*`.

## Persistent storage

Mount one persistent volume at `/app/persistent`. At first startup,
`backend.prepare_runtime_storage` copies the versioned season JSON into the
volume, creates an empty media index, and creates the upload directory.

The following paths must remain persistent:

```text
/app/persistent/seasons
/app/persistent/media
/app/persistent/uploads
```

Local user uploads are intentionally excluded from Git and the Docker image.
Existing local media therefore needs an explicit one-time volume migration or
administrator re-upload after the service and volume exist. Until that step,
the production UI uses its normal image fallbacks. Never commit
`backend/static/uploads/` to seed production.

Static RAG data (`data/rag`) and provenance (`data/sources`) remain versioned in
the image. The dense index is already built and is read-only at runtime.

## Railway deployment outline

Railway is the Deployment V1 target because it supports Docker services,
environment secrets, HTTPS domains, and persistent volumes. The measured local
backend uses roughly 1.3 GB working-set memory after both RAG models load, with
higher private-memory reservation, so configure sufficient memory headroom and
monitor the first production requests.

1. Push this repository to a private GitHub repository.
2. Create one Railway project from the GitHub repository and use the root
   `Dockerfile`.
3. Add a volume mounted at `/app/persistent`.
4. Add the required environment variables above.
5. Set the health-check path to `/api/health`.
6. Keep one replica and one Uvicorn worker.
7. Generate a Railway HTTPS domain.
8. Run public page, Agent, admin, and media persistence smoke tests.
9. Migrate existing local media only after confirming the destination volume.

Creating a paid Railway plan or volume requires the owner's approval. Check the
current Railway price and resource limits before creating resources.

## Health and logging

`GET /api/health` returns only `{"status": "ok"}` and does not initialize the
Agent, LLM provider, embedding model, or reranker.

HTTP logging contains method, path, status, and latency. It does not log request
bodies, passwords, cookies, authorization headers, model reasoning, system
prompts, or tool results. Agent failures are logged server-side while the public
API returns a fixed safe error.

## Admin

- Login page: `/admin/login`
- Media page: `/admin/media`
- Login API: `POST /api/admin/login`
- Logout API: `POST /api/admin/logout`
- Session API: `GET /api/admin/me`

All media write endpoints enforce the administrator session in FastAPI. Hiding
the frontend controls is not the authorization boundary.

## Known limitations

- JSON writes are protected only inside one process and are not suitable for
  multiple workers or replicas.
- Administrator sessions are stored in memory and are invalidated by a backend
  restart.
- The local embedding and reranker models increase image size, RAM use, and cold
  start latency.
- The Agent depends on the configured LLM provider's availability and rate limits.
- Chat responses are not streamed.
- PostgreSQL and Redis are not connected yet.
- Evaluation V1 semantic and groundedness coverage remains intentionally
  limited.
- Persistent volume backups and one-time migration of existing local media must
  be configured operationally.

# Backend API

This package defines the future HTTP boundary for the Supersonic FC product. It
contains season-data read APIs and local media upload/storage. Agent chat remains
a placeholder. The backend does **not** import or invoke the existing Agent,
LangGraph workflow, RAG retriever, or a database.

## Run locally

From the project root:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000/docs` for the generated OpenAPI interface.

## Configure the single administrator

Copy the administrator keys from `.env.example` into the project-root `.env`.
Generate values without putting a plaintext password in a tracked file:

```powershell
python -m backend.auth_cli hash-password
python -m backend.auth_cli generate-secret
```

Set `ADMIN_USERNAME`, paste the generated scrypt value into
`ADMIN_PASSWORD_HASH`, and paste the generated secret into `SESSION_SECRET`.
Use `APP_ENV=development` for local HTTP. Production must use HTTPS and
`APP_ENV=production`, which marks the session cookie `Secure`.

The admin cookie is an HttpOnly, SameSite=Strict browser-session cookie backed
by an expiring server-side session. Closing the browser or logging out removes
browser access; restarting the backend invalidates all existing sessions.

Images uploaded at `POST /api/gallery/upload` are stored under
`backend/static/uploads/`; metadata is stored in `data/media/gallery.json`.
The only upload categories are player photos (`player`), team group photos
(`team_group`), and team crests (`team`). Media is organized by season and is
not bound to matches. Player photos and team crests update the selected season's
canonical JSON record.
The existing `frontend/public/supersonic-logo.png` is never overwritten.

All media writes (`POST`, `PATCH`, and `DELETE`) require the administrator
session. Public read endpoints remain open.

Agent chat remains HTTP 501 until its future adapter exists.

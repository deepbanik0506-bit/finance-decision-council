# Deployment Guide

```
Browser ──HTTPS──▶ Vercel (React/Vite static site)
                      │  fetch(VITE_API_BASE_URL + /api/analyze)
                      ▼
                 Render web service (FastAPI, uvicorn)
                      │  backend/council_service.py
                      ▼
                 Existing LangGraph council (src/finance_council)
                      ├──▶ Groq API   (GROQ_API_KEY, server-side only)
                      └──▶ Yahoo Finance via yfinance
```

Deploy the **backend first**: the frontend build needs the backend URL, and the
backend's CORS allow-list needs the frontend URL. The order is:

1. Render backend (with a temporary `ALLOWED_ORIGINS`)
2. Vercel frontend (with `VITE_API_BASE_URL` = Render URL)
3. Update `ALLOWED_ORIGINS` on Render to the Vercel URL

---

## 1. Render (FastAPI backend)

### Option A — Blueprint (uses `render.yaml`)

1. Push the repository to GitHub.
2. Render dashboard → **New → Blueprint** → select the repository.
3. Render reads `render.yaml` and asks for the `sync: false` values:
   - `GROQ_API_KEY`: your Groq key
   - `ALLOWED_ORIGINS`: for now `http://localhost:5173` (replace in step 3)
4. Click **Apply**. Note the service URL, `https://<service-name>.onrender.com`.

### Option B — Manual web service

Render dashboard → **New → Web Service** → connect the repository, then:

| Setting | Value |
|---|---|
| Runtime | Python |
| Root directory | *(leave blank: repository root)* |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"` |
| Health check path | `/health` |

The service must run from the repository root, because `backend/` imports the
existing council as `src.finance_council`.

### Backend environment variables (Render → Environment)

| Variable | Required | Example / default | Notes |
|---|---|---|---|
| `GROQ_API_KEY` | yes | — | Secret. Never put it in Vercel. |
| `GROQ_MODEL` | yes | `openai/gpt-oss-20b` | Model used by all three agents. |
| `ALLOWED_ORIGINS` | yes | `https://<project>.vercel.app` | Comma-separated, exact origins, no trailing slash. |
| `PYTHON_VERSION` | recommended | `3.14` | Version used for local verification. |
| `ALLOWED_ORIGIN_REGEX` | no | `^https://<project>(-[a-z0-9-]+)?\.vercel\.app$` | Only if Vercel preview deployments must call the API. |
| `RATE_LIMIT_PER_MINUTE` | no | `5` | Analyses per client IP per minute. |
| `MAX_CONCURRENT_ANALYSES` | no | `2` | Extra requests get HTTP 503 `server_busy`. |
| `ENABLE_DOCS` | no | `true` | `false` hides `/docs` and `/openapi.json`. |
| `LOG_LEVEL` | no | `INFO` | |

### Verify

```bash
curl https://<service-name>.onrender.com/health
# {"status":"ok",...,"council_configured":true,...}
```

`council_configured: false` means `GROQ_API_KEY` or `GROQ_MODEL` is missing.

Free Render instances sleep when idle, and the first request after that can take
about a minute. The frontend shows "API unreachable" until the health check
succeeds. Click the status pill to check again.

---

## 2. Vercel (React frontend)

1. Vercel dashboard → **Add New → Project** → import the repository.
2. Configure:

| Setting | Value |
|---|---|
| Root directory | `frontend` |
| Framework preset | Vite (auto-detected; also set in `frontend/vercel.json`) |
| Build command | `npm run build` |
| Output directory | `dist` |
| Install command | `npm install` (default) |

3. **Environment variables** (Production, and Preview if you use it):

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://<service-name>.onrender.com` (no trailing slash) |

`VITE_*` variables are compiled into public JavaScript. Only the backend URL goes
here, never a key. If this variable is missing, the production build still
succeeds, but the site shows a "Frontend not configured" error.

4. Deploy and note the URL, `https://<project>.vercel.app`.

Changing `VITE_API_BASE_URL` requires a **redeploy**, because the value is fixed
at build time.

---

## 3. Connect frontend ↔ backend

1. Render → service → Environment → set
   `ALLOWED_ORIGINS=https://<project>.vercel.app` (add custom domains with commas).
2. Save. Render restarts the service.
3. Open the Vercel URL. The header pill should read **API online**.
4. Run one analysis to confirm the path end to end. This uses Groq quota.

### Troubleshooting

| Symptom | Cause |
|---|---|
| Browser console shows a CORS error | `ALLOWED_ORIGINS` does not exactly match the Vercel origin (scheme, no trailing slash). |
| "Frontend not configured" | `VITE_API_BASE_URL` was not set at build time. Set it and redeploy. |
| "Backend not configured" (503) | `GROQ_API_KEY` / `GROQ_MODEL` missing on Render. |
| "Model provider rate limit reached" (429) | Groq quota or rate limit exhausted. Wait, or use a higher tier. |
| First request is very slow | Render free instance waking from sleep. |

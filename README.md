# Herufi — Predictive Analytics for Sports & Business

A full-stack Python web application showcasing predictive models for sports outcomes and business metrics. Built with FastAPI, SQLAlchemy, Jinja2, HTMX, Alpine.js, and Tailwind CSS.

## Prerequisites

- Python 3.11+
- (Optional) Docker & Docker Compose for one-command startup with PostgreSQL

## Local Dev Quickstart

```bash
cd herufi

# 1. Install dependencies
make install

# 2. Copy env file and edit if needed
cp .env.example .env

# 3. Seed the database with sample data
make seed

# 4. Start the dev server
make dev
```

Open http://localhost:8000 in your browser.

**Dev admin credentials:** `admin@herufi.com` / `herufi-dev-2026`

## Create an Admin User

```bash
make admin
# prompts for email and password
```

Or directly:

```bash
python scripts/create_admin.py your@email.com yourpassword
```

## Adding a New Insight

1. Log in at `/admin` with your admin credentials.
2. POST to `/api/admin/insights` with a JSON body matching `InsightPostCreate`:
   - `slug`, `title`, `domain` (sports|business), `tags`, `summary`, `body_markdown`
   - `hero_chart_config` (optional) — Chart.js config JSON rendered as the hero visual
   - `is_published: true` to go live immediately
3. The insight appears on `/insights` and can be linked to from `/`.

## Plugging In a Real ML Model

1. Train your model (scikit-learn, XGBoost, etc.) and save it:
   ```python
   import pickle
   with open("app/ml/artifacts/my-model.pkl", "wb") as f:
       pickle.dump(model, f)
   ```
2. When calling `predict()`, pass `model="my-model"` in the input dict.
3. The interface in `app/ml/interface.py` will auto-load the artifact and call `.predict()`.
4. For custom output shapes, subclass `PredictionResult` or extend `_load_model()`.

## Running Tests

```bash
make test
```

## Linting

```bash
make lint   # check
make format # auto-fix
```

## Docker (web + PostgreSQL)

```bash
make docker-up
```

This starts the FastAPI app on port 8000 and a PostgreSQL 16 instance. Data persists in a named volume `pgdata`.

## Deployment Notes

### Vercel (recommended — via GitHub)

Herufi ships with a `vercel.json` that routes all traffic to the FastAPI app via Vercel's Python runtime. You need a managed PostgreSQL database (Vercel Postgres, Neon, or Supabase).

**Step-by-step:**

```bash
# 1. Push the repo to GitHub
git init && git add . && git commit -m "initial commit"
gh repo create herufi --public --push

# 2. Install the Vercel CLI (optional — you can also use the dashboard)
npm i -g vercel

# 3. Link your project
vercel link

# 4. Add environment variables (or set them in the Vercel dashboard)
vercel env add SECRET_KEY
vercel env add DATABASE_URL      # postgresql+asyncpg://user:pass@host/db?sslmode=require
vercel env add ADMIN_EMAIL
vercel env add APP_ENV           # production

# 5. Deploy
vercel --prod
```

**Important Vercel constraints:**
- Use `postgresql+asyncpg://` (NOT `psycopg2`) — async driver required
- After first deploy, run migrations against your production DB:
  ```bash
  DATABASE_URL=postgresql+asyncpg://... python -c "
  import asyncio
  from alembic.config import Config
  from alembic import command
  cfg = Config('alembic.ini')
  command.upgrade(cfg, 'head')
  "
  ```
- Static files (`/static/`) are served directly by Vercel from `app/static/`
- SQLite is **not** available in production — always use PostgreSQL

### Fly.io

```bash
fly launch --name herufi
fly secrets set DATABASE_URL=postgresql+asyncpg://<url> SECRET_KEY=<random>
fly deploy
```

### Render / Railway

1. Connect your GitHub repo.
2. Set environment variables from `.env.example`.
3. Set build command: `pip install -e .`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Production Checklist

- [ ] Set `APP_ENV=production`
- [ ] Use a strong random `SECRET_KEY` (`python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Point `DATABASE_URL` to managed PostgreSQL (`postgresql+asyncpg://...`)
- [ ] Run `alembic upgrade head` against production DB before first deploy
- [ ] Create admin user: `python scripts/create_admin.py your@email.com yourpassword`
- [ ] Set `ADMIN_EMAIL` for contact form notifications
- [ ] Upload your CV PDF to `app/static/cv.pdf`
- [ ] Replace `TODO(mike):` markers with real content (`grep -r "TODO(mike):" .`)

## CI / CD

GitHub Actions runs on every push to `main` or `develop`:
- `ruff` lint check
- `black` format check
- `mypy` type check
- `pytest` test suite with coverage

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

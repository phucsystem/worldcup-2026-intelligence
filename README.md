# World Cup Intelligence

Daily AI-generated FIFA WC 2026 brief pipeline.

## Architecture

![World Cup 2026 Intelligence — System Architecture](ck_docs/diagrams/architecture.png)

A cron-scheduled **Container Apps Job** runs a **LangGraph** pipeline (`Collector → Analyst → Editor`) at 07:00 Australia/Melbourne. The Collector pulls fixtures/standings from **API-Football** and computes all tables, position deltas, and best-thirds qualification deterministically in `standings_math` (unit-tested); the **DeepSeek** LLM only narrates the pre-computed facts. Results persist to **PostgreSQL**; the article is published only after the Editor succeeds (keep-last-good). A read-only **FastAPI** serves briefs/standings to the **Next.js 16 SSR** dashboard.

> Editable source: [`ck_docs/diagrams/architecture.drawio`](ck_docs/diagrams/architecture.drawio) (open in [draw.io](https://app.diagrams.net)) · also available as [SVG](ck_docs/diagrams/architecture.svg).

## Prerequisites

- Docker + Docker Compose v2+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 20+ / npm

## Dev Loop

### 1. Environment

```bash
cp .env.example .env
# Fill in API_FOOTBALL_KEY and DEEPSEEK_API_KEY
```

### 2. Start Postgres

```bash
docker compose up -d postgres
```

### 3. Run migrations

```bash
cd backend
DATABASE_URL=postgresql+psycopg://wc:wc@localhost:5432/worldcup uv run alembic -c db/alembic.ini upgrade head
```

### 4. Start backend (local)

```bash
cd backend
uv run uvicorn app.main:app --reload
# http://localhost:8000/health
```

### 5. Start frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

### 6. Full stack via Docker Compose (one command)

Runs the entire stack — Postgres, migrations + seed, the API, and the SSR frontend:

```bash
docker compose up --build
```

Service startup is ordered automatically:
`postgres` (healthcheck) → `migrate` (alembic upgrade + seed the 12-group skeleton, then exits) → `backend` (healthcheck) → `frontend`.

Then open:
- Frontend: http://localhost:3000
- API: http://localhost:8000/health · http://localhost:8000/api/standings

The frontend (SSR) reaches the API over the compose network via `API_BASE=http://backend:8000` — no host config needed.

**Optional API keys** (for live data + brief generation): create `.env` at the repo root with `API_FOOTBALL_KEY` and `DEEPSEEK_API_KEY`; compose passes them to the `backend` service. Without them, the site still runs and shows the seeded standings (briefs list stays empty).

**Real data on the free API-Football plan:** season 2026 requires a paid plan; the free plan covers 2021–2023. Set `API_FOOTBALL_SEASON=2022` in `.env` to populate the DB with the real Qatar 2022 World Cup (64 matches, 8 groups), then trigger a collect:

```bash
docker compose exec backend python -m app.data.collect --date $(date +%F)
# or: curl -X POST http://localhost:8000/api/admin/collect
```

The collector pulls group membership from the standings endpoint, counts only group-stage matches toward the tables, and computes all standings deterministically in Python.

**Generate a brief inside the running stack:**

```bash
# Fetches fresh data (collector) AND generates the brief in one step.
docker compose exec backend python -m app.pipeline.run --date 2026-06-19
```

`pipeline.run` (and the scheduled job) runs the collector first, then the brief. If the API key is missing or the fetch fails, it logs a warning and proceeds with whatever data is already in the DB rather than skipping the brief. To backfill data without generating a brief, run the collector alone:

```bash
docker compose exec backend python -m app.data.collect --date 2026-06-19
```

**HTTP triggers (local/dev only — unauthenticated):**

The backend also exposes two POST endpoints to trigger work over HTTP (handy for a local scheduler/webhook). They default to today's date in `BRIEF_TIMEZONE`; pass `?date=YYYY-MM-DD` to override.

```bash
# Collect data only (no LLM cost)
curl -X POST http://localhost:8000/api/admin/collect

# Full pipeline: collect -> generate + publish brief
curl -X POST "http://localhost:8000/api/admin/run-brief?date=2026-06-20"
```

> ⚠️ These endpoints write data and spend API-Football quota + DeepSeek tokens, and have **no authentication**. They are for local/dev use. Do **not** expose them on a public ingress without adding auth.

Reset everything (including the DB volume):

```bash
docker compose down -v
```

## Tests

```bash
cd backend
uv run pytest
```

## Project Structure

```
backend/     FastAPI app, pipeline, data collectors
frontend/    Next.js + Tailwind dashboard
db/          Alembic migrations (inside backend/)
infra/       Azure Bicep IaC
```

---

## Deploy to Azure

**NEVER commit secrets.** All secret values are passed as Bicep `@secure()` parameters or GitHub Actions secrets — never hardcoded.

### Prerequisites

- Azure CLI (`az`) installed and `az login` completed
- An Azure subscription with Contributor access on the target resource group
- An Azure Container Registry (ACR) created in the same subscription
- Docker installed locally for image builds

### Secret / Environment Reference

| Secret / Param | Where set | Description |
|---|---|---|
| `POSTGRES_ADMIN_USER` | Bicep param / GH secret | Postgres admin username |
| `POSTGRES_ADMIN_PASSWORD` | Bicep param / GH secret | Postgres admin password (min 8 chars, mixed case, digit, special) |
| `API_FOOTBALL_KEY` | Bicep param / GH secret | API-Football.com API key |
| `DEEPSEEK_API_KEY` | Bicep param / GH secret | DeepSeek API key |
| `AZURE_CREDENTIALS` | GH secret only | `az ad sp create-for-rbac --sdk-auth` JSON blob |
| `ACR_LOGIN_SERVER` | Bicep param / GH secret | e.g. `myregistry.azurecr.io` |

### Step-by-step Manual Deploy

#### 1. Create resource group and ACR

```bash
az group create --name wc2026-rg --location australiaeast

az acr create \
  --resource-group wc2026-rg \
  --name <YOUR_ACR_NAME> \
  --sku Basic \
  --admin-enabled true
```

#### 2. Build and push images

```bash
ACR=<YOUR_ACR_NAME>.azurecr.io
az acr login --name <YOUR_ACR_NAME>

# API
docker build -f backend/Dockerfile.api -t $ACR/wc2026-api:latest backend/
docker push $ACR/wc2026-api:latest

# Job
docker build -f backend/Dockerfile.job -t $ACR/wc2026-job:latest backend/
docker push $ACR/wc2026-job:latest

# Frontend
docker build -f frontend/Dockerfile -t $ACR/wc2026-frontend:latest frontend/
docker push $ACR/wc2026-frontend:latest
```

#### 3. Provision infrastructure via Bicep

```bash
az deployment group create \
  --resource-group wc2026-rg \
  --template-file infra/main.bicep \
  --parameters \
      envName=prod \
      acrServer=$ACR \
      apiImageTag=$ACR/wc2026-api:latest \
      frontendImageTag=$ACR/wc2026-frontend:latest \
      jobImageTag=$ACR/wc2026-job:latest \
      postgresAdminUser='<ADMIN_USER>' \
      postgresAdminPassword='<ADMIN_PASSWORD>' \
      apiFootballKey='<API_FOOTBALL_KEY>' \
      deepseekApiKey='<DEEPSEEK_API_KEY>'
```

The deployment outputs `apiUrl` and `frontendUrl`.

#### 4. Run database migrations

Get the Postgres FQDN from the deployment output, then:

```bash
DATABASE_URL="postgresql+psycopg://<ADMIN_USER>:<ADMIN_PASSWORD>@<PG_FQDN>/worldcup?sslmode=require"

cd backend
DATABASE_URL=$DATABASE_URL uv run alembic -c db/alembic.ini upgrade head
```

#### 5. Smoke test

```bash
# Verify API health
curl https://<API_FQDN>/health

# Trigger the daily brief job manually in Azure Portal:
# Container Apps Jobs → wc2026-brief-job-prod → Run now
# Wait ~2 minutes, then check the frontend URL for today's brief.

# Or trigger via CLI:
az containerapp job start --name wc2026-brief-job-prod --resource-group wc2026-rg
```

#### 6. Verify end-to-end

1. Job completes (check Execution History in Azure Portal)
2. `GET <API_URL>/api/briefs/latest` returns the new brief
3. Frontend URL shows today's brief on the home page

### Optional CI/CD

`.github/workflows/deploy.yml` is included but **disabled by default** (`if: false` guards).
To enable automatic deploy on push to `main`:

1. Add all secrets from the table above to GitHub → Settings → Secrets → Actions
2. Remove the two `if: false` lines from `deploy.yml`
3. Push to `main`

### DST / Cron Note

The brief job uses two Container Apps Jobs (one per DST offset). See comments in `infra/container-app-job.bicep` for the cron strategy. Deploy two instances — `wc2026-brief-job-aest` (cron `0 21 * * *`) and `wc2026-brief-job-aedt` (cron `0 20 * * *`) — the in-process scheduler guard ensures only one runs the pipeline each day.

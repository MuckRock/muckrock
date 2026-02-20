# FOIA Coach — Local Setup Guide

Get the FOIA Coach API and UI running locally in about 10 minutes.

## Prerequisites

- **Docker Desktop** — install from [docker.com](https://www.docker.com/products/docker-desktop/) and make sure it's running
- **Git** — to clone the repo
- **Seed data tarball** (`foia_coach_seed_data.tar.gz`) — get this from a teammate

## Step 1: Clone the repo

```bash
git clone <repo-url>
cd muckrock
```

## Step 2: Configure the API environment

Create the env files directory and the two config files:

```bash
mkdir -p .envs/.local
```

**`.envs/.local/.foia_coach_postgres`** — copy this as-is:

```bash
POSTGRES_HOST=foia_coach_postgres
POSTGRES_PORT=5432
POSTGRES_DB=foia_coach
POSTGRES_USER=foia_coach_user
POSTGRES_PASSWORD=foia_coach_dev_password_change_in_production
```

**`.envs/.local/.foia_coach_api`** — get the shared OpenAI API key from a teammate and fill it in:

```bash
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_SECRET_KEY=local-dev-secret-key-not-for-production

# OpenAI — get the shared key from a teammate
OPENAI_API_KEY=<paste-shared-key-here>
OPENAI_VECTOR_STORE_NAME=StatePublicRecordsStore
OPENAI_MODEL=gpt-4o-mini
OPENAI_REAL_API_ENABLED=true

# RAG provider (use openai for real queries, mock for zero-cost testing)
RAG_PROVIDER=openai

# Leave these as-is unless you have a reason to change them
GEMINI_API_KEY=unused
GEMINI_REAL_API_ENABLED=false
GEMINI_FILE_SEARCH_STORE_NAME=StatePublicRecordsStore
GEMINI_MODEL=gemini-2.0-flash

BACKEND_API_URL=http://localhost:8001
MUCKROCK_API_URL=http://internal.dev.muckrock.com
MUCKROCK_API_TOKEN=
```

## Step 3: Load the seed data

Get the `foia_coach_seed_data.tar.gz` file from a teammate and place it in the `foia-coach-api/` directory:

```
muckrock/
├── foia-coach-api/
│   ├── foia_coach_seed_data.tar.gz   <-- put it here
│   ├── apps/
│   ├── config/
│   └── ...
└── local.yml
```

Then run the load script:

```bash
./foia-coach-api/scripts/load_seed_data.sh
```

This extracts two directories into `foia-coach-api/` and loads the database:

- **`fixtures/seed_resources.json`** — database records (resource metadata, upload status)
- **`media/foia_coach/`** — the actual resource files (PDFs, Markdown, text)

Both directories, along with the tarball, are gitignored so they won't show up in `git status`.

If you prefer to do it manually:

```bash
cd foia-coach-api
tar xzf foia_coach_seed_data.tar.gz

# Start the database
docker compose -f ../local.yml up -d foia_coach_postgres

# Run migrations and load data
docker compose -f ../local.yml run --rm foia_coach_api python manage.py migrate --noinput
docker compose -f ../local.yml run --rm foia_coach_api python manage.py loaddata /app/fixtures/seed_resources.json
```

## Step 4: Start the services

```bash
docker compose -f local.yml up foia_coach_api foia_coach_ui foia_coach_postgres
```

Wait for the startup logs to settle, then open:

- **UI:** http://localhost:5173
- **API:** http://localhost:8001/api/v1/

## Step 5: Configure the UI

1. Open http://localhost:5173
2. Click the **Settings** icon
3. Verify these settings:
   - **API URL:** `http://localhost:8001`
   - **AI Provider:** OpenAI
   - **Model:** `gpt-4o-mini`
4. Click **Save Settings**
5. Click **Test Connection** — you should see a success message

## Step 6: Try a query

Go back to the main chat and ask:

> What is the FOIA response deadline in Colorado?

You should see an answer with citations and a provider badge showing "openai".

## What's in the seed data?

The seed data tarball contains:

- **`fixtures/seed_resources.json`** — database records for `JurisdictionResource` and `ResourceProviderUpload` models (jurisdiction metadata, file paths, upload status)
- **`media/foia_coach/`** — the actual resource files (PDFs, Markdown, text) referenced by the database records

Since the team shares an OpenAI API key, the OpenAI vector store is already populated with these files. The seed data ensures your local database knows about them so the API can reference them in query responses and citations.

## Using the Mock provider (no API costs)

To develop without making OpenAI API calls:

1. In the UI Settings, change **AI Provider** to "Mock (Testing)"
2. Or set `RAG_PROVIDER=mock` in `.envs/.local/.foia_coach_api` and restart

Mock mode returns instant fake responses — useful for UI development.

## Updating seed data

If resources have been added or changed, the person who made the changes can re-export:

```bash
./foia-coach-api/scripts/export_seed_data.sh
```

This creates a fresh `foia_coach_seed_data.tar.gz` that can be shared with the team.

## Troubleshooting

**"API calls are disabled"**
Check that `OPENAI_REAL_API_ENABLED=true` is set in `.envs/.local/.foia_coach_api` and restart the API: `docker compose -f local.yml restart foia_coach_api`

**"Connection refused" in the UI**
Make sure all three services are running: `docker compose -f local.yml up foia_coach_api foia_coach_ui foia_coach_postgres`

**CORS errors in browser console**
The API allows requests from `http://localhost:5173` by default. If you're using a different port, update `CORS_ALLOWED_ORIGINS` in `foia-coach-api/config/settings/local.py`.

**Database errors after loading fixture**
Run migrations first: `docker compose -f local.yml run --rm foia_coach_api python manage.py migrate --noinput`, then re-load the fixture.

**Empty responses or no citations**
Verify resources are loaded: visit http://localhost:8001/api/v1/resources/ — you should see a list of resources. If empty, re-run the `loaddata` command from Step 3.

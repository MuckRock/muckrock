# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

MuckRock is a Django-based collaborative news platform for FOIA (Freedom of Information Act) requests. The codebase includes a main MuckRock application and a simplified FOIAMachine variant, both running from the same codebase with different branding based on the domain.

**Key Dependencies:**

- Requires [Squarelet](https://github.com/muckrock/squarelet/) for user authentication (OIDC)
- MuckRock containers join Squarelet's docker network
- Install and run Squarelet first before setting up MuckRock

## Development Commands

### Environment Setup

```bash
# Set docker compose file (add to shell profile)
export COMPOSE_FILE=local.yml

# Initialize environment variables
python initialize_dotenvs.py

# Build JavaScript assets
inv npm ci
inv npm "run build"

# Start all services
inv up

# Stop all services
inv down

# Rebuild docker images
inv build
```

### Running Services

```bash
# Django shell with shell_plus
inv shell

# Bash shell in Django container
inv sh

# PostgreSQL shell
inv dbshell

# Run Django management command
inv manage <command>
inv manage migrate

# Run in foreground with debugger support
inv runserver

# Run celery worker in foreground
inv celeryworker

# Run celery beat scheduler
inv celerybeat
```

### Frontend Development

```bash
# Build JavaScript/CSS once
inv npm "run build"

# Lint JavaScript
inv npm "run lint"

# Run JavaScript tests (vitest, muckrock/assets/js/**/*.test.js)
inv npm "run test"
```

### Testing

```bash
# Run all tests
inv test

# Run specific test path (quote several, space-separated)
inv test --path muckrock/foia/tests/test_models.py
inv test --path "muckrock/foia/tests/ muckrock/task/tests/"

# Run with test database creation (slow)
inv test --create-db

# Run with ipdb debugger on failures
inv test --ipdb

# Generate coverage report
inv coverage
```

### Code Quality

```bash
# Format code (black + isort)
inv format

# Check formatting without changes
inv format-check

# Run pylint
inv pylint
```

### Dependency Management

```bash
# Update requirements.txt from .in files
inv pip-compile

# Upgrade all dependencies
inv pip-compile --upgrade

# Upgrade specific package
inv pip-compile --package <package-name>

# After updating requirements
inv build
```

### Search Index

```bash
# Rebuild full search index (watson)
inv manage buildwatson

# Update specific model index
inv manage buildwatson foia.FOIALogEntry
```

## Architecture

### Django Apps Structure

**Core Request Management:**

- `foia` - Core FOIA request models, communications, file management, status tracking
- `communication` - Generic communication backends (Email, Fax, Mail, Portal)
- `portal` - Integration with agency portals (FOIAonline, GovQA, NextRequest, etc.)
- `task` - Internal staff workflow tasks (18+ task types)

**Government Data:**

- `agency` - FOIA agencies with contact info, fee rates, portal associations
- `jurisdiction` - States/localities, exemptions, laws, response time calculations
- `business_days` - Holiday calendars and deadline tracking

**User & Organization:**

- `accounts` - User profiles, subscriptions, statistics (integrates with Squarelet)
- `organization` - Team accounts with shared request quotas
- `squarelet` - OIDC authentication backend

**Content & Features:**

- `news` - Articles, photos, author management
- `project` - Collaborative FOIA projects
- `crowdfund` - Fundraising campaigns for requests
- `crowdsource` - Community contribution assignments
- `qanda` - Question/answer functionality

**Infrastructure:**

- `core` - Site-wide utilities, middleware, storage backends, Celery config
- `message` - Digest notifications (hourly, daily, weekly, monthly)
- `mailgun` - Email integration
- `fine_uploader` - Document upload handling
- `foiamachine` - FOIA Machine branded version
- `gloo` - AI-powered request analysis (git submodule, excluded from tests)

### Key Patterns

**QuerySet Managers:**
Most major models have custom QuerySet managers with `get_queryset()` methods for complex filtering and optimization. Use `.select_related()` and `.prefetch_related()` extensively to prevent N+1 queries.

**API Versioning:**

- API v1: Original REST API under `api/` viewsets (maintained for compatibility)
- API v2: Newer API under each app's `api_v2/` subdirectory
- Both use Django Rest Framework with Token + Session authentication

**Permissions:**

- Object-level permissions via `django-rules`
- Rules defined in each app's `rules.py`
- Check permissions with `request.user.has_perm('foia.view_foiarequest', foia)`

**Model History:**

- `django-reversion` for version control
- `django-simple-history` for automatic change tracking
- Use `@reversion.create_revision()` decorator for tracking changes

**Celery Tasks:**

- Background jobs run via Celery with Redis broker
- Fax tasks route to dedicated "phaxio" queue
- 20+ scheduled periodic tasks via Celery Beat
- Tasks auto-discovered from `tasks.py` in each app

### Frontend Architecture

**Build System:**

- Vite for bundling (config in `vite.config.js`), loaded into templates by `django-vite`
- Entry points: main, foiamachine, docViewer, getHelp, reviewAgency, print
- Source in `muckrock/assets/js/`, `muckrock/assets/scss/`, and Svelte components in `muckrock/assets/components/`
- `inv up` starts the `muckrock_vite` container running the dev server on port 4201; with `DEBUG` on, Django serves assets from it, so no rebuild is needed while it runs
- Tests and production read the built manifest at `muckrock/assets/dist/manifest.json`; run `inv npm "run build"` before tests that render templates
**JavaScript Stack:**

- New code: Svelte 5 components and TypeScript (`getHelp.ts`, `reviewAgency.ts`)
- Legacy: React 15 with Redux, jQuery 3.6.4 (exposed globally, heavily used throughout), jQuery UI 1.10.x

**Key Modules:**

- `foiaCreate.js` - FOIA request creation UI
- `foiaRequest.js` - Request detail page
- `task.js` - Staff task management
- `crowdsource.js` - Crowdsourced assignments

### External Integrations

**Required Services:**

- **Squarelet** - User authentication (OIDC), set `SQUARELET_KEY`, `SQUARELET_SECRET`, `JWT_VERIFYING_KEY` in `.envs/.local/.django`
- **PostgreSQL** - Primary database (version 15)
- **Redis** - Celery broker and cache backend

**Optional Services (use "test" values for local dev):**

- **DocumentCloud** - Document hosting and embedding
- **Mailgun** - Email delivery with webhook callbacks
- **Phaxio** - Fax delivery
- **Lob** - Physical mail printing
- **Stripe** - Payment processing and subscriptions
- **AWS S3** - File storage (media, static assets)
- **OpenAI** - AI features (set `OPENAI_API_KEY="test"` for local)

### Multi-Domain Setup

The application serves two brands from the same codebase:

- `dev.muckrock.com` - Full-featured MuckRock platform
- `dev.foiamachine.org` - Simplified FOIA filing tool (manual workflow)

Add both to `/etc/hosts`:

```bash
echo "127.0.0.1   dev.muckrock.com" | sudo tee -a /etc/hosts
echo "127.0.0.1   dev.foiamachine.org" | sudo tee -a /etc/hosts
```

## Important Notes

**Settings Files:**

- `base.py` - Common configuration
- `local.py` - Development environment
- `test.py` - Test environment
- `heroku.py` - Shared Heroku config, extended by `staging.py` / `production.py`

**Database Migrations:**
After model changes, create migrations inside the Django container:

```bash
inv manage makemigrations
inv manage migrate
```

**Storage Configuration:**

- Development uses local storage (muckrock/static/media/)
- Production uses S3 with CloudFront CDN
- Custom storage backends in `muckrock/core/storage.py`

**Testing:**

- Tests use pytest with pytest-django
- Test settings: `muckrock.settings.test`
- Gloo app excluded from tests (it's a git submodule)
- Test files: `test_*.py` or `tests.py`

**Celery Scheduled Tasks:**
Major periodic tasks include:

- `followup_requests` - Auto-send FOIA followups (daily 1 AM)
- `autoimport` - Import scanned documents (daily 2 AM, 10 hour timeout)
- `store_statistics` - Aggregate stats (daily 7:30 AM)
- Digest tasks: hourly, daily (10 AM), weekly (Mon 10 AM), monthly (1st, 10 AM)

**Search:**
Full-text search via `django-watson`. After registering new models, rebuild the index with `inv manage buildwatson`.

**Code Formatting:**

- Use `black` for Python formatting (excludes migrations, vendor, gloo)
- Use `isort` for import sorting (skip gloo submodule)
- Run `inv format` before committing

**Git Submodules:**
The `muckrock/gloo` directory is a git submodule. If you cloned without `--recurse-submodules`, initialize it:

```bash
cd muckrock/gloo
git submodule init
git submodule update
```

<!-- CLAUDE.md shared standard v1 — canonical copy: squarelet/CLAUDE.md -->

## Code comments

Comments say **why**, not what. If the code already says it, delete the comment.

- **One or two short sentences.** If it needs a paragraph, it belongs in a
  doc comment, the PR description, or a doc under `docs/`.
- **Keep the consequence, drop the lead-in.** The clause naming what the
  code does is the half to cut; the clause saying what breaks otherwise is
  the half worth keeping.
- **Never describe code that is not there.** No "this used to...", no
  narrating the change, no explaining why something was removed. `git log`
  and the PR hold that.
- **No reasoning out loud.** Don't walk through scenarios, anticipate
  objections, or record the thought process behind a choice.
- **Do comment the surprising**: a constraint an external system imposes,
  an ordering requirement, a failure that cannot be seen locally. That is
  what a reader cannot get from the code.

```typescript
// Good - a constraint you cannot see from here
// The API rejects a redaction whose page range crosses a document split.

// Bad - narrates the change
// `currentPage` is now derived from the store instead of a prop, so
// this component no longer needs to read it from context.
```

## Docstrings / doc comments

One line on what it does. Add more only for a contract a caller needs: what it rejects/throws, what it returns in the edge case, ordering it requires, side effects it has, a cost worth avoiding.

Two tests before you keep a second paragraph:

- Does it restate the first line in more words? Delete it.
- Would a caller behave differently for knowing it? Keep it, in one or two sentences.

```typescript
// Good - the whole contract, one line
/** Does the document still have pages pending OCR? */

// Good - a second paragraph a caller acts on
/**
 * The document's current processing status, or "error" if any page failed.
 *
 * Read from the cached store value; the document list renders one row
 * per document and cannot afford an API call each.
 */
```

## Pull request descriptions

Open with one sentence on what changes. Then:

- **Behaviour changes** — name them, or say "none".
- **Migrations** — what they do, whether they reverse.
- **What to check** — the QA steps, as a checklist.

Bullets, not prose. Don't recount how the change came about or what was tried first.

## Tests

Name the behaviour, not the mechanism: `renders the error state when OCR fails`, not `test handle error`. A test whose assertion would pass against the unfixed code is not a test.

<!-- /CLAUDE.md shared standard -->

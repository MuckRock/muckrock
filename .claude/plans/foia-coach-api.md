# FOIA Coach Standalone API Service - Implementation Plan

## Progress Tracker

**Last Updated:** 2025-12-09

| Phase | Status | Completed | Notes |
|-------|--------|-----------|-------|
| Phase 0: Rollback Phase 1 & 2 | ✅ Complete | 2025-12-09 | All code backed up, migration rolled back, main app clean |
| Phase 1: Django Scaffold | ⏳ Pending | - | Next phase |
| Phase 2: Docker Configuration | ⏳ Pending | - | |
| Phase 3: Models & API Client | ⏳ Pending | - | |
| Phase 4a: Gemini Service & Signals | ⏳ Pending | - | |
| Phase 4b: Management Commands & Tests | ⏳ Pending | - | |
| Phase 5: REST API Endpoints | ⏳ Pending | - | |
| Phase 6: Integration & Documentation | ⏳ Pending | - | |

---

## Executive Summary

Create a standalone Django API service to resolve dependency conflicts while preserving completed Phase 1 & 2 work. The service will run in its own Docker container, share the PostgreSQL database with the main MuckRock app, and expose REST APIs for the SvelteKit UI.

## Problem Statement

**Dependency Conflict:**
- `google-genai >= 1.49.0` requires `httpx >= 0.28.1`
- `ollama` (required by `baml` for Gloo) requires `httpx < 0.28.0`
- Cannot use latest google-genai features in main MuckRock app

**Solution:**
Standalone service with independent dependencies, sharing only the PostgreSQL database.

---

## Architecture Overview

### Service Topology

```
┌─────────────────────────────────┐
│   Main MuckRock Django App      │
│   Port: 8000                    │
│   - baml/ollama/httpx<0.28      │
│   - Full MuckRock features      │
│   - Owns: jurisdiction table    │
└────────────┬────────────────────┘
             │
             ├─── PostgreSQL (shared) ───┐
             │                           │
┌────────────▼────────────────────┐     │
│   FOIA Coach API Service        │     │
│   Port: 8001                    │     │
│   - google-genai>=1.49/httpx>=0.28   │
│   - Minimal Django              │     │
│   - Owns: resource tables       │◄────┘
│   - Read-only: jurisdiction     │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   SvelteKit UI (Phase 4)        │
│   Port: 5173                    │
│   - Consumes FOIA Coach API     │
└─────────────────────────────────┘
```

### Database Strategy

**Phase 1 (Initial Development):**
- FOIA Coach API shares PostgreSQL container with main app (for speed of iteration)
- Owns new tables: `foia_coach_jurisdictionresource`
- Accesses Jurisdiction data via main MuckRock API (no direct DB access to jurisdiction table)

**Phase 2 (Flexible Deployment):**
- FOIA Coach API can point to different MuckRock API endpoints:
  - Local dev: `http://muckrock_django/api/...` (in Docker network)
  - Remote dev: `https://dev.muckrock.com/api/...`
  - Production: `https://muckrock.com/api/...`
- Configured via `MUCKROCK_API_URL` and `MUCKROCK_API_TOKEN` environment variables
- Enables sharing with collaborators without local database assumptions

**Table Naming Convention:**
- Prefix: `foia_coach_*` for clarity and separation
- Only creates tables for resources it owns directly

---

## Project Structure

```
muckrock/
├── local.yml                           # Updated: Add foia_coach_api service
├── foia-coach-api/                     # NEW: Standalone service root
│   ├── manage.py                       # Django management
│   ├── requirements.in                 # Minimal dependencies
│   ├── requirements.txt                # Compiled requirements
│   ├── pytest.ini                      # Test configuration
│   ├── .env.example                    # Environment template
│   ├── compose/
│   │   └── local/
│   │       ├── Dockerfile              # Service container
│   │       ├── entrypoint              # Database readiness check
│   │       └── start                   # Django startup script
│   ├── config/                         # Django project config
│   │   ├── __init__.py
│   │   ├── urls.py                     # Root URL configuration
│   │   ├── wsgi.py                     # WSGI entry point
│   │   └── settings/
│   │       ├── __init__.py
│   │       ├── base.py                 # Core settings
│   │       ├── local.py                # Local dev settings
│   │       └── test.py                 # Test settings
│   └── apps/                           # Django applications
│       ├── __init__.py
│       ├── jurisdiction/               # Adapted from Phase 1 & 2
│       │   ├── __init__.py
│       │   ├── apps.py
│       │   ├── models.py               # JurisdictionResource + read-only Jurisdiction
│       │   ├── admin.py                # Django admin
│       │   ├── signals.py              # Auto-upload handlers
│       │   ├── factories.py            # Test factories
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   └── gemini_service.py   # Gemini File Search integration
│       │   ├── management/
│       │   │   └── commands/
│       │   │       ├── gemini_create_store.py
│       │   │       ├── gemini_upload_resource.py
│       │   │       ├── gemini_sync_all.py
│       │   │       └── gemini_query.py
│       │   └── tests/
│       │       ├── __init__.py
│       │       ├── conftest.py
│       │       └── test_gemini_service.py
│       └── api/                        # REST API (Phase 3)
│           ├── __init__.py
│           ├── apps.py
│           ├── urls.py                 # API routes
│           ├── serializers.py          # DRF serializers
│           ├── viewsets.py             # DRF viewsets
│           ├── permissions.py          # Custom permissions
│           └── tests/
│               ├── __init__.py
│               └── test_api.py
└── muckrock/                           # Existing app (UNCHANGED)
    └── jurisdiction/
        └── models.py                   # Jurisdiction (owned by main app)
```

---

## Implementation Phases

Each phase is designed to:
- **Complete in 30 minutes to 1 hour** (smaller phases for more checkpoints)
- Fit within single Claude Code session
- Result in a working, committable state
- Be independently testable
- Minimal testing scope (support development progress only)

**Note:** Authentication is deferred until after SvelteKit UI is built. No security requirements for experimental phase.

---

### Phase 0: Rollback Phase 1 & 2 Migrations (15-30 minutes)

**Goal:** Clean up the Phase 1 & 2 work from main MuckRock app to prepare for standalone service.

#### Background

During Phase 1 & 2 development, we added:
- Migration `0032_geminifilesearchstore_jurisdictionresource.py`
- `JurisdictionResource` and `GeminiFileSearchStore` models to main app
- Signal handlers, management commands, service layer

These need to be removed from the main app before creating the standalone service.

#### Tasks

1. **Rollback migration in main app**
   ```bash
   docker compose -f local.yml run --rm muckrock_django \
     python manage.py migrate jurisdiction 0031
   ```

2. **Delete migration file**
   ```bash
   rm muckrock/jurisdiction/migrations/0032_geminifilesearchstore_jurisdictionresource.py
   ```

3. **Remove code from main app** (delete safely - available in git history):
   - Copy `muckrock/jurisdiction/services/gemini_service.py` → `/tmp/gemini_service.py.backup`
   - Copy management commands to `/tmp/` for reference during migration
   - Copy test file → `/tmp/test_gemini_service.py.backup`
   - Delete all Phase 1 & 2 code from main app (services/, management commands, signal handlers)
   - **Rationale:** Keep main service clean and production-ready; git history preserves all code

4. **Remove models from jurisdiction/models.py**
   - Remove `JurisdictionResource` class
   - Remove `GeminiFileSearchStore` class

5. **Verify main app still works**
   ```bash
   docker compose -f local.yml run --rm muckrock_django python manage.py check
   docker compose -f local.yml up muckrock_django
   # Visit http://localhost:8000/admin/ to verify
   ```

6. **Commit cleanup**
   ```bash
   git add -A
   git commit -m "refactor(foia-coach): Rollback Phase 1&2 from main app, prepare for standalone service"
   ```

#### Deliverables

- [x] Migration 0032 rolled back
- [x] Migration file deleted
- [x] Code backed up to /tmp/
- [x] Models removed from main app
- [x] Main app still functional
- [x] Changes committed

**Status: ✅ COMPLETED (2025-12-09)**

**Notes:**
- All Phase 1 & 2 code successfully backed up to `/tmp/` (6 files total)
- Migration rolled back cleanly to 0031
- Removed `JurisdictionResource` and `GeminiFileSearchStore` models from main app
- Deleted entire `services/` directory, `signals.py`, all Gemini management commands, and test file
- Updated `admin.py` to remove Gemini admin classes
- Updated `apps.py` to remove signal import
- Main app passes Django checks (0 errors, 2 pre-existing warnings)
- All changes committed to git

#### Success Criteria

```bash
# Migration rolled back
docker compose -f local.yml run --rm muckrock_django python manage.py showmigrations jurisdiction | tail -1
# Output: [X] 0031_alter_jurisdiction_always_proxy_and_more

# App check passes
docker compose -f local.yml run --rm muckrock_django python manage.py check
# Output: System check identified no issues

# Code backed up
ls /tmp/ | grep gemini
# Output: gemini_service.py.backup, test_gemini_service.py.backup
```

---

### Phase 1: Minimal Django Project Scaffold (30-60 minutes)

**Goal:** Create a minimal Django project structure with proper configuration.

**Note:** This creates the foundation only - no models or Docker yet. Small phase for easy checkpoint.

#### Tasks

1. **Create project directory structure**
   - `foia-coach-api/` root directory
   - `config/` for project settings
   - `config/settings/` with base.py, local.py, test.py
   - `apps/` for applications
   - Root files: manage.py, requirements.in, pytest.ini

2. **Configure minimal requirements.in**
   ```
   # Core Django
   django==4.2.*
   psycopg2-binary

   # Google Gemini (latest without conflicts!)
   google-genai>=1.49.0

   # Django REST Framework
   djangorestframework
   django-filter
   django-cors-headers

   # Testing
   pytest
   pytest-django
   pytest-mock
   factory-boy

   # Utilities
   python-dotenv
   ```

3. **Create base settings** (config/settings/base.py)
   - Minimal INSTALLED_APPS (django.contrib core + apps.jurisdiction + apps.api)
   - DATABASE configuration from environment variable
   - GEMINI_API_KEY from environment
   - REST_FRAMEWORK basic config
   - CORS configuration for local dev

4. **Create local.py settings**
   - DEBUG = True
   - ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'foia_coach_api']
   - CORS_ALLOWED_ORIGINS for SvelteKit

5. **Create test.py settings**
   - Override for test database
   - Disable signal handlers for controlled testing

6. **Create manage.py**
   - Standard Django management entry point
   - Set default settings module to 'config.settings.local'

7. **Create root URLs** (config/urls.py)
   - Admin (optional, for debugging)
   - API v1 routes (placeholder for Phase 3)

#### Deliverables

- [ ] Project structure created
- [ ] requirements.in defined
- [ ] Settings files configured
- [ ] manage.py working
- [ ] Can run: `python manage.py check` (passes with no apps warning)

#### Success Criteria

```bash
cd foia-coach-api
python manage.py check
# Output: System check identified no issues (0 silenced).
```

---

### Phase 2: Docker Configuration (30-60 minutes)

**Goal:** Create Docker container for FOIA Coach API and integrate with docker-compose.

**Note:** Just Docker setup - no models or code yet. Verify container starts successfully.

#### Tasks

1. **Create Dockerfile** (compose/local/Dockerfile)
   ```dockerfile
   FROM python:3.11-slim

   ENV PYTHONUNBUFFERED=1 \
       PYTHONDONTWRITEBYTECODE=1

   RUN apt-get update && apt-get install -y \
       postgresql-client \
       && rm -rf /var/lib/apt/lists/*

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY ./compose/local/entrypoint /entrypoint
   RUN chmod +x /entrypoint

   COPY ./compose/local/start /start
   RUN chmod +x /start

   COPY . /app

   ENTRYPOINT ["/entrypoint"]
   CMD ["/start"]
   ```

2. **Create entrypoint script** (compose/local/entrypoint)
   - PostgreSQL readiness check
   - Environment variable validation
   - Execute passed command

3. **Create start script** (compose/local/start)
   ```bash
   #!/bin/bash
   set -e

   python manage.py migrate --noinput
   python manage.py runserver 0.0.0.0:8000
   ```

4. **Update local.yml** - Add new service
   ```yaml
   foia_coach_api:
     build:
       context: ./foia-coach-api
       dockerfile: ./compose/local/Dockerfile
     image: muckrock_foia_coach_api_local
     container_name: foia_coach_api_local
     depends_on:
       - muckrock_postgres
     volumes:
       - ./foia-coach-api:/app:z
     env_file:
       - ./.envs/.local/.postgres
       - ./.envs/.local/.foia_coach_api
     ports:
       - "8001:8000"
     command: /start
     networks:
       - default
   ```

5. **Create environment file** (.envs/.local/.foia_coach_api)
   ```bash
   DJANGO_SETTINGS_MODULE=config.settings.local
   GEMINI_API_KEY=your_key_here
   GEMINI_FILE_SEARCH_STORE_NAME=StatePublicRecordsStore
   ```

6. **Add .env.example** to foia-coach-api/
   - Template for required environment variables

7. **Test Docker build and startup**
   ```bash
   docker-compose -f local.yml build foia_coach_api
   docker-compose -f local.yml up foia_coach_api
   ```

#### Deliverables

- [ ] Dockerfile created
- [ ] Entrypoint script created
- [ ] Start script created
- [ ] local.yml updated
- [ ] Environment file created
- [ ] Container builds successfully
- [ ] Container starts and runs migrate

#### Success Criteria

```bash
docker-compose -f local.yml up foia_coach_api
# Output: Django development server running at http://0.0.0.0:8000/
# Accessible at: http://localhost:8001/
```

---

### Phase 3: Models & MuckRock API Client (45-60 minutes)

**Goal:** Create JurisdictionResource model and API client to fetch Jurisdiction data from main MuckRock service.

**Note:** This phase creates both the data model and API integration. No direct database access to jurisdiction table.

#### Tasks

1. **Create apps/jurisdiction app structure**
   ```bash
   mkdir -p apps/jurisdiction/services
   mkdir -p apps/jurisdiction/management/commands
   mkdir -p apps/jurisdiction/tests
   touch apps/jurisdiction/{__init__.py,apps.py,models.py,admin.py,signals.py}
   ```

2. **Create MuckRock API client** (apps/jurisdiction/services/muckrock_client.py)
   ```python
   """Client for fetching jurisdiction data from main MuckRock API"""
   import requests
   from django.conf import settings
   from typing import List, Dict, Optional

   class MuckRockAPIClient:
       """
       Client for accessing MuckRock API to fetch jurisdiction data.
       Supports both local Docker and remote API endpoints.
       """
       def __init__(self):
           self.base_url = settings.MUCKROCK_API_URL
           self.token = settings.MUCKROCK_API_TOKEN
           self.session = requests.Session()
           if self.token:
               self.session.headers['Authorization'] = f'Token {self.token}'

       def get_jurisdictions(self, level: str = 's') -> List[Dict]:
           """Fetch state jurisdictions from MuckRock API"""
           response = self.session.get(
               f'{self.base_url}/api/v2/jurisdiction/',
               params={'level': level}
           )
           response.raise_for_status()
           return response.json()['results']

       def get_jurisdiction(self, abbrev: str) -> Optional[Dict]:
           """Fetch single jurisdiction by abbreviation"""
           response = self.session.get(
               f'{self.base_url}/api/v2/jurisdiction/{abbrev}/'
           )
           if response.status_code == 404:
               return None
           response.raise_for_status()
           return response.json()
   ```

3. **Add settings for MuckRock API** (config/settings/base.py)
   ```python
   # MuckRock API Configuration
   MUCKROCK_API_URL = os.environ.get(
       'MUCKROCK_API_URL',
       'http://dev.muckrock.com'  # Default uses /etc/hosts mapping
   )
   MUCKROCK_API_TOKEN = os.environ.get('MUCKROCK_API_TOKEN', '')
   ```

4. **Create models.py** with JurisdictionResource only:
   ```python
   class JurisdictionResource(models.Model):
       """
       Knowledge resource file associated with a jurisdiction.
       Jurisdiction data is fetched from MuckRock API, not stored locally.
       """
       # Store jurisdiction reference as simple fields (no FK)
       jurisdiction_id = models.IntegerField(
           help_text='ID from main MuckRock jurisdiction table'
       )
       jurisdiction_abbrev = models.CharField(
           max_length=5,
           help_text='State abbreviation (e.g., CO, GA, TN)'
       )

       file = models.FileField(
           upload_to='foia_coach/jurisdiction_resources/%Y/%m/',
           help_text='Text or Markdown file with state-specific FOIA knowledge'
       )
       display_name = models.CharField(max_length=255)
       description = models.TextField(blank=True)

       # Gemini integration metadata
       gemini_file_id = models.CharField(max_length=255, blank=True, null=True)
       gemini_display_name = models.CharField(max_length=255, blank=True, null=True)
       indexed_at = models.DateTimeField(blank=True, null=True)
       index_status = models.CharField(
           max_length=20,
           choices=[
               ('pending', 'Pending Upload'),
               ('uploading', 'Uploading'),
               ('indexing', 'Indexing'),
               ('ready', 'Ready'),
               ('error', 'Error')
           ],
           default='pending'
       )

       resource_type = models.CharField(
           max_length=50,
           choices=[
               ('law_guide', 'Law Guide'),
               ('request_tips', 'Request Tips'),
               ('exemptions', 'Exemptions Guide'),
               ('agency_info', 'Agency Information'),
               ('case_law', 'Case Law'),
               ('general', 'General Information')
           ],
           default='general'
       )

       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)
       is_active = models.BooleanField(default=True)
       order = models.PositiveIntegerField(default=0)

       class Meta:
           db_table = 'foia_coach_jurisdictionresource'
           ordering = ['jurisdiction_abbrev', 'order', 'display_name']
           indexes = [
               models.Index(fields=['jurisdiction_abbrev']),
               models.Index(fields=['jurisdiction_id']),
           ]

       def __str__(self):
           return f"{self.jurisdiction_abbrev} - {self.display_name}"

       @property
       def jurisdiction(self):
           """Fetch full jurisdiction data from MuckRock API"""
           from .services.muckrock_client import MuckRockAPIClient
           client = MuckRockAPIClient()
           return client.get_jurisdiction(self.jurisdiction_abbrev)
   ```

5. **Update requirements.in** - Add requests library
   ```
   requests>=2.31.0
   ```

6. **Create admin.py** - Admin with jurisdiction lookup
   ```python
   from django.contrib import admin
   from .models import JurisdictionResource
   from .services.muckrock_client import MuckRockAPIClient

   @admin.register(JurisdictionResource)
   class JurisdictionResourceAdmin(admin.ModelAdmin):
       list_display = ['display_name', 'jurisdiction_abbrev', 'resource_type', 'index_status', 'created_at']
       list_filter = ['resource_type', 'index_status', 'is_active']
       search_fields = ['display_name', 'jurisdiction_abbrev']

       def formfield_for_dbfield(self, db_field, request, **kwargs):
           # Could add jurisdiction choices from API here
           return super().formfield_for_dbfield(db_field, request, **kwargs)
   ```

7. **Generate and run migrations**
   ```bash
   docker compose -f local.yml run --rm foia_coach_api python manage.py makemigrations
   docker compose -f local.yml run --rm foia_coach_api python manage.py migrate
   ```

8. **Test API client**
   ```bash
   docker compose -f local.yml run --rm foia_coach_api python manage.py shell
   >>> from apps.jurisdiction.services.muckrock_client import MuckRockAPIClient
   >>> client = MuckRockAPIClient()
   >>> jurisdictions = client.get_jurisdictions(level='s')
   >>> len(jurisdictions)
   # Should return number of state jurisdictions
   ```

#### Deliverables

- [ ] MuckRock API client created
- [ ] JurisdictionResource model created (no FK to jurisdiction)
- [ ] Admin interface configured
- [ ] Migrations generated and applied
- [ ] Can fetch jurisdictions from MuckRock API
- [ ] Can create JurisdictionResource with jurisdiction reference

#### Success Criteria

```bash
# Can fetch jurisdictions from MuckRock API
docker compose -f local.yml run --rm foia_coach_api python manage.py shell
>>> from apps.jurisdiction.services.muckrock_client import MuckRockAPIClient
>>> client = MuckRockAPIClient()
>>> jurisdictions = client.get_jurisdictions(level='s')
>>> len(jurisdictions) > 0
# Returns: True

# Can create resource
>>> from apps.jurisdiction.models import JurisdictionResource
>>> jr = JurisdictionResource(jurisdiction_id=1, jurisdiction_abbrev='CO', display_name='Test')
>>> jr.save()
# Success

# Property fetches jurisdiction data
>>> jr.jurisdiction
# Returns: {'id': 1, 'name': 'Colorado', 'abbrev': 'CO', ...}
```

---

### Phase 4a: Migrate Gemini Service & Signals (45-60 minutes)

**Goal:** Copy and adapt GeminiFileSearchService and signal handlers.

**Note:** Split into smaller phases. This phase just gets the core service working.

#### Tasks

1. **Copy GeminiFileSearchService**
   - Source: `/tmp/gemini_service.py.backup` (from Phase 0)
   - Destination: `foia-coach-api/apps/jurisdiction/services/gemini_service.py`
   - Adaptations needed:
     - Change settings import: `from django.conf import settings` → works as-is
     - Update model imports to local models
     - Remove GeminiFileSearchStore model dependency (simplify)

2. **Adapt signal handlers**
   - Create new `foia-coach-api/apps/jurisdiction/signals.py`
   - Copy signal logic from Phase 2 work
   - Keep `transaction.on_commit()` pattern
   - Update imports for new project structure

3. **Configure signal registration** (apps/jurisdiction/apps.py)
   ```python
   class JurisdictionConfig(AppConfig):
       default_auto_field = 'django.db.models.BigAutoField'
       name = 'apps.jurisdiction'

       def ready(self):
           import apps.jurisdiction.signals  # noqa
   ```

4. **Test service integration**
   - Create simple test resource
   - Verify signal fires
   - Verify service uploads to Gemini

#### Deliverables

- [ ] GeminiFileSearchService copied and adapted
- [ ] Signal handlers working
- [ ] Service can upload to Gemini

#### Success Criteria

```bash
# Service available
docker compose -f local.yml run --rm foia_coach_api python manage.py shell
>>> from apps.jurisdiction.services.gemini_service import GeminiFileSearchService
>>> service = GeminiFileSearchService()
>>> service.get_or_create_store()
# Success - no errors

# Can create resource and signal fires
>>> from apps.jurisdiction.models import JurisdictionResource, Jurisdiction
>>> j = Jurisdiction.objects.filter(level='s').first()
>>> r = JurisdictionResource.objects.create(jurisdiction=j, display_name="Test", ...)
>>> r.index_status
# Output: 'ready' or 'uploading' (signal fired)
```

---

### Phase 4b: Management Commands & Tests (45-60 minutes)

**Goal:** Add management commands and test suite.

**Note:** Separate phase for testing infrastructure. Keeps Phase 4a focused on core functionality.

#### Tasks

1. **Copy management commands**
   - Copy all 4 commands from `/tmp/` backups
   - Adapt imports for new project structure
   - Test each command works in new container

2. **Create factories.py** for testing
   - Adapt JurisdictionResourceFactory
   - Adapt JurisdictionFactory (read-only, for tests only)

3. **Copy and adapt test suite**
   - Source: `/tmp/test_gemini_service.py.backup`
   - Destination: `foia-coach-api/apps/jurisdiction/tests/test_gemini_service.py`
   - Create conftest.py for pytest fixtures
   - Update imports for new structure
   - Ensure signal disconnection in setUp

4. **Run tests to verify migration**
   ```bash
   docker compose -f local.yml run --rm foia_coach_api pytest
   ```

#### Deliverables

- [ ] All 4 management commands working
- [ ] Test suite adapted
- [ ] Most tests passing (minimal fixes only)
- [ ] Factories created for test data

#### Success Criteria

```bash
# Management commands work
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_create_store
# Output: Store created successfully

# Tests run (don't need all passing, just running)
docker compose -f local.yml run --rm foia_coach_api pytest
# Output: Test suite runs, most tests passing
```

---

---

### Phase 5: REST API Endpoints (45-60 minutes)

**Goal:** Create Django REST Framework API endpoints for SvelteKit UI consumption.

**Note:** No authentication required (deferred until after SvelteKit UI). Focus on functional endpoints only.

#### Tasks

1. **Create apps/api app structure**
   ```bash
   mkdir -p apps/api/tests
   touch apps/api/{__init__.py,apps.py,urls.py,serializers.py,viewsets.py,permissions.py}
   ```

2. **Create serializers** (apps/api/serializers.py)

   **JurisdictionSerializer (read-only):**
   ```python
   class JurisdictionSerializer(serializers.ModelSerializer):
       resource_count = serializers.SerializerMethodField()

       class Meta:
           model = Jurisdiction
           fields = ['id', 'name', 'slug', 'abbrev', 'level', 'resource_count']

       def get_resource_count(self, obj):
           return obj.foia_coach_resources.filter(is_active=True).count()
   ```

   **JurisdictionResourceSerializer:**
   ```python
   class JurisdictionResourceSerializer(serializers.ModelSerializer):
       jurisdiction_name = serializers.CharField(source='jurisdiction.name', read_only=True)
       jurisdiction_abbrev = serializers.CharField(source='jurisdiction.abbrev', read_only=True)

       class Meta:
           model = JurisdictionResource
           fields = [
               'id', 'jurisdiction', 'jurisdiction_name', 'jurisdiction_abbrev',
               'display_name', 'description', 'resource_type', 'index_status',
               'indexed_at', 'is_active', 'created_at'
           ]
           read_only_fields = ['index_status', 'indexed_at']
   ```

   **QueryRequestSerializer & QueryResponseSerializer:**
   ```python
   class QueryRequestSerializer(serializers.Serializer):
       question = serializers.CharField(required=True)
       state = serializers.CharField(required=False, allow_blank=True)
       context = serializers.JSONField(required=False)

   class QueryResponseSerializer(serializers.Serializer):
       answer = serializers.CharField()
       citations = serializers.ListField(child=serializers.DictField())
       state = serializers.CharField(required=False, allow_null=True)
   ```

3. **Create viewsets** (apps/api/viewsets.py)

   **JurisdictionViewSet (read-only):**
   ```python
   class JurisdictionViewSet(viewsets.ReadOnlyModelViewSet):
       queryset = Jurisdiction.objects.filter(level='s').order_by('name')
       serializer_class = JurisdictionSerializer
       lookup_field = 'abbrev'
   ```

   **JurisdictionResourceViewSet (read-only for now):**
   ```python
   class JurisdictionResourceViewSet(viewsets.ReadOnlyModelViewSet):
       queryset = JurisdictionResource.objects.filter(is_active=True)
       serializer_class = JurisdictionResourceSerializer
       filterset_fields = ['jurisdiction', 'resource_type', 'index_status']
   ```

   **QueryViewSet (custom action):**
   ```python
   class QueryViewSet(viewsets.ViewSet):
       @action(detail=False, methods=['post'])
       def query(self, request):
           serializer = QueryRequestSerializer(data=request.data)
           serializer.is_valid(raise_exception=True)

           service = GeminiFileSearchService()
           result = service.query(
               question=serializer.validated_data['question'],
               state=serializer.validated_data.get('state'),
               context=serializer.validated_data.get('context')
           )

           response_serializer = QueryResponseSerializer(result)
           return Response(response_serializer.data)
   ```

4. **Create API URLs** (apps/api/urls.py)
   ```python
   router = DefaultRouter()
   router.register(r'jurisdictions', JurisdictionViewSet, basename='jurisdiction')
   router.register(r'resources', JurisdictionResourceViewSet, basename='resource')
   router.register(r'query', QueryViewSet, basename='query')

   urlpatterns = [
       path('v1/', include(router.urls)),
   ]
   ```

5. **Update root URLs** (config/urls.py)
   ```python
   urlpatterns = [
       path('admin/', admin.site.urls),
       path('api/', include('apps.api.urls')),
   ]
   ```

6. **Configure CORS** for SvelteKit (config/settings/local.py)
   ```python
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:5173",  # SvelteKit dev server
       "http://127.0.0.1:5173",
   ]
   ```

7. **Test API endpoints manually** (minimal testing for experimental phase)
   ```bash
   # List jurisdictions
   curl http://localhost:8001/api/v1/jurisdictions/

   # Query endpoint
   curl -X POST http://localhost:8001/api/v1/query/query/ \
     -H "Content-Type: application/json" \
     -d '{"question": "What is response time in Colorado?", "state": "CO"}'
   ```

#### Deliverables

- [ ] Serializers created for all models
- [ ] ViewSets implemented (read-only + query)
- [ ] URL routing configured
- [ ] CORS configured for local dev
- [ ] Manual API testing successful (no automated tests required)

#### Success Criteria

```bash
# API endpoints accessible
curl http://localhost:8001/api/v1/jurisdictions/ | jq
# Returns: JSON list of state jurisdictions

curl http://localhost:8001/api/v1/resources/ | jq
# Returns: JSON list of resources

curl -X POST http://localhost:8001/api/v1/query/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question", "state": "CO"}' | jq
# Returns: JSON with answer and citations
```

---

---

### Phase 6: Integration & Documentation (30-45 minutes)

**Goal:** End-to-end validation and basic documentation.

**Note:** Minimal testing for experimental phase. Focus on ensuring both services work together.

#### Tasks

1. **Load test data**
   - Create fixture for Colorado jurisdiction resource
   - Load via management command or fixture
   - Upload to Gemini via signal

2. **End-to-end validation**
   - Upload resource via Django admin
   - Verify auto-upload to Gemini via signal
   - Query via API endpoint
   - Check response includes citation

3. **Integration testing checklist**
   - [ ] Can read jurisdictions from main app table
   - [ ] Can create resources in new table
   - [ ] Signals trigger upload to Gemini
   - [ ] Management commands work
   - [ ] API endpoints return correct data
   - [ ] CORS allows SvelteKit origin
   - [ ] Both services run simultaneously (8000 and 8001)

4. **Create basic documentation**
   - Document API endpoints for frontend team
   - Document how to load test data
   - Note any known issues or limitations

#### Deliverables

- [ ] Test data loaded and working
- [ ] End-to-end flow validated
- [ ] Integration checklist complete
- [ ] Basic API documentation created

#### Success Criteria

```bash
# Both services running
docker-compose -f local.yml ps
# Output: muckrock_django (8000) and foia_coach_api (8001) both Up

# API accessible from both localhost and container
curl http://localhost:8001/api/v1/jurisdictions/ | jq '.count'
# Returns: Number of state jurisdictions

# Can upload and query
# 1. Create resource via admin at http://localhost:8001/admin/
# 2. Verify indexed_status becomes 'ready'
# 3. Query via API
# 4. Receive answer with citations
```

---

## Configuration Reference

### Environment Variables

**Required in `.envs/.local/.foia_coach_api`:**
```bash
DJANGO_SETTINGS_MODULE=config.settings.local
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_FILE_SEARCH_STORE_NAME=StatePublicRecordsStore
DATABASE_URL=postgres://user:pass@muckrock_postgres:5432/muckrock
```

### Docker Commands Cheatsheet

**Note:** Use `docker compose` (not `docker-compose`) for newer Docker versions.

```bash
# Build service
docker compose -f local.yml build foia_coach_api

# Start service
docker compose -f local.yml up foia_coach_api

# Run management command
docker compose -f local.yml run --rm foia_coach_api python manage.py <command>

# Run tests
docker compose -f local.yml run --rm foia_coach_api pytest

# Shell access
docker compose -f local.yml run --rm foia_coach_api python manage.py shell

# Database migrations
docker compose -f local.yml run --rm foia_coach_api python manage.py makemigrations
docker compose -f local.yml run --rm foia_coach_api python manage.py migrate

# View logs
docker compose -f local.yml logs -f foia_coach_api
```

---

## Critical Files Summary

### Files to Create (in order of phases)

**Phase 0 (Rollback):**
- Backup files to `/tmp/` directory
- Delete migration `0032_*`
- Remove models from `muckrock/jurisdiction/models.py`

**Phase 1:**
- `foia-coach-api/requirements.in`
- `foia-coach-api/manage.py`
- `foia-coach-api/config/settings/base.py`
- `foia-coach-api/config/settings/local.py`
- `foia-coach-api/config/settings/test.py`
- `foia-coach-api/config/urls.py`
- `foia-coach-api/pytest.ini`

**Phase 2:**
- `foia-coach-api/compose/local/Dockerfile`
- `foia-coach-api/compose/local/entrypoint`
- `foia-coach-api/compose/local/start`
- `.envs/.local/.foia_coach_api`
- `foia-coach-api/.env.example`

**Phase 3:**
- `foia-coach-api/apps/jurisdiction/models.py`
- `foia-coach-api/apps/jurisdiction/services/muckrock_client.py`
- `foia-coach-api/apps/jurisdiction/admin.py`
- `foia-coach-api/apps/jurisdiction/apps.py`
- Update `foia-coach-api/requirements.in` (add requests)

**Phase 4a:**
- `foia-coach-api/apps/jurisdiction/services/gemini_service.py` (copy from backup)
- `foia-coach-api/apps/jurisdiction/signals.py` (adapt from Phase 2 work)

**Phase 4b:**
- `foia-coach-api/apps/jurisdiction/management/commands/*.py` (copy 4 files from backup)
- `foia-coach-api/apps/jurisdiction/factories.py` (adapt)
- `foia-coach-api/apps/jurisdiction/tests/test_gemini_service.py` (copy from backup)

**Phase 5:**
- `foia-coach-api/apps/api/serializers.py`
- `foia-coach-api/apps/api/viewsets.py`
- `foia-coach-api/apps/api/urls.py`

**Phase 6:**
- `README.md` or API documentation

### Files to Modify

**Phase 0:**
- `muckrock/jurisdiction/models.py` - Remove JurisdictionResource and GeminiFileSearchStore (delete, not move)
- `muckrock/jurisdiction/signals.py` - Remove Gemini-related signals (delete, not move)
- `muckrock/jurisdiction/services/` - Delete entire directory
- `muckrock/jurisdiction/management/commands/gemini_*.py` - Delete all Gemini commands
- `muckrock/jurisdiction/tests/test_gemini_service.py` - Delete test file
- **All deletions safe:** Code preserved in git history for reference

**Phase 2:**
- `local.yml` - Add foia_coach_api service definition

**Phase 3:**
- `config/settings/base.py` - Add MUCKROCK_API_URL and MUCKROCK_API_TOKEN settings
- `.envs/.local/.foia_coach_api` - Add MuckRock API configuration

---

## Testing Strategy

**Minimal testing for experimental phase.** Focus on:

### Essential Tests Only
- Service layer methods (with mocks) - from Phase 2 work
- Basic model functionality
- Manual API endpoint testing

### Test Execution
```bash
# Run existing tests from Phase 2
docker compose -f local.yml run --rm foia_coach_api pytest apps/jurisdiction/

# Manual API testing (preferred for experimental phase)
curl http://localhost:8001/api/v1/jurisdictions/
curl -X POST http://localhost:8001/api/v1/query/query/ -H "Content-Type: application/json" -d '{...}'
```

**Note:** Comprehensive test coverage is not required. Defer until after SvelteKit UI demonstrates value.

---

## Success Metrics

### Technical Success
- ✅ No dependency conflicts between services
- ✅ All Phase 2 tests passing in new service
- ✅ REST API endpoints functional
- ✅ Signals trigger Gemini uploads
- ✅ Both services run simultaneously

### Functional Success
- ✅ Can upload jurisdiction resources
- ✅ Resources auto-index in Gemini
- ✅ Query endpoint returns RAG answers with citations
- ✅ CORS allows SvelteKit frontend access
- ✅ Jurisdiction data fetched via MuckRock API
- ✅ Can point to local, dev, or production MuckRock API

### Process Success
- ✅ Each phase completable in single session
- ✅ Context limits not exceeded per phase
- ✅ Clean commits after each phase
- ✅ Main MuckRock app unaffected

---

## Next Steps After Phase 6

Once this standalone API service is complete:

1. **Update original plan** - Mark Phase 3 as complete in `.claude/foia-coach.md`
2. **Begin Phase 4** - SvelteKit UI development (separate session)
3. **Load real data** - Partner resources for CO, GA, TN
4. **Evaluate** - Gemini API performance and quality
5. **Iterate** - Based on experimentation results

---

## Risk Mitigation

### API Integration Risks
- **Risk:** MuckRock API changes or becomes unavailable
- **Mitigation:** API versioning (v2), graceful error handling, caching (future)
- **Risk:** Authentication issues with remote APIs
- **Mitigation:** Clear error messages, token validation, fallback to local Docker

### Dependency Drift
- **Risk:** google-genai updates break compatibility
- **Mitigation:** Pin versions in requirements.in, test upgrades carefully

### Signal Reliability
- **Risk:** Signals don't fire or fail silently
- **Mitigation:** Comprehensive logging, manual sync commands available

### API Performance
- **Risk:** Query endpoint too slow for good UX
- **Mitigation:** This is experimental - learning is the goal, not production perf

---

## Rollback Plan

If standalone approach doesn't work:

1. **Keep the code** - Don't delete, just stop the service
2. **Maintain main app** - Main MuckRock unaffected
3. **Alternative paths:**
   - Wait for dependency resolution
   - Use older google-genai without File Search
   - Explore different RAG providers

The isolated architecture makes this a low-risk experiment.

---

## Estimated Timeline

| Phase | Tasks | Time Estimate | Complexity |
|-------|-------|---------------|------------|
| Phase 0 | Rollback Phase 1&2 | 15-30 min | Low |
| Phase 1 | Django scaffold | 30-60 min | Low |
| Phase 2 | Docker config | 30-60 min | Low |
| Phase 3 | Models + API client | 45-60 min | Medium |
| Phase 4a | Gemini service + signals | 45-60 min | Medium |
| Phase 4b | Commands + tests | 45-60 min | Medium |
| Phase 5 | REST API | 45-60 min | Medium |
| Phase 6 | Integration & docs | 30-45 min | Low |
| **Total** | | **5-8 hours** | |

**Smaller phases (30-60 min each) for:**
- More frequent commits and checkpoints
- Easier backtracking if issues arise
- Better context limit management
- Clearer progress tracking

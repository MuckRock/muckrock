# FOIA Coach - Interactive State Public Records Guide

## Project Overview

Build an interactive guide to state public records and provide coaching for document requests. The system will use Google Gemini's File Search API (RAG) to provide state-by-state guidance when requesting public records.

### Key Principles
- **No automated request generation** - We provide knowledge, not language
- **State-specific expertise** - Starting with Colorado, Georgia, and Tennessee
- **Modular architecture** - Django API backend + SvelteKit experimental UI
- **Incremental development** - Implement in phases, commit incrementally
- **Experimental project** - Focus on learning Gemini API, not production robustness
- **Automatic sync** - Model signals handle Gemini uploads on save/update

---

## Architecture Overview

### Components

1. **Django Backend Enhancements**
   - New `JurisdictionResource` model for managing uploaded knowledge files
   - Google Gemini File Search integration for RAG
   - REST API endpoints for chat/query interface
   - File upload management and indexing

2. **SvelteKit Frontend (Separate Container)**
   - Rapid UI experimentation environment
   - Chat interface for state-specific guidance
   - State selection and resource browsing
   - Independent deployment from main Django app

3. **Google Gemini Integration**
   - File Search Store for state resources
   - Automatic file indexing and chunking
   - RAG-powered query responses with citations
   - Expert persona system instruction

---

## Current System Analysis

### Existing Jurisdiction Models

**Jurisdiction Model** (`muckrock/jurisdiction/models.py:74`)
- Tracks Federal/State/Local jurisdictions
- Fields: name, slug, abbrev, level, parent, hidden, image, public_notes, aliases
- Related to `Law` model (OneToOne)
- Related to `JurisdictionPage` model (OneToOne)

**Law Model** (`muckrock/jurisdiction/models.py:245`)
- OneToOne with Jurisdiction
- Contains: name, shortname, citation, url, days, waiver, has_appeal
- Additional analysis fields: law_analysis, fee_schedule, etc.

**JurisdictionPage Model** (`muckrock/jurisdiction/models.py:303`)
- OneToOne with Jurisdiction (state/federal only)
- Markdown content field for jurisdiction pages
- Has revision history

---

## Implementation Plan

### Phase 1: Django Model & Database Schema
**Goal:** Create database structure for managing jurisdiction resources

#### Tasks
1. Add to existing `jurisdiction` app
2. Design and implement `JurisdictionResource` model
3. Create model for tracking Gemini File Search metadata
4. Set up admin interface for resource management
5. Create database migrations
6. Implement Django signals to auto-upload on save/update
7. Write basic model tests

#### `JurisdictionResource` Model Design
```python
class JurisdictionResource(models.Model):
    """Knowledge resource file associated with a jurisdiction"""

    jurisdiction = models.ForeignKey(
        Jurisdiction,
        related_name='resources',
        on_delete=models.CASCADE,
        limit_choices_to={'level': 's'}  # State level only for now
    )

    # File management
    file = models.FileField(
        upload_to='jurisdiction_resources/%Y/%m/',
        help_text='Text file containing state-specific FOIA knowledge'
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

    # Metadata
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

    # Ordering for display
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['jurisdiction', 'order', 'display_name']
        verbose_name = 'Jurisdiction Resource'
        verbose_name_plural = 'Jurisdiction Resources'

    def __str__(self):
        return f"{self.jurisdiction.name} - {self.display_name}"
```

#### `GeminiFileSearchStore` Model Design
```python
class GeminiFileSearchStore(models.Model):
    """Tracks the Gemini File Search store configuration"""

    store_name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Stats
    total_files = models.PositiveIntegerField(default=0)
    last_sync_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Gemini File Search Store'
        verbose_name_plural = 'Gemini File Search Stores'

    def __str__(self):
        return self.display_name
```

#### Signal Handlers
```python
# muckrock/jurisdiction/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import JurisdictionResource

@receiver(post_save, sender=JurisdictionResource)
def upload_resource_to_gemini(sender, instance, created, **kwargs):
    """Automatically upload/update resource in Gemini when saved"""
    from .services.gemini_service import GeminiFileSearchService

    if instance.file and instance.is_active:
        service = GeminiFileSearchService()
        service.upload_and_index_resource(instance)

@receiver(post_delete, sender=JurisdictionResource)
def remove_resource_from_gemini(sender, instance, **kwargs):
    """Remove resource from Gemini when deleted"""
    from .services.gemini_service import GeminiFileSearchService

    if instance.gemini_file_id:
        service = GeminiFileSearchService()
        service.remove_resource(instance)
```

#### Deliverables
- [x] Models created with proper fields and relationships
- [x] Migrations generated and tested
- [x] Admin interface configured
- [x] Signal handlers for automatic Gemini sync
- [x] Basic model tests written and passing

---

### Phase 2: Google Gemini Integration Service
**Goal:** Build service layer for interacting with Gemini File Search API

#### Tasks
1. Install Google Generative AI SDK (`google-genai`)
2. Create `gemini_service.py` module with client wrapper
3. Implement File Search Store creation/management
4. Implement file upload and indexing (supports plain text and Markdown)
5. Implement query/chat functionality with system instructions
6. Implement streaming query functionality
7. Add methods for signal handlers (upload_and_index_resource, remove_resource)
8. Add basic error handling and retry logic
9. Create management commands for manual admin operations
10. Write basic integration tests

#### Service Architecture
```python
# muckrock/jurisdiction/services/gemini_service.py

class GeminiFileSearchService:
    """Service for managing Gemini File Search integration"""

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.store_name = None

    def create_store(self, display_name='StatePublicRecordsStore'):
        """Create or get the File Search store"""
        pass

    def upload_resource(self, resource: JurisdictionResource):
        """Upload a jurisdiction resource file to Gemini (plain text or Markdown)"""
        pass

    def index_resource(self, resource: JurisdictionResource):
        """Index a resource file in the File Search store"""
        pass

    def upload_and_index_resource(self, resource: JurisdictionResource):
        """Combined method for signal handlers - upload and index in one call"""
        pass

    def remove_resource(self, resource: JurisdictionResource):
        """Remove a resource from Gemini (for delete signal)"""
        pass

    def query(self, question: str, state: str = None, context: dict = None):
        """Query the RAG system with a question"""
        pass

    def query_stream(self, question: str, state: str = None, context: dict = None):
        """Query the RAG system with streaming response"""
        pass

    def get_system_instruction(self):
        """Return the expert persona system instruction"""
        pass
```

#### Management Commands
- `inv manage "gemini_create_store"` - Create/initialize the File Search store
- `inv manage "gemini_upload_resource <resource_id>"` - Upload single resource
- `inv manage "gemini_sync_all"` - Sync all pending resources
- `inv manage "gemini_query 'question' --state CO"` - Test queries

#### System Instruction Design
```python
SYSTEM_INSTRUCTION = """
You are the State Public Records & FOIA Coach. Your role is to provide
accurate, well-cited guidance about state public records laws and best
practices for requesting public records.

CRITICAL RULES:
1. Base ALL responses strictly on the documents in your knowledge base
2. ALWAYS cite the source document for every piece of information
3. If information is not in your knowledge base, explicitly say so
4. Do NOT generate request language - provide knowledge and coaching only
5. Focus on helping users understand the law and process
6. Highlight state-specific requirements, deadlines, and exemptions
7. Provide context about common pitfalls and best practices

When answering questions:
- Quote relevant law sections with citations
- Explain deadlines and response times
- Describe exemptions and their proper use
- Suggest what information users should research further
- Encourage specificity in their requests
- Note any jurisdiction-specific procedures

NEVER:
- Generate full request text
- Make legal claims beyond what's in documents
- Provide information from outside your knowledge base
- Make assumptions about unstated facts
"""
```

#### Deliverables
- [ ] Gemini service module implemented
- [ ] Signal handler methods (upload_and_index_resource, remove_resource) working
- [ ] Management commands created for manual operations
- [ ] Store creation and file upload working (plain text and Markdown)
- [ ] Query functionality with citations working
- [ ] Streaming query functionality working
- [ ] Basic error handling and logging implemented
- [ ] Basic integration tests passing

---

### Phase 3: Django REST API Endpoints
**Goal:** Create API endpoints for the SvelteKit frontend to consume

#### Tasks
1. Create DRF serializers for models
2. Implement API viewsets
3. Add API endpoints to urls (including streaming endpoint)
4. Implement CORS configuration for local dev
5. Add basic authentication/permissions
6. Write basic API documentation
7. Write basic API tests

#### API Endpoints

**Resources API**
- `GET /api/v1/foia-coach/jurisdictions/` - List states with resources
- `GET /api/v1/foia-coach/jurisdictions/<abbrev>/` - State detail with resources
- `GET /api/v1/foia-coach/resources/` - List all resources (filtered)
- `GET /api/v1/foia-coach/resources/<id>/` - Resource detail

**Chat/Query API**
- `POST /api/v1/foia-coach/query/` - Submit query to RAG system
  ```json
  {
    "question": "What is the response time for public records in Colorado?",
    "state": "CO",  // optional filter
    "context": {}   // optional additional context
  }
  ```
  Response:
  ```json
  {
    "answer": "...",
    "citations": [
      {
        "source": "CO_PublicRecordsLaw.txt",
        "display_name": "Colorado Public Records Law Guide"
      }
    ],
    "state": "CO"
  }
  ```

- `POST /api/v1/foia-coach/query/stream/` - Submit query with streaming response (experimental)
  - Same request format as above
  - Response: Server-Sent Events (SSE) stream
  - Each event contains a chunk of the response text
  - Final event includes complete citations

**Admin API** (authenticated only)
- `POST /api/v1/foia-coach/admin/sync-resource/<id>/` - Trigger resource sync
- `GET /api/v1/foia-coach/admin/sync-status/` - Get sync status

#### Serializers
```python
class JurisdictionResourceSerializer(serializers.ModelSerializer):
    jurisdiction_name = serializers.CharField(source='jurisdiction.name', read_only=True)
    jurisdiction_abbrev = serializers.CharField(source='jurisdiction.abbrev', read_only=True)

    class Meta:
        model = JurisdictionResource
        fields = [
            'id', 'jurisdiction', 'jurisdiction_name', 'jurisdiction_abbrev',
            'display_name', 'description', 'resource_type',
            'index_status', 'indexed_at', 'is_active', 'created_at'
        ]
        read_only_fields = ['index_status', 'indexed_at']
```

#### Deliverables
- [ ] Serializers implemented
- [ ] Viewsets and endpoints created (including streaming endpoint)
- [ ] API URLs configured
- [ ] CORS configured for local development
- [ ] Streaming response working with SSE
- [ ] Basic API tests written and passing
- [ ] Basic API documentation complete

---

### Phase 4: SvelteKit Frontend Application
**Goal:** Create experimental UI in separate Docker container

#### Tasks
1. Create SvelteKit project structure
2. Create Dockerfile for SvelteKit dev environment
3. Update docker-compose to add SvelteKit service
4. Build state selection interface
5. Build chat/query interface (with optional streaming support)
6. Implement API client for Django backend (both regular and streaming)
7. Add basic styling (TailwindCSS?)
8. Set up hot reload for development

#### Docker Configuration

**New service in `local.yml`:**
```yaml
muckrock_sveltekit:
  build:
    context: ./foia-coach-ui
    dockerfile: Dockerfile
  image: muckrock_foia_coach_ui
  ports:
    - "5173:5173"  # Vite dev server
  volumes:
    - ./foia-coach-ui:/app
    - /app/node_modules
  environment:
    - VITE_API_URL=http://localhost:8000
  command: npm run dev -- --host
```

#### SvelteKit Project Structure
```
foia-coach-ui/
├── src/
│   ├── lib/
│   │   ├── api/
│   │   │   └── client.ts          # API client
│   │   ├── components/
│   │   │   ├── StateSelector.svelte
│   │   │   ├── ChatInterface.svelte
│   │   │   ├── MessageList.svelte
│   │   │   └── ResourceList.svelte
│   │   ├── stores/
│   │   │   └── chat.ts            # Chat state management
│   │   └── types/
│   │       └── index.ts           # TypeScript types
│   ├── routes/
│   │   ├── +page.svelte           # Home/state selection
│   │   ├── [state]/
│   │   │   └── +page.svelte       # State-specific chat
│   │   └── +layout.svelte         # App layout
│   └── app.html
├── Dockerfile
├── package.json
└── svelte.config.js
```

#### Key Features
1. **State Selection Page**
   - Grid/list of available states (CO, GA, TN initially)
   - Show resource count and last updated
   - Quick info about each state's law

2. **Chat Interface**
   - Clean, accessible chat UI
   - Message history
   - Loading states
   - Optional streaming responses (experimental)
   - Citation display
   - Copy responses

3. **Resource Browser** (optional for Phase 4)
   - List resources for selected state
   - Filter by resource type
   - View resource metadata

#### Deliverables
- [ ] SvelteKit project initialized
- [ ] Docker configuration working
- [ ] State selection UI complete
- [ ] Chat interface functional (with optional streaming)
- [ ] API integration working (both regular and streaming endpoints)
- [ ] Basic styling applied
- [ ] Hot reload working

---

### Phase 5: Initial Data & Experimentation
**Goal:** Load initial resources and validate the experimental system

#### Tasks
1. Prepare resource files for CO, GA, TN (plain text or Markdown)
2. Create fixtures or data loading scripts
3. Upload and index all resources (automatic via signals or manual commands)
4. Basic end-to-end validation of full flow
5. Evaluate Gemini API performance and quality
6. Test streaming vs. non-streaming responses
7. Document learnings and next steps

#### Resource File Preparation
Partners will provide plain text or Markdown files with state-specific knowledge:
- Colorado public records law guide
- Georgia public records law guide
- Tennessee public records law guide

**File Format:** Plain text (.txt) or Markdown (.md)

Each file should include:
- Law overview and citation
- Response time requirements
- Fee structures
- Exemptions overview
- Appeal processes
- Agency-specific notes
- Best practices

#### Validation Checklist
- [ ] Files upload successfully to Gemini (plain text and Markdown)
- [ ] Indexing completes via signals or manual commands
- [ ] Queries return relevant, cited responses
- [ ] Citations reference correct source files
- [ ] State filtering works correctly
- [ ] Response times measured (both regular and streaming)
- [ ] Streaming responses work as expected
- [ ] Basic error cases are handled
- [ ] UI provides usable experience for experimentation

#### Deliverables
- [ ] Initial resource files loaded (plain text and Markdown)
- [ ] Basic validation tests passing
- [ ] Performance observations documented
- [ ] Gemini API evaluation complete
- [ ] Streaming vs. non-streaming comparison documented
- [ ] Learnings and recommendations documented
- [ ] Basic documentation for adding new states

---

## Technical Considerations

### Environment Variables
Add to `.envs/.local/.django`:
```bash
GEMINI_API_KEY=your_api_key_here
GEMINI_FILE_SEARCH_STORE_NAME=StatePublicRecordsStore
```

### Dependencies
**Django (requirements.in):**
- `google-genai

**SvelteKit (package.json):**
- `@sveltejs/kit`
- `vite`
- `typescript`
- `tailwindcss` (optional)
- `axios` or `fetch` for API calls

### File Storage
- Use Django's default file storage for uploaded resources
- Store files in `media/jurisdiction_resources/`
- Consider S3 storage for production

### Security Considerations
- Validate file types on upload (plain text and Markdown only: .txt, .md)
- Limit file sizes (e.g., 10MB max)
- Sanitize filenames
- Add basic rate limiting to query endpoints
- Basic authentication for API access
- CORS properly configured for local development
- **Note:** This is an experimental project, full production security hardening deferred

### Performance Considerations
- Gemini queries may take 2-5 seconds
- Streaming responses may provide better perceived performance
- Signal-based uploads happen synchronously (use async Celery tasks for production)
- Add loading states in UI for both regular and streaming responses
- Consider caching common queries (future enhancement)
- Consider pagination for resource lists
- **Note:** Performance optimization not a priority for experimental phase

---

## Development Workflow

### Session-by-Session Implementation
Each phase should be completed in a separate Claude Code session:

1. **Session 1: Phase 1** - Models, migrations, and signals
2. **Session 2: Phase 2** - Gemini service integration
3. **Session 3: Phase 3** - Django REST API (including streaming)
4. **Session 4: Phase 4** - SvelteKit frontend
5. **Session 5: Phase 5** - Data loading and experimentation

After each session, commit the working code:
```bash
git add .
git commit -m "feat(foia-coach): Phase X - [description]"
```

### Testing Strategy (Experimental Focus)
- Basic unit tests for models and core services
- Basic integration tests for Gemini API (can use mocks)
- Basic API endpoint tests
- Manual validation of critical flows
- Hands-on experimentation with UI and streaming responses

---

## Success Metrics (Experimental Project)

### Phase Completion Criteria
- Basic tests passing
- Code is functional and documented
- No critical bugs blocking experimentation
- Learnings documented

### Evaluation Criteria
- Query response accuracy (qualitative assessment)
- Response time observations (both regular and streaming)
- File upload and indexing reliability
- Citations present and useful
- Streaming API viability assessment
- Overall Gemini API suitability for this use case

---

## Open Questions & Decisions Needed

1. **~~Resource File Format~~** ✓ RESOLVED
   - **Decision:** Plain text (.txt) or Markdown (.md)
   - Structure: Free-form, partners provide formatted content
   - Files should be comprehensive guides covering all aspects of state law

2. **~~Automatic Syncing~~** ✓ RESOLVED
   - **Decision:** Use Django signals to automatically upload/update files to Gemini on save
   - Manual commands available for admin operations and troubleshooting

3. **~~Streaming API~~** ✓ RESOLVED
   - **Decision:** Implement separate streaming endpoint as experiment
   - Evaluate streaming vs. non-streaming in Phase 5

4. **Scope of Coaching** (To be evaluated)
   - What types of questions should we support?
   - Should we coach on specific request strategies?
   - How do we prevent generating request language?
   - Will be informed by experimentation with Gemini responses

---

## Current Status

- [x] Branch created: `foia-coach`
- [x] Planning document created
- [x] User has added `GEMINI_API_KEY` to environment
- [x] Plan updated with clarifications:
  - Model signals for automatic Gemini sync
  - Plain text and Markdown file support
  - Experimental focus (not production-ready)
  - Streaming API endpoint added
- [x] Ready to begin Phase 1 implementation

---

## Next Steps

1. **~~Review and refine plan~~** ✓ COMPLETE
2. **~~Finalize resource file format~~** ✓ COMPLETE (plain text and Markdown)
3. **Get sample files** from CO, GA, TN partners (plain text or Markdown)
4. **Begin Phase 1** - Models, migrations, and signals implementation
5. **Iterate and adjust plan** as we experiment and learn

---

## Notes & Learnings

### Planning Phase Updates (2025-11-26)
- **File Format Decision:** Plain text (.txt) and Markdown (.md) files
- **Automatic Sync:** Django signals will handle automatic upload/update to Gemini on model save
- **Experimental Nature:** This is a learning project to evaluate Gemini API, not production-ready
- **Streaming API:** Added separate streaming endpoint to experiment with streaming responses
- **Testing Approach:** Basic tests only, focus on hands-on experimentation and evaluation
- **Key Learning Goals:**
  - Gemini File Search API capabilities and limitations
  - RAG quality and citation accuracy
  - Response times (regular vs. streaming)
  - Overall suitability for FOIA coaching use case

_This section will be updated as we progress through implementation_


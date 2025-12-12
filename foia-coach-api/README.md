# FOIA Coach API

A Django-based API service that provides RAG-powered (Retrieval-Augmented Generation) assistance for FOIA requests using multiple AI providers.

## Overview

The FOIA Coach API helps users navigate Freedom of Information Act (FOIA) processes by providing intelligent answers based on jurisdiction-specific resources. The system supports multiple RAG providers, allowing flexibility in choosing the best AI service for your needs.

## Architecture

- **Framework:** Django REST Framework
- **Database:** PostgreSQL (`foia_coach`)
- **Port:** 8001 (standalone service)
- **RAG Providers:** OpenAI, Google Gemini, Mock (for testing)
- **Integration:** MuckRock API for jurisdiction data

## RAG Provider System

The FOIA Coach API uses a flexible provider architecture that supports multiple RAG backends:

### Available Providers

| Provider | Description | Best For | API Required |
|----------|-------------|----------|--------------|
| **OpenAI** | Uses OpenAI's Vector Stores and Assistants API | Production use, highest quality responses | Yes |
| **Gemini** | Uses Google's Gemini File Search | Alternative production option, cost-effective | Yes |
| **Mock** | Fake responses for testing | Testing, development without API costs | No |

### Provider Selection

Set the default provider using the `RAG_PROVIDER` environment variable:

```bash
# Use OpenAI (default)
export RAG_PROVIDER=openai

# Use Gemini
export RAG_PROVIDER=gemini

# Use Mock for testing
export RAG_PROVIDER=mock
```

You can also override the provider per-request via API or command-line flags.

### Provider Configuration

Each provider requires specific configuration:

#### OpenAI Configuration

```bash
export OPENAI_API_KEY=your_openai_api_key
export OPENAI_MODEL=gpt-4o  # optional, defaults to gpt-4o
export OPENAI_VECTOR_STORE_NAME="FOIA Coach Resources"
export OPENAI_REAL_API_ENABLED=true  # Enable API calls
```

#### Gemini Configuration

```bash
export GEMINI_API_KEY=your_gemini_api_key
export GEMINI_MODEL=gemini-2.0-flash-live  # optional
export GEMINI_FILE_SEARCH_STORE_NAME="FOIA Coach Resources"
export GEMINI_REAL_API_ENABLED=true  # Enable API calls
```

#### Safety Settings

For safety, all real API calls are **disabled by default** in test and development environments. This prevents accidental API usage and costs.

Set `*_REAL_API_ENABLED=true` explicitly to enable API calls:

```bash
# In production
OPENAI_REAL_API_ENABLED=true
GEMINI_REAL_API_ENABLED=true

# In tests (default)
OPENAI_REAL_API_ENABLED=false
GEMINI_REAL_API_ENABLED=false
```

## Quick Start

### Installation

```bash
# Start the service
docker compose -f local.yml up foia_coach_api

# Run migrations
docker compose -f local.yml run --rm foia_coach_api python manage.py migrate

# Create provider store
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_create_store --provider=openai
```

### Basic Usage

```bash
# Test provider configuration
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider --provider=openai

# Upload a resource
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_upload_resource 1 --provider=openai

# Query the system
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_query "What is the FOIA deadline in Colorado?" \
    --state=CO --provider=openai
```

## Management Commands

All management commands support the `--provider` flag to select a RAG provider:

### Test Provider Configuration

```bash
python manage.py test_rag_provider [options]

Options:
  --provider TEXT     Provider to test (default: RAG_PROVIDER setting)
  --list             List all available providers
  --all              Test all available providers
  --query TEXT       Optional test query to run
```

Examples:
```bash
# Test default provider
python manage.py test_rag_provider

# Test specific provider
python manage.py test_rag_provider --provider=openai

# Test all providers
python manage.py test_rag_provider --all

# List available providers
python manage.py test_rag_provider --list
```

### Create Store

```bash
python manage.py gemini_create_store [options]

Options:
  --provider TEXT    RAG provider to use
  --name TEXT       Custom display name for the store
```

### Upload Resource

```bash
python manage.py gemini_upload_resource RESOURCE_ID [options]

Options:
  --provider TEXT    RAG provider to use
  --force           Force re-upload even if already indexed
```

### Sync All Resources

```bash
python manage.py gemini_sync_all [options]

Options:
  --provider TEXT    RAG provider to use
  --all             Sync all resources, not just pending ones
  --state TEXT      Sync only resources for a specific state
```

### Query

```bash
python manage.py gemini_query QUESTION [options]

Options:
  --provider TEXT    RAG provider to use
  --state TEXT      Filter by state (e.g., CO, GA, TN)
  --stream          Use streaming response
```

## API Endpoints

### Query Status

Check available providers and their status:

```bash
GET /api/v1/query/status/
```

Response:
```json
{
  "current_provider": "openai",
  "available_providers": ["openai", "gemini", "mock"],
  "api_status": {
    "openai": "enabled",
    "gemini": "disabled",
    "mock": "always_enabled"
  },
  "status": "ready",
  "message": "Using openai provider. Set RAG_PROVIDER environment variable to change provider."
}
```

### Execute Query

```bash
POST /api/v1/query/query/
```

Request:
```json
{
  "question": "What is the response time in Colorado?",
  "state": "CO",
  "provider": "openai",
  "model": "gpt-4o"
}
```

Response:
```json
{
  "answer": "In Colorado, agencies must respond within 3 business days...",
  "citations": [
    {
      "display_name": "Colorado FOIA Guide",
      "source": "colorado_guide.pdf"
    }
  ],
  "provider": "openai",
  "model": "gpt-4o",
  "state": "CO"
}
```

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API reference.

## Provider Comparison

### Feature Comparison

| Feature | OpenAI | Gemini | Mock |
|---------|--------|--------|------|
| **Cost** | $$ | $ | Free |
| **Response Quality** | Excellent | Very Good | N/A |
| **Speed** | Fast | Very Fast | Instant |
| **Max Files** | 10,000 per store | Unlimited | Unlimited |
| **File Size Limit** | 512 MB | 2 GB | N/A |
| **Context Window** | 128K tokens | 2M tokens | N/A |
| **Streaming** | Yes | Yes | Yes |
| **Citations** | Yes | Yes | Yes |

### When to Use Each Provider

**OpenAI:**
- Production environments requiring highest quality responses
- When you need detailed, accurate citations
- Complex queries requiring advanced reasoning
- Budget allows for premium service

**Gemini:**
- Cost-conscious production deployments
- Very large documents (>512 MB)
- Queries requiring large context windows
- High-volume scenarios

**Mock:**
- Testing without API costs
- CI/CD pipelines
- Development environments
- Integration testing

### Cost Comparison

**OpenAI:**
- Vector Store: $0.10 per GB/day
- Assistant API: $0.03 per 1K tokens (input) + $0.06 per 1K tokens (output)
- Estimated: ~$5-10/month for typical usage

**Gemini:**
- File Search: Free tier available (15 RPM limit)
- Gemini 2.0 Flash: Free for moderate usage
- Estimated: $0-5/month for typical usage

**Mock:**
- Always free
- No API calls made

## Testing

### Unit Tests

All tests use MockProvider by default to prevent API calls:

```bash
# Run all tests
docker compose -f local.yml run --rm foia_coach_api pytest

# Run provider tests
docker compose -f local.yml run --rm foia_coach_api \
  pytest apps/jurisdiction/tests/test_providers.py

# Run with coverage
docker compose -f local.yml run --rm foia_coach_api \
  pytest --cov=apps.jurisdiction
```

### Manual Testing with Real APIs

To test with real API providers (development only):

```bash
# Set API enabled flag
OPENAI_REAL_API_ENABLED=true docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider --provider=openai --query="Test question"
```

**Warning:** Manual testing with real APIs will incur costs. Only use for development/verification.

## Migration from Gemini-Only

If you're migrating from a Gemini-only setup:

1. **Existing data is preserved:** The migration automatically converts `gemini_file_id` to `provider_file_id`
2. **Backward compatibility:** Both fields are synced automatically
3. **Switch providers:** Simply change `RAG_PROVIDER` environment variable
4. **Re-upload resources:** Run `gemini_sync_all --provider=openai` to upload to new provider

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for detailed migration instructions.

## Development

### Project Structure

```
foia-coach-api/
├── apps/
│   ├── api/                      # REST API endpoints
│   │   ├── serializers.py        # API serializers (provider-aware)
│   │   └── viewsets.py           # API views (provider-aware)
│   └── jurisdiction/
│       ├── models.py              # JurisdictionResource model
│       ├── signals.py             # Auto-upload signals
│       ├── services/
│       │   ├── providers/         # RAG provider system
│       │   │   ├── base.py        # Abstract base class
│       │   │   ├── openai_provider.py
│       │   │   ├── gemini_provider.py
│       │   │   ├── mock_provider.py
│       │   │   ├── factory.py     # Provider factory
│       │   │   └── helpers.py     # Utility functions
│       │   ├── openai_service.py  # OpenAI implementation
│       │   └── gemini_service.py  # Gemini implementation
│       ├── management/commands/   # CLI commands
│       └── tests/                 # Test suite
├── config/
│   └── settings/
│       ├── base.py                # Base settings
│       ├── local.py               # Local dev settings
│       └── test.py                # Test settings (API disabled)
└── README.md                      # This file
```

### Adding a New Provider

To add a new RAG provider:

1. Create provider class in `apps/jurisdiction/services/providers/`:
   ```python
   from .base import RAGProviderBase

   class MyProvider(RAGProviderBase):
       PROVIDER_NAME = 'myprovider'

       def query(self, question, **kwargs):
           # Implementation
           pass
   ```

2. Register in `__init__.py`:
   ```python
   RAGProviderFactory.register_provider('myprovider', MyProvider)
   ```

3. Add configuration settings
4. Add tests
5. Update documentation

## Troubleshooting

### API Disabled Error

**Error:** `API calls are disabled`

**Solution:** Set the appropriate `*_REAL_API_ENABLED=true` flag:
```bash
export OPENAI_REAL_API_ENABLED=true
# or
export GEMINI_REAL_API_ENABLED=true
```

### Provider Not Found

**Error:** `Provider 'xyz' not found`

**Solution:** Check available providers:
```bash
python manage.py test_rag_provider --list
```

Valid providers: `openai`, `gemini`, `mock`

### API Key Invalid

**Error:** `Authentication failed`

**Solution:** Verify your API key is set correctly:
```bash
# For OpenAI
export OPENAI_API_KEY=sk-...

# For Gemini
export GEMINI_API_KEY=...
```

### Quota Exceeded

**Error:** `API quota exceeded`

**Solution:**
- Wait for quota to reset (usually 1 minute)
- Upgrade to paid tier
- Switch to alternate provider
- Use Mock provider for testing

## Resources

- [API Documentation](./API_DOCUMENTATION.md)
- [Migration Guide](./MIGRATION_GUIDE.md)
- [Safety Guidelines](./README_GEMINI_SAFETY.md)
- [OpenAI Documentation](https://platform.openai.com/docs)
- [Gemini Documentation](https://ai.google.dev/gemini-api/docs)

## Contributing

When contributing:

1. **Always use MockProvider in tests** - Never make real API calls in CI/CD
2. **Add `--provider` flag** to new commands
3. **Update documentation** for provider-specific features
4. **Test with all providers** before submitting PR

## License

See main MuckRock repository for license information.

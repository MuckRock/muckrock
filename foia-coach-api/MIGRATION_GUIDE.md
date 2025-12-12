# Migration Guide: Gemini-Only to Multi-Provider

This guide helps you migrate from the legacy Gemini-only implementation to the new multi-provider system.

## Overview

The multi-provider system adds support for OpenAI and other RAG providers while maintaining full backward compatibility with existing Gemini deployments.

## What Changed

### Database Schema

New provider-agnostic fields were added to `JurisdictionResource`:

| Old Field (Deprecated) | New Field | Description |
|------------------------|-----------|-------------|
| `gemini_file_id` | `provider_file_id` | Provider-specific file ID |
| `gemini_display_name` | (removed) | No longer needed |
| N/A | `provider` | Selected provider (openai/gemini/mock) |
| N/A | `provider_store_id` | Provider-specific store ID |
| N/A | `provider_metadata` | Provider-specific metadata (JSON) |

### Code Changes

| Component | Old | New |
|-----------|-----|-----|
| **Service** | `GeminiFileSearchService()` | `get_provider(name)` |
| **Import** | `from ...gemini_service import GeminiFileSearchService` | `from ...providers.helpers import get_provider` |
| **Commands** | Gemini-specific | Provider-aware with `--provider` flag |
| **API** | Gemini-only | Multi-provider with provider selection |

## Migration Steps

### Step 1: Backup Database

```bash
# Create database backup
docker compose -f local.yml run --rm postgres \
  pg_dump -U foia_coach foia_coach > backup_$(date +%Y%m%d).sql
```

### Step 2: Run Migration

The migration automatically converts existing Gemini data:

```bash
# Run migrations
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py migrate
```

The migration will:
- Add new provider fields
- Copy `gemini_file_id` → `provider_file_id`
- Set `provider='gemini'` for existing resources
- Preserve all existing data

### Step 3: Update Configuration

#### Option A: Continue Using Gemini

No changes needed! Your existing configuration works:

```bash
# Keep existing Gemini config
export RAG_PROVIDER=gemini
export GEMINI_API_KEY=your_key
export GEMINI_REAL_API_ENABLED=true
```

#### Option B: Switch to OpenAI

Add OpenAI configuration:

```bash
# Set OpenAI as default
export RAG_PROVIDER=openai
export OPENAI_API_KEY=your_openai_key
export OPENAI_REAL_API_ENABLED=true

# Optional: OpenAI-specific settings
export OPENAI_MODEL=gpt-4o
export OPENAI_VECTOR_STORE_NAME="FOIA Coach Resources"
```

### Step 4: Re-upload Resources (If Switching Providers)

If switching from Gemini to OpenAI, re-upload all resources:

```bash
# Create OpenAI store
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_create_store --provider=openai

# Upload all resources to OpenAI
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all --provider=openai --all

# Verify
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider --provider=openai
```

### Step 5: Update Custom Code

If you have custom code calling the service directly:

#### Before:
```python
from apps.jurisdiction.services.gemini_service import GeminiFileSearchService

service = GeminiFileSearchService()
result = service.query(question="What is the deadline?", state="CO")
```

#### After:
```python
from apps.jurisdiction.services.providers.helpers import get_provider

provider = get_provider()  # Uses RAG_PROVIDER setting
# or
provider = get_provider('openai')  # Explicit provider

result = provider.query(question="What is the deadline?", state="CO")
```

### Step 6: Update Tests

Tests automatically use MockProvider, but if you have custom tests:

#### Before:
```python
from apps.jurisdiction.services.gemini_service import GeminiFileSearchService

@patch('apps.jurisdiction.services.gemini_service.genai.Client')
def test_query(mock_client):
    service = GeminiFileSearchService()
    result = service.query("Test question")
```

#### After:
```python
from apps.jurisdiction.services.providers.helpers import get_provider

def test_query():
    # MockProvider is used by default in tests
    provider = get_provider('mock')
    result = provider.query("Test question")
    # No mocking needed!
```

## Verification Checklist

After migration, verify everything works:

- [ ] Database migration completed successfully
- [ ] Existing resources have `provider_file_id` populated
- [ ] Provider configuration is set correctly
- [ ] Test provider connectivity: `python manage.py test_rag_provider`
- [ ] Upload a new resource successfully
- [ ] Query returns correct results
- [ ] API endpoints work with new provider field
- [ ] Tests pass with MockProvider
- [ ] Management commands work with `--provider` flag

## Rollback Plan

If you need to rollback:

### Rollback Migration

```bash
# Rollback database migration
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py migrate jurisdiction 0001

# Restore from backup
docker compose -f local.yml run --rm postgres \
  psql -U foia_coach foia_coach < backup_20231210.sql
```

### Rollback Code

```bash
# Checkout previous commit
git checkout <previous_commit_hash>

# Restart services
docker compose -f local.yml restart
```

## Common Issues

### Issue: Resources not showing in new provider

**Symptom:** Uploaded resources to Gemini, but queries to OpenAI don't see them

**Solution:** Resources must be uploaded to each provider separately:
```bash
python manage.py gemini_sync_all --provider=openai --all
```

### Issue: Provider field is None

**Symptom:** `provider` field is `None` for existing resources

**Solution:** Run data migration again or manually update:
```sql
UPDATE jurisdiction_jurisdictionresource
SET provider = 'gemini'
WHERE gemini_file_id IS NOT NULL AND provider IS NULL;
```

### Issue: API calls disabled in production

**Symptom:** Getting "API calls are disabled" error in production

**Solution:** Ensure `*_REAL_API_ENABLED=true` is set:
```bash
export OPENAI_REAL_API_ENABLED=true
export GEMINI_REAL_API_ENABLED=true
```

### Issue: Tests failing with API errors

**Symptom:** Tests making real API calls

**Solution:** Verify test settings use MockProvider:
```python
# In config/settings/test.py
RAG_PROVIDER = 'mock'
OPENAI_REAL_API_ENABLED = False
GEMINI_REAL_API_ENABLED = False
```

## Backward Compatibility

The migration maintains backward compatibility:

### Field Syncing

The `gemini_file_id` and `provider_file_id` fields are automatically synced:

```python
resource.provider = 'gemini'
resource.provider_file_id = 'files/abc123'
resource.save()

# gemini_file_id is automatically set to 'files/abc123'
assert resource.gemini_file_id == 'files/abc123'
```

### Legacy Service Still Works

The legacy `GeminiFileSearchService` still works:

```python
# This still works (but is deprecated)
from apps.jurisdiction.services.gemini_service import GeminiFileSearchService
service = GeminiFileSearchService()
```

However, new code should use the provider factory:

```python
# Preferred approach
from apps.jurisdiction.services.providers.helpers import get_provider
provider = get_provider('gemini')
```

## Performance Considerations

### Provider Selection Impact

Different providers have different performance characteristics:

| Provider | Upload Time | Query Latency | Best For |
|----------|-------------|---------------|----------|
| **OpenAI** | ~5-10s per file | ~2-3s | Quality |
| **Gemini** | ~3-5s per file | ~1-2s | Speed |
| **Mock** | Instant | Instant | Testing |

### Cost Impact

Switching providers may affect costs:

- **Gemini → OpenAI**: Costs may increase (~2-3x)
- **OpenAI → Gemini**: Costs may decrease
- **Either → Mock**: Free for testing

## Support

If you encounter issues during migration:

1. Check the [Troubleshooting](#common-issues) section above
2. Review [README.md](./README.md) for configuration details
3. Run diagnostics: `python manage.py test_rag_provider --all`
4. Check logs for error messages
5. Open an issue with migration logs attached

## Timeline

Recommended migration timeline:

1. **Week 1:** Review documentation, plan migration
2. **Week 2:** Test migration in development environment
3. **Week 3:** Test migration in staging environment
4. **Week 4:** Execute production migration during low-traffic period
5. **Week 5:** Monitor and optimize

## Next Steps

After successful migration:

1. Review [README.md](./README.md) for full feature documentation
2. Explore provider comparison to optimize costs
3. Set up monitoring for provider performance
4. Update team documentation with new commands
5. Consider implementing provider fallback logic

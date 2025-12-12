# OpenAI Quick Start Guide

Get your FOIA Coach SvelteKit app working with OpenAI in 5 minutes!

## Step 1: Configure OpenAI in the API (2 minutes)

Edit `.envs/.local/.foia_coach_api`:

```bash
# Add these lines
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_REAL_API_ENABLED=true
RAG_PROVIDER=openai
```

Restart the API:
```bash
docker compose -f local.yml restart foia_coach_api
```

## Step 2: Create OpenAI Vector Store (1 minute)

```bash
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_create_store --provider=openai
```

Expected output:
```
Using provider: openai
Getting or creating provider store...
✓ Store ready: vs_abc123xyz...
```

## Step 3: Upload Resources (5 minutes)

Upload all your jurisdiction resources to OpenAI:

```bash
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all --provider=openai --all
```

Or just upload one state for testing:

```bash
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all --provider=openai --state=CO --all
```

## Step 4: Start Your SvelteKit App

```bash
cd foia-coach-ui
npm run dev
```

Open http://localhost:5173

## Step 5: Configure in the UI

1. Go to **Settings** (click the settings icon)
2. Change **AI Provider** to "OpenAI"
3. Set **Model** to "gpt-4o" (or "gpt-4o-mini" for cheaper queries)
4. Click **Save Settings**
5. Click **Test Connection** to verify it works

## Step 6: Ask a Question!

Go back to the main chat interface and ask:

```
What is the FOIA response deadline in Colorado?
```

You should see:
- ✅ Answer from OpenAI
- ✅ Provider badge showing "openai"
- ✅ Citations with source documents
- ✅ State indicator (CO)

## What Changed in Your UI

Your SvelteKit app now has:

1. **Provider Selection** - Choose OpenAI, Gemini, or Mock in settings
2. **Model Configuration** - Set specific models (gpt-4o, gpt-4o-mini, etc.)
3. **Provider Badges** - See which provider answered each question
4. **Better Citations** - Display names and jurisdiction tags

## Settings Explained

| Setting | Description | Examples |
|---------|-------------|----------|
| **API URL** | FOIA Coach API location | `http://localhost:8001` |
| **API Token** | Optional auth token | (leave blank for local dev) |
| **AI Provider** | Which AI service to use | OpenAI, Gemini, Mock |
| **Model** | Specific model version | `gpt-4o`, `gpt-4o-mini`, `gemini-2.0-flash-001` |

## Cost Optimization

### Use gpt-4o-mini for Lower Costs

In Settings, change Model to `gpt-4o-mini`:
- **10x cheaper** than gpt-4o
- Still excellent quality
- Faster responses
- Perfect for most questions

### Expected Costs

With **gpt-4o**:
- Per query: ~$0.01-0.05
- 100 queries: ~$1-5
- Monthly (moderate use): ~$10-20

With **gpt-4o-mini**:
- Per query: ~$0.001-0.005
- 100 queries: ~$0.10-0.50
- Monthly (moderate use): ~$1-2

## Testing Without Costs

Use the **Mock** provider for testing:
1. Go to Settings
2. Change AI Provider to "Mock (Testing)"
3. Save Settings
4. Ask questions - get instant fake responses
5. No API costs!

## Troubleshooting

### "API calls are disabled"

**Solution:** Make sure you set `OPENAI_REAL_API_ENABLED=true` in `.envs/.local/.foia_coach_api` and restarted the service.

### No answers or empty responses

**Solution:** Check that resources are uploaded:
```bash
docker compose -f local.yml run --rm foia_coach_api python manage.py shell
>>> from apps.jurisdiction.models import JurisdictionResource
>>> JurisdictionResource.objects.filter(provider='openai', index_status='ready').count()
```

If the count is 0, run the upload command from Step 3.

### "Invalid API key"

**Solution:**
1. Get a new key from https://platform.openai.com/api-keys
2. Update `.envs/.local/.foia_coach_api`
3. Restart: `docker compose -f local.yml restart foia_coach_api`

### CORS errors in browser console

**Solution:** The API should already have CORS configured, but if you see errors, check that `CORS_ALLOWED_ORIGINS` includes your SvelteKit dev server URL in `config/settings/local.py`.

## Switching Between Providers

You can switch providers anytime:

1. **In Settings UI:**
   - Go to Settings
   - Change "AI Provider" dropdown
   - Save Settings
   - New queries use the new provider

2. **Per Query (Advanced):**
   - The API client automatically uses your selected provider
   - Provider and model info is saved with each message
   - Chat history shows which provider answered each question

## Next Steps

✅ **You're all set!** Your app now supports:
- OpenAI GPT-4o for high-quality answers
- Gemini for cost-effective queries
- Mock provider for testing
- Easy switching between providers
- Full chat history with provider tracking

### Want to go further?

- [ ] Add streaming responses for real-time typing effect
- [ ] Implement response caching for common questions
- [ ] Add analytics to track provider performance
- [ ] Build admin panel for resource management
- [ ] Add user authentication

## Quick Reference

```bash
# Upload resources to OpenAI
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all --provider=openai --all

# Query from command line
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_query "What are FOIA fees?" \
    --provider=openai --state=CO

# Test provider
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider --provider=openai

# Check provider status (in browser)
curl http://localhost:8001/api/v1/query/status/
```

## Support

Need help? Check these docs:
- [Full API Documentation](../foia-coach-api/README.md)
- [SvelteKit Integration Guide](../foia-coach-api/SVELTEKIT_INTEGRATION_GUIDE.md)
- [Usage Examples](../foia-coach-api/USAGE_EXAMPLES.md)
- [Migration Guide](../foia-coach-api/MIGRATION_GUIDE.md)

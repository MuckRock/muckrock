# ⚠️ IMPORTANT: Gemini API Safety

## Quick Start - Stay Safe

### Default Configuration (SAFE)
```bash
# In .envs/.local/.foia_coach_api
GEMINI_REAL_API_ENABLED=false  # ✅ API calls BLOCKED
```

### When You Need Real API Calls
```bash
# 1. Enable temporarily
GEMINI_REAL_API_ENABLED=true  # ⚠️ Will consume quota!

# 2. Restart service
docker compose -f local.yml restart foia_coach_api

# 3. Monitor logs for warnings
docker compose -f local.yml logs foia_coach_api -f | grep "⚠️"

# 4. DISABLE when done
GEMINI_REAL_API_ENABLED=false
docker compose -f local.yml restart foia_coach_api
```

## Why This Matters

**During initial development (Dec 9-10, 2025):**
- Sent **107,800 API requests** in 2 days
- Exhausted free tier quota (1,500/day limit)
- Got 429 (Too Many Requests) errors
- Caused by infinite loop bug + missing mocks

**Free tier limits:**
- 60 requests per minute
- 1,500 requests per day
- Each resource upload = 2-12 requests
- Each query = 2 requests

## Safety Measures in Place

✅ **Request tracking & warnings** - Logs every 50 requests, alerts at 200
✅ **API disabled by default** - Must explicitly enable
✅ **Tests use mocks** - No real API calls in tests
✅ **Signals protected** - Can't trigger infinite loops
✅ **Environment flag** - `GEMINI_REAL_API_ENABLED`

## Common Scenarios

### Running Tests (Always Safe)
```bash
docker compose -f local.yml run --rm foia_coach_api pytest
# ✅ Uses mocked API, won't consume quota
```

### Manual Testing
```bash
# Will fail by default (safe!)
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_upload_resource 1

# Error: RuntimeError: Gemini API calls are disabled...
```

### Development Work
```bash
# Code changes, migrations, etc - all safe by default
# API is disabled unless you explicitly enable it
```

## If You Hit Rate Limits

1. **Stop immediately:**
   ```bash
   GEMINI_REAL_API_ENABLED=false
   docker compose -f local.yml restart foia_coach_api
   ```

2. **Check request count:**
   ```python
   from apps.jurisdiction.services.gemini_service import GeminiFileSearchService
   stats = GeminiFileSearchService.get_request_stats()
   print(stats)
   ```

3. **Review logs:**
   ```bash
   docker compose -f local.yml logs foia_coach_api | grep "⚠️"
   ```

4. **Wait 24 hours** for quota reset (free tier)

## Full Documentation

See `GEMINI_API_SAFETY.md` for:
- Detailed safety measures
- Request monitoring
- Best practices
- Troubleshooting guide
- Emergency procedures

## Questions?

1. Check logs: `docker compose -f local.yml logs foia_coach_api`
2. Check settings: `echo $GEMINI_REAL_API_ENABLED`
3. Read full docs: `GEMINI_API_SAFETY.md`
4. Contact team lead if quota exhausted

---

**Remember:** Default configuration is SAFE. API calls are BLOCKED unless you explicitly enable them.

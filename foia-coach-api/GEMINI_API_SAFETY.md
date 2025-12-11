# Gemini API Safety & Best Practices

## Overview

This document outlines safety measures implemented to prevent accidental Gemini API quota consumption during development and testing.

## The Problem

During initial development (Dec 9-10, 2025), we sent **107,800 Gemini API requests** in two days due to:
1. Infinite recursion bug in signal handlers (before fix)
2. Tests making real API calls instead of using mocks
3. Multiple API calls per operation (upload = 3-12+ requests)
4. No safety checks or warnings

This exhausted our free tier quota and resulted in 429 (Too Many Requests) errors.

## Safety Measures Implemented

### 1. Request Tracking & Throttling

**Location**: `apps/jurisdiction/services/gemini_service.py`

Every Gemini API call is now tracked with warnings:

```python
# Automatic tracking
GeminiFileSearchService._track_request()  # Called before each API call

# Warnings triggered:
# - Every 50 requests: Session count + recent rate
# - After 200 requests: ⚠️ WARNING - likely a bug
# - If >50 QPM: ⚠️ RATE LIMIT WARNING
```

**View statistics in code:**
```python
from apps.jurisdiction.services.gemini_service import GeminiFileSearchService

stats = GeminiFileSearchService.get_request_stats()
# Returns:
# {
#     'total_requests_this_session': 45,
#     'requests_last_minute': 12,
#     'rate_limit_threshold': 50,
#     'session_limit_threshold': 200
# }
```

### 2. GEMINI_REAL_API_ENABLED Flag

**Default: DISABLED (False)**

Real API calls are blocked by default. Must explicitly enable.

**Configuration:**

```bash
# .envs/.local/.foia_coach_api
GEMINI_REAL_API_ENABLED=false  # SAFE DEFAULT

# To enable real API calls (e.g., for manual testing):
GEMINI_REAL_API_ENABLED=true  # ⚠️ USE CAREFULLY!
```

**Behavior:**
- When `False`: Service initializes with `client=None`, all API methods raise `RuntimeError`
- When `True`: Normal operation, API calls proceed (will consume quota)

**Warning on startup:**
```
⚠️ GEMINI_REAL_API_ENABLED is False - Real API calls are DISABLED.
Set GEMINI_REAL_API_ENABLED=true in environment to enable.
```

### 3. Test Safeguards

**Location**: `apps/jurisdiction/tests/conftest.py`

All tests automatically:
1. **Disable API calls**: `GEMINI_REAL_API_ENABLED = False`
2. **Disconnect signals**: Prevents automatic uploads on model saves
3. **Reset tracking**: Clears request counts between tests
4. **Mock API client**: All test methods use `@patch('...genai.Client')`

**Test settings**: `config/settings/test.py`
```python
GEMINI_REAL_API_ENABLED = False  # CRITICAL SAFETY MEASURE
```

**Special fixture for tests that need API enabled:**
```python
def test_something(gemini_service_with_real_api_enabled):
    # API is enabled BUT client is still mocked
    # This tests the enable/disable logic itself
    pass
```

### 4. Signal Handler Protection

**Location**: `apps/jurisdiction/signals.py`

Signal handler only uploads if `status='pending'`:

```python
@receiver(post_save, sender=JurisdictionResource)
def upload_resource_to_gemini(sender, instance, created, **kwargs):
    # CRITICAL: Prevent infinite recursion
    if instance.index_status != 'pending':
        return  # Skip if already uploading/ready/error

    # ... upload logic that updates status
```

**This prevents the infinite loop:**
1. Save with `status='pending'` → Signal fires → Upload starts
2. Update to `status='uploading'` → Signal fires but returns early
3. Update to `status='ready'` → Signal fires but returns early

## How to Use Gemini API Safely

### During Development

**Default (Recommended):**
```bash
# Leave GEMINI_REAL_API_ENABLED=false in .envs/.local/.foia_coach_api
# All API calls will be blocked with helpful error messages
```

**When you NEED real API calls:**
```bash
# 1. Set environment variable
GEMINI_REAL_API_ENABLED=true

# 2. Restart container
docker compose -f local.yml restart foia_coach_api

# 3. Watch logs for request count warnings
docker compose -f local.yml logs foia_coach_api -f

# 4. DISABLE again when done!
GEMINI_REAL_API_ENABLED=false
docker compose -f local.yml restart foia_coach_api
```

### During Testing

Tests are **automatically safe** - no action needed!

```bash
# All tests use mocked API client
docker compose -f local.yml run --rm foia_coach_api pytest

# GEMINI_REAL_API_ENABLED is False in test settings
# Signals are disconnected
# API client is mocked with @patch decorator
```

### Manual Testing / Management Commands

```bash
# Safe by default (will fail if API disabled)
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_upload_resource 1

# Error: RuntimeError: Gemini API calls are disabled...

# Enable temporarily for real upload:
# 1. Edit .envs/.local/.foia_coach_api
# 2. Set GEMINI_REAL_API_ENABLED=true
# 3. Restart container
# 4. Run command
# 5. Set back to false
```

## Request Limits

### Gemini Free Tier (as of Dec 2024)
- **60 QPM** (Queries Per Minute)
- **1,500 QPD** (Queries Per Day)
- **50,000 TPM** (Tokens Per Minute)

### Our API Call Patterns

**Per Resource Upload:**
- List stores: 1 request
- Upload file: 1 request
- Poll status: 0-10 requests (if needed)
- **Total: 2-12 requests per upload**

**Per Query:**
- Get store: 1 request
- Generate content: 1 request
- **Total: 2 requests per query**

**Per Delete:**
- Get store: 1 request
- Delete file: 1 request
- **Total: 2 requests per delete**

### Estimating API Usage

```python
# Upload 10 resources: ~20-120 requests
# Query 50 times: ~100 requests
# Delete 5 resources: ~10 requests
# ----------------------------
# Total: ~130-230 requests

# Free tier daily limit: 1,500 requests
# Safe margin: Stay under 500 requests/day during development
```

## Monitoring API Usage

### In Application Logs

Watch for these log messages:

```
INFO: Gemini API: 50 requests made this session. 12 requests in the last minute.
WARNING: Gemini API: 100 requests made this session. 18 requests in the last minute.
ERROR: ⚠️ GEMINI API USAGE WARNING: 250 requests made this session! This is likely a bug...
ERROR: ⚠️ RATE LIMIT WARNING: 55 requests in the last minute! Gemini free tier limit is 60 QPM...
```

### In Code

```python
from apps.jurisdiction.services.gemini_service import GeminiFileSearchService

# Check current statistics
stats = GeminiFileSearchService.get_request_stats()
print(f"Total this session: {stats['total_requests_this_session']}")
print(f"Last minute: {stats['requests_last_minute']}")

# Reset tracking (useful after identifying issue)
GeminiFileSearchService.reset_request_tracking()
```

### In Google Cloud Console

1. Visit: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/
2. Select your project
3. View "Quotas & System Limits"
4. Monitor usage graphs

## What To Do If You Hit Rate Limits

### Immediate Actions

1. **Stop making API calls:**
   ```bash
   # Disable API immediately
   GEMINI_REAL_API_ENABLED=false
   docker compose -f local.yml restart foia_coach_api
   ```

2. **Check request count:**
   ```python
   GeminiFileSearchService.get_request_stats()
   ```

3. **Review logs for warnings:**
   ```bash
   docker compose -f local.yml logs foia_coach_api | grep "⚠️"
   ```

### Investigation

1. **Check for infinite loops:**
   - Review recent code changes to signals
   - Verify status checks in signal handlers

2. **Confirm tests are using mocks:**
   ```bash
   # Tests should complete in seconds, not minutes
   docker compose -f local.yml run --rm foia_coach_api pytest -v
   ```

3. **Check GEMINI_REAL_API_ENABLED:**
   ```bash
   docker compose -f local.yml exec foia_coach_api env | grep GEMINI
   ```

### Recovery

Free tier quotas reset after 24 hours. Options:

1. **Wait 24 hours** for quota reset
2. **Upgrade to paid tier** (if urgent): https://ai.google.dev/pricing
3. **Use test mode** (mocked API) for development

## Upgrading to Paid Tier

If you need more than free tier limits:

1. Visit: https://console.cloud.google.com/billing
2. Enable billing on your project
3. API limits increase automatically:
   - **1,000 QPM** (vs 60 free)
   - **1,000,000 QPD** (vs 1,500 free)
   - Pay per token beyond free tier

**Estimated costs (as of Dec 2024):**
- Gemini 1.5 Flash: $0.075 / 1M input tokens
- 100k requests ~= $7.50 (very rough estimate)

## Best Practices Summary

### ✅ DO:
- Keep `GEMINI_REAL_API_ENABLED=false` by default
- Watch logs for request count warnings
- Use mocked API client in tests
- Disconnect signals in test setup
- Test with small datasets first
- Monitor Google Cloud Console quotas

### ❌ DON'T:
- Enable real API calls without monitoring
- Run tests against real API
- Create resources in loops without checking signal status
- Ignore warning logs about high request counts
- Assume unlimited API access

## Emergency Contacts

If you suspect runaway API usage:

1. **Stop all services immediately:**
   ```bash
   docker compose -f local.yml down
   ```

2. **Check Google Cloud Console** for current usage

3. **Review git history** for recent changes to:
   - `apps/jurisdiction/services/gemini_service.py`
   - `apps/jurisdiction/signals.py`
   - Test files

4. **Contact team lead** if quota exhausted and blocking development

## Additional Resources

- [Gemini API Pricing](https://ai.google.dev/pricing)
- [Gemini API Quotas](https://ai.google.dev/gemini-api/docs/quota)
- [Google Cloud Console](https://console.cloud.google.com/)
- [FOIA Coach API Plan](./.claude/plans/foia-coach-api.md)

---

**Last Updated:** 2025-12-11
**Created By:** Claude Code
**Purpose:** Prevent repeat of 107k request incident

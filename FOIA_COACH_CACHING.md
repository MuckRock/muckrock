# FOIA Coach - Jurisdictions Caching Implementation

## Overview
Implemented localStorage caching for the jurisdictions dropdown to improve performance and reduce API calls.

## Implementation Details

### New Files
- `foia-coach-ui/src/lib/stores/jurisdictions.svelte.ts` - Cached jurisdictions store

### Modified Files
- `foia-coach-ui/src/lib/components/QueryForm.svelte` - Uses cached store instead of direct API calls

## How It Works

1. **First Load**: Fetches jurisdictions from API and caches in localStorage
2. **Subsequent Loads**: Reads from localStorage cache (instant)
3. **Cache TTL**: 24 hours (jurisdictions don't change frequently)
4. **Automatic Refresh**: Cache expires after TTL and refetches automatically

## Storage Details

- **Storage Key**: `foia-coach-jurisdictions`
- **Cache Structure**:
  ```json
  {
    "jurisdictions": [...],
    "timestamp": 1234567890
  }
  ```
- **TTL**: 24 hours (86400000 ms)

## Store API

```typescript
import { jurisdictionsStore } from '$lib/stores/jurisdictions.svelte';

// Load jurisdictions (uses cache if available)
await jurisdictionsStore.load();

// Force reload from API
await jurisdictionsStore.reload();

// Clear cache
jurisdictionsStore.clear();

// Access data
jurisdictionsStore.jurisdictions // Jurisdiction[]
jurisdictionsStore.loading       // boolean
jurisdictionsStore.error          // string | null
```

## Benefits

1. **Faster Load Times**: Instant display from cache vs. ~500ms API call
2. **Reduced API Load**: Fewer requests to backend
3. **Offline Resilience**: Works from cache even if API is temporarily unavailable
4. **Better UX**: No loading delay on page navigation/refresh

## Console Logs

The store logs its behavior:
- `Using cached jurisdictions` - Cache hit
- `Jurisdictions cache is stale, will refetch` - Cache expired
- `Fetching jurisdictions from API...` - API call in progress
- `Cached jurisdictions to localStorage` - Cache saved

## Testing

1. **First Load**: Open browser console, visit app - see "Fetching from API"
2. **Cached Load**: Refresh page - see "Using cached jurisdictions" (instant)
3. **Expire Cache**: Wait 24 hours or clear localStorage
4. **Manual Clear**: Run `jurisdictionsStore.clear()` in console

## Future Enhancements

- Add manual refresh button in UI
- Show cache age indicator
- Make TTL configurable via settings
- Add cache versioning for schema changes

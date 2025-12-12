# SvelteKit Integration Guide: OpenAI Provider

This guide walks you through setting up OpenAI and integrating it with your SvelteKit app.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Configure OpenAI](#step-1-configure-openai)
3. [Step 2: Create OpenAI Vector Store](#step-2-create-openai-vector-store)
4. [Step 3: Upload Resources to OpenAI](#step-3-upload-resources-to-openai)
5. [Step 4: Test OpenAI Integration](#step-4-test-openai-integration)
6. [Step 5: Integrate with SvelteKit](#step-5-integrate-with-sveltekit)
7. [Step 6: Build SvelteKit Components](#step-6-build-sveltekit-components)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- OpenAI API account with credits
- FOIA Coach API running (`docker compose -f local.yml up`)
- SvelteKit app set up
- At least one jurisdiction resource ready to upload

---

## Step 1: Configure OpenAI

### 1.1 Get Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create an account
3. Navigate to API Keys: https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key (it starts with `sk-proj-...`)

### 1.2 Set Environment Variables

Add these to your `.envs/.local/.foia_coach_api` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_VECTOR_STORE_NAME=FOIA Coach Resources
OPENAI_MODEL=gpt-4o
OPENAI_REAL_API_ENABLED=true

# Set OpenAI as default provider
RAG_PROVIDER=openai
```

### 1.3 Restart Services

```bash
# Restart to pick up new environment variables
docker compose -f local.yml restart foia_coach_api
```

---

## Step 2: Create OpenAI Vector Store

The Vector Store is where OpenAI stores and indexes your documents.

```bash
# Create the vector store
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_create_store --provider=openai

# Expected output:
# Using provider: openai
# Getting or creating provider store...
# ✓ Store ready: vs_abc123xyz...
```

**What this does:**
- Creates a new Vector Store in your OpenAI account
- Names it "FOIA Coach Resources"
- Returns the store ID (starts with `vs_`)

---

## Step 3: Upload Resources to OpenAI

Now upload your jurisdiction resources to OpenAI.

### 3.1 Check Existing Resources

First, see what resources you have:

```bash
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py shell

>>> from apps.jurisdiction.models import JurisdictionResource
>>> resources = JurisdictionResource.objects.filter(is_active=True)
>>> for r in resources:
...     print(f"ID: {r.id}, State: {r.jurisdiction_abbrev}, Name: {r.display_name}, Status: {r.index_status}")
...
>>> exit()
```

### 3.2 Upload Single Resource (Test)

Upload one resource to test:

```bash
# Upload resource ID 1
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_upload_resource 1 --provider=openai

# Expected output:
# Using provider: openai
# Uploading resource 1: CO - Colorado FOIA Guide
# ✓ Successfully uploaded and indexed resource 1
```

**What this does:**
- Uploads the file to OpenAI's storage
- Adds it to the Vector Store
- Updates the resource record with `provider_file_id`
- Sets `index_status='ready'`

### 3.3 Upload All Resources

Once the test works, upload everything:

```bash
# Upload all pending resources
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all --provider=openai --all

# Expected output:
# Using provider: openai
# Syncing 5 resource(s) to openai...
#   - CO: Colorado Guide... ✓
#   - GA: Georgia Guide... ✓
#   - TX: Texas Guide... ✓
#   - NY: New York Guide... ✓
#   - CA: California Guide... ✓
#
# ✓ Sync complete: 5 successful, 0 errors
```

### 3.4 Upload Specific State

Or upload just one state:

```bash
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all --provider=openai --state=CO --all
```

---

## Step 4: Test OpenAI Integration

### 4.1 Test Provider Configuration

```bash
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider --provider=openai

# Expected output:
# Testing provider: openai
# ============================================================
#
# 1. Validating configuration...
#    ✓ Configuration valid
#
# 2. Creating provider instance...
#    ✓ Provider created: openai
#
# 3. Checking provider info...
#    Provider: openai
#    Model: gpt-4o
#    API Enabled: True
#    API Key: sk-proj-ab...
#
# 4. Testing store access...
#    ✓ Store accessible: vs_abc123xyz...
#
# ✓ Provider openai is working correctly!
```

### 4.2 Test Query

```bash
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_query \
    "What is the FOIA response deadline in Colorado?" \
    --state=CO \
    --provider=openai

# Expected output:
# Provider: openai
# Question: What is the FOIA response deadline in Colorado?
# State filter: CO
#
# Answer:
# ------------------------------------------------------------
# In Colorado, agencies must respond to FOIA requests within
# 3 business days of receiving the request...
# ------------------------------------------------------------
#
# Citations:
#   [1] Colorado FOIA Guide
#       colorado_guide.pdf
#
# ✓ Query complete
```

### 4.3 Test Streaming Query

```bash
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_query \
    "Explain the FOIA appeal process" \
    --state=CO \
    --provider=openai \
    --stream
```

---

## Step 5: Integrate with SvelteKit

### 5.1 Create API Client

Create `src/lib/api/foiaCoach.ts`:

```typescript
// src/lib/api/foiaCoach.ts

const FOIA_COACH_API_URL = 'http://localhost:8001/api/v1';

export interface QueryRequest {
  question: string;
  state?: string;
  provider?: 'openai' | 'gemini' | 'mock';
  model?: string;
  context?: Record<string, any>;
}

export interface Citation {
  display_name: string;
  source: string;
  jurisdiction_abbrev?: string;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  provider: string;
  model: string;
  state?: string;
}

export interface ProviderStatus {
  current_provider: string;
  available_providers: string[];
  api_status: {
    openai: 'enabled' | 'disabled';
    gemini: 'enabled' | 'disabled';
    mock: 'always_enabled';
  };
  status: string;
  message: string;
}

export interface Resource {
  id: number;
  jurisdiction_id: number;
  jurisdiction_abbrev: string;
  jurisdiction_name: string;
  display_name: string;
  description: string;
  resource_type: string;
  provider: string;
  index_status: 'pending' | 'ready' | 'error';
  indexed_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  file_url: string;
  order: number;
}

export interface ResourceListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Resource[];
}

class FOIACoachClient {
  private baseUrl: string;

  constructor(baseUrl: string = FOIA_COACH_API_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Get provider status
   */
  async getStatus(): Promise<ProviderStatus> {
    const response = await fetch(`${this.baseUrl}/query/status/`);
    if (!response.ok) {
      throw new Error(`Failed to get status: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Execute a RAG query
   */
  async query(request: QueryRequest): Promise<QueryResponse> {
    const response = await fetch(`${this.baseUrl}/query/query/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Query failed');
    }

    return response.json();
  }

  /**
   * List resources
   */
  async listResources(params?: {
    state?: string;
    provider?: string;
    index_status?: string;
  }): Promise<ResourceListResponse> {
    const url = new URL(`${this.baseUrl}/resources/`);

    if (params?.state) {
      url.searchParams.set('jurisdiction_abbrev', params.state);
    }
    if (params?.provider) {
      url.searchParams.set('provider', params.provider);
    }
    if (params?.index_status) {
      url.searchParams.set('index_status', params.index_status);
    }

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`Failed to list resources: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get single resource
   */
  async getResource(id: number): Promise<Resource> {
    const response = await fetch(`${this.baseUrl}/resources/${id}/`);
    if (!response.ok) {
      throw new Error(`Failed to get resource: ${response.statusText}`);
    }
    return response.json();
  }
}

// Export singleton instance
export const foiaCoach = new FOIACoachClient();

// Export class for custom instances
export { FOIACoachClient };
```

### 5.2 Create Environment Configuration

Add to your `.env` or `.env.local`:

```bash
# SvelteKit Environment Variables
PUBLIC_FOIA_COACH_API_URL=http://localhost:8001/api/v1
```

Update the client to use environment variables:

```typescript
// src/lib/api/foiaCoach.ts
import { PUBLIC_FOIA_COACH_API_URL } from '$env/static/public';

const FOIA_COACH_API_URL = PUBLIC_FOIA_COACH_API_URL || 'http://localhost:8001/api/v1';
```

---

## Step 6: Build SvelteKit Components

### 6.1 Query Form Component

Create `src/lib/components/FOIAQueryForm.svelte`:

```svelte
<script lang="ts">
  import { foiaCoach, type QueryResponse } from '$lib/api/foiaCoach';

  // Props
  export let initialState: string = '';

  // State
  let question = '';
  let selectedState = initialState;
  let selectedProvider: 'openai' | 'gemini' | 'mock' = 'openai';
  let loading = false;
  let result: QueryResponse | null = null;
  let error: string | null = null;

  // US States (abbreviated list - add all 50)
  const states = [
    { abbrev: 'CO', name: 'Colorado' },
    { abbrev: 'GA', name: 'Georgia' },
    { abbrev: 'TX', name: 'Texas' },
    { abbrev: 'NY', name: 'New York' },
    { abbrev: 'CA', name: 'California' },
    // Add more states...
  ];

  async function handleSubmit() {
    if (!question.trim()) {
      error = 'Please enter a question';
      return;
    }

    loading = true;
    error = null;
    result = null;

    try {
      result = await foiaCoach.query({
        question: question.trim(),
        state: selectedState || undefined,
        provider: selectedProvider,
      });
    } catch (e) {
      error = e instanceof Error ? e.message : 'Query failed';
    } finally {
      loading = false;
    }
  }

  function reset() {
    question = '';
    selectedState = initialState;
    result = null;
    error = null;
  }
</script>

<div class="foia-query-form">
  <h2>Ask a FOIA Question</h2>

  <form on:submit|preventDefault={handleSubmit}>
    <!-- Question Input -->
    <div class="form-group">
      <label for="question">Your Question</label>
      <textarea
        id="question"
        bind:value={question}
        placeholder="What is the FOIA response deadline?"
        rows="3"
        disabled={loading}
      />
    </div>

    <!-- State Filter -->
    <div class="form-group">
      <label for="state">State (Optional)</label>
      <select id="state" bind:value={selectedState} disabled={loading}>
        <option value="">All States</option>
        {#each states as state}
          <option value={state.abbrev}>{state.name} ({state.abbrev})</option>
        {/each}
      </select>
    </div>

    <!-- Provider Selection -->
    <div class="form-group">
      <label for="provider">AI Provider</label>
      <select id="provider" bind:value={selectedProvider} disabled={loading}>
        <option value="openai">OpenAI (GPT-4)</option>
        <option value="gemini">Google Gemini</option>
        <option value="mock">Mock (Testing)</option>
      </select>
    </div>

    <!-- Submit Button -->
    <div class="form-actions">
      <button type="submit" disabled={loading || !question.trim()}>
        {loading ? 'Thinking...' : 'Ask Question'}
      </button>

      {#if result || error}
        <button type="button" on:click={reset}>
          Ask Another Question
        </button>
      {/if}
    </div>
  </form>

  <!-- Error Display -->
  {#if error}
    <div class="error-message">
      <strong>Error:</strong> {error}
    </div>
  {/if}

  <!-- Result Display -->
  {#if result}
    <div class="result">
      <div class="result-header">
        <h3>Answer</h3>
        <div class="result-meta">
          <span class="badge">{result.provider}</span>
          <span class="badge">{result.model}</span>
          {#if result.state}
            <span class="badge">{result.state}</span>
          {/if}
        </div>
      </div>

      <div class="answer">
        {result.answer}
      </div>

      {#if result.citations.length > 0}
        <div class="citations">
          <h4>Sources</h4>
          <ul>
            {#each result.citations as citation, i}
              <li>
                <strong>[{i + 1}]</strong>
                {citation.display_name}
                {#if citation.jurisdiction_abbrev}
                  <span class="state-badge">{citation.jurisdiction_abbrev}</span>
                {/if}
                <br />
                <small>{citation.source}</small>
              </li>
            {/each}
          </ul>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .foia-query-form {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  textarea,
  select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
  }

  textarea:focus,
  select:focus {
    outline: none;
    border-color: #4a90e2;
  }

  .form-actions {
    display: flex;
    gap: 1rem;
  }

  button {
    padding: 0.75rem 1.5rem;
    background: #4a90e2;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.2s;
  }

  button:hover:not(:disabled) {
    background: #357abd;
  }

  button:disabled {
    background: #ccc;
    cursor: not-allowed;
  }

  button[type='button'] {
    background: #6c757d;
  }

  button[type='button']:hover {
    background: #545b62;
  }

  .error-message {
    padding: 1rem;
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    margin-top: 1rem;
  }

  .result {
    margin-top: 2rem;
    padding: 1.5rem;
    background: #f8f9fa;
    border-radius: 4px;
  }

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .result-meta {
    display: flex;
    gap: 0.5rem;
  }

  .badge {
    padding: 0.25rem 0.75rem;
    background: #e9ecef;
    color: #495057;
    border-radius: 12px;
    font-size: 0.875rem;
  }

  .answer {
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }

  .citations {
    border-top: 1px solid #dee2e6;
    padding-top: 1rem;
  }

  .citations h4 {
    margin-bottom: 1rem;
    color: #495057;
  }

  .citations ul {
    list-style: none;
    padding: 0;
  }

  .citations li {
    padding: 0.75rem;
    background: white;
    border-radius: 4px;
    margin-bottom: 0.5rem;
  }

  .state-badge {
    display: inline-block;
    padding: 0.125rem 0.5rem;
    background: #4a90e2;
    color: white;
    border-radius: 8px;
    font-size: 0.75rem;
    margin-left: 0.5rem;
  }

  small {
    color: #6c757d;
  }
</style>
```

### 6.2 Use in a Page

Create or update `src/routes/+page.svelte`:

```svelte
<script lang="ts">
  import FOIAQueryForm from '$lib/components/FOIAQueryForm.svelte';
</script>

<div class="container">
  <header>
    <h1>FOIA Coach</h1>
    <p>Get AI-powered answers to your Freedom of Information Act questions</p>
  </header>

  <main>
    <FOIAQueryForm />
  </main>
</div>

<style>
  .container {
    min-height: 100vh;
    padding: 2rem;
  }

  header {
    text-align: center;
    margin-bottom: 3rem;
  }

  h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }

  p {
    color: #6c757d;
    font-size: 1.125rem;
  }
</style>
```

### 6.3 Add Provider Status Indicator

Create `src/lib/components/ProviderStatus.svelte`:

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { foiaCoach, type ProviderStatus } from '$lib/api/foiaCoach';

  let status: ProviderStatus | null = null;
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      status = await foiaCoach.getStatus();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load status';
    } finally {
      loading = false;
    }
  });
</script>

{#if loading}
  <div class="status-indicator loading">Checking provider status...</div>
{:else if error}
  <div class="status-indicator error">
    <span class="icon">⚠️</span>
    API Unavailable
  </div>
{:else if status}
  <div class="status-indicator">
    <span class="icon">✓</span>
    Using <strong>{status.current_provider}</strong>
    <span class="api-status" class:enabled={status.api_status.openai === 'enabled'}>
      OpenAI: {status.api_status.openai}
    </span>
  </div>
{/if}

<style>
  .status-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: #e7f5e7;
    border-radius: 4px;
    font-size: 0.875rem;
  }

  .status-indicator.loading {
    background: #fff3cd;
  }

  .status-indicator.error {
    background: #f8d7da;
  }

  .icon {
    font-size: 1.25rem;
  }

  .api-status {
    margin-left: auto;
    padding: 0.25rem 0.75rem;
    background: #f8d7da;
    border-radius: 12px;
    text-transform: capitalize;
  }

  .api-status.enabled {
    background: #d4edda;
    color: #155724;
  }
</style>
```

---

## Troubleshooting

### Issue: "API Key Invalid"

**Error:** `Authentication failed` or `Invalid API key`

**Solution:**
1. Verify your API key is correct
2. Check it's properly set in `.envs/.local/.foia_coach_api`
3. Restart the service: `docker compose -f local.yml restart foia_coach_api`
4. Test: `docker compose -f local.yml run --rm foia_coach_api python manage.py test_rag_provider --provider=openai`

### Issue: "API Calls Disabled"

**Error:** `OpenAI API calls are disabled`

**Solution:**
1. Set `OPENAI_REAL_API_ENABLED=true` in your environment file
2. Restart services
3. Verify: Check `/api/v1/query/status/` shows `openai: enabled`

### Issue: "No Resources Found"

**Error:** Query returns empty or says no citations

**Solution:**
1. Check resources are uploaded: `docker compose -f local.yml run --rm foia_coach_api python manage.py shell`
   ```python
   from apps.jurisdiction.models import JurisdictionResource
   JurisdictionResource.objects.filter(provider='openai', index_status='ready').count()
   ```
2. If 0, upload resources: `python manage.py gemini_sync_all --provider=openai --all`

### Issue: CORS Errors in Browser

**Error:** `Access to fetch at 'http://localhost:8001' from origin 'http://localhost:5173' has been blocked by CORS`

**Solution:**
Add CORS headers to Django settings:

```python
# In config/settings/base.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # SvelteKit dev server
    "http://localhost:3000",  # Alternative port
]

# Or for development only:
CORS_ALLOW_ALL_ORIGINS = True  # Only for local development!
```

### Issue: Slow Queries

**Symptom:** Queries take 10+ seconds

**Solutions:**
1. Use streaming for better UX (implement in SvelteKit with Server-Sent Events)
2. Switch to `gpt-4o-mini` for faster responses:
   ```bash
   export OPENAI_MODEL=gpt-4o-mini
   ```
3. Add caching layer in your SvelteKit app for repeated questions

### Issue: High Costs

**Symptom:** OpenAI bills are high

**Solutions:**
1. Monitor usage in OpenAI dashboard
2. Use `gpt-4o-mini` instead of `gpt-4o` (10x cheaper)
3. Implement rate limiting in your SvelteKit app
4. Cache responses for common questions
5. Switch to Gemini for cost-effective alternative

---

## Next Steps

1. ✅ OpenAI configured and tested
2. ✅ Resources uploaded
3. ✅ SvelteKit integrated
4. 🔲 Add streaming support for real-time responses
5. 🔲 Implement response caching
6. 🔲 Add analytics to track popular questions
7. 🔲 Build admin interface for managing resources
8. 🔲 Add user authentication

## Additional Resources

- [OpenAI Platform Documentation](https://platform.openai.com/docs)
- [Vector Stores Guide](https://platform.openai.com/docs/assistants/tools/file-search)
- [SvelteKit Documentation](https://kit.svelte.dev/)
- [FOIA Coach README](./README.md)
- [Usage Examples](./USAGE_EXAMPLES.md)

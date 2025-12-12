# FOIA Coach API - Usage Examples

This document provides practical examples for using the FOIA Coach API with different RAG providers.

## Table of Contents

- [Getting Started](#getting-started)
- [Provider Selection](#provider-selection)
- [Management Commands](#management-commands)
- [API Usage](#api-usage)
- [Python Client Examples](#python-client-examples)
- [Advanced Usage](#advanced-usage)

## Getting Started

### Basic Setup

```bash
# Start the services
docker compose -f local.yml up foia_coach_api

# In a new terminal, check provider status
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider --list
```

Output:
```
Available RAG Providers:
  - openai (current)
  - gemini
  - mock

Current provider: openai
```

## Provider Selection

### Using Default Provider

The default provider is set via `RAG_PROVIDER` environment variable:

```bash
# Use OpenAI (default)
export RAG_PROVIDER=openai

# Use Gemini
export RAG_PROVIDER=gemini

# Use Mock for testing
export RAG_PROVIDER=mock
```

### Per-Request Provider Selection

Override the default provider for specific requests:

```bash
# Command line
python manage.py gemini_query "What is the deadline?" --provider=gemini

# API
curl -X POST http://localhost:8001/api/v1/query/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the deadline?", "provider": "openai"}'
```

## Management Commands

### Testing Provider Configuration

```bash
# Test default provider
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider

# Test specific provider
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider --provider=openai

# Test all providers
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider --all

# Test with a query
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider \
    --provider=openai \
    --query="What are the FOIA fees in Texas?"
```

### Creating Provider Stores

```bash
# Create store with default provider
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_create_store

# Create store with specific provider
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_create_store --provider=openai

# Create store with custom name
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_create_store \
    --provider=openai \
    --name="FOIA Coach Production Store"
```

### Uploading Resources

```bash
# Upload single resource (default provider)
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_upload_resource 1

# Upload with specific provider
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_upload_resource 1 --provider=openai

# Force re-upload
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_upload_resource 1 --provider=openai --force
```

### Syncing Multiple Resources

```bash
# Sync pending resources (default provider)
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all

# Sync with specific provider
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all --provider=openai

# Sync all resources (not just pending)
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all --provider=openai --all

# Sync specific state
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all --provider=openai --state=CO

# Sync all Colorado resources to both providers
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all --provider=openai --state=CO --all

docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_sync_all --provider=gemini --state=CO --all
```

### Querying the System

```bash
# Simple query (default provider)
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_query "What is the FOIA deadline?"

# Query with state filter
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_query \
    "What is the response deadline?" \
    --state=CO

# Query with specific provider
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_query \
    "What are the exemptions?" \
    --state=GA \
    --provider=openai

# Streaming query
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_query \
    "Explain the FOIA process" \
    --stream \
    --provider=openai
```

## API Usage

### Check Provider Status

```bash
curl http://localhost:8001/api/v1/query/status/
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

### Basic Query

```bash
curl -X POST http://localhost:8001/api/v1/query/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the response time in Colorado?"
  }'
```

Response:
```json
{
  "answer": "In Colorado, agencies must respond to FOIA requests within 3 business days...",
  "citations": [
    {
      "display_name": "Colorado FOIA Guide",
      "source": "colorado_guide.pdf",
      "jurisdiction_abbrev": "CO"
    }
  ],
  "provider": "openai",
  "model": "gpt-4o",
  "state": null
}
```

### Query with State Filter

```bash
curl -X POST http://localhost:8001/api/v1/query/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the FOIA fees?",
    "state": "TX"
  }'
```

### Query with Provider Selection

```bash
# Use Gemini
curl -X POST http://localhost:8001/api/v1/query/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the exemptions?",
    "state": "GA",
    "provider": "gemini"
  }'

# Use OpenAI with specific model
curl -X POST http://localhost:8001/api/v1/query/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain the appeal process",
    "state": "CO",
    "provider": "openai",
    "model": "gpt-4o"
  }'
```

### List Resources

```bash
# Get all resources
curl http://localhost:8001/api/v1/resources/

# Filter by state
curl http://localhost:8001/api/v1/resources/?jurisdiction_abbrev=CO

# Filter by provider
curl http://localhost:8001/api/v1/resources/?provider=openai

# Filter by index status
curl http://localhost:8001/api/v1/resources/?index_status=ready
```

## Python Client Examples

### Basic Query Client

```python
import requests

class FOIACoachClient:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"

    def query(self, question, state=None, provider=None, model=None):
        """Execute a RAG query."""
        url = f"{self.api_url}/query/query/"
        data = {
            "question": question,
            "state": state,
            "provider": provider,
            "model": model
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def get_status(self):
        """Get provider status."""
        url = f"{self.api_url}/query/status/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def list_resources(self, state=None, provider=None):
        """List available resources."""
        url = f"{self.api_url}/resources/"
        params = {}
        if state:
            params['jurisdiction_abbrev'] = state
        if provider:
            params['provider'] = provider

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

# Usage
client = FOIACoachClient()

# Check status
status = client.get_status()
print(f"Current provider: {status['current_provider']}")

# Query with default provider
result = client.query(
    question="What is the FOIA deadline in Colorado?",
    state="CO"
)
print(f"Answer: {result['answer']}")
print(f"Provider: {result['provider']}")

# Query with specific provider
result = client.query(
    question="What are the exemptions?",
    state="GA",
    provider="gemini"
)
print(f"Answer: {result['answer']}")
```

### Comparing Providers

```python
def compare_providers(question, state=None):
    """Compare answers from different providers."""
    client = FOIACoachClient()
    providers = ['openai', 'gemini']

    results = {}
    for provider in providers:
        try:
            result = client.query(
                question=question,
                state=state,
                provider=provider
            )
            results[provider] = {
                'answer': result['answer'],
                'citations': len(result.get('citations', [])),
                'model': result.get('model')
            }
        except Exception as e:
            results[provider] = {'error': str(e)}

    return results

# Usage
comparison = compare_providers(
    "What is the response deadline?",
    state="CO"
)

for provider, result in comparison.items():
    print(f"\n{provider.upper()}:")
    if 'error' in result:
        print(f"  Error: {result['error']}")
    else:
        print(f"  Model: {result['model']}")
        print(f"  Citations: {result['citations']}")
        print(f"  Answer: {result['answer'][:100]}...")
```

### Batch Processing

```python
def batch_upload_resources(resource_ids, provider='openai'):
    """Upload multiple resources."""
    import subprocess

    results = []
    for resource_id in resource_ids:
        cmd = [
            'docker', 'compose', '-f', 'local.yml',
            'run', '--rm', 'foia_coach_api',
            'python', 'manage.py', 'gemini_upload_resource',
            str(resource_id),
            '--provider', provider
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            results.append({
                'resource_id': resource_id,
                'success': True,
                'output': result.stdout
            })
        except subprocess.CalledProcessError as e:
            results.append({
                'resource_id': resource_id,
                'success': False,
                'error': e.stderr
            })

    return results

# Usage
resource_ids = [1, 2, 3, 4, 5]
results = batch_upload_resources(resource_ids, provider='openai')

for result in results:
    status = "✓" if result['success'] else "✗"
    print(f"{status} Resource {result['resource_id']}")
```

## Advanced Usage

### Provider Failover

```python
def query_with_failover(question, state=None, providers=None):
    """Try multiple providers until one succeeds."""
    if providers is None:
        providers = ['openai', 'gemini', 'mock']

    client = FOIACoachClient()

    for provider in providers:
        try:
            result = client.query(
                question=question,
                state=state,
                provider=provider
            )
            return result
        except Exception as e:
            print(f"Provider {provider} failed: {e}")
            continue

    raise Exception("All providers failed")

# Usage
try:
    result = query_with_failover(
        "What is the deadline?",
        state="CO",
        providers=['openai', 'gemini']
    )
    print(f"Answered by: {result['provider']}")
except Exception as e:
    print(f"Error: {e}")
```

### Monitoring Provider Performance

```python
import time

def benchmark_provider(provider, question, iterations=5):
    """Benchmark provider performance."""
    client = FOIACoachClient()
    times = []

    for i in range(iterations):
        start = time.time()
        try:
            result = client.query(question=question, provider=provider)
            elapsed = time.time() - start
            times.append(elapsed)
        except Exception as e:
            print(f"Error in iteration {i+1}: {e}")

    if times:
        return {
            'provider': provider,
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'iterations': len(times)
        }
    return None

# Usage
question = "What is the FOIA deadline?"

openai_stats = benchmark_provider('openai', question)
gemini_stats = benchmark_provider('gemini', question)

print(f"OpenAI: {openai_stats['avg_time']:.2f}s average")
print(f"Gemini: {gemini_stats['avg_time']:.2f}s average")
```

### Bulk State Migration

```python
def migrate_state_to_provider(state, from_provider, to_provider):
    """Migrate all resources for a state to a new provider."""
    import subprocess

    # Get resources for state
    client = FOIACoachClient()
    resources = client.list_resources(state=state, provider=from_provider)

    print(f"Migrating {len(resources['results'])} resources from {from_provider} to {to_provider}")

    # Upload each resource to new provider
    for resource in resources['results']:
        resource_id = resource['id']
        cmd = [
            'docker', 'compose', '-f', 'local.yml',
            'run', '--rm', 'foia_coach_api',
            'python', 'manage.py', 'gemini_upload_resource',
            str(resource_id),
            '--provider', to_provider,
            '--force'
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✓ Migrated resource {resource_id}")
        except Exception as e:
            print(f"✗ Failed to migrate resource {resource_id}: {e}")

# Usage
migrate_state_to_provider('CO', from_provider='gemini', to_provider='openai')
```

## Testing Examples

### Unit Test with MockProvider

```python
from django.test import TestCase
from apps.jurisdiction.services.providers.helpers import get_provider

class TestFOIAQuery(TestCase):
    def test_query_with_mock_provider(self):
        """Test query with MockProvider (no API calls)."""
        provider = get_provider('mock')

        result = provider.query(
            question="What is the deadline?",
            state="CO"
        )

        self.assertIn('answer', result)
        self.assertIn('citations', result)
        self.assertEqual(result['provider'], 'mock')
        self.assertIsInstance(result['citations'], list)
```

### Integration Test

```python
from django.test import TestCase
from apps.jurisdiction import factories
from apps.jurisdiction.services.providers.helpers import get_provider

class TestResourceUpload(TestCase):
    def test_upload_with_mock_provider(self):
        """Test resource upload with MockProvider."""
        # Create test resource
        resource = factories.JurisdictionResourceFactory(
            jurisdiction_id=1,
            jurisdiction_abbrev='CO',
            provider='mock',
            index_status='pending'
        )

        # Upload
        provider = get_provider('mock')
        result = provider.upload_resource(resource)

        # Verify
        self.assertIn('file_id', result)
        self.assertIn('store_id', result)

        resource.refresh_from_db()
        self.assertEqual(resource.index_status, 'ready')
```

## Troubleshooting Examples

### Debug Provider Configuration

```bash
# Check configuration
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py shell

>>> from apps.jurisdiction.services.providers.helpers import get_provider
>>> provider = get_provider('openai')
>>> info = provider.get_info()
>>> print(info)
```

### Test Connectivity

```bash
# Test if provider is reachable
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider --provider=openai

# Test with actual query
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider \
    --provider=openai \
    --query="Test connectivity"
```

### Check Resource Status

```bash
# List resources by status
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py shell

>>> from apps.jurisdiction.models import JurisdictionResource
>>>
>>> # Pending resources
>>> pending = JurisdictionResource.objects.filter(index_status='pending')
>>> print(f"Pending: {pending.count()}")
>>>
>>> # Ready resources by provider
>>> for provider in ['openai', 'gemini']:
...     count = JurisdictionResource.objects.filter(
...         provider=provider,
...         index_status='ready'
...     ).count()
...     print(f"{provider}: {count}")
```

## Additional Resources

- [README.md](./README.md) - Complete documentation
- [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - Migration instructions
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - Full API reference

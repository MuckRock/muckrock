# FOIA Coach API Documentation

## Overview

The FOIA Coach API provides access to jurisdiction-specific FOIA resources and RAG-powered query capabilities using Gemini File Search.

**Base URL:** `http://localhost:8001/api/v1/`

**Architecture:**
- Standalone Django service (port 8001)
- Separate PostgreSQL database (`foia_coach`)
- Integrates with main MuckRock API for jurisdiction data
- Uses Google Gemini File Search for RAG queries

---

## Authentication

**Current Status:** No authentication required (experimental phase)

**Future:** Authentication will be added after SvelteKit UI development.

---

## Endpoints

### 1. List Jurisdictions

Fetch all state-level jurisdictions from the main MuckRock API.

**Endpoint:** `GET /api/v1/jurisdictions/`

**Response:**
```json
{
  "count": 50,
  "results": [
    {
      "id": 127,
      "name": "Colorado",
      "slug": "colorado",
      "abbrev": "CO",
      "level": "s",
      "resource_count": 1
    }
  ]
}
```

**Fields:**
- `id` - Jurisdiction ID from main MuckRock database
- `name` - Full jurisdiction name
- `slug` - URL-friendly identifier
- `abbrev` - State abbreviation (e.g., "CO", "GA", "TN")
- `level` - Jurisdiction level ("s" for state)
- `resource_count` - Number of active resources for this jurisdiction

---

### 2. Get Single Jurisdiction

Retrieve details for a specific jurisdiction by abbreviation.

**Endpoint:** `GET /api/v1/jurisdictions/{abbrev}/`

**Example:** `GET /api/v1/jurisdictions/CO/`

**Response:**
```json
{
  "id": 127,
  "name": "Colorado",
  "slug": "colorado",
  "abbrev": "CO",
  "level": "s",
  "resource_count": 1
}
```

---

### 3. List Resources

Fetch jurisdiction resources (FOIA guides, exemptions, case law, etc.).

**Endpoint:** `GET /api/v1/resources/`

**Query Parameters:**
- `jurisdiction_id` - Filter by jurisdiction ID
- `jurisdiction_abbrev` - Filter by state abbreviation (e.g., `?jurisdiction_abbrev=CO`)
- `resource_type` - Filter by type (`law_guide`, `request_tips`, `exemptions`, etc.)
- `index_status` - Filter by indexing status (`pending`, `uploading`, `indexing`, `ready`, `error`)
- `is_active` - Filter by active status (default: `true`)
- `ordering` - Sort results (e.g., `?ordering=created_at`, `?ordering=-updated_at`)

**Example:** `GET /api/v1/resources/?jurisdiction_abbrev=CO&resource_type=law_guide`

**Response:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "jurisdiction_id": 127,
      "jurisdiction_abbrev": "CO",
      "jurisdiction_name": "Colorado",
      "display_name": "Colorado Open Records Act (CORA) Guide",
      "description": "Comprehensive guide to making FOIA requests in Colorado under CORA",
      "resource_type": "law_guide",
      "index_status": "ready",
      "indexed_at": "2025-12-10T16:06:03.054566Z",
      "is_active": true,
      "created_at": "2025-12-10T16:06:00.527746Z",
      "updated_at": "2025-12-10T16:06:00.527772Z",
      "file_url": "http://localhost:8001/media/foia_coach/jurisdiction_resources/2025/12/colorado_cora_guide.md",
      "order": 1
    }
  ]
}
```

**Resource Types:**
- `law_guide` - State FOIA law guides
- `request_tips` - Tips for making effective requests
- `exemptions` - Exemptions guides
- `agency_info` - Agency-specific information
- `case_law` - Relevant case law
- `general` - General information

**Index Status:**
- `pending` - Waiting to be uploaded to Gemini
- `uploading` - Currently uploading
- `indexing` - Being indexed by Gemini
- `ready` - Ready for queries
- `error` - Upload/indexing failed

---

### 4. Get Single Resource

Retrieve details for a specific resource.

**Endpoint:** `GET /api/v1/resources/{id}/`

**Example:** `GET /api/v1/resources/1/`

**Response:** Same as single item in list response above.

---

### 5. RAG Query

Execute a natural language query against indexed jurisdiction resources using Gemini File Search.

**Endpoint:** `POST /api/v1/query/query/`

**Request Body:**
```json
{
  "question": "What is the response time for FOIA requests in Colorado?",
  "state": "CO",
  "context": {},
  "model": "gemini-2.0-flash-exp"
}
```

**Fields:**
- `question` (required) - Natural language question
- `state` (optional) - State abbreviation to scope the query
- `context` (optional) - Additional context as JSON object
- `model` (optional) - Gemini model to use (default: `gemini-2.0-flash-exp`)

**Response:**
```json
{
  "answer": "In Colorado, agencies must respond within 3 business days to acknowledge receipt and provide a timeline. The actual records should be produced 'as soon as practicable,' typically within 7 business days.",
  "citations": [
    {
      "document_name": "co-colorado-open-records-ac-2xlly8gvdt78",
      "display_name": "CO - Colorado Open Records Act (CORA) Guide",
      "relevance_score": 0.95
    }
  ],
  "state": "CO"
}
```

**Error Response:**
```json
{
  "error": "Query failed: <error message>",
  "question": "What is the response time in Colorado?",
  "state": "CO"
}
```

**Notes:**
- Queries are rate-limited by Gemini API quotas
- Only queries resources with `index_status: "ready"`
- Citations include source documents used to generate the answer

---

## CORS Configuration

The API is configured to accept requests from the following origins:

- `http://localhost:5173` (SvelteKit dev server)
- `http://127.0.0.1:5173`

**Credentials:** CORS credentials are enabled (`Access-Control-Allow-Credentials: true`)

---

## Management Commands

The following Django management commands are available for administration:

### Create/Verify Gemini Store
```bash
docker compose -f local.yml exec foia_coach_api python manage.py gemini_create_store
```

### Upload Single Resource
```bash
docker compose -f local.yml exec foia_coach_api python manage.py gemini_upload_resource <resource_id>
```

### Sync All Resources
```bash
docker compose -f local.yml exec foia_coach_api python manage.py gemini_sync_all
```

Options:
- `--state CO` - Only sync resources for specific state
- `--resource-type law_guide` - Only sync specific resource type
- `--force` - Re-upload resources even if already indexed

### Test Query
```bash
docker compose -f local.yml exec foia_coach_api python manage.py gemini_query "What is the response time in Colorado?" --state CO
```

---

## Testing the API

### Using curl

**List jurisdictions:**
```bash
curl http://localhost:8001/api/v1/jurisdictions/ | python3 -m json.tool
```

**Get Colorado resources:**
```bash
curl http://localhost:8001/api/v1/resources/?jurisdiction_abbrev=CO | python3 -m json.tool
```

**Submit query:**
```bash
curl -X POST http://localhost:8001/api/v1/query/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the response time in Colorado?", "state": "CO"}' \
  | python3 -m json.tool
```

### Using Python

```python
import requests

# List jurisdictions
response = requests.get('http://localhost:8001/api/v1/jurisdictions/')
jurisdictions = response.json()

# Get Colorado resources
response = requests.get('http://localhost:8001/api/v1/resources/', params={'jurisdiction_abbrev': 'CO'})
resources = response.json()

# Submit query
response = requests.post('http://localhost:8001/api/v1/query/query/', json={
    'question': 'What is the response time in Colorado?',
    'state': 'CO'
})
query_result = response.json()
print(query_result['answer'])
```

---

## Database

**Separate Database:** The FOIA Coach API uses its own PostgreSQL database (`foia_coach`), completely isolated from the main MuckRock database.

**Connection Details:**
- Host: `foia_coach_postgres` (Docker network) / `localhost:5433` (from host)
- Database: `foia_coach`
- User: `foia_coach_user`

**Tables:**
- `foia_coach_jurisdictionresource` - Jurisdiction-specific FOIA resources
- Django core tables (auth, sessions, etc.)

**Note:** Jurisdiction data is fetched from the main MuckRock API, not stored locally.

---

## Known Issues & Limitations

### Current Limitations

1. **No Authentication:** API is open for experimental phase. Authentication will be added later.

2. **Gemini API Quotas:** Free tier has limited requests:
   - 50 requests per day
   - 2 requests per minute
   - Quota exceeded errors return HTTP 500

3. **Single Store:** All resources are indexed in one Gemini File Search store. Future versions may use per-state stores.

4. **Supported File Types:** The service automatically detects and handles multiple file formats:
   - **Text formats:** `.txt`, `.md`, `.markdown`
   - **PDF documents:** `.pdf`
   - **Microsoft Word:** `.docx`, `.doc`
   - **Microsoft Excel:** `.xlsx`, `.xls`
   - **Microsoft PowerPoint:** `.pptx`, `.ppt`
   - **CSV files:** `.csv`
   - **Unknown formats:** Default to `text/plain`

   MIME types are automatically detected from file extensions.

### Troubleshooting

**Issue:** API returns empty results
- **Solution:** Check that resources exist and have `is_active=True` and `index_status='ready'`

**Issue:** Jurisdiction endpoint returns 503
- **Solution:** Ensure main MuckRock Django service is running on port 8000

**Issue:** Query endpoint returns 500
- **Solution:** Check Gemini API quota limits and verify resources are indexed

**Issue:** CORS errors in browser
- **Solution:** Ensure SvelteKit dev server is on port 5173, or update CORS settings

---

## Future Enhancements

- [ ] Add authentication (token-based or JWT)
- [ ] Per-state Gemini stores for better query scoping
- [ ] Support for PDF and other document types
- [ ] Bulk upload API for resources
- [ ] Webhooks for indexing status updates
- [ ] Query history and analytics
- [ ] Caching layer for frequent queries
- [ ] Rate limiting per user/token

---

## Support

For issues or questions:
- GitHub: https://github.com/MuckRock/muckrock
- Check logs: `docker compose -f local.yml logs foia_coach_api`
- Admin interface: http://localhost:8001/admin/

---

**Last Updated:** 2025-12-10
**API Version:** Experimental (Pre-1.0)

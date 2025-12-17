# Batch Import Guide - PDF Resources

This guide walks you through batch-importing PDF resources for a jurisdiction (e.g., Tennessee) and uploading them to the OpenAI provider.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Step 1: Prepare Your PDF Files](#step-1-prepare-your-pdf-files)
- [Step 2: Create JurisdictionResource Records](#step-2-create-jurisdictionresource-records)
  - [Option A: Django Admin Interface](#option-a-django-admin-interface-recommended-for-small-batches)
  - [Option B: Django Shell Script](#option-b-django-shell-script-recommended-for-batch-imports)
  - [Option C: Management Command](#option-c-management-command-for-programmatic-imports)
- [Step 3: Upload to OpenAI Provider](#step-3-upload-to-openai-provider)
- [Step 4: Verify Upload Status](#step-4-verify-upload-status)
- [Troubleshooting](#troubleshooting)

## Overview

The batch import process consists of three main steps:
1. **Prepare** your PDF files in a local directory
2. **Create** JurisdictionResource records for each PDF
3. **Upload** the resources to the OpenAI provider

## Prerequisites

Before starting, ensure:

1. **Services are running:**
   ```bash
   docker compose -f local.yml up foia_coach_api
   ```

2. **OpenAI provider is configured:**
   ```bash
   # Check your .envs/.local/.foia_coach_api file contains:
   export OPENAI_API_KEY=sk-...
   export OPENAI_REAL_API_ENABLED=true
   export RAG_PROVIDER=openai
   ```

3. **OpenAI vector store exists:**
   ```bash
   docker compose -f local.yml run --rm foia_coach_api \
     python manage.py gemini_create_store --provider=openai
   ```

4. **Know your jurisdiction details:**
   - **jurisdiction_id**: The ID from the main MuckRock jurisdiction table (e.g., 155 for Tennessee)
   - **jurisdiction_abbrev**: State abbreviation (e.g., "TN" for Tennessee)

## Step 1: Prepare Your PDF Files

Organize your PDFs in a local directory with descriptive names:

```bash
/path/to/tennessee-pdfs/
├── TN_FOIA_Law_Guide_2024.pdf
├── TN_Request_Tips.pdf
├── TN_Exemptions_Guide.pdf
├── TN_Agency_Directory.pdf
└── TN_Common_Denials.pdf
```

**Naming Convention (Recommended):**
- Use clear, descriptive names
- Include the state abbreviation prefix
- Use underscores instead of spaces
- Keep names under 100 characters

## Step 2: Create JurisdictionResource Records

Choose one of the following methods based on your batch size:

### Option A: Django Admin Interface (Recommended for Small Batches)

Best for: **1-10 files**

1. **Access Django Admin:**
   ```bash
   # Navigate to: http://localhost:8001/admin/
   # Login with your superuser credentials
   ```

2. **Create resources manually:**
   - Go to **Jurisdiction** → **Jurisdiction resources** → **Add jurisdiction resource**
   - Fill in the form:
     - **Jurisdiction id**: 42 (for Tennessee)
     - **Jurisdiction abbrev**: TN
     - **Display name**: "Tennessee FOIA Law Guide"
     - **Description**: Brief description of the resource
     - **Resource type**: Choose appropriate type (e.g., "Law Guide")
     - **File**: Upload the PDF
     - **Order**: Set display order (0, 1, 2, etc.)
     - **Is active**: ✓ Checked
   - Click **Save**

3. **Repeat** for each PDF file.

**Pros:** Visual interface, immediate feedback, no coding required
**Cons:** Time-consuming for many files

### Option B: Django Shell Script (Recommended for Batch Imports)

Best for: **10+ files**

1. **Create a batch import script:**

   Create a file `batch_import_tennessee.py` in your local directory:

   ```python
   """
   Batch import script for Tennessee PDF resources.

   Usage:
   docker compose -f local.yml run --rm foia_coach_api \
     python manage.py shell < batch_import_tennessee.py
   """

   from django.core.files import File
   from apps.jurisdiction.models import JurisdictionResource
   import os

   # Configuration
   JURISDICTION_ID = 155  # Tennessee jurisdiction ID
   JURISDICTION_ABBREV = "TN"
   PDF_DIRECTORY = "/path/to/tennessee-pdfs"  # Update this path

   # Resource definitions
   # Format: (filename, display_name, description, resource_type)
   RESOURCES = [
       (
           "TN_FOIA_Law_Guide_2024.pdf",
           "Tennessee FOIA Law Guide 2024",
           "Comprehensive guide to Tennessee's Freedom of Information Act",
           "law_guide"
       ),
       (
           "TN_Request_Tips.pdf",
           "Tennessee FOIA Request Tips",
           "Best practices for filing FOIA requests in Tennessee",
           "request_tips"
       ),
       (
           "TN_Exemptions_Guide.pdf",
           "Tennessee FOIA Exemptions Guide",
           "Complete list of exemptions under Tennessee FOIA law",
           "exemptions"
       ),
       (
           "TN_Agency_Directory.pdf",
           "Tennessee Agency Directory",
           "Contact information for Tennessee state agencies",
           "agency_info"
       ),
       (
           "TN_Common_Denials.pdf",
           "Tennessee Common Denials Reference",
           "Guide to common denial reasons and how to appeal them",
           "general"
       ),
   ]

   # Import resources
   created_count = 0
   error_count = 0

   print(f"Starting batch import of {len(RESOURCES)} resources for {JURISDICTION_ABBREV}...")
   print("=" * 70)

   for idx, (filename, display_name, description, resource_type) in enumerate(RESOURCES, 1):
       file_path = os.path.join(PDF_DIRECTORY, filename)

       # Check if file exists
       if not os.path.exists(file_path):
           print(f"✗ [{idx}/{len(RESOURCES)}] File not found: {filename}")
           error_count += 1
           continue

       try:
           # Check if resource already exists
           existing = JurisdictionResource.objects.filter(
               jurisdiction_abbrev=JURISDICTION_ABBREV,
               display_name=display_name
           ).first()

           if existing:
               print(f"⊘ [{idx}/{len(RESOURCES)}] Already exists: {display_name}")
               continue

           # Create resource
           with open(file_path, 'rb') as f:
               resource = JurisdictionResource.objects.create(
                   jurisdiction_id=JURISDICTION_ID,
                   jurisdiction_abbrev=JURISDICTION_ABBREV,
                   display_name=display_name,
                   description=description,
                   resource_type=resource_type,
                   file=File(f, name=filename),
                   is_active=True,
                   order=idx - 1
               )

           print(f"✓ [{idx}/{len(RESOURCES)}] Created: {display_name} (ID: {resource.id})")
           created_count += 1

       except Exception as e:
           print(f"✗ [{idx}/{len(RESOURCES)}] Error creating {display_name}: {str(e)}")
           error_count += 1

   # Summary
   print("=" * 70)
   print(f"Import complete!")
   print(f"  Created:  {created_count}")
   print(f"  Errors:   {error_count}")
   print(f"  Skipped:  {len(RESOURCES) - created_count - error_count}")
   print(f"  Total:    {len(RESOURCES)}")

   if created_count > 0:
       print(f"\nNext step: Upload to OpenAI provider")
       print(f"  docker compose -f local.yml run --rm foia_coach_api \\")
       print(f"    python manage.py upload_resources_to_provider \\")
       print(f"    --provider=openai --state={JURISDICTION_ABBREV}")
   ```

2. **Update the script:**
   - Set `PDF_DIRECTORY` to your local folder path
   - Update `JURISDICTION_ID` (find it in MuckRock admin)
   - Customize the `RESOURCES` list with your PDFs

3. **Copy PDFs to Docker volume (if needed):**

   If your PDFs are on your local machine, you need to make them accessible to the Docker container:

   ```bash
   # Option 1: Copy to media directory
   docker compose -f local.yml cp /path/to/tennessee-pdfs/. \
     foia_coach_api:/app/media/temp_import/

   # Then update PDF_DIRECTORY in script to:
   # PDF_DIRECTORY = "/app/media/temp_import"

   # Option 2: Use Docker volume mount (add to local.yml)
   # Add under foia_coach_api.volumes:
   #   - /path/to/tennessee-pdfs:/import:ro

   # Then update PDF_DIRECTORY in script to:
   # PDF_DIRECTORY = "/import"
   ```

4. **Run the import:**
   ```bash
   docker compose -f local.yml run --rm foia_coach_api \
     python manage.py shell < batch_import_tennessee.py
   ```

**Pros:** Fast for many files, repeatable, version-controlled
**Cons:** Requires Python knowledge, file path management

### Option C: Management Command (For Programmatic Imports)

Best for: **Automated/scheduled imports**

Create a custom management command for reusable imports:

1. **Create command file:**
   ```bash
   touch foia-coach-api/apps/jurisdiction/management/commands/import_jurisdiction_pdfs.py
   ```

2. **Add the command code:**
   ```python
   """
   Management command to batch import PDF resources for a jurisdiction.

   Usage:
   python manage.py import_jurisdiction_pdfs \
     --state=TN \
     --jurisdiction-id=42 \
     --directory=/path/to/pdfs \
     --pattern="*.pdf"
   """

   from django.core.management.base import BaseCommand, CommandError
   from django.core.files import File
   from apps.jurisdiction.models import JurisdictionResource
   import os
   import glob


   class Command(BaseCommand):
       help = 'Batch import PDF resources for a jurisdiction'

       def add_arguments(self, parser):
           parser.add_argument(
               '--state',
               required=True,
               help='Jurisdiction abbreviation (e.g., TN, CO, GA)'
           )
           parser.add_argument(
               '--jurisdiction-id',
               type=int,
               required=True,
               help='Jurisdiction ID from MuckRock database'
           )
           parser.add_argument(
               '--directory',
               required=True,
               help='Directory containing PDF files'
           )
           parser.add_argument(
               '--pattern',
               default='*.pdf',
               help='File pattern to match (default: *.pdf)'
           )
           parser.add_argument(
               '--resource-type',
               default='general',
               choices=[
                   'law_guide', 'request_tips', 'exemptions',
                   'agency_info', 'case_law', 'general'
               ],
               help='Default resource type for all files'
           )
           parser.add_argument(
               '--dry-run',
               action='store_true',
               help='Show what would be imported without creating resources'
           )

       def handle(self, *args, **options):
           state = options['state']
           jurisdiction_id = options['jurisdiction_id']
           directory = options['directory']
           pattern = options['pattern']
           resource_type = options['resource_type']
           dry_run = options['dry_run']

           # Validate directory
           if not os.path.isdir(directory):
               raise CommandError(f"Directory does not exist: {directory}")

           # Find PDF files
           search_pattern = os.path.join(directory, pattern)
           pdf_files = sorted(glob.glob(search_pattern))

           if not pdf_files:
               raise CommandError(f"No files found matching pattern: {search_pattern}")

           self.stdout.write(
               self.style.SUCCESS(
                   f"Found {len(pdf_files)} file(s) in {directory}"
               )
           )

           if dry_run:
               self.stdout.write(self.style.WARNING("DRY RUN MODE - No resources will be created"))

           created_count = 0
           skipped_count = 0
           error_count = 0

           for idx, file_path in enumerate(pdf_files, 1):
               filename = os.path.basename(file_path)
               # Use filename (without extension) as display name
               display_name = f"{state} - {os.path.splitext(filename)[0].replace('_', ' ')}"

               # Check if already exists
               existing = JurisdictionResource.objects.filter(
                   jurisdiction_abbrev=state,
                   display_name=display_name
               ).first()

               if existing:
                   self.stdout.write(
                       f"  ⊘ [{idx}/{len(pdf_files)}] Already exists: {display_name}"
                   )
                   skipped_count += 1
                   continue

               if dry_run:
                   self.stdout.write(
                       f"  → [{idx}/{len(pdf_files)}] Would create: {display_name}"
                   )
                   continue

               try:
                   with open(file_path, 'rb') as f:
                       resource = JurisdictionResource.objects.create(
                           jurisdiction_id=jurisdiction_id,
                           jurisdiction_abbrev=state,
                           display_name=display_name,
                           description=f"Resource: {filename}",
                           resource_type=resource_type,
                           file=File(f, name=filename),
                           is_active=True,
                           order=idx - 1
                       )

                   self.stdout.write(
                       self.style.SUCCESS(
                           f"  ✓ [{idx}/{len(pdf_files)}] Created: {display_name} (ID: {resource.id})"
                       )
                   )
                   created_count += 1

               except Exception as e:
                   self.stdout.write(
                       self.style.ERROR(
                           f"  ✗ [{idx}/{len(pdf_files)}] Error: {display_name} - {str(e)}"
                       )
                   )
                   error_count += 1

           # Summary
           self.stdout.write("\n" + "=" * 70)
           self.stdout.write(self.style.SUCCESS("Import Summary:"))
           self.stdout.write(f"  Created:  {created_count}")
           self.stdout.write(f"  Skipped:  {skipped_count}")
           self.stdout.write(f"  Errors:   {error_count}")
           self.stdout.write(f"  Total:    {len(pdf_files)}")
           self.stdout.write("=" * 70)

           if created_count > 0 and not dry_run:
               self.stdout.write(
                   self.style.SUCCESS(
                       f"\nNext step: Upload to OpenAI provider\n"
                       f"  python manage.py upload_resources_to_provider "
                       f"--provider=openai --state={state}"
                   )
               )
   ```

3. **Run the command:**
   ```bash
   # Dry run first to preview
   docker compose -f local.yml run --rm foia_coach_api \
     python manage.py import_jurisdiction_pdfs \
     --state=TN \
     --jurisdiction-id=155 \
     --directory=/import \
     --dry-run

   # Actual import
   docker compose -f local.yml run --rm foia_coach_api \
     python manage.py import_jurisdiction_pdfs \
     --state=TN \
     --jurisdiction-id=155 \
     --directory=/import
   ```

**Pros:** Reusable, automated, production-ready
**Cons:** Requires creating the management command first

## Step 3: Upload to OpenAI Provider

Once your JurisdictionResource records are created, upload them to the OpenAI provider:

### Upload All Tennessee Resources

```bash
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py upload_resources_to_provider \
  --provider=openai \
  --state=TN
```

This command will:
- Find all active resources for Tennessee
- Create ResourceProviderUpload records for OpenAI
- Trigger automatic upload via signal handlers
- Display progress and summary

### Command Options

```bash
# Dry run to preview
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py upload_resources_to_provider \
  --provider=openai \
  --state=TN \
  --dry-run

# Force re-upload (if resources already uploaded)
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py upload_resources_to_provider \
  --provider=openai \
  --state=TN \
  --force

# Upload without state filter (all resources)
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py upload_resources_to_provider \
  --provider=openai
```

### Expected Output

```
Filtering resources for state: TN
Found 5 active resource(s) to upload to openai

  ✓ Created upload for TN: Tennessee FOIA Law Guide 2024
  ✓ Created upload for TN: Tennessee FOIA Request Tips
  ✓ Created upload for TN: Tennessee FOIA Exemptions Guide
  ✓ Created upload for TN: Tennessee Agency Directory
  ✓ Created upload for TN: Tennessee Common Denials Reference

============================================================
Upload Summary:
  Created:  5
  Updated:  0
  Skipped:  0
  Total:    5
============================================================

Uploads will be processed by signal handlers.
Check the admin interface or logs to monitor progress.
```

## Step 4: Verify Upload Status

### Check via Django Admin

1. Navigate to: http://localhost:8001/admin/jurisdiction/jurisdictionresource/
2. Look at the **Provider Upload Status** column
3. Status should show: `openai: ready`

### Check via Management Command

```bash
# Test OpenAI provider with a query
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py gemini_query \
  "What is the FOIA response deadline in Tennessee?" \
  --state=TN \
  --provider=openai
```

### Check via API

```bash
# List resources with upload status
curl http://localhost:8001/api/v1/resources/?jurisdiction_abbrev=TN

# Execute a test query
curl -X POST http://localhost:8001/api/v1/query/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are Tennessee FOIA fees?",
    "state": "TN",
    "provider": "openai"
  }'
```

### Check via Django Shell

```bash
docker compose -f local.yml run --rm foia_coach_api python manage.py shell
```

```python
from apps.jurisdiction.models import JurisdictionResource, ResourceProviderUpload

# Check Tennessee resources
tn_resources = JurisdictionResource.objects.filter(jurisdiction_abbrev='TN')
print(f"Total TN resources: {tn_resources.count()}")

# Check upload status
for resource in tn_resources:
    upload = resource.get_upload_status('openai')
    if upload:
        print(f"{resource.display_name}: {upload.index_status}")
    else:
        print(f"{resource.display_name}: No OpenAI upload")

# Count by status
from django.db.models import Count
status_counts = ResourceProviderUpload.objects.filter(
    resource__jurisdiction_abbrev='TN',
    provider='openai'
).values('index_status').annotate(count=Count('id'))

print("\nStatus summary:")
for item in status_counts:
    print(f"  {item['index_status']}: {item['count']}")
```

## Troubleshooting

### Issue: "No active resources found"

**Cause:** No JurisdictionResource records created, or `is_active=False`

**Solution:**
```bash
# Check if resources exist
docker compose -f local.yml run --rm foia_coach_api python manage.py shell

>>> from apps.jurisdiction.models import JurisdictionResource
>>> JurisdictionResource.objects.filter(jurisdiction_abbrev='TN').count()
```

### Issue: Upload status stuck at "pending"

**Cause:** Signal handlers not processing, or OpenAI API error

**Solution:**
1. Check logs:
   ```bash
   docker compose -f local.yml logs foia_coach_api | grep -i openai
   ```

2. Check error messages in admin interface

3. Manually retry upload:
   ```bash
   docker compose -f local.yml run --rm foia_coach_api \
     python manage.py upload_resources_to_provider \
     --provider=openai \
     --state=TN \
     --force
   ```

### Issue: "API calls are disabled"

**Cause:** `OPENAI_REAL_API_ENABLED` not set to `true`

**Solution:**
```bash
# Check environment variable
docker compose -f local.yml run --rm foia_coach_api \
  python manage.py shell -c "from django.conf import settings; print(settings.OPENAI_REAL_API_ENABLED)"

# Set in .envs/.local/.foia_coach_api
OPENAI_REAL_API_ENABLED=true

# Restart services
docker compose -f local.yml restart foia_coach_api
```

### Issue: File upload fails in Docker

**Cause:** File path not accessible inside container

**Solution:**
Use Docker volume mount or copy files to container:

```bash
# Method 1: Docker cp
docker compose -f local.yml cp /local/path/pdfs/. foia_coach_api:/app/media/import/

# Method 2: Add volume mount to local.yml
# Under foia_coach_api.volumes:
#   - /local/path/pdfs:/import:ro
```

### Issue: Duplicate resources created

**Cause:** Re-running import script without checking for existing resources

**Solution:**
The import scripts check for duplicates by `display_name`. If you get duplicates:

```bash
# Remove duplicates via Django shell
docker compose -f local.yml run --rm foia_coach_api python manage.py shell

>>> from apps.jurisdiction.models import JurisdictionResource
>>> from django.db.models import Count
>>>
>>> # Find duplicates
>>> duplicates = JurisdictionResource.objects.filter(
...     jurisdiction_abbrev='TN'
... ).values('display_name').annotate(
...     count=Count('id')
... ).filter(count__gt=1)
>>>
>>> # Delete newer duplicates (keep oldest)
>>> for dup in duplicates:
...     resources = JurisdictionResource.objects.filter(
...         jurisdiction_abbrev='TN',
...         display_name=dup['display_name']
...     ).order_by('created_at')
...
...     # Delete all except the first (oldest)
...     resources.exclude(id=resources.first().id).delete()
```

## Next Steps

After successful import and upload:

1. **Test queries** to ensure resources are working:
   ```bash
   docker compose -f local.yml run --rm foia_coach_api \
     python manage.py gemini_query \
     "What is the FOIA process in Tennessee?" \
     --state=TN \
     --provider=openai
   ```

2. **Update resource metadata** in Django admin:
   - Add better descriptions
   - Adjust resource types
   - Set proper ordering

3. **Upload to additional providers** (optional):
   ```bash
   # Upload to Gemini as well
   docker compose -f local.yml run --rm foia_coach_api \
     python manage.py upload_resources_to_provider \
     --provider=gemini \
     --state=TN
   ```

4. **Monitor costs** in OpenAI dashboard:
   - Vector store storage costs
   - API usage costs

## Additional Resources

- [README.md](./README.md) - Complete system documentation
- [USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md) - More usage examples
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - Full API reference
- [OpenAI File Search Documentation](https://platform.openai.com/docs/assistants/tools/file-search)

## Support

For issues or questions:
- Check the troubleshooting section above
- Review Django admin error messages
- Check Docker logs: `docker compose -f local.yml logs foia_coach_api`
- Consult the main README.md for provider configuration

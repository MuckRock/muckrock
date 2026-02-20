#!/bin/bash
# Export seed data (DB fixture + media files) as a tarball for teammates.
#
# Usage:
#   ./foia-coach-api/scripts/export_seed_data.sh
#
# Creates: foia-coach-api/foia_coach_seed_data.tar.gz
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$API_DIR")"

echo "==> Exporting database fixture..."
docker compose -f "$ROOT_DIR/local.yml" run --rm foia_coach_api \
  python manage.py dumpdata \
  jurisdiction.JurisdictionResource \
  jurisdiction.ResourceProviderUpload \
  --indent 2 \
  -o /app/fixtures/seed_resources.json

echo "==> Packaging seed data tarball..."
cd "$API_DIR"
tar czf foia_coach_seed_data.tar.gz \
  fixtures/seed_resources.json \
  media/foia_coach/

SIZE=$(du -sh foia_coach_seed_data.tar.gz | cut -f1)
echo "==> Created: foia-coach-api/foia_coach_seed_data.tar.gz ($SIZE)"
echo "    Share this file with teammates."

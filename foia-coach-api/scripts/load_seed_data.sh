#!/bin/bash
# Load seed data from a teammate's exported tarball.
#
# Usage:
#   ./foia-coach-api/scripts/load_seed_data.sh [path/to/foia_coach_seed_data.tar.gz]
#
# If no path is given, looks for foia-coach-api/foia_coach_seed_data.tar.gz
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$API_DIR")"
TARBALL="${1:-$API_DIR/foia_coach_seed_data.tar.gz}"

if [ ! -f "$TARBALL" ]; then
  echo "Error: Seed data tarball not found at $TARBALL"
  echo "Usage: $0 [path/to/foia_coach_seed_data.tar.gz]"
  exit 1
fi

echo "==> Extracting seed data from $TARBALL..."
cd "$API_DIR"
tar xzf "$TARBALL"

echo "==> Running database migrations..."
docker compose -f "$ROOT_DIR/local.yml" run --rm foia_coach_api \
  python manage.py migrate --noinput

echo "==> Loading fixture into database..."
docker compose -f "$ROOT_DIR/local.yml" run --rm foia_coach_api \
  python manage.py loaddata /app/fixtures/seed_resources.json

echo ""
echo "==> Seed data loaded successfully!"
echo "    - Database records: loaded"
echo "    - Media files: extracted to foia-coach-api/media/"
echo ""
echo "    The resource files are now on disk and tracked in the database."
echo "    Since you're sharing an OpenAI API key, the vector store is"
echo "    already populated — no upload step needed."
echo ""
echo "    Start the services:"
echo "      docker compose -f local.yml up foia_coach_api foia_coach_ui foia_coach_postgres"

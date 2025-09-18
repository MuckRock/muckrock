#!/bin/bash

# Check that the script is running in a Heroku review app.
#
# This is inferred from the presence of a HEROKU_APP_NAME environment variable,
# which is automatically injected by Heroku into review apps.
# 
# By checking that we're in a "staging" environment, we have confidence that we're
# only copying staging data into an environment that expects to receive it.
set -e
if [ -n "$HEROKU_APP_NAME" ] && [ "$DJANGO_ENV" = "staging" ]; then
  # Restore the data from the staging app database backup to the review app database.
  LATEST_BACKUP=$(heroku pg:backups --app muckrock-staging | awk '/b[0-9]+/ {print $1; exit}')
  heroku pg:backups:restore "muckrock-staging::$LATEST_BACKUP" DATABASE_URL \
    --app "$HEROKU_APP_NAME" \
    --confirm "$HEROKU_APP_NAME"
  # Call the Python postdeploy script to add the review app redirect URI
  python3 "$(dirname "$0")/postdeploy.py" add
fi

# No matter what environment we're in, ensure we run any Django migrations.
python manage.py migrate --noinput

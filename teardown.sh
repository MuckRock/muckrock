#!/bin/bash

if [ -n "$HEROKU_APP_NAME" ] && [ "$DJANGO_ENV" = "staging" ]; then
  python3 "$(dirname "$0")/postdeploy.py remove"
fi
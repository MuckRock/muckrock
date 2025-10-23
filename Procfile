web: bin/start-nginx gunicorn -c config/gunicorn.conf muckrock.wsgi:application
scheduler: celery -A muckrock.core.celery worker -E -B --loglevel=INFO
worker: celery -A muckrock.core.celery worker -E -Q celery,phaxio --loglevel=INFO
release: python manage.py compress --settings=muckrock.settings.production && python manage.py migrate --no-input && python manage.py collectstatic --no-input

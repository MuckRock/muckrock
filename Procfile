web: bin/start-nginx gunicorn -c config/gunicorn.conf muckrock.wsgi:application
scheduler: celery -A muckrock.core.celery worker -E -B --loglevel=INFO
worker: celery -A muckrock.core.celery worker -E -Q celery,phaxio --loglevel=INFO

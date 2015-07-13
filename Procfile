
#web:       newrelic-admin run-program python manage.py run_gunicorn -b 0.0.0.0:$PORT -w 3 -k gevent --max-requests 250 --log-level debug --debug
#web:       newrelic-admin run-program waitress-serve --port=$PORT --channel-timeout=30 muckrock.wsgi:application
web:       bin/start-nginx newrelic-admin run-program gunicorn -c gunicorn.conf muckrock.wsgi:application
#web:       newrelic-admin run-program gunicorn -c gunicorn.conf muckrock.wsgi:application
#web:       newrelic-admin run-program gunicorn muckrock.wsgi --log-file - -b 0.0.0.0:$PORT --log-level debug --debug
scheduler: newrelic-admin run-program python manage.py celery worker -E -B --loglevel=INFO
worker:    newrelic-admin run-program python manage.py celery worker -E --loglevel=INFO

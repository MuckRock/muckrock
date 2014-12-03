
web:       newrelic-admin run-program python manage.py run_gunicorn -b 0.0.0.0:$PORT -w 3 -k gevent --max-requests 250
#web:       newrelic-admin run-program waitress-serve --port=$PORT --channel-timeout=30 muckrock.wsgi:application
#web:       bin/start-nginx newrelic-admin run-program gunicorn -c gunicorn.conf muckrock.wsgi:application
#web:       newrelic-admin run-program gunicorn -c gunicorn.conf muckrock.wsgi:application
scheduler: newrelic-admin run-program python manage.py celeryd -E -B --loglevel=INFO
worker:    newrelic-admin run-program python manage.py celeryd -E --loglevel=INFO

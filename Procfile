
#web:       newrelic-admin run-program python manage.py run_gunicorn -b 0.0.0.0:$PORT -w 3 -k gevent --max-requests 250
web:       newrelic-admin run-program waitress-serve --port=$PORT muckrock.wsgi:application
scheduler: newrelic-admin run-program python manage.py celeryd -E -B --loglevel=INFO
worker:    newrelic-admin run-program python manage.py celeryd -E --loglevel=INFO

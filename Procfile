
web:       python manage.py run_gunicorn -b 0.0.0.0:$PORT -w 9 -k gevent --max-requests 250
scheduler: python manage.py celeryd -E -B --loglevel=INFO
worker:    python manage.py celeryd -E --loglevel=INFO

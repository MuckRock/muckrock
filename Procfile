
web:     python muckrock/manage.py run_gunicorn -b 0.0.0.0:$PORT -w 9 -k gevent --max-requests 250
celeryd: python muckrock/manage.py celeryd -E -B --loglevel=INFO

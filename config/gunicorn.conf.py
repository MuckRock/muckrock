import multiprocessing
import os

# def pre_fork(server, worker):
#     f = '/tmp/app-initialized'
#     open(f, 'w').close()

bind = "0.0.0.0:5000"
workers = int(os.environ.get('GUNICORN_WORKERS', 3))
max_requests = 50
timeout = 120
log_level = 'debug'
accesslog = "/app/gunicorn.access.log"
errorlog = "/app/gunicorn.error.log"

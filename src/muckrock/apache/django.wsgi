import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'muckrock.settings'

sys.path.append('/home/mitch/MuckRock/src/')
sys.path.append('/home/mitch/MuckRock/src/muckrock/')
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

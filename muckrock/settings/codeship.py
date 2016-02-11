from muckrock.settings.test import *

DATABASES['default'] = {
    'NAME': 'test',
    'USER': os.environ.get('PG_USER'),
    'PASSWORD': os.environ.get('PG_PASSWORD'),
    'HOST': '127.0.0.1',
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
}

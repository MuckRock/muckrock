"""
This file contains python variables that configure Lamson for email processing.
"""
import os
import sys

sys.path.insert(1, '../muckrock')
sys.path.insert(1, '../')

from muckrock.settings import LAMSON_RELAY_HOST, LAMSON_RELAY_PORT, LAMSON_RECEIVER_HOST, \
                              LAMSON_RECEIVER_PORT, LAMSON_ROUTER_HOST

# You may add additional parameters such as `username' and `password' if your
# relay server requires authentication, `starttls' (boolean) or `ssl' (boolean)
# for secure connections.
relay_config = {'host': LAMSON_RELAY_HOST, 'port': LAMSON_RELAY_PORT}

receiver_config = {'host': LAMSON_RECEIVER_HOST, 'port': LAMSON_RECEIVER_PORT}

handlers = ['app.handlers.request']

router_defaults = {'host': LAMSON_ROUTER_HOST.replace('.', '\.'), 'address': r'[0-9]+-[0-9]{8}'}

template_config = {'dir': 'app', 'module': 'templates'}

# the config/boot.py will turn these values into variables set in settings

# these are for django compatibility
os.environ['DJANGO_SETTINGS_MODULE'] = 'muckrock.settings'

# This file contains python variables that configure Lamson for email processing.
import logging
import os
import sys

# You may add additional parameters such as `username' and `password' if your
# relay server requires authentication, `starttls' (boolean) or `ssl' (boolean)
# for secure connections.
relay_config = {'host': 'localhost', 'port': 1025}

receiver_config = {'host': 'localhost', 'port': 8823}

handlers = ['app.handlers.request']

router_defaults = {'host': r'requests\.muckrock\.com', 'address': r'[0-9]+-[0-9]{8}'}

template_config = {'dir': 'app', 'module': 'templates'}

# the config/boot.py will turn these values into variables set in settings

# these are for django compatibility
os.environ['DJANGO_SETTINGS_MODULE'] = 'muckrock.settings'
sys.path.insert(1, '../../')
sys.path.insert(1, '../')

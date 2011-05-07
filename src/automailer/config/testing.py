"""
Initialization for testing environment
"""

import sys
sys.path.insert(0, './')

from config import settings
from lamson import view
from lamson.routing import Router
from lamson.server import Relay
import jinja2
import logging
import logging.config
import os

logging.config.fileConfig("config/test_logging.conf")

# the relay host to actually send the final message to (set debug=1 to see what
# the relay is saying to the log server).
settings.relay = Relay(host=settings.relay_config['host'],
                       port=8825, debug=0)


settings.receiver = None

# pylint: disable-msg=W0142
Router.defaults(**settings.router_defaults)
Router.load(settings.handlers)
Router.RELOAD = True
Router.LOG_EXCEPTIONS = False

view.LOADER = jinja2.Environment(
    loader=jinja2.PackageLoader(settings.template_config['dir'],
                                settings.template_config['module']))

# if you have pyenchant and enchant installed then the template tests will do
# spell checking for you, but you need to tell pyenchant where to find itself
# if 'PYENCHANT_LIBRARY_PATH' not in os.environ:
#     os.environ['PYENCHANT_LIBRARY_PATH'] = '/opt/local/lib/libenchant.dylib'

# these are for django compatibility
os.environ['DJANGO_SETTINGS_MODULE'] = 'muckrock.settings'

"""
Initilization for production environment
"""
from config import settings
from lamson.routing import Router
from lamson.server import Relay, SMTPReceiver
from lamson import view, queue
import logging
import logging.config
import jinja2

from sentry.client.handlers import SentryHandler

logging.config.fileConfig("config/logging.conf")

logger = logging.getLogger()
rlogger = logging.getLogger('routing')
sentry_handler = SentryHandler()
sentry_handler.setLevel(logging.INFO)

# ensure we havent already registered the handler
if SentryHandler not in [x.__class__ for x in logger.handlers]:
    logger.addHandler(sentry_handler)
    rlogger.addHandler(sentry_handler)

    # Add StreamHandler to sentry's default so you can catch missed exceptions
    logger = logging.getLogger('sentry.errors')
    logger.propagate = False
    logger.addHandler(logging.StreamHandler())

# the relay host to actually send the final message to
settings.relay = Relay(host=settings.relay_config['host'],
                       port=settings.relay_config['port'], debug=1)

# where to listen for incoming messages
settings.receiver = SMTPReceiver(settings.receiver_config['host'],
                                 settings.receiver_config['port'])

# pylint: disable-msg=W0142
Router.defaults(**settings.router_defaults)
Router.load(settings.handlers)
Router.RELOAD = True
Router.UNDELIVERABLE_QUEUE = queue.Queue("run/undeliverable")

view.LOADER = jinja2.Environment(
    loader=jinja2.PackageLoader(settings.template_config['dir'],
                                settings.template_config['module']))


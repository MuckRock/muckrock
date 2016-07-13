"""
Views for the FOIA application
"""

from autocomplete_light import shortcuts as autocomplete_light
autocomplete_light.autodiscover()

from muckrock.foia.views.views import *
from muckrock.foia.views.actions import *
from muckrock.foia.views.composers import *
from muckrock.foia.views.comms import *
from muckrock.foia.views.files import *

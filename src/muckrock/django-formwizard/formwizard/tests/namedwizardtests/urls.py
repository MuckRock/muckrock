from django.conf.urls.defaults import *
from formwizard.tests.namedwizardtests.forms import ContactWizard, Page1, Page2, Page3, Page4

def get_named_wizard():
    return ContactWizard(
        [('form1', Page1), ('form2', Page2), ('form3', Page3), ('form4', Page4)],
        url_name='nwiz_session',
        done_step_name='nwiz_session_done'
    )

urlpatterns = patterns('',
    url(r'^nwiz_session/(?P<step>.+)/$', get_named_wizard(), name='nwiz_session'),
    url(r'^nwiz_session/$', get_named_wizard(), name='nwiz_session_start'),

)


"""
url(r'^nwiz_cookie/(?P<step>.+)/$', ContactWizard(
    'formwizard.storage.cookie.CookieStorage',
    [('form1', Page1), ('form2', Page2), ('form3', Page3), ('form4', Page4)],
    url_name='nwiz_cookie',
    done_step_name='nwiz_cookie_done'
))
"""

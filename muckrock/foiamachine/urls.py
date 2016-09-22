
from django.conf.urls import patterns, include, url

import debug_toolbar

from muckrock.foiamachine import views

urlpatterns = patterns(
    '',
    url(r'^$', views.homepage, name='index'),
    url(r'^__debug__/', include(debug_toolbar.urls)),
)

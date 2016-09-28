
from django.conf.urls import patterns, include, url
from django.contrib.auth import views as auth_views

import debug_toolbar

from muckrock.foiamachine import views
from muckrock.forms import PasswordResetForm

urlpatterns = patterns(
    '',
    url(r'^$', views.Homepage.as_view(), name='index'),
    url(r'^accounts/signup/$', views.Signup.as_view(), name='signup'),
    url(r'^accounts/login/$',
        auth_views.login,
        {'template_name': 'foiamachine/registration/login.html'},
        name='login'),
    url(r'^accounts/logout/$',
        auth_views.logout,
        {'next_page': 'index'},
        name='logout'),
    url(r'^__debug__/', include(debug_toolbar.urls)),
)

"""
URL mappings for the Fine Uploader application
"""

from django.conf.urls import url

from muckrock.fine_uploader import views

urlpatterns = [
        url(r'^sign/$', views.sign, name='fine-uploader-sign'),
        url(r'^success/$', views.success, name='fine-uploader-success'),
        url(r'^blank/$', views.blank, name='fine-uploader-blank'),
        url(r'^delete/$', views.delete, name='fine-uploader-delete'),
        url(r'^key/$', views.key_name, name='fine-uploader-key-name'),
        url(r'^session/$', views.session, name='fine-uploader-session'),
        ]

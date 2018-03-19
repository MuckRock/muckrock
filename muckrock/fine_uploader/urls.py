"""
URL mappings for the Fine Uploader application
"""

# Django
from django.conf.urls import url

# MuckRock
from muckrock.fine_uploader import views

urlpatterns = [
    url(
        r'^sign/$',
        views.sign,
        name='fine-uploader-sign',
    ),
    url(
        r'^blank/$',
        views.blank,
        name='fine-uploader-blank',
    ),
    url(
        r'^success_request/$',
        views.success_request,
        name='fine-uploader-success-request',
    ),
    url(
        r'^success_composer/$',
        views.success_composer,
        name='fine-uploader-success-composer',
    ),
    url(
        r'^success_comm/$',
        views.success_comm,
        name='fine-uploader-success-comm',
    ),
    url(
        r'^success_dataset/$',
        views.success_dataset,
        name='fine-uploader-success-dataset',
    ),
    url(
        r'^key_request/$',
        views.key_name_request,
        name='fine-uploader-key-name-request',
    ),
    url(
        r'^key_composer/$',
        views.key_name_composer,
        name='fine-uploader-key-name-composer',
    ),
    url(
        r'^key_comm/$',
        views.key_name_comm,
        name='fine-uploader-key-name-comm',
    ),
    url(
        r'^key_dataset/$',
        views.key_name_dataset,
        name='fine-uploader-key-name-dataset',
    ),
    url(
        r'^delete_request/$',
        views.delete_request,
        name='fine-uploader-delete-request',
    ),
    url(
        r'^delete_composer/$',
        views.delete_composer,
        name='fine-uploader-delete-composer',
    ),
    url(
        r'^session_request/$',
        views.session_request,
        name='fine-uploader-session-request',
    ),
    url(
        r'^session_composer/$',
        views.session_composer,
        name='fine-uploader-session-composer',
    ),
]

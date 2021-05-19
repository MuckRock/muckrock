"""
URL mappings for the Fine Uploader application
"""

# Django
from django.conf.urls import url

# MuckRock
from muckrock.fine_uploader import views

urlpatterns = [
    url(r"^blank/$", views.blank, name="fine-uploader-blank"),
    url(r"^upload_chunk/$", views.upload_chunk, name="fine-uploader-chunk"),
    url(
        r"^success_request/$",
        views.success_request,
        name="fine-uploader-success-request",
    ),
    url(
        r"^success_composer/$",
        views.success_composer,
        name="fine-uploader-success-composer",
    ),
    url(r"^success_comm/$", views.success_comm, name="fine-uploader-success-comm"),
    url(
        r"^preupload_request/$",
        views.preupload_request,
        name="fine-uploader-preupload-request",
    ),
    url(
        r"^preupload_composer/$",
        views.preupload_composer,
        name="fine-uploader-preupload-composer",
    ),
    url(
        r"^preupload_comm/$", views.preupload_comm, name="fine-uploader-preupload-comm"
    ),
    url(
        r"^delete_request/?(?P<idx>\d*)$",
        views.delete_request,
        name="fine-uploader-delete-request",
    ),
    url(
        r"^delete_composer/?(?P<idx>\d*)$",
        views.delete_composer,
        name="fine-uploader-delete-composer",
    ),
    url(
        r"^session_request/$",
        views.session_request,
        name="fine-uploader-session-request",
    ),
    url(
        r"^session_composer/$",
        views.session_composer,
        name="fine-uploader-session-composer",
    ),
]

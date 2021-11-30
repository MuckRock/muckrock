"""
URL mappings for the Fine Uploader application
"""

# Django
from django.urls import re_path

# MuckRock
from muckrock.fine_uploader import views

urlpatterns = [
    re_path(r"^blank/$", views.blank, name="fine-uploader-blank"),
    re_path(r"^upload_chunk/$", views.upload_chunk, name="fine-uploader-chunk"),
    re_path(
        r"^success_request/$",
        views.success_request,
        name="fine-uploader-success-request",
    ),
    re_path(
        r"^success_composer/$",
        views.success_composer,
        name="fine-uploader-success-composer",
    ),
    re_path(r"^success_comm/$", views.success_comm, name="fine-uploader-success-comm"),
    re_path(
        r"^preupload_request/$",
        views.preupload_request,
        name="fine-uploader-preupload-request",
    ),
    re_path(
        r"^preupload_composer/$",
        views.preupload_composer,
        name="fine-uploader-preupload-composer",
    ),
    re_path(
        r"^preupload_comm/$", views.preupload_comm, name="fine-uploader-preupload-comm"
    ),
    re_path(
        r"^delete_request/?(?P<idx>\d*)$",
        views.delete_request,
        name="fine-uploader-delete-request",
    ),
    re_path(
        r"^delete_composer/?(?P<idx>\d*)$",
        views.delete_composer,
        name="fine-uploader-delete-composer",
    ),
    re_path(
        r"^session_request/$",
        views.session_request,
        name="fine-uploader-session-request",
    ),
    re_path(
        r"^session_composer/$",
        views.session_composer,
        name="fine-uploader-session-composer",
    ),
]

"""
URL mappings for the Task application
"""

# Django
from django.urls import re_path
from django.views.generic.base import RedirectView

# MuckRock
from muckrock.task import views

urlpatterns = [
    re_path(r"^$", RedirectView.as_view(url="/task/response/"), name="task-list"),
    re_path(r"^orphan/$", views.OrphanTaskList.as_view(), name="orphan-task-list"),
    re_path(
        r"^orphan/(?P<pk>\d+)/$", views.OrphanTaskList.as_view(), name="orphan-task"
    ),
    re_path(
        r"^snail-mail/$", views.SnailMailTaskList.as_view(), name="snail-mail-task-list"
    ),
    re_path(
        r"^snail-mail/(?P<pk>\d+)/$",
        views.SnailMailTaskList.as_view(),
        name="snail-mail-task",
    ),
    re_path(
        r"^review-agency/$",
        views.ReviewAgencyTaskList.as_view(),
        name="review-agency-task-list",
    ),
    re_path(
        r"^review-agency/(?P<pk>\d+)/$",
        views.ReviewAgencyTaskList.as_view(),
        name="review-agency-task",
    ),
    re_path(r"^portal/$", views.PortalTaskList.as_view(), name="portal-task-list"),
    re_path(
        r"^portal/(?P<pk>\d+)/$", views.PortalTaskList.as_view(), name="portal-task"
    ),
    re_path(
        r"^new-portal/$", views.NewPortalTaskList.as_view(), name="new-portal-task-list"
    ),
    re_path(
        r"^new-portal/(?P<pk>\d+)/$",
        views.NewPortalTaskList.as_view(),
        name="new-portal-task",
    ),
    re_path(r"^flagged/$", views.FlaggedTaskList.as_view(), name="flagged-task-list"),
    re_path(
        r"^flagged/(?P<pk>\d+)/$", views.FlaggedTaskList.as_view(), name="flagged-task"
    ),
    re_path(
        r"^new-agency/$", views.NewAgencyTaskList.as_view(), name="new-agency-task-list"
    ),
    re_path(
        r"^new-agency/(?P<pk>\d+)/$",
        views.NewAgencyTaskList.as_view(),
        name="new-agency-task",
    ),
    re_path(
        r"^response/$", views.ResponseTaskList.as_view(), name="response-task-list"
    ),
    re_path(
        r"^response/(?P<pk>\d+)/$",
        views.ResponseTaskList.as_view(),
        name="response-task",
    ),
    re_path(
        r"^status-change/$",
        views.StatusChangeTaskList.as_view(),
        name="status-change-task-list",
    ),
    re_path(
        r"^status-change/(?P<pk>\d+)/$",
        views.StatusChangeTaskList.as_view(),
        name="status-change-task",
    ),
    re_path(
        r"^crowdfund/$", views.CrowdfundTaskList.as_view(), name="crowdfund-task-list"
    ),
    re_path(
        r"^crowdfund/(?P<pk>\d+)/$",
        views.CrowdfundTaskList.as_view(),
        name="crowdfund-task",
    ),
    re_path(
        r"^multirequest/$",
        views.MultiRequestTaskList.as_view(),
        name="multirequest-task-list",
    ),
    re_path(
        r"^multirequest/(?P<pk>\d+)/$",
        views.MultiRequestTaskList.as_view(),
        name="multirequest-task",
    ),
    re_path(
        r"^project-review/$",
        views.ProjectReviewTaskList.as_view(),
        name="projectreview-task-list",
    ),
    re_path(
        r"^project-review/(?P<pk>\d+)/$",
        views.ProjectReviewTaskList.as_view(),
        name="projectreview-task",
    ),
    re_path(
        r"^payment-info/$",
        views.PaymentInfoTaskList.as_view(),
        name="payment-info-task-list",
    ),
    re_path(
        r"^payment-info/(?P<pk>\d+)/$",
        views.PaymentInfoTaskList.as_view(),
        name="payment-info-task",
    ),
    # tasks for a specific request
    re_path(
        r"^request/(?P<pk>\d+)/$",
        views.RequestTaskList.as_view(),
        name="request-task-list",
    ),
    re_path(
        r"^snail-mail/pdf/$", views.snail_mail_bulk_pdf, name="snail-mail-bulk-pdf"
    ),
    re_path(
        r"^snail-mail/pdf/(?P<pk>\d+)/$", views.snail_mail_pdf, name="snail-mail-pdf"
    ),
    re_path(
        r"^review-agency-ajax/(?P<pk>\d+)/$",
        views.review_agency_ajax,
        name="review-agency-ajax",
    ),
    re_path(r"^assign-to/$", views.assign_to, name="task-assign"),
    re_path(
        r"^bulk-new-agency/$",
        views.BulkNewAgency.as_view(),
        name="task-bulk-new-agency",
    ),
]

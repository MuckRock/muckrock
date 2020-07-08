"""
Views for the organization application
"""
# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from django.db.models.query import Prefetch
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import is_safe_url
from django.views.generic import DetailView, RedirectView

# MuckRock
from muckrock.core.views import MROrderedListView
from muckrock.foia.models import FOIARequest
from muckrock.organization.models import Organization


class OrganizationListView(MROrderedListView):
    """List of organizations"""

    model = Organization
    template_name = "organization/list.html"
    sort_map = {"name": "name"}

    def get_queryset(self):
        """Filter out individual orgs and private orgs for non-staff"""
        queryset = (
            super(OrganizationListView, self).get_queryset().filter(individual=False)
        )
        if not self.request.user.is_staff:
            queryset = queryset.filter(private=False)
        return queryset


class OrganizationDetailView(DetailView):
    """Organization detail view"""

    queryset = Organization.objects.filter(individual=False).prefetch_related(
        Prefetch("users", queryset=User.objects.select_related("profile"))
    )
    template_name = "organization/detail.html"

    def get_object(self, queryset=None):
        """Get the org"""
        org = super(OrganizationDetailView, self).get_object(queryset=queryset)
        user = self.request.user
        is_member = user.is_authenticated and org.has_member(user)
        if org.private and not is_member and not user.is_staff:
            raise Http404
        return org

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        context = super(OrganizationDetailView, self).get_context_data(**kwargs)
        organization = context["organization"]
        user = self.request.user
        context["is_staff"] = user.is_staff
        if user.is_authenticated:
            context["is_admin"] = organization.has_admin(user)
            context["is_member"] = organization.has_member(user)
        else:
            context["is_owner"] = False
            context["is_member"] = False
        requests = FOIARequest.objects.organization(organization).get_viewable(user)
        context["requests"] = {
            "count": requests.count(),
            "filed": requests.order_by("-composer__datetime_submitted")[:10],
            "completed": requests.get_done().order_by("-datetime_done")[:10],
        }

        context["members"] = organization.users.all()
        if organization.requests_per_month > 0:
            context["requests_progress"] = (
                float(organization.monthly_requests) / organization.requests_per_month
            ) * 100
        else:
            context["requests_progress"] = 0

        context["sidebar_admin_url"] = reverse(
            "admin:organization_organization_change", args=(organization.pk,)
        )
        return context


class OrganizationSquareletView(RedirectView):
    """Organization squarelet view redirects to squarelet"""

    def get_redirect_url(self, slug, *args, **kwargs):
        """Different URL for individual orgs"""
        organization = get_object_or_404(Organization, slug=slug)
        if organization.individual:
            user = User.objects.get(profile__uuid=organization.uuid)
            return "{}/users/{}/".format(settings.SQUARELET_URL, user.username)
        else:
            return "{}/organizations/{}/".format(settings.SQUARELET_URL, slug)


@login_required
def activate(request):
    """Activate one of your organizations"""
    redirect_url = request.POST.get("next", "/")
    redirect_url = redirect_url if is_safe_url(redirect_url) else "/"

    try:
        organization = request.user.organizations.get(
            pk=request.POST.get("organization")
        )
        request.user.profile.organization = organization
        # update the navbar header cache
        cache.set(
            "sb:{}:user_org".format(request.user.username),
            organization,
            settings.DEFAULT_CACHE_TIMEOUT,
        )
        messages.success(
            request,
            "You have switched your active organization to {}".format(
                organization.display_name
            ),
        )
    except Organization.DoesNotExist:
        messages.error(request, "Organization does not exist")
    except ValueError:
        messages.error(request, "You are not a member of that organization")

    return redirect(redirect_url)

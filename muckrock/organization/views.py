"""
Views for the organization application
"""
# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import is_safe_url
from django.views.generic import RedirectView

# MuckRock
from muckrock.organization.models import Organization


class OrganizationDetailView(RedirectView):
    """Organization detail view redirects to squarelet"""

    def get_redirect_url(self, slug, *args, **kwargs):
        """Different URL for individual orgs"""
        organization = get_object_or_404(Organization, slug=slug)
        if organization.individual:
            user = User.objects.get(profile__uuid=organization.uuid)
            return '{}/users/{}/'.format(settings.SQUARELET_URL, user.username)
        else:
            return '{}/organizations/{}/'.format(settings.SQUARELET_URL, slug)


class OrganizationListView(RedirectView):
    """Organization list view redirects to squarelet"""
    url = '{}/organizations/'.format(settings.SQUARELET_URL)


def activate(request):
    """Activate one of your organizations"""
    redirect_url = request.POST.get('next', '/')
    redirect_url = redirect_url if is_safe_url(redirect_url) else '/'

    try:
        organization = request.user.organizations.get(
            pk=request.POST.get('organization'),
        )
        request.user.profile.organization = organization
        # update the navbar header cache
        cache.set(
            'sb:{}:user_org'.format(request.user.username),
            organization,
            settings.DEFAULT_CACHE_TIMEOUT,
        )
        messages.success(
            request, 'You have switched your active organization to {}'.format(
                organization.display_name
            )
        )
    except Organization.DoesNotExist:
        messages.error(request, 'Organization does not exist')
    except ValueError:
        messages.error(request, 'You are not a member of that organization')

    return redirect(redirect_url)

"""Context processors to ensure data is displayed in sidebar for all views"""

# Django
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm

# MuckRock
from muckrock.core.utils import cache_get_or_set
from muckrock.foia.models import FOIAComposer, FOIARequest
from muckrock.news.models import Article
from muckrock.project.models import Project


def get_recent_articles():
    """Lists last five recent news articles"""
    return Article.objects.get_published().order_by("-pub_date")[:5]


def get_actionable_requests(user):
    """Gets requests that require action or attention"""
    requests = FOIARequest.objects.filter(composer__user=user)
    started = FOIAComposer.objects.filter(user=user, status="started").count()
    payment = requests.filter(status="payment").count()
    fix = requests.filter(status="fix").count()
    return {"started": started, "payment": payment, "fix": fix}


def get_unread_notifications(user):
    """Gets unread notifiations for user, if they're logged in."""
    if user.is_authenticated:
        return user.notifications.get_unread()
    else:
        return None


def get_organization(user):
    """Gets a users active organization"""

    return cache_get_or_set(
        "sb:%s:user_org" % user.username,
        lambda: user.profile.organization,
        settings.DEFAULT_CACHE_TIMEOUT,
    )


def get_organizations(user):
    """Gets all of the users organizations"""

    return cache_get_or_set(
        "sb:%s:user_orgs" % user.username,
        user.organizations.get_cache,
        settings.DEFAULT_CACHE_TIMEOUT,
    )


def sidebar_info(request):
    """Displays info about a user's requsts in the sidebar"""
    # content for all users
    if request.path.startswith(("/admin/", "/sitemap", "/news-sitemaps", "/api_v1/")):
        return {}
    sidebar_info_dict = {
        "dropdown_recent_articles": get_recent_articles(),
        "login_form": AuthenticationForm(),
    }
    if request.user.is_authenticated:
        # content for logged in users
        sidebar_info_dict.update(
            {
                "unread_notifications": get_unread_notifications(request.user),
                "actionable_requests": get_actionable_requests(request.user),
                "user_organization": get_organization(request.user),
                "organizations": get_organizations(request.user),
                "my_projects": Project.objects.get_for_contributor(
                    request.user
                ).optimize()[:4],
                "payment_failed_organizations": request.user.organizations.filter(
                    memberships__admin=True, payment_failed=True
                ),
            }
        )

    return sidebar_info_dict

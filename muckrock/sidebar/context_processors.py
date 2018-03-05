"""Context processors to ensure data is displayed in sidebar for all views"""

# Django
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm

# Standard Library
from datetime import datetime, timedelta

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article
from muckrock.organization.models import Organization
from muckrock.project.models import Project
from muckrock.sidebar.models import Broadcast
from muckrock.utils import cache_get_or_set


def get_recent_articles():
    """Lists last five recent news articles"""
    return Article.objects.get_published().order_by('-pub_date')[:5]


def get_actionable_requests(user):
    """Gets requests that require action or attention"""
    requests = FOIARequest.objects.filter(user=user)
    started = requests.filter(status='started').count()
    payment = requests.filter(status='payment').count()
    fix = requests.filter(status='fix').count()
    return {
        'started': started,
        'payment': payment,
        'fix': fix,
    }


def get_unread_notifications(user):
    """Gets unread notifiations for user, if they're logged in."""
    if user.is_authenticated():
        return user.notifications.get_unread()
    else:
        return None


def get_organization(user):
    """Gets organization, if it exists"""

    return cache_get_or_set(
        'sb:%s:user_org' % user.username, user.profile.get_org,
        settings.DEFAULT_CACHE_TIMEOUT
    )


def sidebar_broadcast(user):
    """Displays a broadcast to a given usertype"""

    def load_broadcast(user_class):
        """Return a function to load the correct broadcast"""

        def inner():
            """Argument-less function to load correct broadcast"""
            try:
                # exclude stale broadcasts from displaying
                last_week = datetime.now() - timedelta(7)
                broadcast = Broadcast.objects.get(
                    updated__gte=last_week, context=user_class
                ).text
            except Broadcast.DoesNotExist:
                broadcast = ''
            return broadcast

        return inner

    try:
        user_class = user.profile.acct_type if user.is_authenticated(
        ) else 'anonymous'
    except Profile.DoesNotExist:
        user_class = 'anonymous'
    return cache_get_or_set(
        'sb:%s:broadcast' % user_class, load_broadcast(user_class),
        settings.DEFAULT_CACHE_TIMEOUT
    )


def sidebar_info(request):
    """Displays info about a user's requsts in the sidebar"""
    # content for all users
    if request.path.startswith(('/admin/', '/sitemap', '/news-sitemaps')):
        return {}
    sidebar_info_dict = {
        'dropdown_recent_articles': get_recent_articles(),
        'broadcast': sidebar_broadcast(request.user),
        'login_form': AuthenticationForm()
    }
    if request.user.is_authenticated():
        # content for logged in users
        sidebar_info_dict.update({
            'unread_notifications':
                get_unread_notifications(request.user),
            'actionable_requests':
                get_actionable_requests(request.user),
            'organization':
                get_organization(request.user),
            'my_projects':
                Project.objects.get_for_contributor(request.user).optimize()
                [:4],
            'payment_failed':
                request.user.profile.payment_failed
        })

    return sidebar_info_dict

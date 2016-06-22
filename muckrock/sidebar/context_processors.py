"""Context processors to ensure data is displayed in sidebar for all views"""

from django.contrib.auth.forms import AuthenticationForm

from datetime import datetime, timedelta

from muckrock.accounts.models import Profile
from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article
from muckrock.organization.models import Organization
from muckrock.project.models import Project
from muckrock.sidebar.models import Broadcast
from muckrock.utils import cache_get_or_set

def get_recent_articles():
    """Lists last five recent news articles"""
    return cache_get_or_set(
            'sb:recent_articles',
            lambda: Article.objects.get_published().order_by('-pub_date')[:10],
            600)

def get_actionable_requests(user):
    """Gets requests that require action or attention"""
    requests = FOIARequest.objects.filter(user=user).select_related('jurisdiction')
    updates = requests.filter(updated=True)
    started = requests.filter(status='started')
    payment = requests.filter(status='payment')
    fix = requests.filter(status='fix')
    return {
        'count': len(updates) + len(started) + len(payment) + len(fix),
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
    def load_organization(user):
        """Return a function to load the user's organization"""
        def inner():
            """Argument-less function to load user's organization"""
            org = None
            if user.profile.organization:
                org = user.profile.organization
            owned_org = Organization.objects.filter(owner=user)
            if owned_org.exists():
                # there should only ever be one. if there is more than one, just get the first.
                org = owned_org.first()
            return org
        return inner
    return cache_get_or_set(
            'sb:%s:user_org' % user.username,
            load_organization(user),
            600)

def sidebar_broadcast(user):
    """Displays a broadcast to a given usertype"""

    def load_broadcast(user_class):
        """Return a function to load the correct broadcast"""
        def inner():
            """Argument-less function to load correct broadcast"""
            try:
                # exclude stale broadcasts from displaying
                last_week = datetime.now() - timedelta(7)
                broadcast = Broadcast.objects.get(updated__gte=last_week, context=user_class).text
            except Broadcast.DoesNotExist:
                broadcast = ''
            return broadcast
        return inner

    try:
        user_class = user.profile.acct_type if user.is_authenticated() else 'anonymous'
    except Profile.DoesNotExist:
        user_class = 'anonymous'
    return cache_get_or_set(
            'sb:%s:broadcast' % user_class,
            load_broadcast(user_class),
            600)

def sidebar_info(request):
    """Displays info about a user's requsts in the sidebar"""
    # content for all users
    sidebar_info_dict = {
        'recent_articles': get_recent_articles(),
        'broadcast': sidebar_broadcast(request.user),
        'login_form': AuthenticationForm()
    }
    if request.user.is_authenticated():
        # content for logged in users
        sidebar_info_dict.update({
            'unread_notifications': get_unread_notifications(request.user),
            'actionable_requests': get_actionable_requests(request.user),
            'organization': get_organization(request.user),
            'my_projects': Project.objects.get_for_contributor(request.user).exists(),
            'payment_failed': request.user.profile.payment_failed
        })
    else:
        # content for logged out users
        pass
    return sidebar_info_dict

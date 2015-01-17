"""
Context processors to ensure data is displayed in sidebar for all views
"""
# from django.core.exceptions import DoesNotExist

from muckrock.foia.models import FOIARequest
from muckrock.sidebar.models import Sidebar

def sidebar_user_info(request):
    """Displays info about a user's requsts in the sidebar"""
    if request.user.is_authenticated():
        requests = FOIARequest.objects.filter(user=request.user)
        updates = requests.filter(updated=True)
        fixes = requests.filter(status='fix')
        drafts = requests.filter(status='started')
        payments = requests.filter(status='payment')
        return {
            'updates': updates,
            'fixes': fixes,
            'payments': payments,
            'drafts': drafts,
        }
    else:
        return {}

def sidebar_message(request):
    """Displays a message to a given usertype"""
    user = request.user
    try:
        user_class = user.get_profile().acct_type if user.is_authenticated() else 'anonymous'
    except Exception:
        user_class = 'anonymous'
    message = Sidebar.objects.get_text(user_class)
    return {'broadcast': message}

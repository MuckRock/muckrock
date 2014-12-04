from muckrock.foia.models import FOIARequest
from muckrock.sidebar.models import Sidebar, SIDEBAR_TITLES

def sidebar_user_info(request):
    if request.user.is_authenticated():
        requests = FOIARequest.objects.filter(user=request.user)
        updates = requests.filter(updated=True)
        fixes = requests.filter(status='fix')
        drafts = requests.filter(status='started')
        return {
            'updates': updates,
            'fixes': fixes,
            'drafts': drafts,
        }
    else:
        return {}

def sidebar_message(request):
    user = request.user
    user_class = user.get_profile().acct_type if user.is_authenticated() else 'anonymous'
    message = Sidebar.objects.get_text(user_class)
    return {'broadcast': message}

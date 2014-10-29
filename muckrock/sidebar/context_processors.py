from muckrock.foia.models import FOIARequest, STATUS

def sidebar_user_info (request):
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
"""
Site-wide context processors
"""
from django.conf import settings

from muckrock.forms import NewsletterSignupForm

def google_analytics(request):
    """
    Retrieve and delete any google analytics session data and send it to the template
    """
    return {'ga': request.session.pop('ga', None)}

def newsletter(request):
    """Add newsletter form to context."""
    form = NewsletterSignupForm(initial={'list': settings.MAILCHIMP_LIST_DEFAULT})
    return {'newsletter_form': form}

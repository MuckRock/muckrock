"""
Utility method for the accounts application
"""

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.forms import ValidationError
from django.utils.safestring import mark_safe

# Standard Library
import json
import logging
import random
import re
import string
from datetime import date
from hashlib import md5

# Third Party
import requests
import stripe
from social_django.utils import load_backend, load_strategy

# MuckRock
from muckrock.core.utils import retry_on_error, stripe_retry_on_error

logger = logging.getLogger(__name__)


def unique_username(name):
    """Create a globally unique username from a name and return it."""
    # username can be at most 150 characters
    # strips illegal characters from username
    base_username = re.sub(r"[^\w\-.@]", "", name)[:141]
    username = base_username
    while User.objects.filter(username__iexact=username).exists():
        username = "{}_{}".format(
            base_username, "".join(random.sample(string.ascii_letters, 8))
        )
    return username


def validate_stripe_email(email):
    """Validate an email from stripe"""
    if not email:
        return None
    if len(email) > 254:
        return None
    try:
        validate_email(email)
    except ValidationError:
        return None
    return email


def stripe_get_customer(email, description, name):
    """Get a customer for an authenticated or anonymous user"""
    return stripe_retry_on_error(
        stripe.Customer.create,
        description=description,
        email=email,
        name=name,
        idempotency_key=True,
    )


def mailchimp_subscribe(
    request, email, list_=settings.MAILCHIMP_LIST_DEFAULT, **kwargs
):
    """Adds the email to the mailing list throught the MailChimp API.
    http://developer.mailchimp.com/documentation/mailchimp/reference/lists/members/"""
    api_url = settings.MAILCHIMP_API_ROOT + "/lists/" + list_ + "/members/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "apikey %s" % settings.MAILCHIMP_API_KEY,
    }
    merge_fields = {}
    if "url" in kwargs:
        merge_fields["URL"] = kwargs["url"]
    if "source" in kwargs:
        merge_fields["SOURCE"] = kwargs["source"]
    data = {
        "email_address": email,
        "status": "subscribed",
        "merge_fields": merge_fields,
        "tags": ["Newsletter For the Record"],
    }
    response = retry_on_error(
        requests.ConnectionError, requests.post, api_url, json=data, headers=headers
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exception:
        if response.status_code == 400 and response.json()["title"] == "Member Exists":
            if not kwargs.get("suppress_msg"):
                messages.error(request, "Email is already a member of this list")
        else:
            if not kwargs.get("suppress_msg"):
                messages.error(
                    request, "Sorry, an error occurred while trying to subscribe you."
                )
            logger.warning(exception)
        return True

    if not kwargs.get("suppress_msg"):
        messages.success(
            request,
            "Thank you for subscribing to our newsletter. We sent a "
            "confirmation email to your inbox.",
        )
    mixpanel_event(request, "Newsletter Sign Up", {"Email": email, "List": list_})
    return False


def mailchimp_donor_tag(email):
    """Tag a donor on mailchimp"""

    list_ = settings.MAILCHIMP_LIST_DEFAULT
    subscriber_hash = md5(email.lower().encode()).hexdigest()

    # first ensure they are on the wide list
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"apikey {settings.MAILCHIMP_API_KEY}",
    }
    api_url = f"{settings.MAILCHIMP_API_ROOT}/lists/{list_}/members/{subscriber_hash}"
    data = {
        "email_address": email,
        "status_if_new": "unsubscribed",
    }
    response = retry_on_error(
        requests.ConnectionError, requests.put, api_url, json=data, headers=headers
    )
    response.raise_for_status()

    # then tag them
    api_url += "/tags"
    data = {
        "tags": [
            {"name": date.today().strftime("donor %Y %B"), "status": "active"},
            {"name": "donor", "status": "active"},
        ]
    }
    response = retry_on_error(
        requests.ConnectionError, requests.post, api_url, json=data, headers=headers
    )
    response.raise_for_status()


def mixpanel_event(request, event, props=None, **kwargs):
    """Add an event to the session to be sent via javascript on the next page
    load
    """
    # only tracking logged in users for now
    if props is None:
        props = {}
    if "mp_events" in request.session:
        request.session["mp_events"].append((event, mark_safe(json.dumps(props))))
    else:
        request.session["mp_events"] = [(event, mark_safe(json.dumps(props)))]
    if kwargs.get("signup"):
        request.session["mp_alias"] = True
    if kwargs.get("charge"):
        request.session["mp_charge"] = kwargs["charge"]


def mini_login(request, username, password):
    """Provide authentication via squarelet via the password grant type"""
    strategy = load_strategy(request)
    backend = load_backend(strategy, "squarelet", redirect_uri=None)
    backend.password_grant_auth = (username, password)
    backend.STATE_PARAMETER = False
    backend.REDIRECT_STATE = False
    user = backend.complete(request=request)
    return user


def user_entitlement_count(entitlement):
    """Count how many users have a certain entitlement"""
    User.objects.filter(organizations__entitlement__slug=entitlement).distinct().count()

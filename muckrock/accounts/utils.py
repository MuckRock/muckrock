"""
Utility method for the accounts application
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.forms import ValidationError

from datetime import date
import re
import stripe

from muckrock.accounts.models import Profile
from muckrock.utils import stripe_retry_on_error, generate_key


def miniregister(full_name, email):
    """
    Create a new user from just their full name and email and return the user.
    - compress first and last name to create username
        - username must be unique
        - if the username already exists, add a number to the end
    - given the username, email create a new User
    - split the full name string to get the first and last names
    - create a Profile for the user
    - send the user a welcome email with a link to reset their password
    """
    from muckrock.message.tasks import welcome_miniregister
    password = generate_key(12)
    full_name = full_name.strip()
    username = unique_username(full_name)
    first_name, last_name = split_name(full_name)
    # create a new User
    user = User.objects.create_user(
        username,
        email,
        password,
        first_name=first_name,
        last_name=last_name
    )
    # create a new Profile
    Profile.objects.create(
        user=user,
        acct_type='basic',
        monthly_requests=settings.MONTHLY_REQUESTS.get('basic', 0),
        date_update=date.today()
    )
    # send the new user a welcome email
    welcome_miniregister.delay(user)
    return user, password


def split_name(name):
    """Splits a full name into a first and last name."""
    # infer first and last names from the full name
    # limit first and last names to 30 characters each
    if ' ' in name:
        first_name, last_name = name.rsplit(' ', 1)
        first_name = first_name[:30]
        last_name = last_name[:30]
    else:
        first_name = name[:30]
        last_name = ''
    return first_name, last_name


def unique_username(name):
    """Create a globally unique username from a name and return it."""
    # username can be at most 30 characters
    # strips illegal characters from username
    base_username = re.sub(r'[^\w\-.@]', '', name)[:30]
    username = base_username
    num = 1
    while User.objects.filter(username__iexact=username).exists():
        postfix = str(num)
        username = '%s%s' % (base_username[:30 - len(postfix)], postfix)
        num += 1
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


def stripe_get_customer(user, email, description):
    """Get a customer for an authenticated or anonymous user"""
    if user and user.is_authenticated:
        return user.profile.customer()
    else:
        return stripe_retry_on_error(
                stripe.Customer.create,
                description=description,
                email=email,
                idempotency_key=True,
                )

"""
Utility functions for communication app
"""

# Django
from django.core.validators import ValidationError

# MuckRock
from muckrock.communication.models import EmailAddress, PhoneNumber


def get_email_or_fax(email_or_fax):
    """Convert a string into either an email or phone number model"""

    # fetch validates the email
    email = EmailAddress.objects.fetch(email_or_fax)
    if email is not None:
        return email

    # not a valid email, try fax
    # fetch validates the phone number
    fax = PhoneNumber.objects.fetch(email_or_fax)
    if fax is not None:
        return fax

    # neither is valid, raise an error
    raise ValidationError("Invalid email or fax")

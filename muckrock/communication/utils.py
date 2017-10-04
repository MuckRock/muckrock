"""
Utility functions for communication app
"""

from django.core.validators import ValidationError

import phonenumbers

from muckrock.communication.models import EmailAddress, PhoneNumber


def get_email_or_fax(email_or_fax):
    """Convert a string into either an email or phone number model"""
    # fetch validates the email
    email = EmailAddress.objects.fetch(email_or_fax)
    if email:
        return email
    try:
        number = phonenumbers.parse(email_or_fax, 'US')
        if not phonenumbers.is_valid_number(number):
            raise ValidationError('Invalid email or fax')
        phone, _ = PhoneNumber.objects.update_or_create(
                number=number,
                defaults={'type': 'fax'},
                )
        return phone
    except phonenumbers.NumberParseException:
        raise ValidationError('Invalid email or fax')

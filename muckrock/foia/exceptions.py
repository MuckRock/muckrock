"""
Exceptions for the FOIA app
"""


class FoiaFormError(Exception):
    """If a form fails validation during FOIA detail view"""


class MimeError(Exception):
    """Try to attach a file with a disallowed mime type"""


class SizeError(Exception):
    """Uploaded file is not the correct size"""


class InsufficientRequestsError(Exception):
    """User needs to purchase more requests"""

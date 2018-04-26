"""
Exceptions for the FOIA app
"""


class FoiaFormError(Exception):
    """If a form fails validation during FOIA detail view"""


class SizeError(Exception):
    """Uploaded file is not the correct size"""


class InsufficientRequestsError(Exception):
    """User needs to purchase more requests"""

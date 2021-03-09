"""
Exceptions for the FOIA app
"""


class FoiaFormError(Exception):
    """If a form fails validation during FOIA detail view"""

    def __init__(self, form_name, form, comm_id=None):
        self.form_name = form_name
        self.form = form
        self.comm_id = comm_id
        super().__init__()


class SizeError(Exception):
    """Uploaded file is not the correct size"""


class InsufficientRequestsError(Exception):
    """User needs to purchase more requests"""

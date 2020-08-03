"""
M2M Through Models for Agency communication addresses
"""

# Django
from django.db import models

REQUEST_TYPES = (("primary", "Primary"), ("appeal", "Appeal"), ("none", "None"))
ADDRESS_REQUEST_TYPES = (
    ("primary", "Primary"),
    ("appeal", "Appeal"),
    ("check", "Check"),
    ("none", "None"),
)

EMAIL_TYPES = (("to", "To"), ("cc", "CC"), ("none", "None"))


class AgencyAddress(models.Model):
    """Through model for agency to address M2M"""

    agency = models.ForeignKey("Agency", on_delete=models.CASCADE)
    address = models.ForeignKey("communication.Address", on_delete=models.PROTECT)
    request_type = models.CharField(
        max_length=7, choices=ADDRESS_REQUEST_TYPES, default="none"
    )

    def __str__(self):
        val = str(self.address)
        if self.request_type != "none":
            val = "%s\n(%s)" % (val, self.request_type)
        return val


class AgencyEmail(models.Model):
    """Through model for agency to email M2M"""

    agency = models.ForeignKey("Agency", on_delete=models.CASCADE)
    email = models.ForeignKey("communication.EmailAddress", on_delete=models.PROTECT)
    request_type = models.CharField(max_length=7, choices=REQUEST_TYPES, default="none")
    email_type = models.CharField(max_length=4, choices=EMAIL_TYPES, default="none")

    def __str__(self):
        val = str(self.email)
        if self.request_type != "none" and self.email_type != "none":
            val = "%s (%s - %s)" % (val, self.request_type, self.email_type)
        return val


class AgencyPhone(models.Model):
    """Through model for agency to phone M2M"""

    agency = models.ForeignKey("Agency", on_delete=models.CASCADE)
    phone = models.ForeignKey("communication.PhoneNumber", on_delete=models.PROTECT)
    request_type = models.CharField(max_length=7, choices=REQUEST_TYPES, default="none")

    def __str__(self):
        val = str(self.phone)
        if self.request_type != "none":
            val = "%s (%s)" % (val, self.request_type)
        return val

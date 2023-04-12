"""
Models for FOIAs obtained from an agency's FOIA Logs
"""

# Django
from django.db import models


class FOIALog(models.Model):
    """A FOIA from a FOIA Log"""

    request_id = models.CharField(max_length=255, unique=True)
    requestor = models.CharField(max_length=255)
    subject = models.TextField()
    date = models.DateField()
    agency = models.ForeignKey(
        "agency.Agency",
        on_delete=models.PROTECT,
    )

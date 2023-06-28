"""
Models for FOIAs obtained from an agency's FOIA Logs
"""

# Django
from django.db import models

# MuckRock
from muckrock.foia.models.request import STATUS
from django.template.loader import render_to_string


class FOIALog(models.Model):
    """A FOIA from a FOIA Log"""

    class Meta:
        ordering = ["date_requested"]
        verbose_name = "FOIA Log"
        app_label = "foia"

    request_id = models.CharField(max_length=255, unique=True)
    requestor = models.CharField(max_length=255)
    subject = models.TextField()
    date_requested = models.DateField()
    date_completed = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS, blank=True)
    agency = models.ForeignKey(
        "agency.Agency",
        on_delete=models.PROTECT,
    )
    foia_request = models.ForeignKey(
        "foia.foiarequest",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    def request_copy(self):
        """Prepares language for requesting a copy of any responsive documents"""
        return render_to_string(
            "text/foia/copy_log.txt",
            {
                "request_id": self.request_id,
                "date_requested": self.date_requested,
                "subject": self.subject
            },
        )

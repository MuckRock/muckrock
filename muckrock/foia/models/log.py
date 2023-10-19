"""
Models for FOIAs obtained from an agency's FOIA Logs
"""

# Django
from django.contrib.auth.models import User
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

# MuckRock
from muckrock.foia.models.request import STATUS


class FOIALog(models.Model):
    """A FOIA log is a collection of FOIA log entries"""

    class Meta:
        verbose_name = "FOIA Log"
        app_label = "foia"

    agency = models.ForeignKey(
        "agency.Agency",
        on_delete=models.PROTECT,
    )
    start_date = models.DateField()
    end_date = models.DateField()
    contributed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="foia_logs",
        blank=True,
        null=True,
    )
    internal_note = models.TextField(blank=True)
    source = models.CharField(
        max_length=255,
        blank=True,
        help_text="URL, MuckRock request, or wherever the log was obtained from",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="+",
    )

    def __str__(self):
        return f"{self.agency} FOIA Log from {self.start_date} to {self.end_date}"


class FOIALogEntry(models.Model):
    """A FOIA from a FOIA Log"""

    class Meta:
        ordering = ["date_requested"]
        verbose_name = "FOIA Log Entry"
        verbose_name_plural = "FOIA Log Entries"
        app_label = "foia"

    request_id = models.CharField(max_length=255)
    requester = models.CharField(max_length=255, blank=True)
    requester_organization = models.CharField(max_length=255, blank=True)
    subject = models.TextField()
    exemptions = models.CharField(max_length=255, blank=True)
    date_requested = models.DateField(blank=True, null=True)
    date_completed = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS, blank=True)
    foia_request = models.ForeignKey(
        "foia.foiarequest",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    foia_log = models.ForeignKey(
        FOIALog,
        on_delete=models.CASCADE,
    )
    datetime_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"FOIA Log Entry #{self.request_id}"

    @property
    def agency(self):
        """Get the agency from the FOIA Log"""
        return self.foia_log.agency

    def request_copy(self):
        """Prepares language for requesting a copy of any responsive documents"""
        return render_to_string(
            "text/foia/copy_log.txt",
            {
                "request_id": self.request_id,
                "date_requested": self.date_requested,
                "subject": self.subject,
            },
        )

    def get_absolute_url(self):
        """The url for this object"""
        return reverse("foia-log", kwargs={"idx": self.pk})

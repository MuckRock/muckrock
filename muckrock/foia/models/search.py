"""
Models for saving searches for future use
"""

# Django
from django.db import models
from django.http.request import QueryDict

# MuckRock
from muckrock.foia.models.request import STATUS

BLANK_STATUS = [("", "-")] + STATUS


class FOIASavedSearch(models.Model):
    """A query and filter values for search reuse"""

    # for keeping track of the saved search
    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    title = models.CharField(max_length=255)

    # fields to search and filter on
    query = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=BLANK_STATUS)
    users = models.ManyToManyField("auth.User", related_name="+")
    agencies = models.ManyToManyField("agency.Agency")
    jurisdictions = models.ManyToManyField(
        "jurisdiction.Jurisdiction", through="SearchJurisdiction"
    )
    projects = models.ManyToManyField("project.Project")
    tags = models.ManyToManyField("tags.Tag")
    embargo = models.BooleanField(null=True, blank=True)
    exclude_crowdfund = models.BooleanField(null=True, blank=True)
    min_pages = models.PositiveSmallIntegerField(blank=True, null=True)
    min_date = models.DateField(blank=True, null=True)
    max_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.title

    def urlencode(self):
        """Return a URL encoded GET string"""

        def convert_date(date):
            """Get date into correct format"""
            if date is None:
                return ""
            else:
                return date.strftime("%m/%d/%Y")

        params = QueryDict("", mutable=True)
        min_pages = self.min_pages if self.min_pages is not None else ""
        min_date = convert_date(self.min_date)
        max_date = convert_date(self.max_date)
        params.update(
            {
                "q": self.query,
                "status": self.status,
                "has_embargo": self.embargo,
                "has_crowdfund": self.exclude_crowdfund,
                "minimum_pages": min_pages,
                "date_range_0": min_date,
                "date_range_1": max_date,
                "search_title": self.title,
            }
        )
        params.setlist("user", self.users.values_list("pk", flat=True))
        params.setlist("agency", self.agencies.values_list("pk", flat=True))
        params.setlist("projects", self.projects.values_list("pk", flat=True))
        params.setlist("tags", self.tags.values_list("pk", flat=True))
        params.setlist(
            "jurisdiction", [str(j) for j in self.searchjurisdiction_set.all()]
        )
        return params.urlencode()

    class Meta:
        unique_together = ("user", "title")


class SearchJurisdiction(models.Model):
    """Many to many through model for jurisdictions"""

    search = models.ForeignKey(FOIASavedSearch, on_delete=models.CASCADE)
    jurisdiction = models.ForeignKey(
        "jurisdiction.Jurisdiction", on_delete=models.CASCADE
    )
    include_local = models.BooleanField()

    def __str__(self):
        return "{}-{}".format(self.jurisdiction_id, self.include_local)

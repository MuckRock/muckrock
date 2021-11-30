# -*- coding: utf-8 -*-
"""Models for the Crowdsource application"""

# Django
from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.core.mail.message import EmailMessage
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models.aggregates import Count
from django.db.models.expressions import Case, Value, When
from django.db.models.functions import Concat
from django.db.models.functions.datetime import TruncDay
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# Standard Library
import json
from html import unescape
from random import choice

# Third Party
from bleach.sanitizer import Cleaner
from pkg_resources import resource_filename
from pyembed.core import PyEmbed
from pyembed.core.consumer import PyEmbedConsumerError
from pyembed.core.discovery import AutoDiscoverer, ChainingDiscoverer, FileDiscoverer
from taggit.managers import TaggableManager

# MuckRock
from muckrock.crowdsource import fields
from muckrock.crowdsource.querysets import (
    CrowdsourceDataQuerySet,
    CrowdsourceQuerySet,
    CrowdsourceResponseQuerySet,
)
from muckrock.tags.models import TaggedItemBase


class Crowdsource(models.Model):
    """A Crowdsource"""

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    user = models.ForeignKey(
        "auth.User", related_name="crowdsources", on_delete=models.PROTECT
    )
    project = models.ForeignKey(
        "project.Project",
        related_name="crowdsources",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    datetime_created = models.DateTimeField(default=timezone.now)
    datetime_opened = models.DateTimeField(blank=True, null=True)
    datetime_closed = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=9,
        default="draft",
        choices=(("draft", "Draft"), ("open", "Opened"), ("close", "Closed")),
    )
    description = models.TextField(help_text="May use markdown")
    project_only = models.BooleanField(
        default=False,
        help_text="Only members of the project will be able to complete "
        "assignments for this crowdsource",
    )
    project_admin = models.BooleanField(
        default=False,
        help_text="Members of this project will be able to manage this crowdsource "
        "as if they were the owner",
    )
    data_limit = models.PositiveSmallIntegerField(
        default=3,
        help_text="Number of times each data assignment will be completed "
        "(by different users) - only used if using data for this crowdsource",
        validators=[MinValueValidator(1)],
    )
    multiple_per_page = models.BooleanField(
        default=False,
        verbose_name="Allow multiple submissions per data item",
        help_text="This is useful for cases when there may be multiple "
        "records of interest per data source",
    )
    user_limit = models.BooleanField(
        default=True,
        help_text="Is the user limited to completing this form only once? "
        "(else, it is unlimited) - only used if not using data for this crowdsource",
    )
    registration = models.CharField(
        max_length=8,
        choices=(("required", "Required"), ("off", "Off"), ("optional", "Optional")),
        default="required",
        help_text="Is registration required to complete this assignment?",
    )
    submission_emails = models.ManyToManyField("communication.EmailAddress")
    featured = models.BooleanField(
        default=False, help_text="Featured assignments will appear on the homepage."
    )
    ask_public = models.BooleanField(
        default=True,
        help_text="Add a field asking users if we can publically credit them "
        "for their response",
    )

    objects = CrowdsourceQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """URL"""
        return reverse("crowdsource-detail", kwargs={"slug": self.slug, "idx": self.pk})

    def get_data_to_show(self, user, ip_address):
        """Get the crowdsource data to show"""
        options = self.data.get_choices(self.data_limit, user, ip_address)
        if options:
            return choice(options)
        else:
            return None

    @transaction.atomic
    def create_form(self, form_json):
        """Create the crowdsource form from the form builder json"""
        form_data = json.loads(form_json)
        seen_labels = set()
        cleaner = Cleaner(tags=[], attributes={}, styles=[], strip=True)
        # reset the order for all fields to avoid violating the unique constraint
        # it also allows for detection of deleted fields
        self.fields.update(order=None)
        for order, field_data in enumerate(form_data):
            label = cleaner.clean(field_data["label"])[:255]
            label = unescape(label)
            label = self._uniqify_label_name(seen_labels, label)
            description = cleaner.clean(field_data.get("description", ""))[:255]
            kwargs = {
                "label": label,
                "type": field_data["type"],
                "help_text": description,
                "min": field_data.get("min"),
                "max": field_data.get("max"),
                "required": field_data.get("required", False),
                "gallery": field_data.get("gallery", False),
                "order": order,
            }
            try:
                field = self.fields.get(pk=field_data.get("name"))
                self.fields.filter(pk=field.pk).update(**kwargs)
            except (CrowdsourceField.DoesNotExist, ValueError):
                field = self.fields.create(**kwargs)

            if "values" in field_data and field.field.accepts_choices:
                # delete existing choices and re-create them to avoid
                # violating unique constraints on edits, and to delete removed
                # choices - responses store by value, so this does not destroy
                # any data
                field.choices.all().delete()
                for choice_order, value in enumerate(field_data["values"]):
                    field.choices.update_or_create(
                        choice=cleaner.clean(value["label"])[:255],
                        defaults=dict(
                            value=cleaner.clean(value["value"])[:255],
                            order=choice_order,
                        ),
                    )
        # any field which has no order after all fields are
        # re-created has been deleted
        self.fields.filter(order=None).update(deleted=True)

    def _uniqify_label_name(self, seen_labels, label):
        """Ensure the label names are all unique"""
        new_label = label
        i = 0
        while new_label in seen_labels:
            i += 1
            postfix = str(i)
            new_label = "{}-{}".format(label[: 254 - len(postfix)], postfix)
        seen_labels.add(new_label)
        return new_label

    def get_form_json(self):
        """Get the form JSON for editing the form"""
        return json.dumps([f.get_json() for f in self.fields.filter(deleted=False)])

    def get_header_values(self, metadata_keys, include_emails=False):
        """Get header values for CSV export"""
        values = ["user", "public", "datetime", "skip", "flag", "gallery", "tags"]
        if include_emails:
            values.insert(1, "email")
        if self.multiple_per_page:
            values.append("number")
        if self.data.exists():
            values.append("datum")
            values.extend(metadata_keys)
        field_labels = list(
            self.fields.exclude(type__in=fields.STATIC_FIELDS).values_list(
                Case(
                    When(deleted=True, then=Concat("label", Value(" (deleted)"))),
                    default="label",
                ),
                flat=True,
            )
        )
        return values + field_labels

    def get_metadata_keys(self):
        """Get the metadata keys for this crowdsource's data"""
        datum = self.data.first()
        if datum:
            return list(datum.metadata.keys())
        else:
            return []

    def total_assignments(self):
        """Total assignments to be completed"""
        if not self.data.all():
            return None
        return len(self.data.all()) * self.data_limit

    def percent_complete(self):
        """Percent of tasks complete"""
        total = self.total_assignments()
        if not total:
            return 0
        return int(100 * self.responses.count() / float(total))

    def contributor_line(self):
        """Line about who has contributed"""
        responses = self.responses.select_related("user__profile")
        users = list({r.user for r in responses if r.user and r.public})
        total = len(users)

        def join_names(users):
            """Create a comma seperated list of user names"""
            return ", ".join(u.profile.full_name or u.username for u in users)

        if total > 4:
            return "{} and {} others helped".format(join_names(users[:3]), total - 3)
        elif total > 1:
            return "{} and {} helped".format(
                join_names(users[:-1]),
                users[-1].profile.full_name or users[-1].username,
            )
        elif total == 1:
            return "{} helped".format(users[0].profile.full_name or users[0].username)
        elif responses:
            # there have been responses, but none of them are public
            return ""
        else:
            return "No one has helped yet, be the first!"

    def responses_per_day(self):
        """How many responses there have been per day"""
        return (
            self.responses.annotate(date=TruncDay("datetime"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

    class Meta:
        verbose_name = "assignment"
        permissions = (
            (
                "form_crowdsource",
                "Can view and fill out the assignments for this crowdsource",
            ),
        )


class CrowdsourceData(models.Model):
    """A source of data to show with the crowdsource questions"""

    crowdsource = models.ForeignKey(
        Crowdsource, related_name="data", on_delete=models.CASCADE
    )
    url = models.URLField(max_length=255, verbose_name="Data URL", blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    objects = CrowdsourceDataQuerySet.as_manager()

    def __str__(self):
        return "Crowdsource Data: {}".format(self.url)

    def embed(self):
        """Get the html to embed into the crowdsource"""
        if self.url:
            try:
                # first try to get embed code from oEmbed
                return mark_safe(
                    PyEmbed(
                        # we don't use the default discoverer because it contains a bug
                        # that makes it always match spotify
                        discoverer=ChainingDiscoverer(
                            [
                                FileDiscoverer(
                                    resource_filename(__name__, "oembed_providers.json")
                                ),
                                AutoDiscoverer(),
                            ]
                        )
                    ).embed(self.url, max_height=400)
                )
            except PyEmbedConsumerError:
                # fall back to a simple iframe
                return format_html(
                    '<iframe src="{}" width="100%" height="400px"></iframe>', self.url
                )
        else:
            return ""

    class Meta:
        verbose_name = "assignment data"


class CrowdsourceField(models.Model):
    """A field on a crowdsource form"""

    crowdsource = models.ForeignKey(
        Crowdsource, related_name="fields", on_delete=models.CASCADE
    )
    label = models.CharField(max_length=255)
    type = models.CharField(max_length=15, choices=fields.FIELD_CHOICES)
    help_text = models.CharField(max_length=255, blank=True)
    min = models.PositiveSmallIntegerField(blank=True, null=True)
    max = models.PositiveSmallIntegerField(blank=True, null=True)
    required = models.BooleanField(default=True)
    gallery = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(blank=True, null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        if self.deleted:
            return "{} (Deleted)".format(self.label)
        else:
            return self.label

    def get_form_field(self):
        """Return a form field appropriate for rendering this field"""
        return self.field().get_form_field(self)

    def get_json(self):
        """Get the JSON represenation for this field"""
        data = {
            "type": self.type,
            "label": self.label,
            "description": self.help_text,
            "required": self.required,
            "gallery": self.gallery,
            "name": str(self.pk),
        }
        if self.field.accepts_choices:
            data["values"] = [
                {"label": c.choice, "value": c.value} for c in self.choices.all()
            ]
        if self.min is not None:
            data["min"] = self.min
        if self.max is not None:
            data["max"] = self.max
        return data

    @property
    def field(self):
        """Get the crowdsource field instance"""
        return fields.FIELD_DICT[self.type]

    class Meta:
        verbose_name = "assignment field"
        ordering = ("order",)
        unique_together = (("crowdsource", "label"), ("crowdsource", "order"))


class CrowdsourceChoice(models.Model):
    """A choice presented to crowdsource users"""

    field = models.ForeignKey(
        CrowdsourceField, related_name="choices", on_delete=models.CASCADE
    )
    choice = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.choice

    class Meta:
        verbose_name = "assignment choice"
        ordering = ("order",)
        unique_together = (("field", "choice"), ("field", "order"))


class CrowdsourceResponse(models.Model):
    """A response to a crowdsource question"""

    crowdsource = models.ForeignKey(
        Crowdsource, related_name="responses", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        "auth.User",
        related_name="crowdsource_responses",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    public = models.BooleanField(
        default=False,
        help_text="Publically credit the user who submitted this response in the gallery",
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    datetime = models.DateTimeField(default=timezone.now)
    data = models.ForeignKey(
        CrowdsourceData,
        blank=True,
        null=True,
        related_name="responses",
        on_delete=models.PROTECT,
    )
    skip = models.BooleanField(default=False)
    # number is only used for multiple_per_page crowdsources,
    # keeping track of how many times a single user has submitted
    # per data item
    number = models.PositiveSmallIntegerField(default=1)
    flag = models.BooleanField(default=False)
    gallery = models.BooleanField(default=False)

    # edits
    edit_user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="edited_crowdsource_responses",
    )
    edit_datetime = models.DateTimeField(null=True, blank=True)

    objects = CrowdsourceResponseQuerySet.as_manager()
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    def __str__(self):
        if self.user:
            from_ = str(self.user)
        elif self.ip_address:
            from_ = str(self.ip_address)
        else:
            from_ = "Anonymous"
        return "Response by {} on {}".format(from_, self.datetime)

    def get_values(self, metadata_keys, include_emails=False):
        """Get the values for this response for CSV export"""
        values = [
            self.user.username if self.user else "Anonymous",
            self.public,
            self.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            self.skip,
            self.flag,
            self.gallery,
            ", ".join(self.tags.values_list("name", flat=True)),
        ]
        if include_emails:
            values.insert(1, self.user.email if self.user else "")
        if self.crowdsource.multiple_per_page:
            values.append(self.number)
        if self.data:
            values.append(self.data.url)
            values.extend(self.data.metadata.get(k, "") for k in metadata_keys)
        field_labels = self.crowdsource.fields.exclude(
            type__in=fields.STATIC_FIELDS
        ).values_list("label", flat=True)
        field_values = self.get_field_values()
        # ensure exactly one value per field - default to empty string
        # a multivalued field may have no values
        values += [field_values.get(label, "") for label in field_labels]
        return values

    def get_field_values(self):
        """Return a dictionary of field labels to field values
        This handle filtering and aggregating of multivalued fields
        """
        return dict(
            self.values.order_by("field__order")
            # exclude headers and paragraph fields
            .exclude(field__type__in=fields.STATIC_FIELDS)
            # filter out blank values for multivalued fields
            # there might be blank ones to hold original values,
            # and we do not want that in the comma separated list
            .exclude(value="", field__type__in=fields.MULTI_FIELDS)
            # group by field
            .values("field")
            # concat all values for the same field with commas
            .annotate(agg_value=StringAgg("value", ", "))
            # select the concated value
            .values_list("field__label", "agg_value")
        )

    def create_values(self, data):
        """Given the form data, create the values for this response"""
        # these values are passed in the form, but should not have
        # values created for them
        for key in ["data_id", "full_name", "email", "newsletter", "public"]:
            data.pop(key, None)
        for pk, value in data.items():
            value = value if value is not None else ""
            if not isinstance(value, list):
                value = [value]
            for value_item in value:
                try:
                    field = CrowdsourceField.objects.get(
                        crowdsource=self.crowdsource, pk=pk
                    )
                    self.values.create(
                        field=field, value=value_item, original_value=value_item
                    )
                except CrowdsourceField.DoesNotExist:
                    pass

    def send_email(self, email):
        """Send an email of this response"""
        metadata = self.crowdsource.get_metadata_keys()
        text = "\n".join(
            "{}: {}".format(k, v)
            for k, v in zip(
                self.crowdsource.get_header_values(metadata), self.get_values(metadata)
            )
        )
        text += "\n{}{}#assignment-responses".format(
            settings.MUCKROCK_URL, self.crowdsource.get_absolute_url()
        )
        EmailMessage(
            subject="[Assignment Response] {} by {}".format(
                self.crowdsource.title, self.user.username if self.user else "Anonymous"
            ),
            body=text,
            from_email=settings.ASSIGNMENTS_EMAIL,
            to=[email],
            bcc=[settings.DIAGNOSTIC_EMAIL],
        ).send(fail_silently=False)

    class Meta:
        verbose_name = "assignment response"


class CrowdsourceValue(models.Model):
    """A field value for a given response"""

    response = models.ForeignKey(
        CrowdsourceResponse, related_name="values", on_delete=models.CASCADE
    )
    field = models.ForeignKey(
        CrowdsourceField, related_name="values", on_delete=models.CASCADE
    )
    value = models.CharField(max_length=2000, blank=True)
    original_value = models.CharField(max_length=2000, blank=True)

    def __str__(self):
        return self.value

    class Meta:
        verbose_name = "assignment value"

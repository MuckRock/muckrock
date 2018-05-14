# -*- coding: utf-8 -*-
"""Models for the Crowdsource application"""

# Django
from django.contrib.postgres.fields import JSONField
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# Standard Library
import json
from HTMLParser import HTMLParser
from random import choice

# Third Party
from bleach.sanitizer import Cleaner
from pyembed.core import PyEmbed
from pyembed.core.consumer import PyEmbedConsumerError

# MuckRock
from muckrock.crowdsource import fields
from muckrock.crowdsource.constants import DOCUMENT_URL_RE

DOCCLOUD_EMBED = """
<div class="DC-embed DC-embed-document DV-container">
  <div style="position:relative;padding-bottom:129.42857142857142%;height:0;overflow:hidden;max-width:100%;">
    <iframe
        src="//www.documentcloud.org/documents/{doc_id}.html?
            embed=true&amp;responsive=false&amp;sidebar=false"
        title="{doc_id} (Hosted by DocumentCloud)"
        sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
        frameborder="0"
        style="position:absolute;top:0;left:0;width:100%;height:100%;border:1px solid #aaa;border-bottom:0;box-sizing:border-box;">
    </iframe>
  </div>
</div>
"""


class CrowdsourceQuerySet(models.QuerySet):
    """Object manager for crowdsources"""

    def get_viewable(self, user):
        """Get the viewable crowdsources for the user"""
        if user.is_staff:
            return self
        elif user.is_authenticated:
            return self.filter(
                Q(user=user) | Q(status='open', project_only=False) |
                Q(status='open', project_only=True, project__contributors=user)
            )
        else:
            return self.filter(status='open', project_only=False)


class Crowdsource(models.Model):
    """A Crowdsource"""

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    user = models.ForeignKey('auth.User', related_name='crowdsources')
    project = models.ForeignKey(
        'project.Project',
        related_name='crowdsources',
        blank=True,
        null=True,
    )
    datetime_created = models.DateTimeField(default=timezone.now)
    datetime_opened = models.DateTimeField(blank=True, null=True)
    datetime_closed = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=9,
        default='draft',
        choices=(
            ('draft', 'Draft'),
            ('open', 'Opened'),
            ('close', 'Closed'),
        )
    )
    description = models.TextField(help_text='May use markdown')
    project_only = models.BooleanField(
        default=False,
        help_text='Only members of the project will be able to complete '
        'assignments for this crowdsource',
    )
    data_limit = models.PositiveSmallIntegerField(
        default=3,
        help_text='Number of times each data assignment will be completed '
        '(by different users) - only used if using data for this crowdsource',
        validators=[MinValueValidator(1)],
    )
    multiple_per_page = models.BooleanField(
        default=False,
        verbose_name='Allow multiple submissions per data item',
        help_text='This is useful for cases when there may be multiple '
        'records of interest per data source',
    )
    user_limit = models.BooleanField(
        default=True,
        help_text='Is the user limited to completing this form only once? '
        '(else, it is unlimited) - only used if not using data for this crowdsource',
    )
    submission_email = models.EmailField(blank=True)

    objects = CrowdsourceQuerySet.as_manager()

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """URL"""
        return reverse(
            'crowdsource-detail',
            kwargs={
                'slug': self.slug,
                'idx': self.pk,
            },
        )

    def get_data_to_show(self, user):
        """Get the crowdsource data to show"""
        options = self.data.get_choices(self.data_limit, user)
        if options:
            return choice(options)
        else:
            return None

    def create_form(self, form_json):
        """Create the crowdsource form from the form builder json"""
        # delete any old fields and re-create from the new JSON
        self.fields.all().delete()
        form_data = json.loads(form_json)
        seen_labels = set()
        cleaner = Cleaner(tags=[], attributes={}, styles=[], strip=True)
        htmlparser = HTMLParser()
        for order, field_data in enumerate(form_data):
            label = cleaner.clean(field_data['label'])[:255]
            label = htmlparser.unescape(label)
            label = self._uniqify_label_name(seen_labels, label)
            field = self.fields.create(
                label=label,
                type=field_data['type'],
                help_text=cleaner.clean(
                    field_data.get('description', ''),
                )[:255],
                min=field_data.get('min'),
                max=field_data.get('max'),
                required=field_data.get('required', False),
                order=order,
            )
            if 'values' in field_data and field.field.accepts_choices:
                for choice_order, value in enumerate(field_data['values']):
                    field.choices.create(
                        choice=cleaner.clean(value['label'])[:255],
                        value=cleaner.clean(value['value'])[:255],
                        order=choice_order,
                    )

    def _uniqify_label_name(self, seen_labels, label):
        """Ensure the label names are all unique"""
        new_label = label
        i = 0
        while new_label in seen_labels:
            i += 1
            postfix = str(i)
            new_label = u'{}-{}'.format(label[:254 - len(postfix)], postfix)
        seen_labels.add(new_label)
        return new_label

    def get_form_json(self):
        """Get the form JSON for editing the form"""
        return json.dumps([f.get_json() for f in self.fields.all()])

    def get_header_values(self, metadata_keys):
        """Get header values for CSV export"""
        values = ['user', 'datetime', 'skip']
        if self.multiple_per_page:
            values.append('number')
        if self.data.exists():
            values.append('datum')
            values.extend(metadata_keys)
        field_labels = list(self.fields.values_list('label', flat=True))
        return values + field_labels

    def get_metadata_keys(self):
        """Get the metadata keys for this crowdsource's data"""
        datum = self.data.first()
        if datum:
            return datum.metadata.keys()
        else:
            return []

    def total_assignments(self):
        """Total assignments to be completed"""
        if not self.data.all():
            return None
        return len(self.data.all()) * self.data_limit

    class Meta:
        verbose_name = 'assignment'


class CrowdsourceDataQuerySet(models.QuerySet):
    """Object manager for crowdsource data"""

    def get_choices(self, data_limit, user):
        """Get choices for data to show"""
        choices = (
            self.annotate(count=models.Count('responses__user', distinct=True))
            .filter(count__lt=data_limit)
        )
        if user is not None:
            choices = choices.exclude(responses__user=user)
        return choices


class CrowdsourceData(models.Model):
    """A source of data to show with the crowdsource questions"""

    crowdsource = models.ForeignKey(Crowdsource, related_name='data')
    url = models.URLField(max_length=255, verbose_name='Data URL')
    metadata = JSONField(default=dict, blank=True)

    objects = CrowdsourceDataQuerySet.as_manager()

    def __unicode__(self):
        return u'Crowdsource Data: {}'.format(self.url)

    def embed(self):
        """Get the html to embed into the crowdsource"""
        try:
            # first try to get embed code from oEmbed
            return mark_safe(PyEmbed().embed(self.url, max_height=400))
        except PyEmbedConsumerError:
            # if this is a private document cloud document, it will not have
            # an oEmbed, create the embed manually
            doc_match = DOCUMENT_URL_RE.match(self.url)
            if doc_match:
                return mark_safe(
                    DOCCLOUD_EMBED.format(doc_id=doc_match.group('doc_id'))
                )
            else:
                # fall back to a simple iframe
                return format_html(
                    '<iframe src="{}" width="100%" height="400px"></iframe>',
                    self.url,
                )

    class Meta:
        verbose_name = 'assignment data'


class CrowdsourceField(models.Model):
    """A field on a crowdsource form"""

    crowdsource = models.ForeignKey(Crowdsource, related_name='fields')
    label = models.CharField(max_length=255)
    type = models.CharField(
        max_length=10,
        choices=fields.FIELD_CHOICES,
    )
    help_text = models.CharField(max_length=255, blank=True)
    min = models.PositiveSmallIntegerField(blank=True, null=True)
    max = models.PositiveSmallIntegerField(blank=True, null=True)
    required = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return self.label

    def get_form_field(self):
        """Return a form field appropriate for rendering this field"""
        return self.field().get_form_field(self)

    def get_json(self):
        """Get the JSON represenation for this field"""
        data = {
            'type': self.type,
            'label': self.label,
            'description': self.help_text,
            'required': self.required,
        }
        if self.field.accepts_choices:
            data['values'] = [{
                'label': c.choice,
                'value': c.value
            } for c in self.choices.all()]
        if self.min is not None:
            data['min'] = self.min
        if self.max is not None:
            data['max'] = self.max
        return data

    @property
    def field(self):
        """Get the crowdsource field instance"""
        return fields.FIELD_DICT[self.type]

    class Meta:
        verbose_name = 'assignment field'
        ordering = ('order',)
        unique_together = (
            ('crowdsource', 'label'),
            ('crowdsource', 'order'),
        )


class CrowdsourceChoice(models.Model):
    """A choice presented to crowdsource users"""

    field = models.ForeignKey(CrowdsourceField, related_name='choices')
    choice = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return self.choice

    class Meta:
        verbose_name = 'assignment choice'
        ordering = ('order',)
        unique_together = (
            ('field', 'choice'),
            ('field', 'order'),
        )


class CrowdsourceResponse(models.Model):
    """A response to a crowdsource question"""
    crowdsource = models.ForeignKey(Crowdsource, related_name='responses')
    user = models.ForeignKey('auth.User', related_name='crowdsource_responses')
    datetime = models.DateTimeField(default=timezone.now)
    data = models.ForeignKey(
        CrowdsourceData,
        blank=True,
        null=True,
        related_name='responses',
    )
    skip = models.BooleanField(default=False)
    # number is only used for multiple_per_page crowdsources,
    # keeping track of how many times a single user has submitted
    # per data item
    number = models.PositiveSmallIntegerField(default=1)

    def __unicode__(self):
        return u'Response by {} on {}'.format(
            self.user,
            self.datetime,
        )

    def get_values(self, metadata_keys):
        """Get the values for this response for CSV export"""
        values = [
            self.user.username,
            self.datetime.strftime('%Y-%m-%d %H:%M:%S'),
            self.skip,
        ]
        if self.crowdsource.multiple_per_page:
            values.append(self.number)
        if self.data:
            values.append(self.data.url)
            values.extend(self.data.metadata.get(k, '') for k in metadata_keys)
        values += list(
            self.values.order_by('field__order').values_list(
                'value', flat=True
            )
        )
        return values

    def create_values(self, data):
        """Given the form data, create the values for this response"""
        # these values are passed in the form, but should not have
        # values created for them
        for key in ['data_id', 'full_name', 'email', 'newsletter']:
            data.pop(key, None)
        for label, value in data.iteritems():
            try:
                field = CrowdsourceField.objects.get(
                    crowdsource=self.crowdsource,
                    label=label,
                )
                self.values.create(
                    field=field,
                    value=value if value is not None else '',
                )
            except CrowdsourceField.DoesNotExist:
                pass

    def send_email(self, email):
        """Send an email of this response"""
        metadata = self.crowdsource.get_metadata_keys()
        text = u'\n'.join(
            u'{}: {}'.format(k, v) for k, v in zip(
                self.crowdsource.get_header_values(metadata),
                self.get_values(metadata),
            )
        )
        send_mail(
            '[Assignment Response] {} by {}'.format(
                self.crowdsource.title,
                self.user.username,
            ),
            text,
            'info@muckrock.com',
            [email],
        )

    class Meta:
        verbose_name = 'assignment response'


class CrowdsourceValue(models.Model):
    """A field value for a given response"""

    response = models.ForeignKey(CrowdsourceResponse, related_name='values')
    field = models.ForeignKey(CrowdsourceField, related_name='values')
    value = models.CharField(max_length=2000)

    def __unicode__(self):
        return self.value

    class Meta:
        verbose_name = 'assignment value'

# -*- coding: utf-8 -*-
"""Models for the Crowdsource application"""

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.mail.message import EmailMessage
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# Standard Library
import json
from HTMLParser import HTMLParser
from random import choice

# Third Party
from bleach.sanitizer import Cleaner
from pkg_resources import resource_filename
from pyembed.core import PyEmbed
from pyembed.core.consumer import PyEmbedConsumerError
from pyembed.core.discovery import (
    AutoDiscoverer,
    ChainingDiscoverer,
    FileDiscoverer,
)
from taggit.managers import TaggableManager

# MuckRock
from muckrock.crowdsource import fields
from muckrock.crowdsource.constants import DOCUMENT_URL_RE
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
    project_admin = models.BooleanField(
        default=False,
        help_text=
        'Members of this project will be able to manage this crowdsource '
        'as if they were the owner',
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
    registration = models.CharField(
        max_length=8,
        choices=(
            ('required', 'Required'),
            ('off', 'Off'),
            ('optional', 'Optional'),
        ),
        default='required',
        help_text='Is registration required to complete this assignment?',
    )
    submission_emails = models.ManyToManyField('communication.EmailAddress')

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

    def get_data_to_show(self, user, ip_address):
        """Get the crowdsource data to show"""
        options = self.data.get_choices(self.data_limit, user, ip_address)
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
                gallery=field_data.get('gallery', False),
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

    def get_header_values(self, metadata_keys, include_emails=False):
        """Get header values for CSV export"""
        values = ['user', 'datetime', 'skip', 'flag', 'gallery', 'tags']
        if include_emails:
            values.insert(1, 'email')
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

    def percent_complete(self):
        """Percent of tasks complete"""
        total = self.total_assignments()
        if not total:
            return 0
        return int(100 * self.responses.count() / float(total))

    def contributor_line(self):
        """Line about who has contributed"""
        users = list({r.user for r in self.responses.all() if r.user})
        total = len(users)

        def join_names(users):
            """Create a comma seperated list of user names"""
            return ', '.join(u.profile.full_name or u.username for u in users)

        if total > 4:
            return '{} and {} others helped'.format(
                join_names(users[:3]), total - 3
            )
        elif total > 1:
            return '{} and {} helped'.format(
                join_names(users[:-1]), users[-1].profile.full_name
                or users[-1].username
            )
        elif total == 1:
            return '{} helped'.format(
                users[0].profile.full_name or users[0].username
            )
        else:
            return 'No one has helped yet, be the first!'

    class Meta:
        verbose_name = 'assignment'
        permissions = ((
            'form_crowdsource',
            'Can view and fill out the assignments for this crowdsource'
        ),)


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
            return mark_safe(
                PyEmbed(
                    # we don't use the default discoverer because it contains a bug
                    # that makes it always match spotify
                    discoverer=ChainingDiscoverer([
                        FileDiscoverer(
                            resource_filename(
                                __name__, 'oembed_providers.json'
                            )
                        ),
                        AutoDiscoverer(),
                    ])
                ).embed(self.url, max_height=400)
            )
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
    gallery = models.BooleanField(default=False)
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
            'gallery': self.gallery,
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
    user = models.ForeignKey(
        'auth.User',
        related_name='crowdsource_responses',
        blank=True,
        null=True,
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
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
    flag = models.BooleanField(default=False)
    gallery = models.BooleanField(default=False)

    # edits
    edit_user = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='edited_crowdsource_responses',
    )
    edit_datetime = models.DateTimeField(null=True, blank=True)

    objects = CrowdsourceResponseQuerySet.as_manager()
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    def __unicode__(self):
        if self.user:
            from_ = unicode(self.user)
        elif self.ip_address:
            from_ = unicode(self.ip_address)
        else:
            from_ = u'Anonymous'
        return u'Response by {} on {}'.format(
            from_,
            self.datetime,
        )

    def get_values(self, metadata_keys, include_emails=False):
        """Get the values for this response for CSV export"""
        values = [
            self.user.username if self.user else 'Anonymous',
            self.datetime.strftime('%Y-%m-%d %H:%M:%S'),
            self.skip,
            self.flag,
            self.gallery,
            ', '.join(self.tags.values_list('name', flat=True)),
        ]
        if include_emails:
            values.insert(1, self.user.email if self.user else '')
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
        for pk, value in data.iteritems():
            value = value if value is not None else ''
            try:
                field = CrowdsourceField.objects.get(
                    crowdsource=self.crowdsource,
                    pk=pk,
                )
                self.values.create(
                    field=field,
                    value=value,
                    original_value=value,
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
        text += '\n{}{}#assignment-responses'.format(
            settings.MUCKROCK_URL,
            self.crowdsource.get_absolute_url(),
        )
        EmailMessage(
            subject='[Assignment Response] {} by {}'.format(
                self.crowdsource.title,
                self.user.username if self.user else 'Anonymous',
            ),
            body=text,
            from_email='info@muckrock.com',
            to=[email],
            bcc=['diagnostics@muckrock.com'],
        ).send(fail_silently=False)

    class Meta:
        verbose_name = 'assignment response'


class CrowdsourceValue(models.Model):
    """A field value for a given response"""

    response = models.ForeignKey(CrowdsourceResponse, related_name='values')
    field = models.ForeignKey(CrowdsourceField, related_name='values')
    value = models.CharField(max_length=2000, blank=True)
    original_value = models.CharField(max_length=2000, blank=True)

    def __unicode__(self):
        return self.value

    class Meta:
        verbose_name = 'assignment value'

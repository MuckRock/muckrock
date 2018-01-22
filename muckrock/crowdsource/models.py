# -*- coding: utf-8 -*-
"""Models for the Crowdsource application"""

from django.contrib.postgres.fields import JSONField
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

import json
from pyembed.core import PyEmbed
from pyembed.core.consumer import PyEmbedConsumerError
from random import choice

from muckrock.crowdsource import fields


class Crowdsource(models.Model):
    """A Crowdsource"""

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    user = models.ForeignKey('auth.User', related_name='crowdsources')
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
                ))
    description = models.CharField(max_length=255)
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
        options = (self.data
                .annotate(response_count=models.Count('responses'))
                .filter(response_count__lt=self.data_limit)
                .exclude(responses__user=user)
                )
        if options:
            return choice(options)
        else:
            return None

    def create_form(self, form_json):
        """Create the crowdsource form from the form builder json"""
        form_data = json.loads(form_json)
        for order, field_data in enumerate(form_data):
            field = self.fields.create(
                    label=field_data['label'].strip('<br>'),
                    type=field_data['type'],
                    help_text=field_data.get('description', ''),
                    order=order,
                    )
            if 'values' in field_data and field.field.accepts_choices:
                for choice_order, value in enumerate(field_data['values']):
                    field.choices.create(
                            choice=value['label'],
                            value=value['value'],
                            order=choice_order,
                            )

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


class CrowdsourceData(models.Model):
    """A source of data to show with the crowdsource questions"""

    crowdsource = models.ForeignKey(Crowdsource, related_name='data')
    url = models.URLField(max_length=255, verbose_name='Data URL')
    metadata = JSONField(default=dict, blank=True)

    def __unicode__(self):
        return u'Crowdsource Data: {}'.format(self.url)

    def embed(self):
        """Get the html to embed into the crowdsource"""
        try:
            # first try to get embed code from oEmbed
            return mark_safe(PyEmbed().embed(self.url, max_height=400))
        except PyEmbedConsumerError:
            # fall back to a simple iframe
            return format_html(
                    '<iframe src="{}" width="100%" height="400px"></iframe>',
                    self.url,
                    )


class CrowdsourceField(models.Model):
    """A field on a crowdsource form"""

    crowdsource = models.ForeignKey(Crowdsource, related_name='fields')
    label = models.CharField(max_length=255)
    type = models.CharField(
            max_length=10,
            choices=fields.FIELD_CHOICES,
            )
    help_text = models.CharField(max_length=255, blank=True)
    order = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return self.label

    def get_form_field(self):
        """Return a form field appropriate for rendering this field"""
        kwargs = {'label': self.label}
        if self.field.accepts_choices:
            kwargs['choices'] = [(c.value, c.choice) for c in self.choices.all()]
        if self.help_text:
            kwargs['help_text'] = self.help_text
        return self.field.field(**kwargs)

    @property
    def field(self):
        """Get the crowdsource field instance"""
        return fields.FIELD_DICT[self.type]

    class Meta:
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
        values += list(self.values
                .order_by('field__order')
                .values_list('value', flat=True)
                )
        return values


class CrowdsourceValue(models.Model):
    """A field value for a given response"""

    response = models.ForeignKey(CrowdsourceResponse, related_name='values')
    field = models.ForeignKey(CrowdsourceField, related_name='values')
    value = models.CharField(max_length=255)

    def __unicode__(self):
        return self.value

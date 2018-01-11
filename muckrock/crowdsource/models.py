# -*- coding: utf-8 -*-
"""Models for the Crowdsource application"""

from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

import json
from pyembed.core import PyEmbed
from pyembed.core.consumer import PyEmbedConsumerError

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
        # ordering by ? might be slow, might need to find a different
        # way to select a random record
        return self.data.exclude(responses__user=user).order_by('?').first()

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


class CrowdsourceData(models.Model):
    """A source of data to show with the crowdsource questions"""

    crowdsource = models.ForeignKey(Crowdsource, related_name='data')
    url = models.URLField(max_length=255, verbose_name='Data URL')

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

    def __unicode__(self):
        return u'Response by {} on {}'.format(
                self.user,
                self.datetime,
                )


class CrowdsourceValue(models.Model):
    """A field value for a given response"""

    response = models.ForeignKey(CrowdsourceResponse, related_name='values')
    field = models.ForeignKey(CrowdsourceField, related_name='values')
    value = models.CharField(max_length=255)

    def __unicode__(self):
        return self.value

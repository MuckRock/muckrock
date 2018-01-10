# -*- coding: utf-8 -*-
"""Models for the Crowdsource application"""

from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe

from pyembed.core import PyEmbed

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


class CrowdsourceData(models.Model):
    """A source of data to show with the crowdsource questions"""

    crowdsource = models.ForeignKey(Crowdsource, related_name='data')
    url = models.URLField(
            max_length=255,
            help_text='This should be an oEmbed enabled URL',
            )

    def __unicode__(self):
        return u'Crowdsource Data: {}'.format(self.url)

    def embed(self):
        """Get the html to embed into the crowdsource"""
        return mark_safe(PyEmbed().embed(self.url, max_height=400))


class CrowdsourceField(models.Model):
    """A field on a crowdsource form"""

    crowdsource = models.ForeignKey(Crowdsource, related_name='fields')
    label = models.CharField(max_length=255)
    type = models.CharField(
            max_length=10,
            choices=fields.FIELD_CHOICES,
            )
    order = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return self.label


    def get_form_field(self):
        """Return a form field appropriate for rendering this field"""
        field = fields.FIELD_DICT[self.type]
        if field.accepts_choices:
            choices = [(c.choice, c.choice) for c in self.choices.all()]
            return field.field(label=self.label, choices=choices)
        else:
            return field.field(label=self.label)

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

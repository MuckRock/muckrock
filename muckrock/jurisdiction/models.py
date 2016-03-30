"""
Models for the Jurisdiction application
"""
from django.db import models
from django.db.models import Avg, Count, F, Sum
from django.template.defaultfilters import slugify

from easy_thumbnails.fields import ThumbnailerImageField
from random import choice

from muckrock.business_days.models import Holiday, HolidayCalendar, Calendar

# pylint: disable=bad-continuation

class RequestHelper(object):
    """Helper methods for classes that have a foiarequest_set"""

    def exemptions(self):
        """Get a list of exemptions tagged for requests from this agency"""
        return (self.foiarequest_set
                .filter(tags__name__startswith='exemption')
                .order_by('tags__name')
                .values('tags__name')
                .annotate(count=Count('tags')))

    def average_response_time(self):
        """Get the average response time from a submitted to completed request"""
        avg = (self.foiarequest_set.aggregate(
                avg=Avg(F('date_done') - F('date_submitted')))['avg'])
        return int(avg) if avg else 0

    def total_pages(self):
        """Total pages released"""

        pages = self.foiarequest_set.aggregate(Sum('files__pages'))['files__pages__sum']
        if pages is None:
            return 0
        return pages


class Jurisdiction(models.Model, RequestHelper):
    """A jursidiction that you may file FOIA requests in"""

    levels = (('f', 'Federal'), ('s', 'State'), ('l', 'Local'))

    name = models.CharField(max_length=50)
    # slug should be slugify(unicode(self))
    slug = models.SlugField(max_length=55)
    full_name = models.CharField(max_length=55, blank=True)
    abbrev = models.CharField(max_length=5, blank=True)
    level = models.CharField(max_length=1, choices=levels)
    parent = models.ForeignKey('self', related_name='children', blank=True, null=True)
    hidden = models.BooleanField(default=False)
    image = ThumbnailerImageField(upload_to='jurisdiction_images', blank=True, null=True)
    image_attr_line = models.CharField(blank=True, max_length=255, help_text='May use html')
    public_notes = models.TextField(blank=True, help_text='May use html')

    # non local
    days = models.PositiveSmallIntegerField(blank=True, null=True, help_text='How many days do they'
                                                                             ' have to respond?')
    observe_sat = models.BooleanField(default=False,
            help_text='Are holidays observed on Saturdays? '
                      '(or are they moved to Friday?)')
    holidays = models.ManyToManyField(Holiday, blank=True)
    use_business_days = models.BooleanField(default=True, help_text='Response time in business days'
                                                                    ' (or calendar days)?')
    intro = models.TextField(blank=True, help_text='Intro paragraph for request - '
                                         'usually includes the pertinant FOI law')
    law_name = models.CharField(blank=True, max_length=255, help_text='The pertinant FOIA law')
    waiver = models.TextField(blank=True, help_text='Optional - custom waiver paragraph if '
                              'FOI law has special line for waivers')
    has_appeal = models.BooleanField(
            default=True,
            help_text='Does this jurisdiction have an appeals process?')
    requires_proxy = models.BooleanField(default=False)

    def __unicode__(self):
        if self.level == 'l' and not self.full_name and self.parent:
            self.full_name = '%s, %s' % (self.name, self.parent.abbrev)
            self.save()
            return self.full_name
        elif self.level == 'l':
            return self.full_name
        else:
            return self.name

    def __repr__(self):
        return '<Jurisdiction: %d>' % self.pk

    def get_absolute_url(self):
        """The url for this object"""
        return self.get_url('detail')

    @models.permalink
    def get_url(self, view):
        """The url for this object"""
        view = 'jurisdiction-%s' % view
        if self.level == 'l':
            return (view, [], {'fed_slug': self.parent.parent.slug,
                               'state_slug': self.parent.slug,
                               'local_slug': self.slug})
        elif self.level == 's':
            return (view, [], {'fed_slug': self.parent.slug,
                               'state_slug': self.slug})
        elif self.level == 'f':
            return (view, [], {'fed_slug': self.slug})

    def save(self, *args, **kwargs):
        """Normalize fields before saving"""
        self.slug = slugify(self.slug)
        self.name = self.name.strip()
        super(Jurisdiction, self).save(*args, **kwargs)

    def get_url_flag(self):
        """So we can call from template"""
        return self.get_url('flag')

    def legal(self):
        """Return the jurisdiction abbreviation for which law this jurisdiction falls under"""
        if self.level == 'l':
            return self.parent.abbrev
        else:
            return self.abbrev

    def get_days(self):
        """How many days does an agency have to reply?"""
        if self.level == 'l':
            return self.parent.days
        else:
            return self.days

    def get_day_type(self):
        """Does this jurisdiction use business or calendar days?"""
        if self.level == 'l':
            return 'business' if self.parent.use_business_days else 'calendar'
        else:
            return 'business' if self.use_business_days else 'calendar'

    def get_intro(self):
        """Intro for requests"""
        if self.level == 'l':
            return self.parent.intro
        else:
            return self.intro

    def get_waiver(self):
        """Waiver paragraph for requests"""
        if self.level == 'l':
            return self.parent.waiver
        else:
            return self.waiver

    def get_law_name(self):
        """The law name for the jurisdiction"""
        if self.level == 'l':
            return self.parent.law_name
        else:
            return self.law_name

    def get_calendar(self):
        """Get a calendar of business days for the jurisdiction"""
        if self.level == 'l' and not self.parent.use_business_days:
            return Calendar()
        elif self.level == 'l' and self.parent.use_business_days:
            return HolidayCalendar(self.parent.holidays.all(), self.parent.observe_sat)
        elif not self.use_business_days:
            return Calendar()
        else:
            return HolidayCalendar(self.holidays.all(), self.observe_sat)

    def get_proxy(self):
        """Get a random proxy user for this jurisdiction"""
        from muckrock.accounts.models import Profile
        try:
            proxy = choice(Profile.objects.filter(
                acct_type='proxy', state=self.legal()))
            return proxy.user
        except IndexError:
            return None

    def get_state(self):
        """The state name for the jurisdiction"""
        # pylint: disable=no-member
        if self.level == 'l':
            return self.parent.name
        else:
            return self.name

    def can_appeal(self):
        """Can you appeal to this jurisdiction?"""
        if self.level == 'l':
            return self.parent.has_appeal
        else:
            return self.has_appeal

    class Meta:
        # pylint: disable=too-few-public-methods
        ordering = ['name']
        unique_together = ('slug', 'parent')



"""
Models for the Jurisdiction application
"""
from django.db import models
from django.db.models import Sum
from django.template.defaultfilters import slugify

from easy_thumbnails.fields import ThumbnailerImageField

from muckrock.business_days.models import Holiday, HolidayCalendar, Calendar
from muckrock.tags.models import Tag

# pylint: disable=bad-continuation

class RequestHelper(object):
    """Helper methods for classes that have a foiarequest_set"""
    # pylint: disable=no-member

    def exemptions(self):
        """Get a list of exemptions tagged for requests from this agency"""

        exemption_list = []
        for tag in Tag.objects.filter(name__startswith='exemption'):
            count = self.foiarequest_set.filter(tags=tag).count()
            if count:
                exemption_list.append({'name': tag.name, 'count': count})

        return exemption_list

    def interesting_requests(self):
        """Return a list of interesting requests to display on the agency's detail page"""
        # pylint: disable=W0141

        def make_req(headline, reqs):
            """Make a request dict if there is at least one request in reqs"""
            if reqs.exists():
                return {'headline': headline, 'req': reqs[0]}

        return filter(None, [
            make_req('Most Recently Completed Request',
                     self.foiarequest_set
                         .get_done()
                         .get_public()
                         .order_by('-date_done')),
            make_req('Oldest Overdue Request',
                     self.foiarequest_set
                         .get_overdue()
                         .get_public()
                         .order_by('date_due')),
            make_req('Largest Fufilled Request',
                     self.foiarequest_set
                         .get_done()
                         .get_public()
                         .filter(files__pages__gt=0)
                         .annotate(pages=Sum('files__pages'))
                         .order_by('-pages')),
            make_req('Most Viewed Request',
                     self.foiarequest_set
                         .get_public()
                         .order_by('-times_viewed')),
        ])

    def average_response_time(self):
        """Get the average response time from a submitted to completed request"""

        reqs = self.foiarequest_set.exclude(date_submitted=None).exclude(date_done=None)
        if reqs.exists():
            return sum((req.date_done - req.date_submitted).days for req in reqs) / reqs.count()
        else:
            return 0

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

    def __unicode__(self):
        # pylint: disable=no-member
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
        # pylint: disable=no-member
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
        # pylint: disable=no-member
        if self.level == 'l':
            return self.parent.abbrev
        else:
            return self.abbrev

    def get_days(self):
        """How many days does an agency have to reply?"""
        # pylint: disable=no-member
        if self.level == 'l':
            return self.parent.days
        else:
            return self.days

    def get_day_type(self):
        """Does this jurisdiction use business or calendar days?"""
        # pylint: disable=no-member
        if self.level == 'l':
            return 'business' if self.parent.use_business_days else 'calendar'
        else:
            return 'business' if self.use_business_days else 'calendar'

    def get_intro(self):
        """Intro for requests"""
        # pylint: disable=no-member
        if self.level == 'l':
            return self.parent.intro
        else:
            return self.intro

    def get_waiver(self):
        """Waiver paragraph for requests"""
        # pylint: disable=no-member
        if self.level == 'l':
            return self.parent.waiver
        else:
            return self.waiver

    def get_law_name(self):
        """The law name for the jurisdiction"""
        # pylint: disable=no-member
        if self.level == 'l':
            return self.parent.law_name
        else:
            return self.law_name

    def get_calendar(self):
        """Get a calendar of business days for the jurisdiction"""
        # pylint: disable=no-member
        if self.level == 'l' and not self.parent.use_business_days:
            return Calendar()
        elif self.level == 'l' and self.parent.use_business_days:
            return HolidayCalendar(self.parent.holidays.all(), self.parent.observe_sat)
        elif not self.use_business_days:
            return Calendar()
        else:
            return HolidayCalendar(self.holidays.all(), self.observe_sat)

    def can_appeal(self):
        """Can you appeal to this jurisdiction?"""
        # pylint: disable=no-member
        if self.level == 'l':
            return self.parent.has_appeal
        else:
            return self.has_appeal

    class Meta:
        # pylint: disable=too-few-public-methods
        ordering = ['name']
        unique_together = ('slug', 'parent')



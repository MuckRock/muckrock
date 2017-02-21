"""
Models for the Jurisdiction application
"""
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import F, Q, Avg, Sum, Count
from django.template.defaultfilters import slugify

from easy_thumbnails.fields import ThumbnailerImageField
from taggit.managers import TaggableManager

from muckrock.business_days.models import Holiday, HolidayCalendar, Calendar
from muckrock.foia.models import FOIARequest, END_STATUS
from muckrock.tags.models import TaggedItemBase

# pylint: disable=bad-continuation

class RequestHelper(object):
    """Helper methods for classes that have a get_requests() method"""
    def average_response_time(self):
        """Get the average response time from a submitted to completed request"""
        requests = self.get_requests()
        avg = (requests.aggregate(avg=Avg(F('date_done') - F('date_submitted')))['avg'])
        return int(avg) if avg else 0

    def average_fee(self):
        """Get the average fees required on requests that have a price."""
        requests = self.get_requests()
        avg = requests.filter(price__gt=0).aggregate(price=Avg('price'))['price']
        return avg if avg else 0

    def fee_rate(self):
        """Get the percentage of requests that have a fee."""
        requests = self.get_requests()
        filed = float(requests.get_submitted().count())
        fee = float(requests.get_submitted().filter(price__gt=0).count())
        rate = 0
        if filed > 0:
            rate = fee/filed * 100
        return rate

    def success_rate(self):
        """Get the percentage of requests that are successful."""
        requests = self.get_requests()
        filed = float(requests.get_submitted().count())
        completed = float(requests.get_done().count())
        rate = 0
        if filed > 0:
            rate = completed/filed * 100
        return rate

    def total_pages(self):
        """Total pages released"""
        requests = self.get_requests()
        pages = requests.aggregate(Sum('files__pages'))['files__pages__sum']
        return pages if pages else 0


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
    law_analysis = models.TextField(blank=True, help_text='Our analysis of the state FOIA law, '
                                                'as a part of FOI95.')

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
        return reverse('jurisdiction-detail', kwargs=self.get_slugs())

    def get_slugs(self):
        """Return a dictionary of slugs for this jurisdiction, for constructing URLs."""
        slugs = {}
        if self.level == 'l':
            slugs.update({
                'fed_slug': self.parent.parent.slug,
                'state_slug': self.parent.slug,
                'local_slug': self.slug
            })
        elif self.level == 's':
            slugs.update({
                'fed_slug': self.parent.slug,
                'state_slug': self.slug
            })
        elif self.level == 'f':
            slugs.update({
                'fed_slug': self.slug
            })
        return slugs

    def get_url(self, view):
        """The url for this object"""
        view = 'jurisdiction-%s' % view
        slugs = self.get_slugs()
        return reverse(view, kwargs=slugs)

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
        proxy = (Profile.objects
                .filter(acct_type='proxy', state=self.legal())
                .order_by('-preferred_proxy')
                .first())
        if proxy:
            return proxy.user
        else:
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

    def get_requests(self):
        """State level jurisdictions should return requests from their localities as well."""
        if self.level == 's':
            requests = FOIARequest.objects.filter(
                Q(jurisdiction=self)|
                Q(jurisdiction__parent=self)
            )
        else:
            requests = FOIARequest.objects.filter(jurisdiction=self)
        return requests.exclude(status='started')

    class Meta:
        # pylint: disable=too-few-public-methods
        ordering = ['name']
        unique_together = ('slug', 'parent')


class Law(models.Model):
    """A law that allows for requests for public records from a jurisdiction."""
    jurisdiction = models.ForeignKey(Jurisdiction, related_name='laws')
    name = models.CharField(max_length=255, help_text='The common name of the law.')
    shortname = models.CharField(blank=True, max_length=20,
        help_text='Abbreviation or acronym, e.g. FOIA, FOIL, OPRA')
    citation = models.CharField(max_length=255, help_text='The legal reference for this law.')
    url = models.URLField(help_text='The URL of the full text of the law.')
    summary = models.CharField(blank=True, max_length=255, verbose_name='Major Dates')

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '%d' % self.pk

    def get_absolute_url(self):
        """Return the url for the jurisdiction."""
        return self.jurisdiction.get_absolute_url()


class Exemption(models.Model):
    """An exemption describes a reason for not releasing documents or information inside them."""
    # Required fields
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    jurisdiction = models.ForeignKey(Jurisdiction, related_name='exemptions')
    aliases = models.TextField(blank=True)
    basis = models.TextField(help_text='The legal or contextual basis for the exemption.')
    # Optional fields
    tags = TaggableManager(through=TaggedItemBase, blank=True)
    requests = models.ManyToManyField(
        FOIARequest,
        through='jurisdiction.InvokedExemption',
        related_name='exemptions',
        blank=True
    )
    contributors = models.ManyToManyField(User, related_name='exemptions', blank=True)
    proper_use = models.TextField(blank=True,
        help_text='An editorialized description of cases when the exemption is properly used.')
    improper_use = models.TextField(blank=True,
        help_text='An editorialized description of cases when the exemption is improperly used.')
    key_citations = models.TextField(blank=True,
        help_text='Significant references to the exemption in caselaw or previous appeals.')

    def __unicode__(self):
        return u'%s exemption of %s' % (self.name, self.jurisdiction)

    def __repr__(self):
        return '%s' % self.slug

    def save(self, *args, **kwargs):
        """Normalize fields before saving"""
        self.slug = slugify(self.name)
        super(Exemption, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """Return the url for the exemption detail page"""
        kwargs = self.jurisdiction.get_slugs()
        kwargs['slug'] = self.slug
        kwargs['pk'] = self.pk
        return reverse('exemption-detail', kwargs=kwargs)


class InvokedExemption(models.Model):
    """An invoked exemption tracks the use of an exemption in the course of fulfilling
    (or rejecting!) a FOIA request. It should connect a request to an exemption and contain
    information particular to the invocation of the exemption to the request.

    It augments the Exemption model by providing specific examples of situations
    where the exemption was invoked, i.e. there should only ever be 1 exemption
    but there can be many invocations of that exemption."""
    exemption = models.ForeignKey(Exemption, related_name='invokations')
    request = models.ForeignKey(FOIARequest)
    use_language = models.TextField(blank=True,
        help_text='What language did the aguency use to invoke the exemption?')
    properly_invoked = models.BooleanField(default=True,
        help_text='Did the agency properly invoke the exemption to the request?')

    def __unicode__(self):
        return u'%s exemption of %s' % (self.exemption.name, self.request)

    def __repr__(self):
        return '%d' % self.pk

    def get_absolute_url(self):
        """Return the url for the exemption detail page, targeting the invokation."""
        kwargs = self.exemption.jurisdiction.get_slugs()
        kwargs['slug'] = self.exemption.slug
        kwargs['pk'] = self.exemption.pk
        return reverse('exemption-detail', kwargs=kwargs) + '#invoked-%d' % self.pk


class ExampleAppeal(models.Model):
    """Exemptions should contain example appeal language for users to reference.
    This language will be curated by staff and contain the language as well as
    the context when the language is most effective. Each ExampleAppeal instance
    should connect to an Exemption."""
    exemption = models.ForeignKey(Exemption, related_name='example_appeals')
    title = models.TextField(default='Untitled Example')
    language = models.TextField()
    context = models.TextField(blank=True,
        help_text='Under what circumstances is this appeal language most effective?')

    def __unicode__(self):
        return u'%(name)s for %(exemption)s' % {
            'name': self.title if self.title else 'Example appeal',
            'exemption': self.exemption
        }

    def __repr__(self):
        return '<ExampleAppeal: %d>' % self.pk

    def get_absolute_url(self):
        """Return the url for the exemption detail page, targeting the appeal."""
        kwargs = self.exemption.jurisdiction.get_slugs()
        kwargs['slug'] = self.exemption.slug
        kwargs['pk'] = self.exemption.pk
        return reverse('exemption-detail', kwargs=kwargs) + '#appeal-%d' % self.pk


class Appeal(models.Model):
    """Appeals should capture information about appeals submitted to agencies.
    It should capture the communication used to appeal, as well as the base language
    used to write the appeal, if any was used."""
    communication = models.ForeignKey('foia.FOIACommunication', related_name='appeals')
    base_language = models.ManyToManyField(ExampleAppeal, related_name='appeals', blank=True)

    def __unicode__(self):
        return u'Appeal of %s' % self.communication.foia

    def __repr__(self):
        return '<Appeal: %d>' % self.pk

    def get_absolute_url(self):
        """Return the url for the communication."""
        return self.communication.get_absolute_url()

    def is_successful(self):
        """Evaluate the FOIARequest communications to judge whether the appeal is successful."""
        foia = self.communication.foia
        subsequent_comms = (foia.communications.filter(date__gt=self.communication.date)
                                               .annotate(appeal__count=Count('appeals')))
        successful = False
        successful = successful or subsequent_comms.filter(status='done').exists()
        successful = successful and not subsequent_comms.filter(appeal__count__gt=0).exists()
        return successful

    def is_finished(self):
        """Evaluate the FOIARequest communications to judge whether the appeal is finished."""
        foia = self.communication.foia
        subsequent_comms = foia.communications.filter(date__gt=self.communication.date)
        return subsequent_comms.filter(status__in=END_STATUS).exists()

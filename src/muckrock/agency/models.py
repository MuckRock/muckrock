"""
Models for the Agency application
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum

from jurisdiction.models import Jurisdiction
from tags.models import Tag
import fields

class AgencyType(models.Model):
    """Marks an agency as fufilling requests of this type for its jurisdiction"""

    name = models.CharField(max_length=60)

    def __unicode__(self):
        return self.name

    class Meta:
        # pylint: disable=R0903
        ordering = ['name']


class Agency(models.Model):
    """An agency for a particular jurisdiction that has at least one agency type"""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    jurisdiction = models.ForeignKey(Jurisdiction, related_name='agencies')
    types = models.ManyToManyField(AgencyType, blank=True)
    approved = models.BooleanField()
    user = models.ForeignKey(User, null=True, blank=True)
    appeal_agency = models.ForeignKey('self', null=True, blank=True)
    can_email_appeals = models.BooleanField()

    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    other_emails = fields.EmailsListField(blank=True, max_length=255)
    contact_salutation = models.CharField(blank=True, max_length=30)
    contact_first_name = models.CharField(blank=True, max_length=100)
    contact_last_name = models.CharField(blank=True, max_length=100)
    contact_title = models.CharField(blank=True, max_length=255)
    url = models.URLField(blank=True, verbose_name='Website', help_text='Begin with http://')
    expires = models.DateField(blank=True, null=True)
    phone = models.CharField(blank=True, max_length=20)
    fax = models.CharField(blank=True, max_length=20)
    notes = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    def normalize_fax(self):
        """Return a fax number suitable for use in a faxaway email address"""

        fax = ''.join(c for c in self.fax if c.isdigit())
        if len(fax) == 10:
            return '1' + fax
        if len(fax) == 11 and fax[0] == '1':
            return fax
        return None

    def get_email(self):
        """Returns an email address to send to"""

        if self.email:
            return self.email
        elif self.normalize_fax():
            return '%s@fax2.faxaway.com' % self.normalize_fax()
        else:
            return ''

    def get_other_emails(self):
        """Returns other emails as a list"""
        return fields.email_separator_re.split(self.other_emails)

    def exemptions(self):
        """Get a list of exemptions tagged for requests from this agency"""
        # pylint: disable=E1101

        exemption_list = []
        for tag in Tag.objects.filter(name__startswith='exemption'):
            count = self.foiarequest_set.filter(tags=tag).count()
            if count:
                exemption_list.append({'name': tag.name, 'count': count})

        return exemption_list

    def interesting_requests(self):
        """Return a list of interesting requests to display on the agency's detail page"""
        # pylint: disable=E1101
        # pylint: disable=W0141

        def make_req(headline, reqs):
            """Make a request dict if there is at least one request in reqs"""
            if reqs.exists():
                print reqs[0].title
                print reqs[0].total_pages()
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
                         .filter(documents__pages__gt=0)
                         .annotate(pages=Sum('documents__pages'))
                         .order_by('-pages')),
            make_req('Most Viewed Request',
                     self.foiarequest_set
                         .get_public()
                         .order_by('-times_viewed')),
        ])

    def average_response_time(self):
        """Get the average response time from a submitted to completed request"""
        # pylint: disable=E1101

        reqs = self.foiarequest_set.exclude(date_submitted=None).exclude(date_done=None)
        return sum((req.date_done - req.date_submitted).days for req in reqs) / reqs.count()


    class Meta:
        # pylint: disable=R0903
        verbose_name_plural = 'agencies'


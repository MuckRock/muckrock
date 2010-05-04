"""
Models for the FOIA application
"""

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.mail import send_mail
from utils import try_or_none

JURISDICTIONS = (('MA', 'Massachusetts'),)

STATUS = (
    ('started', 'Started'),
    ('submitted', 'Submitted'),
    ('processed', 'Processed'),
    ('fix', 'Fix required'),
    ('rejected', 'Rejected'),
    ('done', 'Response received'),
)

class FOIARequest(models.Model):
    """A Freedom of Information Act request"""

    user = models.ForeignKey(User)
    title = models.CharField(max_length=30)
    slug = models.SlugField(max_length=30)
    # tags = ManyToManyField(tags)
    status = models.CharField(max_length=10, choices=STATUS)
    jurisdiction = models.CharField(max_length=5, choices=JURISDICTIONS)
    agency = models.CharField(max_length=30) # choices?
    # fees?
    request = models.TextField()
    response = models.TextField(blank=True)
    # response in pdf/jpg scan of official document version
    date_submitted = models.DateField(blank=True, null=True)
    date_done = models.DateField(blank=True, null=True, verbose_name='Date response received')

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        # pylint: disable-msg=E1101
        return ('foia-detail', [], {'user_name': self.user.username, 'slug': self.slug})

    def is_editable(self):
        """Can this request be updated?"""
        return self.status == 'started' or self.status == 'fix'

    def doc_first_page(self):
        """Get the first page of this requests corresponding document"""
        # pylint: disable-msg=E1101
        return self.images.get(page=1)

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['title']
        verbose_name = 'FOIA Request'
        unique_together = (('user', 'slug'),)

class FOIAImage(models.Model):
    """An image attached to a FOIA request"""
    # pylint: disable-msg=E1101
    foia = models.ForeignKey(FOIARequest, related_name='images')
    image = models.ImageField(upload_to='foia_images')
    page = models.SmallIntegerField(unique=True)

    def __unicode__(self):
        return '%s Document Page %d' % (self.foia.title, self.page)

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('foia-doc-detail', [],
                {'user_name': self.foia.user.username,
                 'slug': self.foia.slug,
                 'page': self.page})

    def next(self):
        """Get next document page"""
        return try_or_none(self.DoesNotExist, self.foia.images.get, page=self.page + 1)

    def previous(self):
        """Get previous document page"""
        return try_or_none(self.DoesNotExist, self.foia.images.get, page=self.page - 1)

    def total_pages(self):
        """Get total page count"""
        return self.foia.images.count()

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['page']
        verbose_name = 'FOIA Document Image'

mail_template = \
"""
Dear %(name)s,

This mail is to let you know that your FOIA Request "%(title)s"
has been updated.  Its current status is '%(status)s' and you may
view the full details of the request here:
http://www.muckrock.com%(link)s.

Thanks for using MuckRock and please email us if you have any
questions about our service!

Sincerely,
The MuckRock Team
"""

def foia_save_handler(sender, **kwargs):
    """Log changes to FOIA Requests"""
    # pylint: disable-msg=W0613

    request = kwargs['instance']
    msg = mail_template % {'name': request.user.get_full_name(),
                           'title': request.title,
                           'status': request.get_status_display(),
                           'link': request.get_absolute_url()}
    send_mail('[MuckRock] FOIA request has been updated',
              msg, 'info@muckrock.com', [request.user.email], fail_silently=False)

post_save.connect(foia_save_handler, sender=FOIARequest, dispatch_uid='muckrock.foia.models')

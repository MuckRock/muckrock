"""
Tests for the request handler
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core import management, mail
from django.db import connection
from django.test import utils

from lamson.testing import queue, relay, RouterConversation
from lamson import routing, mail as lmail

import nose.tools
from datetime import date

from accounts.models import Profile
from foia.models import FOIARequest, Jurisdiction
from muckrock.settings import LAMSON_ROUTER_HOST

relay = relay(port=8823)
client = RouterConversation('mitch@localhost.gov', 'requests_tests')
old_db = ''

def setup():
    """Set up the test environment"""
    # pylint: disable-msg=W0603
    # pylint: disable-msg=W0212

    utils.setup_test_environment()
    settings.DEBUG = False

    global old_db
    old_db = settings.DATABASE_NAME
    # get commands to load the cache
    management.get_commands()
    # then override syncdb to core in the cache to not use the south syncdb
    management._commands['syncdb'] = 'django.core'
    connection.creation.create_test_db()

    # populate the db
    user = User.objects.create_user('mitch', 'mitch@test.com')
    Profile.objects.create(user=user, date_update=date.today())
    jurisdiction = Jurisdiction.objects.create(name='United States of America',
                                               slug='united-states-of-america',
                                               abbrev='USA')
    foia = FOIARequest.objects.create(user=user, jurisdiction=jurisdiction,
                                      title='test foia', slug='test-foia',
                                      email='test@foia.gov')
    foia.set_mail_id()

def teardown():
    """Tear down the test environment"""

    connection.creation.destroy_test_db(old_db)
    utils.teardown_test_environment()

def test_drops_open_relay_messages():
    """
    But, make sure that mail NOT for test.com gets dropped silently.
    """
    client.begin()
    client.say('tester@badplace.notinterwebs', 'Relay should not happen')
    nose.tools.eq_(queue().count(), 0, 'You are configured currently to accept everything.  '
                                       'You should change config/settings.py router_defaults so '
                                       'host is your actual host name that will receive mail.')

def test_bad_sender():
    """Test a bad sender"""

    foia = FOIARequest.objects.get(title='test foia')
    client.begin()
    client.deliver('%s@%s' % (foia.mail_id, LAMSON_ROUTER_HOST), 'mitch@localhost.com',
                   'Subject', 'Test a bad sender.')
    nose.tools.ok_(queue().pop()[1]['subject'].startswith('Bad Sender'))

def test_bad_addr():
    """Test sending to a FOIA mail id that does not exist"""
    client.begin()
    client.say('123-12345678@%s' % LAMSON_ROUTER_HOST, 'Test a bad address.')
    nose.tools.ok_(queue().pop()[1]['subject'].startswith('Invalid address'))

def test_normal():
    """Test a normal succesful response"""

    foia = FOIARequest.objects.get(title='test foia')
    client.begin()
    client.say('%s@%s,other@agency.gov' % (foia.mail_id, LAMSON_ROUTER_HOST), 'Test normal.')

    foia = FOIARequest.objects.get(pk=foia.pk)
    nose.tools.eq_(foia.first_request(), 'Test normal.')

    mail_ls = sorted([queue().pop(), queue().pop()])
    nose.tools.ok_(mail_ls.pop()[1]['subject'].startswith('[RESPONSE]'))
    nose.tools.eq_(mail_ls.pop()[1].body(), 'Test normal.')

    nose.tools.eq_(len(mail.outbox), 1)
    nose.tools.eq_(mail.outbox[0].to, [foia.user.email])

    nose.tools.eq_(foia.email, 'mitch@localhost.gov')
    nose.tools.eq_(foia.other_emails, 'other@agency.gov')


# test different attachment types

def test_attachments():
    """Test a message with an attachment"""

    try:
        foia = FOIARequest.objects.get(title='test foia')

        sample = lmail.MailResponse(
            From='mitch@localhost.gov',
            To='%s@%s' % (foia.mail_id, LAMSON_ROUTER_HOST),
            Subject='Test Attachment Subject',
            Body='Test Attachment Body')
        sample.attach(filename='data.xls', data='abc123')
        msg = lmail.MailRequest('localhost', sample['From'], sample['To'], str(sample))
        routing.Router.deliver(msg)

        foia = FOIARequest.objects.get(pk=foia.pk)
        nose.tools.eq_(foia.files.all()[0].ffile.name, 'foia_files/data.xls')

    finally:
        # delete the file from the file system
        foia.files.all()[0].delete()


# test different attachment types
